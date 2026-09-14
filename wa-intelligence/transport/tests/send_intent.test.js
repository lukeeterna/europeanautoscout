'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
// Use the exact production SQLite driver installed from the lockfile.
const DatabaseSync = require('better-sqlite3');
const { TransportError } = require('../errors');
const source = fs.readFileSync(path.join(__dirname, '../../wa-daemon.js'), 'utf8');
const schema = source.slice(source.indexOf('function tableColumns('), source.indexOf('function ensureBridgeSchema('));
const boundary = source.slice(source.indexOf('function persistOutbound('), source.indexOf('\nfunction persistInbound('));
const request = { dealerId: 'fixture', phone: '390000000001', templateId: 'TEST', message: 'mock only' };

function runtime(t, opts = {}) {
  const root = opts.root || fs.mkdtempSync(path.join(os.tmpdir(), 'argos-intent-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const filename = path.join(root, 'primary.sqlite');
  let db, ctx, sends = 0;
  function open() {
    db = new DatabaseSync(filename);
    db.pragma('journal_mode = WAL');
    db.pragma('synchronous = FULL');
    ctx = vm.createContext({ db, fs, TransportError, MAX_BODY_CHARS: 4000, TRANSPORT_MODE: 'wwebjs',
      POST_SEND_UPDATE: 'mock', DB_PATH: filename,
      nowIso: () => new Date().toISOString(),
      sha256: value => crypto.createHash('sha256').update(value).digest('hex'),
      normalizePhone: x => x, getDealerById: () => ({ dealer_id: 'fixture' }),
      assertTransportPreconditions: () => {}, verifyDossierMetadata: () => {},
      finalPolicyGuard: () => { if (opts.policyError) throw new Error('policy'); return { ok: true }; },
      runPythonJson: () => opts.updateError ? { status: 1, json: { ok: false } } : ({ status: 0, json: { ok: true } }), audit: () => {},
      activeTransport: { sendText: async () => { sends++; return opts.send ? opts.send() : { wa_msg_id: 'mock-id' }; } },
    });
    vm.runInContext(`class GuardError extends Error { constructor(code, message, {transient=false}={}) { super(message); this.code=code; this.transient=transient; } }\n${schema}\nensurePrimarySchema();\n${boundary}`, ctx);
  }
  open();
  t.after(() => db.close());
  return { send: (r = request) => ctx.guardedSend(r), get db() { return db; },
    get sends() { return sends; }, restart() { db.close(); open(); } };
}

test('concurrent duplicate intent invokes transport once', async t => {
  let resolve;
  const wait = new Promise(r => { resolve = r; });
  const h = runtime(t, { send: () => wait });
  const first = h.send();
  await assert.rejects(h.send(), err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS');
  resolve({ wa_msg_id: 'mock-id' });
  await first;
  assert.equal(h.sends, 1);
});

test('successful duplicate after restart returns stored message id without sending', async t => {
  const h = runtime(t);
  const first = await h.send();
  h.restart();
  const second = await h.send();
  assert.equal(second.wa_msg_id, first.wa_msg_id);
  assert.equal(h.sends, 1);
  assert.equal(h.db.prepare('SELECT count(*) n FROM messages').get().n, 1);
});

test('uncertain failure persists through restart and changed caller key', async t => {
  const h = runtime(t, { send: () => { throw new Error('unknown outcome'); } });
  await assert.rejects(h.send());
  h.restart();
  await assert.rejects(h.send({ ...request, idempotencyKey: 'another-key' }), err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS');
  assert.equal(h.sends, 1);
});

test('DB persistence failure after delivery never resends', async t => {
  const h = runtime(t);
  h.db.exec("CREATE TRIGGER fail_outbound BEFORE INSERT ON messages BEGIN SELECT RAISE(ABORT, 'disk failure fixture'); END;");
  await assert.rejects(h.send());
  h.restart();
  await assert.rejects(h.send(), err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS');
  assert.equal(h.sends, 1);
});

test('pre-policy error contacts nobody', async t => {
  const h = runtime(t, { policyError: true });
  await assert.rejects(h.send());
  assert.equal(h.sends, 0);
});

test('known pre-send not-ready failure may safely retry', async t => {
  let calls = 0;
  const h = runtime(t, { send: () => { if (++calls === 1) throw new TransportError('TRANSPORT_NOT_READY', 'not ready', {transient:true}); return {wa_msg_id:'mock-id'}; } });
  await assert.rejects(h.send());
  await h.send();
  assert.equal(calls, 2);
  assert.equal(h.db.prepare('SELECT count(*) n FROM messages').get().n, 1);
});

test('caller key cannot be reused for a different request', async t => {
  const h = runtime(t);
  await h.send({ ...request, idempotencyKey: 'test-key' });
  await assert.rejects(h.send({ ...request, idempotencyKey: 'test-key', message: 'changed' }), err => err.code === 'IDEMPOTENCY_CONFLICT');
  assert.equal(h.sends, 1);
});


test('failed post-send state update retains delivered evidence and blocks replay', async t => {
  const h = runtime(t, { updateError: true });
  await assert.rejects(h.send(), err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS');
  h.restart();
  await assert.rejects(h.send(), err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS');
  assert.equal(h.sends, 1);
  assert.equal(h.db.prepare('SELECT status FROM argos_send_intents').get().status, 'DELIVERED');
  assert.equal(h.db.prepare('SELECT wa_msg_id FROM argos_send_intents').get().wa_msg_id, 'mock-id');
});


test('real process exit during send leaves durable intent blocking recovery resend', t => {
  const { spawnSync } = require('node:child_process');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'argos-crash-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const prefix = fs.readFileSync(__filename, 'utf8').split("test('concurrent duplicate")[0];
  const child = spawnSync(process.execPath, ['-e', prefix + "\nconst h=runtime({after(){}}, {root:process.env.ARGOS_TEST_ROOT, send:()=>process.exit(78)}); h.send();"],
    { cwd: __dirname, env: { ...process.env, ARGOS_TEST_ROOT: root }, encoding: 'utf8', timeout: 5000 });
  assert.equal(child.status, 78, child.stderr);
  const h = runtime(t, { root });
  return assert.rejects(h.send(), err => {
    assert.equal(h.sends, 0);
    assert.equal(h.db.prepare('SELECT status FROM argos_send_intents').get().status, 'IN_FLIGHT');
    return err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS';
  });
});
