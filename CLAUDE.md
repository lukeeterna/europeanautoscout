# ARGOS — combaretrovamiauto-enterprise

## CANONICO — questo repo (europeanautoscout) è il repo canonico ARGOS.
Archivio storico locale: ~/Documents/combaretrovamiauto-enterprise (SOLA LETTURA;
contiene la history pre-scrub e i dataset PII solo-locali).
Offsite del canonico = push su GitHub (i bundle T7 restano per l'archivio).
Regola doc: nelle doc versionate niente denominazioni nominative di ditte
individuali — citare per P.IVA o indice.
I 6 path in .gitignore non entrano MAI in git.

## Stato pipeline
- E2E: FUNZIONANTE (verificato S157) — scrape→CoVe→PDF su BMW Serie 3 in 41s, 2 PROCEED su 16 listing
- WA daemon: ONLINE su iMac (porta 9191)
- Dealer contattati reali: 0 (TEST_FOUNDER in attesa risposta fino al 23 Aprile)
- Scraper OK (verificato S157 — tutti producono ~20 listing/modello con price/km/seller_name): BMW X3/X1/X5/Serie 3/Serie 5, Audi Q5/A4, Mercedes Classe C/E/GLC/GLE

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
Esegui `/chiudi-ordinatamente` (`.claude/commands/chiudi-ordinatamente.md`): protocollo
idempotente che rigenera l'handoff canonico `HANDOFF_CURRENT.md` (root) da git/disco,
propone il commit dei soli file toccati (conferma y/n) e stampa il render per il giudice.
Lo stato vivo resta in `STATE.md` (GENERATO, non editare a mano) + `state/rings.json`;
le memorie cross-sessione in `~/.claude/projects/.../memory/MEMORY.md` (Write tool, fuori dal repo).

## Rules
@.claude/rules/identity.md
@.claude/rules/communication.md
@.claude/rules/cove.md
@.claude/rules/security.md
@.claude/rules/competitors.md
