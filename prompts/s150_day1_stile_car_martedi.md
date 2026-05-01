# S150 — INVIO Day 1 Stile Car (martedì 5/5/2026 mattina)

**Sessione**: S150
**Data target invio**: martedì 5 maggio 2026, ore 11:00 (mattina lavorativa Sud, RELAZIONALE NON in giorno festivo)
**Trigger**: audit E2E S149b+S149c CHIUSO con verdetto 🟢 GO (`.planning/E2E-AUDIT-S149.md`). P0 ZERO. Daemon validato S149 (ack=1/2/3 + payload integro). Templates.py iMac fixato S149b. Image sanitizer/scrape/LLM cascade verificati S149c. Stile Car ANCORA COLD post-rollback S147. Day 1 messaggio già pronto in `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`.

---

## ⚠️ PRE-DAY1 GATE OBBLIGATORIO (S150 step -1, prima di qualsiasi altro)

**Configurare hold/manual approval su tutti gli intent diversi da NEGATIVE**.

Motivo: smoke test S149b ha rivelato che reply LLM `auto_approve_and_send` produce output qualità sotto-Cormorant (lowercase, no domanda chiusa, pitch generico) per intent CURIOSITY/POSITIVE/VEHICLE_REQUEST/INTEREST. Su Stile Car reale = primo dealer bruciato.

Soluzione pre-Day 1:
- ✅ NEGATIVE → template-first auto-send (OBJ_1_NO_INTEREST, verificato S149c test 7)
- ❌ Tutti gli altri intent → Telegram HOLD richiede approvazione Luke manuale prima di invio

Verificare in `wa-intelligence/response-analyzer.py` la funzione `auto_approve_and_send` (intorno r1844) e capire se esiste già un toggle per "hold-non-NEGATIVE" o se va patchato. Se va patchato → fix prima di Day 1.

---

## 0. Letture obbligatorie

1. `.planning/E2E-AUDIT-S149.md` (verdetto S149c GO + lista P1 da non sottovalutare)
2. `~/.claude/projects/.../memory/MEMORY.md` entry S149c
3. `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` (messaggio + post-invio SQL)
4. `.claude/rules/communication.md` (regole linguaggio Day 1)
5. `HANDOFF.md` sezione S149c → S150

---

## 1. Stato pre-S150

- ✅ Daemon WA fixato e validato S149 (3 patch attive + committate, ack=1/2/3 reale verificato con TEST_FOUNDER)
- ✅ Templates.py iMac fixato S149b (DAY3_SOFT + DAY3_VEHICLE \n escape)
- ✅ Image sanitizer iMac validato S149c (banner+OCR+inpaint OK su immagine reale)
- ✅ Scrape live BMW X3 validato S149c (10 PROCEED/17, MarketVerifier index OK)
- ✅ LLM cascade health S149c: GOOGLE_AI/GROQ/OPENROUTER tutte SET, fallback Groq operativo
- ⏳ Stile Car (393334254654, TIER0_FG_001, RELAZIONALE 8.5): COLD, mai contattato realmente
- ⏳ Listing BMW X3 xDrive20i 2022 €34.904 (Autohaus Becker-Tiemann Schaumburg): da ri-verificare 200 OK pre-invio
- ⏳ Pre-warming LinkedIn (follow Stile Car): impossibile strutturalmente — Stile Car non ha presenza LinkedIn (verificato S147). Deroga vincolo già motivata.

---

## 2. Pre-flight obbligatorio (martedì 5/5 ore 10:30)

