#!/bin/bash
# deploy_qr_server.sh — CoVe 2026
# Deploy send_qr_server.js su iMac via SSH heredoc
# Usage: bash deploy_qr_server.sh "393XXXXXXXXX" "testo messaggio"

set -e

NUMERO="${1:?Errore: numero richiesto (es: 393XXXXXXXXX)}"
MESSAGGIO="${2:?Errore: messaggio richiesto}"
IMAC="gianlucadistasi@192.168.1.12"
DEST="$HOME/Documents/app-antigravity-auto/wa-sender"

# Escape per heredoc
MSG_ESCAPED=$(printf '%s' "$MESSAGGIO" | sed "s/'/'\\''/g")

echo "[ARGOS] ▶ Deploy QR server su iMac..."
echo "[ARGOS]   Numero: ${NUMERO}@c.us"
echo "[ARGOS]   Messaggio: ${MESSAGGIO:0:60}..."

ssh "$IMAC" bash << REMOTE
set -e
mkdir -p "$DEST"
cd "$DEST"

# Installa dipendenze se mancanti
if [ ! -d node_modules/whatsapp-web.js ]; then
  echo "[ARGOS] Installo dipendenze npm..."
  npm init -y 2>/dev/null
  npm install whatsapp-web.js qrcode 2>&1 | tail -3
fi

cat > send_qr_server.js << 'JSEOF'
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const http = require('http');

const NUMERO   = 'NUMERO_PLACEHOLDER@c.us';
const MSG      = 'MSG_PLACEHOLDER';

let qrHtml = '<p style="font-size:1.4em">⏳ Inizializzazione Chromium...</p>';
let stato   = 'INIT';

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type':'text/html;charset=utf-8'});
  res.end(\`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ARGOS™ Auth \${stato}</title>
  <style>
    body{background:#08080A;color:#fff;font-family:sans-serif;
         text-align:center;padding:40px;margin:0}
    h1{color:#B8960C;letter-spacing:3px;font-size:1.8em}
    .stato{background:#1a1a1a;padding:10px 24px;border-radius:6px;
           display:inline-block;margin:10px 0;font-size:1.1em}
    svg{border:3px solid #B8960C;border-radius:8px;margin:20px auto;
        display:block;max-width:360px}
    .ok{color:#00e676} .err{color:#ff1744}
  </style>
</head>
<body>
  <h1>ARGOS™ WhatsApp Auth</h1>
  <div class="stato">Stato: <strong>\${stato}</strong></div>
  \${qrHtml}
  <p style="color:#787880;font-size:.9em">Auto-refresh ogni 3s</p>
  <script>
    if(!document.title.includes('INVIATO') && !document.title.includes('FAILED'))
      setTimeout(()=>location.reload(),3000);
  </script>
</body>
</html>\`);
});

server.listen(8765,'0.0.0.0',()=>{
  console.log('[ARGOS] ▶ QR Server attivo su porta 8765');
  console.log('[ARGOS] >>> Apri su MacBook: http://192.168.1.12:8765 <<<');
  console.log('[ARGOS] >>> Scansiona QR con Android Very Mobile SIM <<<');
});

const client = new Client({
  authStrategy: new LocalAuth({clientId:'argosautomotive'}),
  puppeteer:{
    headless:true,
    args:['--no-sandbox','--disable-setuid-sandbox',
          '--disable-dev-shm-usage','--disable-gpu',
          '--no-first-run','--no-zygote']
  }
});

client.on('qr', async qr => {
  stato = 'SCANSIONA QR';
  console.log('[ARGOS] QR generato — apri browser MacBook e scansiona');
  try {
    qrHtml = await qrcode.toString(qr,{type:'svg',width:340,margin:2});
  } catch(e) {
    qrHtml = '<p class="err">Errore SVG: '+e.message+'</p>';
  }
});

client.on('authenticated', () => {
  stato = 'AUTENTICATO';
  qrHtml = '<p class="ok" style="font-size:2em">✅ AUTENTICATO</p><p>Invio messaggio in corso...</p>';
  console.log('[ARGOS] ✅ Autenticato');
});

client.on('auth_failure', err => {
  stato = 'AUTH_FAILED';
  qrHtml = '<p class="err" style="font-size:1.5em">❌ Auth fallita</p><p>Riavvia script e scansiona QR</p>';
  console.error('[ARGOS] ❌ Auth failure:', err);
  setTimeout(()=>process.exit(1), 5000);
});

client.on('ready', async () => {
  console.log('[ARGOS] Client pronto. Invio a '+NUMERO+'...');
  try {
    await client.sendMessage(NUMERO, MSG);
    stato = 'INVIATO';
    qrHtml = \`<p class="ok" style="font-size:2em">✅ MESSAGGIO INVIATO</p>
              <p>A: \${NUMERO}</p>
              <p style="color:#787880">Sessione salvata — prossimi invii senza QR</p>\`;
    console.log('[ARGOS] ✅ MESSAGGIO INVIATO a '+NUMERO);
    setTimeout(async()=>{
      await client.destroy();
      server.close();
      process.exit(0);
    }, 8000);
  } catch(err) {
    stato = 'SEND_FAILED';
    qrHtml = '<p class="err">❌ Invio fallito: '+err.message+'</p>';
    console.error('[ARGOS] ❌ Invio fallito:', err);
    process.exit(1);
  }
});

client.initialize();
JSEOF

# Sostituisci placeholder con valori reali
sed -i "s|NUMERO_PLACEHOLDER|${NUMERO}|g" send_qr_server.js
sed -i "s|MSG_PLACEHOLDER|${MSG_ESCAPED}|g" send_qr_server.js

echo "[ARGOS] ✅ send_qr_server.js pronto"
REMOTE

echo ""
echo "[ARGOS] ✅ Deploy completato su iMac"
echo "[ARGOS] Prossimo step:"
echo "  ssh gianlucadistasi@192.168.1.12 'cd ~/Documents/app-antigravity-auto/wa-sender && nohup node send_qr_server.js > /tmp/wa_log.txt 2>&1 &'"
echo "  open http://192.168.1.12:8765"
