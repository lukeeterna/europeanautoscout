# S148 — DEBUG WA daemon (invii falsi positivi scoperti in S147)

**Sessione**: S148
**Trigger**: bug critico S147 — daemon logga "✅ INVIATO via HTTP" ma messaggi NON consegnati. Marker TEST_FOUNDER + Day 1 Stile Car entrambi falsi positivi.
**Stato**: Stile Car **MAI realmente contattato** — DB rollback eseguito (PENDING/COLD/outbound=0).

---

## 0. Letture obbligatorie

1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` entry "2026-04-30 17:00 — S147 BUG CRITICO DAEMON"
2. `HANDOFF.md` sezione "S147 OUTCOME" + correzione S148
3. `wa-intelligence/wa-daemon.js` (sezioni `sendMessage`, `simulateTyping`, gestione errori)
4. `~/.pm2/logs/argos-wa-daemon-out.log` su iMac (pattern "INVIATO" + "Send failed" + "simulateTyping")

---

## 1. Diagnosi pre-fix

### 1.1 Verifica sessione WA (manuale Luke)
Sul telefono ARGOS Business **3281536308**:
1. WhatsApp → menu (3 puntini) → **Dispositivi collegati**
2. Esiste sessione "WhatsApp Web" o "Desktop"?
   - **NO** → sessione persa, serve riautenticare via QR
   - **SÌ** ma vecchia/inattiva → disconnetti tutti, ricomincia da capo
   - **SÌ** attiva e recente → bug è lib whatsapp-web.js, vai a 1.3

### 1.2 Re-auth QR (se 1.1 = NO)
```bash
ssh gianlucadistasi@192.168.1.2 'export NVM_DIR="$HOME/.nvm"; source "$NVM_DIR/nvm.sh"; nvm use --delete-prefix v20.11.0; export PATH="/Users/gianlucadistasi/.npm-global/bin:$PATH"; pm2 logs argos-wa-daemon --lines 100 --nostream' | grep -A 30 "QR"
```
Se daemon mostra QR ASCII → scansiona da telefono ARGOS Business.
Se non lo mostra → restart daemon: `pm2 restart argos-wa-daemon` + log immediato.

### 1.3 Verifica versione lib whatsapp-web.js (se 1.1 = SÌ)
```bash
ssh gianlucadistasi@192.168.1.2 "cat ~/Documents/app-antigravity-auto/wa-intelligence/package.json | grep -A 1 'whatsapp-web'"
ssh gianlucadistasi@192.168.1.2 "ls ~/Documents/app-antigravity-auto/wa-intelligence/node_modules/whatsapp-web.js/package.json && cat ~/Documents/app-antigravity-auto/wa-intelligence/node_modules/whatsapp-web.js/package.json | grep version"
```
Cercare versione installata vs latest. L'errore `chat.sendPresenceUpdate is not a function` indica API change. Possibili fix:
- **Upgrade**: `npm install whatsapp-web.js@latest` + restart
- **Downgrade**: pin a versione che aveva l'API funzionante (15/04 quando Enzo Car ha risposto "Nulla")
- **Patch**: nel codice `wa-daemon.js` cerca chiamate a `sendPresenceUpdate` e `chat.sendPresenceUpdate` — sostituisci/rimuovi con check `typeof chat.sendPresenceUpdate === 'function'` prima di chiamare

### 1.4 Test send post-fix (NON usare numeri reali)
Prima del primo test reale:
```bash
# Test marker su TEST_FOUNDER
echo '{"phone":"393314928901","message":"DEBUG marker S148","dealer_id":"TEST_FOUNDER"}' | ssh gianlucadistasi@192.168.1.2 'API_KEY=$(grep ARGOS_API_KEY ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2 | tr -d "\""); curl -s -X POST http://localhost:9191/send -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" --data-binary @-'
```
**Conferma manuale Luke**: messaggio arrivato sul telefono entro 10 secondi?
- **SÌ** → daemon fixato, procedere con Day 1 Stile Car (testo invariato in `DAY1_STILE_CAR.md`)
- **NO** → debug più profondo, NON inviare

---

## 2. Hardening daemon (post-fix, NON skippare)

### 2.1 Aggiungere ack delivery al daemon
Nel codice `wa-daemon.js` dopo `sendMessage()`:
- Aspettare evento `message_ack` con stato `ACK_DEVICE` o `ACK_READ`
- Logare "✅ DELIVERED" SOLO dopo ack ricevuto
- Se nessun ack entro 30s → log "⚠️ NO ACK DELIVERY" + alert Telegram + NON aggiornare conversations

### 2.2 Sostituire log "INVIATO via HTTP" con "QUEUED via HTTP"
Onestà sui log. Il fatto che il daemon abbia ricevuto la richiesta HTTP non significa nulla per il dealer.

### 2.3 Endpoint `/send` deve restituire success SOLO dopo ack
Cambiare la response API da:
```json
{"status":"sent","msg_id":"out_..."}
```
a:
```json
{"status":"queued","msg_id":"out_...","ack_pending":true}
```
+ endpoint `/messages/<msg_id>/status` per poll delivery.

---

## 3. Rinviare Day 1 Stile Car (solo dopo daemon verde)

Stile Car è **ancora COLD** — DB rollback completato. Quando il daemon è fixato:
1. Re-eseguire pre-flight 1.1-1.4 di `prompts/s147_day1_stile_car_invio.md`
2. Verificare listing X3 ancora vivo (`curl -sI` 200) — il listing potrebbe essere sparito nel frattempo
3. Se listing 404 → rieseguire scrape live (`tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"`)
4. Inviare Day 1 (testo già pronto in `DAY1_STILE_CAR.md`)
5. Verificare delivery REALE su telefono ARGOS Business (Luke conferma con screenshot)
6. SQL UPDATE conversations SOLO dopo conferma delivery

