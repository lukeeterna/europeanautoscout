# S149 — RESTART daemon WA + test marker (patch S148 già applicate su disco)

**Sessione**: S149
**Trigger**: in S148 sono state applicate 3 patch a `wa-daemon.js` su iMac MA il daemon in memoria PM2 corre ancora il vecchio codice. Serve restart + test marker + analisi log per validare fix.
**Stato pre-S149**: Stile Car ANCORA COLD (rollback S147 valido). Nessun messaggio reale ancora inviato. Daemon online da ~21h+ (cached `connected`, NON validato per invio reale).

---

## 0. Letture obbligatorie

1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` entry "2026-05-01 08:50 — S148 DIAGNOSI WA daemon"
2. `HANDOFF.md` sezione S148 → S149
3. `prompts/S148_NEXT_SESSION_PROMPT.md` per contesto originale

---

## 1. Stato esatto pre-S149

**Patch applicate sul filesystem iMac** (`~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js`):
- Patch 1: log TUTTI gli ack 1/2/3/4 con `_serialized` wa_msg_id (~righe 724-744)
- Patch 2: capture `sentMsg.id._serialized` come `wa_msg_id` reale in DB (~righe 922-925, 940-941, 949)
- Patch 3: `client.getState()` live check pre-send → 503 + alert Telegram + log `STALE_SESSION` se ≠ `'CONNECTED'` (~righe 894-904)

**Verifiche già fatte**:
- Sintassi Node OK (`node --check`)
- Diff pulito (solo le 3 patch, nessun side-effect)
- Backup remoto: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js.bak_s148_20260501_092358`
- File è 1568 righe (era 1549, +19 linee coerenti con il diff)

