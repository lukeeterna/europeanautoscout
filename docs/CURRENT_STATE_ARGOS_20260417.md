# CURRENT_STATE_ARGOS — 2026-04-17

Snapshot completo dello stato di ARGOS Automotive al termine di S132.
Documento statico destinato ad handoff esterno / consolidamento. Non sintetizzato.

Working dir MacBook: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
Working dir iMac: `/Users/gianlucadistasi/Documents/app-antigravity-auto`
Branch: `master` | Ultimo commit: `96c3865 fix(S132): scraper slug -(alle) + seller_name nel DB`

---

## SEZIONE 1 — Parametri tecnici immutabili

### 1.1 CoVe Engine v4 (`src/cove/cove_engine_v4.py` — NON MODIFICARE)

Soglie di decisione:
- `DEALER_PREMIUM_THRESHOLD = 0.75` — confidence minima per proporre a dealer premium
- `VIN_CHECK_THRESHOLD = 0.60` — sotto questa soglia, PROCEED solo con VIN check superato
- `UNCERTAINTY_LAMBDA = 0.25` — fallback per `Si = μ − λ·σ`
- `VIN_TRIGGER_KM_ANNO = 4_500` — km/anno sotto il quale scatta il VIN check (KBA 10° percentile)

Lambda adattivo (penalità incertezza Bayesian):
- `price < €20.000` → λ = 0.20 (budget)
- `€20.000 ≤ price < €40.000` → λ = 0.25 (standard)
- `price ≥ €40.000` → λ = 0.40 (premium, penalità massima)

Pesi score components (calibrati DeepResearch 2026):
- `WEIGHT_PRICE = 0.35` (↓ da 0.40)
- `WEIGHT_KM = 0.25` (↓ da 0.30)
- `WEIGHT_AGE = 0.20` (invariato)
- `WEIGHT_HISTORY = 0.20` (↑ da 0.10 — RADDOPPIATO, odometer fraud principale rischio)

Soglie km/anno (KBA 2023):
- `VERY_LOW = 6_000`
- `NORMAL_LO = 10_000`
- `NORMAL_HI = 20_000`
- `ELEVATED = 28_000`
- `HIGH = 40_000`
- `ANOMALY = 55_000`

Segmento anno target: `MIN_Y = 2018`, `MAX_Y = 2023` (fuori range → rifiutato).

Formula scoring Bayesian: `Si = μ − λ·σ` — Frontiers AI 2026.
Metodologia CoVe: FACTORED method (Dhuliawala et al., ACL 2024).
CoVe Tags: `[VERIFIED]` / `[ESTIMATED]` / `[UNKNOWN]` / `[SUSPICIOUS]`.

### 1.2 Scraper — rate limits

File: `tools/scrapers/config.py`
- Limiti anno target: `YEAR_MIN = 2018`, `YEAR_MAX = 2025`
- Limiti km per categoria:
  - `STANDARD = 80.000 km`
  - `SUV = 100.000 km`
  - `SUPERCAR = 30.000 km`
- Default portali: `results_per_page = 20`, `max_pages = 10`, `burst_size = 5`, `daily_request_cap = 2.000 req`
- `rate_limit_min_s` / `rate_limit_max_s`: 3-15s (jitter, per portale)
- `rate_limit_burst_pause_s`: 30-45s (pausa dopo burst)
- Override per portale: `mobile.de` e `leboncoin.fr` hanno burst_size ridotto (3) e pause lunghe; `SE` ha rate 5-12s

Skill scraper-ops — regole immutabili:
- `sleep(15)` tra richieste — non ridurre
- `Semaphore(5)` — non aumentare
- `DAILY_LIMIT = 30` scraping — non aumentare senza approvazione
- User-Agent sempre Mozilla/5.0 realistico
- Solo dati strutturati, MAI CSS selectors fragili

### 1.3 WhatsApp daemon — anti-ban

File: `wa-intelligence/wa-daemon.js`
- `CONFIG.DAILY_LIMIT = 30` (hard cap costante)
- `MAX_REPLIES_PER_DEALER = 10` al giorno
- `SCHEDULER_INTERVAL = 30 min`
- `max_memory_restart = 512M` (wa-daemon) / `128M` (tg-bot)

Warm-up dinamico (`getDailyLimit()`):
- week_age ≤ 1 → 10 msg/giorno
- week_age ≤ 3 → 15 msg/giorno
- week_age > 3 → 20 msg/giorno (never > 20 per API non ufficiale)

Long pause anti-bot (S117): pausa random 5-10 min ogni 5 messaggi inviati.

Delay human-like (`HumanLike`):
- `logNormalDelay`: lognormale `exp(ln(mean) + z·(std/mean))`, clamp `[2s, 3·mean]`
- `simulateTyping`: `messageLength * 50 + random(0-1500)`ms, clamp `[2s, 10s]`
- `simulateRecording`: `duration_sec * 1000 * (0.8 + random*0.4)`, max 30s

Business hours (`wa-intelligence/time-context.js`):
- `BUSINESS_HOURS = { start: 8, end: 22 }` — S116 esteso temporaneamente a 22 per test E2E
- MEMORY.md registra `{start:8, end:20}` storicamente — check finestra al momento dell'invio
- `TIMEZONE = 'Europe/Rome'`
- Domenica: chiuso totale. Sabato mattina: attivo.
- `WARNING_HOURS_BEFORE = 2`, `CRITICAL_HOURS_BEFORE = 0.5`

Deadline step mapping:
- `WA_DAY1_SENT` → `EMAIL_DAY7` dopo 7 giorni calendario
- `EMAIL_DAY7_SENT` → `WA_DAY12` dopo 5 giorni
- `WA_DAY12_SENT` → `CLOSED_TIMEOUT` dopo 7 giorni

Message buffer (debounce multi-input):
- `DEBOUNCE_MS = 15000` (15s silence window)
- `HARD_CAP_MS = 45000` (45s max dal primo messaggio)

### 1.4 PM2 — policy restart

`wa-intelligence/ecosystem.config.js`:
- `argos-wa-daemon`: `max_restarts=10`, `min_uptime=30s`, `restart_delay=5000ms`, `kill_timeout=10s`
- `argos-tg-bot`: `max_restarts=20`, `min_uptime=10s`, `restart_delay=3000ms`
- `watch=false` (no hot reload in prod), `autorestart=true`

### 1.5 Fee calculator (`tools/fee_calculator.py`)

Tier 1 — Scouting Only: `€800-1200` (default €800)
Tier 2 — Import Basic: `€800-1200` (default €1000)
Tier 3 — Import Premium: `€1200-2000` (default €1500)

Margine dealer stimato per fascia prezzo:
- < €15.000 → 8%
- €15.000-30.000 → 10%
- €30.000-50.000 → 12%
- > €50.000 → 14%

Fattura Svantaggiosa (TD17/18/19) saving: `€150-200` range.

### 1.6 Altri parametri

- WAL mode + `busy_timeout = 10000` su SQLite (Node e Python)
- PRAGMA integrity_check ogni 5 min
- Heartbeat iMac ogni 30 min
- Backup DB ogni 6h via `sqlite3 .backup`
- Circuit breaker LLM: 3 fail in 5 min → skip provider
- Validator length cap: messaggio ≤ 4096 char
- Response analyzer LLM cap: output ≤ 1000 char (banned se oltre)

---

## SEZIONE 2 — Path, credenziali, endpoint

### 2.1 Working directories

