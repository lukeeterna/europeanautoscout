'use strict';

const fs = require('fs');
const https = require('https');
const path = require('path');
const crypto = require('crypto');
const { TransportError } = require('./errors');
const META_TEMPLATE_CONTRACT = require('../meta_templates.json');

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
      transient: statusCode === 429,
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
    let submitted = false;
    const req = https.request(
      { hostname, method, path: requestPath, headers },
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
      if (ambiguousOnNetworkFailure && submitted) {
        reject(new TransportError(
          'TRANSPORT_DELIVERY_AMBIGUOUS',
          'Message delivery outcome is ambiguous; automatic retry is forbidden',
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
    submitted = true;
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
  return { boundary, body: Buffer.concat([head, file, tail]) };
}

function normalizeTemplateText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function templateRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

function bodyComponent(row) {
  return (Array.isArray(row?.components) ? row.components : [])
    .find((component) => String(component?.type || '').toUpperCase() === 'BODY');
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
    this.templateLanguage = String(env.META_WA_TEMPLATE_LANGUAGE || 'it');
    this.connected = false;
    this.approvedTemplateNames = new Set();
  }

  _authHeaders(extra = {}) {
    return { Authorization: `Bearer ${this.accessToken}`, ...extra };
  }

  _assertCoreConfig() {
    if (!this.accessToken || !this.phoneNumberId || !this.wabaId) {
      throw new TransportError(
        'TRANSPORT_CONFIG_MISSING',
        'Cloud API access token, phone number id and WABA id are required',
      );
    }
  }

  _configuredTemplateContracts() {
    const configured = [];
    let configuredCount = 0;
    for (const [internalId, contract] of Object.entries(META_TEMPLATE_CONTRACT)) {
      const envName = String(contract?.env_name || '');
      const name = String(this.env[envName] || '').trim();
      if (name) configuredCount += 1;
      configured.push({ internalId, contract, envName, name });
    }
    if (configuredCount === 0) return [];
    if (configuredCount !== configured.length) {
      throw new TransportError(
        'TRANSPORT_CONFIG_MISSING',
        'All proactive Meta template names must be configured together',
      );
    }
    return configured;
  }

  async _graphRequest({ method, endpoint, body = null, headers = {}, deliveryRequest = false }) {
    this._assertCoreConfig();
    const response = await this.requestFn({
      hostname: 'graph.facebook.com',
      method,
      path: `/${this.graphVersion}/${endpoint.replace(/^\/+/, '')}`,
      headers: this._authHeaders(headers),
      body,
      timeoutMs: this.timeoutMs,
      ambiguousOnNetworkFailure: deliveryRequest,
    });
    const payload = parseJsonBuffer(response.body);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      const remote = sanitizeGraphError(response.statusCode, payload);
      if (response.statusCode === 401 || response.statusCode === 403 || remote.metaCode === 190) {
        this.connected = false;
      }
      if (deliveryRequest && response.statusCode >= 500) {
        throw new TransportError(
          'TRANSPORT_DELIVERY_AMBIGUOUS',
          `Message delivery outcome is ambiguous after HTTP ${response.statusCode}; automatic retry is forbidden`,
          {
            ambiguous: true,
            transient: false,
            statusCode: response.statusCode,
            metaCode: remote.metaCode,
            metaType: remote.metaType,
          },
        );
      }
      throw remote;
    }
    return payload;
  }

  async _validateConfiguredTemplates() {
    const configured = this._configuredTemplateContracts();
    this.approvedTemplateNames.clear();
    if (!configured.length) return { configured: 0, approved: 0 };

    for (const item of configured) {
      const query = new URLSearchParams({
        name: item.name,
        fields: 'name,status,language,category,components',
      }).toString();
      const payload = await this._graphRequest({
        method: 'GET',
        endpoint: `${this.wabaId}/message_templates?${query}`,
      });
      const row = templateRows(payload).find((candidate) => String(candidate?.name || '') === item.name);
      if (!row) {
        throw new TransportError('META_TEMPLATE_NOT_FOUND', `Configured Meta template not found: ${item.internalId}`);
      }
      if (String(row.status || '').toUpperCase() !== 'APPROVED') {
        throw new TransportError('META_TEMPLATE_NOT_APPROVED', `Meta template is not approved: ${item.internalId}`);
      }
      if (String(row.language || '') !== this.templateLanguage) {
        throw new TransportError('META_TEMPLATE_LANGUAGE_MISMATCH', `Meta template language mismatch: ${item.internalId}`);
      }
      if (String(row.category || '').toUpperCase() !== String(item.contract.category || '').toUpperCase()) {
        throw new TransportError('META_TEMPLATE_CATEGORY_MISMATCH', `Meta template category mismatch: ${item.internalId}`);
      }
      const body = bodyComponent(row);
      if (!body || normalizeTemplateText(body.text) !== normalizeTemplateText(item.contract.body)) {
        throw new TransportError('META_TEMPLATE_BODY_MISMATCH', `Meta template body mismatch: ${item.internalId}`);
      }
      this.approvedTemplateNames.add(item.name);
    }
    return { configured: configured.length, approved: this.approvedTemplateNames.size };
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
      const templates = await this._validateConfiguredTemplates();
      this.connected = true;
      return {
        connected: true,
        phone_number_id: this.phoneNumberId,
        display_phone_number: String(payload.display_phone_number || ''),
        templates,
      };
    } catch (err) {
      this.connected = false;
      this.approvedTemplateNames.clear();
      throw err;
    }
  }

  isConnected() {
    return this.connected;
  }

  async _postMessage(phone, messageObject) {
    if (!this.connected) {
      throw new TransportError('TRANSPORT_NOT_READY', 'Cloud API transport is not connected', { transient: true });
    }
    const digits = String(phone || '').replace(/\D/g, '');
    if (!digits) throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'phone is required');
    const requestBody = Buffer.from(JSON.stringify({
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to: digits,
      ...messageObject,
    }), 'utf8');
    const payload = await this._graphRequest({
      method: 'POST',
      endpoint: `${this.phoneNumberId}/messages`,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': String(requestBody.length),
      },
      body: requestBody,
      deliveryRequest: true,
    });
    const waMessageId = String(payload?.messages?.[0]?.id || '');
    if (!waMessageId) {
      throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API response is missing message id');
    }
    return { ok: true, wa_msg_id: waMessageId };
  }

  async sendText({ phone, body }) {
    const text = String(body || '').trim();
    if (!text) throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'body is required');
    return this._postMessage(phone, {
      type: 'text',
      text: { preview_url: false, body: String(body) },
    });
  }

  async sendTemplate({ phone, template }) {
    const name = String(template?.name || '').trim();
    const languageCode = String(template?.language?.code || '').trim();
    if (!name || !languageCode) {
      throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'template name and language are required');
    }
    const configured = this._configuredTemplateContracts();
    if (configured.length && !this.approvedTemplateNames.has(name)) {
      throw new TransportError('META_TEMPLATE_NOT_APPROVED', 'Template was not approved during transport initialization');
    }
    if (languageCode !== this.templateLanguage) {
      throw new TransportError('META_TEMPLATE_LANGUAGE_MISMATCH', 'Template language differs from validated language');
    }
    const payload = {
      name,
      language: { code: languageCode },
    };
    if (Array.isArray(template.components) && template.components.length) {
      payload.components = template.components;
    }
    return this._postMessage(phone, { type: 'template', template: payload });
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
    });
    const mediaId = String(uploaded?.id || '');
    if (!mediaId) {
      throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'Graph API media upload response is missing id');
    }

    const sent = await this._postMessage(digits, {
      type: 'document',
      document: {
        id: mediaId,
        caption: String(caption || ''),
        filename: path.basename(filePath),
      },
    });
    return { ...sent, media_id: mediaId };
  }

  async shutdown() {
    this.connected = false;
    this.approvedTemplateNames.clear();
  }
}

module.exports = {
  CloudApiTransport,
  DEFAULT_GRAPH_VERSION,
  buildMultipartMediaBody,
  nodeHttpsRequest,
  normalizeTemplateText,
  templateRows,
};
