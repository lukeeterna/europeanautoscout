'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { WwebjsTransport } = require('../wwebjs_transport');

for (const kind of ['text', 'document']) {
  for (const outcome of ['reject', 'missing-id']) {
    test(`${kind}: ${outcome} after sendMessage is ambiguous and nonretryable`, async () => {
      let sends = 0;
      const t = new WwebjsTransport();
      t.connected = true;
      t.MessageMedia = { fromFilePath: () => ({}) };
      t.client = { isRegisteredUser: async () => true, sendMessage: async () => {
        sends++;
        if (outcome === 'reject') throw new Error('connection lost after possible delivery');
        return {};
      } };
      const send = () => kind === 'text' ? t.sendText({ phone: '390000000001', body: 'fixture' })
        : t.sendDocument({ phone: '390000000001', filePath: '/mock', caption: 'fixture' });
      await assert.rejects(send, err => err.code === 'TRANSPORT_DELIVERY_AMBIGUOUS' && err.ambiguous && !err.transient);
      assert.equal(sends, 1);
    });
  }
}

test('registration rejection happens before any send', async () => {
  const t = new WwebjsTransport(); t.connected = true;
  let sends = 0;
  t.client = { isRegisteredUser: async () => false, sendMessage: async () => sends++ };
  await assert.rejects(() => t.sendText({ phone: '390000000001', body: 'fixture' }), { code: 'WHATSAPP_NOT_REGISTERED' });
  assert.equal(sends, 0);
});
