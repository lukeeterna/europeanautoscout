---
name: argos-wa-debug
description: >
  ADDENDUM a argos-outreach-automation. Usa SEMPRE questa skill quando:
  il log dice INVIATO ma WhatsApp non mostra il messaggio, sessione esiste
  ma invio non confermato visivamente, "messaggio non arrivato", "wa non inviato",
  "verifica invio", "debug whatsapp", "sessione corrotta", "reset sessione".
  PRIORITÀ su argos-outreach-automation in caso di conflitto.
version: 1.0.0
allowed-tools: Bash, Read, Write
---

# ARGOS™ WA Debug — Addendum CoVe 2026

## PROBLEMA NOTO: "log dice INVIATO, WA non mostra nulla"

### Cause possibili (in ordine di probabilità)

| Causa | Sintomo | Fix |
|---|---|---|
| Sessione SIM sbagliata | Auth ok ma da SIM diversa da Very Mobile | Reset + re-auth Very Mobile |
| `sendMessage` silent fail | Log INVIATO, nessun receipt | Debug con ACK check |
| Numero non su WA | Chat non esiste | Verifica con `isRegisteredUser()` |
| Sessione corrotta/vecchia | Reconnect automatico senza QR | Reset forzato |
| Formato numero sbagliato | `@c.us` accettato ma numero inesistente | Verifica formato |

---

## STEP D1 — Verifica formato numero

```bash
# Numero usato: 393336142544
# Formato corretto IT: 39 (paese) + 10 cifre
# Verifica: 393336142544 = 39 + 3336142544 = ✅ 10 cifre locali

ssh gianlucadistasi@192.168.1.12 "
  export PATH=/usr/local/bin:\$PATH
  node -e \"
const { Client, LocalAuth } = require('/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-sender/node_modules/whatsapp-web.js');
const client = new Client({
  authStrategy: new LocalAuth({
    clientId: 'argosautomotive',
    dataPath: '/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth'
  }),
  puppeteer: {headless:true, args:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu']}
});
client.on('ready', async () => {
  const num = '393336142544@c.us';
  const exists = await client.isRegisteredUser(num);
  console.log('NUMERO_REGISTRATO_WA:', exists);
  if (exists) {
    const contact = await client.getContactById(num);
    console.log('NOME_WA:', contact.pushname || contact.name || 'n/a');
  }
  await client.destroy();
  process.exit(0);
});
client.on('auth_failure', () => { console.log('AUTH_FAILURE'); process.exit(1); });
client.initialize();
\" 2>/dev/null
"
```

**OUTPUT ATTESO:**
- `NUMERO_REGISTRATO_WA: true` → numero corretto, problema è altrove
- `NUMERO_REGISTRATO_WA: false` → numero sbagliato o non su WA
- `AUTH_FAILURE` → sessione corrotta → vai a STEP D3

---

## STEP D2 — Identifica SIM attiva nella sessione

```bash
ssh gianlucadistasi@192.168.1.12 "
  export PATH=/usr/local/bin:\$PATH
  node -e \"
const { Client, LocalAuth } = require('/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-sender/node_modules/whatsapp-web.js');
const client = new Client({
  authStrategy: new LocalAuth({
    clientId: 'argosautomotive',
    dataPath: '/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth'
  }),
  puppeteer: {headless:true, args:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu']}
});
client.on('ready', async () => {
  const me = await client.getContactById(client.info.wid._serialized);
  console.log('ACCOUNT_ATTIVO:', client.info.wid.user);
  console.log('NOME:', client.info.pushname);
  console.log('PIATTAFORMA:', client.info.platform);
  await client.destroy();
  process.exit(0);
});
client.on('auth_failure', () => { console.log('AUTH_FAILURE — sessione corrotta'); process.exit(1); });
client.initialize();
\" 2>/dev/null
"
```

**Verifica:** `ACCOUNT_ATTIVO` deve corrispondere al numero Very Mobile IT.
Se è un numero diverso → sessione sbagliata → STEP D3.

---

## STEP D3 — Reset sessione e re-autenticazione pulita

