'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');

const source = fs.readFileSync(path.join(__dirname, '../wa-intelligence/tools/argos_c10_pairing_helper.js'), 'utf8');
const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function harness(t, options = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'argos-pair-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const env = {
    ARGOS_PAIR_DATA_PATH: path.join(root, 'auth'),
    ARGOS_PAIR_QR_FILE: path.join(root, 'qr.txt'),
    ARGOS_PAIR_STATUS_FILE: path.join(root, 'status'),
    ARGOS_PAIR_CHROME: path.join(root, 'chrome'),
    ARGOS_PAIR_CLIENT_ID: 'argos-business',
    ...options.env,
  };
  fs.writeFileSync(env.ARGOS_PAIR_CHROME, 'mock');
  const exits = [], timers = new Map(), requested = [];
  let nextTimer = 0, instance;
  class FakeClient extends EventEmitter {
    constructor(config) { super(); this.config = config; this.initializeCount = 0; this.destroyCount = 0; instance = this; }
    initialize() { this.initializeCount++; return options.initialize ? options.initialize() : Promise.resolve(); }
    destroy() { this.destroyCount++; return options.destroy ? options.destroy() : Promise.resolve(); }
  }
  class FakeLocalAuth { constructor(config) { this.config = config; } }
  const processMock = new EventEmitter();
  processMock.env = env;
  processMock.pid = 12345;
  processMock.exit = code => { exits.push(code); };
  const fakeRequire = name => {
    requested.push(name);
    if (name === 'fs') return options.fs || fs;
    if (name === 'path') return path;
    if (name === 'qrcode') return { toDataURL: options.qr || (async () => 'data:image/png;base64,bW9jaw==') };
    if (name === 'whatsapp-web.js') return { Client: FakeClient, LocalAuth: FakeLocalAuth };
    throw new Error(`Unexpected dependency: ${name}`);
  };
  vm.runInNewContext(source, {
    require: fakeRequire, process: processMock,
    setTimeout(fn, ms) { const id = ++nextTimer; timers.set(id, { fn, ms }); return id; },
    clearTimeout(id) { timers.delete(id); },
  }, { filename: 'argos_c10_pairing_helper.js' });
  const status = () => fs.existsSync(env.ARGOS_PAIR_STATUS_FILE) ? fs.readFileSync(env.ARGOS_PAIR_STATUS_FILE, 'utf8').trim() : null;
  return { root, env, exits, timers, requested, process: processMock, get client() { return instance; }, status,
    async emit(event, value) { instance.emit(event, value); await flush(); },
  };
}

test('READY is not published until browser destruction completes', async t => {
  const shutdown = deferred();
  const h = harness(t, { destroy: () => shutdown.promise });
  await h.emit('ready');
  assert.notEqual(h.status(), 'READY');
  assert.deepEqual(h.exits, []);
  assert.equal(h.client.destroyCount, 1);
  shutdown.resolve(); await flush();
  assert.equal(h.status(), 'READY');
  assert.deepEqual(h.exits, [0]);
  assert.equal(h.client.initializeCount, 1);
});

test('destroy failure cannot publish successful READY', async t => {
  const h = harness(t, { destroy: () => Promise.reject(new Error('browser still open')) });
  await h.emit('ready');
  assert.notEqual(h.status(), 'READY');
  assert.deepEqual(h.exits, [25]);
});

test('late asynchronous QR result cannot overwrite terminal state', async t => {
  const qr = deferred();
  const h = harness(t, { qr: () => qr.promise });
  await h.emit('qr', 'secret-qr');
  await h.emit('auth_failure');
  qr.resolve('data:image/png;base64,bW9jaw=='); await flush();
  assert.equal(h.status(), 'AUTH_FAILURE');
  assert.equal(fs.existsSync(h.env.ARGOS_PAIR_QR_FILE), false);
  assert.deepEqual(h.exits, [21]);
});

test('first QR is captured once, mode 0600, with no re-generation', async t => {
  let calls = 0;
  const h = harness(t, { qr: async () => { calls++; return 'data:image/png;base64,bW9jaw=='; } });
  await h.emit('qr', 'first'); await h.emit('qr', 'second');
  assert.equal(calls, 1);
  assert.equal(h.status(), 'QR_READY');
  assert.equal(fs.readFileSync(h.env.ARGOS_PAIR_QR_FILE, 'utf8').trim(), 'data:image/png;base64,bW9jaw==');
  assert.equal(fs.statSync(h.env.ARGOS_PAIR_QR_FILE).mode & 0o777, 0o600);
  assert.equal(fs.statSync(h.env.ARGOS_PAIR_STATUS_FILE).mode & 0o777, 0o600);
  assert.deepEqual(h.exits, []);
});

test('competing terminal events destroy only once and preserve first verdict', async t => {
  const shutdown = deferred();
  const h = harness(t, { destroy: () => shutdown.promise });
  h.client.emit('auth_failure'); h.client.emit('ready'); h.client.emit('disconnected');
  h.client.emit('qr', 'late');
  shutdown.resolve(); await flush();
  assert.equal(h.status(), 'AUTH_FAILURE');
  assert.equal(h.client.destroyCount, 1);
  assert.deepEqual(h.exits, [21]);
});

