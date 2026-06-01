# CURRENT STATE 01 — Technical

Documento estratto dai file del repository. Nessuna ricostruzione da memoria.
Generato: 2026-04-17 (revisione S133.1 — rimosse sezioni fuori scope).

Divergenze note (verificare con Luke):
- `BUSINESS_HOURS.end`: file vivo = 22 (S116, esteso per test E2E); memoria interna citava 20.
- Skill `wa-daemon-ops/SKILL.md:22` cita `$WA_API_KEY`; produzione usa `ARGOS_API_KEY`.
- Skill `scraper-ops/SKILL.md:47` dice `sleep(15)`; `tools/scrapers/config.py` usa `rate_limit_min_s=3.0–6.0`.

---

## Sezione A — Parametri numerici immutabili

### A.1 CoVe Engine — scoring e soglie

| Parametro | Valore | Fonte |
|---|---|---|
| UNCERTAINTY_LAMBDA (Si = μ − λ·σ) | 0.25 | src/cove/cove_params_calibrated.py:34 |
| UNCERTAINTY_LAMBDA_RANGE | (0.20, 0.30) | src/cove/cove_params_calibrated.py:37 |
| UNCERTAINTY_LAMBDA_CI95 | (0.22, 0.28) | src/cove/cove_params_calibrated.py:38 |
| WEIGHT [PRICE/KM/AGE/HISTORY] | 0.40 / 0.30 / 0.20 / 0.10 | src/cove/cove_params_calibrated.py:53-56 |
| WEIGHT_SIGMA [PRICE/KM/AGE/HISTORY] | 0.08 / 0.12 / 0.05 / 0.35 | src/cove/cove_params_calibrated.py:72-75 |
| PRICE_DECAY_ALPHA [BMW/MB/Audi/DEFAULT] | 0.142 / 0.128 / 0.135 / 0.140 | src/cove/cove_params_calibrated.py:91-94 |
| PRICE_DECAY_ALPHA_SIGMA [BMW/MB/Audi/DEFAULT] | 0.018 / 0.015 / 0.017 / 0.020 | src/cove/cove_params_calibrated.py:99-102 |
| DEALER_PREMIUM_THRESHOLD | 0.75 | src/cove/cove_params_calibrated.py:148 |
| VIN_CHECK_THRESHOLD | 0.60 | src/cove/cove_params_calibrated.py:151 |
| SCORE_RANGES [REJECTED/VIN_CHECK/PROCEED_LOW/PROCEED] | (0,.40) / (.40,.60) / (.60,.75) / (.75,1.0) | src/cove/cove_params_calibrated.py:155-158 |
| CONFIDENCE_MULTIPLIERS [HIGH(σ<0.15)/MED([.15,.30])/LOW(>.30)] | 1.0 / 0.95 / 0.90 | src/cove/cove_params_calibrated.py:170-172 |
| TIER_MULTIPLIERS [TIER1/TIER2/SKIP] | 1.0 / 0.90 / 0.0 | src/cove/cove_params_calibrated.py:178-180 |

Formule derivate:
- `price_mu = initial_price × exp(-alpha × age_years)` (src/cove/cove_params_calibrated.py:130)
- `price_sigma = price_mu × age_years × alpha_sigma` (src/cove/cove_params_calibrated.py:134)

### A.2 Scraper — rate limit e veicoli