```bash
# 1. SSH iMac raggiungibile
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime"

# 2. Daemon online + connected
ssh gianlucadistasi@192.168.1.2 "curl -s http://localhost:9191/status"
# Atteso: wa_status=connected, daily_sent=0, daily_remaining=15

# 3. Listing X3 ancora vivo (autoscout24.de)
curl -sI "https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-ahk-hifi-sportsitze-benzin-schwarz-70dcd99b-3d68-45ac-ae20-2113e8f3d719" | head -1
# Atteso: HTTP/2 200 (se 404 → vai a §6 fallback listing)

# 4. Stile Car ancora COLD in DB
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, dealer_name, current_step, conversation_state, outbound_count FROM conversations WHERE dealer_id='TIER0_FG_001';\""
# Atteso: TIER0_FG_001 | Stile Car | PENDING | COLD | 0

# 5. Test marker TEST_FOUNDER con payload Day 1 verbatim (replay hardening test S149)
# CRITICO: usa python3 per JSON safe (jq mancante su iMac)
ssh gianlucadistasi@192.168.1.2 'API_KEY=$(grep ARGOS_API_KEY ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2 | tr -d "\"")
PAYLOAD=$(python3 -c "
import json
msg = (
    \"Buongiorno, le scrivo direttamente — seguo BMW compatte e TEST è uno dei pochi piazzali sotto Foggia con un parco fatto bene.\n\n\"
    \"X3 xDrive20i 2022, 66.000 km, €34.900 — automatica, AHK, HiFi, sport. La stessa configurazione su AS24 Italia parte da €37.000.\n\n\"
    \"Margine netto per lei ~€3.400, fee €800 solo a consegna.\n\n\"
    \"Volevo proporla a lei prima che ad altri. Le mando la scheda?\n\n\"
    \"Luca\"
)
print(json.dumps({\"phone\":\"393314928901\",\"message\":msg,\"dealer_id\":\"TEST_FOUNDER\"}, ensure_ascii=False))
")
curl -s -X POST http://localhost:9191/send -H "Content-Type: application/json; charset=utf-8" -H "X-API-Key: $API_KEY" --data-binary "$PAYLOAD"'

# Atteso: status=sent + log mostra:
# - 📤 sendMessage returned wa_msg_id=true_*@lid_*
# - 🛰️ SENT_SERVER ack=1
# - 📬 DELIVERED ack=2
# entro 30s

# 5-bis. CONFERMA VISIVA Luke (CRITICA — gap noto S149)
# Luke deve verificare sul telefono 393314928901:
# - 5 paragrafi SEPARATI (non un blocco unico)
# - €34.900, ~€3.400, €37.000, €800 con simbolo € correttamente
# - "è" leggibile (non `?` né `\u00e8`)
# - "—" em dash leggibile (non quadratino)
# Se UNO solo rotto → STOP, problema encoding o whatsapp client
```

Se uno di questi step fallisce → STOP, debug, NO Day 1 invio.

---

## 3. Sequenza invio Day 1 (richiede OK Luke + finestra 11:00-12:00)

### Step 1 — leggi messaggio finale
File: `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` §"DAY 1 — messaggio"

```
Buongiorno, le scrivo direttamente — seguo BMW compatte e Stile Car è uno dei pochi piazzali sotto Foggia con un parco fatto bene.

X3 xDrive20i 2022, 66.000 km, €34.900 — automatica, AHK, HiFi, sport. La stessa configurazione su AS24 Italia parte da €37.000.

Margine netto per lei ~€3.400, fee €800 solo a consegna.

Volevo proporla a lei prima che ad altri. Le mando la scheda?

Luca
```

### Step 2 — invio via daemon
```bash
ssh gianlucadistasi@192.168.1.2 'API_KEY=$(grep ARGOS_API_KEY ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2 | tr -d "\"")
MSG="Buongiorno, le scrivo direttamente — seguo BMW compatte e Stile Car è uno dei pochi piazzali sotto Foggia con un parco fatto bene.\n\nX3 xDrive20i 2022, 66.000 km, €34.900 — automatica, AHK, HiFi, sport. La stessa configurazione su AS24 Italia parte da €37.000.\n\nMargine netto per lei ~€3.400, fee €800 solo a consegna.\n\nVolevo proporla a lei prima che ad altri. Le mando la scheda?\n\nLuca"
curl -s -X POST http://localhost:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"phone\":\"393334254654\",\"message\":\"$MSG\",\"dealer_id\":\"TIER0_FG_001\"}"'
```

Atteso response:
```json
{"status":"sent","msg_id":"out_<...>","daily_sent":1,"first_contact":true}
```

### Step 3 — analisi log post-send (entro 60s)
```bash
ssh gianlucadistasi@192.168.1.2 "tail -30 ~/.pm2/logs/argos-wa-daemon-out.log"
```

**Cerca**:
- `📤 sendMessage returned wa_msg_id=true_*@lid_*` (Patch 2 ✅)
- `🛰️ SENT_SERVER: ...393334254654...` (ack=1, server WA ricevuto)
- `📬 DELIVERED: ...393334254654...` (ack=2, telefono Stile Car ha ricevuto)
- `[STATE] TIER0_FG_001: → ENGAGED (out=1)`

**Se vedi `STALE_SESSION rilevata`** → STOP, daemon è stale, NON è arrivato. Vai a §5 recovery.

