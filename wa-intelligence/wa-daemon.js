/**
 * wa-daemon.js — ARGOS™ WA Intelligence Daemon
 * CoVe 2026 | Enterprise Grade | PM2 Managed
 *
 * S60: Migrato da DuckDB a SQLite (WAL mode, multi-processo nativo).
 * S64: Migrato dbExec/dbQuery da python3 shell a better-sqlite3 nativo.
 *      Aggiunto scheduler multi-step (Day 3 + Day 7 voice).
 *
 * RESPONSABILITÀ:
 *   - Mantiene la sessione WhatsApp SEMPRE attiva (non si chiude mai)
 *   - Ascolta TUTTI gli eventi WA in real-time
 *   - Su ogni messaggio in arrivo: log → SQLite → analyzer → Telegram alert
 *   - Gestisce la coda di invio (anti-ban sleep obbligatorio)
 *   - Scheduler automatico: Day 3 follow-up + Day 7 voice note
 *
 * AVVIO: pm2 start wa-daemon.js --name argos-wa-daemon
 * STOP:  pm2 stop argos-wa-daemon
 * LOG:   pm2 logs argos-wa-daemon
 */

'use strict';

const { Client, LocalAuth }     = require('whatsapp-web.js');
const { execSync, spawn }       = require('child_process');
const http                      = require('http');
const fs                        = require('fs');
const path                      = require('path');
const Database                  = require('better-sqlite3');

const TC = require('./time-context.js');
const QRCode = require('qrcode');

// ── Configurazione ────────────────────────────────────────────
const CONFIG = {
    SESSION_ID:    process.env.WA_CLIENT_ID || 'argos-business',
    DB_PATH:       process.env.DB_PATH
                   || process.env.ARGOS_DB_PATH
                   || path.join(__dirname, '..', 'dealer_network.sqlite'),  // S169 fix: portable (iMac+MacBook diff dir names)
    TELEGRAM_SCRIPT: path.join(__dirname, 'telegram-handler.py'),
    ANALYZER_SCRIPT: path.join(__dirname, 'response-analyzer.py'),
    OUTBOUND_GUARD:  path.join(__dirname, 'outbound_guard.py'),
    POST_SEND_UPDATE: path.join(__dirname, 'post_send_update.py'),
    PYTHON_BIN:    'python3',
    SEND_QUEUE:    [],          // coda messaggi in uscita
    DAILY_SENT:    0,
    DAILY_LIMIT:   30,
    DAILY_RESET:   null,        // data ultimo reset
    LOG_FILE:      '/tmp/argos-wa-daemon.log',
    SCHEDULER_INTERVAL: 30 * 60 * 1000,  // 30 minuti
};

// S117: Anti-ban — agent_state table + warm-up schedule
function initAntibanTables() {
    const db = getDb();
    try {
        db.exec(`
            CREATE TABLE IF NOT EXISTS agent_state (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        `);
        db.exec(`
            CREATE TABLE IF NOT EXISTS daily_stats (
                date           TEXT PRIMARY KEY,
                sent           INTEGER DEFAULT 0,
                delivered      INTEGER DEFAULT 0,
                read_count     INTEGER DEFAULT 0,
                replied        INTEGER DEFAULT 0,
                failed         INTEGER DEFAULT 0,
                blocked        INTEGER DEFAULT 0,
                new_contacts   INTEGER DEFAULT 0
            )
        `);
        // Seed defaults
        db.prepare(`INSERT OR IGNORE INTO agent_state (key, value) VALUES (?, ?)`).run('status', 'active');
        db.prepare(`INSERT OR IGNORE INTO agent_state (key, value) VALUES (?, ?)`).run('pause_until', '0');
        db.prepare(`INSERT OR IGNORE INTO agent_state (key, value) VALUES (?, ?)`).run('account_start_date', new Date().toISOString().split('T')[0]);
        log('INFO', 'Anti-ban tables initialized');
    } catch (e) {
        log('WARN', `Anti-ban tables init: ${e.message}`);
    }
}

function getDailyLimit() {
    const db = getDb();
    try {
        const row = db.prepare("SELECT value FROM agent_state WHERE key='account_start_date'").get();
        if (!row) return 10;
        const startDate = new Date(row.value);
        if (isNaN(startDate.getTime())) { log('WARN', `Malformed account_start_date: ${row.value}`); return 10; }
        const now = new Date();
        const weekAge = Math.floor((now - startDate) / (7 * 24 * 60 * 60 * 1000));
        // Warm-up: 10 → 15 → 20 (never exceed 20 for unofficial API)
        if (weekAge <= 1) return 10;
        if (weekAge <= 3) return 15;
        return 20;
    } catch (e) {
        return 10;
    }
}

function getAgentStatus() {
    const db = getDb();
    try {
        const row = db.prepare("SELECT value FROM agent_state WHERE key='status'").get();
        return row ? row.value : 'active';
    } catch (e) {
        return 'active';
    }
}

function getPauseUntil() {
    const db = getDb();
    try {
        const row = db.prepare("SELECT value FROM agent_state WHERE key='pause_until'").get();
        return row ? parseInt(row.value) || 0 : 0;
    } catch (e) {
        return 0;
    }
}

function incrementDailyStats(field) {
    const ALLOWED = {sent:1, delivered:1, read_count:1, replied:1, failed:1, blocked:1, new_contacts:1};
    if (!ALLOWED[field]) { log('ERROR', `incrementDailyStats: invalid field '${field}'`); return; }
    const db = getDb();
    const today = new Date().toISOString().split('T')[0];
    try {
        db.prepare(`INSERT INTO daily_stats (date, ${field}) VALUES (?, 1) ON CONFLICT(date) DO UPDATE SET ${field} = ${field} + 1`).run(today);
    } catch (e) {
        log('WARN', `daily_stats increment ${field}: ${e.message}`);
    }
}