| Parametro | Valore | Fonte |
|---|---|---|
| YEAR_MIN | 2018 | tools/scrapers/config.py:74 |
| YEAR_MAX | 2025 | tools/scrapers/config.py:75 |
| KM_LIMITS[STANDARD] | 80.000 | tools/scrapers/config.py:68 |
| KM_LIMITS[SUV] | 100.000 | tools/scrapers/config.py:69 |
| KM_LIMITS[SUPERCAR] | 30.000 | tools/scrapers/config.py:70 |
| PortalConfig.results_per_page (default) | 20 | tools/scrapers/config.py:98 |
| PortalConfig.max_pages (default) | 10 | tools/scrapers/config.py:99 |
| PortalConfig.rate_limit_min_s (default) | 3.0 | tools/scrapers/config.py:100 |
| PortalConfig.rate_limit_max_s (default) | 8.0 | tools/scrapers/config.py:101 |
| PortalConfig.rate_limit_burst_pause_s (default) | 30.0 | tools/scrapers/config.py:102 |
| PortalConfig.burst_size (default) | 5 | tools/scrapers/config.py:103 |
| PortalConfig.daily_request_cap (default) | 2000 | tools/scrapers/config.py:104 |
| autoscout24_* min/max sleep | 4.0 / 10.0 s | tools/scrapers/config.py:115-116 |
| autoscout24_se max_pages / sleep | 8 / 5.0-12.0 s | tools/scrapers/config.py:159-161 |
| mobile_de min/max sleep | 5.0 / 12.0 s | tools/scrapers/config.py:178-179 |
| mobile_de burst_size / pause | 3 / 45.0 s | tools/scrapers/config.py:180-181 |
| willhaben_at sleep | 4.0 / 10.0 s | tools/scrapers/config.py:189-190 |
| leboncoin_fr sleep | 6.0 / 15.0 s | tools/scrapers/config.py:198-199 |
| leboncoin_fr burst_size / pause / cap | 3 / 60.0 s / 1000 | tools/scrapers/config.py:200-202 |
| PRICE_DROP_ALERT_PCT | 5.0 | tools/scrapers/config.py:217 |
| DEAL_ALERT_BELOW_MARKET_PCT | 8.0 | tools/scrapers/config.py:218 |
| NEW_LISTING_HOURS | 24 | tools/scrapers/config.py:219 |
| scrape_cron | `0 5 * * 1-5` (05:00 lun-ven) | tools/scrapers/config.py:211 |
| digest_cron | `0 8 * * 1-5` (08:00 lun-ven) | tools/scrapers/config.py:212 |
| timezone | Europe/Rome | tools/scrapers/config.py:213 |
| Skill scraper-ops: sleep tra richieste | 15 s | .claude/skills/scraper-ops/SKILL.md:47 |
| Skill scraper-ops: Semaphore | 5 | .claude/skills/scraper-ops/SKILL.md:48 |
| Skill scraper-ops: DAILY_LIMIT | 30 | .claude/skills/scraper-ops/SKILL.md:49 |

### A.3 Dealer discovery — commission scoring

| Parametro | Valore | Fonte |
|---|---|---|
| few_listings_min | 3 | tools/dealer_discovery/config.py:98 |
| few_listings_max | 15 | tools/dealer_discovery/config.py:99 |
| brand_diversity_min | 4 | tools/dealer_discovery/config.py:100 |
| keyword_match_weight | 3.0 | tools/dealer_discovery/config.py:101 |
| few_listings_weight | 2.0 | tools/dealer_discovery/config.py:102 |
| brand_diversity_weight | 2.0 | tools/dealer_discovery/config.py:103 |
| premium_presence_weight | 1.5 | tools/dealer_discovery/config.py:104 |
| low_reviews_weight | 1.0 | tools/dealer_discovery/config.py:105 |
| threshold_commission | 5.0 | tools/dealer_discovery/config.py:106 |
| threshold_fit_argos | 7.0 | tools/dealer_discovery/config.py:107 |
| RATE_LIMIT subito_delay | 5-12 s | tools/dealer_discovery/config.py:112-113 |
| RATE_LIMIT as24_delay | 5-10 s | tools/dealer_discovery/config.py:114-115 |
| RATE_LIMIT gmaps_delay | 8-18 s | tools/dealer_discovery/config.py:116-117 |

### A.4 WA daemon — anti-ban / quote