test('QR render failure closes the client and fails closed', async t => {
  const h = harness(t, { qr: () => Promise.reject(new Error('render')) });
  await h.emit('qr', 'secret');
  assert.equal(h.status(), 'QR_RENDER_FAILED');
  assert.deepEqual(h.exits, [20]);
});

test('initialize rejection is a terminal failure', async t => {
  const h = harness(t, { initialize: () => Promise.reject(new Error('init')) });
  await flush();
  assert.equal(h.status(), 'INIT_FAILED');
  assert.deepEqual(h.exits, [24]);
});

test('timeout closes client and prevents subsequent success', async t => {
  const h = harness(t);
  assert.equal(h.timers.size, 1);
  const timer = [...h.timers.values()][0];
  assert.equal(timer.ms, 360000);
  timer.fn(); await flush();
  await h.emit('ready');
  assert.equal(h.status(), 'TIMEOUT');
  assert.deepEqual(h.exits, [23]);
});

test('missing required configuration fails before client initialization', t => {
  assert.throws(() => harness(t, { env: { ARGOS_PAIR_DATA_PATH: '' } }), /requires staging/);
});

test('shutdown timeout fails closed and never publishes READY', async t => {
  const h = harness(t, { destroy: () => new Promise(() => {}) });
  await h.emit('ready');
  assert.equal(h.status(), 'STOPPING');
  const shutdown = [...h.timers.values()].find(timer => timer.ms === 30000);
  assert.ok(shutdown);
  shutdown.fn(); await flush();
  assert.equal(h.status(), 'DESTROY_FAILED');
  assert.deepEqual(h.exits, [25]);
});

test('authentication before QR rendering completes cannot regress state', async t => {
  const qr = deferred();
  const h = harness(t, { qr: () => qr.promise });
  await h.emit('qr', 'secret-qr');
  await h.emit('authenticated');
  qr.resolve('data:image/png;base64,bW9jaw=='); await flush();
  assert.equal(h.status(), 'AUTHENTICATED');
  assert.equal(fs.existsSync(h.env.ARGOS_PAIR_QR_FILE), false);
});

test('synchronous initialize exception is caught and fails closed', async t => {
  const h = harness(t, { initialize: () => { throw new Error('sync init'); } });
  await flush();
  assert.equal(h.status(), 'INIT_FAILED');
  assert.deepEqual(h.exits, [24]);
});


test('authentication without QR completes without QR retrieval or rendering', async t => {
  let renders = 0;
  const h = harness(t, { qr: async () => { renders++; return 'unused'; } });
  await h.emit('authenticated');
  assert.equal(h.status(), 'AUTHENTICATED_NO_QR');
  await h.emit('ready');
  assert.equal(h.status(), 'READY');
  assert.equal(renders, 0);
  assert.equal(fs.existsSync(h.env.ARGOS_PAIR_QR_FILE), false);
  assert.deepEqual(h.exits, [0]);
});

for (const authenticated of [false, true]) {
  test(`disconnect authenticated=${authenticated} is terminal`, async t => {
    const h = harness(t);
    if (authenticated) await h.emit('authenticated');
    await h.emit('disconnected');
    await h.emit('ready');
    await h.emit('authenticated');
    assert.equal(h.status(), authenticated ? 'DISCONNECTED_AFTER_AUTH' : 'DISCONNECTED');
    assert.deepEqual(h.exits, [22]);
    assert.equal(h.client.destroyCount, 1);
  });
}

for (const [signal, code] of [['SIGTERM', 143], ['SIGINT', 130]]) {
  test(`${signal} destroys once and prevents late READY`, async t => {
    const h = harness(t);
    h.client.emit('qr', 'mock');
    h.process.emit(signal);
    await flush();
    await h.emit('ready');
    assert.equal(h.status(), 'TERMINATED');
    assert.deepEqual(h.exits, [code]);
    assert.equal(h.client.destroyCount, 1);
  });
}

test('READY status write failure exits nonzero', async t => {
  const h = harness(t, { fs: { ...fs, writeFileSync(file, value, options) {
    if (value === 'READY\n') throw new Error('disk full');
    return fs.writeFileSync(file, value, options);
  } } });
  await h.emit('ready');
  assert.equal(h.status(), 'STOPPING');
  assert.deepEqual(h.exits, [25]);
});

test('pairing uses only staged filesystem and allowed dependencies, never send/resume/DB', async t => {
  const paths = [];
  const tracked = { ...fs };
  for (const method of ['existsSync', 'mkdirSync', 'writeFileSync', 'chmodSync', 'renameSync']) {
    tracked[method] = (...args) => { paths.push(args[0]); if (method === 'renameSync') paths.push(args[1]); return fs[method](...args); };
  }
  const h = harness(t, { fs: tracked });
  h.client.sendMessage = () => assert.fail('outbound forbidden');
  await h.emit('qr', 'mock');
  await h.emit('authenticated');
  await h.emit('ready');
  assert.deepEqual(h.requested, ['fs', 'path', 'qrcode', 'whatsapp-web.js']);
  assert.ok(paths.every(p => p.startsWith(h.root + path.sep)));
  assert.equal(h.client.config.authStrategy.config.clientId, 'argos-business');
  assert.equal(h.client.config.authStrategy.config.dataPath, h.env.ARGOS_PAIR_DATA_PATH);
});
