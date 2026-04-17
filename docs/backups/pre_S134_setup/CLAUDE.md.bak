# ARGOS — combaretrovamiauto-enterprise

## Stato pipeline
- E2E: NON FUNZIONANTE — scraper 404 su Mercedes + BMW sedan, seller_name NULL su AS24.it
- WA daemon: ONLINE su iMac (porta 9191)
- Dealer contattati reali: 0 (TEST_FOUNDER in attesa risposta fino al 23 Aprile)
- Scraper OK: BMW X3/X1/X5, Audi Q5/A4 | Scraper ROTTI: BMW Serie 3/5, Mercedes GLC/C/E/GLE

## Sprint corrente
Leggi `CURRENT_SPRINT.md` prima di fare qualsiasi cosa.
Non iniziare Task N+1 prima che Task N sia DONE.
Se trovi un problema nuovo, scrivilo in `BACKLOG.md`, non risolverlo ora.

## Regole invariate
- Test su TEST_FOUNDER (393314928901) prima di qualsiasi dealer reale
- Max 1 messaggio Day 1 per numero — verifica daemon prima di ogni invio
- Day 1: MAI "Germania", "import", "premium", "cerco auto", "estero"
- Risposta dealer reale = query su `messages` table (NON su `current_step`)
- Zero nuove skill/agent/framework finche' pipeline E2E non funziona

## Compaction instructions
Preserva sempre: file modificati | stato task CURRENT_SPRINT.md | test results (pass/fail) | template Day 1 corrente

## Skill ARGOS — carica SOLO quando serve
- `/outreach-day1` → scrivi o valida messaggio Day 1 per un dealer
- `/cove-analysis` → scoring veicoli, query DuckDB, anomalie prezzo
- `/scraper-ops` → fix scraper, MODEL_SLUG, debug listing 404
- `/wa-daemon-ops` → daemon iMac, invio WA, verifica connessione

## File critici
- `tools/scrapers/autoscout_scraper.py` → scraper principale
- `dealer_network.sqlite` (iMac via SSH) → dealer queue
- `src/cove/data/cove_tracker.duckdb` → benchmark listing
- `CURRENT_SPRINT.md` → task correnti | `BACKLOG.md` → problemi parcheggiati

## Comandi
Test: `python3 argos.py test` | Deploy: `bash deploy/sync.sh`
Scrape: `python3 tools/on_demand_runner.py --marca BMW --budget 40000 --dealer "Nome"`
Status: `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"`

## Fine sessione
1. Aggiorna `~/.claude/projects/.../memory/MEMORY.md` (fuori dal repo — Write tool)
2. Crea `prompts/s{N+1}_*.md` + aggiorna `HANDOFF.md` (dentro il repo)
3. `git add HANDOFF.md prompts/s{N+1}_*.md && git commit && git push`

## Rules
@.claude/rules/identity.md
@.claude/rules/communication.md
@.claude/rules/cove.md
@.claude/rules/security.md
@.claude/rules/competitors.md
