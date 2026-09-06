'use strict';

/**
 * ARGOS WhatsApp single-writer daemon — S292 production runtime.
 *
 * Design invariants:
 *   - exactly one outbound policy boundary: guardedSend();
 *   - transport implementation is selected behind that boundary;
 *   - every text/document send has dealer_id + exact template_id;
 *   - final Python outbound_guard runs immediately before transport;
 *   - bridge rows without template_id are blocked, never guessed;
 *   - no simulated typing, human-like jitter, stealth or anti-ban behaviour;
 *   - no voice/multi-message legacy bypasses;
 *   - inbound dealer messages are persisted before deterministic analysis;
 *   - Cloud API webhooks are signature-verified before JSON parsing;
 *   - policy failure is fail-closed and auditable.
 */

const fs = require('fs');
const http = require('http');
const path = require('path');
const crypto = require('crypto');
const { spawn, spawnSync } = require('child_process');
const Database = require('better-sqlite3');
const QRCode = require('qrcode');
const { createTransport, TransportError } = require('./transport');
const {
  createBoundedSeenSet,
  processWebhookPayload,
  verifyWebhookChallenge,
  verifyWebhookSignature,
} = require('./transport/webhook');

const ROOT = path.resolve(__dirname, '..');
const DB_PATH = process.env.ARGOS_DB_PATH || path.join(ROOT, 'dealer_network.sqlite');
const BRIDGE_DB_PATH = process.env.BRIDGE_DB_PATH || '';
const PYTHON_BIN = process.env.ARGOS_PYTHON || 'python3';
const ANALYZER = path.join(__dirname, 'response-analyzer.py');
const OUTBOUND_GUARD = path.join(__dirname, 'outbound_guard.py');
const POST_SEND_UPDATE = path.join(__dirname, 'post_send_update.py');
const PORT = Number(process.env.ARGOS_WA_PORT || 9191);
const HOST = process.env.ARGOS_BIND_HOST || '127.0.0.1';
const API_KEY = process.env.ARGOS_API_KEY || '';
const TRANSPORT_MODE = String(process.env.ARGOS_WA_TRANSPORT || 'wwebjs').trim().toLowerCase();
const BUSINESS_START = Number(process.env.ARGOS_BUSINESS_START_HOUR || 9);
const BUSINESS_END = Number(process.env.ARGOS_BUSINESS_END_HOUR || 18);
const BUSINESS_DAYS = new Set(
  (process.env.ARGOS_BUSINESS_DAYS || '1,2,3,4,5')
    .split(',')
    .map((v) => Number(v.trim()))
    .filter((v) => Number.isInteger(v) && v >= 0 && v <= 6),
);
const GLOBAL_DAILY_LIMIT = Number(process.env.ARGOS_GLOBAL_DAILY_LIMIT || 40);
const DEALER_DAILY_LIMIT = Number(process.env.ARGOS_DEALER_DAILY_LIMIT || 3);
const BRIDGE_POLL_MS = Math.max(5000, Number(process.env.ARGOS_BRIDGE_POLL_MS || 15000));
const INBOUND_DEBOUNCE_MS = Math.min(
  15000,
  Math.max(1000, Number(process.env.ARGOS_INBOUND_DEBOUNCE_MS || 3000)),
);
const MAX_BODY_CHARS = 4000;
const MAX_HTTP_BODY_BYTES = 1024 * 1024;

let activeTransport = null;
let latestQrDataUrl = null;
let bridgeTimer = null;
let shuttingDown = false;
const inboundBuffers = new Map();
const webhookEchoSeen = createBoundedSeenSet();

class GuardError extends Error {
  constructor(code, message, { transient = false } = {}) {
    super(message || code);
    this.name = 'GuardError';
    this.code = code;
    this.transient = transient;
  }
}

