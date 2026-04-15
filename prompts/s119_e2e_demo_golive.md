# S119 — E2E DEMO VERIFICATION → GO-LIVE AUTHORIZATION

## REGOLA ZERO (NON DEROGABILE)
Test live = SOLO 393314928901 (TEST_FOUNDER).
MAI dealer reali senza "go-live autorizzato" dal founder in questa sessione.

---

## STEP 0 — CONTEXT LOAD (eseguire prima di qualsiasi altra cosa)

```bash
# 1. Leggi stato sessione precedente
cat HANDOFF.md
cat memory/MEMORY.md  # via Read tool

# 2. Verifica stato iMac
ssh gianlucadistasi@192.168.1.2 "
  export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
  pm2 list
"

# 3. Health check daemon
APIKEY=$(grep -E '^ARGOS_API_KEY=' ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2)
curl -s http://localhost:9191/health -H "X-API-Key: $APIKEY" | python3 -m json.tool
```

**STOP se:** daemon offline, WA disconnesso, daily_limit esaurito.
**CONTINUA solo se:** `wa_status: connected`, `agent_status: active`, `is_business_hours: true`.

---

## BLOCCO 1 — E2E COMPLETO SU NUMERO DEMO

Esegui ogni step in sequenza. Ogni step ha un CRITERIO DI PASS/FAIL esplicito.
NON passare allo step successivo se lo step corrente e' FAIL.

### STEP 1.1 — Verifica stato iniziale TEST_FOUNDER

```python
# Agente: api-tester
ssh gianlucadistasi@192.168.1.2 "python3 -c \"
import sqlite3
con = sqlite3.connect('Documents/app-antigravity-auto/dealer_network.sqlite')
row = con.execute('''
    SELECT dealer_id, conversation_state, current_step,
           outbound_count, inbound_count, last_inbound_at
    FROM conversations WHERE dealer_id = 'TEST_FOUNDER'
''').fetchone()
print('TEST_FOUNDER:', row)
msgs = con.execute('''
    SELECT direction, body[:80], timestamp_it FROM messages
    WHERE dealer_id = 'TEST_FOUNDER' ORDER BY timestamp_it DESC LIMIT 5
''').fetchall()
for m in msgs: print(m)
con.close()
\""
```

**PASS:** stato leggibile, nessun messaggio inviato nelle ultime 24h (daily cooldown ok)
**FAIL → FIX:** resetta TEST_FOUNDER a COLD se necessario per il test

```python
# Reset a COLD per test pulito
con.execute("UPDATE conversations SET conversation_state='COLD', current_step='PENDING', outbound_count=0, inbound_count=0, last_contact_at=NULL WHERE dealer_id='TEST_FOUNDER'")
```

---

### STEP 1.2 — Genera veicolo reale per il test

```bash
# Agente: api-tester → chiama on_demand_runner
ssh gianlucadistasi@192.168.1.2 "cd Documents/app-antigravity-auto && \
  python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer 'TEST_DEALER' 2>&1 | tail -5"
```

**PASS:** `Pipeline completata in Xs — dossiers/ARGOS_BMW_X3_TEST_DEALER_*.pdf`
**FAIL:** se PDF non generato, eseguire separatamente:
```bash
python3 tools/scripts/pdf_generator_enterprise.py \
  --data "$(cat dossiers/ARGOS_BMW_X3_*.json)" \
  --dealer 'TEST_DEALER' --output dossiers/
```

Estrai dati veicolo top (anno, km, prezzo, margine stimato) — servono per il messaggio.

---

### STEP 1.3 — Day 1: invio messaggio su TEST_FOUNDER

Componi il messaggio usando i dati reali estratti dallo step 1.2.
Template (adatta con dati reali, NON inventare):
```
buongiorno, sono Luca Ferretti.

ho una [MARCA] [MODELLO] [ANNO], [KM] km, [COLORE] — [PREZZO_EU] euro in Germania.

a lei resta un margine di circa [MARGINE] euro netti, bisarca e pratiche incluse.

le mando la scheda se interessato. che tipo di macchine cerca di solito?
```

```bash
APIKEY=$(grep -E '^ARGOS_API_KEY=' wa-intelligence/.env | cut -d= -f2)
curl -s -X POST http://localhost:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APIKEY" \
  -d '{
    "phone": "393314928901",
    "message": "<TESTO COMPOSTO>",
    "dealer_id": "TEST_FOUNDER",
    "template_id": "DAY1_INTRO"
  }' | python3 -m json.tool
```

