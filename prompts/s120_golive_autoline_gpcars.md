# S120 — GO-LIVE AUTOLINE + GP CARS (se autorizzato)

## REGOLA ZERO (NON DEROGABILE)
Test live = SOLO 393314928901 (TEST_FOUNDER).
MAI dealer reali senza "go-live autorizzato" dal founder in questa sessione.

---

## CONTEXT (da S119)

**Cosa è già successo:**
- Enzo Car (TIER1_FG_002) ha risposto "Nulla" → NEGATIVE → CLOSED_NO
- Bug "Nulla"→UNKNOWN fixato in response-analyzer.py:1069
- Stile Car (TIER0_FG_001) + Sa.My. Auto (TIER0_CS_001): Day 1 inviato ieri, in attesa
- Car Plus (TIER0_AV_001): Day 1 inviato, step corretto
- Autoline (TIER1_AV_002) + GP Cars (TIER1_TA_001): COLD, pronti

**Deliverability confermata:** Enzo Car ha risposto in 10 minuti dal primo messaggio.

---

## STEP 0 — CONTEXT LOAD

```bash
ssh gianlucadistasi@192.168.1.2 "
  export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
  pm2 list
  APIKEY=\$(grep -E '^ARGOS_API_KEY=' ~/Documents/app-antigravity-auto/wa-intelligence/.env | cut -d= -f2)
  curl -s http://localhost:9191/health -H \"X-API-Key: \$APIKEY\" | python3 -m json.tool
"
```

**STOP se:** daemon offline, WA disconnesso.

---

## STEP 1 — VERIFICA RISPOSTE STILE CAR + SA.MY.

```sql
-- Messaggi reali (non solo current_step)
SELECT dealer_id, direction, body, timestamp_it FROM messages
WHERE dealer_id IN ('TIER0_FG_001', 'TIER0_CS_001')
ORDER BY timestamp_it;
```

- Se risposta inbound → classify + gestisci con response-analyzer
- Se nessuna risposta e julianday >= 3 → Day 3 scheduler parte automaticamente

---

## STEP 2 — GO-LIVE (solo se founder autorizza)

### Candidati in ordine preferenza
1. **Autoline** (TIER1_AV_002, Lioni AV) — COLD, TIER1
2. **GP Cars** (TIER1_TA_001, Manduria TA) — COLD, TIER1

### Per ogni dealer:

**2a. Genera veicolo**
```bash
ssh gianlucadistasi@192.168.1.2 "cd Documents/app-antigravity-auto && \
  python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 \
  --dealer '<NOME_DEALER>' 2>&1 | tail -5"
```

**2b. Componi Day 1 con dati reali**
```
buongiorno, sono Luca Ferretti.

ho una [MARCA] [MODELLO] [ANNO], [KM] km — [PREZZO_EU] euro in Germania.

a lei resta un margine di circa [MARGINE] euro netti, bisarca e pratiche incluse.

le mando la scheda se interessato. che tipo di macchine cerca di solito?
```

**2c. Invia**
```bash
APIKEY=$(grep -E '^ARGOS_API_KEY=' wa-intelligence/.env | cut -d= -f2)
curl -s -X POST http://localhost:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APIKEY" \
  -d '{"phone": "<NUMERO>", "message": "<TESTO>", "dealer_id": "<ID>", "template_id": "DAY1_INTRO"}'
```

**2d. Verifica post-invio**
```sql
SELECT current_step, outbound_count, last_contact_at
FROM conversations WHERE dealer_id = '<ID>';
-- PASS: current_step = 'DAY1_SENT', last_contact_at NOT NULL
```

---

## STEP 3 — HEALTH METRICS POST INVIO

```bash
curl -s http://localhost:9191/health-metrics -H "X-API-Key: $APIKEY" | python3 -m json.tool
```

- `risk_level: GREEN` o `INSUFFICIENT_DATA` → OK
- `block_rate > 0.02` → `/pause` immediato via TG

---

## DONE CRITERIA S120

| Check | Metodo |
|-------|--------|
| Stile Car + Sa.My.: risposte verificate in messages table | Query DB |
| Se go-live: dealers in DAY1_SENT con last_contact_at | Query DB |
| block_rate = 0 | health-metrics |
| HANDOFF + memory aggiornati | Write tool |
| Commit + push | git |
