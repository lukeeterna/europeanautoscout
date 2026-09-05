'use strict';

/**
 * Single-shot LocalAuth pairing helper for ARGOS C10.
 *
 * This helper never opens the ARGOS databases, never calls the daemon /send or
 * /resume endpoints, and never prints QR material. It creates a fresh LocalAuth
 * profile under a caller-provided staging directory, writes exactly the first QR
 * as a mode-0600 data-url file, then waits for WhatsApp Web READY. The caller may
 * promote the staged profile only after READY.
 */

const fs = require('fs');
const path = require('path');
const QRCode = require('qrcode');
const { Client, LocalAuth } = require('whatsapp-web.js');

const dataPath = process.env.ARGOS_PAIR_DATA_PATH || '';
const qrFile = process.env.ARGOS_PAIR_QR_FILE || '';
const statusFile = process.env.ARGOS_PAIR_STATUS_FILE || '';
const chromeExecutable = process.env.ARGOS_PAIR_CHROME || '';
const clientId = process.env.ARGOS_PAIR_CLIENT_ID || 'argos-business';
const timeoutMs = Math.max(60_000, Number(process.env.ARGOS_PAIR_TIMEOUT_MS || 360_000));

function fail(message) {
  throw new Error(message);
}

if (!dataPath || !qrFile || !statusFile || !chromeExecutable) {
  fail('pairing helper requires staging, qr, status and Chrome paths');
}
if (!fs.existsSync(chromeExecutable)) fail('Chrome executable missing');

fs.mkdirSync(dataPath, { recursive: true, mode: 0o700 });

function atomicWrite(file, value, mode = 0o600) {
  const tmp = `${file}.tmp.${process.pid}`;
  fs.writeFileSync(tmp, value, { encoding: 'utf8', mode });
  fs.chmodSync(tmp, mode);
  fs.renameSync(tmp, file);
}

function setStatus(value) {
  atomicWrite(statusFile, `${value}\n`, 0o600);
}

let client = null;
let finished = false;
let firstQrCaptured = false;
let authenticated = false;
let timer = null;

async function finish(status, exitCode) {
  if (finished) return;
  finished = true;
  if (timer) clearTimeout(timer);
  try { setStatus(status); } catch (_) {}
  try {
    if (client) await client.destroy();
  } catch (_) {}
  process.exit(exitCode);
}

setStatus('STARTING');

client = new Client({
  authStrategy: new LocalAuth({ clientId, dataPath }),
  puppeteer: {
    headless: true,
    executablePath: chromeExecutable,
    args: ['--no-first-run', '--no-default-browser-check'],
  },
});

client.on('qr', async (qr) => {
  if (firstQrCaptured || finished) return;
  firstQrCaptured = true;
  try {
    const dataUrl = await QRCode.toDataURL(qr, { type: 'image/png', errorCorrectionLevel: 'M' });
    atomicWrite(qrFile, `${dataUrl}\n`, 0o600);
    setStatus('QR_READY');
  } catch (_) {
    await finish('QR_RENDER_FAILED', 20);
  }
});

client.on('authenticated', () => {
  authenticated = true;
  if (!finished) setStatus(firstQrCaptured ? 'AUTHENTICATED' : 'AUTHENTICATED_NO_QR');
});

client.on('ready', () => finish('READY', 0));
client.on('auth_failure', () => finish('AUTH_FAILURE', 21));
client.on('disconnected', () => finish(authenticated ? 'DISCONNECTED_AFTER_AUTH' : 'DISCONNECTED', 22));

process.on('SIGTERM', () => finish('TERMINATED', 143));
process.on('SIGINT', () => finish('TERMINATED', 130));

// One initialize call only. Subsequent qr events from the same client are
// deliberately ignored; a fresh attempt requires a fresh manual workflow run.
timer = setTimeout(() => finish('TIMEOUT', 23), timeoutMs);
client.initialize().catch(() => finish('INIT_FAILED', 24));
