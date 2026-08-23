'use strict';

const Database = require('better-sqlite3');
const { TransportError } = require('./errors');

const CUSTOMER_SERVICE_WINDOW_MS = 24 * 60 * 60 * 1000;

function normalizePhone(value) {
  return String(value || '').replace(/\D/g, '');
}

function phoneMatches(a, b) {
  const left = normalizePhone(a);
  const right = normalizePhone(b);
  return Boolean(left && right && (left === right || left.endsWith(right) || right.endsWith(left)));
}

function parseTimestamp(value) {
  const ms = Date.parse(String(value || ''));
  return Number.isFinite(ms) ? ms : null;
}

function consentValid(dealer) {
  return Boolean(
    Number(dealer?.whatsapp_opt_in || 0) === 1
    && String(dealer?.whatsapp_opt_in_at || '').trim()
    && String(dealer?.whatsapp_opt_in_source || '').trim()
    && String(dealer?.whatsapp_opt_in_evidence_id || '').trim()
    && !String(dealer?.whatsapp_opt_out_at || '').trim()
  );
}

class CloudPolicyTransport {
  constructor({ transport, env = process.env, nowFn = () => Date.now(), databaseFactory = (path) => new Database(path, { readonly: true }) } = {}) {
    if (!transport) throw new TransportError('TRANSPORT_CONFIG_MISSING', 'underlying Cloud transport is required');
    this.transport = transport;
    this.env = env;
    this.nowFn = nowFn;
    this.databaseFactory = databaseFactory;
    this.dbPath = String(env.ARGOS_DB_PATH || '');
    this.bridgeDbPath = String(env.BRIDGE_DB_PATH || '');
  }

  async initialize() {
    if (!this.dbPath) {
      throw new TransportError('TRANSPORT_CONFIG_MISSING', 'ARGOS_DB_PATH is required for Cloud policy enforcement');
    }
    return this.transport.initialize();
  }

  isConnected() {
    return this.transport.isConnected();
  }

  _dealerForPhone(phone) {
    let db;
    try {
      db = this.databaseFactory(this.dbPath);
      const columns = new Set(db.prepare("PRAGMA table_info('conversations')").all().map((row) => row.name));
      const required = [
        'phone_number',
        'last_inbound_at',
        'whatsapp_opt_in',
        'whatsapp_opt_in_at',
        'whatsapp_opt_in_source',
        'whatsapp_opt_in_evidence_id',
        'whatsapp_opt_out_at',
      ];
      if (!required.every((name) => columns.has(name))) {
        throw new TransportError('WHATSAPP_CONSENT_SCHEMA_MISSING', 'WhatsApp consent/customer-service schema is incomplete');
      }
      const rows = db.prepare(
        `SELECT dealer_id, phone_number, last_inbound_at,
                whatsapp_opt_in, whatsapp_opt_in_at, whatsapp_opt_in_source,
                whatsapp_opt_in_evidence_id, whatsapp_opt_out_at
           FROM conversations
          WHERE phone_number IS NOT NULL`
      ).all();
      const matches = rows.filter((row) => phoneMatches(row.phone_number, phone));
      if (matches.length !== 1) {
        throw new TransportError(
          'DEALER_PHONE_RESOLUTION_FAILED',
          matches.length ? 'Cloud policy phone maps to multiple dealers' : 'Cloud policy phone is not mapped to a dealer',
        );
      }
      return matches[0];
    } finally {
      try { db?.close(); } catch (_) {}
    }
  }

  _insideCustomerServiceWindow(dealer) {
    const lastInbound = parseTimestamp(dealer?.last_inbound_at);
    if (lastInbound === null) return false;
    const age = this.nowFn() - lastInbound;
    return age >= 0 && age <= CUSTOMER_SERVICE_WINDOW_MS;
  }

  _claimedMetaTemplate({ phone, body, dealer }) {
    if (!this.bridgeDbPath) {
      throw new TransportError('META_TEMPLATE_REQUIRED', 'No bridge database is configured for proactive template send');
    }
    let db;
    try {
      db = this.databaseFactory(this.bridgeDbPath);
      const columns = new Set(db.prepare("PRAGMA table_info('bridge_outbound')").all().map((row) => row.name));
      const required = [
        'target_phone', 'body', 'processing_ts', 'sent_ts',
        'meta_template_json', 'whatsapp_opt_in_evidence_id',
      ];
      if (!required.every((name) => columns.has(name))) {
        throw new TransportError('META_TEMPLATE_SCHEMA_MISSING', 'Bridge Meta template schema is incomplete');
      }
      const rows = db.prepare(
        `SELECT id, target_phone, body, processing_ts, sent_ts,
                meta_template_json, whatsapp_opt_in_evidence_id
           FROM bridge_outbound
          WHERE processing_ts IS NOT NULL AND sent_ts IS NULL
            AND body = ?`
      ).all(String(body || ''));
      const matches = rows.filter((row) => phoneMatches(row.target_phone, phone));
      if (matches.length !== 1) {
        throw new TransportError(
          'META_TEMPLATE_REQUIRED',
          matches.length ? 'Multiple claimed bridge rows match proactive send' : 'No claimed bridge Meta template matches proactive send',
        );
      }
      const row = matches[0];
      const currentEvidence = String(dealer?.whatsapp_opt_in_evidence_id || '').trim();
      if (!currentEvidence || String(row.whatsapp_opt_in_evidence_id || '').trim() !== currentEvidence) {
        throw new TransportError('WHATSAPP_OPT_IN_EVIDENCE_MISMATCH', 'Queued opt-in evidence no longer matches dealer consent');
      }
      let template;
      try {
        template = JSON.parse(String(row.meta_template_json || ''));
      } catch (_) {
        throw new TransportError('META_TEMPLATE_INVALID', 'Queued Meta template payload is invalid JSON');
      }
      if (!template || typeof template !== 'object' || !template.name || !template.language?.code) {
        throw new TransportError('META_TEMPLATE_INVALID', 'Queued Meta template payload is incomplete');
      }
      return template;
    } finally {
      try { db?.close(); } catch (_) {}
    }
  }

  async sendText({ phone, body }) {
    const dealer = this._dealerForPhone(phone);
    if (this._insideCustomerServiceWindow(dealer)) {
      return this.transport.sendText({ phone, body });
    }
    if (!consentValid(dealer)) {
      throw new TransportError(
        'WHATSAPP_OPT_IN_REQUIRED',
        'Business-initiated Cloud message requires traceable WhatsApp opt-in',
      );
    }
    const template = this._claimedMetaTemplate({ phone, body, dealer });
    return this.transport.sendTemplate({ phone, template });
  }

  async sendDocument({ phone, filePath, caption }) {
    const dealer = this._dealerForPhone(phone);
    if (!this._insideCustomerServiceWindow(dealer)) {
      throw new TransportError(
        'META_TEMPLATE_REQUIRED',
        'Free-form document send is allowed only inside the 24-hour customer-service window',
      );
    }
    return this.transport.sendDocument({ phone, filePath, caption });
  }

  async shutdown() {
    return this.transport.shutdown();
  }
}

module.exports = {
  CloudPolicyTransport,
  CUSTOMER_SERVICE_WINDOW_MS,
  consentValid,
  normalizePhone,
  phoneMatches,
};