| Parametro | Valore | Fonte |
|---|---|---|
| DAILY_LIMIT (CONFIG) | 30 | wa-intelligence/wa-daemon.js:45 |
| Warm-up daily limit week ≤1 | 10 | wa-intelligence/wa-daemon.js:94 |
| Warm-up daily limit week ≤3 | 15 | wa-intelligence/wa-daemon.js:95 |
| Warm-up daily limit max | 20 | wa-intelligence/wa-daemon.js:96 |
| MAX_REPLIES_PER_DEALER | 10 | wa-intelligence/wa-daemon.js:334 |
| DEBOUNCE_MS (buffer inbound) | 15000 | wa-intelligence/wa-daemon.js:449 |
| HARD_CAP_MS | 45000 | wa-intelligence/wa-daemon.js:450 |
| SCHEDULER_INTERVAL | 30 * 60 * 1000 (30 min) | wa-intelligence/wa-daemon.js:48 |
| SQLite DB timeout | 10000 ms | wa-intelligence/wa-daemon.js:160 |
| busy_timeout pragma | 10000 | wa-intelligence/wa-daemon.js:162 |
| Long pause ogni N msg | 5 | wa-intelligence/wa-daemon.js:913 |
| Long pause range | 300000–600000 ms (5–10 min) | wa-intelligence/wa-daemon.js:914 |
| HumanLike typing min | 2000 ms | wa-intelligence/wa-daemon.js:467 |
| HumanLike typing factor | messageLength * 50 + rand*1500 | wa-intelligence/wa-daemon.js:467 |
| HumanLike typing max | 10000 ms | wa-intelligence/wa-daemon.js:467 |
| Inter-delay multi-msg | logNormalDelay(5000, 1500) | wa-intelligence/wa-daemon.js:1044 |
| Scheduler sleep | logNormalDelay(300000, 90000) | wa-intelligence/wa-daemon.js:1370,1448 |
| logNormalDelay min clamp | 2000 ms | wa-intelligence/wa-daemon.js:461 |
| logNormalDelay max clamp | meanMs * 3 | wa-intelligence/wa-daemon.js:461 |
| Message length max | 4096 char | wa-intelligence/wa-daemon.js:829 |
| Phone regex valido | `^(39)?3\d{8,9}$` | wa-intelligence/wa-daemon.js:824 |

### A.5 Time context — business hours

| Parametro | Valore | Fonte |
|---|---|---|
| TIMEZONE | Europe/Rome | wa-intelligence/time-context.js:12 |
| BUSINESS_HOURS.start | 8 | wa-intelligence/time-context.js:15 |
| BUSINESS_HOURS.end | 22 | wa-intelligence/time-context.js:15 |
| WARNING_HOURS_BEFORE | 2 | wa-intelligence/time-context.js:18 |
| CRITICAL_HOURS_BEFORE | 0.5 | wa-intelligence/time-context.js:19 |
| STEP_MAP WA_DAY1_SENT → EMAIL_DAY7 | 7 giorni | wa-intelligence/time-context.js:113 |
| STEP_MAP EMAIL_DAY7_SENT → WA_DAY12 | 5 giorni | wa-intelligence/time-context.js:114 |
| STEP_MAP WA_DAY12_SENT → CLOSED_TIMEOUT | 7 giorni | wa-intelligence/time-context.js:115 |
| Domenica | chiuso totale | wa-intelligence/time-context.js:82 |

### A.6 Dashboard — deadline mapping

| Parametro | Valore | Fonte |
|---|---|---|
| days_map DAY1_SENT | 3 | wa-intelligence/dashboard/db.py:390 |
| days_map DAY3_SENT | 4 | wa-intelligence/dashboard/db.py:390 |
| days_map DAY7_VOICE_SENT | 7 | wa-intelligence/dashboard/db.py:390 |
| days_map DAY7_SENT | 7 | wa-intelligence/dashboard/db.py:390 |
| KPI due_soon window | 24 h | wa-intelligence/dashboard/db.py:405 |

### A.7 Comunicazione Day 1
- Max righe WhatsApp Day 1: **5** (.claude/rules/communication.md:4)

---

## Sezione B — Schema dati

### B.1 DuckDB `cove_tracker.duckdb`

**Tabella `cove_results`** (src/cove/cove_engine_v4.py:469-489)
```
listing_id        VARCHAR
make              VARCHAR
model             VARCHAR
year              INTEGER
km                INTEGER        -- MAI mileage (.claude/rules/cove.md)
price             DOUBLE
vin               VARCHAR
source            VARCHAR
status            VARCHAR
confidence        DOUBLE
uncertainty       DOUBLE
fraud_overall     VARCHAR
market_price      DOUBLE
price_delta       DOUBLE
recommendation    VARCHAR        -- MAI verdict
actual_outcome    VARCHAR DEFAULT NULL
analyzed_at       TIMESTAMP      -- MAI created_at
PRIMARY KEY (listing_id, analyzed_at)
```