// ── Shell argument sanitizer (CT-14 fix: prevent command injection) ──
function sanitizeShellArg(str) {
    if (!str) return '';
    return String(str)
        .replace(/"/g, '\\"')
        .replace(/\$/g, '\\$')
        .replace(/`/g, '\\`')
        .replace(/\\/g, '\\\\')
        .replace(/!/g, '\\!');
}

// ── Utility log con timestamp IT ────────────────────────────
function log(level, ...args) {
    const ts  = TC.formatIT(TC.nowIT());
    const msg = `[${ts}][${level}] ${args.join(' ')}`;
    console.log(msg);
    try {
        fs.appendFileSync(CONFIG.LOG_FILE, msg + '\n');
    } catch (_) {}
}

// ── SQLite helpers (better-sqlite3 — zero shell, in-process) ─
let _db = null;

function getDb() {
    if (!_db) {
        _db = new Database(CONFIG.DB_PATH, { timeout: 10000 });
        _db.pragma('journal_mode = WAL');
        _db.pragma('busy_timeout = 10000');
    }
    return _db;
}

function dbExec(sql, params = []) {
    try {
        const db = getDb();
        if (params.length > 0) {
            db.prepare(sql).run(...params);
        } else {
            db.exec(sql);
        }
        return 'OK';
    } catch (e) {
        log('ERROR', 'dbExec failed:', e.message);
        return null;
    }
}

function dbQuery(sql, params = []) {
    try {
        const db = getDb();
        if (params.length > 0) {
            return db.prepare(sql).all(...params);
        }
        return db.prepare(sql).all();
    } catch (e) {
        log('ERROR', 'dbQuery failed:', e.message);
        return [];
    }
}

// ── BRIDGE WIRE-UP S168 (additive, feature-flagged via BRIDGE_DB_PATH) ──
// D-22 F1 (bridge SQLite) + D-07 HITL strict (no auto-send senza approved_ts)
// Reversibile single commit. No-op completo se BRIDGE_DB_PATH unset.
const BRIDGE_DB_PATH                = process.env.BRIDGE_DB_PATH || '';
const BRIDGE_POLL_INTERVAL_MS       = parseInt(process.env.BRIDGE_POLL_INTERVAL_MS || '30000', 10);
const BRIDGE_ANTI_BAN_DELAY_MS_MIN  = 30000;  // riusa D-04 anti-ban
const BRIDGE_ANTI_BAN_DELAY_MS_MAX  = 90000;
const BRIDGE_POLL_BATCH             = 5;      // max 5 send per ciclo (throughput cap)
let _bridgeDb = null;

function getBridgeDb() {
    if (!BRIDGE_DB_PATH) return null;
    if (_bridgeDb) return _bridgeDb;
    try {
        _bridgeDb = new Database(BRIDGE_DB_PATH, { timeout: 5000 });
        _bridgeDb.pragma('journal_mode = WAL');
        _bridgeDb.pragma('busy_timeout = 5000');
        return _bridgeDb;
    } catch (e) {
        log('WARN', `[bridge] open failed ${BRIDGE_DB_PATH}: ${e.message}`);
        return null;
    }
}

function bridgeResolveRole(bdb, phone) {
    // Lookup bridge_parties WHERE phone — fallback 'dealer' se non registrato
    try {
        const row = bdb.prepare('SELECT role FROM bridge_parties WHERE phone = ?').get(phone);
        return row ? row.role : null;
    } catch (e) {
        return null;
    }
}

async function bridgeIngestInbound(msg) {
    const bdb = getBridgeDb();
    if (!bdb) return;
    try {
        // S170 fix: WA 2025+ usa @lid (internal ID) per molti msg → risolvere PRIMA del lookup
        // bridge_parties (registered con phone normalizzato). Stessa logica di handleInboundMessage.
        let rawFrom = msg.from || '';
        let phone = rawFrom;
        if (rawFrom.endsWith('@lid')) {
            try {
                const contact = await msg.getContact();
                if (contact && contact.number) phone = `${contact.number}@c.us`;
            } catch (e) {
                log('WARN', `[bridge] LID resolve failed for ${rawFrom}: ${e.message}`);
            }
        }
        phone = phone.replace('@c.us', '').replace('@lid', '');
        const role = bridgeResolveRole(bdb, phone);
        if (!role) {
            log('INFO', `[bridge] inbound skip (unknown party ${phone}, raw ${rawFrom})`);
            return;
        }
        bdb.prepare(`
            INSERT INTO bridge_inbound (msg_id, party_role, party_phone, party_alias, body, received_ts)
            VALUES (?, ?, ?, NULL, ?, ?)
            ON CONFLICT(msg_id) DO NOTHING
        `).run(
            msg.id?._serialized || String(msg.id),
            role,
            phone,
            msg.body || '',
            Math.floor(Date.now() / 1000)
        );
        log('INFO', `[bridge] inbound ingested phone=${phone} role=${role}`);
    } catch (e) {
        log('WARN', `[bridge] ingest_inbound failed: ${e.message}`);
    }
}

// S171: schema migration idempotente (additive cols processing_ts + attempt_count)
function ensureBridgeOutboundSchemaS171(bdb) {
    try {
        const cols = bdb.prepare("PRAGMA table_info(bridge_outbound)").all().map(c => c.name);
        if (!cols.includes('processing_ts')) {
            bdb.exec('ALTER TABLE bridge_outbound ADD COLUMN processing_ts INTEGER');
            log('INFO', '[bridge] S171 schema: added processing_ts');
        }
        if (!cols.includes('attempt_count')) {
            bdb.exec('ALTER TABLE bridge_outbound ADD COLUMN attempt_count INTEGER DEFAULT 0');
            log('INFO', '[bridge] S171 schema: added attempt_count');
        }
    } catch (e) {
        log('WARN', `[bridge] S171 schema migration skipped: ${e.message}`);
    }
}

// S171: classifica errori send permanent vs transient
function isPermanentSendError(errStr) {
    return /No LID for user|invalid wid|invalid number|not.?registered|forbidden|not.?found/i.test(errStr);
}

// S171: reclaim window stale processing (max poll_interval*4, min 120s)
const BRIDGE_RECLAIM_WINDOW_S = Math.max(120, Math.floor(BRIDGE_POLL_INTERVAL_MS * 4 / 1000));
const BRIDGE_MAX_ATTEMPTS = 3;

async function pollBridgeOutbound(clientRef) {
    const bdb = getBridgeDb();
    if (!bdb || !clientRef) return;
    ensureBridgeOutboundSchemaS171(bdb);
    let pending = [];
    try {
        pending = bdb.prepare(`
            SELECT id, deal_id, target_role, target_phone, body, template_phase, attempt_count
            FROM bridge_outbound
            WHERE approved_ts IS NOT NULL
              AND sent_ts IS NULL
              AND (processing_ts IS NULL OR processing_ts < strftime('%s','now') - ?)
              AND COALESCE(attempt_count, 0) < ?
            ORDER BY approved_ts ASC
            LIMIT ?
        `).all(BRIDGE_RECLAIM_WINDOW_S, BRIDGE_MAX_ATTEMPTS, BRIDGE_POLL_BATCH);
    } catch (e) {
        log('ERROR', `[bridge] poll query failed: ${e.message}`);
        return;
    }
    for (const row of pending) {
        const chatId = `${row.target_phone}@c.us`;
        const now = Math.floor(Date.now() / 1000);

        // S171: atomic claim PRE-send (idempotency lock)
        const claim = bdb.prepare(`
            UPDATE bridge_outbound
            SET processing_ts = ?, attempt_count = COALESCE(attempt_count, 0) + 1
            WHERE id = ?
              AND sent_ts IS NULL
              AND (processing_ts IS NULL OR processing_ts < ?)
        `).run(now, row.id, now - BRIDGE_RECLAIM_WINDOW_S);

        if (claim.changes === 0) {
            log('INFO', `[bridge] skip id=${row.id} (already claimed by concurrent poll)`);
            continue;
        }
        const currentAttempt = (row.attempt_count || 0) + 1;

        try {
            log('INFO', `[bridge] sending id=${row.id} attempt=${currentAttempt} deal=${row.deal_id} phase=${row.template_phase} → ${row.target_phone}`);
            const sentMsg = await clientRef.sendMessage(chatId, row.body);
            const waMsgId = sentMsg?.id?._serialized || null;
            bdb.prepare(`
                UPDATE bridge_outbound
                SET sent_ts = ?, sent_status = 'ok', wa_msg_id = ?, processing_ts = NULL
                WHERE id = ?
            `).run(Math.floor(Date.now() / 1000), waMsgId, row.id);
            log('INFO', `[bridge] sent ok id=${row.id} wa_msg_id=${waMsgId}`);
            // Anti-ban delay 30-90s tra send (riusa pattern D-04)
            const delay = BRIDGE_ANTI_BAN_DELAY_MS_MIN +
                          Math.random() * (BRIDGE_ANTI_BAN_DELAY_MS_MAX - BRIDGE_ANTI_BAN_DELAY_MS_MIN);
            await new Promise(r => setTimeout(r, delay));
        } catch (e) {
            const errStr = (e.message || String(e)).substring(0, 200);
            const permanent = isPermanentSendError(errStr);
            const capped = currentAttempt >= BRIDGE_MAX_ATTEMPTS;
            log('ERROR', `[bridge] send failed id=${row.id} attempt=${currentAttempt}/${BRIDGE_MAX_ATTEMPTS} permanent=${permanent}: ${errStr}`);
            try {
                if (permanent || capped) {
                    // Terminal: set sent_ts to escape poll forever
                    bdb.prepare(`
                        UPDATE bridge_outbound
                        SET sent_status = ?, sent_ts = ?, processing_ts = NULL
                        WHERE id = ?
                    `).run(`error_${permanent ? 'permanent' : 'capped'}: ${errStr}`, Math.floor(Date.now() / 1000), row.id);
                } else {
                    // Transient: clear processing_ts, retry next poll cycle
                    bdb.prepare(`
                        UPDATE bridge_outbound
                        SET sent_status = ?, processing_ts = NULL
                        WHERE id = ?
                    `).run(`error_transient: ${errStr}`, row.id);
                }
            } catch (_) {}
        }
    }
}

// ── S173: Bridge insert helper (Day3 + auto_approve mono-msg) ───────────────
// Usa INSERT OR IGNORE — il UNIQUE INDEX uq_outbound_deal_phone_phase (migrazione S173)
// impedisce duplicati silenziosamente senza eccezioni.
// Returns: { inserted: bool, rowId: number }
function insertBridgeOutbound({ dealId, role, phone, phase, lang, body, state }) {
    const bdb = getBridgeDb();
    if (!bdb) {
        log('WARN', '[bridge] insertBridgeOutbound: no bridge DB, skip');
        return { inserted: false, rowId: -1 };
    }
    try {
        const now = Math.floor(Date.now() / 1000);
        const res = bdb.prepare(`
            INSERT OR IGNORE INTO bridge_outbound
                (deal_id, target_role, target_phone, template_phase, template_lang,
                 body, state_at_send, created_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `).run(dealId, role, phone, phase, lang, body, state, now);
        const inserted = res.changes === 1;
        if (!inserted) {
            log('INFO', `[bridge][dedup] INSERT OR IGNORE skipped duplicate deal=${dealId} phone=${phone} phase=${phase}`);
        }
        return { inserted, rowId: res.lastInsertRowid || -1 };
    } catch (e) {
        log('ERROR', `[bridge] insertBridgeOutbound failed: ${e.message}`);
        return { inserted: false, rowId: -1 };
    }
}

// ── S173: Precheck 24h — verifica ultimo invio su stesso phone ───────────────
// Restituisce { recent: bool, minutesAgo: number } — usato da Day7, /send, Telegram /approva
function bridgePrecheck24h(phone) {
    const bdb = getBridgeDb();
    if (!bdb) return { recent: false, minutesAgo: -1 };
    try {
        const cutoff = Math.floor(Date.now() / 1000) - 24 * 3600;
        const row = bdb.prepare(`
            SELECT sent_ts FROM bridge_outbound
            WHERE target_phone = ? AND sent_ts IS NOT NULL AND sent_ts > ?
            ORDER BY sent_ts DESC LIMIT 1
        `).get(phone, cutoff);
        if (!row) return { recent: false, minutesAgo: -1 };
        const minutesAgo = Math.round((Math.floor(Date.now() / 1000) - row.sent_ts) / 60);
        return { recent: true, minutesAgo };
    } catch (e) {
        log('WARN', `[bridge] precheck24h error: ${e.message}`);
        return { recent: false, minutesAgo: -1 };
    }
}

// ── S173: Audit log force=true overrides ─────────────────────────────────────
// Scrive in ~/venture-os/state/argos-force-overrides.jsonl (audit trail compliance)
function logForceOverride({ phone, context, replyId = null }) {
    const entry = JSON.stringify({
        ts: Math.floor(Date.now() / 1000),
        phone,
        reply_id: replyId,
        founder: 'luke',
        context,
    });
    try {
        const auditPath = require('os').homedir() + '/venture-os/state/argos-force-overrides.jsonl';
        fs.appendFileSync(auditPath, entry + '\n');
        log('INFO', `[force-override] audit logged: phone=${phone} context=${context}`);
    } catch (e) {
        log('WARN', `[force-override] audit log failed: ${e.message} — entry: ${entry}`);
    }
}

// ── Inizializza schema DB se non esiste ──────────────────────
function ensureSchema() {
    const db = getDb();

    db.exec(`
        CREATE TABLE IF NOT EXISTS conversations (
            dealer_id       TEXT PRIMARY KEY,
            dealer_name     TEXT,
            city            TEXT,
            phone_number    TEXT,
            stock_size      INTEGER,
            persona_type    TEXT,
            score           REAL,
            source          TEXT,
            notes           TEXT,
            current_step    TEXT DEFAULT 'PENDING',
            day1_message    TEXT,
            recommendation  TEXT DEFAULT 'PENDING',
            created_at      TEXT DEFAULT (datetime('now')),
            last_contact_at TEXT,
            analyzed_at     TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id              TEXT PRIMARY KEY,
            dealer_id       TEXT,
            dealer_name     TEXT,
            phone_number    TEXT,
            direction       TEXT,
            body            TEXT,
            timestamp_it    TEXT,
            timestamp_iso   TEXT,
            wa_msg_id       TEXT,
            processed       INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS pending_replies (
            id              TEXT PRIMARY KEY,
            dealer_id       TEXT,
            dealer_name     TEXT,
            inbound_msg_id  TEXT,
            reply_text      TEXT,
            reply_label     TEXT,
            cialdini_trigger TEXT,
            approved        INTEGER DEFAULT NULL,
            sent            INTEGER DEFAULT 0,
            scheduled_at    TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS scheduled_actions (
            id              TEXT PRIMARY KEY,
            dealer_id       TEXT,
            dealer_name     TEXT,
            action_type     TEXT,
            due_at          TEXT,
            status          TEXT DEFAULT 'PENDING',
            fired_at        TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id              TEXT PRIMARY KEY,
            event_type      TEXT,
            dealer_id       TEXT,
            payload         TEXT,
            timestamp_it    TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );
    `);

    // S202-INBOX: ALTER idempotent — 3 colonne reactive classifier
    // SQLite non supporta ADD COLUMN IF NOT EXISTS: usiamo PRAGMA table_info come guard
    const messagesColumns = db.prepare("PRAGMA table_info(messages)").all().map(r => r.name);
    if (!messagesColumns.includes('classifier_intent')) {
        db.prepare("ALTER TABLE messages ADD COLUMN classifier_intent TEXT").run();
        log('INFO', 'S202: ADD COLUMN messages.classifier_intent');
    }
    if (!messagesColumns.includes('classifier_confidence')) {
        db.prepare("ALTER TABLE messages ADD COLUMN classifier_confidence REAL").run();
        log('INFO', 'S202: ADD COLUMN messages.classifier_confidence');
    }
    if (!messagesColumns.includes('raw_payload')) {
        db.prepare("ALTER TABLE messages ADD COLUMN raw_payload TEXT").run();
        log('INFO', 'S202: ADD COLUMN messages.raw_payload');
    }

    // Indici partial reactive (IF NOT EXISTS sicuro su SQLite)
    db.exec(`
        CREATE INDEX IF NOT EXISTS idx_messages_phone_dir_ts
            ON messages(phone_number, direction, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_messages_intent
            ON messages(classifier_intent) WHERE classifier_intent IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_messages_unprocessed
            ON messages(processed) WHERE processed = 0;
    `);

    log('INFO', 'Schema DB verificato (better-sqlite3 WAL mode).');
}

// ── Reset contatore giornaliero se è un nuovo giorno ────────
function checkDailyReset() {
    const today = TC.nowIT().toDateString();
    if (CONFIG.DAILY_RESET !== today) {
        CONFIG.DAILY_RESET = today;
        CONFIG.DAILY_SENT  = 0;
        log('INFO', `Daily counter reset — ${today}`);
    }
}

// ── Ricerca dealer dal numero di telefono ────────────────────
function lookupDealer(phone) {
    // Normalizza: rimuovi @c.us e prefisso internazionale
    const normalized = phone.replace('@c.us', '').replace(/^\+/, '');
    const suffix = normalized.slice(-9);
    const rows = dbQuery(`
        SELECT *
        FROM conversations
        WHERE REPLACE(REPLACE(phone_number, '+', ''), ' ', '') = ?
           OR REPLACE(REPLACE(phone_number, '+', ''), ' ', '') LIKE ?
        LIMIT 1
    `, [normalized, `%${suffix}`]);
    return rows[0] || null;
}

// ── Logga messaggio in arrivo su DB ──────────────────────────
function persistInboundMessage(msg, dealer) {
    const now  = TC.nowIT();
    const id   = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const db = getDb();
    // S202-INBOX: raw_payload cattura metadati WA per audit/debug (no PII extra)
    const rawPayload = JSON.stringify({
        from:      msg.from,
        type:      msg.type || 'chat',
        hasMedia:  msg.hasMedia || false,
        timestamp: msg.timestamp || null,
    });
    try {
        db.prepare(`
            INSERT OR IGNORE INTO messages
                (id, dealer_id, dealer_name, phone_number, direction, body,
                 timestamp_it, timestamp_iso, wa_msg_id, processed, raw_payload)
            VALUES (?, ?, ?, ?, 'INBOUND', ?, datetime('now'), ?, ?, 0, ?)
        `).run(
            id,
            dealer?.dealer_id || 'UNKNOWN',
            dealer?.dealer_name || msg.from,
            msg._resolvedPhone || msg.from,
            msg.body,
            now.toISOString(),
            msg.id?.id || id,
            rawPayload
        );
    } catch (e) {
        log('ERROR', 'persistInboundMessage failed:', e.message);
    }
    return id;
}

// ── Aggiorna stato conversazione al DB principale ────────────
function updateConversationState(dealerId, newStep) {
    const db = getDb();
    try {
        db.prepare(`
            UPDATE conversations
            SET current_step     = ?,
                last_contact_at  = datetime('now'),
                analyzed_at      = datetime('now')
            WHERE dealer_id = ?
        `).run(newStep, dealerId);
    } catch (e) {
        log('ERROR', 'updateConversationState failed:', e.message);
    }
}

// ── Cap risposte per-dealer (max 3 auto-risposte/giorno) ────
const DEALER_DAILY_REPLIES = new Map(); // dealerId → count today
const MAX_REPLIES_PER_DEALER = 10;

function canReplyToDealer(dealerId) {
    const today = TC.nowIT().toDateString();
    const key = `${dealerId}_${today}`;
    const count = DEALER_DAILY_REPLIES.get(key) || 0;
    return count < MAX_REPLIES_PER_DEALER;
}

function trackReplyToDealer(dealerId) {
    const today = TC.nowIT().toDateString();
    const key = `${dealerId}_${today}`;
    DEALER_DAILY_REPLIES.set(key, (DEALER_DAILY_REPLIES.get(key) || 0) + 1);
}

// ── Chiama analyzer asincrono ────────────────────────────────
function triggerAnalyzer(inboundMsgId, msgBody, dealer) {
    const dealerId = dealer?.dealer_id || 'UNKNOWN';

    // Cap per-dealer: max 3 risposte auto/giorno
    if (!canReplyToDealer(dealerId)) {
        log('WARN', `⚠️ Cap raggiunto per ${dealer?.dealer_name} (${MAX_REPLIES_PER_DEALER}/giorno) — msg salvato ma non risposto`);
        sendTelegramAlert(`⚠️ *Cap risposte raggiunto*\n👤 ${dealer?.dealer_name}\n📩 "${msgBody.slice(0, 80)}"\n\n_Rispondere manualmente se necessario_`);
        return;
    }
    trackReplyToDealer(dealerId);

    const ctx    = TC.buildAgentTimeContext(dealer || {});
    const ctxStr = JSON.stringify(ctx).replace(/'/g, "\\'");

    log('INFO', `Triggering analyzer per msg: ${inboundMsgId}`);

    // Log analyzer output to file per debug (S65 fix)
    const analyzerLogFd = fs.openSync('/tmp/argos-analyzer.log', 'a');

    const args = [
        CONFIG.ANALYZER_SCRIPT,
        '--msg-id',     inboundMsgId,
        '--msg-body',   msgBody,
        '--dealer-id',  dealer?.dealer_id || 'UNKNOWN',
        '--dealer-name', dealer?.dealer_name || 'Sconosciuto',
        '--persona',    dealer?.persona_type || 'RAGIONIERE',
        '--step',       dealer?.current_step || 'UNKNOWN',
        '--db-path',    CONFIG.DB_PATH,
        '--time-ctx',   ctxStr,
    ];

    // Flag batch se messaggi aggregati dal buffer
    if (msgBody.includes('\n---\n')) {
        args.push('--batch');
    }

    const child = spawn(CONFIG.PYTHON_BIN, args, {
        detached: true,
        stdio:    ['ignore', analyzerLogFd, analyzerLogFd],
    });
    child.unref(); // non blocca il daemon
    fs.closeSync(analyzerLogFd); // CT-12 fix: prevent EMFILE fd leak
}

// ── Invia alert Telegram (fire-and-forget, non blocca event loop — CT-09 fix) ─
function sendTelegramAlert(text, replyMarkup = null) {
    const markupStr = replyMarkup ? JSON.stringify(replyMarkup) : '{}';
    try {
        const child = spawn(CONFIG.PYTHON_BIN, [
            CONFIG.TELEGRAM_SCRIPT, 'alert',
            text.slice(0, 4000),
            markupStr
        ], { detached: true, stdio: 'ignore' });
        child.unref();
        log('INFO', 'Telegram alert dispatched');
    } catch (e) {
        log('ERROR', 'Telegram alert fallito:', e.message);
    }
}

// ── Outbound Guard: pre-send validation via Python (S106) ───
function runOutboundGuard(dealerId, templateId, message) {
    try {
        const result = execSync(
            `${CONFIG.PYTHON_BIN} ${CONFIG.OUTBOUND_GUARD} ` +
            `--db-path "${CONFIG.DB_PATH}" ` +
            `--dealer-id "${sanitizeShellArg(dealerId)}" ` +
            `--template-id "${sanitizeShellArg(templateId)}" ` +
            `--message "${sanitizeShellArg(message.slice(0, 2000))}"`,
            { timeout: 10000, encoding: 'utf-8' }
        );
        return JSON.parse(result.trim());
    } catch (e) {
        log('ERROR', 'outbound_guard failed:', e.message);
        return { ok: false, reason: `GUARD_ERROR: ${e.message}`, check: 'error' };
    }
}

// ── Post-Send Update: state machine transition via Python (S106) ─
function runPostSendUpdate(dealerId, templateId) {
    try {
        const result = execSync(
            `${CONFIG.PYTHON_BIN} ${CONFIG.POST_SEND_UPDATE} ` +
            `--db-path "${CONFIG.DB_PATH}" ` +
            `--dealer-id "${dealerId}" ` +
            `--template-id "${templateId}"`,
            { timeout: 10000, encoding: 'utf-8' }
        );
        const parsed = JSON.parse(result.trim());
        log('INFO', `[STATE] ${dealerId}: → ${parsed.new_state} (out=${parsed.outbound_count})`);
        return parsed;
    } catch (e) {
        log('ERROR', 'post_send_update failed:', e.message);
        return { ok: false };
    }
}

// ── Message Buffer (debounce multi-input) — modulo-level ──
const MESSAGE_BUFFER = new Map();
const DEBOUNCE_MS = 15000;  // 15 secondi silence window
const HARD_CAP_MS = 45000;  // 45 secondi max dal primo messaggio

// ── Anti-Ban: Human-Like Sender (module-level) ──────────────
let _waClient = null; // settato in initClient() quando ready

const HumanLike = {
    logNormalDelay(meanMs, stdMs) {
        const u1 = Math.random();
        const u2 = Math.random();
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        const delay = Math.exp(Math.log(meanMs) + z * (stdMs / meanMs));
        return Math.max(2000, Math.min(delay, meanMs * 3));
    },
    async simulateTyping(cli, chatId, messageLength) {
        try {
            const chat = await (cli || _waClient).getChatById(chatId);
            await chat.sendPresenceUpdate('composing');
            const typingMs = Math.max(2000, Math.min(10000, messageLength * 50 + Math.random() * 1500));
            await new Promise(r => setTimeout(r, typingMs));
        } catch (e) { log('WARN', 'simulateTyping failed:', e.message); }
    },
    async simulateRecording(cli, chatId, audioDurationSec) {
        try {
            const chat = await (cli || _waClient).getChatById(chatId);
            await chat.sendPresenceUpdate('recording');
            const recordMs = audioDurationSec * 1000 * (0.8 + Math.random() * 0.4);
            await new Promise(r => setTimeout(r, Math.min(recordMs, 30000)));
        } catch (e) { log('WARN', 'simulateRecording failed:', e.message); }
    },
    async checkOnWhatsApp(cli, phone) {
        try {
            const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;
            return await (cli || _waClient).isRegisteredUser(chatId);
        } catch (e) { log('WARN', `onWhatsApp check failed: ${e.message}`); return true; }
    },
    async clearPresence(cli, chatId) {
        try { const chat = await (cli || _waClient).getChatById(chatId); await chat.clearState(); } catch (_) {}
    },
    isAllowedToSend(phone) {
        // S177c: TEST_FOUNDER whitelist — numero test del founder bypassa anti-ban (zero rischio ban)
        if (phone && process.env.TEST_FOUNDER_PHONE) {
            const cleanPhone = String(phone).replace(/[^0-9]/g, '');
            const testPhone = String(process.env.TEST_FOUNDER_PHONE).replace(/[^0-9]/g, '');
            if (cleanPhone === testPhone) {
                log('INFO', 'Anti-ban: TEST_FOUNDER whitelist, bypass business hours');
                return true;
            }
        }
        if (!TC.isBusinessHours()) { log('INFO', 'Anti-ban: fuori business hours, invio bloccato'); return false; }
        return true;
    }
};

// ── Handler principale: messaggio in arrivo ──────────────────
async function handleInboundMessage(msg) {
    const now    = TC.nowIT();
    const timeCtx = TC.formatContextForLog(TC.buildAgentTimeContext());

    // 1. Cerca dealer nel DB — SOLO dealer noti in pipeline
    // Se il msg arriva con @lid (nuovo formato WA), ottieni il numero reale dal contatto
    let phone = msg.from;
    if (msg.from.endsWith('@lid')) {
        try {
            const contact = await msg.getContact();
            phone = contact.number ? `${contact.number}@c.us` : msg.from;
            log('INFO', `LID resolved: ${msg.from} → ${phone} (${contact.pushname || '?'})`);
        } catch (e) {
            log('WARN', `LID resolve failed for ${msg.from}: ${e.message}`);
        }
    }

    const dealer = lookupDealer(phone);
    if (!dealer) {
        log('INFO', `⏭️ Messaggio da numero non in pipeline: ${phone} (raw: ${msg.from}) — ignorato`);
        return;
    }

    log('INFO', `━━━ MESSAGGIO IN ARRIVO ━━━`);
    log('INFO', `Da: ${msg.from} → ${dealer.dealer_name} (${dealer.dealer_id})`);
    log('INFO', `Corpo: ${msg.body.slice(0, 120)}`);
    log('INFO', timeCtx);

    // 2. Logga sul DB (usa phone risolto, non raw LID)
    msg._resolvedPhone = phone; // passa il numero risolto

    // S116: Noise filter — skip empty, media, and broadcast noise
    const body = (msg.body || '').trim();
    if (body.length < 3) {
        log('INFO', `⏭️ Noise filter: body troppo corto (${body.length} chars) — skipped`);
        return;
    }
    // Base64 media detection (JPEG, PNG, PDF, audio/video)
    if (body.startsWith('/9j/') || body.startsWith('iVBOR') || body.startsWith('JVBER') ||
        body.startsWith('AAAA') || body.startsWith('SUQz') || body.startsWith('Rklm')) {
        log('INFO', `⏭️ Noise filter: base64 media detected — skipped`);
        return;
    }
    // Long body without spaces = likely base64 or encoded media
    if (body.length > 500 && !body.substring(0, 200).includes(' ')) {
        log('INFO', `⏭️ Noise filter: encoded content detected (${body.length} chars, no spaces) — skipped`);
        return;
    }

    const msgId = persistInboundMessage(msg, dealer);

    // 3. Aggiorna audit log
    const db = getDb();
    try {
        db.prepare(`
            INSERT OR IGNORE INTO audit_log (id, event_type, dealer_id, payload, timestamp_it)
            VALUES (?, 'INBOUND_MESSAGE', ?, ?, datetime('now'))
        `).run(
            `audit_${Date.now()}`,
            dealer?.dealer_id || 'UNKNOWN',
            JSON.stringify({from: msg.from, body: msg.body.slice(0,200), msgId})
        );
    } catch (e) {
        log('ERROR', 'audit_log insert failed:', e.message);
    }

    // 4. Alert Telegram (solo se NON c'è già un buffer attivo per questo dealer)
    const hasExistingBuffer = MESSAGE_BUFFER.has(dealer.dealer_id);

    if (!hasExistingBuffer) {
        const dealerLabel = `*${dealer.dealer_name}* (${dealer.persona_type || '?'}) — step: ${dealer.current_step || '?'}`;
        const daysInfo = dealer?.last_contact_at
            ? `⏱ ${TC.daysElapsed(dealer.last_contact_at)}gg dall'ultimo contatto`
            : '';

        const alertText = [
            `📩 *RISPOSTA WHATSAPP* — ${TC.formatIT(now)}`,
            ``,
            `👤 ${dealerLabel}`,
            daysInfo,
            ``,
            `💬 _"${msg.body.slice(0, 300)}"_`,
            ``,
            `⏳ Analisi in corso (buffer 15s)...`,
        ].filter(Boolean).join('\n');

        sendTelegramAlert(alertText);
    }

    // 5. Aggiorna step se dealer noto (S106: state machine update avviene in response-analyzer.py)
    if (dealer) {
        updateConversationState(dealer.dealer_id, 'INBOUND_RECEIVED');
    }

    // 6. Buffer debounce (aspetta 15s di silenzio prima di analizzare)
    bufferMessage(dealer, msg, msgId);
}

// ── Inizializza client WA ────────────────────────────────────

function bufferMessage(dealer, msg, msgId) {
    const dealerId = dealer.dealer_id;

    if (MESSAGE_BUFFER.has(dealerId)) {
        const buf = MESSAGE_BUFFER.get(dealerId);
        buf.messages.push({ body: msg.body, type: msg.type, id: msgId, timestamp: Date.now() });

        clearTimeout(buf.timer);

        const elapsed = Date.now() - buf.firstAt;
        const remaining = Math.max(1000, HARD_CAP_MS - elapsed);
        const wait = Math.min(DEBOUNCE_MS, remaining);

        buf.timer = setTimeout(() => flushBuffer(dealerId, dealer), wait);
        log('INFO', `Buffer: +1 msg per ${dealer.dealer_name} (${buf.messages.length} in buffer, flush tra ${Math.round(wait/1000)}s)`);
    } else {
        const timer = setTimeout(() => flushBuffer(dealerId, dealer), DEBOUNCE_MS);
        MESSAGE_BUFFER.set(dealerId, {
            messages: [{ body: msg.body, type: msg.type, id: msgId, timestamp: Date.now() }],
            timer,
            firstAt: Date.now(),
        });
        log('INFO', `Buffer: nuovo per ${dealer.dealer_name} (flush tra 15s)`);
    }
}

function flushBuffer(dealerId, dealer) {
    const buf = MESSAGE_BUFFER.get(dealerId);
    if (!buf) return;
    MESSAGE_BUFFER.delete(dealerId);

    const bodies = buf.messages.map(m => m.body).filter(Boolean);
    const combinedBody = bodies.join('\n---\n');
    const firstMsgId = buf.messages[0].id;

    log('INFO', `Buffer flush: ${dealer.dealer_name} — ${buf.messages.length} msg aggregati`);
    triggerAnalyzer(firstMsgId, combinedBody, dealer);
}

// ── Inizializza client WA ────────────────────────────────
function initClient() {
    log('INFO', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    log('INFO', 'ARGOS™ WA Intelligence Daemon v2.1 (SQLite)');
    log('INFO', `Avvio: ${TC.formatIT(TC.nowIT())}`);
    log('INFO', `DB: ${CONFIG.DB_PATH}`);
    log('INFO', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    ensureSchema();

    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: CONFIG.SESSION_ID,
            dataPath: path.join(__dirname, '..', 'wa-sender'),
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--disable-extensions',
                '--single-process',          // iMac 2012 ha poca RAM
            ]
        }
    });

    // ── QR State (esposto via GET /qr) ──────────────────────
    let QR_STATE = { qr: null, status: 'initializing', updated_at: null };

    // ── Events ──────────────────────────────────────────────

    client.on('qr', (qr) => {
        // Genera QR come data URL (base64 PNG) server-side
        QRCode.toDataURL(qr, { width: 300, margin: 2 }, (err, dataUrl) => {
            QR_STATE = { qr: dataUrl || qr, status: 'waiting_scan', updated_at: new Date().toISOString() };
            log('WARN', 'QR generato — disponibile su GET /qr');
            sendTelegramAlert('⚠️ *WA Daemon*: QR pronto. Apri http://192.168.1.2:9191/qr per scansionare');
        });
    });

    client.on('authenticated', () => {
        QR_STATE = { qr: null, status: 'authenticated', updated_at: new Date().toISOString() };
        log('INFO', '✅ Sessione autenticata');
    });

    client.on('auth_failure', (msg) => {
        log('ERROR', 'Auth failure:', msg);
        sendTelegramAlert(`🔴 *WA Daemon Auth Failure*: ${msg}`);
    });

    client.on('ready', () => {
        QR_STATE = { qr: null, status: 'connected', updated_at: new Date().toISOString() };
        const ctx = TC.buildAgentTimeContext();
        log('INFO', '✅ Client PRONTO — in ascolto');
        log('INFO', TC.formatContextForLog(ctx));
        sendTelegramAlert(
            `✅ *ARGOS™ WA Daemon ONLINE*\n` +
            `📅 ${TC.formatIT(TC.nowIT())}\n` +
            `🕐 Business hours: ${TC.isBusinessHours() ? 'SÌ' : 'NO'}\n` +
            `📊 Daily limit: ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`
        );
        // BRIDGE WIRE-UP S168: avvia poll outbound (no-op se BRIDGE_DB_PATH unset)
        if (BRIDGE_DB_PATH) {
            log('INFO', `[bridge] polling enabled every ${BRIDGE_POLL_INTERVAL_MS}ms (batch=${BRIDGE_POLL_BATCH}, anti-ban 30-90s)`);
            setInterval(() => { pollBridgeOutbound(client).catch(e => log('ERROR', `[bridge] poll err: ${e.message}`)); }, BRIDGE_POLL_INTERVAL_MS);
        }
    });

    client.on('disconnected', (reason) => {
        QR_STATE = { qr: null, status: 'disconnected', updated_at: new Date().toISOString() };
        log('ERROR', 'Disconnesso:', reason);
        sendTelegramAlert(`🔴 *WA Daemon disconnesso*: ${reason}\nPM2 riavvierà automaticamente.`);
        setTimeout(() => process.exit(1), 3000);
    });

    // ── Messaggi in arrivo (message_create è più affidabile di message in WA Web.js 2025+)
    client.on('message_create', async (msg) => {
        // Ignora messaggi non rilevanti
        if (msg.fromMe)                        return;
        if (msg.from.endsWith('@g.us'))        return;  // gruppo WA
        if (msg.from === 'status@broadcast')   return;  // stati WA (storie)
        if (msg.from.endsWith('@newsletter'))  return;  // canali WA
        if (msg.from.endsWith('@broadcast'))   return;  // broadcast generico
        if (msg.type === 'e2e_notification')   return;
        // Accetta sia @c.us (vecchio) che @lid (nuovo formato WA 2025+)
        if (!msg.from.endsWith('@c.us') && !msg.from.endsWith('@lid')) return;

        checkDailyReset();
        log('INFO', `📨 Raw msg.from: ${msg.from} | type: ${msg.type} | hasBody: ${!!msg.body}`);
        // BRIDGE WIRE-UP S168: dual-write a bridge_inbound (no-op se BRIDGE_DB_PATH unset)
        // S170 fix: async per LID resolution PRIMA di bridge_parties lookup
        await bridgeIngestInbound(msg);
        await handleInboundMessage(msg);
    });

    // ── Message ACK (conferma lettura) ───────────────────────
    client.on('message_ack', (msg, ack) => {
        // ack: 1=sent server, 2=delivered device, 3=read, 4=played
        const now = TC.formatIT(TC.nowIT());
        const waMsgId = msg.id?._serialized || msg.id?.id || 'unknown';
        const ackLabels = { 1: '🛰️ SENT_SERVER', 2: '📬 DELIVERED', 3: '✓✓ LETTO', 4: '▶️ PLAYED' };
        const label = ackLabels[ack] || `ACK_${ack}`;
        log('INFO', `${label}: ${msg.to} — ${now} — wa_msg_id=${waMsgId}`);
        if (ack === 3) {
            const db = getDb();
            try {
                db.prepare('UPDATE messages SET processed = 1 WHERE wa_msg_id = ?')
                  .run(waMsgId);
                db.prepare(`
                    INSERT OR IGNORE INTO audit_log (id, event_type, dealer_id, payload, timestamp_it)
                    VALUES (?, 'MSG_READ_ACK', 'UNKNOWN', ?, datetime('now'))
                `).run(`ack_${Date.now()}`, JSON.stringify({to: msg.to, ack: 3, wa_msg_id: waMsgId}));
            } catch (e) {
                log('ERROR', 'message_ack db failed:', e.message);
            }
        }
    });

    // HumanLike è ora module-level — setta il client reference
    _waClient = client;

    // ── HTTP Server (porta 9191): health + send + qr ────────
    const API_KEY = process.env.ARGOS_API_KEY || '';

    http.createServer(async (req, res) => {
        checkDailyReset();
        if (!CONFIG._antibanInit) { CONFIG._antibanInit = true; initAntibanTables(); }

        // ── Auth check (skip health check GET /) ──
        if (API_KEY && !(req.method === 'GET' && (req.url === '/' || req.url === '/status'))) {
            const reqKey = req.headers['x-api-key'] || '';
            if (reqKey !== API_KEY) {
                res.writeHead(401, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'unauthorized — X-API-Key header required' }));
                return;
            }
        }

        // GET /qr — mostra QR code per autenticazione (HTML o JSON)
        if (req.method === 'GET' && req.url.startsWith('/qr')) {
            const wantsJson = (req.headers.accept || '').includes('application/json') || req.url.includes('format=json');

            if (wantsJson) {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(QR_STATE));
                return;
            }

            // HTML page con QR code auto-refresh
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });

            if (QR_STATE.status === 'connected') {
                res.end(`<!DOCTYPE html><html><body style="background:#1a1a2e;color:#0f0;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
                    <div style="text-align:center"><h1>✅ WhatsApp Connesso</h1><p>Sessione attiva — daemon in ascolto</p></div></body></html>`);
                return;
            }

            if (QR_STATE.status === 'authenticated') {
                res.end(`<!DOCTYPE html><html><body style="background:#1a1a2e;color:#0f0;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
                    <div style="text-align:center"><h1>✅ Autenticato</h1><p>In attesa di connessione completa...</p></div>
                    <script>setTimeout(()=>location.reload(),3000)</script></body></html>`);
                return;
            }

            if (!QR_STATE.qr) {
                res.end(`<!DOCTYPE html><html><body style="background:#1a1a2e;color:#fff;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
                    <div style="text-align:center"><h1>⏳ QR in generazione...</h1><p>Status: ${QR_STATE.status}</p></div>
                    <script>setTimeout(()=>location.reload(),3000)</script></body></html>`);
                return;
            }

            // QR come immagine base64 PNG — zero dipendenze client
            res.end(`<!DOCTYPE html><html><head><title>ARGOS WA Auth</title></head>
                <body style="background:#1a1a2e;color:#fff;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
                <div style="text-align:center">
                    <h2 style="color:#e94560">ARGOS™ WhatsApp Auth</h2>
                    <img src="${QR_STATE.qr}" style="margin:20px auto;display:block;border:8px solid #fff;border-radius:12px;width:300px;height:300px" />
                    <p>Scansiona con WA Business → Dispositivi collegati → Collega</p>
                    <p style="color:#666;font-size:12px">Auto-refresh ogni 20s | Status: ${QR_STATE.status}</p>
                </div>
                <script>setTimeout(()=>location.reload(), 20000)</script></body></html>`);
            return;
        }

        // POST /send — invia messaggio singolo WA via daemon (con anti-ban)
        if (req.method === 'POST' && req.url === '/send') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const { phone, message, dealer_id, template_id, dry_run, force } = JSON.parse(body);
                    if (!phone || !message) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'phone and message required' }));
                        return;
                    }
                    // Input validation
                    const cleanPhone = phone.replace(/[^0-9]/g, '');
                    if (!/^(39)?3\d{8,9}$/.test(cleanPhone)) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'invalid italian phone number', phone }));
                        return;
                    }
                    if (message.length > 4096) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'message too long (max 4096 chars)' }));
                        return;
                    }
                    // Dry run mode for E2E testing
                    if (dry_run) {
                        const fakeMsgId = `dry_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                        log('INFO', `[DRY RUN] Would send to ${phone}: ${message.slice(0, 50)}...`);
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ status: 'sent', msg_id: fakeMsgId, dry_run: true }));
                        return;
                    }

                    // S106: Outbound Guard — state machine + validator check
                    if (dealer_id && template_id) {
                        const guard = runOutboundGuard(dealer_id, template_id, message);
                        if (!guard.ok) {
                            log('WARN', `[GUARD] BLOCKED: ${dealer_id} — ${guard.reason}`);
                            sendTelegramAlert(`🛑 *Invio BLOCCATO*\n👤 ${dealer_id}\n📋 ${template_id}\n❌ ${guard.reason}`);
                            res.writeHead(403, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({ error: 'outbound_guard_blocked', reason: guard.reason, check: guard.check }));
                            return;
                        }
                        log('INFO', `[GUARD] OK: ${dealer_id} — ${template_id}`);
                    }

                    if (!HumanLike.isAllowedToSend(phone)) {
                        res.writeHead(403, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'outside business hours' }));
                        return;
                    }
                    // S117: Warm-up daily limit
                    const dynamicLimit = getDailyLimit();
                    if (CONFIG.DAILY_SENT >= dynamicLimit) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit reached', daily_sent: CONFIG.DAILY_SENT, daily_limit: dynamicLimit }));
                        return;
                    }

                    // S117: Agent paused check
                    if (getAgentStatus() === 'paused') {
                        res.writeHead(503, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'agent_paused', message: 'POST /resume to restart' }));
                        return;
                    }

                    // S117: Long pause check
                    const pauseUntil = getPauseUntil();
                    if (Date.now() < pauseUntil) {
                        const remaining = Math.round((pauseUntil - Date.now()) / 60000);
                        res.writeHead(503, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'long_pause_active', resume_in_minutes: remaining }));
                        return;
                    }

                    // CT-16 fix: check WA connected before send (cached state)
                    if (!QR_STATE || QR_STATE.status !== 'connected') {
                        res.writeHead(503, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'wa_not_connected', wa_status: QR_STATE?.status || 'unknown' }));
                        return;
                    }

                    // S148 Patch 3: live getState() check — rivela sessioni stale che QR_STATE cached non vede
                    const liveState = await client.getState().catch(e => { log('WARN', `getState failed: ${e.message}`); return null; });
                    if (liveState !== 'CONNECTED') {
                        log('ERROR', `STALE_SESSION rilevata pre-send: getState()=${liveState} (QR_STATE cached=${QR_STATE.status})`);
                        sendTelegramAlert(`🔴 *WA STALE_SESSION* — getState=${liveState}, QR_STATE=${QR_STATE.status}\nServe re-auth QR`);
                        QR_STATE.status = 'stale';
                        res.writeHead(503, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'stale_session', live_state: liveState, cached_state: QR_STATE.status }));
                        return;
                    }

                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;

                    // S173: precheck 24h — blocca invio se phone ha già ricevuto msg nelle ultime 24h
                    // Bypass solo con force=true esplicito nel payload + audit log obbligatorio
                    // `force` estratto dal JSON.parse sopra insieme a phone/message/dealer_id
                    const precheckSend = bridgePrecheck24h(cleanPhone);
                    if (precheckSend.recent && !force) {
                        log('WARN', `[/send][precheck24h] BLOCKED phone=${cleanPhone} — sent ${precheckSend.minutesAgo}min ago. Send force=true to override.`);
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            error: 'precheck_24h_blocked',
                            phone: cleanPhone,
                            minutes_ago: precheckSend.minutesAgo,
                            hint: 'Add force:true to payload to override (audit log will be written)',
                        }));
                        return;
                    }
                    if (precheckSend.recent && force) {
                        logForceOverride({ phone: cleanPhone, context: 'http_send', replyId: null });
                        log('WARN', `[/send][force=true] override precheck24h phone=${cleanPhone} (${precheckSend.minutesAgo}min ago)`);
                    }

                    // Check primo contatto: verifica onWhatsApp
                    const existingMsgs = dbQuery('SELECT COUNT(*) as cnt FROM messages WHERE dealer_id = ? AND direction = ?', [dealer_id || '', 'OUTBOUND']);
                    const isFirstContact = !existingMsgs[0] || existingMsgs[0].cnt === 0;
                    if (isFirstContact) {
                        const onWA = await HumanLike.checkOnWhatsApp(client, phone);
                        if (!onWA) {
                            res.writeHead(400, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({ error: 'number not on WhatsApp', phone }));
                            return;
                        }
                    }

                    // Simula typing prima dell'invio
                    await HumanLike.simulateTyping(client, chatId, message.length);
                    // S148 Patch 2: capture wa_msg_id reale dal return di sendMessage
                    const sentMsg = await client.sendMessage(chatId, message);
                    const waMsgIdReal = sentMsg?.id?._serialized || sentMsg?.id?.id || null;
                    log('INFO', `📤 sendMessage returned wa_msg_id=${waMsgIdReal} for ${chatId}`);
                    await HumanLike.clearPresence(client, chatId);
                    CONFIG.DAILY_SENT++;
                    incrementDailyStats('sent');
                    // S117: Long pause every 5 messages (anti-bot pattern)
                    if (CONFIG.DAILY_SENT % 5 === 0 && CONFIG.DAILY_SENT > 0) {
                        const pauseMs = Math.floor(Math.random() * 300000) + 300000; // 5-10 min
                        const pauseMin = Math.round(pauseMs / 60000);
                        const db2 = getDb();
                        db2.prepare("INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES ('pause_until', ?, datetime('now'))").run(String(Date.now() + pauseMs));
                        log('INFO', `S117 long pause: ${pauseMin}min after ${CONFIG.DAILY_SENT} msgs`);
                        sendTelegramAlert(`⏳ Pausa ${pauseMin}min (ogni 5 msg — pattern umano)`);
                    }

                    const msgId = `out_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                    // S148 Patch 2: wa_msg_id ora è il _serialized reale (matcha ack futuri)
                    const waMsgIdForDb = waMsgIdReal || msgId;
                    const now = TC.nowIT();

                    const db = getDb();
                    db.prepare(`INSERT OR IGNORE INTO messages
                        (id, dealer_id, dealer_name, phone_number, direction, body,
                         timestamp_it, timestamp_iso, wa_msg_id, processed)
                        VALUES (?, ?, '', ?, 'OUTBOUND', ?, datetime('now'), ?, ?, 1)`)
                      .run(msgId, dealer_id || 'MANUAL', chatId, message, now.toISOString(), waMsgIdForDb);

                    if (dealer_id) {
                        // S106: State machine update via Python
                        const tplId = template_id || 'DAY1_INTRO';
                        const postResult = runPostSendUpdate(dealer_id, tplId);

                        // current_step tracks the outreach step, not conversation_state
                        // DAY1* templates → 'DAY1_SENT', DAY3* → 'DAY3_SENT', etc.
                        const stepFromTemplate = tplId.startsWith('DAY1') ? 'DAY1_SENT'
                            : tplId.startsWith('DAY3') ? 'DAY3_SENT'
                            : tplId.startsWith('DAY7') ? 'DAY7_SENT'
                            : (postResult.ok ? postResult.new_state : 'DAY1_SENT');
                        db.prepare(`UPDATE conversations
                                SET current_step = ?,
                                    last_contact_at = datetime('now'),
                                    analyzed_at = datetime('now')
                                WHERE dealer_id = ?`).run(
                            stepFromTemplate,
                            dealer_id
                        );
                    }

                    log('INFO', `✅ INVIATO via HTTP: ${chatId} (${dealer_id || 'manual'})`);
                    sendTelegramAlert(`📤 *Day 1 INVIATO*\n👤 ${dealer_id || chatId}\n📱 ${chatId}\n📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`);

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ status: 'sent', msg_id: msgId, daily_sent: CONFIG.DAILY_SENT, first_contact: isFirstContact }));
                } catch (err) {
                    log('ERROR', 'Send failed:', err.message);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: err.message }));
                }
            });
            return;
        }

        // POST /send-multi — invia 2-3 messaggi separati con typing + delay (AMBRA style)
        if (req.method === 'POST' && req.url === '/send-multi') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const { phone, messages, dealer_id } = JSON.parse(body);
                    if (!phone || !messages || !Array.isArray(messages) || messages.length === 0) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'phone and messages (array) required' }));
                        return;
                    }
                    // Italian phone validation (same as /send)
                    const cleanMultiPhone = phone.replace(/[^0-9]/g, '');
                    if (!/^(39)?3\d{8,9}$/.test(cleanMultiPhone)) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'invalid italian phone number', phone }));
                        return;
                    }
                    if (messages.length > 5) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'max 5 messages per call' }));
                        return;
                    }
                    if (!HumanLike.isAllowedToSend(phone)) {
                        res.writeHead(403, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'outside business hours' }));
                        return;
                    }
                    if (CONFIG.DAILY_SENT + messages.length > CONFIG.DAILY_LIMIT) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit would be exceeded', daily_sent: CONFIG.DAILY_SENT, needed: messages.length }));
                        return;
                    }

                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;

                    // Check primo contatto
                    const existingMsgs = dbQuery('SELECT COUNT(*) as cnt FROM messages WHERE dealer_id = ? AND direction = ?', [dealer_id || '', 'OUTBOUND']);
                    const isFirstContact = !existingMsgs[0] || existingMsgs[0].cnt === 0;
                    if (isFirstContact) {
                        const onWA = await HumanLike.checkOnWhatsApp(client, phone);
                        if (!onWA) {
                            res.writeHead(400, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({ error: 'number not on WhatsApp', phone }));
                            return;
                        }
                    }

                    const msgIds = [];
                    const db = getDb();

                    for (let i = 0; i < messages.length; i++) {
                        const msg = messages[i];
                        if (!msg || typeof msg !== 'string') continue;

                        // Simula typing proporzionale
                        await HumanLike.simulateTyping(client, chatId, msg.length);

                        // Invia messaggio
                        await client.sendMessage(chatId, msg);
                        CONFIG.DAILY_SENT++;
                        incrementDailyStats('sent');

                        const msgId = `multi_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                        msgIds.push(msgId);

                        // Logga su DB
                        const now = TC.nowIT();
                        db.prepare(`INSERT OR IGNORE INTO messages
                            (id, dealer_id, dealer_name, phone_number, direction, body,
                             timestamp_it, timestamp_iso, wa_msg_id, processed)
                            VALUES (?, ?, '', ?, 'OUTBOUND', ?, datetime('now'), ?, ?, 1)`)
                          .run(msgId, dealer_id || 'MANUAL', chatId, msg, now.toISOString(), msgId);

                        // Delay log-normale tra messaggi (non dopo l'ultimo)
                        if (i < messages.length - 1) {
                            const interDelay = HumanLike.logNormalDelay(5000, 1500);
                            log('INFO', `Multi-msg delay: ${Math.round(interDelay/1000)}s prima del msg ${i+2}`);
                            await new Promise(r => setTimeout(r, interDelay));
                        }
                    }

                    // Clear typing dopo ultimo messaggio
                    await HumanLike.clearPresence(client, chatId);

                    // Aggiorna step
                    if (dealer_id) {
                        db.prepare(`UPDATE conversations
                                SET current_step = 'DAY1_SENT',
                                    last_contact_at = datetime('now'),
                                    analyzed_at = datetime('now')
                                WHERE dealer_id = ?`).run(dealer_id);
                    }

                    log('INFO', `✅ MULTI-INVIATO via HTTP: ${chatId} (${dealer_id || 'manual'}) — ${msgIds.length} msg`);
                    sendTelegramAlert(`📤 *Multi-msg INVIATO*\n👤 ${dealer_id || chatId}\n📱 ${chatId}\n💬 ${msgIds.length} messaggi\n📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`);

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ status: 'sent', msg_ids: msgIds, count: msgIds.length, daily_sent: CONFIG.DAILY_SENT }));
                } catch (err) {
                    log('ERROR', 'Send-multi failed:', err.message);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: err.message }));
                }
            });
            return;
        }

        // POST /send-voice — invia voice note WA via daemon (con anti-ban recording indicator)
        if (req.method === 'POST' && req.url === '/send-voice') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const { phone, audio_path, dealer_id } = JSON.parse(body);
                    if (!phone || !audio_path) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'phone and audio_path required' }));
                        return;
                    }
                    if (!HumanLike.isAllowedToSend(phone)) {
                        res.writeHead(403, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'outside business hours' }));
                        return;
                    }
                    if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit reached', daily_sent: CONFIG.DAILY_SENT }));
                        return;
                    }

                    const { MessageMedia } = require('whatsapp-web.js');
                    const media = MessageMedia.fromFilePath(audio_path);
                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;

                    // Simula recording indicator prima dell'invio
                    const estimatedDuration = Math.ceil(fs.statSync(audio_path).size / 4000);
                    await HumanLike.simulateRecording(client, chatId, estimatedDuration);

                    await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
                    await HumanLike.clearPresence(client, chatId);
                    CONFIG.DAILY_SENT++;
                    incrementDailyStats('sent');

                    const msgId = `voice_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                    log('INFO', `🎤 VOICE NOTE INVIATO: ${chatId} (${dealer_id || 'manual'}) — ${audio_path}`);
                    sendTelegramAlert(`🎤 *Voice Note INVIATO*\n👤 ${dealer_id || chatId}\n📱 ${chatId}\n📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`);

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ status: 'sent', msg_id: msgId, daily_sent: CONFIG.DAILY_SENT }));
                } catch (err) {
                    log('ERROR', 'Send-voice failed:', err.message);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: err.message }));
                }
            });
            return;
        }

        // POST /send-doc — invia documento (PDF, immagine) via WA
        if (req.method === 'POST' && req.url === '/send-doc') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const { phone, file_path, caption, dealer_id, force } = JSON.parse(body);
                    if (!phone || !file_path) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'phone and file_path required' }));
                        return;
                    }
                    // Italian phone validation
                    const cleanPhone = phone.replace(/[^0-9]/g, '');
                    if (!/^(39)?3\d{8,9}$/.test(cleanPhone)) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'invalid italian phone number' }));
                        return;
                    }
                    if (!fs.existsSync(file_path)) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'file not found', file_path }));
                        return;
                    }
                    // HITL approval gate (S189 + S190 fix code-review HIGH-1/HIGH-2)
                    // dealer_id RICHIESTO sempre — escape hatch esplicito force=true per admin manuale
                    // (pattern già usato in /send, vedi feedback_single_writer_principle_bridge.md)
                    if (!dealer_id && !force) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            error: 'dealer_id required (or force=true with explicit admin override)'
                        }));
                        return;
                    }
                    if (dealer_id) {
                        const db = getDb();
                        let row = db.prepare(
                            'SELECT id, approval_status FROM dossiers WHERE dealer_id = ? AND file_path = ?'
                        ).get(dealer_id, file_path);

                        if (!row) {
                            // Prima chiamata = auto-register PENDING (idempotent su UNIQUE constraint)
                            const ts = Math.floor(Date.now() / 1000);
                            let info;
                            try {
                                info = db.prepare(
                                    'INSERT INTO dossiers (dealer_id, file_path, created_ts, approval_status) VALUES (?, ?, ?, ?)'
                                ).run(dealer_id, file_path, ts, 'PENDING');
                            } catch (e) {
                                if (e.code === 'SQLITE_CONSTRAINT_UNIQUE') {
                                    // Concurrent INSERT race — re-query existing row, return current state
                                    row = db.prepare(
                                        'SELECT id, approval_status FROM dossiers WHERE dealer_id = ? AND file_path = ?'
                                    ).get(dealer_id, file_path);
                                    log('INFO', `🔒 DOSSIER race-resolved: id=${row.id} status=${row.approval_status}`);
                                    res.writeHead(403, { 'Content-Type': 'application/json' });
                                    res.end(JSON.stringify({
                                        error: 'dossier already registered (race)',
                                        approval_status: row.approval_status,
                                        dossier_id: row.id
                                    }));
                                    return;
                                }
                                throw e;
                            }
                            log('INFO', `🔒 DOSSIER REGISTERED PENDING: id=${info.lastInsertRowid} dealer=${dealer_id}`);
                            sendTelegramAlert(`🔒 *Dossier PENDING review*\n👤 ${dealer_id}\n📎 ${file_path.split('/').pop()}\n🔗 https://imac:8080/pending-dossiers`);
                            res.writeHead(403, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({
                                error: 'dossier registered, awaiting Luke approval',
                                approval_status: 'PENDING',
                                dossier_id: info.lastInsertRowid
                            }));
                            return;
                        }

                        if (row.approval_status !== 'APPROVED') {
                            res.writeHead(403, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({
                                error: 'dossier not approved',
                                approval_status: row.approval_status,
                                dossier_id: row.id
                            }));
                            return;
                        }
                        // APPROVED → fall through to existing send logic
                        log('INFO', `✅ DOSSIER APPROVED: id=${row.id} dealer=${dealer_id}`);
                    } else {
                        // force=true sans dealer_id — admin manual override, audit it
                        log('WARN', `⚠️  /send-doc FORCE override (no dealer_id) — file=${file_path.split('/').pop()}`);
                        sendTelegramAlert(`⚠️ */send-doc force override*\n📎 ${file_path.split('/').pop()}\n📞 ${phone}`);
                    }
                    if (!HumanLike.isAllowedToSend(phone)) {
                        res.writeHead(403, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'outside business hours' }));
                        return;
                    }
                    if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit reached', daily_sent: CONFIG.DAILY_SENT }));
                        return;
                    }

                    const { MessageMedia } = require('whatsapp-web.js');
                    const media = MessageMedia.fromFilePath(file_path);
                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;

                    await HumanLike.simulateTyping(client, chatId, 3);
                    await client.sendMessage(chatId, media, { caption: caption || '' });
                    await HumanLike.clearPresence(client, chatId);
                    CONFIG.DAILY_SENT++;
                    incrementDailyStats('sent');

                    const msgId = `doc_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                    log('INFO', `📄 DOC INVIATO: ${chatId} (${dealer_id || 'manual'}) — ${file_path}`);
                    sendTelegramAlert(`📄 *Doc INVIATO*\n👤 ${dealer_id || chatId}\n📎 ${file_path.split('/').pop()}\n📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`);

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ status: 'sent', msg_id: msgId, daily_sent: CONFIG.DAILY_SENT }));
                } catch (err) {
                    log('ERROR', 'Send-doc failed:', err.message);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: err.message }));
                }
            });
            return;
        }

        // POST /pause — S117 anti-ban
        if (req.method === 'POST' && req.url === '/pause') {
            const db = getDb();
            db.prepare("INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES ('status', 'paused', datetime('now'))").run();
            log('WARN', 'Agent PAUSED via API');
            sendTelegramAlert('⏸ *ARGOS Agent PAUSED* — nessun messaggio verrà inviato.');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'paused' }));
            return;
        }

        // POST /resume — S117 anti-ban
        if (req.method === 'POST' && req.url === '/resume') {
            const db = getDb();
            db.prepare("INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES ('status', 'active', datetime('now'))").run();
            db.prepare("INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES ('pause_until', '0', datetime('now'))").run();
            log('INFO', 'Agent RESUMED via API');
            sendTelegramAlert('▶️ *ARGOS Agent RESUMED* — operatività ripristinata.');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'active' }));
            return;
        }

        // GET /health-metrics — S117 block rate monitoring
        if (req.method === 'GET' && req.url === '/health-metrics') {
            const db = getDb();
            const today = new Date().toISOString().split('T')[0];
            const stats = db.prepare('SELECT * FROM daily_stats WHERE date = ?').get(today) || {};
            const sent = stats.sent || 0;
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                date: today,
                sent,
                delivered:     stats.delivered || 0,
                read_count:    stats.read_count || 0,
                replied:       stats.replied || 0,
                failed:        stats.failed || 0,
                blocked:       stats.blocked || 0,
                delivery_rate: sent > 0 ? ((stats.delivered||0)/sent).toFixed(3) : 'N/A',
                block_rate:    sent > 0 ? ((stats.blocked||0)/sent).toFixed(3) : 'N/A',
                reply_rate:    sent > 0 ? ((stats.replied||0)/sent).toFixed(3) : 'N/A',
                risk_level:    sent >= 20
                    ? ((stats.blocked||0)/sent > 0.02 ? 'RED'
                       : (stats.delivered||0)/sent < 0.85 ? 'YELLOW' : 'GREEN')
                    : 'INSUFFICIENT_DATA',
            }, null, 2));
            return;
        }

        // GET / or /status — health check
        const dynamicLimit = getDailyLimit();
        const agentStatus = getAgentStatus();
        const ctx = TC.buildAgentTimeContext();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status:           agentStatus === 'paused' ? 'PAUSED' : 'OK',
            daemon:           'argos-wa-daemon',
            version:          '2.4-antiban',
            now_it:           ctx.now_it,
            is_business_hours: ctx.is_business_hours,
            daily_sent:       CONFIG.DAILY_SENT,
            daily_limit:      dynamicLimit,
            daily_remaining:  Math.max(0, dynamicLimit - CONFIG.DAILY_SENT),
            agent_status:     agentStatus,
            uptime_sec:       Math.round(process.uptime()),
            wa_status:        QR_STATE.status,
            qr_available:     !!QR_STATE.qr,
        }, null, 2));
    }).listen(9191, '0.0.0.0', () => {
        log('INFO', 'HTTP server su http://0.0.0.0:9191 (health + /send + /qr)');
    });

    // ── Scheduler Multi-Step (Day 3 + Day 7) ─────────────────
    startScheduler(client);

    client.initialize();
    return client;
}

// ── VOICE NOTE TEMPLATES PER ARCHETIPO ──────────────────────
const VOICE_TEMPLATES = {
    NARCISO: `Buongiorno, sono Luca Ferretti di ARGOS Automotive. Ho riservato questa opportunità esclusivamente per la sua area. Selezioniamo veicoli premium in Germania e Belgio, solo per concessionari selezionati. Km certificati, storico verificato, garanzia costruttore UE. Se vuole, le invio un esempio concreto su misura per il suo stock. A presto.`,
    BARONE: `Buongiorno, mi permetto di ricontattarla con calma. Sono Luca Ferretti di ARGOS Automotive. Lavoriamo su misura per concessionari come il suo: selezione veicoli premium in Europa, con km certificati e storico verificato. Zero anticipi, paga solo a veicolo approvato. Se ha cinque minuti, le mostro come funziona. Buona giornata.`,
    RAGIONIERE: `Buongiorno, Luca Ferretti. Le invio i margini aggiornati: su una BMW X3 2021 dalla Germania, il risparmio medio è tra 4 e 7mila euro rispetto al mercato italiano. Km certificati, storico completo, zero anticipi. I numeri parlano da soli. Se vuole, le mando un caso concreto. A presto.`,
    TECNICO: `Buongiorno, Luca Ferretti di ARGOS Automotive. Ho la documentazione completa sulla nostra procedura: verifica chilometraggio con storico tagliandi, ispezione 100 punti, garanzia costruttore UE valida in Italia. Ogni veicolo è tracciato e certificato. Se le interessa, le invio un esempio dettagliato. Buona giornata.`,
    RELAZIONALE: `Buongiorno, ci tenevo a risentirla. Sono Luca Ferretti di ARGOS Automotive. So che i tempi dei concessionari sono stretti, per questo gestiamo tutto noi. Selezioniamo veicoli premium in Europa con km certificati e storico verificato. Zero complicazioni per lei. Quando ha un momento, mi faccia sapere. Un saluto.`,
    CONSERVATORE: `Buongiorno, Luca Ferretti di ARGOS Automotive. Volevo rassicurarla: nessun rischio, tutto documentato. Ogni veicolo ha km certificati, storico tagliandi verificato, garanzia costruttore UE. Paga solo a veicolo consegnato e approvato, zero anticipi. Se vuole, le mostro un caso reale con tutta la documentazione. Buona giornata.`,
    DELEGATORE: `Buongiorno, Luca Ferretti. Gestisco tutto io: selezione, verifica, documenti, trasporto. A lei serve solo dire sì. Zero anticipi, zero complicazioni, paga solo a veicolo approvato. Se le interessa, le invio un esempio e ci penso io a tutto il resto. Buona giornata.`,
    PERFORMANTE: `Buongiorno, Luca Ferretti. Ho un veicolo disponibile subito: BMW, Mercedes o Audi dalla Germania, pronto in 48 ore con km certificati e storico verificato. Zero anticipi, paga solo a consegna. Se mi dice cosa cerca, le mando la proposta entro domani. A presto.`,
    OPPORTUNISTA: `Buongiorno, Luca Ferretti. I numeri sono interessanti: margine medio tra 4 e 7mila euro su veicoli premium dalla Germania. Zero anticipi, il margine è tutto suo. Se vuole, le mando un caso concreto con i numeri reali. Buona giornata.`,
};

// Day 3 follow-up text templates
const DAY3_TEMPLATES = {
    NARCISO: `buongiorno, le scrivo solo perche ho trovato una macchina che secondo me fa al caso suo — config rara che in Italia non si trova facilmente.\n\nse ha 2 minuti le mando la scheda. nessun impegno\n\nLuca`,
    BARONE: `buongiorno, non voglio disturbare. le scrivo perche ho individuato un paio di auto che potrebbero interessarle — km certificati, storico completo.\n\nse e quando ha tempo, sono a disposizione\n\nLuca`,
    RAGIONIERE: `buongiorno, un dato veloce: su una BMW X3 2022 trovata in Germania questa settimana, il margine netto per il dealer e' circa €5.200 dopo trasporto e fee.\n\nse vuole i numeri completi, mi scriva\n\nLuca`,
    TECNICO: `buongiorno, ho preparato una scheda tecnica di esempio su una Mercedes GLC recente — allestimento completo, VIN check fatto, km verificati.\n\nse le interessa vedere il livello di documentazione, gliela mando\n\nLuca`,
    RELAZIONALE: `buongiorno, ci tenevo a farle sapere che resto a disposizione. nessuna fretta, quando vuole approfondire sono qui.\n\nbuona giornata\n\nLuca`,
    CONSERVATORE: `buongiorno, capisco che valutare un nuovo fornitore richiede tempo. per questo le confermo: zero rischi, zero anticipi. paga solo a macchina consegnata e approvata.\n\nse ha domande, sono qui\n\nLuca`,
    DELEGATORE: `buongiorno, se decide di provare gestisco tutto io — trovo la macchina, verifico, preparo documenti, organizzo trasporto. a lei basta dirmi cosa cerca\n\nLuca`,
    PERFORMANTE: `buongiorno, ho 3 auto disponibili subito in Germania. se mi dice marca e budget, le mando la proposta entro oggi\n\nLuca`,
    OPPORTUNISTA: `buongiorno, i margini di questa settimana sono ancora piu interessanti. su un'Audi Q5 2022 dalla Germania: margine netto circa €6.000 per il dealer.\n\nse vuole i numeri completi, mi scriva\n\nLuca`,
};

