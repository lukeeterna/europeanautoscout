'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  CloudPolicyTransport,
  CUSTOMER_SERVICE_WINDOW_MS,
  consentValid,
} = require('../cloud_policy_transport');

const CONVERSATION_COLUMNS = [
  'dealer_id',
  'phone_number',
  'last_inbound_at',
  'whatsapp_opt_in',
  'whatsapp_opt_in_at',
  'whatsapp_opt_in_source',
  'whatsapp_opt_in_evidence_id',
  'whatsapp_opt_out_at',
];

const BRIDGE_COLUMNS = [
  'id',
  'target_phone',
  'body',
  'processing_ts',
  'sent_ts',
  'meta_template_json',
  'whatsapp_opt_in_evidence_id',
];

function fakeDatabaseFactory({ primaryPath = '/primary.sqlite', bridgePath = '/bridge.sqlite', dealers = [], bridgeRows = [] } = {}) {
  return (dbPath) => ({
    prepare(sql) {
      if (sql.includes("PRAGMA table_info('conversations')")) {
        return { all: () => CONVERSATION_COLUMNS.map((name) => ({ name })) };
      }
      if (sql.includes('FROM conversations')) {
        return { all: () => dealers.map((row) => ({ ...row })) };
      }
      if (sql.includes("PRAGMA table_info('bridge_outbound')")) {
        return { all: () => BRIDGE_COLUMNS.map((name) => ({ name })) };
      }
      if (sql.includes('FROM bridge_outbound')) {
        return {
          all: (body) => bridgeRows
            .filter((row) => row.processing_ts != null && row.sent_ts == null && row.body === body)
            .map((row) => ({ ...row })),
        };
      }
      throw new Error(`unexpected SQL on ${dbPath}: ${sql}`);
    },
    close() {},
  });
}

function fakeUnderlying() {
  const calls = [];
  let connected = false;
  return {
    calls,
    async initialize() { connected = true; calls.push(['initialize']); return { connected: true }; },
    isConnected() { return connected; },
    async sendText(args) { calls.push(['text', args]); return { ok: true, wa_msg_id: 'wamid.text' }; },
    async sendTemplate(args) { calls.push(['template', args]); return { ok: true, wa_msg_id: 'wamid.template' }; },
    async sendDocument(args) { calls.push(['document', args]); return { ok: true, wa_msg_id: 'wamid.document' }; },
    async shutdown() { connected = false; calls.push(['shutdown']); },
  };
}

function optedInDealer(overrides = {}) {
  return {
    dealer_id: 'dealer-1',
    phone_number: '+39 333 123',
    last_inbound_at: null,
    whatsapp_opt_in: 1,
    whatsapp_opt_in_at: '2026-08-20T10:00:00Z',
    whatsapp_opt_in_source: 'website_form',
    whatsapp_opt_in_evidence_id: 'consent-1',
    whatsapp_opt_out_at: null,
    ...overrides,
  };
}

function policy({ dealer, bridgeRows = [], nowMs = Date.parse('2026-08-23T10:00:00Z') } = {}) {
  const transport = fakeUnderlying();
  const env = { ARGOS_DB_PATH: '/primary.sqlite', BRIDGE_DB_PATH: '/bridge.sqlite' };
  const databaseFactory = fakeDatabaseFactory({ dealers: [dealer], bridgeRows });
  return {
    transport,
    policy: new CloudPolicyTransport({ transport, env, databaseFactory, nowFn: () => nowMs }),
  };
}

test('33 traceable opt-in requires source, evidence, timestamp and no revocation', () => {
  assert.equal(consentValid(optedInDealer()), true);
  assert.equal(consentValid(optedInDealer({ whatsapp_opt_in_source: '' })), false);
  assert.equal(consentValid(optedInDealer({ whatsapp_opt_in_evidence_id: '' })), false);
  assert.equal(consentValid(optedInDealer({ whatsapp_opt_out_at: '2026-08-22T10:00:00Z' })), false);
});