**Tabella `vehicle_listings`** (src/cove/db_schema.py:24-43 + pipeline_orchestrator.py:731-741)
```
listing_id            VARCHAR PRIMARY KEY
vin                   VARCHAR
make                  VARCHAR
model                 VARCHAR
year                  INTEGER
mileage               INTEGER     -- NOTA: qui la colonna è `mileage`
price_eu              DOUBLE
price_it_estimate     DOUBLE
source                VARCHAR
url                   VARCHAR
detail_url            VARCHAR
scraped_at            TIMESTAMP DEFAULT NOW()
fuel_type             VARCHAR
transmission          VARCHAR
power_kw              INTEGER
color                 VARCHAR
image_count           INTEGER DEFAULT 0
-- aggiunte da pipeline_orchestrator.setup_pipeline_schema():
pipeline_state        VARCHAR DEFAULT 'DISCOVERED'
state_updated_at      TIMESTAMP
seller_contact_sent_at TIMESTAMP
seller_followup_count INTEGER DEFAULT 0
seller_name           VARCHAR
seller_email          VARCHAR
seller_phone          VARCHAR
matched_dealer        VARCHAR
dossier_path          VARCHAR
```

**Tabella `vehicle_images`** (src/cove/db_schema.py:46-53)
```
id          INTEGER PRIMARY KEY DEFAULT nextval('vehicle_images_id_seq')
listing_id  VARCHAR NOT NULL
image_url   VARCHAR NOT NULL
image_type  VARCHAR DEFAULT 'listing'
downloaded  BOOLEAN DEFAULT FALSE
local_path  VARCHAR
```

