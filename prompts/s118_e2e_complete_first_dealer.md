# S118 — COMPLETARE E2E TEST + PRIMO DEALER REALE

## STEP 0 — CONTEXT LOAD
1. `HANDOFF.md`
2. `memory/MEMORY.md`
3. `wa-intelligence/time-context.js` — verificare BUSINESS_HOURS.end

## BLOCCO 1 — CHIUSURA BUG APERTI (15 min)

### 1.1 Ripristina business hours
```javascript
// time-context.js:15 — riportare a 20
const BUSINESS_HOURS = { start: 8, end: 20 };
```
Deploy + restart.

### 1.2 Test NEGATIVE
Invia su WA: "non mi interessa"
PASS: classificazione NEGATIVE, stato CLOSED_NO, NESSUNA risposta inviata, TG notifica chiusura.

### 1.3 Test Day 3 scheduler
Forza esecuzione scheduler o simula data:
```bash
ssh gianlucadistasi@192.168.1.2 << 'EOF'
# Verifica che lo scheduler e' configurato per Day 3
grep -n "day3\|Day.3\|DAY3" wa-intelligence/wa-daemon.js | head -10
# Verifica candidati Day 3
python3 -c "
import sqlite3
con = sqlite3.connect('dealer_network.sqlite')
rows = con.execute('''
    SELECT dealer_id, dealer_name, conversation_state, current_step
    FROM conversations
    WHERE conversation_state = 'CONTACTED'
      AND last_contact_at < datetime('now', '-3 days')
''').fetchall()
for r in rows: print(r)
"
EOF
```

## BLOCCO 2 — PRIMO DEALER REALE (30 min)

### 2.1 Scegli dealer COLD
Raccomandati: Enzo Car (Ascoli Satriano FG), Autoline (Lioni AV), GP Cars (Manduria TA).
Nessun danno pregresso — zero messaggi inviati.

### 2.2 Genera veicolo reale
```bash
python3 tools/on_demand_runner.py --marca BMW --budget 35000 --dealer "Enzo Car"
```
Verifica PDF generato in dossiers/ con quality gate 7/7.

### 2.3 Componi e invia Day 1
Template (NO LLM):
```
buongiorno, sono Luca Ferretti.

ho una [MARCA] [MODELLO] [ANNO], [KM] km, [COLORE] — [PREZZO] euro in Germania.

a lei resta un margine di circa [MARGINE] euro netti, bisarca e pratiche incluse.

le mando la scheda se interessato. che tipo di macchine cerca di solito?
```

Invio via API:
```bash
curl -X POST http://localhost:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: KEY" \
  -d '{"phone":"NUMERO","message":"TESTO","dealer_id":"DEALER_ID","template_id":"DAY1_INTRO"}'
```

### 2.4 Monitora
- Telegram: /status /metrics
- Se risponde: sistema gestisce autonomamente
- Se non risponde: Day 3 scheduler parte automaticamente

## BLOCCO 3 — MONITORING 48H

Verifica ogni 12h:
```bash
curl http://localhost:9191/health-metrics -H "X-API-Key: KEY"
```
- risk_level GREEN → OK
- reply ricevuta → sistema risponde autonomamente
- block rate > 0 → FERMA TUTTO con /pause

## DONE CRITERIA

| Check | Pass | Status |
|-------|------|--------|
| Business hours ripristinato a 20 | time-context.js | ☐ |
| Test NEGATIVE → CLOSED_NO | DB query | ☐ |
| Day 3 scheduler verificato | log + DB | ☐ |
| Primo dealer COLD contattato | DB + TG | ☐ |
| 48h monitoring GREEN | /health-metrics | ☐ |