**PASS:** `{"status": "sent", "first_contact": true/false, "daily_sent": N}`
**FAIL:** errore HTTP, WA error, guard blocked

Verifica DB dopo invio:
```sql
SELECT current_step, outbound_count, last_contact_at FROM conversations
WHERE dealer_id = 'TEST_FOUNDER';
-- PASS: current_step = 'DAY1_SENT', outbound_count >= 1, last_contact_at NOT NULL
```

---

### STEP 1.4 — Simula inbound CURIOSITY

Invia dal telefono del founder (393314928901) verso il numero WA business (3281536308):
```
chi è lei?
```

Attendi 30-60 secondi. Verifica risposta automatica:
```bash
ssh gianlucadistasi@192.168.1.2 "python3 -c \"
import sqlite3
con = sqlite3.connect('Documents/app-antigravity-auto/dealer_network.sqlite')
msgs = con.execute('''
    SELECT direction, body, timestamp_it FROM messages
    WHERE dealer_id = 'TEST_FOUNDER'
    ORDER BY timestamp_it DESC LIMIT 5
''').fetchall()
for m in msgs: print(m)
pending = con.execute('''
    SELECT reply_text[:100], sent, created_at FROM pending_replies
    WHERE dealer_id = 'TEST_FOUNDER' ORDER BY created_at DESC LIMIT 3
''').fetchall()
print('PENDING:', pending)
con.close()
\""
```

**PASS:** messaggio INBOUND registrato + reply OUTBOUND inviata automaticamente
**FAIL:** nessuna risposta in 60s → controllare `pm2 logs argos-wa-daemon --lines 50`

---

### STEP 1.5 — Simula inbound OBJECTION

Invia dal telefono:
```
quanto costa il servizio?
```

**PASS:** risposta automatica entro 60s, nessuna fee menzionata, tono B2B
**FAIL → DEBUG:** `pm2 logs argos-wa-daemon --lines 30` + controllare LLM cascade

Verifica risposta non contiene parole vietate:
```bash
# Parole vietate: fee, €, euro, costo, prezzo, servizio, algoritmo, piattaforma
```

---

### STEP 1.6 — Simula inbound NEGATIVE

Invia dal telefono:
```
non mi interessa grazie
```

**PASS:**
- Nessuna risposta inviata dal sistema
- `current_step = 'CLOSED_NO'` nel DB
- Notifica TG ricevuta con "DEALER CHIUSO — NEGATIVE"

```sql
SELECT current_step FROM conversations WHERE dealer_id = 'TEST_FOUNDER';
-- PASS: CLOSED_NO
```

---

### STEP 1.7 — Verifica Day 3 Scheduler

```bash
ssh gianlucadistasi@192.168.1.2 "
export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
# Simula dealer che non risponde da 3+ giorni
python3 -c \"
import sqlite3
con = sqlite3.connect('Documents/app-antigravity-auto/dealer_network.sqlite')
con.execute(\\\"UPDATE conversations SET current_step='DAY1_SENT', last_contact_at=datetime('now','-4 days'), conversation_state='CONTACTED' WHERE dealer_id='TEST_FOUNDER'\\\")
con.commit()
print('Impostato last_contact_at a 4 giorni fa')
con.close()
\"
# Forza esecuzione scheduler via API (se disponibile) o controlla log
curl -s http://localhost:9191/trigger-scheduler -H 'X-API-Key: <APIKEY>' 2>/dev/null || \
  echo 'Scheduler automatico ogni 30min — attendi o controlla pm2 logs'
"
```

**PASS:** Day 3 message inviato a 393314928901 entro 30min (scheduler polling)
**ALTERNATIVA:** verifica che la query del scheduler trovi il dealer:
```sql
SELECT dealer_id FROM conversations
WHERE current_step = 'DAY1_SENT'
  AND last_contact_at IS NOT NULL
  AND julianday('now') - julianday(last_contact_at) >= 3;
```

---

### STEP 1.8 — Health metrics post-test

```bash
curl -s http://localhost:9191/health-metrics -H "X-API-Key: $APIKEY" | python3 -m json.tool
```

**PASS:** `risk_level: GREEN` o `INSUFFICIENT_DATA`, `block_rate: 0.000`, `failed: 0`
**FAIL:** `risk_level: RED` o `block_rate > 0` → FERMA TUTTO, NON procedere al BLOCCO 2

---

## BLOCCO 2 — CONFRONTO CON FOUNDER → AUTORIZZAZIONE GO-LIVE

