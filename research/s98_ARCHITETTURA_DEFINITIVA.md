# ARGOS — Architettura Definitiva v1.0

**Data:** 2026-04-02
**Stato:** Pipeline fermata. Nessun dealer reale finche' questo piano non e' implementato e testato.

---

## 1. DIAGNOSI: PERCHE' SI ROMPE TUTTO

### 1.1 Due mondi scollegati
```
MacBook: /Users/macbook/Documents/combaretrovamiauto-enterprise/
  - dealer_network.sqlite (tabelle: dealers, market_*)
  - Codice sorgente, scraper, CoVe, PDF generator
  - Deploy: SCP manuale di singoli file

iMac: /Users/gianlucadistasi/Documents/app-antigravity-auto/
  - dealer_network.sqlite (tabelle: conversations, messages, pending_replies)
  - WA daemon, Telegram bot, scheduler
  - Riceve file via SCP, spesso non allineato
```
**Risultato:** Due DB con schema diversi, codice non sincronizzato, bug che appaiono solo su una macchina.

### 1.2 15 script scollegati
```
send_day1_tier1.py          — hardcoded dealer + messaggi
send_day1_tier1_batch2.py   — altro batch hardcoded
send_day7_tier0.py          — altro batch hardcoded
send_all_20260402.sh        — cron one-shot hardcoded
on_demand_runner.py         — pipeline scrape→cove→pdf
outreach_scheduler.py       — scheduler hourly
response-analyzer.py        — LLM risposte
dealer_crm.py               — CRM (tabella dealers)
wa-daemon.js                — daemon WA (tabella conversations)
scheduler.py                — scheduler 5min
telegram-handler.py         — Telegram approval
batch_runner.py             — batch scraper
pipeline_orchestrator.py    — pipeline CoVe
daily_scrape.sh             — cron 5am
pdf_generator_enterprise.py — PDF
```
Nessuno parla con gli altri in modo strutturato. Ogni connessione e' un hack.

### 1.3 Zero monitoring
- DB si corrompe → crash loop per ore senza alert
- OpenRouter esaurisce credito → 402 per ore senza alert
- Cron non gira (Mac in sleep) → nessuno lo sa
- Cap 3 reply/dealer raggiunto → test bloccato senza feedback