---

## 4. Vincoli S148

- ✋ NESSUN messaggio reale (a Stile Car o altri dealer) finché il daemon non passa test 1.4 con conferma manuale
- ✋ NON aggiornare `conversations` con DAY1_SENT senza conferma delivery REALE da telefono
- ✋ NON fidarsi di `wa_status:connected` nel JSON `/status` — è cached
- ✋ Se serve riavvio sessione WA con QR → richiede presenza fisica Luke col telefono Business
- ✋ Modifiche a `wa-daemon.js`: prima leggere TUTTO il file, capire architettura ack handling, non bricolage incrementale

---

## 5. Riferimenti

- IP iMac: `192.168.1.2`
- Daemon: `http://192.168.1.2:9191`
- Daemon source: `~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js` (su iMac)
- Pacchetto: `whatsapp-web.js` (versione da verificare)
- Test number Luke: `393314928901` (TEST_FOUNDER)
- Numero ARGOS Business (sender): `3281536308`
- Stile Car (target reale): `393334254654` / TIER0_FG_001 / RELAZIONALE 8.5 — **ANCORA COLD post-rollback S147**
- Listing X3: https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-ahk-hifi-sportsitze-benzin-schwarz-70dcd99b-3d68-45ac-ae20-2113e8f3d719 (vivo a 30/04 16:43, da riverificare in S148)

---

## 6. Storia bug (per future debug session)

- **15/04**: Enzo Car risponde "Nulla" → daemon FUNZIONAVA
- **27/04 (S145)**: WA daemon "uptime 12gg, connected" — non testato invio reale
- **28/04 (S146)**: PM2 resurrect post crash better-sqlite3, daemon "connected" 0/15 inviati — non testato invio reale
- **30/04 mattina (S147)**: PM2 daemon vuoto post-reboot iMac → resurrect → "connected" + 0/15
- **30/04 10:51**: marker test TEST_FOUNDER → log "INVIATO" → **non arrivato**
- **30/04 16:44**: Day 1 Stile Car → log "INVIATO" → **non arrivato**
- **30/04 17:00**: scoperto bug, rollback DB, prompt S148

Punto di rottura ignoto fra 15/04 e 30/04. Possibile: aggiornamento WhatsApp sul telefono ARGOS Business + lib whatsapp-web.js outdated.