function nowIso() {
  return new Date().toISOString();
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function normalizePhone(value) {
  return String(value || '').replace(/\D/g, '');
}

function transportConnected() {
  try {
    return Boolean(activeTransport && activeTransport.isConnected());
  } catch (_) {
    return false;
  }
}

function dbOpen(file) {
  const db = new Database(file);
  db.pragma('journal_mode = WAL');
  db.pragma('busy_timeout = 10000');
  return db;
}

const db = dbOpen(DB_PATH);
let bridgeDb = null;
if (BRIDGE_DB_PATH) {
  fs.mkdirSync(path.dirname(BRIDGE_DB_PATH), { recursive: true });
  bridgeDb = dbOpen(BRIDGE_DB_PATH);
}

function tableColumns(database, table) {
  try {
    return new Set(database.prepare(`PRAGMA table_info('${table.replace(/'/g, "''")}')`).all().map((row) => row.name));
  } catch (_) {
    return new Set();
  }
}

function ensureColumn(database, table, column, definition) {
  if (!tableColumns(database, table).has(column)) {
    database.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${definition}`);
  }
}

function ensurePrimarySchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS conversations (
      dealer_id TEXT PRIMARY KEY,
      dealer_name TEXT,
      phone_number TEXT,
      persona TEXT,
      current_step TEXT DEFAULT 'NEW',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS messages (
      id TEXT PRIMARY KEY,
      dealer_id TEXT NOT NULL,
      direction TEXT NOT NULL,
      body TEXT,
      wa_msg_id TEXT,
      received_at TEXT,
      processed INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS audit_log (
      id TEXT PRIMARY KEY,
      event_type TEXT NOT NULL,
      dealer_id TEXT,
      payload TEXT,
      timestamp_it TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS argos_runtime_state (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
  `);

  const conversationColumns = {
    conversation_state: "TEXT DEFAULT 'COLD'",
    outbound_count: 'INTEGER DEFAULT 0',
    inbound_count: 'INTEGER DEFAULT 0',
    last_inbound_at: 'TEXT',
    state_updated_at: 'TEXT',
    escalation_flag: 'INTEGER DEFAULT 0',
    handoff_source: "TEXT DEFAULT 'cold'",
    is_micro_dealer: 'INTEGER DEFAULT 0',
    demand_evidence_json: 'TEXT',
    demand_evidence_id: 'TEXT',
    demand_evidence_source: 'TEXT',
    mandate_verified_at: 'TEXT',
    outreach_authorized: 'INTEGER DEFAULT 0',
  };
  Object.entries(conversationColumns).forEach(([name, definition]) =>
    ensureColumn(db, 'conversations', name, definition),
  );

  const messageColumns = {
    template_id: 'TEXT',
    classifier_intent: 'TEXT',
    classifier_confidence: 'REAL',
  };
  Object.entries(messageColumns).forEach(([name, definition]) =>
    ensureColumn(db, 'messages', name, definition),
  );

  db.prepare(`
    INSERT OR IGNORE INTO argos_runtime_state(key, value, updated_at)
    VALUES ('agent_status', 'PAUSED', ?)
  `).run(nowIso());
}

function ensureBridgeSchema() {
  if (!bridgeDb) return;
  bridgeDb.exec(`
    CREATE TABLE IF NOT EXISTS bridge_outbound (
      id TEXT PRIMARY KEY,
      deal_id TEXT NOT NULL,
      target_role TEXT NOT NULL,
      target_phone TEXT NOT NULL,
      template_phase TEXT NOT NULL,
      template_lang TEXT NOT NULL DEFAULT 'it',
      body TEXT NOT NULL,
      state_at_send TEXT,
      created_ts INTEGER NOT NULL,
      approved_ts INTEGER,
      sent_ts INTEGER,
      sent_status TEXT,
      wa_msg_id TEXT,
      processing_ts INTEGER,
      attempt_count INTEGER DEFAULT 0,
      action_type TEXT DEFAULT 'agent_auto'
    );
    CREATE TABLE IF NOT EXISTS bridge_inbound (
      id TEXT PRIMARY KEY,
      deal_id TEXT,
      source_role TEXT DEFAULT 'dealer',
      source_phone TEXT NOT NULL,
      body TEXT,
      wa_msg_id TEXT,
      created_ts INTEGER NOT NULL
    );
  `);
  const outboundColumns = {
    template_id: 'TEXT',
    inbound_msg_id: 'TEXT',
    guard_status: 'TEXT',
    guard_reason: 'TEXT',
    next_attempt_ts: 'INTEGER',
  };
  Object.entries(outboundColumns).forEach(([name, definition]) =>
    ensureColumn(bridgeDb, 'bridge_outbound', name, definition),
  );
  bridgeDb.exec(`
    CREATE INDEX IF NOT EXISTS idx_bridge_outbound_ready
      ON bridge_outbound(approved_ts, sent_ts, next_attempt_ts, processing_ts);
    CREATE UNIQUE INDEX IF NOT EXISTS uq_s292_outbound_inbound_template
      ON bridge_outbound(deal_id, target_phone, inbound_msg_id, template_id)
      WHERE inbound_msg_id IS NOT NULL AND template_id IS NOT NULL;
  `);
}

ensurePrimarySchema();
ensureBridgeSchema();

function audit(eventType, dealerId, payload = {}) {
  try {
    const canonical = JSON.stringify(payload);
    const id = `audit_${sha256(`${dealerId || ''}|${eventType}|${canonical}|${Date.now()}`).slice(0, 24)}`;
    db.prepare(`
      INSERT INTO audit_log(id, event_type, dealer_id, payload, timestamp_it)
      VALUES (?, ?, ?, ?, ?)
    `).run(id, eventType, dealerId || null, canonical, nowIso());
  } catch (err) {
    console.error('[audit]', eventType, err.message);
  }
}

function runtimeStatus() {
  const row = db.prepare("SELECT value FROM argos_runtime_state WHERE key='agent_status'").get();
  return row ? String(row.value || 'PAUSED').toUpperCase() : 'PAUSED';
}

function setRuntimeStatus(value) {
  const status = String(value || '').toUpperCase();
  if (!['ACTIVE', 'PAUSED'].includes(status)) throw new Error('invalid runtime status');
  db.prepare(`
    INSERT INTO argos_runtime_state(key, value, updated_at) VALUES('agent_status', ?, ?)
    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
  `).run(status, nowIso());
  audit('RUNTIME_STATUS', null, { status });
}

function italyClock() {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Rome',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  const weekdayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return {
    weekday: weekdayMap[values.weekday],
    hour: Number(values.hour),
    minute: Number(values.minute),
  };
}

