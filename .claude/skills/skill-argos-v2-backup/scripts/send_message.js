#!/usr/bin/env node
/**
 * send_message.js — ARGOS™ CoVe 2026
 * Invio WhatsApp senza QR (sessione LocalAuth già autenticata)
 *
 * Usage: node send_message.js "393XXXXXXXXX@c.us" "testo"
 * Prerequisito: ~/.wwebjs_auth/session-argosautomotive/ deve esistere
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const fs = require('fs');

const NUMERO    = process.argv[2];
const MESSAGGIO = process.argv[3];

// ── Validazione input ────────────────────────────────────────
if (!NUMERO || !MESSAGGIO) {
    console.error('[ARGOS] Usage: node send_message.js "393XXXXXXXXX@c.us" "testo"');
    process.exit(1);
}
if (!NUMERO.endsWith('@c.us')) {
    console.error('[ARGOS] Formato errato. Usa: 393XXXXXXXXX@c.us (prefisso 39 + numero senza 0)');
    process.exit(1);
}

// ── Verifica sessione esistente ──────────────────────────────
const sessionPath = `${process.env.HOME}/.wwebjs_auth/session-argosautomotive`;
if (!fs.existsSync(sessionPath)) {
    console.error('[ARGOS] ❌ Sessione non trovata:', sessionPath);
    console.error('[ARGOS] Esegui prima send_qr_server.js per autenticarti');
    process.exit(1);
}

// ── Anti-ban sleep ───────────────────────────────────────────
const SLEEP_MIN = 90;
const SLEEP_MAX = 720;
const sleepSec  = Math.floor(Math.random() * (SLEEP_MAX - SLEEP_MIN + 1)) + SLEEP_MIN;

console.log(`[ARGOS] Anti-ban sleep: ${sleepSec}s...`);
console.log(`[ARGOS] Invio a: ${NUMERO}`);
console.log(`[ARGOS] Messaggio: ${MESSAGGIO.slice(0, 80)}${MESSAGGIO.length > 80 ? '...' : ''}`);

setTimeout(async () => {
    const client = new Client({
        authStrategy: new LocalAuth({ clientId: 'argosautomotive' }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run'
            ]
        }
    });

    // Timeout safety: 3 minuti max
    const timeout = setTimeout(() => {
        console.error('[ARGOS] ❌ Timeout — client non pronto in 3 minuti');
        process.exit(1);
    }, 180_000);

    client.on('auth_failure', async () => {
        clearTimeout(timeout);
        console.error('[ARGOS] ❌ Sessione scaduta — esegui send_qr_server.js');
        process.exit(1);
    });

    client.on('disconnected', async (reason) => {
        clearTimeout(timeout);
        console.error('[ARGOS] ❌ Disconnesso:', reason);
        process.exit(1);
    });

    client.on('ready', async () => {
        clearTimeout(timeout);
        console.log('[ARGOS] ✅ Client pronto. Invio in corso...');
        try {
            await client.sendMessage(NUMERO, MESSAGGIO);
            console.log('[ARGOS] ✅ INVIATO');
            console.log(`[ARGOS]    A: ${NUMERO}`);
            console.log(`[ARGOS]    Timestamp: ${new Date().toISOString()}`);
            await client.destroy();
            process.exit(0);
        } catch (err) {
            console.error('[ARGOS] ❌ Invio fallito:', err.message);
            await client.destroy();
            process.exit(1);
        }
    });

    client.initialize();

}, sleepSec * 1000);