**Tabella `cove_verifications`** (src/cove/cove_tracker.py:66-74)
```
listing_id        VARCHAR PRIMARY KEY
had_vin           BOOLEAN NOT NULL
confidence_score  DOUBLE NOT NULL
dealer_accepted   BOOLEAN DEFAULT FALSE
fraud_flags       INTEGER DEFAULT 0
ts                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
Indici: `idx_cove_had_vin`, `idx_cove_dealer_accepted`.

**Tabella `pipeline_log`** (src/cove/pipeline_orchestrator.py:754-763)
```
id            INTEGER
listing_id    VARCHAR NOT NULL
from_state    VARCHAR
to_state      VARCHAR NOT NULL
action        VARCHAR NOT NULL
details       VARCHAR
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```
Sequenza: `pipeline_log_seq`.

**View `calibration_report`** (src/cove/cove_engine_v4.py:505-516) — aggregata su `cove_results`.

### B.2 SQLite `dealer_network.sqlite`

**Tabella `conversations`** (wa-intelligence/wa-daemon.js:200-216)
```
dealer_id       TEXT PRIMARY KEY
dealer_name     TEXT
city            TEXT
phone_number    TEXT
stock_size      INTEGER
persona_type    TEXT
score           REAL
source          TEXT
notes           TEXT
current_step    TEXT DEFAULT 'PENDING'
day1_message    TEXT
recommendation  TEXT DEFAULT 'PENDING'
created_at      TEXT DEFAULT (datetime('now'))
last_contact_at TEXT
analyzed_at     TEXT
```
Colonne aggiunte via ALTER (usate da query, non in CREATE):
`outbound_count`, `inbound_count` (wa-intelligence/dashboard/db.py:375-379).

**Tabella `messages`** (wa-intelligence/wa-daemon.js:217-229)
```
id              TEXT PRIMARY KEY
dealer_id       TEXT
dealer_name     TEXT
phone_number    TEXT           -- con suffisso '@c.us' per WA
direction       TEXT           -- 'INBOUND' | 'OUTBOUND'
body            TEXT
timestamp_it    TEXT
timestamp_iso   TEXT
wa_msg_id       TEXT
processed       INTEGER DEFAULT 0
created_at      TEXT DEFAULT (datetime('now'))
```

**Tabella `pending_replies`** (wa-intelligence/wa-daemon.js:230-242)
```
id                TEXT PRIMARY KEY
dealer_id         TEXT
dealer_name       TEXT
inbound_msg_id    TEXT
reply_text        TEXT
reply_label       TEXT
cialdini_trigger  TEXT
approved          INTEGER DEFAULT NULL
sent              INTEGER DEFAULT 0
scheduled_at      TEXT
created_at        TEXT DEFAULT (datetime('now'))
```

**Tabella `scheduled_actions`** (wa-intelligence/wa-daemon.js:243-252)
```
id            TEXT PRIMARY KEY
dealer_id     TEXT
dealer_name   TEXT
action_type   TEXT
due_at        TEXT
status        TEXT DEFAULT 'PENDING'
fired_at      TEXT
created_at    TEXT DEFAULT (datetime('now'))
```

**Tabella `audit_log`** (wa-intelligence/wa-daemon.js:253-260)
```
id            TEXT PRIMARY KEY
event_type    TEXT
dealer_id     TEXT
payload       TEXT
timestamp_it  TEXT
created_at    TEXT DEFAULT (datetime('now'))
```

**Tabella `agent_state`** (wa-intelligence/wa-daemon.js:56-61)
```
key         TEXT PRIMARY KEY
value       TEXT NOT NULL
updated_at  TEXT DEFAULT (datetime('now'))
```
Chiavi seed: `status` ('active'), `pause_until` ('0'), `account_start_date` (ISO date).

**Tabella `daily_stats`** (wa-intelligence/wa-daemon.js:63-72)
```
date           TEXT PRIMARY KEY
sent           INTEGER DEFAULT 0
delivered      INTEGER DEFAULT 0
read_count     INTEGER DEFAULT 0
replied        INTEGER DEFAULT 0
failed         INTEGER DEFAULT 0
blocked        INTEGER DEFAULT 0
new_contacts   INTEGER DEFAULT 0
```

**Tabella `llm_costs`** (wa-intelligence/dashboard/db.py:71-76)
```
id          INTEGER PRIMARY KEY AUTOINCREMENT
model       TEXT
tokens      INTEGER
cost_usd    REAL
dealer_id   TEXT
purpose     TEXT
created_at  TEXT DEFAULT (datetime('now'))
```

**Tabella `training_corrections`** (wa-intelligence/telegram-handler.py:193-202)
```
id              TEXT PRIMARY KEY
reply_id        TEXT
dealer_id       TEXT
original_label  TEXT
original_text   TEXT
corrected_text  TEXT
created_at      TEXT DEFAULT (datetime('now'))
```

### B.3 Convenzioni naming (`.claude/rules/cove.md`)
- `recommendation` (MAI `verdict`)
- `analyzed_at` (MAI `created_at`)
- `confidence` in [0.0, 1.0]
- `km` su `cove_results` (NON `mileage`)
- `mileage` su `vehicle_listings` (collisione voluta — schema diverso)

---

## Sezione C — Path filesystem

### C.1 MacBook (working dir primaria)

| Path | Scopo | Fonte |
|---|---|---|
| `/Users/macbook/Documents/combaretrovamiauto-enterprise` | repo root | CLAUDE.md |
| `src/cove/data/cove_tracker.duckdb` | DuckDB CoVe (copia locale) | src/cove/cove_engine_v4.py:97, db_schema.py:184 |
| `dealer_network.sqlite` (root repo) | SQLite alternativa | tools/outreach_scheduler.py:22 |
| `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` | auto-memory | CLAUDE.md |

### C.2 iMac (server produzione)

| Path | Scopo | Fonte |
|---|---|---|
| SSH: `gianlucadistasi@192.168.1.2` | accesso iMac | .claude/rules/identity.md |
| `/Users/gianlucadistasi/Documents/app-antigravity-auto/` | project root iMac | wa-intelligence/wa-daemon.js:37 |
| `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite` | SQLite produzione (DB_PATH default) | wa-intelligence/wa-daemon.js:37 |
| `~/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb` | DuckDB CoVe (read in analyzer) | wa-intelligence/response-analyzer.py:361 |
| `/tmp/argos-wa-daemon.log` | LOG_FILE daemon | wa-intelligence/wa-daemon.js:47 |
| `/tmp/argos-analyzer.log` | analyzer log | wa-intelligence/wa-daemon.js:367 |

### C.3 File critici (path relativi repo)

| Path | Ruolo | Fonte |
|---|---|---|
| `src/cove/cove_engine_v4.py` | CoVe engine — NON modificare | .claude/rules/cove.md:8 |
| `src/cove/cove_params_calibrated.py` | parametri CoVe | — |
| `src/cove/db_schema.py` | schema vehicle_listings/images | — |
| `src/cove/pipeline_orchestrator.py` | pipeline state machine | — |
| `src/cove/fraud_flags.py` | fraud detection | CLAUDE.md identity |
| `tools/scrapers/autoscout_scraper.py` | scraper principale + MODEL_SLUG | CLAUDE.md |
| `tools/scrapers/config.py` | portali + rate limits | — |
| `tools/on_demand_runner.py` | runner on-demand | CLAUDE.md |
| `tools/fee_calculator.py` | calcolo fee | .claude/rules/identity.md |
| `tools/scripts/pdf_generator_enterprise.py` | PDF dossier | .claude/rules/identity.md |
| `tools/dealer_discovery/config.py` | target province IT + scoring commission | — |
| `wa-intelligence/wa-daemon.js` | WA daemon (PM2: wa-daemon) | — |
| `wa-intelligence/dashboard/app.py` | dashboard FastAPI | — |
| `wa-intelligence/response-analyzer.py` | LLM response analyzer | — |
| `wa-intelligence/time-context.js` | business hours + deadline | — |
| `wa-intelligence/outbound_guard.py` | pre-send validation | wa-daemon.js:40 |
| `wa-intelligence/post_send_update.py` | state transition post-send | wa-daemon.js:41 |
| `CURRENT_SPRINT.md` | task correnti (root) | CLAUDE.md |
| `BACKLOG.md` | problemi parcheggiati | CLAUDE.md |

### C.4 Reference files

| Path | Fonte |
|---|---|
| `research/S73_MASTER_REFERENCE.md` | .claude/rules/identity.md |
| `research/s98_ARCHITETTURA_DEFINITIVA.md` | .claude/rules/identity.md |
| `research/s94_MESSAGGI_DEFINITIVI_V3.md` | .claude/rules/identity.md |

---

## Sezione D — Endpoint e integrazioni

### D.1 WA daemon (iMac, porta 9191)

Bind: `0.0.0.0:9191` (wa-intelligence/wa-daemon.js:1255).
Auth: header `X-API-Key` su tutti i metodi tranne `GET /` e `GET /status` (wa-daemon.js:755).

| Metodo | Path | Scopo | Fonte |
|---|---|---|---|
| GET | `/` | health check | wa-daemon.js:1236 |
| GET | `/status` | health JSON (uptime, daily_sent, wa_status) | wa-daemon.js:1236 |
| GET | `/qr` | QR HTML (auto-refresh 20s) | wa-daemon.js:765 |
| GET | `/qr?format=json` | QR state JSON | wa-daemon.js:766 |
| POST | `/send` | invia singolo (`{phone, message, dealer_id, template_id, dry_run}`) | wa-daemon.js:811 |
| POST | `/send-multi` | invia 2-3 msg con typing delay | wa-daemon.js:968 |
| POST | `/send-voice` | invia voice note | wa-daemon.js:1077 |
| POST | `/send-doc` | invia documento/immagine | wa-daemon.js:1128 |
| POST | `/pause` | pausa agent | wa-daemon.js:1188 |
| POST | `/resume` | resume agent | wa-daemon.js:1199 |
| GET | `/health-metrics` | stats giornaliere + block rate | wa-daemon.js:1211 |

Validazione `/send`:
- phone regex: `^(39)?3\d{8,9}$` (wa-daemon.js:824)
- message max length: 4096 char (wa-daemon.js:829)

### D.2 Dashboard (iMac, porta 8080)

Bind: `port=8080` (wa-intelligence/run_dashboard.py:23, uvicorn).
PM2 process: `argos-dashboard` (.claude/rules/identity.md).
Auth: password su login (wa-intelligence/dashboard/auth.py).

### D.3 API esterne LLM (wa-intelligence/response-analyzer.py:53-61)

| Provider | Model | URL | Env var | Docs |
|---|---|---|---|---|
| OpenRouter | `anthropic/claude-haiku-4-5` | `https://openrouter.ai/api/v1/chat/completions` | `OPENROUTER_API_KEY` | https://openrouter.ai/docs |
| Google Gemini | `gemini-2.5-flash` | `https://generativelanguage.googleapis.com/v1beta/models` | `GOOGLE_AI_API_KEY` | https://ai.google.dev/docs |
| Groq | `llama-3.3-70b-versatile` | `https://api.groq.com/openai/v1/chat/completions` | `GROQ_API_KEY` | https://console.groq.com/docs |