**Cose NON ancora fatte**:
- ❌ `pm2 restart argos-wa-daemon` (daemon in memoria runtime ancora old code)
- ❌ Test marker TEST_FOUNDER post-fix
- ❌ Decisione su branch DELIVERED / STALE_SESSION / wa_msg_id=null
- ❌ Commit del fix nel repo combaretrovamiauto-enterprise (file vive solo sull'iMac)

---

## 2. Sequenza operativa S149

### Step 1 — pre-flight (read-only, ~30s)
```bash
ssh gianlucadistasi@192.168.1.2 'export NVM_DIR="$HOME/.nvm"; source "$NVM_DIR/nvm.sh" 2>/dev/null; nvm use 20.11.0 >/dev/null 2>&1; export PATH="/Users/gianlucadistasi/.npm-global/bin:$PATH"; pm2 list'
ssh gianlucadistasi@192.168.1.2 "curl -s http://localhost:9191/status"
ssh gianlucadistasi@192.168.1.2 "ls -la ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js.bak_s148_*"
ssh gianlucadistasi@192.168.1.2 "wc -l ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js"
```
Conferma: backup esiste, file è 1568 righe, daemon online.

### Step 2 — restart daemon (richiede OK Luke, ~15s downtime)
```bash
ssh gianlucadistasi@192.168.1.2 'export NVM_DIR="$HOME/.nvm"; source "$NVM_DIR/nvm.sh" 2>/dev/null; nvm use 20.11.0 >/dev/null 2>&1; export PATH="/Users/gianlucadistasi/.npm-global/bin:$PATH"; pm2 restart argos-wa-daemon && pm2 save'
```
Aspetta 20s. Tail log:
```bash
ssh gianlucadistasi@192.168.1.2 "tail -50 ~/.pm2/logs/argos-wa-daemon-out.log"
```
Cerca: `✅ Sessione autenticata` + `✅ Client PRONTO`. Se vedi `auth_failure` o `disconnected` → STOP, sessione persa, vai a Step 5.

### Step 3 — test marker TEST_FOUNDER (richiede Luke col telefono pronto)
```bash
ssh gianlucadistasi@192.168.1.2 'API_KEY=$(grep ARGOS_API_KEY ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2 | tr -d "\""); curl -s -X POST http://localhost:9191/send -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d "{\"phone\":\"393314928901\",\"message\":\"DEBUG marker S149 — fix daemon test\",\"dealer_id\":\"TEST_FOUNDER\"}"'
```
Output atteso post-fix:
- Caso A (sessione viva): `{"status":"sent","msg_id":"out_...","daily_sent":...}` → ok
- Caso B (sessione fantasma): `{"error":"stale_session","live_state":"UNPAIRED|null","cached_state":"connected"}` → 503

### Step 4 — analisi log (entro 60s da invio)
```bash
ssh gianlucadistasi@192.168.1.2 "tail -30 ~/.pm2/logs/argos-wa-daemon-out.log"
```
**Pattern da cercare**:
- `📤 sendMessage returned wa_msg_id=true_393314928901@c.us_XXXXX` → patch 2 funziona
- `🛰️ SENT_SERVER: 393314928901@c.us` (entro 5s) → ack 1 = lib ha consegnato al server WA
- `📬 DELIVERED: 393314928901@c.us` (entro 15s) → ack 2 = arrivato sul tuo telefono
- `✓✓ LETTO: 393314928901@c.us` (quando apri WA) → ack 3
- **Se vedi `STALE_SESSION rilevata pre-send`** → patch 3 ha rilevato sessione fantasma, vai a Step 5

**Conferma manuale di Luke**: messaggio "DEBUG marker S149" arrivato sul telefono entro 30s? SÌ/NO.

### Step 5 — fork decisionale

**Branch A — DELIVERED (ack=2 nel log + Luke conferma sul telefono)**:
1. Daemon FIXATO ✅
2. Commit fix nel repo combaretrovamiauto-enterprise:
   ```bash
   # Scarica file fixato dall'iMac per backup nel repo
   scp gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js wa-intelligence/wa-daemon.js
   git add wa-intelligence/wa-daemon.js
   git commit -m "fix(S148): WA daemon ack listener + getState pre-send + wa_msg_id reale"
   git push
   ```
3. Aggiorna MEMORY con outcome
4. Crea prompt S150 = invio Day 1 Stile Car sabato 2/5 mattina ore 11:00
5. Riverifica listing X3 ancora vivo prima del Day 1

**Branch B — STALE_SESSION (log `STALE_SESSION rilevata` + `live_state=UNPAIRED|null`)**:
1. Sessione fantasma CONFERMATA, lib whatsapp-web.js non emette `disconnected` event
2. Need re-auth QR — richiede Luke col telefono Business
3. Sequenza re-auth:
   - Luke: telefono ARGOS Business 3281536308 → WhatsApp → menu → Dispositivi collegati → disconnetti TUTTE (inclusa "argos")
   - SSH iMac: `pm2 restart argos-wa-daemon` (forza re-auth flow)
   - Aspetta 30s, poi: `curl http://192.168.1.2:9191/qr` da browser MacBook → QR appare
   - Luke: scansiona QR dal telefono Business
   - Verifica `curl http://192.168.1.2:9191/status` → `wa_status:connected`
   - Ri-test marker TEST_FOUNDER
4. Se re-auth ok → vai a Branch A
5. Se re-auth fallisce → analisi più profonda (lib upgrade vs downgrade)

**Branch C — wa_msg_id=null nel log (`📤 sendMessage returned wa_msg_id=null`)**:
1. La lib whatsapp-web.js@1.34.6 non ritorna l'oggetto Message → API change incompatibile
2. Investigare: leggere `node_modules/whatsapp-web.js/src/Client.js` metodo `sendMessage` per capire il return shape
3. Possibile fix: upgrade `whatsapp-web.js@latest` (dopo aver verificato changelog)
4. Test post-upgrade

**Branch D — caso peggiore (nessun ack di nessun livello entro 60s + state CONNECTED + wa_msg_id valido)**:
1. Sessione "tecnicamente connessa" ma server WA non riceve i messaggi
2. Diagnosi: aprire devtools puppeteer, controllare network requests
3. Possibile: rate-limit silenzioso, ban shadow, IP block
4. Mitigazione temporanea: cambiare client_id e re-auth come "argos2"

---

## 3. Vincoli S149 (immutabili)

- ✋ NO outreach reale finché Branch A confermato con ack=2 + occhi di Luke sul messaggio
- ✋ NO `UPDATE conversations.current_step='DAY1_SENT'` per Stile Car finché S150
- ✋ Stile Car (393334254654, TIER0_FG_001, RELAZIONALE 8.5) ANCORA COLD post-rollback S147 — no auto-update
- ✋ Se Branch B: re-auth richiede presenza fisica Luke col telefono Business
- ✋ Backup `wa-daemon.js.bak_s148_20260501_092358` su iMac NON cancellare finché Branch A confermato
- ✋ S149 NON è la sessione di invio Day 1 — è solo validazione fix daemon

---

## 4. Pre-flight rapido (per Claude Code S149)

```bash
# 1. SSH iMac raggiungibile su .2
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime"

# 2. Daemon stato
ssh gianlucadistasi@192.168.1.2 "curl -s http://localhost:9191/status"

# 3. File patched è 1568 righe
ssh gianlucadistasi@192.168.1.2 "wc -l ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js"

# 4. Backup esiste
ssh gianlucadistasi@192.168.1.2 "ls -la ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js.bak_s148_*"
```

Se uno di questi fallisce → STOP, debug pre-S149.

---

## 5. Target di fine S149

- ✅ Daemon restartato con patch attive in memoria
- ✅ Test marker TEST_FOUNDER esito noto (Branch A/B/C/D identificato)
- ✅ Se Branch A → daemon committato nel repo + prompt S150 pronto per invio Day 1 Stile Car
- ✅ Se Branch B → re-auth completato + Branch A o decisione esplicita di stop
- ✅ MEMORY + HANDOFF aggiornati con outcome reale

---

## 6. Riferimenti rapidi

- iMac IP: `192.168.1.2`
- Daemon endpoint: `http://192.168.1.2:9191` (porta 9191)
- TEST_FOUNDER (per marker test): `393314928901` — telefono personale Luke
- ARGOS Business sender: `3281536308`
- Stile Car (NO touch S149): `393334254654` / TIER0_FG_001 / RELAZIONALE 8.5
- Daemon source path: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js`
- Backup: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js.bak_s148_20260501_092358`
- Logs: `~/.pm2/logs/argos-wa-daemon-out.log` + `argos-wa-daemon-error.log`
- Lib: `~/node_modules/whatsapp-web.js/` (v1.34.6)
- Sessione persistence: `~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/session-argos-business/`
