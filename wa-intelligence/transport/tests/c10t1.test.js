'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');

const {
  CloudApiTransport,
  createTransport,
  validateCloudEnvironment,
} = require('..');
const { TransportError } = require('../errors');
const { WwebjsTransport } = require('../wwebjs_transport');
const {
  createBoundedSeenSet,
  processWebhookPayload,
  verifyWebhookChallenge,
  verifyWebhookSignature,
} = require('../webhook');

function cloudEnv(overrides = {}) {
  return {
    ARGOS_WA_TRANSPORT: 'cloud',
    META_GRAPH_API_VERSION: 'v25.0',
    META_WA_ACCESS_TOKEN: 'test-token-not-real',
    META_WA_PHONE_NUMBER_ID: '123456789',
    META_WA_WABA_ID: '987654321',
    META_WA_WEBHOOK_VERIFY_TOKEN: 'verify-test',
    META_APP_SECRET: 'app-secret-test',
    ...overrides,
  };
}

function response(statusCode, payload) {
  return {
    statusCode,
    headers: {},
    body: Buffer.from(JSON.stringify(payload), 'utf8'),
  };
}

async function initializedTransport(requestFn, env = cloudEnv()) {
  const transport = new CloudApiTransport({ env, requestFn });
  await transport.initialize();
  return transport;
}

test('01 cloud environment fails closed when required values are missing', () => {
  assert.throws(() => validateCloudEnvironment({ ARGOS_WA_TRANSPORT: 'cloud' }), /configuration incomplete/);
});

test('02 cloud graph version defaults when omitted', () => {
  const env = cloudEnv();
  delete env.META_GRAPH_API_VERSION;
  const transport = new CloudApiTransport({ env, requestFn: async () => response(200, { id: env.META_WA_PHONE_NUMBER_ID }) });
  assert.equal(transport.graphVersion, 'v25.0');
});

test('03 unsupported transport mode fails closed', () => {
  assert.throws(() => createTransport({ env: { ARGOS_WA_TRANSPORT: 'other' } }), /Unsupported WhatsApp transport/);
});

test('04 cloud factory returns CloudApiTransport only with complete env', () => {
  const transport = createTransport({ env: cloudEnv(), requestFn: async () => response(200, {}) });
  assert.ok(transport instanceof CloudApiTransport);
});

test('05 cloud initialize performs read-only phone id validation', async () => {
  const calls = [];
  const env = cloudEnv();
  const transport = new CloudApiTransport({
    env,
    requestFn: async (request) => {
      calls.push(request);
      return response(200, { id: env.META_WA_PHONE_NUMBER_ID, display_phone_number: '+39 000' });
    },
  });
  const result = await transport.initialize();
  assert.equal(result.connected, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].method, 'GET');
  assert.match(calls[0].path, /fields=id,display_phone_number/);
  assert.doesNotMatch(calls[0].path, /messages/);
});

test('06 cloud initialize failure leaves transport disconnected', async () => {
  const transport = new CloudApiTransport({ env: cloudEnv(), requestFn: async () => response(401, { error: { code: 190 } }) });
  await assert.rejects(() => transport.initialize(), TransportError);
  assert.equal(transport.isConnected(), false);
});

test('07 cloud text payload has official WhatsApp message shape', async () => {
  const calls = [];
  const env = cloudEnv();
  const transport = await initializedTransport(async (request) => {
    calls.push(request);
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    return response(200, { messages: [{ id: 'wamid.text.1' }] });
  }, env);
  await transport.sendText({ phone: '+39 333-123', body: 'ciao' });
  const send = calls[1];
  const payload = JSON.parse(send.body.toString('utf8'));
  assert.equal(payload.messaging_product, 'whatsapp');
  assert.equal(payload.recipient_type, 'individual');
  assert.equal(payload.to, '39333123');
  assert.equal(payload.type, 'text');
  assert.deepEqual(payload.text, { preview_url: false, body: 'ciao' });
});

test('08 cloud text returns real Meta message id', async () => {
  const env = cloudEnv();
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    return response(200, { messages: [{ id: 'wamid.returned.by.meta' }] });
  }, env);
  const result = await transport.sendText({ phone: '39333123', body: 'ciao' });
  assert.equal(result.wa_msg_id, 'wamid.returned.by.meta');
});