- MacBook: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- iMac: `/Users/gianlucadistasi/Documents/app-antigravity-auto`
- Python 3.13 (entrambi), Node v20 (iMac)
- macOS 11 (MacBook)

### 2.2 Database

- SQLite (iMac): `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`
  - Copia locale MacBook: `dealer_network.sqlite` (schema divergente — market_listings vs conversations)
  - La copia in `wa-intelligence/` è vuota — NON usarla.
- DuckDB CoVe: `src/cove/data/cove_tracker.duckdb` (su iMac e MacBook)
- DuckDB NHTSA: `src/cove/data/nhtsa_wmi.duckdb`
- Memory: `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md`
- Snapshot MCP SQLite: `/tmp/argos_dashboard_snapshot.db`

### 2.3 Endpoint

- WA daemon: `http://192.168.1.2:9191` (iMac LAN)
  - `/status`, `/send`, `/send-multi`, `/send-voice`, `/send-doc`, `/pause`, `/resume`, `/health-metrics`
  - Auth: header `X-API-Key` (env var `ARGOS_API_KEY`)
- Dashboard ARGOS: `http://192.168.1.2:8080` (iMac LAN)
- Landing pubblica: `https://argos-automotive.pages.dev` (Cloudflare Pages)

### 2.4 Numeri telefono

- WA Business ARGOS (Luca Ferretti): `+39 328 153 6308` (`3281536308`)
- Telefono fisso VoIP: `0972 536 918` (EhiWeb)
- TEST_FOUNDER (unico numero autorizzato per test): `39<TEST_FOUNDER_NUM>`
- Telegram alerts chat: `ARGOS_TELEGRAM_CHAT_ID=931063621`

### 2.5 Email

- Persona: `ferretti.argosautomotive@gmail.com`

### 2.6 File critici

- CoVe engine: `src/cove/cove_engine_v4.py` — NON modificare
- Fraud flags: `src/cove/fraud_flags.py`
- Scrapers: `tools/scrapers/` (autoscout_scraper.py, mobile_de_scraper.py, base_scraper.py, config.py, portal_profiles.py, detail_enricher.py, market_intelligence.py, resilient_fetcher.py, trend_analyzer.py, ...)
- Fee calculator: `tools/fee_calculator.py`
- PDF generator: `tools/scripts/pdf_generator_enterprise.py`
- On-demand runner: `tools/on_demand_runner.py`
- Scraper→CoVe pipeline: `src/cove/scraper_cove_pipeline.py`
- Image sanitizer: `src/cove/image_sanitizer.py`
- Pipeline orchestrator: `src/cove/pipeline_orchestrator.py`
- VIN verification: `src/cove/vin_verification.py`, `src/cove/vincario_free_client.py`
- Market verifier: `src/cove/market_verifier_enterprise.py`
- WA daemon: `wa-intelligence/wa-daemon.js`
- Validator: `wa-intelligence/validator.py`
- Outbound guard: `wa-intelligence/outbound_guard.py`
- Post-send update: `wa-intelligence/post_send_update.py`
- State machine: `wa-intelligence/state_machine.py`
- Response analyzer: `wa-intelligence/response-analyzer.py`
- Templates engine: `wa-intelligence/templates.py`
- Dashboard: `wa-intelligence/dashboard/app.py`
- Time context: `wa-intelligence/time-context.js`
- PM2 ecosystem: `wa-intelligence/ecosystem.config.js`
- Scripts deploy: `wa-intelligence/deploy.sh`
- Backstory persona: `tools/backstory_luca_ferretti.md`
- CLAUDE.md + rules: `CLAUDE.md`, `.claude/rules/*.md`

### 2.7 API integrations (solo nomi — chiavi in `.env`, mai in chat/commit)

Env var presenti in `.env` (redacted):
- `WA_BUSINESS_NUMBER`, `WA_CLIENT_ID`
- `VOIP_NUMBER`, `VOIP_USERNAME`, `VOIP_PASSWORD`, `VOIP_SIP_SERVER`, `VOIP_SIP_PORT`, `VOIP_CODEC`
- `ARGOS_GMAIL`, `ARGOS_GMAIL_PWD`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`
- `GOOGLE_AI_API_KEY`
- `FACEBOOK_EMAIL`, `FACEBOOK_PWD`
- `LINKEDIN_EMAIL`, `LINKEDIN_PWD`
- `ARGOS_API_KEY` (header `X-API-Key` per /send daemon)
- `GROQ_API_KEY`, `OPENROUTER_API_KEY`
- `AUTODEV_API_KEY` (auto.dev)
- `OPENROUTER_MODEL` (default `anthropic/claude-haiku-4-5`)

Env var daemon iMac (`wa-intelligence/.env`):
- `ARGOS_DB_PATH`, `ARGOS_TELEGRAM_CHAT_ID`, `ARGOS_TELEGRAM_TOKEN`, `WA_CLIENT_ID`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `ARGOS_API_KEY`

LLM cascade 5 livelli (ordine):
1. Gemini (Google AI)
2. Groq
3. OpenRouter free tier
4. Gemini Lite
5. Ollama locale

### 2.8 Comandi operativi

- Test E2E: `python3 argos.py test`
- Deploy iMac: `bash deploy/sync.sh` (rsync atomico + symlink swap)
- Scrape on-demand: `python3 tools/on_demand_runner.py --marca BMW --budget 40000 --dealer "Nome"`
- Status daemon: `ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"`
- PM2 iMac: `ssh gianlucadistasi@192.168.1.2 "pm2 status"` / `pm2 logs wa-daemon --lines 50` / `pm2 restart wa-daemon`
- SSH iMac: `ssh gianlucadistasi@192.168.1.2`

---

## SEZIONE 3 — Schema dati

### 3.1 DuckDB `cove_tracker.duckdb`

Tabelle presenti: `cove_results`, `cove_verifications`, `dealer_automation_log`, `dealer_automation_sequences`, `dealer_contacts`, `dealer_prospect_scoring`, `email_outreach`, `events`, `market_checks`, `pipeline_log`, `vehicle_assignments`, `vehicle_data_locked`, `vehicle_images`, `vehicle_listings`, `calibration_report`.

#### `cove_results`
| Campo | Tipo | Note |
|---|---|---|
| listing_id | VARCHAR | PK, NOT NULL |
| make | VARCHAR | |
| model | VARCHAR | |
| year | INTEGER | |
| km | INTEGER | **NON `mileage`** |
| price | DOUBLE | |
| vin | VARCHAR | |
| source | VARCHAR | |
| status | VARCHAR | |
| confidence | DOUBLE | 0.0-1.0 |
| uncertainty | DOUBLE | |
| fraud_overall | VARCHAR | |
| market_price | DOUBLE | |
| price_delta | DOUBLE | |
| recommendation | VARCHAR | **NON `verdict`** — valori PROCEED / SKIP / VIN_CHECK |
| actual_outcome | VARCHAR | |
| analyzed_at | TIMESTAMP | **NON `created_at`**, NOT NULL |

#### `vehicle_listings` (DuckDB CoVe)
```
listing_id VARCHAR NOT NULL, vin, make, model, year, mileage, price_eu, price_it_estimate,
source, url, detail_url, scraped_at, fuel_type, transmission, power_kw, color,
image_count, pipeline_state, state_updated_at, seller_contact_sent_at, seller_followup_count,
seller_name, seller_email, seller_phone, matched_dealer, dossier_path,
vin_verified BOOLEAN, vin_verification_data, recall_count
```
Nota: in DuckDB CoVe il campo km si chiama `mileage`. In `cove_results` si chiama `km`. **Attenzione al naming divergente**.