### D.4 Portali scraper (tools/scrapers/config.py:108-204)

| Portal key | Name | Base URL | Country |
|---|---|---|---|
| autoscout24_de | AutoScout24 DE | https://www.autoscout24.de | DE |
| autoscout24_nl | AutoScout24 NL | https://www.autoscout24.nl | NL |
| autoscout24_be | AutoScout24 BE | https://www.autoscout24.be | BE |
| autoscout24_at | AutoScout24 AT | https://www.autoscout24.at | AT |
| autoscout24_fr | AutoScout24 FR | https://www.autoscout24.fr | FR |
| autoscout24_se | AutoScout24 SE | https://www.autoscout24.se | SE |
| autoscout24_it | AutoScout24 IT | https://www.autoscout24.it | IT |
| mobile_de | mobile.de | https://suchen.mobile.de | DE |
| willhaben_at | willhaben.at | https://www.willhaben.at | AT |
| leboncoin_fr | leboncoin.fr | https://www.leboncoin.fr | FR |

URL builder patterns suffix per portale (src/cove/db_schema.py:65-93):
`autoscout24_de:/angebote/{hash}` · `_nl:/aanbod/{hash}` · `_fr:/annonces/{hash}` · `_it:/annunci/{hash}` · `otomoto_pl:/osobowe/oferta/{id}` · `finn_no:/car/used/ad.html?finnkode={hash}`