// ── Genera voice note con edge-tts ──────────────────────────
function generateVoiceNote(text, outputPath) {
    try {
        // edge-tts con voce italiana DiegoNeural
        execSync(
            `${process.env.HOME}/Library/Python/3.9/bin/edge-tts --voice it-IT-DiegoNeural --rate "+5%" --text "${text.replace(/"/g, '\\"')}" --write-media "${outputPath}"`,
            { timeout: 30000, stdio: 'pipe' }
        );
        return fs.existsSync(outputPath);
    } catch (e) {
        log('ERROR', 'generateVoiceNote failed:', e.message);
        return false;
    }
}

// ── Scheduler: controlla dealer che necessitano follow-up ───
function startScheduler(client) {
    log('INFO', 'Scheduler multi-step avviato (ogni 30 min)');

    async function checkScheduledActions() {
        if (!TC.isBusinessHours()) {
            log('INFO', 'Scheduler: fuori orario business, skip');
            return;
        }

        checkDailyReset();
        const db = getDb();

        // Trova dealer che necessitano Day 3 follow-up
        const day3Candidates = db.prepare(`
            SELECT * FROM conversations
            WHERE current_step = 'DAY1_SENT'
              AND last_contact_at IS NOT NULL
              AND julianday('now') - julianday(last_contact_at) >= 3
              AND julianday('now') - julianday(last_contact_at) < 7
        `).all();

        for (const dealer of day3Candidates) {
            if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                log('WARN', 'Scheduler: daily limit raggiunto, stop');
                break;
            }

            const template = DAY3_TEMPLATES[dealer.persona_type] || DAY3_TEMPLATES.RAGIONIERE;
            const phone = (dealer.phone_number || '').replace(/[+\s-]/g, '');
            if (!phone) continue;

            // S173: Day3 → bridge (single writer principle D-22)
            // client.sendMessage diretto rimosso — bridge pollBridgeOutbound gestisce send
            try {
                const { inserted } = insertBridgeOutbound({
                    dealId:  dealer.dealer_id,
                    role:    'dealer',
                    phone,
                    phase:   'day3',
                    lang:    'it',
                    body:    template,
                    state:   'DAY1_SENT',
                });
                if (inserted) {
                    // Auto-approve: Day3 è scheduling automatico, non richiede HITL
                    const bdb = getBridgeDb();
                    if (bdb) {
                        bdb.prepare(`
                            UPDATE bridge_outbound
                            SET approved_ts = strftime('%s','now')
                            WHERE deal_id = ? AND target_phone = ? AND template_phase = 'day3'
                              AND sent_ts IS NULL AND approved_ts IS NULL
                        `).run(dealer.dealer_id, phone);
                    }

                    db.prepare(`UPDATE conversations
                        SET current_step = 'DAY3_SENT', last_contact_at = datetime('now'), analyzed_at = datetime('now')
                        WHERE dealer_id = ?`).run(dealer.dealer_id);

                    log('INFO', `📤 DAY 3 QUEUED (bridge): ${dealer.dealer_name} (${dealer.persona_type})`);
                    sendTelegramAlert(
                        `📤 *Day 3 Follow-up in coda bridge*\n` +
                        `👤 ${dealer.dealer_name} (${dealer.persona_type})\n` +
                        `📱 ${phone}\n` +
                        `📊 prossimo poll ~30s`
                    );
                } else {
                    log('INFO', `[bridge][dedup] Day3 già in coda per ${dealer.dealer_id} — skip`);
                }
            } catch (e) {
                log('ERROR', `Day 3 bridge insert failed for ${dealer.dealer_id}:`, e.message);
            }
        }

        // Trova dealer che necessitano Day 7 voice note
        const day7Candidates = db.prepare(`
            SELECT * FROM conversations
            WHERE current_step IN ('DAY3_SENT', 'DAY1_SENT')
              AND last_contact_at IS NOT NULL
              AND julianday('now') - julianday(last_contact_at) >= 4
              AND current_step = 'DAY3_SENT'
        `).all();

        // Anche dealer Day1 senza risposta dopo 7 giorni totali
        const day7FromDay1 = db.prepare(`
            SELECT * FROM conversations
            WHERE current_step = 'DAY1_SENT'
              AND last_contact_at IS NOT NULL
              AND julianday('now') - julianday(last_contact_at) >= 7
        `).all();

        const allDay7 = [...day7Candidates, ...day7FromDay1];
        const seenIds = new Set();

        for (const dealer of allDay7) {
            if (seenIds.has(dealer.dealer_id)) continue;
            seenIds.add(dealer.dealer_id);

            if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                log('WARN', 'Scheduler: daily limit raggiunto, stop');
                break;
            }

            const voiceText = VOICE_TEMPLATES[dealer.persona_type] || VOICE_TEMPLATES.RAGIONIERE;
            const phone = (dealer.phone_number || '').replace(/[+\s-]/g, '');
            if (!phone) continue;

            const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;
            const voicePath = `/tmp/argos_voice_DAY7_${dealer.dealer_id}.mp3`;

            // S173: precheck 24h — evita duplicati Day7 se inviato di recente
            // Day7 voice = MessageMedia (binario) — bridge schema solo body TEXT (BACKLOG #S172-1)
            // Usa client.sendMessage diretto con force=true esplicito + precheck 24h
            const precheck7 = bridgePrecheck24h(phone);
            if (precheck7.recent) {
                // force=true non è settato in scheduler automatico — rispetta D-07 HITL
                // Se il dealer ha ricevuto un msg nelle ultime 24h, skippa e avvisa
                log('WARN', `[Day7][precheck] skip ${dealer.dealer_id} — sent ${precheck7.minutesAgo}min ago (< 24h). Retry next cycle.`);
                sendTelegramAlert(
                    `⚠️ *Day 7 VOICE SKIP* — precheck 24h\n` +
                    `👤 ${dealer.dealer_name}\n` +
                    `📱 ${phone}\n` +
                    `_Ultimo invio: ${precheck7.minutesAgo}min fa. Ritenterò al prossimo ciclo._\n` +
                    `_Per forzare: usa force=true via /send HTTP con API key_`
                );
                continue;
            }

            // Genera voice note
            const generated = generateVoiceNote(voiceText, voicePath);
            if (!generated) {
                log('ERROR', `Voice note generation failed for ${dealer.dealer_id}`);
                continue;
            }

            try {
                const { MessageMedia } = require('whatsapp-web.js');
                const media = MessageMedia.fromFilePath(voicePath);

                // Anti-ban: simula recording indicator prima dell'invio
                await HumanLike.simulateRecording(client, chatId, 20);
                // Day7 voice — callsite diretto autorizzato (BACKLOG #S172-1: bridge extension pending)
                // force=true implicito poiché precheck 24h già superato sopra
                log('INFO', `[Day7] force=true implicit (precheck 24h passed) — dealer=${dealer.dealer_id}`);
                await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
                await HumanLike.clearPresence(client, chatId);
                CONFIG.DAILY_SENT++;
                incrementDailyStats('sent');

                db.prepare(`UPDATE conversations
                    SET current_step = 'DAY7_VOICE_SENT', last_contact_at = datetime('now'), analyzed_at = datetime('now')
                    WHERE dealer_id = ?`).run(dealer.dealer_id);

                log('INFO', `🎤 DAY 7 VOICE INVIATO: ${dealer.dealer_name} (${dealer.persona_type})`);
                sendTelegramAlert(
                    `🎤 *Day 7 Voice Note INVIATO*\n` +
                    `👤 ${dealer.dealer_name} (${dealer.persona_type})\n` +
                    `📱 ${chatId}\n` +
                    `📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`
                );

                // Cleanup voice file
                try { fs.unlinkSync(voicePath); } catch (_) {}

                // Anti-ban: delay log-normale tra voice note (media 5 min)
                const sleepMs = HumanLike.logNormalDelay(300000, 90000);
                log('INFO', `Day7 voice anti-ban delay: ${Math.round(sleepMs/1000)}s`);
                await new Promise(r => setTimeout(r, sleepMs));
            } catch (e) {
                log('ERROR', `Day 7 voice send failed for ${dealer.dealer_id}:`, e.message);
            }
        }

        if (day3Candidates.length === 0 && allDay7.length === 0) {
            log('INFO', 'Scheduler: nessun follow-up necessario');
        }
    }

    // Prima esecuzione dopo 2 minuti dall'avvio
    setTimeout(() => {
        checkScheduledActions().catch(e => log('ERROR', 'Scheduler error:', e.message));
    }, 2 * 60 * 1000);

    // Poi ogni 30 minuti
    setInterval(() => {
        checkScheduledActions().catch(e => log('ERROR', 'Scheduler error:', e.message));
    }, CONFIG.SCHEDULER_INTERVAL);
}

