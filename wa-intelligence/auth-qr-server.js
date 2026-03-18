#!/usr/bin/env node
/**
 * auth-qr-server.js — ARGOS WA Session Auth via HTTP
 * Solo autenticazione, nessun invio messaggi.
 *
 * Avvio: node auth-qr-server.js
 * Apri: http://192.168.1.2:8765 dal browser
 * Scansiona QR con WA Business sul telefono
 * Quando dice AUTENTICATO, chiudi e avvia wa-daemon
 */

'use strict';

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const http = require('http');
const path = require('path');

const CLIENT_ID = process.env.WA_CLIENT_ID || 'argos-business';
const DATA_PATH = path.join(__dirname, '..', 'wa-sender');
const PORT = 8765;

let qrHtml = '<p style="font-size:1.4em">Inizializzazione Chromium...</p>';
let stato = 'INIT';

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html;charset=utf-8' });
    res.end(`<!DOCTYPE html><html>
<head><meta charset="utf-8"><title>ARGOS Auth - ${stato}</title>
<style>body{background:#08080A;color:#fff;font-family:sans-serif;text-align:center;padding:40px}
h1{color:#B8960C}svg{border:3px solid #B8960C;border-radius:8px;margin:20px auto;display:block;max-width:360px}
.ok{color:#00e676}.err{color:#ff1744}</style></head>
<body><h1>ARGOS WA Auth</h1>
<p>Session: <strong>${CLIENT_ID}</strong> | Stato: <strong>${stato}</strong></p>
${qrHtml}
<p style="color:#787880;font-size:.9em">Auto-refresh 3s</p>
<script>if(!document.title.includes('PRONTO'))setTimeout(()=>location.reload(),3000);</script>
</body></html>`);
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`[ARGOS] QR Auth Server su http://192.168.1.2:${PORT}`);
    console.log(`[ARGOS] Session ID: ${CLIENT_ID}`);
    console.log(`[ARGOS] Data path: ${DATA_PATH}`);
});

const client = new Client({
    authStrategy: new LocalAuth({
        clientId: CLIENT_ID,
        dataPath: DATA_PATH,
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-first-run',
        ]
    }
});

client.on('qr', async (qr) => {
    stato = 'SCANSIONA QR';
    console.log('[ARGOS] QR pronto — apri http://192.168.1.2:8765');
    try {
        qrHtml = await qrcode.toString(qr, { type: 'svg', width: 340, margin: 2 });
    } catch (e) {
        qrHtml = `<p class="err">SVG error: ${e.message}</p>`;
    }
});

client.on('authenticated', () => {
    stato = 'AUTENTICATO';
    qrHtml = '<p class="ok" style="font-size:2em">AUTENTICATO</p><p>Sessione salvata. Attendo ready...</p>';
    console.log('[ARGOS] Autenticato - sessione salvata');
});

client.on('ready', () => {
    stato = 'PRONTO';
    qrHtml = '<p class="ok" style="font-size:2em">SESSIONE PRONTA</p>' +
             '<p>Puoi chiudere questa pagina e avviare wa-daemon.</p>' +
             '<p style="color:#787880">pm2 start ecosystem.config.js --only argos-wa-daemon</p>';
    console.log('[ARGOS] Client PRONTO — sessione valida.');
    console.log('[ARGOS] Chiudi con Ctrl+C, poi avvia wa-daemon.');
    // Auto-chiusura dopo 30s
    setTimeout(async () => {
        console.log('[ARGOS] Auto-shutdown...');
        await client.destroy();
        server.close();
        process.exit(0);
    }, 30000);
});

client.on('auth_failure', (msg) => {
    stato = 'AUTH FAILURE';
    qrHtml = `<p class="err" style="font-size:1.5em">Auth fallita: ${msg}</p>`;
    console.error('[ARGOS] Auth failure:', msg);
});

client.initialize();