**Agente:** nessuno — questo e' un checkpoint umano obbligatorio.

Dopo BLOCCO 1 completato con tutti gli step PASS, presenta al founder:

### Checklist da mostrare al founder

```
=== SISTEMA PRONTO PER GO-LIVE? ===

STEP 1.1 — Stato DB pulito        [ PASS / FAIL ]
STEP 1.2 — Veicolo generato       [ PASS / FAIL ] → [marca modello anno km €prezzo]
STEP 1.3 — Day 1 inviato          [ PASS / FAIL ] → msg_id: [id]
STEP 1.4 — CURIOSITY gestito      [ PASS / FAIL ] → risposta: "[primi 50 char]"
STEP 1.5 — OBJECTION gestito      [ PASS / FAIL ] → risposta: "[primi 50 char]"
STEP 1.6 — NEGATIVE chiuso        [ PASS / FAIL ] → CLOSED_NO verificato
STEP 1.7 — Day 3 scheduler        [ PASS / FAIL ]
STEP 1.8 — Health GREEN           [ PASS / FAIL ] → risk: [livello]

Messaggi inviati oggi: [N] / 10
Nessun blocco WA: SI / NO

=== PROPOSTA PRIMO DEALER REALE ===
Nome: [dealer scelto]
Numero: [phone]
Veicolo: [marca modello anno €prezzo →€margine]
```

**DOMANDA AL FOUNDER:** "Confermato go-live con [dealer]?"

**Se SI** → esegui BLOCCO 3
**Se NO** → chiudi sessione, aggiorna HANDOFF con feedback

---

## BLOCCO 3 — PRIMO DEALER REALE (solo se BLOCCO 2 autorizzato)

### STEP 3.1 — Scegli dealer

Criteri (in ordine):
1. COLD (outbound_count = 0) — zero danni pregressi
2. Sud Italia + brand premium nel stock
3. Fit score >= 7.5

Candidati attuali: Autoline (TIER1_AV_002, Lioni AV), GP Cars (TIER1_TA_001, Manduria TA)

### STEP 3.2 — Genera veicolo per il dealer scelto

```bash
python3 tools/on_demand_runner.py \
  --marca BMW --modello X3 --budget 35000 \
  --dealer "<NOME_DEALER>"
```

Verifica PDF generato e dati veicolo (anno, km, prezzo, margine).

### STEP 3.3 — Invia Day 1

```bash
curl -s -X POST http://localhost:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APIKEY" \
  -d '{
    "phone": "<NUMERO_DEALER>",
    "message": "<MESSAGGIO_CON_DATI_REALI>",
    "dealer_id": "<DEALER_ID>",
    "template_id": "DAY1_INTRO"
  }'
```

**Verifica post-invio:**
```sql
SELECT current_step, outbound_count, last_contact_at
FROM conversations WHERE dealer_id = '<DEALER_ID>';
-- PASS: current_step = 'DAY1_SENT', last_contact_at NOT NULL
```

### STEP 3.4 — Monitora per 24h

```bash
# Ogni 6h (o quando TG notifica risposta):
curl -s http://localhost:9191/health-metrics -H "X-API-Key: $APIKEY"
```

- `risk_level: GREEN` → OK
- risposta dealer → sistema risponde autonomamente → verifica pending_replies
- `block_rate > 0.02` → `/pause` immediato via TG

---

## DONE CRITERIA S119

| Check | Metodo verifica |
|-------|----------------|
| Tutti step 1.1-1.8 PASS | Query DB + log daemon |
| Founder ha visto output e autorizzato | Confronto esplicito BLOCCO 2 |
| Se go-live: dealer in DAY1_SENT con last_contact_at | Query DB |
| HANDOFF aggiornato | Read HANDOFF.md |
| Commit e push | `git log -1` |

---

## NOTE TECNICHE

**pm2 PATH obbligatorio:**
```bash
export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:$PATH
```

**Verifica risposta reale (NON affidarsi a current_step):**
```sql
SELECT direction, body, timestamp_it FROM messages
WHERE dealer_id = ? ORDER BY timestamp_it;
```

**Se il daemon non risponde a un inbound:**
```bash
pm2 logs argos-wa-daemon --lines 50
# Cercare: BLOCKED, cooldown, business hours, DAILY_LIMIT
```

**Se il PDF non viene generato:**
```bash
python3 tools/scripts/pdf_generator_enterprise.py \
  --data "$(cat dossiers/ARGOS_BMW_X3_*.json)" \
  --dealer "Nome" --output dossiers/
```
