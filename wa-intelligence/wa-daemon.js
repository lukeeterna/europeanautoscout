/**
 * wa-daemon.js — ARGOS™ WA Intelligence Daemon
 * CoVe 2026 | Enterprise Grade | PM2 Managed
 *
 * RESPONSABILITÀ:
 *   - Mantiene la sessione WhatsApp SEMPRE attiva (non si chiude mai)
 *   - Ascolta TUTTI gli eventi WA in real-time
 *   - Su ogni messaggio in arrivo: log → DuckDB → analyzer → Telegram alert
 *   - Gestisce la coda di invio (anti-ban sleep obbligatorio)
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

const TC = require('./time-context.js');

// ── Configurazione ────────────────────────────────────────────
const CONFIG = {
    SESSION_ID:    'argosautomotive',
    DB_PATH:       process.env.DB_PATH
                   || `${process.env.HOME}/Documents/app-antigravity-auto/dealer_network.duckdb`,
    TELEGRAM_SCRIPT: path.join(__dirname, 'telegram-handler.py'),
    ANALYZER_SCRIPT: path.join(__dirname, 'response-analyzer.py'),
    PYTHON_BIN:    'python3',
    SEND_QUEUE:    [],          // coda messaggi in uscita
    DAILY_SENT:    0,
    DAILY_LIMIT:   30,
    DAILY_RESET:   null,        // data ultimo reset
    LOG_FILE:      '/tmp/argos-wa-daemon.log',
};

// ── Utility log con timestamp IT ────────────────────────────
function log(level, ...args) {
    const ts  = TC.formatIT(TC.nowIT());
    const msg = `[${ts}][${level}] ${args.join(' ')}`;
    console.log(msg);
    try {
        fs.appendFileSync(CONFIG.LOG_FILE, msg + '\n');
    } catch (_) {}
}

// ── DuckDB helpers (via python3 one-liner) ─────────────────
function dbExec(sql, params = {}) {
    const paramStr = JSON.stringify(params).replace(/"/g, '\\"');
    const script = `
import duckdb, json, sys
con = duckdb.connect("${CONFIG.DB_PATH}")
try:
    params = json.loads('${paramStr}') if '${paramStr}' != '{}' else {}
    con.execute("""${sql}""", list(params.values()) if params else [])
    con.commit()
    print("OK")
except Exception as e:
    print("ERR:" + str(e), file=sys.stderr)
    sys.exit(1)
finally:
    con.close()
`;
    try {
        return execSync(`${CONFIG.PYTHON_BIN} -c "${script.replace(/\n/g, '; ')}"`,
                        { encoding: 'utf8', timeout: 10000 }).trim();
    } catch (e) {
        log('ERROR', 'dbExec failed:', e.message);
        return null;
    }
}

function dbQuery(sql) {
    const script = `
import duckdb, json
con = duckdb.connect("${CONFIG.DB_PATH}")
try:
    rows = con.execute("""${sql}""").fetchall()
    cols = [d[0] for d in con.description] if con.description else []
    result = [dict(zip(cols, row)) for row in rows]
    print(json.dumps(result, default=str))
except Exception as e:
    print("[]")
finally:
    con.close()
`;
    try {
        const raw = execSync(`${CONFIG.PYTHON_BIN} -c "${script.replace(/\n/g, '; ')}"`,
                             { encoding: 'utf8', timeout: 10000 }).trim();
        return JSON.parse(raw);
    } catch {
        return [];
    }
}

// ── Inizializza schema DB se non esiste ──────────────────────
function ensureSchema() {
    const ddl = `
        CREATE TABLE IF NOT EXISTS messages (
            id              VARCHAR PRIMARY KEY,
            dealer_id       VARCHAR,
            dealer_name     VARCHAR,
            phone_number    VARCHAR,
            direction       VARCHAR,   -- INBOUND | OUTBOUND
            body            TEXT,
            timestamp_it    TIMESTAMP,
            timestamp_iso   VARCHAR,
            wa_msg_id       VARCHAR,
            processed       BOOLEAN DEFAULT FALSE,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pending_replies (
            id              VARCHAR PRIMARY KEY,
            dealer_id       VARCHAR,
            dealer_name     VARCHAR,
            inbound_msg_id  VARCHAR,
            reply_text      TEXT,
            reply_label     VARCHAR,   -- es. POSITIVE_ACK, OBJECTION_OBJ2
            cialdini_trigger VARCHAR,
            approved        BOOLEAN DEFAULT NULL,   -- NULL=pendente
            sent            BOOLEAN DEFAULT FALSE,
            scheduled_at    TIMESTAMP,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS scheduled_actions (
            id              VARCHAR PRIMARY KEY,
            dealer_id       VARCHAR,
            dealer_name     VARCHAR,
            action_type     VARCHAR,   -- WA_DAY7, EMAIL_DAY7, WA_DAY12 ...
            due_at          TIMESTAMP,
            status          VARCHAR DEFAULT 'PENDING',  -- PENDING|FIRED|CANCELLED
            fired_at        TIMESTAMP,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id              VARCHAR PRIMARY KEY,
            event_type      VARCHAR,
            dealer_id       VARCHAR,
            payload         JSON,
            timestamp_it    TIMESTAMP,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    `;
    // Esegui statement per statement
    ddl.split(';').map(s => s.trim()).filter(Boolean).forEach(stmt => dbExec(stmt));
    log('INFO', 'Schema DB verificato.');
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
    const rows = dbQuery(`
        SELECT *
        FROM conversations
        WHERE REPLACE(REPLACE(phone_number, '+', ''), ' ', '') = '${normalized}'
           OR REPLACE(REPLACE(phone_number, '+', ''), ' ', '') LIKE '%${normalized.slice(-9)}'
        LIMIT 1
    `);
    return rows[0] || null;
}

// ── Logga messaggio in arrivo su DB ──────────────────────────
function persistInboundMessage(msg, dealer) {
    const now  = TC.nowIT();
    const id   = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    dbExec(`
        INSERT OR IGNORE INTO messages
            (id, dealer_id, dealer_name, phone_number, direction, body,
             timestamp_it, timestamp_iso, wa_msg_id, processed)
        VALUES
            ('${id}',
             '${dealer?.dealer_id || 'UNKNOWN'}',
             '${(dealer?.dealer_name || msg.from).replace(/'/g, "''")}',
             '${msg.from}',
             'INBOUND',
             '${msg.body.replace(/'/g, "''")}',
             CURRENT_TIMESTAMP,
             '${now.toISOString()}',
             '${msg.id?.id || id}',
             FALSE)
    `);
    return id;
}

// ── Aggiorna stato conversazione al DB principale ────────────
function updateConversationState(dealerId, newStep) {
    dbExec(`
        UPDATE conversations
        SET current_step     = '${newStep}',
            last_contact_at  = CURRENT_TIMESTAMP,
            analyzed_at      = CURRENT_TIMESTAMP
        WHERE dealer_id = '${dealerId}'
    `);
}

// ── Chiama analyzer asincrono ────────────────────────────────
function triggerAnalyzer(inboundMsgId, msgBody, dealer) {
    const ctx    = TC.buildAgentTimeContext(dealer || {});
    const ctxStr = JSON.stringify(ctx).replace(/'/g, "\\'");

    log('INFO', `Triggering analyzer per msg: ${inboundMsgId}`);

    const child = spawn(CONFIG.PYTHON_BIN, [
        CONFIG.ANALYZER_SCRIPT,
        '--msg-id',     inboundMsgId,
        '--msg-body',   msgBody,
        '--dealer-id',  dealer?.dealer_id || 'UNKNOWN',
        '--dealer-name', dealer?.dealer_name || 'Sconosciuto',
        '--persona',    dealer?.persona_type || 'RAGIONIERE',
        '--step',       dealer?.current_step || 'UNKNOWN',
        '--db-path',    CONFIG.DB_PATH,
        '--time-ctx',   ctxStr,
    ], {
        detached: true,
        stdio:    'ignore',
    });
    child.unref(); // non blocca il daemon
}

// ── Invia alert Telegram IMMEDIATO (non async) ───────────────
function sendTelegramAlert(text, replyMarkup = null) {
    const markupStr = replyMarkup ? JSON.stringify(replyMarkup) : '{}';
    try {
        execSync(`${CONFIG.PYTHON_BIN} ${CONFIG.TELEGRAM_SCRIPT} alert \
            "${text.replace(/"/g, '\\"')}" \
            '${markupStr}'`,
            { timeout: 10000, stdio: 'pipe' });
        log('INFO', 'Telegram alert inviato');
    } catch (e) {
        log('ERROR', 'Telegram alert fallito:', e.message);
    }
}

// ── Handler principale: messaggio in arrivo ──────────────────
async function handleInboundMessage(msg) {
    const now    = TC.nowIT();
    const timeCtx = TC.formatContextForLog(TC.buildAgentTimeContext());

    log('INFO', `━━━ MESSAGGIO IN ARRIVO ━━━`);
    log('INFO', `Da: ${msg.from}`);
    log('INFO', `Corpo: ${msg.body.slice(0, 120)}`);
    log('INFO', timeCtx);

    // 1. Cerca dealer nel DB
    const dealer = lookupDealer(msg.from);

    // 2. Logga sul DB
    const msgId = persistInboundMessage(msg, dealer);

    // 3. Aggiorna audit log
    dbExec(`
        INSERT OR IGNORE INTO audit_log (id, event_type, dealer_id, payload, timestamp_it)
        VALUES (
            'audit_${Date.now()}',
            'INBOUND_MESSAGE',
            '${dealer?.dealer_id || 'UNKNOWN'}',
            '${JSON.stringify({from: msg.from, body: msg.body.slice(0,200), msgId}).replace(/'/g,"''")}',
            CURRENT_TIMESTAMP
        )
    `);

    // 4. Alert Telegram immediato con contesto temporale
    const dealerLabel = dealer
        ? `*${dealer.dealer_name}* (${dealer.persona_type || '?'}) — step: ${dealer.current_step || '?'}`
        : `*SCONOSCIUTO* — ${msg.from}`;

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
        `⏳ Analisi psicologica in corso...`,
    ].filter(Boolean).join('\n');

    sendTelegramAlert(alertText);

    // 5. Aggiorna step se dealer noto
    if (dealer) {
        updateConversationState(dealer.dealer_id, `RESPONSE_RECEIVED_${Date.now()}`);
    }

    // 6. Avvia analisi asincrona (genera candidate replies)
    triggerAnalyzer(msgId, msg.body, dealer);
}

// ── Inizializza client WA ────────────────────────────────────
function initClient() {
    log('INFO', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    log('INFO', 'ARGOS™ WA Intelligence Daemon v2.0');
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

    // ── Events ──────────────────────────────────────────────

    client.on('qr', () => {
        log('WARN', 'QR richiesto — sessione scaduta. Avvia send_qr_server.js per re-auth.');
        sendTelegramAlert('⚠️ *WA Daemon*: sessione scaduta. Richiesta nuova autenticazione QR.');
    });

    client.on('authenticated', () => {
        log('INFO', '✅ Sessione autenticata');
    });

    client.on('auth_failure', (msg) => {
        log('ERROR', 'Auth failure:', msg);
        sendTelegramAlert(`🔴 *WA Daemon Auth Failure*: ${msg}`);
    });

    client.on('ready', () => {
        const ctx = TC.buildAgentTimeContext();
        log('INFO', '✅ Client PRONTO — in ascolto');
        log('INFO', TC.formatContextForLog(ctx));
        sendTelegramAlert(
            `✅ *ARGOS™ WA Daemon ONLINE*\n` +
            `📅 ${TC.formatIT(TC.nowIT())}\n` +
            `🕐 Business hours: ${TC.isBusinessHours() ? 'SÌ' : 'NO'}\n` +
            `📊 Daily limit: ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`
        );
    });

    client.on('disconnected', (reason) => {
        log('ERROR', 'Disconnesso:', reason);
        sendTelegramAlert(`🔴 *WA Daemon disconnesso*: ${reason}\nPM2 riavvierà automaticamente.`);
        // PM2 gestisce il restart — non chiamiamo process.exit() qui
        // per permettere il cleanup. PM2 vede il crash e restarta.
        setTimeout(() => process.exit(1), 3000);
    });

    // ── Messaggi in arrivo ───────────────────────────────────
    client.on('message', async (msg) => {
        // Ignora messaggi propri e di gruppo
        if (msg.fromMe)                        return;
        if (msg.from.endsWith('@g.us'))        return;  // gruppo WA
        if (msg.type === 'e2e_notification')   return;

        checkDailyReset();
        await handleInboundMessage(msg);
    });

    // ── Message ACK (conferma lettura) ───────────────────────
    client.on('message_ack', (msg, ack) => {
        // ack: 1=sent, 2=delivered, 3=read, 4=played
        if (ack === 3) {
            const now = TC.formatIT(TC.nowIT());
            log('INFO', `✓✓ LETTO: ${msg.to} — ${now}`);
            dbExec(`
                UPDATE messages
                SET processed = TRUE
                WHERE wa_msg_id = '${msg.id?.id || ''}'
            `);
            dbExec(`
                INSERT OR IGNORE INTO audit_log (id, event_type, dealer_id, payload, timestamp_it)
                VALUES (
                    'ack_${Date.now()}',
                    'MSG_READ_ACK',
                    'UNKNOWN',
                    '{"to":"${msg.to}","ack":3}',
                    CURRENT_TIMESTAMP
                )
            `);
        }
    });

    // ── Health check HTTP (porta 9191) ───────────────────────
    http.createServer((req, res) => {
        const ctx = TC.buildAgentTimeContext();
        checkDailyReset();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status:           'OK',
            daemon:           'argos-wa-daemon',
            version:          '2.0',
            now_it:           ctx.now_it,
            is_business_hours: ctx.is_business_hours,
            daily_sent:       CONFIG.DAILY_SENT,
            daily_limit:      CONFIG.DAILY_LIMIT,
            daily_remaining:  CONFIG.DAILY_LIMIT - CONFIG.DAILY_SENT,
            uptime_sec:       Math.round(process.uptime()),
        }, null, 2));
    }).listen(9191, '127.0.0.1', () => {
        log('INFO', 'Health check HTTP su http://127.0.0.1:9191');
    });

    client.initialize();
    return client;
}

// ── Entry point ──────────────────────────────────────────────
const waClient = initClient();

// Graceful shutdown
process.on('SIGTERM', async () => {
    log('INFO', 'SIGTERM ricevuto — shutdown graceful');
    try { await waClient.destroy(); } catch (_) {}
    process.exit(0);
});

process.on('unhandledRejection', (reason) => {
    log('ERROR', 'UnhandledRejection:', reason?.message || reason);
});
