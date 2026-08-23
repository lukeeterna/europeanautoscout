'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const ecosystem = require('../../ecosystem.config.js');

const META_SECRET_KEYS = [
  'META_WA_ACCESS_TOKEN',
  'META_WA_PHONE_NUMBER_ID',
  'META_WA_WABA_ID',
  'META_WA_WEBHOOK_VERIFY_TOKEN',
  'META_APP_SECRET',
];

function app(name) {
  const found = ecosystem.apps.find((item) => item.name === name);
  assert.ok(found, `missing PM2 app ${name}`);
  return found;
}

test('30 only argos-wa-daemon receives official Meta credentials', () => {
  const daemon = app('argos-wa-daemon');
  for (const key of META_SECRET_KEYS) {
    assert.ok(Object.prototype.hasOwnProperty.call(daemon.env, key), `daemon missing ${key}`);
  }

  for (const other of ecosystem.apps.filter((item) => item.name !== 'argos-wa-daemon')) {
    for (const key of META_SECRET_KEYS) {
      assert.equal(
        Object.prototype.hasOwnProperty.call(other.env || {}, key),
        false,
        `${other.name} must not inherit ${key}`,
      );
    }
  }
});

test('31 PM2 defaults remain fail-closed and single-writer', () => {
  const daemon = app('argos-wa-daemon');
  const scheduler = app('argos-outreach-scheduler');
  assert.equal(daemon.env.ARGOS_WA_TRANSPORT, 'wwebjs');
  assert.equal(daemon.env.ARGOS_AUTOMATION_ENABLED, '0');
  assert.equal(scheduler.env.ARGOS_AUTOMATION_ENABLED, '0');
  assert.equal(path.basename(daemon.script), 'runtime_entrypoint.py');
  assert.notEqual(path.basename(scheduler.script), 'wa-daemon.js');
});

test('32 no second PM2 app executes wa-daemon.js', () => {
  const writers = ecosystem.apps.filter((item) => path.basename(String(item.script || '')) === 'wa-daemon.js');
  assert.equal(writers.length, 0, 'PM2 must enter the writer only through runtime_entrypoint.py');
});