function isBusinessHours() {
  const clock = italyClock();
  return BUSINESS_DAYS.has(clock.weekday) && clock.hour >= BUSINESS_START && clock.hour < BUSINESS_END;
}

function getDealerById(dealerId) {
  return db.prepare('SELECT * FROM conversations WHERE dealer_id = ? LIMIT 1').get(dealerId) || null;
}

function getDealerByPhone(phone) {
  const target = normalizePhone(phone);
  if (!target) return null;
  const rows = db.prepare('SELECT * FROM conversations WHERE phone_number IS NOT NULL').all();
  let best = null;
  let bestLen = 0;
  for (const row of rows) {
    const candidate = normalizePhone(row.phone_number);
    if (!candidate) continue;
    if (candidate === target || candidate.endsWith(target) || target.endsWith(candidate)) {
      const score = Math.min(candidate.length, target.length);
      if (score > bestLen) {
        best = row;
        bestLen = score;
      }
    }
  }
  return best;
}

function outgoingTodayCount(dealerId = null) {
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  if (dealerId) {
    return Number(
      db.prepare(`
        SELECT COUNT(*) AS n FROM messages
        WHERE direction='OUTBOUND' AND dealer_id=? AND created_at >= ?
      `).get(dealerId, cutoff)?.n || 0,
    );
  }
  return Number(
    db.prepare(`
      SELECT COUNT(*) AS n FROM messages
      WHERE direction='OUTBOUND' AND created_at >= ?
    `).get(cutoff)?.n || 0,
  );
}

function runPythonJson(script, args, timeoutMs = 15000) {
  const result = spawnSync(PYTHON_BIN, [script, ...args], {
    encoding: 'utf8',
    timeout: timeoutMs,
    maxBuffer: 1024 * 1024,
    env: { ...process.env, PYTHONPATH: ROOT },
  });
  const stdout = String(result.stdout || '').trim();
  let parsed = null;
  if (stdout) {
    const line = stdout.split(/\r?\n/).filter(Boolean).slice(-1)[0];
    try { parsed = JSON.parse(line); } catch (_) { parsed = null; }
  }
  return {
    status: result.status,
    signal: result.signal,
    error: result.error ? result.error.message : null,
    stderr: String(result.stderr || '').trim(),
    json: parsed,
  };
}

function finalPolicyGuard(dealerId, templateId, message) {
  if (!dealerId || !templateId || !message) {
    throw new GuardError('MISSING_TRANSPORT_CONTEXT', 'dealer_id, template_id and message are required');
  }
  const result = runPythonJson(
    OUTBOUND_GUARD,
    ['--db-path', DB_PATH, '--dealer-id', dealerId, '--template-id', templateId, '--message', message],
  );
  if (result.status !== 0 || !result.json || result.json.ok !== true) {
    const reason = result.json?.reason || result.stderr || result.error || 'outbound guard failed';
    const transient = /WAIT_FOR_INBOUND|REQUIRES_INBOUND|CAP_REACHED/.test(reason);
    throw new GuardError('OUTBOUND_POLICY_BLOCK', reason, { transient });
  }
  return result.json;
}

function assertTransportPreconditions(dealer, phone) {
  if (!dealer) throw new GuardError('DEALER_NOT_FOUND', 'dealer not found');
  if (runtimeStatus() !== 'ACTIVE') {
    throw new GuardError('AGENT_PAUSED', 'ARGOS runtime is paused', { transient: true });
  }
  if (!isBusinessHours()) {
    throw new GuardError('OUTSIDE_BUSINESS_HOURS', 'outside configured Europe/Rome business hours', { transient: true });
  }
  if (!transportConnected()) {
    throw new GuardError('TRANSPORT_NOT_READY', 'WhatsApp transport is not ready', { transient: true });
  }
  const stored = normalizePhone(dealer.phone_number);
  const requested = normalizePhone(phone);
  if (!stored || !requested || !(stored === requested || stored.endsWith(requested) || requested.endsWith(stored))) {
    throw new GuardError('PHONE_DEALER_MISMATCH', 'target phone does not match dealer record');
  }
  if (outgoingTodayCount() >= GLOBAL_DAILY_LIMIT) {
    throw new GuardError('GLOBAL_DAILY_LIMIT', 'global 24h outbound limit reached', { transient: true });
  }
  if (outgoingTodayCount(dealer.dealer_id) >= DEALER_DAILY_LIMIT) {
    throw new GuardError('DEALER_DAILY_LIMIT', 'dealer 24h outbound limit reached', { transient: true });
  }
}