```bash
# 1. Kill processi node esistenti su iMac
ssh gianlucadistasi@192.168.1.12 "
  pkill -f 'node' 2>/dev/null || true
  sleep 2
  echo 'Processi node terminati'
"

# 2. Elimina sessione corrotta/sbagliata
ssh gianlucadistasi@192.168.1.12 "
  rm -rf ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/
  echo 'Sessione eliminata'
"

# 3. Verifica pulizia
ssh gianlucadistasi@192.168.1.12 "
  ls ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/ 2>&1 || echo 'OK — directory assente'
"
```

---

## STEP D4 — Re-auth forzata con receipt check

Crea questo script su iMac (versione con verifica consegna):

```bash
ssh gianlucadistasi@192.168.1.12 "cat > ~/Documents/app-antigravity-auto/wa-sender/send_verified.js" << 'JSEOF'
const { Client, LocalAuth } = require('./node_modules/whatsapp-web.js');
const qrcode = require('./node_modules/qrcode');
const http = require('http');

const NUMERO   = process.argv[2] || '393336142544@c.us';
const MSG      = process.argv[3] || 'test';
const BASE_DIR = __dirname;

let html = '<p>⏳ Init Chromium (1-2 min su iMac 2012)...</p>';
let stato = 'INIT';

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type':'text/html;charset=utf-8'});
  res.end(`<!DOCTYPE html><html>