test('09 explicit Graph 400 fails closed with sanitized metadata', async () => {
  const env = cloudEnv();
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    return response(400, { error: { code: 100, type: 'OAuthException', message: 'remote detail' } });
  }, env);
  await assert.rejects(
    () => transport.sendText({ phone: '39333123', body: 'ciao' }),
    (err) => err.code === 'TRANSPORT_REMOTE_ERROR' && err.statusCode === 400 && err.metaCode === 100,
  );
});

test('10 explicit Graph 500 performs zero internal retries', async () => {
  const env = cloudEnv();
  let postCalls = 0;
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    postCalls += 1;
    return response(500, { error: { code: 2, type: 'ServerError' } });
  }, env);
  await assert.rejects(() => transport.sendText({ phone: '39333123', body: 'ciao' }));
  assert.equal(postCalls, 1);
});

test('11 ambiguous delivery performs zero automatic retries', async () => {
  const env = cloudEnv();
  let postCalls = 0;
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    postCalls += 1;
    throw new TransportError('TRANSPORT_DELIVERY_AMBIGUOUS', 'ambiguous', { ambiguous: true });
  }, env);
  await assert.rejects(
    () => transport.sendText({ phone: '39333123', body: 'ciao' }),
    (err) => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS',
  );
  assert.equal(postCalls, 1);
});

test('12 missing Meta message id is rejected rather than invented', async () => {
  const env = cloudEnv();
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    return response(200, { messages: [{}] });
  }, env);
  await assert.rejects(
    () => transport.sendText({ phone: '39333123', body: 'ciao' }),
    (err) => err.code === 'TRANSPORT_INVALID_RESPONSE',
  );
});

test('13 document requires an existing local file before any upload', async () => {
  const env = cloudEnv();
  let postCalls = 0;
  const transport = await initializedTransport(async (request) => {
    if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
    postCalls += 1;
    return response(200, {});
  }, env);
  await assert.rejects(() => transport.sendDocument({ phone: '39333123', filePath: '/definitely/missing.pdf', caption: 'x' }));
  assert.equal(postCalls, 0);
});