### Step 4 — verifica DB post-invio
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, current_step, conversation_state, outbound_count, last_contact_at FROM conversations WHERE dealer_id='TIER0_FG_001'; SELECT direction, body, wa_msg_id, timestamp_it FROM messages WHERE dealer_id='TIER0_FG_001' ORDER BY timestamp_it DESC LIMIT 1;\""
```
Atteso: `current_step=DAY1_SENT`, `conversation_state=ENGAGED` (o COLD se daemon non aggiorna in primo invio — verificare codice), `outbound_count=1`, `last_contact_at=<oggi>`. Messaggio in `messages` con `direction=OUTBOUND` e `wa_msg_id` formato `true_*@lid_*`.

---

## 4. Branch decisionali post-invio

### Branch A — invio confermato (ack=2 + DB aggiornato)
1. ✅ Day 1 Stile Car ANDATO (PRIMO DEALER REALE EVER)
2. Aggiorna MEMORY: data invio + msg_id reale + esito
3. Aggiorna `HANDOFF.md`: stato pipeline ora ha 1 ENGAGED
4. NO follow-up automatico — Day 3 (sabato 5/5) sarà S151 con foto HD + secondo veicolo
5. Monitor inbound: ogni inbound da 393334254654 trigger immediato analisi
6. Crea prompt S151 = "monitor risposta Stile Car + Day 3 prep"

### Branch B — STALE_SESSION rilevata
1. Daemon ha bloccato il send (Patch 3 funziona)
2. Re-auth QR (vedi prompt S149 §Branch B)
3. Post re-auth: ri-test marker TEST_FOUNDER → poi ri-tentativo Day 1 SE giorno è ancora sabato 2/5 e finestra business non è chiusa
4. Se finestra persa → riprogramma S151 per lunedì 4/5

### Branch C — ack=1 ma NO ack=2 entro 60s
1. Server WA ha ricevuto ma Stile Car non ha il messaggio (telefono spento? numero rotto?)
2. NON è failure daemon — è failure receiver
3. Aspetta 30 minuti, ri-controlla log per ack=2 ritardato
4. Se persiste 24h senza ack=2 → numero potenzialmente sbagliato, verifica fonte
5. NO Day 3 finché ack=2 arrivato

---

## 5. Recovery scenarios

### Listing X3 morto (404)
File: `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` ha solo X3 €34.904. Se 404:
1. Esegui scrape live: `python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"`
2. Top candidate PROCEED → ricalibra DAY1 con nuovi numeri
3. Riapprovazione Luke prima invio

### Daemon offline pre-invio
1. SSH iMac, `pm2 logs argos-wa-daemon --lines 50`
2. Se crash: `pm2 restart argos-wa-daemon` con NVM Node 20.11
3. Se sessione persa: re-auth QR
4. Se IP regress (`.12` invece `.2`): usa `.2` (vedi MEMORY S147 imac_network)

### Stile Car risponde "Chi sei?" pre-Day 3
DAY1_STILE_CAR.md ha §"Risposte pronte" con templates per:
- "Quanto costa?" → success fee €800 a consegna
- "Chi sei? Referenze?" → Luca persona + sito + 0 referenze (atto di fede)
- "Mandami la scheda" → invia PDF dossier

---

## 6. Vincoli S150 (immutabili)

- ✋ **NO INVIO se uno solo dei pre-flight (§2) fallisce**
- ✋ **NO INVIO domenica** (RELAZIONALE non manda festivo, sabato mattina ok)
- ✋ **NO INVIO prima delle 10:30** (mattina lavorativa Sud)
- ✋ **NO INVIO dopo le 12:30** (pranzo Sud)
- ✋ **MAX 1 messaggio Day 1** — se invio fallisce per timing, NON ritentare stesso giorno con messaggio diverso
- ✋ **NO modifica testo Day 1** rispetto a `DAY1_STILE_CAR.md` salvo Luke OK esplicito
- ✋ **NO Day 3 prep in S150** (rinvia a S151)
- ✋ **NO altri dealer** (Sa.My., Car Plus, Autoline, GP Cars) finché Stile Car non ha risposta

---

## 7. Target di fine S150

- ✅ Pre-flight verde (5/5 step §2)
- ✅ Day 1 inviato a Stile Car con ack=2 confermato dai log + DB aggiornato
- ✅ MEMORY aggiornata con outcome e msg_id reale
- ✅ HANDOFF aggiornato (pipeline: 1 ENGAGED reale)
- ✅ Prompt S151 pronto = monitor inbound Stile Car + prep Day 3 (sab 5/5)
- ✅ Commit + push

OPPURE

- ✅ Branch B/C identificato e gestito + prompt S151 ricalibrato

---

## 8. Riferimenti rapidi

- iMac IP: `192.168.1.2`
- Daemon: `http://192.168.1.2:9191`
- Stile Car WA: `393334254654`
- Stile Car DB: `TIER0_FG_001` / RELAZIONALE / 8.5 / Orta Nova FG
- TEST_FOUNDER (per pre-flight test): `393314928901`
- Listing X3: `https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-ahk-hifi-sportsitze-benzin-schwarz-70dcd99b-3d68-45ac-ae20-2113e8f3d719`
- Dossier PDF: `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf`
- Day 1 testo: `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`
- Daemon source: `wa-intelligence/wa-daemon.js` (committato S149)
