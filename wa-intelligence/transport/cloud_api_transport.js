'use strict';

const fs = require('fs');
const https = require('https');
const path = require('path');
const crypto = require('crypto');
const { TransportError } = require('./errors');

const DEFAULT_GRAPH_VERSION = 'v25.0';
const DEFAULT_TIMEOUT_MS = 15000;

function parseJsonBuffer(buffer) {
  const text = Buffer.isBuffer(buffer) ? buffer.toString('utf8') : String(buffer || '');
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (_) {
    throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API returned invalid JSON');
  }
}

function sanitizeGraphError(statusCode, payload) {
  const error = payload && typeof payload === 'object' ? payload.error || {} : {};
  return new TransportError(
    'TRANSPORT_REMOTE_ERROR',
    `Graph API returned HTTP ${statusCode}`,
    {
      statusCode,
      metaCode: error.code ?? null,
      metaType: error.type ?? null,
      transient: statusCode === 429 || statusCode >= 500,
    },
  );
}

function nodeHttpsRequest({
  hostname = 'graph.facebook.com',
  method = 'GET',
  path: requestPath,
  headers = {},
  body = null,
  timeoutMs = DEFAULT_TIMEOUT_MS,
  ambiguousOnNetworkFailure = false,
}) {
  return new Promise((resolve, reject) => {
    let transmitted = false;
    const req = https.request(
      {
        hostname,
        method,
        path: requestPath,
        headers,
      },
      (res) => {
        const chunks = [];
        let size = 0;
        res.on('data', (chunk) => {
          size += chunk.length;
          if (size > 4 * 1024 * 1024) {
            req.destroy(new Error('response too large'));
            return;
          }
          chunks.push(chunk);
        });
        res.on('end', () => {
          resolve({
            statusCode: Number(res.statusCode || 0),
            headers: res.headers || {},
            body: Buffer.concat(chunks),
          });
        });
      },
    );

    req.on('error', (err) => {
      if (ambiguousOnNetworkFailure && transmitted) {
        reject(new TransportError(
          'TRANSPORT_DELIVERY_AMBIGUOUS',
          'Transport outcome is ambiguous; automatic retry is forbidden',
          { ambiguous: true, transient: false, cause: err },
        ));
        return;
      }
      reject(new TransportError(
        'TRANSPORT_NETWORK_ERROR',
        'Graph API request failed',
        { transient: true, cause: err },
      ));
    });

    req.setTimeout(timeoutMs, () => req.destroy(new Error('request timeout')));
    transmitted = true;
    req.end(body || undefined);
  });
}

function mimeForFile(filePath) {
  switch (path.extname(filePath).toLowerCase()) {
    case '.pdf': return 'application/pdf';
    case '.jpg':
    case '.jpeg': return 'image/jpeg';
    case '.png': return 'image/png';
    case '.txt': return 'text/plain';
    default: return 'application/octet-stream';
  }
}

function buildMultipartMediaBody(filePath) {
  const filename = path.basename(filePath);
  const mime = mimeForFile(filePath);
  const file = fs.readFileSync(filePath);
  const boundary = `----argos-${crypto.randomBytes(12).toString('hex')}`;
  const head = Buffer.from(
    `--${boundary}\r\n` +
    'Content-Disposition: form-data; name="messaging_product"\r\n\r\n' +
    'whatsapp\r\n' +
    `--${boundary}\r\n` +
    `Content-Disposition: form-data; name="file"; filename="${filename.replace(/"/g, '')}"\r\n` +
    `Content-Type: ${mime}\r\n\r\n`,
    'utf8',
  );
  const tail = Buffer.from(`\r\n--${boundary}--\r\n`, 'utf8');
  return {
    boundary,
    body: Buffer.concat([head, file, tail]),
  };
}