#### `vehicle_images`
```
id INTEGER PK NOT NULL, listing_id NOT NULL, image_url NOT NULL,
image_type, downloaded BOOLEAN, local_path
```

#### `cove_verifications`
```
listing_id NOT NULL, had_vin BOOLEAN NOT NULL, confidence_score DOUBLE NOT NULL,
dealer_accepted BOOLEAN, fraud_flags INTEGER, ts TIMESTAMP
```

#### `market_checks`
```
check_id PK NOT NULL, listing_id, make, model, year, km, price_asked,
ref_price, ref_sigma, price_delta, n_comparable, sources_used,
market_depth, delta_conf, stolen_status, checked_at TIMESTAMP
```

#### `pipeline_log`
```
id, listing_id NOT NULL, from_state, to_state NOT NULL, action NOT NULL, details, created_at
```

#### `dealer_contacts`
```
contact_id PK, phone_number, contact_name, company, role, location, status, source,
first_contact, last_contact, conversion_stage, notes, dealer_type, brand_specialization,
inventory_size, target_region, whatsapp_opt_in BOOLEAN, gdpr_consent_date,
email_address, lead_score INT, automation_stage, last_automation_action,
top_dealers_source BOOLEAN
```

#### `dealer_prospect_scoring`
```
scoring_id PK, contact_id, company_score, engagement_score, conversion_probability,
priority_tier, last_score_update, scoring_factors JSON, automated_actions_enabled BOOLEAN
```

#### `vehicle_assignments`
```
assignment_id PK NOT NULL, contact_id NOT NULL, listing_id NOT NULL, make_model,
year, price_eur, km, argos_confidence, assignment_date, status,
response_received BOOLEAN, conversion_outcome
```

#### `vehicle_data_locked`
```
vehicle_id PK, km_verified, km_source, price_verified, price_source,
validation_status, locked_at, last_validated_at, modification_blocked BOOLEAN
```

#### `calibration_report` (view)
```
confidence_bucket, total, deals, actual_rate, avg_confidence
```

#### `email_outreach`, `events`, `dealer_automation_log`, `dealer_automation_sequences`
Schema completo in DuckDB (vedi query live); presenti per storico automation.

### 3.2 SQLite `dealer_network.sqlite` (iMac) — DB ufficiale outreach

Tabelle: `agent_state`, `audit_log`, `conversations`, `daily_stats`, `lia_log`, `llm_costs`, `messages`, `pending_replies`, `scheduled_actions`, `validation_log`.

#### `conversations`
```
dealer_id TEXT PK, dealer_name, city, phone_number, stock_size INTEGER, persona_type,
score REAL, source, notes, current_step, day1_message, recommendation,
created_at, last_contact_at, analyzed_at, conversation_state,
outbound_count INTEGER, inbound_count INTEGER, last_inbound_at, state_updated_at,
escalation_flag INTEGER, is_active_partner INTEGER, partner_since,
total_transactions INTEGER, total_revenue_dealer REAL, last_analytics_sent,
trusted_partner_sent INTEGER,
opt_out INTEGER, opt_out_at TIMESTAMP, opt_out_source, opt_out_raw_message
```

#### `messages`
```
id TEXT PK, dealer_id, dealer_name, phone_number (con suffisso @c.us), direction,
body, timestamp_it, timestamp_iso, wa_msg_id, processed INTEGER, created_at
```
Nota: colonna `phone_number` (non `phone`). Risposta dealer reale = query su `messages` con `direction='inbound'`, NON su `conversations.current_step`.

#### `agent_state`
```
key TEXT PK, value TEXT NOT NULL, updated_at
```
Chiavi presenti: `status` (active/paused), `pause_until` (timestamp ms), `account_start_date` (YYYY-MM-DD).

#### `daily_stats`
```
date TEXT PK, sent, delivered, read_count, replied, failed, blocked, new_contacts
```

#### `lia_log` — Legitimate Interest Assessment (GDPR)
```
id INTEGER PK, dealer_id NOT NULL, legal_basis, purpose, data_source,
data_source_date DATE, opt_out_mechanism_present INTEGER, ts TIMESTAMP
```

#### `validation_log`
```
id INTEGER PK, dealer_id NOT NULL, rule_id NOT NULL, decision NOT NULL,
motivation TEXT, message_hash TEXT, mode TEXT (shadow|canary|enforce), ts TIMESTAMP
```

#### `llm_costs`
```
id TEXT PK, dealer_id, model, input_tokens, output_tokens, total_tokens,
cost_usd REAL, created_at
```

#### `pending_replies`
```
id TEXT PK, dealer_id, dealer_name, inbound_msg_id, reply_text, reply_label,
cialdini_trigger, approved INTEGER, sent INTEGER, scheduled_at, created_at, msg_checksum
```

#### `scheduled_actions`, `audit_log`
Schema in chiaro in `wa-daemon.js:243` e `:253`.

### 3.3 SQLite `dealer_network.sqlite` locale MacBook — DB market intelligence divergente

**Attenzione**: la copia locale MacBook ha schema diverso — contiene `dealers`, `market_listings`, `market_daily_trends`, `market_insights`, `market_price_changes`, `market_scraper_runs`. NON è il DB outreach. Il DB autorevole per outreach è su iMac.

### 3.4 Convenzioni di naming (INVIOLABILI)

- `recommendation` (MAI `verdict`)
- `analyzed_at` (MAI `created_at` per CoVe)
- `confidence` range `0.0-1.0`
- `phone_number` in `messages`/`conversations` (NON `phone`)
- `km` in `cove_results` / `mileage` in `vehicle_listings` (DuckDB) — naming divergente documentato
- `direction` = `inbound` | `outbound`
- `current_step` valori noti: `PENDING`, `DAY1_SENT`, `DAY3_SENT`, `DAY7_SENT`, `WA_DAY1_SENT`, `WA_DAY12_SENT`, `EMAIL_DAY7_SENT`, `CLOSED_TIMEOUT`, `MANUAL_CHECK`

---

## SEZIONE 4 — Brand protection e regole messaggistica

### 4.1 Banned words — validator content rules

`FORBIDDEN_TERMS` (substring match, `response-analyzer.py:1178`):
```
carfax, cove engine, claude, anthropic, openai, chatgpt,
intelligenza artificiale, machine learning, algoritmo,
embedding, vincario, händlergarantie,
non possiamo fatturare, reimportazione, piattaforma
```

`FORBIDDEN_WORDS_EXACT` (word boundary):
```
cove, gpt, rag, bot, argos, llm, prompt, automatico
```

`_LLM_BANNED_WORDS` (generazione LLM, stringa `.lower()`):
```
cove, claude, anthropic, openai, gpt, llm,
algoritmo, machine learning, intelligenza artificiale,
bot, automatico, embedding, rag, prompt
```

### 4.2 Parole mai nel Day 1 (oltre banned words)

- "Germania", "estero", "import", "premium", "cerco auto", "opportunità"
- CTA vietate: "attendo riscontro", "posso inviarle"
- Emoji, link, allegati: vietati
- Presentazione oltre 1 riga: vietata

### 4.3 Terminologia vietata (rules/cove.md + communication.md)