function verifyDossierMetadata({ dealer, filePath, metadataPath }) {
  if (!metadataPath || !fs.existsSync(metadataPath)) {
    throw new GuardError('DOSSIER_METADATA_REQUIRED', 'dealer-ready dossier metadata is required');
  }
  if (!filePath || !fs.existsSync(filePath)) {
    throw new GuardError('DOSSIER_FILE_MISSING', 'dossier file not found');
  }
  let meta;
  try {
    meta = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  } catch (err) {
    throw new GuardError('DOSSIER_METADATA_INVALID', err.message);
  }
  if (meta.dealer_ready !== true) {
    throw new GuardError('DOSSIER_NOT_DEALER_READY', 'metadata dealer_ready is not true');
  }
  if (String(meta.dealer_id || '') !== String(dealer.dealer_id)) {
    throw new GuardError('DOSSIER_DEALER_MISMATCH', 'dossier dealer_id mismatch');
  }
  if (!meta.evidence_id || String(meta.evidence_id) !== String(dealer.demand_evidence_id || '')) {
    throw new GuardError('DOSSIER_EVIDENCE_MISMATCH', 'dossier evidence_id mismatch');
  }
  const state = String(dealer.conversation_state || 'COLD').toUpperCase();
  if (!['MANDATE_CONFIRMED', 'CONVERTING'].includes(state)) {
    throw new GuardError('DOSSIER_STATE_BLOCK', `dossier send requires verified mandate, state=${state}`);
  }
  const actualHash = sha256(fs.readFileSync(filePath));
  if (String(meta.file_sha256 || '').toLowerCase() !== actualHash.toLowerCase()) {
    throw new GuardError('DOSSIER_HASH_MISMATCH', 'dossier sha256 does not match metadata');
  }
  return meta;
}

function persistOutbound({ dealerId, message, templateId, waMessageId }) {
  const id = `out_${sha256(`${dealerId}|${waMessageId}|${templateId}`).slice(0, 24)}`;
  db.prepare(`
    INSERT OR IGNORE INTO messages
      (id, dealer_id, direction, body, wa_msg_id, received_at, processed, created_at, template_id)
    VALUES (?, ?, 'OUTBOUND', ?, ?, ?, 1, ?, ?)
  `).run(id, dealerId, message, waMessageId, nowIso(), nowIso(), templateId);

  const update = runPythonJson(
    POST_SEND_UPDATE,
    ['--db-path', DB_PATH, '--dealer-id', dealerId, '--template-id', templateId],
  );
  if (update.status !== 0 || !update.json?.ok) {
    audit('POST_SEND_STATE_ERROR', dealerId, {
      template_id: templateId,
      error: update.stderr || update.error || update.json || null,
    });
  }
}

function transportGuardError(err) {
  if (!(err instanceof TransportError)) return err;
  const transient = err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS' ? false : Boolean(err.transient);
  return new GuardError(err.code || 'TRANSPORT_ERROR', err.message || 'transport error', { transient });
}

async function guardedSend({
  dealerId,
  phone,
  templateId,
  message,
  documentPath = null,
  dossierMetadataPath = null,
}) {
  const dealer = getDealerById(dealerId);
  assertTransportPreconditions(dealer, phone);
  const text = String(message || '').trim();
  if (!text || text.length > MAX_BODY_CHARS) {
    throw new GuardError('INVALID_MESSAGE_LENGTH', 'message must be 1..4000 characters');
  }
  const policy = finalPolicyGuard(dealerId, templateId, text);

  if (documentPath) {
    verifyDossierMetadata({ dealer, filePath: documentPath, metadataPath: dossierMetadataPath });
  }

  const digits = normalizePhone(phone);
  let sent;
  try {
    sent = documentPath
      ? await activeTransport.sendDocument({ phone: digits, filePath: documentPath, caption: text })
      : await activeTransport.sendText({ phone: digits, body: text });
  } catch (err) {
    const wrapped = transportGuardError(err);
    audit('TRANSPORT_SEND_BLOCKED', dealerId, {
      template_id: templateId,
      code: wrapped.code || 'TRANSPORT_ERROR',
      ambiguous: err instanceof TransportError ? Boolean(err.ambiguous) : false,
    });
    throw wrapped;
  }

  const waMessageId = String(sent?.wa_msg_id || '');
  if (!waMessageId) {
    throw new GuardError('TRANSPORT_INVALID_RESPONSE', 'transport response is missing message id');
  }
  persistOutbound({ dealerId, message: text, templateId, waMessageId });
  audit('OUTBOUND_SENT', dealerId, {
    template_id: templateId,
    phone_suffix: digits.slice(-4),
    wa_msg_id: waMessageId,
    document: Boolean(documentPath),
    transport: TRANSPORT_MODE,
    policy,
  });
  return { ok: true, wa_msg_id: waMessageId, policy };
}

