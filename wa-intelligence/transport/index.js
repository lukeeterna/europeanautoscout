'use strict';

const { CloudApiTransport, DEFAULT_GRAPH_VERSION } = require('./cloud_api_transport');
const { WwebjsTransport } = require('./wwebjs_transport');
const { TransportError } = require('./errors');

function validateCloudEnvironment(env = process.env) {
  const required = [
    'META_WA_ACCESS_TOKEN',
    'META_WA_PHONE_NUMBER_ID',
    'META_WA_WABA_ID',
    'META_WA_WEBHOOK_VERIFY_TOKEN',
    'META_APP_SECRET',
  ];
  const missing = required.filter((name) => !String(env[name] || '').trim());
  if (missing.length) {
    throw new TransportError(
      'TRANSPORT_CONFIG_MISSING',
      `Cloud API configuration incomplete: ${missing.join(', ')}`,
    );
  }
  return {
    graphVersion: String(env.META_GRAPH_API_VERSION || DEFAULT_GRAPH_VERSION),
    phoneNumberId: String(env.META_WA_PHONE_NUMBER_ID),
    wabaId: String(env.META_WA_WABA_ID),
  };
}

function createTransport({
  env = process.env,
  callbacks = {},
  requestFn,
  moduleLoader,
} = {}) {
  const mode = String(env.ARGOS_WA_TRANSPORT || 'wwebjs').trim().toLowerCase();
  if (mode === 'cloud') {
    validateCloudEnvironment(env);
    return new CloudApiTransport({ env, requestFn });
  }
  if (mode === 'wwebjs') {
    return new WwebjsTransport({ env, callbacks, moduleLoader });
  }
  throw new TransportError('TRANSPORT_MODE_INVALID', `Unsupported WhatsApp transport mode: ${mode}`);
}

module.exports = {
  CloudApiTransport,
  TransportError,
  WwebjsTransport,
  createTransport,
  validateCloudEnvironment,
};