- MAI "CarFax EU" → usare "DAT Fahrzeughistorie / TUV report"
- MAI "Handlergarantie" / "Händlergarantie" → usare "garanzia costruttore UE"
- MAI "DEKRA/DAT" nei messaggi finché non operativi
- MAI margine senza IVA → specificare sempre inclusa/esclusa
- MAI "veicolo EU", "ROI", "pipeline", "piattaforma", "algoritmo", "reimportazione" nei messaggi dealer

### 4.4 Linguaggio OK

- "macchina", "auto", "auto tedesca"
- "margine", "ci guadagna €X", "km certificati"
- Numeri in EUR netti (MAI percentuali): "€4.500 netti per lei" > "margine 18%"

### 4.5 Nomi pubblici ARGOS

- ARGOS Automotive (brand commerciale)
- ARGOS GRADE (etichetta A-E sul dossier)
- ARGOS™ (protocollo di verifica, NON azienda)

### 4.6 Persona sales — Luca Ferretti

- Nome: Luca Ferretti
- Ruolo pubblico: Vehicle Sourcing Specialist — Mercati EU
- WA Business: +39 328 153 6308
- Telefono fisso VoIP: 0972 536 918 (EhiWeb)
- Email: ferretti.argosautomotive@gmail.com
- Landing: https://argos-automotive.pages.dev
- Esperienza dichiarabile: "oltre 10 anni nel settore automotive europeo"
- Inizio: "Italia e Germania, poi specializzato nello scouting per concessionari"
- Portafoglio: "pochi concessionari selezionati, massimo 2-3 per provincia"
- Pricing: "paghi solo a veicolo consegnato" (success fee)
- Tono: professionale diretto, "Lei" al primo contatto Sud Italia, passare al "tu" solo se dealer lo fa prima
- Mai: "noi", "il nostro team", "la nostra piattaforma", "25 anni", "sede a Amsterdam/Monaco/Milano", "team di analisti", "algoritmo proprietario/AI/ML", "X dealer attivi" (se non vero)

### 4.7 Brand ARGOS — come usarlo

- Primo contatto: NON menzionare ARGOS. Firma "Luca Ferretti" o solo "Luca".
- Domanda "come verifichi le auto?": "Ho un protocollo di verifica che chiamo ARGOS — controlla prezzo, km, storico e anomalie su ogni veicolo prima di proporlo"
- Sul sito/landing: ARGOS appare come protocollo, non come azienda.

### 4.8 Template Day 1 corrente — hardcoded (primi 5 dealer, zero LLM)

Variante A (con `days_on_market` disponibile):
```
Buongiorno, sono Luca Ferretti.
Ho notato che la sua {MODELLO} {ANNO} a €{PREZZO} e' il prezzo piu' alto
tra i {MODELLO} {ANNO} che trovo su AutoScout24 in Italia,
ed e' in listing da {GIORNI} giorni.
Volevo capire se e' una scelta precisa sull'auto o se sta valutando di muoverla.
Luca
```

Variante B (fallback se `days_on_market IS NULL`):
```
Buongiorno, sono Luca Ferretti.
Ho notato che la sua {MODELLO} {ANNO} a €{PREZZO} e' il prezzo piu' alto
tra i {MODELLO} {ANNO} che trovo su AutoScout24 in Italia in questo momento.
Volevo capire se e' una scelta precisa sull'auto o se sta valutando di muoverla.
Luca
```

Variabili — 4 in totale, tutte da SQL:
- `{MODELLO}` ← `vehicle_listings.model`
- `{ANNO}` ← `vehicle_listings.year`
- `{PREZZO}` ← `vehicle_listings.price` (formato `€XX.XXX`)
- `{GIORNI}` ← `vehicle_listings.days_on_market` (se NULL → Variante B)

### 4.9 Template `wa-intelligence/templates.py` (storici, non usati dai primi 5 — da riallineare)

10 template definiti: `DAY1_PREMIUM`, `DAY1_MIXED`, `DAY1_GENERALIST`, `IDENTITY_RESPONSE`, `VEHICLE_PROPOSAL`, + altri (Day 3, Day 7 voice, OBJ_1/2, ecc.). Stato S132: hardcoded Day 1 ha precedenza sui template legacy per i primi 5 dealer.

### 4.10 Regole numeri verificabili

- Se non hai tutti e 3 i dati certi (MODELLO, ANNO, PREZZO) → NON generare messaggio
- Se "prezzo più alto" non è verificabilmente vero → usare altra osservazione reale
- Ogni numero nel messaggio deve essere verificabile dal dealer su AutoScout24
- Se campione benchmark < 5 listing → non dire "media", dire "tra i [N] che trovo oggi"
- "Diversi mesi" al posto di numero esatto → VIETATO

### 4.11 Sequenza touchpoint canonica

```
Day 1:  Veicolo concreto + domanda chiusa (WA testo)
Day 3:  Foto HD + secondo veicolo (WA testo+foto)
Day 7:  FOMO lieve O uscita dignitosa (WA testo)
Day 10: Vocale 20 sec (WA voice)
Day 14: Referral o case study (WA testo)
Day 21: Break-up gentile (WA testo)
Day 30: Telefonata o visita fisica (tel)
```

### 4.12 Credibilità sequenziale Sud Italia

1. Chi sei? → persona reale con volto (Google trovabile)
2. Chi ti ha mandato? → referral o specificità chirurgica sul SUO stock
3. Cosa hai fatto? → track record (recensioni, case study)
4. Cosa mi offri? → veicolo concreto con numeri
Se salti uno step, ricominci da capo.

---

## SEZIONE 5 — Skill ARGOS attive (`.claude/skills/`)

Skill repo-scoped (caricamento on-demand):

### `cove-analysis/SKILL.md`
description: Analisi e scoring veicoli con CoVe Engine. Carica quando Luke dice "analizza veicolo", "score", "anomalia prezzo", "benchmark", "confidence", "PROCEED/SKIP", o quando stai lavorando su cove_tracker.duckdb o cove_engine_v4.py. NON caricare per invio messaggi o fix scraper.

### `outreach-day1/SKILL.md`
description: Genera o valida messaggio Day 1 per dealer italiano. Carica quando Luke dice "genera day 1", "messaggio per [dealer]", "outreach", "contatta dealer", o nomina un dealer specifico per primo contatto. NON caricare per follow-up Day 3+ o per analisi CoVe.

### `scraper-ops/SKILL.md`
description: Fix e manutenzione scraper AutoScout24. Carica quando Luke dice "fix scraper", "scraper rotto", "404 listing", "MODEL_SLUG", "seller_name NULL", "on_demand_runner", o quando stai lavorando su tools/scrapers/autoscout_scraper.py o tools/on_demand_runner.py. NON caricare per scoring CoVe o invio WA.

### `wa-daemon-ops/SKILL.md`
description: Operazioni WA daemon su iMac. Carica quando Luke dice "verifica daemon", "invia messaggio WA", "stato WhatsApp", "daemon offline", "debug connessione", "porta 9191", o quando devi inviare o verificare un messaggio WhatsApp via wa-daemon.js. NON caricare per generare il testo del messaggio (usa outreach-day1).

