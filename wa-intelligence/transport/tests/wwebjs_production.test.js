'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const ecosystem = require('../../ecosystem.config.js');

function app(name) {
  const found = ecosystem.apps.find((item) => item.name === name);
  assert.ok(found, `missing PM2 app ${name}`);
  return found;
}

test('50 zero-cost production defaults to wwebjs and remains paused/inert', () => {
  const daemon = app('argos-wa-daemon');
  const scheduler = app('argos-outreach-scheduler');
  assert.equal(daemon.env.ARGOS_WA_TRANSPORT, 'wwebjs');
  assert.equal(daemon.env.ARGOS_AUTOMATION_ENABLED, '0');
  assert.equal(scheduler.env.ARGOS_AUTOMATION_ENABLED, '0');
  assert.equal(path.basename(daemon.script), 'runtime_entrypoint.py');
});

test('51 LocalAuth identity and Chrome executable are propagated to daemon', () => {
  const daemon = app('argos-wa-daemon');
  assert.ok(Object.prototype.hasOwnProperty.call(daemon.env, 'ARGOS_WA_CLIENT_ID'));
  assert.ok(Object.prototype.hasOwnProperty.call(daemon.env, 'ARGOS_WA_SESSION_DIR'));
  assert.ok(Object.prototype.hasOwnProperty.call(daemon.env, 'CHROME_EXECUTABLE_PATH'));
});

test('52 scheduler is not a WhatsApp writer', () => {
  const scheduler = app('argos-outreach-scheduler');
  assert.notEqual(path.basename(String(scheduler.script || '')), 'wa-daemon.js');
});