test('34 inside 24h customer-service window uses free-form text only', async () => {
  const now = Date.parse('2026-08-23T10:00:00Z');
  const dealer = optedInDealer({
    whatsapp_opt_in: 0,
    whatsapp_opt_in_at: null,
    whatsapp_opt_in_source: null,
    whatsapp_opt_in_evidence_id: null,
    last_inbound_at: new Date(now - CUSTOMER_SERVICE_WINDOW_MS + 1000).toISOString(),
  });
  const { policy: wrapped, transport } = policy({ dealer, nowMs: now });
  const result = await wrapped.sendText({ phone: '39333123', body: 'risposta' });
  assert.equal(result.wa_msg_id, 'wamid.text');
  assert.equal(transport.calls.filter(([kind]) => kind === 'text').length, 1);
  assert.equal(transport.calls.filter(([kind]) => kind === 'template').length, 0);
});

test('35 outside 24h without traceable opt-in blocks before transport', async () => {
  const dealer = optedInDealer({ whatsapp_opt_in: 0, whatsapp_opt_in_at: null });
  const { policy: wrapped, transport } = policy({ dealer });
  await assert.rejects(
    () => wrapped.sendText({ phone: '39333123', body: 'proattivo' }),
    (err) => err.code === 'WHATSAPP_OPT_IN_REQUIRED',
  );
  assert.equal(transport.calls.length, 0);
});

test('36 outside 24h requires exactly the claimed bridge Meta template', async () => {
  const dealer = optedInDealer();
  const template = { name: 'argos_day1_it', language: { code: 'it' }, components: [] };
  const bridgeRows = [{
    id: 'row-1',
    target_phone: '39333123',
    body: 'proattivo',
    processing_ts: 123,
    sent_ts: null,
    meta_template_json: JSON.stringify(template),
    whatsapp_opt_in_evidence_id: 'consent-1',
  }];
  const { policy: wrapped, transport } = policy({ dealer, bridgeRows });
  const result = await wrapped.sendText({ phone: '+39 333 123', body: 'proattivo' });
  assert.equal(result.wa_msg_id, 'wamid.template');
  const calls = transport.calls.filter(([kind]) => kind === 'template');
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0][1].template, template);
  assert.equal(transport.calls.filter(([kind]) => kind === 'text').length, 0);
});

test('37 queued opt-in evidence cannot survive consent replacement', async () => {
  const dealer = optedInDealer({ whatsapp_opt_in_evidence_id: 'consent-new' });
  const bridgeRows = [{
    id: 'row-old',
    target_phone: '39333123',
    body: 'proattivo',
    processing_ts: 123,
    sent_ts: null,
    meta_template_json: JSON.stringify({ name: 'argos_day1_it', language: { code: 'it' } }),
    whatsapp_opt_in_evidence_id: 'consent-old',
  }];
  const { policy: wrapped, transport } = policy({ dealer, bridgeRows });
  await assert.rejects(
    () => wrapped.sendText({ phone: '39333123', body: 'proattivo' }),
    (err) => err.code === 'WHATSAPP_OPT_IN_EVIDENCE_MISMATCH',
  );
  assert.equal(transport.calls.length, 0);
});

test('38 free-form document outside 24h is blocked before upload', async () => {
  const { policy: wrapped, transport } = policy({ dealer: optedInDealer() });
  await assert.rejects(
    () => wrapped.sendDocument({ phone: '39333123', filePath: '/tmp/x.pdf', caption: 'x' }),
    (err) => err.code === 'META_TEMPLATE_REQUIRED',
  );
  assert.equal(transport.calls.length, 0);
});

test('39 initialization fails closed when machine-local DB paths are absent', async () => {
  const transport = fakeUnderlying();
  const noPrimary = new CloudPolicyTransport({ transport, env: { BRIDGE_DB_PATH: '/bridge.sqlite' } });
  await assert.rejects(() => noPrimary.initialize(), (err) => err.code === 'TRANSPORT_CONFIG_MISSING');
  const noBridge = new CloudPolicyTransport({ transport, env: { ARGOS_DB_PATH: '/primary.sqlite' } });
  await assert.rejects(() => noBridge.initialize(), (err) => err.code === 'TRANSPORT_CONFIG_MISSING');
  assert.equal(transport.calls.length, 0);
});