<head><meta charset="utf-8"><title>ARGOS™ ${stato}</title>
<style>body{background:#08080A;color:#fff;font-family:sans-serif;text-align:center;padding:40px}
h1{color:#B8960C} svg{border:3px solid #B8960C;border-radius:8px;margin:20px auto;display:block;max-width:380px}
.ok{color:#00e676} .err{color:#ff1744} .warn{color:#ffab00}</style></head>
<body><h1>ARGOS™ WA Auth</h1>
<p>Stato: <strong>${stato}</strong></p>${html}
<p style="color:#787880;font-size:.85em">Account attivo: ${client.info ? client.info.wid.user : 'n/a'}</p>
<script>if(!document.title.includes('✅')&&!document.title.includes('❌'))setTimeout(()=>location.reload(),3000)</script>
</body></html>`);
});

server.listen(8765,'0.0.0.0',()=>{
  console.log('>>> http://192.168.1.12:8765 — apri nel browser MacBook <<<');
});

const client = new Client({
  authStrategy: new LocalAuth({
    clientId: 'argosautomotive',
    dataPath: BASE_DIR + '/.wwebjs_auth'
  }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu','--no-first-run']
  }
});

client.on('qr', async qr => {
  stato = '📱 SCANSIONA QR';
  console.log('QR pronto — apri browser e scansiona con Very Mobile SIM');
  try {
    html = await qrcode.toString(qr, {type:'svg',width:360,margin:2});
  } catch(e) { html = '<p class="err">SVG error: '+e.message+'</p>'; }
});

client.on('authenticated', () => {
  stato = '🔐 AUTENTICATO';
  html = '<p class="ok" style="font-size:1.8em">✅ Autenticato</p><p>Verifica account...</p>';
  console.log('Autenticato');
});

client.on('auth_failure', () => {
  stato = '❌ AUTH FAILURE';
  html = '<p class="err">Auth fallita — elimina sessione e riprova</p>';
  console.error('AUTH FAILURE');
  setTimeout(()=>process.exit(1), 5000);
});

client.on('ready', async () => {
  const account = client.info.wid.user;
  console.log('Account attivo:', account);
  stato = '📤 INVIO';
  html = `<p class="ok">✅ Auth come: <strong>+${account}</strong></p><p>Verifica numero destinatario...</p>`;

  // Step 1: verifica numero registrato
  const NUM_CLEAN = NUMERO.replace('@c.us','');
  let isRegistered = false;
  try {
    isRegistered = await client.isRegisteredUser(NUMERO);
    console.log('Numero registrato su WA:', isRegistered);
  } catch(e) {
    console.log('isRegisteredUser error:', e.message);
  }

  if (!isRegistered) {
    stato = '❌ NUMERO NON WA';
    html = `<p class="err">❌ +${NUM_CLEAN} NON è registrato su WhatsApp</p>
            <p>Verifica il numero con Mario direttamente</p>`;
    console.error('NUMERO NON REGISTRATO SU WHATSAPP:', NUMERO);
    await client.destroy();
    server.close();
    process.exit(1);
  }

  // Step 2: invio con receipt check
  try {
    console.log('Invio a', NUMERO, '...');
    const msg = await client.sendMessage(NUMERO, MSG);
    console.log('Message ID:', msg.id._serialized);
    console.log('ACK iniziale:', msg.ack); // 0=pending, 1=sent, 2=received, 3=read

    stato = '✅ INVIATO';
    html = `<p class="ok" style="font-size:1.8em">✅ MESSAGGIO INVIATO</p>
            <p>Da: +${account}</p>
            <p>A: +${NUM_CLEAN}</p>
            <p>Message ID: ${msg.id._serialized}</p>
            <p>ACK: ${msg.ack} (1=server ricevuto, 2=device ricevuto, 3=letto)</p>
            <p style="color:#787880">Controlla WhatsApp — il messaggio deve apparire nella chat</p>`;

    console.log('✅ INVIATO — Message ID:', msg.id._serialized);
    console.log('VERIFICA: apri WhatsApp e controlla la chat con +'+NUM_CLEAN);

    setTimeout(async()=>{
      await client.destroy();
      server.close();
      process.exit(0);
    }, 15000);

  } catch(err) {
    stato = '❌ SEND FAILED';
    html = `<p class="err">❌ Invio fallito: ${err.message}</p>`;
    console.error('SEND ERROR:', err.message);
    await client.destroy();
    server.close();
    process.exit(1);
  }
});

client.initialize();
JSEOF

echo "send_verified.js creato"
```

---

## STEP D5 — Avvio e monitoraggio

```bash
# Kill tutto e avvia fresh
ssh gianlucadistasi@192.168.1.12 "
  export PATH=/usr/local/bin:\$PATH
  pkill -f 'node.*send' 2>/dev/null || true
  sleep 2
  cd ~/Documents/app-antigravity-auto/wa-sender
  nohup node send_verified.js '393336142544@c.us' 'Buongiorno Mario, sono Luca Ferretti.\nHo individuato una BMW 330i G20 con km verificati 45.200 a €27.800 franco DE — margine potenziale per Lei €3.100.\nPosso mandarle una scheda tecnica?' > /tmp/wa_verified.txt 2>&1 &
  echo 'Avviato PID:' \$!
  sleep 8 && cat /tmp/wa_verified.txt
"

# Apri browser per QR
open http://192.168.1.12:8765
```

**AZIONE UMANA:** scansiona QR con Android Very Mobile SIM.
Il browser mostrerà `Account attivo: +NUMERO` — verifica che sia il Very Mobile.

---

## STEP D6 — Proof of send reale

```bash
ssh gianlucadistasi@192.168.1.12 "
  echo '=== LOG VERIFICATO ==='
  cat /tmp/wa_verified.txt
  echo '=== SESSIONE ==='
  ls ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/session-argosautomotive/ 2>&1 | wc -l
"
```

**PROOF REALE richiede TUTTI questi:**
1. Log: `Account attivo: 39XXXXXXXXXX` (numero Very Mobile)
2. Log: `Numero registrato su WA: true`
3. Log: `✅ INVIATO — Message ID: xxx`
4. Browser mostra ACK ≥ 1
5. **Controllo visivo WhatsApp** — messaggio visibile nella chat

**Se ACK = 0** → messaggio pending/non consegnato → controlla connessione internet iMac
**Se `NUMERO NON REGISTRATO`** → numero Mario sbagliato o non usa WA personale

---

## INTEGRAZIONE CON SKILL PRINCIPALE

Aggiungere alla sezione ERRORI NOTI di `argos-outreach-automation/SKILL.md`:

```
| Log "INVIATO" ma WA vuoto | Sessione SIM sbagliata o silent fail | Usa argos-wa-debug STEP D1→D6 |
| Reconnect automatico senza QR | Sessione vecchia riutilizzata | Reset D3 + re-auth D4 |
| ACK = 0 | Pending, non consegnato | Verifica internet iMac |
| NUMERO NON REGISTRATO | Numero errato o non WA | Verifica contatto direttamente |
```
