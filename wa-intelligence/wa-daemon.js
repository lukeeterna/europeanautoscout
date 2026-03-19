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

// ── Configurazione ────────────────────────────────────────────
const CONFIG = {
    SESSION_ID:    process.env.WA_CLIENT_ID || 'argos-business',
    DB_PATH:       process.env.DB_PATH
                   || `${process.env.HOME}/Documents/app-antigravity-auto/dealer_network.sqlite`,
    TELEGRAM_SCRIPT: path.join(__dirname, 'telegram-handler.py'),
    ANALYZER_SCRIPT: path.join(__dirname, 'response-analyzer.py'),
    PYTHON_BIN:    'python3',
    SEND_QUEUE:    [],          // coda messaggi in uscita
    DAILY_SENT:    0,
    DAILY_LIMIT:   30,
    DAILY_RESET:   null,        // data ultimo reset
    LOG_FILE:      '/tmp/argos-wa-daemon.log',
    SCHEDULER_INTERVAL: 30 * 60 * 1000,  // 30 minuti
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
    try {
        db.prepare(`
            INSERT OR IGNORE INTO messages
                (id, dealer_id, dealer_name, phone_number, direction, body,
                 timestamp_it, timestamp_iso, wa_msg_id, processed)
            VALUES (?, ?, ?, ?, 'INBOUND', ?, datetime('now'), ?, ?, 0)
        `).run(
            id,
            dealer?.dealer_id || 'UNKNOWN',
            dealer?.dealer_name || msg.from,
            msg.from,
            msg.body,
            now.toISOString(),
            msg.id?.id || id
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

// ── Chiama analyzer asincrono ────────────────────────────────
function triggerAnalyzer(inboundMsgId, msgBody, dealer) {
    const ctx    = TC.buildAgentTimeContext(dealer || {});
    const ctxStr = JSON.stringify(ctx).replace(/'/g, "\\'");

    log('INFO', `Triggering analyzer per msg: ${inboundMsgId}`);

    // Log analyzer output to file per debug (S65 fix)
    const analyzerLogFd = fs.openSync('/tmp/argos-analyzer.log', 'a');

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
        stdio:    ['ignore', analyzerLogFd, analyzerLogFd],
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

    // 1. Cerca dealer nel DB — SOLO dealer noti in pipeline
    const dealer = lookupDealer(msg.from);
    if (!dealer) {
        log('INFO', `⏭️ Messaggio da numero non in pipeline: ${msg.from} — ignorato`);
        return;
    }

    log('INFO', `━━━ MESSAGGIO IN ARRIVO ━━━`);
    log('INFO', `Da: ${msg.from} → ${dealer.dealer_name} (${dealer.dealer_id})`);
    log('INFO', `Corpo: ${msg.body.slice(0, 120)}`);
    log('INFO', timeCtx);

    // 2. Logga sul DB
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
        setTimeout(() => process.exit(1), 3000);
    });

    // ── Messaggi in arrivo ───────────────────────────────────
    client.on('message', async (msg) => {
        // Ignora messaggi non rilevanti
        if (msg.fromMe)                        return;
        if (msg.from.endsWith('@g.us'))        return;  // gruppo WA
        if (msg.from === 'status@broadcast')   return;  // stati WA (storie)
        if (msg.from.endsWith('@newsletter'))  return;  // canali WA
        if (msg.from.endsWith('@broadcast'))   return;  // broadcast generico
        if (msg.type === 'e2e_notification')   return;
        if (!msg.from.endsWith('@c.us'))       return;  // solo chat 1:1 reali

        checkDailyReset();
        await handleInboundMessage(msg);
    });

    // ── Message ACK (conferma lettura) ───────────────────────
    client.on('message_ack', (msg, ack) => {
        // ack: 1=sent, 2=delivered, 3=read, 4=played
        if (ack === 3) {
            const now = TC.formatIT(TC.nowIT());
            log('INFO', `✓✓ LETTO: ${msg.to} — ${now}`);
            const db = getDb();
            try {
                db.prepare('UPDATE messages SET processed = 1 WHERE wa_msg_id = ?')
                  .run(msg.id?.id || '');
                db.prepare(`
                    INSERT OR IGNORE INTO audit_log (id, event_type, dealer_id, payload, timestamp_it)
                    VALUES (?, 'MSG_READ_ACK', 'UNKNOWN', ?, datetime('now'))
                `).run(`ack_${Date.now()}`, JSON.stringify({to: msg.to, ack: 3}));
            } catch (e) {
                log('ERROR', 'message_ack db failed:', e.message);
            }
        }
    });

    // ── HTTP Server (porta 9191): health + send ─────────────
    http.createServer(async (req, res) => {
        checkDailyReset();

        // POST /send — invia messaggio WA via daemon
        if (req.method === 'POST' && req.url === '/send') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', async () => {
                try {
                    const { phone, message, dealer_id } = JSON.parse(body);
                    if (!phone || !message) {
                        res.writeHead(400, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'phone and message required' }));
                        return;
                    }
                    if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit reached', daily_sent: CONFIG.DAILY_SENT }));
                        return;
                    }

                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;
                    await client.sendMessage(chatId, message);
                    CONFIG.DAILY_SENT++;

                    const msgId = `out_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                    const now = TC.nowIT();

                    // Logga su DB
                    const db = getDb();
                    db.prepare(`INSERT OR IGNORE INTO messages
                        (id, dealer_id, dealer_name, phone_number, direction, body,
                         timestamp_it, timestamp_iso, wa_msg_id, processed)
                        VALUES (?, ?, '', ?, 'OUTBOUND', ?, datetime('now'), ?, ?, 1)`)
                      .run(msgId, dealer_id || 'MANUAL', chatId, message, now.toISOString(), msgId);

                    // Aggiorna step se dealer_id fornito
                    if (dealer_id) {
                        db.prepare(`UPDATE conversations
                                SET current_step = 'DAY1_SENT',
                                    last_contact_at = datetime('now'),
                                    analyzed_at = datetime('now')
                                WHERE dealer_id = ?`).run(dealer_id);
                    }

                    log('INFO', `✅ INVIATO via HTTP: ${chatId} (${dealer_id || 'manual'})`);
                    sendTelegramAlert(`📤 *Day 1 INVIATO*\n👤 ${dealer_id || chatId}\n📱 ${chatId}\n📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`);

                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ status: 'sent', msg_id: msgId, daily_sent: CONFIG.DAILY_SENT }));
                } catch (err) {
                    log('ERROR', 'Send failed:', err.message);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: err.message }));
                }
            });
            return;
        }

        // POST /send-voice — invia voice note WA via daemon
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
                    if (CONFIG.DAILY_SENT >= CONFIG.DAILY_LIMIT) {
                        res.writeHead(429, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'daily limit reached', daily_sent: CONFIG.DAILY_SENT }));
                        return;
                    }

                    const { MessageMedia } = require('whatsapp-web.js');
                    const media = MessageMedia.fromFilePath(audio_path);
                    const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;
                    await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
                    CONFIG.DAILY_SENT++;

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

        // GET / — health check
        const ctx = TC.buildAgentTimeContext();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status:           'OK',
            daemon:           'argos-wa-daemon',
            version:          '2.2-sqlite',
            now_it:           ctx.now_it,
            is_business_hours: ctx.is_business_hours,
            daily_sent:       CONFIG.DAILY_SENT,
            daily_limit:      CONFIG.DAILY_LIMIT,
            daily_remaining:  CONFIG.DAILY_LIMIT - CONFIG.DAILY_SENT,
            uptime_sec:       Math.round(process.uptime()),
        }, null, 2));
    }).listen(9191, '127.0.0.1', () => {
        log('INFO', 'HTTP server su http://127.0.0.1:9191 (health + /send)');
    });

    // ── Scheduler Multi-Step (Day 3 + Day 7) ─────────────────
    startScheduler(client);

    client.initialize();
    return client;
}

// ── VOICE NOTE TEMPLATES PER ARCHETIPO ──────────────────────
const VOICE_TEMPLATES = {
    NARCISO: `Buongiorno, sono Luca Ferretti di ARGOS Automotive. Ho riservato questa opportunità esclusivamente per la sua area. Selezioniamo veicoli premium in Germania e Belgio, solo per concessionari selezionati. Report DAT e ispezione DEKRA inclusi. Se vuole, le invio un esempio concreto su misura per il suo stock. A presto.`,
    BARONE: `Buongiorno, mi permetto di ricontattarla con calma. Sono Luca Ferretti di ARGOS Automotive. Lavoriamo su misura per concessionari come il suo: selezione veicoli premium in Europa, con report DAT e ispezione DEKRA. Zero anticipi, paga solo a veicolo approvato. Se ha cinque minuti, le mostro come funziona. Buona giornata.`,
    RAGIONIERE: `Buongiorno, Luca Ferretti di ARGOS Automotive. Le invio i margini aggiornati: su una BMW X3 2021 dalla Germania, il risparmio medio è tra 4 e 7mila euro rispetto al mercato italiano. Fee fissa mille euro, report DAT incluso. Nessun anticipo. I numeri parlano da soli. Se vuole, le mando un caso concreto. A presto.`,
    TECNICO: `Buongiorno, Luca Ferretti di ARGOS Automotive. Ho il report DAT pronto e la documentazione completa sulla nostra procedura: ispezione DEKRA, verifica chilometraggio, garanzia costruttore UE valida in Italia. Ogni veicolo è tracciato e certificato. Se le interessa, le invio un esempio dettagliato. Buona giornata.`,
    RELAZIONALE: `Buongiorno, ci tenevo a risentirla. Sono Luca Ferretti di ARGOS Automotive. So che i tempi dei concessionari sono stretti, per questo gestiamo tutto noi. Selezioniamo veicoli premium in Europa con report e ispezione inclusi. Zero complicazioni per lei. Quando ha un momento, mi faccia sapere. Un saluto.`,
    CONSERVATORE: `Buongiorno, Luca Ferretti di ARGOS Automotive. Volevo rassicurarla: nessun rischio, tutto documentato. Ogni veicolo ha report DAT, ispezione DEKRA, garanzia costruttore UE. Paga solo a veicolo consegnato e approvato, zero anticipi. Se vuole, le mostro un caso reale con tutta la documentazione. Buona giornata.`,
    DELEGATORE: `Buongiorno, Luca Ferretti di ARGOS Automotive. Gestisco tutto io: selezione, report, ispezione, trasporto. A lei serve solo dire sì. Fee fissa mille euro, zero anticipi, zero complicazioni. Se le interessa, le invio un esempio e ci penso io a tutto il resto. Buona giornata.`,
    PERFORMANTE: `Buongiorno, Luca Ferretti di ARGOS Automotive. Ho un veicolo disponibile subito: BMW, Mercedes o Audi dalla Germania, pronto in 48 ore con report DAT e DEKRA. Fee mille euro, zero anticipi. Se mi dice cosa cerca, le mando la proposta entro domani. A presto.`,
    OPPORTUNISTA: `Buongiorno, Luca Ferretti di ARGOS Automotive. I numeri sono interessanti: margine medio tra 4 e 7mila euro su veicoli premium dalla Germania. Fee fissa mille euro, nessun anticipo. Il margine è tutto suo. Se vuole, le mando un caso concreto con i numeri reali. Buona giornata.`,
};

// Day 3 follow-up text templates
const DAY3_TEMPLATES = {
    NARCISO: `Buongiorno, solo un rapido aggiornamento. Ho selezionato alcune opportunità esclusive per la sua area — veicoli premium che non troverà facilmente sul mercato italiano.\n\nSe ha 5 minuti, le mostro i dettagli.\n\n— Luca`,
    BARONE: `Buongiorno, non voglio essere invadente. Le scrivo solo perché ho individuato un paio di veicoli che potrebbero interessarle.\n\nSe e quando ha tempo, sono a disposizione.\n\n— Luca`,
    RAGIONIERE: `Buongiorno, le condivido un dato: questa settimana su 3 BMW X3 2021 selezionate in Germania, il margine medio per il dealer è stato €5.200.\n\nSe vuole i dettagli, mi scriva.\n\n— Luca`,
    TECNICO: `Buongiorno, ho preparato una scheda tecnica di esempio: report DAT + foto ispezione DEKRA su una Mercedes GLC recente.\n\nSe le interessa vedere il livello di documentazione, gliela invio.\n\n— Luca`,
    RELAZIONALE: `Buongiorno, ci tenevo a farle sapere che resto a disposizione. Nessuna fretta, quando vorrà approfondire sono qui.\n\nBuona giornata.\n\n— Luca`,
    CONSERVATORE: `Buongiorno, capisco che valutare un nuovo fornitore richiede tempo. Per questo le confermo: zero rischi, zero anticipi. Paga solo a veicolo consegnato e approvato.\n\nSe ha domande, sono qui.\n\n— Luca`,
    DELEGATORE: `Buongiorno, solo un promemoria: se decide di provare, io gestisco tutto — selezione, documenti, trasporto. A lei basta dirmi che tipo di veicolo cerca.\n\n— Luca`,
    PERFORMANTE: `Buongiorno, aggiornamento rapido: ho 3 veicoli disponibili subito in Germania. Se mi dice marca e budget, le mando la proposta entro oggi.\n\n— Luca`,
    OPPORTUNISTA: `Buongiorno, i margini di questa settimana sono ancora più interessanti. Su un'Audi Q5 2022 dalla Germania: risparmio netto per il dealer circa €6.000.\n\nSe vuole i numeri completi, mi scriva.\n\n— Luca`,
};

// ── Genera voice note con edge-tts ──────────────────────────
function generateVoiceNote(text, outputPath) {
    try {
        // edge-tts con voce italiana DiegoNeural
        execSync(
            `edge-tts --voice it-IT-DiegoNeural --rate "+5%" --text "${text.replace(/"/g, '\\"')}" --write-media "${outputPath}"`,
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

            const chatId = phone.endsWith('@c.us') ? phone : `${phone}@c.us`;

            try {
                await client.sendMessage(chatId, template);
                CONFIG.DAILY_SENT++;

                // Logga e aggiorna step
                const msgId = `day3_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
                db.prepare(`INSERT OR IGNORE INTO messages
                    (id, dealer_id, dealer_name, phone_number, direction, body,
                     timestamp_it, timestamp_iso, wa_msg_id, processed)
                    VALUES (?, ?, ?, ?, 'OUTBOUND', ?, datetime('now'), ?, ?, 1)`)
                  .run(msgId, dealer.dealer_id, dealer.dealer_name, chatId,
                       template, TC.nowIT().toISOString(), msgId);

                db.prepare(`UPDATE conversations
                    SET current_step = 'DAY3_SENT', last_contact_at = datetime('now'), analyzed_at = datetime('now')
                    WHERE dealer_id = ?`).run(dealer.dealer_id);

                log('INFO', `📤 DAY 3 INVIATO: ${dealer.dealer_name} (${dealer.persona_type})`);
                sendTelegramAlert(
                    `📤 *Day 3 Follow-up INVIATO*\n` +
                    `👤 ${dealer.dealer_name} (${dealer.persona_type})\n` +
                    `📱 ${chatId}\n` +
                    `📊 ${CONFIG.DAILY_SENT}/${CONFIG.DAILY_LIMIT}`
                );

                // Anti-ban: attendi 2-5 minuti tra invii
                const sleepMs = (120 + Math.random() * 180) * 1000;
                await new Promise(r => setTimeout(r, sleepMs));
            } catch (e) {
                log('ERROR', `Day 3 send failed for ${dealer.dealer_id}:`, e.message);
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

            // Genera voice note
            const generated = generateVoiceNote(voiceText, voicePath);
            if (!generated) {
                log('ERROR', `Voice note generation failed for ${dealer.dealer_id}`);
                continue;
            }

            try {
                const { MessageMedia } = require('whatsapp-web.js');
                const media = MessageMedia.fromFilePath(voicePath);
                await client.sendMessage(chatId, media, { sendAudioAsVoice: true });
                CONFIG.DAILY_SENT++;

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

                // Anti-ban: attendi 3-6 minuti tra voice note
                const sleepMs = (180 + Math.random() * 180) * 1000;
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

// ── Entry point ──────────────────────────────────────────────
const waClient = initClient();

// Graceful shutdown
process.on('SIGTERM', async () => {
    log('INFO', 'SIGTERM ricevuto — shutdown graceful');
    try { await waClient.destroy(); } catch (_) {}
    try { if (_db) _db.close(); } catch (_) {}
    process.exit(0);
});

process.on('unhandledRejection', (reason) => {
    log('ERROR', 'UnhandledRejection:', reason?.message || reason);
});