// S117: Block rate monitoring — every hour
setInterval(() => {
    const db = getDb();
    const today = new Date().toISOString().split('T')[0];
    try {
        const stats = db.prepare('SELECT sent, blocked, delivered, replied FROM daily_stats WHERE date = ?').get(today);
        if (!stats || stats.sent < 20) return; // sample too small
        const blockRate = stats.blocked / stats.sent;
        if (blockRate > 0.02) {
            log('ERROR', `BLOCK RATE CRITICO: ${(blockRate*100).toFixed(1)}% > 2%`);
            sendTelegramAlert(`🚨 *ARGOS AUTO-STOP*\nBlock rate: ${(blockRate*100).toFixed(1)}% > 2%\nInviati: ${stats.sent} | Bloccati: ${stats.blocked}\nNumero WA a rischio BAN. Agent fermato.\n_/resume per riprendere dopo verifica._`);
            db.prepare("INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES ('status', 'paused', datetime('now'))").run();
        }
        const deliveryRate = stats.delivered / stats.sent;
        if (deliveryRate < 0.85 && stats.sent >= 20) {
            sendTelegramAlert(`⚠️ Delivery rate bassa: ${(deliveryRate*100).toFixed(1)}% < 85%`);
        }
    } catch (e) {
        log('WARN', `Block rate check: ${e.message}`);
    }
}, 60 * 60 * 1000); // every hour