class CloudApiTransport {
  constructor({ env = process.env, requestFn = nodeHttpsRequest, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
    this.env = env;
    this.requestFn = requestFn;
    this.timeoutMs = timeoutMs;
    this.graphVersion = String(env.META_GRAPH_API_VERSION || DEFAULT_GRAPH_VERSION).replace(/^\/+|\/+$/g, '');
    this.accessToken = String(env.META_WA_ACCESS_TOKEN || '');
    this.phoneNumberId = String(env.META_WA_PHONE_NUMBER_ID || '');
    this.wabaId = String(env.META_WA_WABA_ID || '');
    this.connected = false;
  }

  _authHeaders(extra = {}) {
    return {
      Authorization: `Bearer ${this.accessToken}`,
      ...extra,
    };
  }

  _assertCoreConfig() {
    if (!this.accessToken || !this.phoneNumberId) {
      throw new TransportError(
        'TRANSPORT_CONFIG_MISSING',
        'Cloud API access token and phone number id are required',
      );
    }
  }

  async _graphRequest({ method, endpoint, body = null, headers = {}, ambiguousOnNetworkFailure = false }) {
    this._assertCoreConfig();
    const response = await this.requestFn({
      hostname: 'graph.facebook.com',
      method,
      path: `/${this.graphVersion}/${endpoint.replace(/^\/+/, '')}`,
      headers: this._authHeaders(headers),
      body,
      timeoutMs: this.timeoutMs,
      ambiguousOnNetworkFailure,
    });
    const payload = parseJsonBuffer(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw sanitizeGraphError(response.statusCode, payload);
    }
    return payload;
  }

  async initialize() {
    this._assertCoreConfig();
    try {
      const payload = await this._graphRequest({
        method: 'GET',
        endpoint: `${this.phoneNumberId}?fields=id,display_phone_number`,
      });
      if (!payload || String(payload.id || '') !== this.phoneNumberId) {
        throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Phone number id validation failed');
      }
      this.connected = true;
      return {
        connected: true,
        phone_number_id: this.phoneNumberId,
        display_phone_number: String(payload.display_phone_number || ''),
      };
    } catch (err) {
      this.connected = false;
      throw err;
    }
  }

  isConnected() {
    return this.connected;
  }

  async sendText({ phone, body }) {
    if (!this.connected) {
      throw new TransportError('TRANSPORT_NOT_READY', 'Cloud API transport is not connected', { transient: true });
    }
    const digits = String(phone || '').replace(/\D/g, '');
    if (!digits || !String(body || '').trim()) {
      throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'phone and body are required');
    }
    const requestBody = Buffer.from(JSON.stringify({
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to: digits,
      type: 'text',
      text: {
        preview_url: false,
        body: String(body),
      },
    }), 'utf8');
    const payload = await this._graphRequest({
      method: 'POST',
      endpoint: `${this.phoneNumberId}/messages`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': String(requestBody.length),
      },
      body: requestBody,
      ambiguousOnNetworkFailure: true,
    });
    const waMessageId = String(payload?.messages?.[0]?.id || '');
    if (!waMessageId) {
      throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API response is missing message id');
    }
    return { ok: true, wa_msg_id: waMessageId };
  }

  async sendDocument({ phone, filePath, caption }) {
    if (!this.connected) {
      throw new TransportError('TRANSPORT_NOT_READY', 'Cloud API transport is not connected', { transient: true });
    }
    const digits = String(phone || '').replace(/\D/g, '');
    if (!digits || !filePath || !fs.existsSync(filePath)) {
      throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'phone and existing filePath are required');
    }

    const multipart = buildMultipartMediaBody(filePath);
    const uploaded = await this._graphRequest({
      method: 'POST',
      endpoint: `${this.phoneNumberId}/media`,
      headers: {
        'Content-Type': `multipart/form-data; boundary=${multipart.boundary}`,
        'Content-Length': String(multipart.body.length),
      },
      body: multipart.body,
      ambiguousOnNetworkFailure: true,
    });
    const mediaId = String(uploaded?.id || '');
    if (!mediaId) {
      throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API media upload response is missing id');
    }

    const requestBody = Buffer.from(JSON.stringify({
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to: digits,
      type: 'document',
      document: {
        id: mediaId,
        caption: String(caption || ''),
        filename: path.basename(filePath),
      },
    }), 'utf8');
    const payload = await this._graphRequest({
      method: 'POST',
      endpoint: `${this.phoneNumberId}/messages`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': String(requestBody.length),
      },
      body: requestBody,
      ambiguousOnNetworkFailure: true,
    });
    const waMessageId = String(payload?.messages?.[0]?.id || '');
    if (!waMessageId) {
      throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API response is missing message id');
    }
    return { ok: true, wa_msg_id: waMessageId, media_id: mediaId };
  }

  async shutdown() {
    this.connected = false;
  }
}

module.exports = {
  CloudApiTransport,
  DEFAULT_GRAPH_VERSION,
  buildMultipartMediaBody,
  nodeHttpsRequest,
};
