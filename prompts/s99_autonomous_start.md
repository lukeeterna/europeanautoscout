# S99 — Sprint 1: Sicurezza + Infra (Agent-First)

## Contesto

S98 ha completato la deep research architetturale (9 ricerche parallele).
CLAUDE.md riscritto come Agent-First Operational Brain.
Skill-loader e skill-handover attivi.
Pipeline dealer FERMATA finche' test E2E non passano.

## Protocollo di avvio
1. SessionStart hook verifica automaticamente: skill, CLAUDE.md, WA daemon
2. Leggi `memory/MEMORY.md` per stato corrente
3. Leggi `research/s98_ARCHITETTURA_DEFINITIVA.md` per contesto architetturale
4. Se WA daemon unreachable → fix prima di tutto
5. Se tutto OK → procedi con Sprint 1

## Sprint 1 Tasks (in ordine)

### 1A. Sicurezza critica (1 ora)
- API key auth su `wa-daemon.js` porta 9191 (linea 884, bind 0.0.0.0)
  - Aggiungere header X-API-Key su tutti gli endpoint tranne GET /status
  - Generare ARGOS_API_KEY random, aggiungere a .env
  - Aggiornare tutti i caller (send_*.py, outreach_scheduler.py, dashboard)
- Fix command injection `telegram-handler.py` (linea 155)
  - reply_id e reply_text passati via shell interpolation
  - Sostituire con subprocess args list
- Input validation su /send: telefono italiano, messaggio <4096
- chmod 600 su .env e sqlite su iMac
- Prompt injection defense su response-analyzer.py
  - Sanitizzare input dealer (rimuovere pattern "ignora istruzioni")
  - Validare output LLM (no parole banned)

### 1B. Infra solida (2 ore)
- DB unificato: merge schema `conversations` + `dealers`
  - Creare `src/db.py` con migration system
  - Schema version table
  - WAL mode + busy_timeout=10000 ovunque
- `deploy/sync.sh` — rsync atomico con symlink swap
  - Exclude .env, node_modules, *.sqlite*, *.duckdb
  - npm ci solo se package.json cambiato
  - Healthcheck post-deploy
- Backup DB: cron iMac ogni 6h (`sqlite3 .backup`)
- Monitoring → Telegram alert ogni 5 min:
  - WA connected
  - DB integrity_check
  - LLM health (1 token test)
- Spostare TUTTI i cron da MacBook a iMac (il MacBook dorme)
- Fix IP 192.168.1.12 → 192.168.1.2 in deploy.sh

### 1C. LLM resiliente (1 ora)
- Signup Groq (gratis): console.groq.com → API key
- Installare Ollama su iMac: `brew install ollama && ollama pull llama3.2:8b`
- Creare `src/llm_cascade.py` con circuit breaker:
  1. Gemini Flash (250/day)
  2. Groq Llama 70B (1000/day, <1s)
  3. OpenRouter free router (1000/day)
  4. Gemini Lite (1000/day)
  5. Ollama locale (illimitato)
- Refactoring response-analyzer.py per usare cascade
- Health check LLM mattina (7:00) + alert se tutti down

### 1D. Test E2E automatico (30 min)
- Aggiungere `dry_run` flag su daemon /send
- `--dry-run` flag su response-analyzer.py
- 10 test automatici in `tests/test_e2e.py`:
  1. Daemon status
  2. Dealer in pipeline
  3. Send testo (dry_run)
  4. Send PDF (dry_run)
  5. Analyzer CURIOSITY
  6. Analyzer VEHICLE_REQUEST
  7. Analyzer OBJECTION
  8. Analyzer INTEREST
  9. Pipeline scrape→cove→pdf (--limit 10)
  10. Quality check risposta LLM

## Verifica finale Sprint 1
```bash
python3 tests/test_e2e.py → 10/10 PASS
bash deploy/sync.sh → deploy senza errori
ssh iMac "curl -s localhost:9191/status" → connected + auth
```

## Decisioni confermate dal founder
- iMac e' Intel (Ollama lento ma funziona come fallback)
- Facebook: aspettiamo ricorso
- Dashboard: la teniamo, utile per monitorare
- LLM: full-free (3250/day, nessun costo)