### D.5 Integrazioni interne

| Servizio | Modalità | Fonte |
|---|---|---|
| Telegram bot | script `telegram-handler.py`, chiamato da daemon via spawn | wa-intelligence/wa-daemon.js:38,398 |
| Landing page | https://argos-automotive.pages.dev (Cloudflare Pages) | .claude/rules/identity.md |
| WA Business (produzione) | 3281536308 | .claude/rules/identity.md |

### D.6 Numeri telefono di test

| Numero | Ruolo | Fonte |
|---|---|---|
| 393314928901 | TEST_FOUNDER (unico autorizzato per test) | .claude/skills/wa-daemon-ops/SKILL.md:32,59; CLAUDE.md |

### D.7 Env vars (presenti nel codice)

| Env var | Scopo | Fonte |
|---|---|---|
| `ARGOS_API_KEY` | auth daemon porta 9191 | wa-daemon.js:748 |
| `WA_CLIENT_ID` | SESSION_ID (default `argos-business`) | wa-daemon.js:35 |
| `DB_PATH` | override SQLite path | wa-daemon.js:36 |
| `ARGOS_DB_PATH` | override SQLite dashboard | wa-intelligence/dashboard/db.py:15 |
| `OPENROUTER_API_KEY` | LLM fallback | response-analyzer.py:53 |
| `OPENROUTER_MODEL` | default `anthropic/claude-haiku-4-5` | response-analyzer.py:54 |
| `GOOGLE_AI_API_KEY` | Gemini | response-analyzer.py |
| `GROQ_API_KEY` | Groq | response-analyzer.py:59 |
