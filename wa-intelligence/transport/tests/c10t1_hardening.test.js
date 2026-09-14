'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const { CloudApiTransport } = require('../cloud_api_transport');

function env() {
  return {
    META_GRAPH_API_VERSION: 'v25.0',
    META_WA_ACCESS_TOKEN: 'test-token-not-real',
    META_WA_PHONE_NUMBER_ID: '123456789',
    META_WA_WABA_ID: '987654321',
    META_WA_WEBHOOK_VERIFY_TOKEN: 'verify-test',
    META_APP_SECRET: 'app-secret-test',
  };
}

function response(statusCode, payload) {
  return { statusCode, headers: {}, body: Buffer.from(JSON.stringify(payload), 'utf8') };
}

test('27 authorization failure after initialize drops connected health state', async () => {
  const config = env();
  let calls = 0;
  const transport = new CloudApiTransport({
    env: config,
    requestFn: async (request) => {
      calls += 1;
      if (request.method === 'GET') return response(200, { id: config.META_WA_PHONE_NUMBER_ID });
      return response(401, { error: { code: 190, type: 'OAuthException' } });
    },
  });
  await transport.initialize();
  assert.equal(transport.isConnected(), true);
  await assert.rejects(() => transport.sendText({ phone: '39333123', body: 'ciao' }));
  assert.equal(transport.isConnected(), false);
  assert.equal(calls, 2);
});

test('28 HTTP 5xx on final message delivery is non-retryable ambiguous outcome', async () => {
  const config = env();
  let posts = 0;
  const transport = new CloudApiTransport({
    env: config,
    requestFn: async (request) => {
      if (request.method === 'GET') return response(200, { id: config.META_WA_PHONE_NUMBER_ID });
      posts += 1;
      return response(503, { error: { code: 2, type: 'ServerError' } });
    },
  });
  await transport.initialize();
  await assert.rejects(
    () => transport.sendText({ phone: '39333123', body: 'ciao' }),
    (err) => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS' && err.ambiguous === true && err.transient === false,
  );
  assert.equal(posts, 1);
});

test('29 media-upload 5xx is not mislabeled as dealer-delivery ambiguity', async () => {
  const fs = require('node:fs');
  const os = require('node:os');
  const path = require('node:path');
  const config = env();
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'argos-c10t1-hardening-'));
  const filePath = path.join(dir, 'dealer.pdf');
  fs.writeFileSync(filePath, 'pdf-test');
  let posts = 0;
  try {
    const transport = new CloudApiTransport({
      env: config,
      requestFn: async (request) => {
        if (request.method === 'GET') return response(200, { id: config.META_WA_PHONE_NUMBER_ID });
        posts += 1;
        return response(503, { error: { code: 2, type: 'ServerError' } });
      },
    });
    await transport.initialize();
    await assert.rejects(
      () => transport.sendDocument({ phone: '39333123', filePath, caption: 'dossier' }),
      (err) => err.code === 'TRANSPORT_REMOTE_ERROR' && err.ambiguous === false,
    );
    assert.equal(posts, 1);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