test('14 document performs media upload then message send', async () => {
  const env = cloudEnv();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'argos-c10t1-'));
  const filePath = path.join(dir, 'dealer.pdf');
  fs.writeFileSync(filePath, 'pdf-test');
  const calls = [];
  try {
    const transport = await initializedTransport(async (request) => {
      calls.push(request);
      if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
      if (request.path.endsWith('/media')) return response(200, { id: 'media-1' });
      return response(200, { messages: [{ id: 'wamid.doc.1' }] });
    }, env);
    const result = await transport.sendDocument({ phone: '39333123', filePath, caption: 'dossier' });
    assert.equal(result.media_id, 'media-1');
    assert.equal(result.wa_msg_id, 'wamid.doc.1');
    assert.equal(calls.filter((call) => call.method === 'POST').length, 2);
    const sendPayload = JSON.parse(calls[2].body.toString('utf8'));
    assert.equal(sendPayload.document.id, 'media-1');
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('15 failed media upload never attempts recipient message send', async () => {
  const env = cloudEnv();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'argos-c10t1-'));
  const filePath = path.join(dir, 'dealer.pdf');
  fs.writeFileSync(filePath, 'pdf-test');
  let postCalls = 0;
  try {
    const transport = await initializedTransport(async (request) => {
      if (request.method === 'GET') return response(200, { id: env.META_WA_PHONE_NUMBER_ID });
      postCalls += 1;
      return response(400, { error: { code: 100 } });
    }, env);
    await assert.rejects(() => transport.sendDocument({ phone: '39333123', filePath, caption: 'dossier' }));
    assert.equal(postCalls, 1);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('16 cloud shutdown clears connected state', async () => {
  const env = cloudEnv();
  const transport = await initializedTransport(async () => response(200, { id: env.META_WA_PHONE_NUMBER_ID }), env);
  assert.equal(transport.isConnected(), true);
  await transport.shutdown();
  assert.equal(transport.isConnected(), false);
});

test('17 wwebjs module is lazy-loaded only during initialize', () => {
  let loads = 0;
  const transport = new WwebjsTransport({ moduleLoader: () => { loads += 1; return {}; } });
  assert.ok(transport);
  assert.equal(loads, 0);
});

function fakeWwebModule({ registered = true } = {}) {
  const handlers = {};
  const sent = [];
  class LocalAuth { constructor(options) { this.options = options; } }
  class Client {
    constructor(options) { this.options = options; }
    on(name, handler) { handlers[name] = handler; }
    async initialize() { handlers.ready?.(); }
    async isRegisteredUser() { return registered; }
    async sendMessage(...args) { sent.push(args); return { id: { _serialized: 'wamid.legacy.1' } }; }
    async destroy() {}
  }
  const MessageMedia = { fromFilePath: (filePath) => ({ filePath }) };
  return { module: { Client, LocalAuth, MessageMedia }, handlers, sent };
}

test('18 wwebjs ready event controls connected state', async () => {
  const fake = fakeWwebModule();
  const transport = new WwebjsTransport({ moduleLoader: () => fake.module, env: {} });
  await transport.initialize();
  assert.equal(transport.isConnected(), true);
});

test('19 wwebjs sendText uses the legacy primitive only after registration check', async () => {
  const fake = fakeWwebModule();
  const transport = new WwebjsTransport({ moduleLoader: () => fake.module, env: {} });
  await transport.initialize();
  const result = await transport.sendText({ phone: '39333123', body: 'legacy' });
  assert.equal(result.wa_msg_id, 'wamid.legacy.1');
  assert.equal(fake.sent.length, 1);
});

test('20 wwebjs rejects unregistered targets before sendMessage', async () => {
  const fake = fakeWwebModule({ registered: false });
  const transport = new WwebjsTransport({ moduleLoader: () => fake.module, env: {} });
  await transport.initialize();
  await assert.rejects(() => transport.sendText({ phone: '39333123', body: 'legacy' }), /not registered/);
  assert.equal(fake.sent.length, 0);
});

test('21 webhook signature accepts correct HMAC over raw body', () => {
  const raw = Buffer.from('{"object":"whatsapp_business_account"}');
  const secret = 'secret';
  const signature = `sha256=${crypto.createHmac('sha256', secret).update(raw).digest('hex')}`;
  assert.equal(verifyWebhookSignature(raw, signature, secret), true);
});

test('22 webhook signature rejects invalid or absent signatures', () => {
  const raw = Buffer.from('{}');
  assert.equal(verifyWebhookSignature(raw, 'sha256=bad', 'secret'), false);
  assert.equal(verifyWebhookSignature(raw, '', 'secret'), false);
});

test('23 webhook verification challenge requires matching token and subscribe mode', () => {
  const good = new URLSearchParams('hub.mode=subscribe&hub.verify_token=verify-test&hub.challenge=12345');
  const bad = new URLSearchParams('hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=12345');
  assert.equal(verifyWebhookChallenge(good, 'verify-test'), '12345');
  assert.equal(verifyWebhookChallenge(bad, 'verify-test'), null);
});

test('24 webhook text message normalizes to existing inbound shape', async () => {
  const inbound = [];
  const payload = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ field: 'messages', value: { messages: [{ id: 'wamid.in.1', from: '39333123', type: 'text', text: { body: 'ciao' } }] } }] }],
  };
  await processWebhookPayload(payload, { onInbound: async (msg) => inbound.push(msg) });
  assert.equal(inbound.length, 1);
  assert.equal(inbound[0].from, '39333123@c.us');
  assert.equal(inbound[0].id._serialized, 'wamid.in.1');
});

test('25 webhook statuses are audit/callback only and never inbound', async () => {
  const inbound = [];
  const statuses = [];
  const payload = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ field: 'messages', value: { statuses: [{ id: 'wamid.out.1', status: 'delivered', recipient_id: '39333123' }] } }] }],
  };
  await processWebhookPayload(payload, {
    onInbound: async (msg) => inbound.push(msg),
    onStatus: (status) => statuses.push(status),
  });
  assert.equal(inbound.length, 0);
  assert.equal(statuses.length, 1);
  assert.equal(statuses[0].status, 'delivered');
});

test('26 coexistence echoes dedupe and history/state sync never become inbound', async () => {
  const inbound = [];
  const audit = [];
  const seenEchoes = createBoundedSeenSet();
  const echoChange = { field: 'smb_message_echoes', value: { messages: [{ id: 'wamid.echo.1', to: '39333123' }] } };
  const payload = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [echoChange, echoChange, { field: 'history', value: {} }, { field: 'smb_app_state_sync', value: {} }] }],
  };
  await processWebhookPayload(payload, {
    onInbound: async (msg) => inbound.push(msg),
    onAudit: (event, data) => audit.push({ event, data }),
    seenEchoes,
  });
  assert.equal(inbound.length, 0);
  assert.equal(audit.filter((item) => item.event === 'ECHO_FROM_BUSINESS_APP').length, 1);
  assert.equal(audit.filter((item) => item.event === 'WHATSAPP_COEXISTENCE_SYNC_IGNORED').length, 2);
});