function persistInbound(dealer, msg) {
  const waId = msg?.id?._serialized || `wa_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  const id = `in_${sha256(waId).slice(0, 24)}`;
  const body = String(msg.body || '').slice(0, MAX_BODY_CHARS);
  const result = db.prepare(`
    INSERT OR IGNORE INTO messages
      (id, dealer_id, direction, body, wa_msg_id, received_at, processed, created_at)
    VALUES (?, ?, 'INBOUND', ?, ?, ?, 0, ?)
  `).run(id, dealer.dealer_id, body, waId, nowIso(), nowIso());
  return { inserted: result.changes === 1, id, waId, body };
}

function bridgeIngestInbound(dealer, persisted, phone) {
  if (!bridgeDb || !persisted.inserted) return;
  const bridgeId = `bin_${sha256(`${dealer.dealer_id}|${persisted.waId}`).slice(0, 24)}`;
  try {
    bridgeDb.prepare(`
      INSERT OR IGNORE INTO bridge_inbound
        (id, deal_id, source_role, source_phone, body, wa_msg_id, created_ts)
      VALUES (?, ?, 'dealer', ?, ?, ?, ?)
    `).run(
      bridgeId,
      dealer.dealer_id,
      normalizePhone(phone),
      persisted.body,
      persisted.waId,
      Math.floor(Date.now() / 1000),
    );
  } catch (err) {
    audit('BRIDGE_INBOUND_ERROR', dealer.dealer_id, { error: err.message });
  }
}

function runAnalyzer({ dealer, messageIds, body }) {
  const evidenceId = messageIds.join('+').slice(0, 512);
  const args = [
    ANALYZER,
    '--msg-id', evidenceId,
    '--msg-body', body.slice(0, MAX_BODY_CHARS),
    '--dealer-id', String(dealer.dealer_id),
    '--dealer-name', String(dealer.dealer_name || dealer.name || 'Dealer'),
    '--persona', String(dealer.persona || ''),
    '--step', String(dealer.current_step || ''),
    '--db-path', DB_PATH,
    '--batch',
  ];
  if (BRIDGE_DB_PATH) args.push('--bridge-db-path', BRIDGE_DB_PATH);

  const child = spawn(PYTHON_BIN, args, {
    cwd: ROOT,
    env: { ...process.env, PYTHONPATH: ROOT },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
  child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
  child.on('error', (err) => {
    audit('ANALYZER_SPAWN_ERROR', dealer.dealer_id, { error: err.message });
  });
  child.on('close', (code) => {
    audit('ANALYZER_EXIT', dealer.dealer_id, {
      code,
      output: stdout.trim().slice(-4000),
      stderr: stderr.trim().slice(-2000),
      evidence_id: evidenceId,
    });
  });
}

function bufferInbound(dealer, persisted) {
  const key = String(dealer.dealer_id);
  const existing = inboundBuffers.get(key) || { ids: [], bodies: [], timer: null, dealer };
  existing.ids.push(persisted.id);
  if (persisted.body) existing.bodies.push(persisted.body);
  existing.dealer = dealer;
  if (existing.timer) clearTimeout(existing.timer);
  existing.timer = setTimeout(() => {
    inboundBuffers.delete(key);
    const combined = existing.bodies.join('\n').trim();
    if (!combined) return;
    runAnalyzer({ dealer: existing.dealer, messageIds: existing.ids, body: combined });
  }, INBOUND_DEBOUNCE_MS);
  inboundBuffers.set(key, existing);
}

async function handleInbound(msg) {
  try {
    if (!msg || msg.fromMe) return;
    const from = String(msg.from || '');
    if (!from.endsWith('@c.us')) return;
    const phone = normalizePhone(from.replace('@c.us', ''));
    const dealer = getDealerByPhone(phone);
    if (!dealer) {
      audit('UNKNOWN_INBOUND_IGNORED', null, { phone_suffix: phone.slice(-4) });
      return;
    }
    const persisted = persistInbound(dealer, msg);
    if (!persisted.inserted) return;
    bridgeIngestInbound(dealer, persisted, phone);
    audit('INBOUND_PERSISTED', dealer.dealer_id, {
      msg_id: persisted.id,
      body_sha256: sha256(persisted.body),
    });
    bufferInbound(dealer, persisted);
  } catch (err) {
    console.error('[inbound]', err);
    audit('INBOUND_ERROR', null, { error: err.message });
  }
}

function bridgeReadyRows(limit = 10) {
  if (!bridgeDb) return [];
  const now = Math.floor(Date.now() / 1000);
  const stale = now - 5 * 60;
  return bridgeDb.prepare(`
    SELECT id, deal_id, target_phone, body, template_phase, template_id,
           inbound_msg_id, processing_ts, attempt_count, next_attempt_ts
    FROM bridge_outbound
    WHERE approved_ts IS NOT NULL
      AND sent_ts IS NULL
      AND (sent_status IS NULL OR sent_status IN ('RETRY', 'DEFERRED'))
      AND (next_attempt_ts IS NULL OR next_attempt_ts <= ?)
      AND (processing_ts IS NULL OR processing_ts < ?)
    ORDER BY approved_ts ASC, created_ts ASC
    LIMIT ?
  `).all(now, stale, limit);
}

function claimBridgeRow(id) {
  const now = Math.floor(Date.now() / 1000);
  const stale = now - 5 * 60;
  const result = bridgeDb.prepare(`
    UPDATE bridge_outbound
       SET processing_ts = ?
     WHERE id = ? AND sent_ts IS NULL
       AND (processing_ts IS NULL OR processing_ts < ?)
  `).run(now, id, stale);
  return result.changes === 1;
}

function markBridgeBlocked(row, code, reason) {
  bridgeDb.prepare(`
    UPDATE bridge_outbound
       SET processing_ts=NULL, sent_status='BLOCKED_POLICY',
           guard_status='BLOCK', guard_reason=?
     WHERE id=? AND sent_ts IS NULL
  `).run(`${code}: ${reason}`.slice(0, 1000), row.id);
  audit('BRIDGE_BLOCKED', row.deal_id || null, { row_id: row.id, code, reason });
}

function deferBridge(row, code, reason, attemptIncrement = true) {
  const attempts = Number(row.attempt_count || 0) + (attemptIncrement ? 1 : 0);
  if (attempts >= 5) {
    bridgeDb.prepare(`
      UPDATE bridge_outbound
         SET processing_ts=NULL, attempt_count=?, sent_status='FAILED_RETRIES',
             guard_status='ERROR', guard_reason=?
       WHERE id=? AND sent_ts IS NULL
    `).run(attempts, `${code}: ${reason}`.slice(0, 1000), row.id);
    return;
  }
  const delaySeconds = Math.min(6 * 3600, Math.max(15 * 60, 15 * 60 * Math.pow(2, attempts)));
  const next = Math.floor(Date.now() / 1000) + delaySeconds;
  bridgeDb.prepare(`
    UPDATE bridge_outbound
       SET processing_ts=NULL, attempt_count=?, sent_status='DEFERRED',
           next_attempt_ts=?, guard_status='DEFER', guard_reason=?
     WHERE id=? AND sent_ts IS NULL
  `).run(attempts, next, `${code}: ${reason}`.slice(0, 1000), row.id);
}

async function pollBridgeOutbound() {
  if (!bridgeDb || shuttingDown || !transportConnected() || runtimeStatus() !== 'ACTIVE' || !isBusinessHours()) return;
  for (const row of bridgeReadyRows()) {
    if (!claimBridgeRow(row.id)) continue;
    try {
      if (!row.template_id) {
        markBridgeBlocked(row, 'MISSING_TEMPLATE_ID', 'legacy/ambiguous bridge rows are not transport-authorized');
        continue;
      }
      const dealer = getDealerByPhone(row.target_phone);
      if (!dealer) {
        markBridgeBlocked(row, 'DEALER_NOT_FOUND', 'bridge phone is not mapped to a dealer');
        continue;
      }
      const result = await guardedSend({
        dealerId: dealer.dealer_id,
        phone: row.target_phone,
        templateId: row.template_id,
        message: row.body,
      });
      bridgeDb.prepare(`
        UPDATE bridge_outbound
           SET processing_ts=NULL, sent_ts=?, sent_status='SENT', wa_msg_id=?,
               guard_status='PASS', guard_reason='final_transport_guard_ok'
         WHERE id=? AND sent_ts IS NULL
      `).run(Math.floor(Date.now() / 1000), result.wa_msg_id, row.id);
    } catch (err) {
      if (err instanceof GuardError && !err.transient) {
        markBridgeBlocked(row, err.code, err.message);
      } else {
        deferBridge(row, err.code || 'TRANSPORT_ERROR', err.message || String(err));
      }
    }
  }
}

function startBridgePoller() {
  if (!bridgeDb || bridgeTimer) return;
  bridgeTimer = setInterval(() => {
    pollBridgeOutbound().catch((err) => {
      console.error('[bridge poll]', err);
      audit('BRIDGE_POLL_ERROR', null, { error: err.message });
    });
  }, BRIDGE_POLL_MS);
  bridgeTimer.unref?.();
}

function stopBridgePoller() {
  if (bridgeTimer) clearInterval(bridgeTimer);
  bridgeTimer = null;
}

function httpJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) });
  res.end(body);
}

function httpText(res, status, text) {
  const body = String(text || '');
  res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8', 'Content-Length': Buffer.byteLength(body) });
  res.end(body);
}

function requireApiKey(req, res) {
  if (!API_KEY) {
    httpJson(res, 503, { ok: false, error: 'ARGOS_API_KEY_NOT_CONFIGURED' });
    return false;
  }
  const supplied = String(req.headers['x-api-key'] || '');
  const a = Buffer.from(supplied);
  const b = Buffer.from(API_KEY);
  const equal = a.length === b.length && crypto.timingSafeEqual(a, b);
  if (!equal) {
    httpJson(res, 401, { ok: false, error: 'UNAUTHORIZED' });
    return false;
  }
  return true;
}

function readRawBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_HTTP_BODY_BYTES) {
        reject(new Error('request body too large'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

async function readJsonBody(req) {
  const raw = await readRawBody(req);
  return raw.length ? JSON.parse(raw.toString('utf8')) : {};
}

function auditWebhookStatus(status) {
  audit('WHATSAPP_DELIVERY_STATUS', null, {
    wa_msg_id: status.wa_msg_id,
    status: status.status,
    recipient_suffix: normalizePhone(status.recipient_id).slice(-4),
    error_codes: status.error_codes,
  });
}

async function handleWebhook(req, res, url) {
  if (TRANSPORT_MODE !== 'cloud') {
    return httpJson(res, 404, { ok: false, error: 'WEBHOOK_NOT_ENABLED' });
  }

  if (req.method === 'GET') {
    const challenge = verifyWebhookChallenge(url.searchParams, process.env.META_WA_WEBHOOK_VERIFY_TOKEN || '');
    if (challenge === null) return httpJson(res, 403, { ok: false, error: 'WEBHOOK_VERIFY_FAILED' });
    return httpText(res, 200, challenge);
  }

  if (req.method !== 'POST') return httpJson(res, 405, { ok: false, error: 'METHOD_NOT_ALLOWED' });

  let raw;
  try {
    raw = await readRawBody(req);
  } catch (err) {
    return httpJson(res, 413, { ok: false, error: 'WEBHOOK_BODY_REJECTED' });
  }

  const signature = String(req.headers['x-hub-signature-256'] || '');
  const appSecret = String(process.env.META_APP_SECRET || '');
  if (!verifyWebhookSignature(raw, signature, appSecret)) {
    audit('WHATSAPP_WEBHOOK_SIGNATURE_REJECTED', null, {});
    return httpJson(res, 403, { ok: false, error: 'INVALID_WEBHOOK_SIGNATURE' });
  }

  let payload;
  try {
    payload = raw.length ? JSON.parse(raw.toString('utf8')) : {};
  } catch (_) {
    return httpJson(res, 400, { ok: false, error: 'INVALID_WEBHOOK_JSON' });
  }

  try {
    const result = await processWebhookPayload(payload, {
      onInbound: handleInbound,
      onStatus: auditWebhookStatus,
      onAudit: (eventType, data) => audit(eventType, null, data),
      seenEchoes: webhookEchoSeen,
    });
    return httpJson(res, 200, { ok: true, handled: result.handled });
  } catch (err) {
    audit('WHATSAPP_WEBHOOK_PROCESSING_ERROR', null, { error: err.message });
    return httpJson(res, 500, { ok: false, error: 'WEBHOOK_PROCESSING_ERROR' });
  }
}

async function handleHttp(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

  if (url.pathname === '/webhooks/whatsapp') {
    return handleWebhook(req, res, url);
  }

  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/status' || url.pathname === '/health')) {
    return httpJson(res, 200, {
      ok: true,
      runtime: 'argos-s292-single-writer',
      connected: transportConnected(),
      transport: TRANSPORT_MODE,
      agent_status: runtimeStatus(),
      business_hours: isBusinessHours(),
      bridge_enabled: Boolean(bridgeDb),
      pending_bridge: bridgeDb ? bridgeReadyRows(1000).length : 0,
      global_outbound_24h: outgoingTodayCount(),
      limits: { global_24h: GLOBAL_DAILY_LIMIT, dealer_24h: DEALER_DAILY_LIMIT },
    });
  }

  if (req.method === 'GET' && url.pathname === '/qr') {
    if (TRANSPORT_MODE !== 'wwebjs' || !latestQrDataUrl) {
      return httpJson(res, 404, { ok: false, error: 'QR_NOT_AVAILABLE' });
    }
    return httpJson(res, 200, { ok: true, qr_data_url: latestQrDataUrl });
  }

  if (req.method !== 'POST') return httpJson(res, 404, { ok: false, error: 'NOT_FOUND' });
  if (!requireApiKey(req, res)) return;

  let payload;
  try {
    payload = await readJsonBody(req);
  } catch (err) {
    return httpJson(res, 400, { ok: false, error: 'INVALID_JSON', detail: err.message });
  }

  if (url.pathname === '/pause') {
    setRuntimeStatus('PAUSED');
    return httpJson(res, 200, { ok: true, agent_status: 'PAUSED' });
  }
  if (url.pathname === '/resume') {
    setRuntimeStatus('ACTIVE');
    return httpJson(res, 200, { ok: true, agent_status: 'ACTIVE' });
  }
  if (url.pathname === '/send-multi' || url.pathname === '/send-voice') {
    return httpJson(res, 410, {
      ok: false,
      error: 'LEGACY_TRANSPORT_RETIRED',
      detail: 'Use one evidence-safe template through /send; voice/multi bypasses are disabled.',
    });
  }

  try {
    if (url.pathname === '/send') {
      const result = await guardedSend({
        dealerId: String(payload.dealer_id || ''),
        phone: String(payload.phone || ''),
        templateId: String(payload.template_id || ''),
        message: String(payload.message || ''),
      });
      return httpJson(res, 200, result);
    }
    if (url.pathname === '/send-doc') {
      const result = await guardedSend({
        dealerId: String(payload.dealer_id || ''),
        phone: String(payload.phone || ''),
        templateId: String(payload.template_id || ''),
        message: String(payload.caption || ''),
        documentPath: String(payload.file_path || ''),
        dossierMetadataPath: String(payload.metadata_path || ''),
      });
      return httpJson(res, 200, result);
    }
  } catch (err) {
    const status = err instanceof GuardError ? (err.transient ? 409 : 422) : 500;
    audit('HTTP_SEND_BLOCKED', String(payload.dealer_id || ''), {
      path: url.pathname,
      code: err.code || 'ERROR',
      error: err.message,
    });
    return httpJson(res, status, {
      ok: false,
      error: err.code || 'SEND_ERROR',
      detail: err.message,
      transient: Boolean(err.transient),
    });
  }
  return httpJson(res, 404, { ok: false, error: 'NOT_FOUND' });
}

function transportCallbacks() {
  return {
    onQr: async (qr) => {
      try { latestQrDataUrl = await QRCode.toDataURL(qr); } catch (_) { latestQrDataUrl = null; }
      audit('WHATSAPP_QR', null, { available: Boolean(latestQrDataUrl) });
    },
    onAuthenticated: () => audit('WHATSAPP_AUTHENTICATED', null, {}),
    onReady: () => {
      latestQrDataUrl = null;
      audit('WHATSAPP_READY', null, { transport: 'wwebjs' });
      startBridgePoller();
    },
    onMessage: handleInbound,
    onAuthFailure: (message) => {
      audit('WHATSAPP_AUTH_FAILURE', null, { message: String(message || '') });
      if (!shuttingDown) setTimeout(() => process.exit(2), 500);
    },
    onDisconnected: (reason) => {
      stopBridgePoller();
      audit('WHATSAPP_DISCONNECTED', null, { reason: String(reason || '') });
      if (!shuttingDown) setTimeout(() => process.exit(3), 500);
    },
  };
}

async function startWhatsapp() {
  activeTransport = createTransport({ env: process.env, callbacks: transportCallbacks() });
  const result = await activeTransport.initialize();
  audit('WHATSAPP_TRANSPORT_INITIALIZED', null, {
    transport: TRANSPORT_MODE,
    connected: transportConnected(),
    phone_number_id: TRANSPORT_MODE === 'cloud' ? String(result?.phone_number_id || '') : undefined,
  });
  if (transportConnected()) startBridgePoller();
}

const server = http.createServer((req, res) => {
  handleHttp(req, res).catch((err) => {
    console.error('[http]', err);
    if (!res.headersSent) httpJson(res, 500, { ok: false, error: 'INTERNAL_ERROR' });
    else res.end();
  });
});

server.listen(PORT, HOST, () => {
  console.log(`[ARGOS] S292 single-writer listening on http://${HOST}:${PORT}`);
  console.log(`[ARGOS] DB=${DB_PATH}`);
  console.log(`[ARGOS] bridge=${BRIDGE_DB_PATH || 'disabled'}`);
  console.log(`[ARGOS] transport=${TRANSPORT_MODE}`);
});