### Altre skill presenti (pre-S130, non attivamente triggerate):
`ai-engineer`, `analytics-reporter`, `api-tester`, `app-store-optimizer`, `backend-architect`, `brand-guardian`, `content-creator`, `devops-automator`, `experiment-tracker`, `feedback-synthesizer`, `finance-tracker`, `frontend-developer`, `gh-actions`, `growth-hacker`, `gstack`, `human-first-outreach`, `infrastructure-maintainer`, `instagram-curator`, `legal-compliance-checker`, `mobile-app-builder`, `performance-benchmarker`, `project-shipper`, `rapid-prototyper`, `reddit-community-builder`, `skill-argos`, `skill-argos-debug`, `skill-argos-intel-territoriale`, `skill-argos-orchestrator`, `skill-argos-v2-backup`, `skill-argos-validator`, `skill-browser-chrome`, `skill-cove`, `skill-data-official`, `skill-deep-research`, `skill-handover`, `skill-loader`, `skill-marketing-official`, `skill-sales-official`, `sprint-prioritizer`, `studio-producer`, `support-responder`, `test-results-analyzer`, `tiktok-strategist`, `tool-evaluator`, `trend-researcher`, `twitter-engager`, `ui-designer`, `ux-researcher`, `visual-storyteller`, `whimsy-injector`, `workflow-optimizer`.

Per descrizione integrale leggi `<skill>/SKILL.md` — non riportata qui per estensione.

---

## SEZIONE 6 — Agent attivi (`.claude/agents/`)

### Agent ARGOS-specifici (frontmatter completo letto)

- **agent-cove** — model: `haiku` | tools: Read, Bash | maxTurns 15 | memory project
  CoVe Engine scoring (DuckDB read-only). Deleghe: "score veicolo", "confidence dealer", "query DuckDB", "PROCEED/SKIP/VIN_CHECK", "cove_tracker", "threshold".

- **agent-finance** — model: `haiku` | tools: Read | maxTurns 10
  ROI, fee, P&L, fiscale TD17/18/19, reverse charge, IVA import EU. Solo lettura. Mai fatture autonome.

- **agent-marketing** — model: `sonnet` | tools: Read, Write | maxTurns 20
  Brand, landing page, email sequences, one-pager. REGOLA CRITICA: MAI esporre tech stack (CoVe, Claude, AI) in materiali pubblici.

- **agent-ops** — model: `haiku` | tools: Bash, Read | maxTurns 20
  Infrastruttura iMac, PM2, WA daemon salute, deploy GH Actions, SSH, health endpoints.

- **agent-recovery** — model: `opus` | tools: Read, Write, Bash | maxTurns 20
  Dealer silenti (Recovery Day 7+), obiezioni complesse, stallo, lead freddi.

- **agent-research** — model: `sonnet` | tools: Read, Grep, WebSearch, WebFetch | maxTurns 30 | skills: deep-research
  Nuovi lead, account research, competitive intelligence, mercato EU/IT.

- **agent-sales** — model: `sonnet` | tools: Read, Write, Bash | maxTurns 25 | skills: argos-outreach-automation
  Pipeline dealer, WA/email, sequenze multi-step, persona detection, OBJ handling.

- **architect** — model: `claude-opus-4-6` | tools: Read, Grep, Glob, Bash
  Analizza e pianifica prima di qualunque implementazione. NON modifica file.

- **context-loader** — model: `claude-haiku-4-5-20251001` | tools: Read, Glob
  Carica solo contesto rilevante al task. Keyword → file mapping.

- **implementer** — model: `claude-sonnet-4-6` | tools: Read, Write, Edit, MultiEdit, Bash, Glob
  Implementa piano approvato (solo dopo architect + utente).

- **validator** — model: `claude-opus-4-6` | tools: Read, Bash, Grep | memory project
  Verifica implementazioni con test reali. Trova problemi, non conferma.

### Agent subdirectory (specializzati verticali)

Ruoli brevi (vedi singoli `.md` per frontmatter completo):

- `analytics/` — dashboard-manager, kpi-tracker, pipeline-reporter
- `dossier/` — dossier-generator, watermark-manager
- `engineering/` — ai-engineer, backend-architect
- `finance/` — fee-calculator, revenue-forecaster, roi-analyzer, tax-compliance
- `guardrails/` — cost-enforcer, quality-auditor, terminology-checker
- `identity/` — credibility-builder, persona-manager
- `intelligence/` — cove-scorer, deep-researcher, lead-researcher, market-analyst, price-index-manager, scraper-orchestrator, vehicle-verifier, vin-checker
- `logistics/` — import-manager, transport-coordinator
- `marketing/` — brand-guardian, content-creator, growth-hacker, landing-builder, review-strategist, social-manager
- `operations/` — database-admin, deploy-manager, infra-monitor, telegram-bot, wa-daemon-ops
- `product/` — competitive-intel, dealer-persona-researcher, roadmap-planner, trend-researcher
- `project-management/` — project-shipper
- `sales/` — dealer-outreach, objection-handler, persona-classifier, pipeline-manager, recovery-specialist, sales-agent-blueprint
- `session/` — prompt-generator, session-handoff
- `studio-operations/` — analytics-reporter, finance-tracker, legal-compliance-checker
- `testing/` — outreach-auditor, pipeline-validator, scraper-tester
- `testing-suite/` — api-tester

---

