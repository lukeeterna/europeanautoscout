'use strict';

const crypto = require('crypto');

function timingSafeTextEqual(a, b) {
  const left = Buffer.from(String(a || ''), 'utf8');
  const right = Buffer.from(String(b || ''), 'utf8');
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function verifyWebhookSignature(rawBody, signatureHeader, appSecret) {
  if (!appSecret || !signatureHeader || !Buffer.isBuffer(rawBody)) return false;
  const expected = `sha256=${crypto.createHmac('sha256', appSecret).update(rawBody).digest('hex')}`;
  return timingSafeTextEqual(expected, String(signatureHeader));
}

function verifyWebhookChallenge(searchParams, verifyToken) {
  const mode = String(searchParams.get('hub.mode') || '');
  const token = String(searchParams.get('hub.verify_token') || '');
  const challenge = String(searchParams.get('hub.challenge') || '');
  if (mode !== 'subscribe' || !verifyToken || !timingSafeTextEqual(token, verifyToken)) return null;
  return challenge;
}

function createBoundedSeenSet(limit = 5000) {
  const seen = new Set();
  return {
    has: (id) => seen.has(id),
    add(id) {
      if (!id) return;
      seen.add(id);
      if (seen.size > limit) {
        const first = seen.values().next().value;
        if (first !== undefined) seen.delete(first);
      }
    },
  };
}

function normalizeInboundMessage(message) {
  if (!message || message.type !== 'text' || !message.text || !message.text.body) return null;
  const digits = String(message.from || '').replace(/\D/g, '');
  const waId = String(message.id || '');
  if (!digits || !waId) return null;
  return {
    from: `${digits}@c.us`,
    fromMe: false,
    body: String(message.text.body),
    id: { _serialized: waId },
  };
}

async function processWebhookPayload(payload, {
  onInbound = async () => {},
  onStatus = () => {},
  onAudit = () => {},
  seenEchoes = createBoundedSeenSet(),
} = {}) {
  if (!payload || payload.object !== 'whatsapp_business_account' || !Array.isArray(payload.entry)) {
    onAudit('WHATSAPP_WEBHOOK_IGNORED', { reason: 'unexpected_object' });
    return { handled: 0 };
  }

  let handled = 0;
  for (const entry of payload.entry) {
    for (const change of Array.isArray(entry?.changes) ? entry.changes : []) {
      const field = String(change?.field || '');
      const value = change?.value || {};

      if (field === 'messages') {
        for (const message of Array.isArray(value.messages) ? value.messages : []) {
          const normalized = normalizeInboundMessage(message);
          if (!normalized) {
            onAudit('WHATSAPP_INBOUND_UNSUPPORTED', {
              type: String(message?.type || ''),
              wa_msg_id: String(message?.id || ''),
            });
            continue;
          }
          await onInbound(normalized);
          handled += 1;
        }
        for (const status of Array.isArray(value.statuses) ? value.statuses : []) {
          onStatus({
            wa_msg_id: String(status?.id || ''),
            status: String(status?.status || ''),
            recipient_id: String(status?.recipient_id || ''),
            error_codes: Array.isArray(status?.errors) ? status.errors.map((err) => err?.code).filter(Boolean) : [],
          });
          handled += 1;
        }
        continue;
      }

      if (field === 'smb_message_echoes') {
        const echoes = Array.isArray(value.messages)
          ? value.messages
          : (Array.isArray(value.smb_message_echoes) ? value.smb_message_echoes : []);
        for (const echo of echoes) {
          const waId = String(echo?.id || '');
          if (waId && seenEchoes.has(waId)) continue;
          if (waId) seenEchoes.add(waId);
          onAudit('ECHO_FROM_BUSINESS_APP', {
            wa_msg_id: waId,
            to_suffix: String(echo?.to || '').replace(/\D/g, '').slice(-4),
          });
          handled += 1;
        }
        continue;
      }

      if (field === 'history' || field === 'smb_app_state_sync') {
        onAudit('WHATSAPP_COEXISTENCE_SYNC_IGNORED', { field });
        handled += 1;
        continue;
      }

      onAudit('WHATSAPP_WEBHOOK_FIELD_IGNORED', { field });
    }
  }
  return { handled };
}

module.exports = {
  createBoundedSeenSet,
  normalizeInboundMessage,
  processWebhookPayload,
  timingSafeTextEqual,
  verifyWebhookChallenge,
  verifyWebhookSignature,
};
