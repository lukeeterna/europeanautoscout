'use strict';

const path = require('path');
const { TransportError } = require('./errors');

class WwebjsTransport {
  constructor({ env = process.env, callbacks = {}, moduleLoader = require } = {}) {
    this.env = env;
    this.callbacks = callbacks;
    this.moduleLoader = moduleLoader;
    this.client = null;
    this.MessageMedia = null;
    this.connected = false;
  }

  async initialize() {
    const { Client, LocalAuth, MessageMedia } = this.moduleLoader('whatsapp-web.js');
    this.MessageMedia = MessageMedia;
    const puppeteer = { headless: true };
    if (this.env.CHROME_EXECUTABLE_PATH) puppeteer.executablePath = this.env.CHROME_EXECUTABLE_PATH;
    this.client = new Client({
      authStrategy: new LocalAuth({
        clientId: this.env.ARGOS_WA_CLIENT_ID || 'argos-s292',
        dataPath: this.env.ARGOS_WA_SESSION_DIR || path.join(__dirname, '..', '.wwebjs_auth'),
      }),
      puppeteer,
    });

    this.client.on('qr', (qr) => {
      this.connected = false;
      this.callbacks.onQr?.(qr);
    });
    this.client.on('authenticated', () => this.callbacks.onAuthenticated?.());
    this.client.on('ready', () => {
      this.connected = true;
      this.callbacks.onReady?.();
    });
    this.client.on('message', (msg) => this.callbacks.onMessage?.(msg));
    this.client.on('auth_failure', (message) => {
      this.connected = false;
      this.callbacks.onAuthFailure?.(message);
    });
    this.client.on('disconnected', (reason) => {
      this.connected = false;
      this.callbacks.onDisconnected?.(reason);
    });

    await this.client.initialize();
    return { connected: this.connected };
  }

  isConnected() {
    return Boolean(this.connected && this.client);
  }

  async _chatId(phone) {
    if (!this.isConnected()) {
      throw new TransportError('TRANSPORT_NOT_READY', 'whatsapp-web.js transport is not connected', { transient: true });
    }
    const digits = String(phone || '').replace(/\D/g, '');
    if (!digits) throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'phone is required');
    const chatId = `${digits}@c.us`;
    const registered = await this.client.isRegisteredUser(chatId);
    if (!registered) {
      throw new TransportError('WHATSAPP_NOT_REGISTERED', 'target number is not registered');
    }
    return chatId;
  }

  async sendText({ phone, body }) {
    const chatId = await this._chatId(phone);
    const text = String(body || '').trim();
    if (!text) throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'body is required');
    const sent = await this.client.sendMessage(chatId, text);
    const waMessageId = String(sent?.id?._serialized || '');
    if (!waMessageId) throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'whatsapp-web.js response is missing message id');
    return { ok: true, wa_msg_id: waMessageId };
  }

  async sendDocument({ phone, filePath, caption }) {
    const chatId = await this._chatId(phone);
    if (!filePath) throw new TransportError('TRANSPORT_INVALID_ARGUMENT', 'filePath is required');
    const media = this.MessageMedia.fromFilePath(filePath);
    const sent = await this.client.sendMessage(chatId, media, {
      caption: String(caption || ''),
      sendMediaAsDocument: true,
    });
    const waMessageId = String(sent?.id?._serialized || '');
    if (!waMessageId) throw new TransportError('TRANSPORT_INVALID_RESPONSE', 'whatsapp-web.js response is missing message id');
    return { ok: true, wa_msg_id: waMessageId };
  }

  async shutdown() {
    this.connected = false;
    if (this.client) await this.client.destroy();
    this.client = null;
  }
}

module.exports = { WwebjsTransport };