## SEZIONE 7 — MCP attivi (`.mcp.json`)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"],
      "timeout": 30000
    },
    "sqlite-argos": {
      "command": "/tmp/mcp-sqlite-venv/bin/mcp-server-sqlite",
      "args": ["--db-path", "/tmp/argos_dashboard_snapshot.db"]
    }
  }
}
```

Stato:
- **playwright** — attivo (headless, timeout 30s). Uso: browser automation, scraping Playwright, test E2E UI.
- **sqlite-argos** — attivo. Scope: snapshot dashboard read-only su `/tmp/argos_dashboard_snapshot.db`.

MCP registrati nell'harness (sistema, non repo):
- Gmail, Google Calendar, Google Drive (auth via `authenticate` tool)
- Hugging Face (anonymous, rate-limited; `HF_TOKEN` opzionale)
- Playwright browser (`mcp__playwright__*` suite completa)

---

## SEZIONE 8 — Workflow operativi consolidati

### 8.1 Scraping pipeline

Orchestratore: `tools/on_demand_runner.py` (wrapper zero-reinvention).
Factory scraper: `tools/scrapers/market_intelligence.py → get_scraper()`.

Flusso:
1. Input CLI: `--marca`, `--budget`, `[--modello, --anno-min, --dealer]`
2. Risolve MODEL_SLUG dict → URL per portale (DE/NL/BE/AT/FR/SE/IT)
3. Richiesta HTTP con rate limit per portale (3-15s + burst pause)
4. Parser (JSON strutturato, mai CSS selectors fragili)
5. Upsert in DuckDB `vehicle_listings` (include `seller_name` post-S132)
6. Invoca CoVe Engine scoring (vedi §8.2)
7. Output: path PDF dossier su `dossiers/`

Portali configurati (mapping dei primi 10 da `config.py`): `autoscout24_de`, `autoscout24_nl`, `autoscout24_be`, `autoscout24_at`, `autoscout24_fr`, `autoscout24_se`, `autoscout24_it`, `mobile_de`, `willhaben_at`, `leboncoin_fr`. Regola `rules/identity.md`: 28 portali totali coperti.

Pattern AS24 2026 (sedan/wagon): `{model}-(alle)` — es. `3er-(alle)`, `5er-(alle)`, `c-klasse-(alle)`, `e-klasse-(alle)`, `glc-(alle)`, `gle-(alle)`, `a-klasse-(alle)`. SUV (x3, x5, q5, a4, ...) mantengono slug corto. BE usa path `/fr/lst/` o `/nl/lst/`.

### 8.2 CoVe scoring pipeline

Invocato da: `src/cove/scraper_cove_pipeline.py` e `src/cove/pipeline_orchestrator.py`.

Catena di valore:
```
Scraper (28 portali) → CoVe Engine (scoring + fraud) → Opportunity Selection → Dealer Dossier
```

Flusso per listing:
1. Validazione base (make, model, year in 2018-2023, km/price presenti)
2. Fraud flags check (`fraud_flags.py` → `FraudFlagsChecker`)
3. Market verifier enterprise (benchmark prezzo, sigma, n_comparable)
4. Bayesian uncertainty `Si = μ − λ·σ` (λ adattivo per fascia prezzo)
5. Pesi: price 0.35, km 0.25, age 0.20, history 0.20
6. Decisione:
   - confidence ≥ 0.75 → PROCEED
   - 0.60 ≤ confidence < 0.75 → VIN_CHECK (opt-in con VIN)
   - confidence < 0.60 → SKIP
7. Scrive `cove_results(listing_id, ..., recommendation, confidence, analyzed_at)`
8. Log transizione in `pipeline_log`

VIN check cascade (free tools): freevindecoder (scartato), car-recalls.eu, KBA, DAT consumer, garanzia BMW/MB/Audi (scartata — login proprietario richiesto).
ARGOS GRADE A-E: pesi 35% CoVe confidence, 20% fraud flags, 15% completezza, 15% foto, 10% recall, 5% storico km.

### 8.3 WhatsApp outreach flow

Entry point: POST `/send` su daemon iMac `:9191`.

Pipeline pre-invio:
1. Auth header `X-API-Key`
2. `checkDailyReset()` — azzera contatore se nuovo giorno (Europe/Rome)
3. `isBusinessHours()` — blocca se fuori finestra 8-22 (S116 esteso)
4. `getDailyLimit()` — dinamico 10/15/20 per età account
5. `getAgentStatus()` — blocca se "paused"
6. `getPauseUntil()` — blocca se in long pause (5-10 min ogni 5 msg)
7. `outbound_guard.py` → `state_machine.can_send()` + `is_duplicate()` + `validator.validate()`
8. Se first_contact: `HumanLike.simulateTyping()` (mean 50ms/char + jitter, clamp 2-10s)
9. `client.sendMessage()` (whatsapp-web.js)
10. `post_send_update.py` → transizione stato conversazione (`DAY1_SENT`, `DAY3_SENT`, ecc.)
11. Incremento `daily_stats.sent`, `DAILY_SENT++`
12. Telegram alert con payload sintetico
13. Log in `audit_log`

Payload `/send`:
```json
{"phone": "393...", "message": "testo", "dealer_id": "..."}
```

Response success:
```json
{"status": "sent", "msg_id": "...", "daily_sent": N, "first_contact": true|false}
```

Response blocked:
```json
{"error": "outside business hours" | "daily limit reached" | "long_pause_active" | "...", ...}
```

### 8.4 Warming protocol (S117)

Agent account_start_date registrata in `agent_state`. `getDailyLimit()` applica:
- settimana 0-1: 10 msg/giorno
- settimana 2-3: 15 msg/giorno
- settimana 4+: 20 msg/giorno (cap permanente per API non ufficiale)

Long pause ogni 5 msg: random 5-10 min (scritto in `agent_state.pause_until`).

### 8.5 Validation pipeline messaggi

`validator.py:validate(message, template_id, dealer_state, dealer_id, mode)` — layer content rules:

1. `_check_fee_leak` (no fee se template ≠ OBJ_2_FEE)
2. `_check_identity_inversion`
3. `_check_identity_spoofing`
4. `_check_banned_words` (usa `FORBIDDEN_TERMS` + `FORBIDDEN_WORDS_EXACT` + deobfuscation)
5. `_check_injection_attempt`
6. `_check_length` (<4096)
7. `_check_tech_leak`
8. Layer 4 content rules (S128): `CRED-SEQUENCE`, `NO-OFFER-DAY1`, `TEMPLATE-EXACT-RENDERING`, `LEX-SELFAUTH`, `LEX-SCARCITY`, `BRAND-SELFPROMO`

Modi: `shadow` (log only), `canary` (log + block parziale), `enforce` (block totale).
Log: ogni check in `validation_log(dealer_id, rule_id, decision, motivation, message_hash, mode)`.

GATE conflict resolution Layer 0 (pianificato, non ancora nel codice):
`GATE (ICP, signal fresh) > COMP > BRAND > FORMAT > TIMING > RATE > ARCH > TONE`

### 8.6 Scheduler & recovery

`wa-intelligence/scheduler.py` — loop ogni 30 min.
Scheduled actions: Day 3 follow-up (testo), Day 7 voice note, Day 12 escalation.
Recovery Day 7+: delegata a `agent-recovery` (Opus) se dealer silent.

---

## SEZIONE 9 — Regole progetto (CLAUDE.md integrale)

```markdown
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
- Test su TEST_FOUNDER (39<TEST_FOUNDER_NUM>) prima di qualsiasi dealer reale
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
```

Le 5 rules sono riportate integralmente in §11 (per continuità logica della sezione Gotchas).

---

## SEZIONE 10 — Sprint corrente e backlog

### 10.1 CURRENT_SPRINT.md integrale

```markdown
# Sprint attuale — non modificare fino a completamento

## Task 1: Fix scraper slug Mercedes + BMW sedan
**DONE quando:**
```bash
python3 tools/on_demand_runner.py --marca Mercedes --modello "Classe C" --budget 50000
# restituisce >=3 listing con prezzo e km
```
**File:** `tools/scrapers/autoscout_scraper.py` — dict MODEL_SLUG
**Skill:** `/scraper-ops`

## Task 2: Fix seller_name nei listing IT
**DONE quando:**
```sql
SELECT COUNT(*) FROM vehicle_listings
WHERE source='autoscout24_it' AND seller_name IS NOT NULL;
-- risultato > 0
```
**File:** `tools/scrapers/autoscout_scraper.py` — parsing HTML
**Skill:** `/scraper-ops`
**Prerequisito:** nessuno (parallelo a Task 1)

## Task 3: E2E demo su TEST_FOUNDER
**DONE quando:** messaggio ricevuto su 39<TEST_FOUNDER_NUM> generato dalla pipeline
`scrape → score → genera template → invia via daemon`
**Prerequisiti:** Task 1 e Task 2 DONE
**Skill:** `/outreach-day1` + `/wa-daemon-ops`

---

## Regole sprint
- Non iniziare Task N+1 prima che Task N sia DONE
- Se trovi un problema nuovo → scrivilo in `BACKLOG.md`, non risolverlo ora
- `/compact` a 50% di contesto residuo
- `/clear` tra un task e l'altro
```

Stato S132: Task 1 DONE, Task 2 DONE (commit `96c3865`), Task 3 PENDING (bloccato da business hours 20:01>20:00 — retry ≥09:00 domani; daily quota 4/10 intatta).

### 10.2 BACKLOG.md integrale

```markdown
# Backlog — problemi trovati ma non nel sprint corrente

<!-- Aggiungi qui durante lo sprint. Non risolvere ora. -->

## Gap strutturali (da S130)
- `days_on_market` non recuperabile dai search results — richiede click su detail page
- `vehicle_listings.matched_dealer` = NULL — le due tabelle non sono collegate
- PDF E2E con dati CoVe reali mai completato (immagini sanitizzate OK, dati reali no)