### 1.4 Deploy fragile
- `scp` di singoli file (puo' fallire silenziosamente)
- `deploy.sh` ha IP sbagliato (192.168.1.12 invece di .2)
- `npm rebuild` a mano quando Node version cambia
- `.env` diversi su ogni macchina, token duplicati
- Nessun rollback

### 1.5 Stato dealer duplicato
- Tabella `conversations` (daemon scrive)
- Tabella `dealers` (CRM scrive)
- **De-sync garantito** se entrambi aggiornano indipendentemente

---

## 2. ARCHITETTURA TARGET

### 2.1 Principio
**UN repo. UN DB. UN deploy. UN orchestratore. UN test che dice PASS/FAIL.**

### 2.2 Struttura unificata
```
combaretrovamiauto-enterprise/
├── argos.py                      ← CLI unico (vedi 2.4)
├── config/
│   ├── dealers.yaml              ← Pipeline dealer (fonte verita')
│   └── settings.yaml             ← Config sistema (limiti, modelli LLM, etc)
├── src/
│   ├── cove/                     ← CoVe Engine v4 (NON TOCCARE)
│   ├── orchestrator.py           ← Flusso completo discovery→fee
│   ├── llm_cascade.py            ← LLM con circuit breaker (vedi 3)
│   ├── sender.py                 ← Invio WA unificato
│   ├── monitor.py                ← Health check + alert Telegram
│   └── db.py                     ← Accesso DB unificato + migrazioni
├── tools/
│   ├── scrapers/                 ← Scraper portali EU (invariato)
│   └── scripts/
│       └── pdf_generator.py      ← PDF dossier
├── wa-intelligence/
│   ├── wa-daemon.js              ← Daemon WA (solo iMac)
│   ├── response-analyzer.py      ← Analyzer (usa llm_cascade)
│   └── ecosystem.config.js       ← PM2 config
├── tests/
│   ├── test_e2e.py               ← Test E2E completo (dry_run)
│   ├── test_llm.py               ← Test cascade LLM
│   ├── test_analyzer.py          ← Test classificazione + risposta
│   └── test_pipeline.py          ← Test scrape→cove→pdf
├── deploy/
│   ├── sync.sh                   ← rsync atomico → iMac
│   ├── restart.sh                ← Restart daemon
│   └── healthcheck.sh            ← Verifica post-deploy
├── .env                          ← UNICO file env
└── data/
    ├── dealer_network.sqlite     ← DB UNICO (schema unificato)
    └── cove_tracker.duckdb       ← DB CoVe (read-heavy, separato)
```

### 2.3 DB Unificato — Schema
Un singolo `dealer_network.sqlite` con tutte le tabelle:

```sql
-- Schema version tracking
schema_version (version INTEGER PK, applied_at TEXT, description TEXT)

-- Dealer (fonte verita' unica)
dealers (
  dealer_id TEXT PK,
  name, city, province, region, phone, wa_number, email,
  stock_size, brands_json, premium_pct,
  persona_type,  -- NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE
  tier,          -- TIER0/TIER1/TIER2/SKIP
  score_fit REAL,
  pipeline_status, -- PENDING/CONTACTED/INTERESTED/ACTIVE/CLOSED
  current_step,    -- DAY1_SENT/DAY3_SENT/DAY7_SENT/etc
  first_contact_at, last_contact_at, next_action_at, next_action_type,
  created_at, updated_at
)

-- Messaggi (inbound + outbound, tutti)
messages (
  id INTEGER PK,
  dealer_id TEXT FK,
  direction TEXT,     -- INBOUND/OUTBOUND
  body TEXT,
  classification TEXT, -- CURIOSITY/VEHICLE_REQUEST/OBJECTION/NEGATIVE/etc
  llm_model TEXT,      -- quale LLM ha generato la risposta
  wa_msg_id TEXT,
  delivery_status TEXT, -- SENT/DELIVERED/READ/FAILED
  created_at TEXT
)

-- Azioni pipeline (scheduler)
pipeline_actions (
  id INTEGER PK,
  dealer_id TEXT FK,
  action_type TEXT,    -- DAY1/DAY3/DAY7/DOSSIER/etc
  scheduled_at TEXT,
  executed_at TEXT,
  status TEXT          -- PENDING/EXECUTED/SKIPPED/FAILED
)

-- LLM cost tracking
llm_costs (
  id INTEGER PK,
  provider TEXT, model TEXT,
  tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL,
  dealer_id TEXT,
  created_at TEXT
)

-- System health
system_health (
  id INTEGER PK,
  component TEXT,  -- wa_daemon/llm/db/scraper
  status TEXT,     -- OK/WARN/ERROR
  error_msg TEXT,
  checked_at TEXT
)
```

**Regole SQLite multi-processo:**
- WAL mode sempre (set una volta, persiste)
- `busy_timeout = 10000` su ENTRAMBI Node e Python
- MAI cancellare -wal/-shm con processi aperti
- Backup via `sqlite3 .backup` (MAI `cp`)
- Checkpoint WAL ogni 30 minuti dal daemon

### 2.4 CLI Unificato
```bash
python3 argos.py status              # Stato pipeline + health
python3 argos.py discover            # Trova nuovi dealer
python3 argos.py profile DEALER_ID   # Profila dealer (archetipo, score)
python3 argos.py outreach DEALER_ID  # Prepara + invia Day 1
python3 argos.py search BMW X3 35000 # Scrape → CoVe → PDF
python3 argos.py send DEALER_ID PDF  # Invia dossier
python3 argos.py test                # Test E2E completo
python3 argos.py health              # Health check dettagliato
python3 argos.py deploy              # rsync + restart + healthcheck
```

---

## 3. LLM CASCADE — MAI PIU' FALLBACK TEMPLATE

### 3.1 Architettura a 5 livelli

```
TIER 1: Gemini 2.5 Flash       (FREE, 250/day, qualita' eccellente)
TIER 2: Groq Llama 3.3 70B     (FREE, 1000/day, <1s latenza)
TIER 3: OpenRouter free router  (FREE, 1000/day, auto-seleziona modello)
TIER 4: Gemini 2.5 Flash-Lite  (FREE, 1000/day, leggero)
TIER 5: Ollama locale su iMac  (UNLIMITED, 5-15s, MAI fallisce)
```

**Capacita' totale: 3.250+/day** (serve 50-100). Il sistema non puo' fallire.

### 3.2 Circuit Breaker per provider
Ogni provider ha 3 stati:
- **CLOSED** (sano): richieste normali
- **OPEN** (rotto): skip per `cooldown` secondi
- **HALF-OPEN** (test): 1 richiesta di prova

Trigger apertura: 3 fallimenti in 5 minuti.
Cooldown: 60s (errori server), 300s (rate limit), 24h (credito esaurito).

### 3.3 Nuovi provider da aggiungere

**Groq** (non ancora integrato):
- Endpoint: `https://api.groq.com/openai/v1/chat/completions` (OpenAI-compatibile)
- Modello: `llama-3.3-70b-versatile`
- Free: 30 RPM, 1000 req/day
- Latenza: <1 secondo (hardware LPU custom)
- Azione: creare account gratis su console.groq.com, ottenere API key

**Ollama** (non ancora installato):
- Endpoint: `http://localhost:11434/v1/chat/completions` (OpenAI-compatibile)
- Modello: `llama3.2:8b` (4GB RAM)
- Free: illimitato, locale
- Azione: `brew install ollama && ollama pull llama3.2:8b` su iMac

### 3.4 Health check proattivo
Ogni mattina alle 7:00, testa tutti i provider con 1 token. Logga quale funziona.
Se nessun cloud provider funziona → Telegram alert immediato.

---

## 4. DEPLOY ATOMICO

### 4.1 rsync + symlink swap (sostituisce scp)
```bash
# deploy/sync.sh
IMAC="gianlucadistasi@192.168.1.2"
RELEASE_DIR="/Users/gianlucadistasi/Documents/app-antigravity-auto/releases/$(date +%Y%m%d_%H%M%S)"
CURRENT="/Users/gianlucadistasi/Documents/app-antigravity-auto/current"

# 1. Sync a nuova release directory
rsync -az --delete \
  --exclude='.env' --exclude='node_modules/' \
  --exclude='*.sqlite*' --exclude='*.duckdb' \
  --exclude='__pycache__/' --exclude='.wwebjs_*' \
  ./ "$IMAC:$RELEASE_DIR/"

# 2. Rebuild node_modules solo se package.json cambiato
ssh $IMAC "cd $RELEASE_DIR/wa-intelligence && npm ci --production"

# 3. Symlink atomico
ssh $IMAC "ln -sfn $RELEASE_DIR $CURRENT"

# 4. Restart daemon
ssh $IMAC "export PATH=...pm2 restart argos-wa-daemon"

# 5. Healthcheck
ssh $IMAC "curl -sf http://localhost:9191/status" || echo "DEPLOY FAILED"

# 6. Rollback se fallisce
# ln -sfn PREVIOUS_RELEASE $CURRENT && pm2 restart
```

### 4.2 .env separato
`.env` vive FUORI dalle release, symlinked dentro:
```
/Users/gianlucadistasi/Documents/app-antigravity-auto/.env       ← persistente
/Users/gianlucadistasi/Documents/app-antigravity-auto/current/   ← symlink a release
```

### 4.3 Backup DB automatico
Cron iMac ogni 6 ore:
```bash
sqlite3 $DB ".backup '$BACKUP_DIR/dealer_network_$(date +%Y%m%d_%H%M%S).sqlite'"
# Mantieni ultimi 20 backup
ls -t $BACKUP_DIR/*.sqlite | tail -n +21 | xargs rm -f
```

---

## 5. MONITORING — ALERT TELEGRAM

### 5.1 Cosa monitorare (ogni 5 minuti)
| Check | Soglia | Alert |
|-------|--------|-------|
| WA daemon status | != "connected" | CRITICO |
| DB integrity | PRAGMA integrity_check != "ok" | CRITICO |
| LLM health | tutti i provider falliscono | CRITICO |
| Daily msg sent | > 25 (di 30) | WARNING |
| Disk space | < 1GB | WARNING |
| Nessun msg inbound 24h+ | silenzio prolungato | INFO |
| Deploy age | release > 7 giorni | INFO |

### 5.2 Implementazione
Il daemon gia' ha `setInterval` ogni 30 min per lo scheduler.
Aggiungere un health check parallelo che:
1. Testa DB (`PRAGMA integrity_check`)
2. Testa LLM (1 token a Gemini)
3. Verifica WA connection (`client.getState()`)
4. Se qualcosa fallisce → Telegram alert immediato

---

## 6. TEST E2E — AUTOMATICO, SENZA INTERVENTO UMANO

### 6.1 Strategia
Il daemon accetta un flag `dry_run` sull'endpoint `/send`:
- `dry_run: true` → non invia su WA ma persiste nel DB e ritorna `{"status": "sent", "dry_run": true}`
- Permette di testare tutta la catena senza messaggi reali

### 6.2 Test suite
```
test_e2e.py:
  [1] Daemon status                → GET /status
  [2] Dealer in pipeline           → SELECT conversations
  [3] Send testo (dry_run)         → POST /send {dry_run: true}
  [4] Send PDF (dry_run)           → POST /send {pdf, dry_run: true}
  [5] Analyzer CURIOSITY           → python3 response-analyzer.py --dry-run
  [6] Analyzer VEHICLE_REQUEST     → python3 response-analyzer.py --dry-run
  [7] Analyzer OBJECTION           → python3 response-analyzer.py --dry-run
  [8] Analyzer INTEREST            → python3 response-analyzer.py --dry-run
  [9] Pipeline scrape→cove→pdf     → on_demand_runner.py --limit 10
  [10] Quality check risposta      → nessuna parola banned, max 5 righe, firma Luca
```

### 6.3 Quality check risposte LLM (senza secondo LLM)
```python
BANNED = ["algoritmo", "piattaforma", "pipeline", "ROI", "CoVe", "Claude", "AI"]
assert len(reply) < 500                    # max lunghezza WA
assert len(reply.split('\n')) <= 5         # max 5 righe
assert not any(w in reply.lower() for w in BANNED)  # nessuna parola vietata
assert "?" in reply                        # deve finire con domanda chiusa
```

### 6.4 Regola
**Test DEVE passare PRIMA di ogni deploy e PRIMA di ogni outreach a dealer reali.**

---

## 7. FLUSSO E2E COMPLETO

```
DISCOVERY ──────── chi sono i dealer target?
    │               (92 in data/discovery_p2.json, da filtrare)
    ▼
PROFILING ──────── archetipo, score, tier
    │               (persona_type, score_fit, tier)
    ▼
MESSAGGIO ──────── personalizzato per archetipo
    │               (CHI-PERCHE'-CHIEDI per Day 1)
    ▼
INVIO WA ───────── via daemon API /send
    │               (anti-ban: 8-25s delay, typing, 30/day)
    ▼
RISPOSTA ───────── daemon riceve inbound
    │               (buffer 15s, poi analyzer)
    ▼
CLASSIFICAZIONE ── keyword + LLM cascade
    │
    ├─ CURIOSITY ────── rassicura (chi sei, come hai mio numero)
    ├─ VEHICLE_REQUEST ── estrai marca/modello/budget → PIPELINE
    ├─ INTEREST ──────── approfondisci (come funziona, fee)
    ├─ OBJECTION ─────── gestisci (ho gia' canali, troppo caro)
    └─ NEGATIVE ──────── exit gentile (non mi interessa)
                          │
                          ▼
                    PIPELINE (se VEHICLE_REQUEST)
                    scrape → CoVe → PDF → invio dossier
                          │
                          ▼
                    FEE TRACKING
                    (EUR 800-1200 a consegna)
```

---

## 8. ROADMAP IMPLEMENTATIVA

### Sprint 1: Infra solida (1 sessione)
**Obiettivo:** Un deploy che non rompe, un DB che non si corrompe, alert se qualcosa va storto.

- [ ] Unificare schema DB (merge conversations + dealers in una tabella coherente)
- [ ] Script migrazione DB (da stato attuale a schema unificato)
- [ ] `deploy/sync.sh` con rsync atomico
- [ ] `deploy/healthcheck.sh` post-deploy
- [ ] Backup DB automatico (cron 6h)
- [ ] Monitor base → Telegram alert (DB integrity, WA status, LLM health)
- [ ] Fix IP 192.168.1.12 → 192.168.1.2 ovunque

### Sprint 2: LLM resiliente (1 sessione)
**Obiettivo:** Il sistema risponde SEMPRE, qualunque provider sia down.

- [ ] Signup Groq (gratis, 2 min)
- [ ] Installare Ollama su iMac (`brew install ollama && ollama pull llama3.2:8b`)
- [ ] Implementare `src/llm_cascade.py` con circuit breaker
- [ ] Refactoring response-analyzer.py per usare cascade
- [ ] Health check LLM proattivo (mattina, alert se tutti down)
- [ ] Test: forzare fallimento provider 1-4, verificare che Ollama risponde

### Sprint 3: Orchestratore + Test E2E (1 sessione)
**Obiettivo:** Un CLI unico, test che passano senza intervento umano.

- [ ] `argos.py` CLI con subcommands
- [ ] `dry_run` mode sul daemon /send
- [ ] `--dry-run` mode su response-analyzer.py
- [ ] Test E2E completo (10 test, PASS/FAIL)
- [ ] Regola: deploy bloccato se test non passano

### Sprint 4: Dealer reali (solo se Sprint 1-3 green)
**Obiettivo:** Primo outreach con sistema automatico testato.

- [ ] Test E2E PASSA tutti i 10 test
- [ ] Outreach TIER1 (Enzo Car, Autoline, GP Cars) con Day 1 V3
- [ ] Monitoring attivo 24/7
- [ ] Day 3 automatico (scheduler + dossier)

### Sprint 5: Crescita
- [ ] Discovery automatico (92 dealer → filtro → profiling → priorita')
- [ ] CoVe match veicolo↔dealer (brand/fascia/zona)
- [ ] Programma affiliazione
- [ ] Scale 20+ dealer

---

## 9. COSA NON FARE MAI PIU'

1. **MAI** deploy con `scp` di singoli file → usa `deploy/sync.sh`
2. **MAI** testare mandando messaggi dal telefono → usa `python3 argos.py test`
3. **MAI** avere DB diversi su macchine diverse → un DB, un schema
4. **MAI** mandare a dealer reali senza test E2E green
5. **MAI** aggiungere script `send_dayN_tierX.py` → tutto passa dall'orchestratore
6. **MAI** ignorare errori LLM/DB → monitoring con alert Telegram
7. **MAI** `cp` su file SQLite → solo `sqlite3 .backup`
8. **MAI** cancellare `-wal`/`-shm` con processi aperti

---

## 10. DECISIONI APERTE PER IL FOUNDER

1. **Budget LLM**: full-free (Gemini+Groq+Ollama = 3250/day) oppure $5-10 OpenRouter per Haiku?
   - Raccomandazione: full-free. 3250/day e' 30x il fabbisogno. Ollama non fallisce mai.

2. **iMac**: e' Apple Silicon o Intel?
   - Se Intel: Ollama sara' lento (5-10 tok/s) ma funziona come ultimo fallback
   - Se Apple Silicon: Ollama sara' veloce (30-50 tok/s), quasi come cloud

3. **Facebook**: ricorso o nuovo account con SIM secondaria?

4. **Dashboard**: app.py esiste ma non e' in PM2. Serve? Deprecare?