async function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  stopBridgePoller();
  for (const value of inboundBuffers.values()) {
    if (value.timer) clearTimeout(value.timer);
  }
  inboundBuffers.clear();
  audit('DAEMON_SHUTDOWN', null, { signal });
  server.close();
  try { if (activeTransport) await activeTransport.shutdown(); } catch (_) {}
  try { if (bridgeDb) bridgeDb.close(); } catch (_) {}
  try { db.close(); } catch (_) {}
  process.exit(0);
}

process.on('SIGINT', () => { shutdown('SIGINT'); });
process.on('SIGTERM', () => { shutdown('SIGTERM'); });
process.on('uncaughtException', (err) => {
  console.error('[uncaughtException]', err);
  audit('UNCAUGHT_EXCEPTION', null, { error: err.message, stack: err.stack });
  process.exit(10);
});
process.on('unhandledRejection', (err) => {
  console.error('[unhandledRejection]', err);
  audit('UNHANDLED_REJECTION', null, { error: String(err) });
  process.exit(11);
});

startWhatsapp().catch((err) => {
  console.error('[ARGOS] WhatsApp init failed:', err.message || String(err));
  audit('WHATSAPP_INIT_FAILED', null, { code: err.code || 'ERROR', error: err.message });
  process.exit(4);
});