## Architettura avanzata (Phase 3 — dopo 30 messaggi reali)
- L5 LLM-as-judge validator
- `mv_market_insights` view materializzata su CoVe
- Geographic routing Nord/Centro/Sud
- `insight_delta` schema
- SEQ-NOEXIT-BEFORE-DAY21 rule
- Batch generation + digest Telegram 08:00
- `persona_evolution_log`
- GATE-ICP-001 con soglie calibrate empiricamente
- Confidence-gated blending archetipi (0.65-0.85 → top-2 blend)

## Miglioramenti scraper
- Scraping periodico AutoScout24.it → `dealer_inventory_snapshots` in DuckDB
- Signal: aged inventory (>90 giorni senza variazioni) come trigger primario
- `days_on_market` via detail page click (richiede Playwright o delay aggiuntivo)
- `mobile_de`: MobileDeScraper non implementa `parse_search_results` (abstract method) — on_demand_runner skips silenziosamente
- `seller_name` ancora NULL per listing DE/NL già esistenti — solo nuovi insert la salvano (fix S131)
- `vehicle_listings.seller_city` non estratta (disponibile in `item.location` su AS24.it)
```

### 10.3 HANDOFF.md corrente (S130 — non aggiornato a S132)

Contenuto fatto/scoperto S130, framework messaggi, contraddizione Day 1 (poi risolta S131: citare auto del dealer = OK), file chiave, Stile Car dati (persona RELAZIONALE, score 8.5; BMW X4 2022 €35.499 +7.9% vs benchmark, BMW 118d 2021 €21.500, BMW 216d 2020 €10.999).

---

## SEZIONE 11 — Gotchas e decisioni passate

### 11.1 Regole repo (`.claude/rules/*.md`) — integrali

#### identity.md
```
Brand: ARGOS Automotive | Persona: Luca Ferretti
Business: B2B vehicle scouting EU→IT | Fee: €800-1.200 success-fee
Target: Concessionari family-business Sud Italia, 30-80 auto
Mercati: DE/NL/BE/AT/FR/SE + tutti EU (19 paesi coperti)
Veicoli: BMW/Mercedes/Audi + Porsche/Lambo/Ferrari/McLaren/Range Rover 2018-2025
Landing: https://argos-automotive.pages.dev | Dashboard: iMac:8080 | WA Business: 3281536308
```

#### cove.md
```
- recommendation (MAI verdict) | analyzed_at (MAI created_at) | confidence 0.0-1.0
- DEALER_PREMIUM_THRESHOLD=0.75 | VIN_CHECK_THRESHOLD=0.60 | DAILY_LIMIT=30
- cove_engine_v4.py → NON MODIFICARE
- MAI: CoVe/RAG/Claude/Anthropic/embedding nei messaggi dealer
- MAI "CarFax EU" → "DAT Fahrzeughistorie / TUV report"
- MAI margine senza IVA → specificare sempre
- MAI Handlergarantie → garanzia costruttore UE
- MAI DEKRA/DAT nei messaggi finche' non operativi
- Il valore ARGOS e' nei portali PICCOLI/NICCHIA
- Scraper SEMPRE persistenti — MAI CSS selectors
```

#### communication.md
Regole base (5 righe max, domanda chiusa, prodotto reale con numeri, personalizzato per archetipo). Credibilità sequenziale. Linguaggio (usare macchina/auto/margine; MAI veicolo EU/ROI/pipeline). Cosa NON fare Day 1. Sequenza touchpoint Day 1-30. Reference: s73/s75/s94.

#### security.md
Credenziali zero deroga, API security (X-API-Key porta 9191, input validation telefono italiano, <4096 char), deploy atomico rsync+symlink+healthcheck, DB backup 6h con `sqlite3 .backup` (MAI `cp`), WAL+busy_timeout=10000, LLM cascade 5 livelli con circuit breaker, MAI template fallback senza alert TG, prompt injection defense, minimizzare PII (no telefoni, solo nome+città), monitoring 5 min, Telegram alert, heartbeat 30 min, ZERO COSTI, test E2E prima di outreach.

#### competitors.md
- **Bolidem** — 219 rec 4.8/5, 25 anni, B2C, fee upfront (€20+€299+€950), cliente cerca auto
- **Autotedesche.it** — 162 rec 4.9/5, SEO forte, B2C, 1 persona, fee upfront
- **Importami.com** — fee 4% min €750+IVA upfront, B2C, no outreach
- **GlobalCars** — no volti, no recensioni, non funziona
- **AUTO1** — 62 filiali IT, 6.000 dealer, 10 anni, modello opposto (compra DAL dealer)
- **AutoProff** — aste B2B, media €9k, no premium, EN
- **BCA Italia** — aste remarketing, ATECO richiesto, commissioni opache
- **eCarsTrade** — €350/transazione, no supporto IT

3 vantaggi ARGOS: SCOUTING PROATTIVO, SUCCESS FEE, B2B DEALER SUD.
Gap critico: zero recensioni, zero track record, primo dealer = atto di fede → vale 3-5 via referral.

### 11.2 Decisioni architetturali consolidate

**G1 — opt_out** in `conversations`: 4 campi (`opt_out INT`, `opt_out_at`, `opt_out_source`, `opt_out_raw_message`) per audit GDPR.

**G2 — validation_log + LIA** in SQLite `dealer_network.sqlite` (iMac).

**G3 — daemon endpoint**: 2 endpoint via SSH curl + idempotency key + rate limit 100 req/min + TLS (anche con Tailscale).

**G4 — Primary signal** (RIVISTO S127): aged inventory >90gg IT, NON new listing. Gerarchia: S+ aged → S price drop → A stock velocity → B Google review → C new listing.

**G5 — Opt-out wording**: "L'ho contattata perché il suo numero è pubblico su {data_source}. Se non le interessa, me lo dica e la cancello subito." (template con `{data_source}` dinamico).

**G6 — Archetipi come STATI** (non segmenti): confidence-gated blending (≥0.85 specifico, 0.65-0.85 top-2 blend, <0.65 NEUTRO). 5 core + NEUTRO > 8 fissi.

**Gap GAP-A — Validator enterprise**: Layer 5 LLM-as-judge (DeepSeek) — costo +2-3s, +€0.001/msg su 30/giorno. Layer stack L1-L6.

**Gap GAP-B — Evaluation framework**: golden dataset ≥80 dealer anonimizzati + red-team ≥40 adversarial inputs. Target: block <5% golden, FP <2%.

**Gap GAP-C — Rollout criteri**: shadow → canary ≥50 msg, block <5%, FP <2%, founder approva. Canary → enforce ≥200 msg, zero hard block, reply ≥8%, var block rate <20%. Rollback a shadow se non raggiunto in 4 settimane.

**Gap GAP-D — persona_evolution_log** per A/B testing versioni system prompt dopo 3 mesi dati.

### 11.3 P0 architetturali (S127 critique)

**GATE-ICP-001 (HARD)**: `premium_concentration = (BMW+MB+Audi)/total_stock`. <0.20 block, 0.20-0.30 low_priority, ≥0.30 ICP-CORE. Soglie env vars `ARGOS_ICP_MIN_RATIO`, `ARGOS_ICP_CORE_RATIO`.

**SIGNAL-FRESH-001 (HARD)**: `now() - signal_event.observed_at > 14 giorni` → block. TTL env var `ARGOS_SIGNAL_TTL_DAYS`.

**NO-OFFER-DAY1-001 (HARD)**: complementare a CRED-SEQUENCE-001. CRED blocca offerta senza contesto; NO-OFFER blocca offerta dopo contesto nel Day 1.

**signal_event unificato**: `{url, days_on_market, vehicle, listing_price, scrape_date, signal_strength, signal_observed_at}` — fluisce in message anchor + LIA data_source + opt-out.

**Layer 0 conflict resolution**: `GATE > COMP > BRAND > FORMAT > TIMING > RATE > ARCH > TONE`.

**Batch generation** (P0 governance): 07:00 gen → 07:30 digest TG raggruppato → 08:00 founder approva bulk → 09:30 invio scheduled. Senza batch review, founder abbandona HITL dopo 1 settimana.

**L5 fallback**: NO Opus paid (viola ZERO COST). Integrarsi in cascade esistente `Gemini → Groq → OpenRouter free → Gemini Lite → Ollama`. Env var `ARGOS_L5_FALLBACK_MODEL`. Fail-shadow se cascade down → auto-downgrade canary giornata.

**Geographic routing** (P2): override strutturale solo celle distanti (Nord base / Roma-Sud override). Centro default. Per Sud: override struttura (storia → offerta), non solo markers linguistici. ARCH-GEO-001 SOFT (no HARD — falsi positivi dealer Nord con origini Sud).

### 11.4 Pattern psicologici validati (research 2026, 3° giro)

Hypothesis framing Day 1:
- Aprire con UN'ipotesi specifica (non 2 alternative) + invito a correggerla
- Modalità correttiva > modalità difensiva
- Ipotesi archetype-specific:
  - RAGIONIERE → costo implicito del non-agire
  - NARCISO → qualcosa che mercato IT non ha
- `{days_on_market}` ESATTO, MAI "diversi mesi" se hai il numero
- Reply rate atteso: 15-25% (vs 3.43% industry)

### 11.5 Failure mode documentati — da evitare

- **Regressione S132**: fix seller_name in `scraper_cove_pipeline.py` ha side-effect — i 3 listing IT scrapati 19:39 con seller_name popolato hanno make/model VUOTI. Demo E2E usa listing pre-regressione (2026-03-24). Bloccante per dealer reali — fix prima del primo outreach produzione.
- **Business hours bypass**: `{"error":"outside business hours"}` NON bypassabile (security zero deroga). Retry in finestra 08-20.
- **dealer_network.sqlite in wa-intelligence/**: vuota, NON usarla. Usare quella in root `/Users/gianlucadistasi/Documents/app-antigravity-auto/`.
- **Colonna phone vs phone_number**: in `messages` è `phone_number` con suffisso `@c.us`.
- **current_step come segnale di risposta**: SBAGLIATO. La risposta dealer reale = righe `messages` con `direction='inbound'`.
- **"Germania", "premium", "cerco auto"** nel Day 1: trigger difensivo → dealer non risponde.
- **V3 framework (CHI+PERCHÉ+DOMANDA)** dichiarato SBAGLIATO dal founder S130.
- **Day 1 senza anchor verificabile**: se "prezzo più alto" non è vero al momento dell'invio → ricalcolare benchmark.
- **mobile_de scraper**: `parse_search_results` è abstract, `on_demand_runner` skippa silenziosamente.
- **seller_name listing vecchi**: rimangono NULL — il fix S132 salva solo nuovi insert.
- **PDF E2E con dati reali**: mai completato. Immagini sanitizzate OK, ma il generatore non è mai stato testato con dati CoVe PROCEED reali end-to-end.
- **matched_dealer = NULL**: `vehicle_listings` e `conversations` non collegate → impossibile linkare veicolo al dealer automaticamente.
- **`days_on_market`** non presente in search results AS24.it — richiede click su detail page (Playwright).
- **ARGOS_API_KEY env var**: chiamata `ARGOS_API_KEY` NON `WA_API_KEY` (skill wa-daemon-ops errata storicamente).
- **Opus per L5**: viola ZERO COST → MAI usare modelli paid fuori cascade free.
- **Hardcoded credentials in chat/commit**: zero deroga. Solo `.env` + `.gitignore`.
- **`cp` su SQLite live**: corrompe WAL. Usare `sqlite3 .backup`.
- **Cancellazione `-wal`/`-shm`** con processi aperti: corrompe DB.

### 11.6 Lesson learned operativi

- "640 listing grezzi non sono valore. 20 opportunità verificate con margine stimato SONO valore."
- "Spazzatura nei raw data è NORMALE — serve motore che filtra."
- "Se un componente esiste, USALO. Non reinventarlo."
- "Il valore ARGOS è nei portali PICCOLI/NICCHIA" (non solo AS24/mobile.de).
- Primo dealer = atto di fede. Vale 3-5 dealer via referral.
- Sud Italia: dare del "Lei" al primo contatto, passare al "tu" solo se dealer lo fa prima.
- Persona deve essere trovabile su Google (volto + nome) prima del primo contatto.
- Nel Day 1: citare auto del dealer = OK (osservazione su di lui). Dichiarare cosa fa Luca / dove cerca = VIETATO (attiva filtro anti-spam).
- Prompt injection defense: sanitizzare input dealer, validare output LLM, minimizzare PII nelle chiamate LLM.

### 11.7 Stato asset commerciali

Landing page `https://argos-automotive.pages.dev` — live Cloudflare Pages.
Assets presenti in `assets/`: `ARGOS_APPROVED_sobrio.png`, `ARGOS_logo_sobrio_horizontal.png`, `cover_google_business*.{png,svg,html}`, `favicon*.{svg,png,html}`, `luca_ferretti_v{1-5}.png`, `og_image*.{png,svg,html}`, `one_pager_dealer.{html,pdf}`, `one_pager_v2.{html,png}`, `post_{1,2}*.{txt,png,svg,html}` (BMW X3, Mercedes GLC).

Dossier PDF esempio: `dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf`.

### 11.8 Archivio prompt sessioni

Prompt storici in `prompts/` — da `s83_phase3_phase4_execute.md` a `s99_*`. Il prompt più recente è aggiornato in HANDOFF.md + `prompts/s{N+1}_*.md` a fine sessione.

Reference master:
- `research/S73_MASTER_REFERENCE.md`
- `research/S94_MASTER_REFERENCE.md`
- `research/s98_ARCHITETTURA_DEFINITIVA.md`
- `research/s94_MESSAGGI_DEFINITIVI_V3.md` (nota: V3 dichiarato sbagliato in S130, riferimento solo storico)

### 11.9 Planning docs (`.planning/`)

- `STATE.md` — milestone v1.0, phase 04 (primo-outreach-stile-car) EXECUTING, plan 2/4, 4/5 phases completed, 14/17 plans completed
- `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`
- `CODE-AUDIT.md`, `SECURITY-AUDIT.md`, `TECH-RISK.md`
- `LEGAL-COMPLIANCE.md`, `PMF-VALIDATION.md`, `MARKET-RESEARCH-2026.md`, `HIGH-FIXES-RESEARCH.md`
- `FLUXION-MERGE-DOSSIER.md`
- `deploy_s106_checklist.md`, `s106_readiness_report.md`
- `research/SUMMARY.md`, `ARCHITECTURE.md`, `FEATURES.md`, `STACK.md`, `PITFALLS.md`

Core value consolidato (`.planning/PROJECT.md` 2026-03-24):
> "Il dealer riceve un dossier con dati che non trova da nessun'altra parte — verificati, reali, e pronti per la rivendita."

---

FINE DOCUMENTO — CURRENT_STATE_ARGOS_20260417.md
