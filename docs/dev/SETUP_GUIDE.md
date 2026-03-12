# COMBARETROVAMIAUTO — SETUP GUIDE
## n8n Enterprise Workflow v1.0 | Pre-Deployment Checklist

---

## 1. ENVIRONMENT VARIABLES (.env n8n)

```bash
# DeepSeek
AI_API_KEY=sk-...                          # DeepSeek API key

# Telegram (nuovo token dopo revoca)
TELEGRAM_BOT_TOKEN=bot...                  # Nuovo token da BotFather
TELEGRAM_CHAT_ID=-100...                   # Chat ID notifiche escalation

# WAHA (già in running)
# Endpoint: http://localhost:3000
# Session: argosautomotive
```

---

## 2. IMPORT WORKFLOW IN N8N

1. n8n → Workflows → Import from File
2. Seleziona `combaretrovamiauto_workflow.json`
3. Configura credenziali:
   - Telegram: aggiungi credenziale con nuovo bot token
   - HTTP Request nodes: usano `$env.AI_API_KEY` (già da env)

---

## 3. DUCKDB SETUP

```bash
# Da ~/Documents/app-antigravity-auto
duckdb dealer_network.duckdb < schema_duckdb.sql

# Verifica
duckdb dealer_network.duckdb "SELECT * FROM conversations;"
```

**Sostituire nei seed data:**
- `INSERISCI_NUMERO_MARIO` → numero WhatsApp reale (solo cifre, no +)
- `INSERISCI_CITTA` → città salone
- `INSERISCI_URL_AUTOSCOUT` → URL listing BMW

---

## 4. WAHA WEBHOOK CONFIG

```bash
# Configura WAHA per inviare webhook a n8n
curl -X POST http://localhost:3000/api/sessions/argosautomotive/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://TUO_N8N_HOST:5678/webhook/waha-incoming",
    "events": ["message"]
  }'
```

---

## 5. PRE-REQUISITI BLOCCANTI

### PRE-REQ 1 — Account warm-up (7 giorni)
```
Giorno 1-2: max 5 messaggi/giorno (conversazioni reali)
Giorno 3-4: max 10 messaggi/giorno
Giorno 5-6: max 20 messaggi/giorno
Giorno 7:   max 30 messaggi/giorno → deployment Mario
```

### PRE-REQ 2 — Message variation test
Prima di contattare secondo dealer, verificare che
MSG1 venga variato da DeepSeek (stessa sostanza, forma diversa).
Test: triggera manualmente 3 volte e confronta output.

---

## 6. DRY RUN TEST

```bash
# Simula incoming message da Mario (test webhook)
curl -X POST http://TUO_N8N_HOST:5678/webhook/waha-incoming \
  -H "Content-Type: application/json" \
  -d '{
    "session": "argosautomotive",
    "payload": {
      "from": "NUMERO_MARIO_TEST@c.us",
      "body": "Principalmente tedesco. Ma già ho i miei canali. Chi è lei esattamente?",
      "type": "text"
    }
  }'
```

Verifica:
- [ ] DuckDB aggiornato con stage MSG1_SENT
- [ ] DeepSeek risponde con MSG2A appropriato
- [ ] Delay applicato (non risposta istantanea)
- [ ] Telegram NON notificato (non è escalation)

---

## 7. NODE DA COMPLETARE MANUALMENTE

Il nodo `DuckDB — Get Conversation State` usa executeCommand 
come placeholder. Sostituire con una delle opzioni:

**Opzione A — HTTP call a DuckDB wrapper:**
Crea un piccolo FastAPI server che espone query DuckDB via REST.

**Opzione B — n8n Execute Command:**
```bash
duckdb /path/to/dealer_network.duckdb \
  "SELECT * FROM conversations WHERE phone='{{ $json.phone }}' LIMIT 1" \
  -json
```

**Opzione C — SQLite fallback per MVP:**
Converti schema DuckDB in SQLite e usa il nodo nativo n8n SQLite.

---

## 8. STAGE FLOW REFERENCE

```
PENDING → (trigger manuale) → MSG1_SENT
MSG1_SENT → (risposta dealer) → QUALIFIED o CLOSED_NO
QUALIFIED → (agent pitch) → PITCH_SENT
PITCH_SENT → (obiezione dealer) → OBJECTION
OBJECTION → (risolto) → SUCCESS o CLOSED_NO
SUCCESS → (notifica Telegram) → MATERIAL_SENT
ESCALATION → (notifica Telegram) → human_override = TRUE
```

---

## DEPLOYMENT GO/NO-GO

| Check | Status |
|-------|--------|
| Nuovo Telegram bot token | ⬜ |
| WAHA account warm-up 7gg | ⬜ |
| DuckDB schema applicato | ⬜ |
| Mario seeded correttamente | ⬜ |
| Dry run test superato | ⬜ |
| Message variation verificata | ⬜ |
| Telegram alerts funzionanti | ⬜ |
| **DEPLOY MARIO OREFICE** | ⬜ |