// ── Health Monitor: verifica connessione WA ogni 5 min ──────
let _lastHealthOk = Date.now();
let _healthAlertSent = false;

setInterval(async () => {
    try {
        if (!_waClient) return;
        const state = await _waClient.getState();
        if (state === 'CONNECTED') {
            _lastHealthOk = Date.now();
            if (_healthAlertSent) {
                sendTelegramAlert('✅ *WA riconnesso* — sessione attiva');
                _healthAlertSent = false;
            }
        } else {
            const downMin = Math.round((Date.now() - _lastHealthOk) / 60000);
            if (!_healthAlertSent && downMin >= 5) {
                sendTelegramAlert(`🚨 *WA DISCONNESSO* da ${downMin} min!\nStato: ${state}\n\n_Controllare sessione su http://192.168.1.2:9191/qr_`);
                _healthAlertSent = true;
                log('ERROR', `Health check: WA disconnesso da ${downMin} min, stato: ${state}`);
            }
        }
    } catch (e) {
        log('WARN', `Health check failed: ${e.message}`);
    }
}, 5 * 60 * 1000); // ogni 5 minuti

// ── Entry point ──────────────────────────────────────────────
const waClient = initClient();

// Graceful shutdown (CT-20 fix: flush buffers, cleanup Chrome)
async function gracefulShutdown(signal) {
    log('INFO', `${signal} ricevuto — shutdown graceful`);
    try {
        // Flush pending message buffers
        if (typeof MESSAGE_BUFFER !== 'undefined') {
            for (const [dealerId] of MESSAGE_BUFFER) {
                log('INFO', `Flushing buffer for ${dealerId}`);
                try { flushBuffer(dealerId); } catch (_) {}
            }
        }
    } catch (_) {}
    try { await waClient.destroy(); } catch (_) {}
    try { if (_db) _db.close(); } catch (_) {}
    // Kill orphan Chrome processes (CT-03 fix)
    try { execSync('pkill -f "chromium.*--user-data-dir.*argos" 2>/dev/null || true', { timeout: 3000 }); } catch (_) {}
    process.exit(0);
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

process.on('unhandledRejection', (reason) => {
    log('ERROR', 'UnhandledRejection:', reason?.message || reason);
    sendTelegramAlert(`⚠️ *UnhandledRejection*\n${String(reason?.message || reason).slice(0, 500)}`);
});
