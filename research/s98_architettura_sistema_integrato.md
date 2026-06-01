# S98 — Deep Research: Architettura Sistema Integrato ARGOS

## 1. DIAGNOSI — Perché si rompe tutto

### 1.1 Problema #1: DUE REPO, DUE DB, DUE MONDI
```
MacBook: /Users/macbook/Documents/combaretrovamiauto-enterprise/
  └── dealer_network.sqlite (tabelle: dealers, market_*)
  └── src/cove/, tools/, wa-intelligence/ (codice sorgente)

iMac: /Users/gianlucadistasi/Documents/app-antigravity-auto/
  └── dealer_network.sqlite (tabelle: conversations, messages, pending_replies)
  └── wa-intelligence/ (COPIA MANUALE del codice, spesso non allineata)
```

**Conseguenze:**
- Ogni deploy è un `scp` manuale che può fallire silenziosamente
- Il DB del MacBook ha tabelle diverse dal DB dell'iMac
- Il daemon crasha perché il suo DB si corrompe e nessuno lo monitora
- I send_*.py usano il DB MacBook per il CRM ma inviano via iMac
- Non c'è un singolo `git pull` che aggiorna tutto

### 1.2 Problema #2: Nessun monitoraggio
- OpenRouter esaurisce il credito → nessun alert
- DB si corrompe → crash loop per ore senza notifica
- Daemon va offline → lo scopri solo quando testi
- Cron non gira (Mac in sleep) → nessuno lo sa

### 1.3 Problema #3: 15 script separati, zero orchestrazione
```
Scraper:        tools/on_demand_runner.py
CoVe:           src/cove/cove_engine_v4.py
PDF:            tools/scripts/pdf_generator_enterprise.py
Send Day1:      tools/send_day1_tier1.py
Send Day7:      tools/send_day7_tier0.py
Send Batch2:    tools/send_day1_tier1_batch2.py
Send All:       tools/send_all_20260402.sh
Analyzer:       wa-intelligence/response-analyzer.py
Scheduler:      tools/outreach_scheduler.py
Discovery:      tools/dealer_discovery/discovery_engine.py
CRM:            tools/dealer_crm.py
Fee calc:       tools/fee_calculator.py
Daemon:         wa-intelligence/wa-daemon.js
Dashboard:      wa-intelligence/dashboard/app.py
```
Nessuno di questi parla con gli altri in modo strutturato. Ogni connessione è un hack.

### 1.4 Problema #4: Deploy manuale
- Nessun CI/CD
- `scp` per copiare file singoli
- `npm rebuild` a mano quando Node version cambia
- `.env` diversi su ogni macchina
- Nessun modo di rollback

---

## 2. ARCHITETTURA TARGET — Sistema Integrato

### 2.1 Principio base
**UN repo, UN DB, UN deploy, UN orchestratore.**

### 2.2 Struttura repo unificata
```
combaretrovamiauto-enterprise/
├── .env                          ← UNICO file env (con variabili per locale/remoto)
├── argos.py                      ← CLI UNICO: python3 argos.py [command]
├── config/
│   ├── dealers.yaml              ← Pipeline dealer (fonte di verità)
│   └── settings.yaml             ← Config sistema
├── src/
│   ├── cove/                     ← CoVe Engine (NON TOCCARE)
│   ├── orchestrator.py           ← Orchestratore flusso completo
│   ├── analyzer.py               ← Response analyzer (LLM cascade)
│   ├── sender.py                 ← Invio WA/PDF unificato
│   └── monitor.py                ← Health check + alerting
├── tools/
│   ├── scrapers/                 ← Scraper portali EU
│   ├── pdf_generator.py          ← PDF dossier
│   └── fee_calculator.py         ← Fee
├── wa-intelligence/
│   ├── wa-daemon.js              ← Daemon WA (iMac only)
│   └── .env.daemon               ← Config specifica daemon
├── tests/
│   ├── test_e2e.py               ← Test E2E completo
│   ├── test_analyzer.py          ← Test analyzer tutti i casi
│   ├── test_sender.py            ← Test invio WA
│   └── test_pipeline.py          ← Test scrape→cove→pdf
├── deploy/
│   ├── sync.sh                   ← Sync repo → iMac (rsync, non scp)
│   ├── restart.sh                ← Restart daemon post-deploy
│   └── healthcheck.sh            ← Verifica tutto funziona
└── data/
    ├── dealer_network.sqlite     ← DB UNICO (CRM + conversations + messages)
    └── cove_tracker.duckdb       ← DB CoVe (separato, read-heavy)
```

### 2.3 DB Unificato — Schema
```sql
-- CRM
dealers (dealer_id, name, city, phone, persona, score, tier, status, ...)
-- Conversazioni (merging conversations + messages)
conversations (id, dealer_id, direction, body, classification, llm_model, created_at)
-- Pipeline
pipeline_actions (id, dealer_id, action_type, scheduled_at, executed_at, status)
-- Monitoring
system_health (id, component, status, last_check, error_msg)
llm_costs (id, model, tokens_in, tokens_out, cost_usd, dealer_id, created_at)
```

### 2.4 Orchestratore — Flusso unico
```
python3 argos.py discover          → Trova nuovi dealer
python3 argos.py profile DEALER    → Profila dealer (archetipo, score)
python3 argos.py outreach DEALER   → Prepara + invia Day 1
python3 argos.py respond           → Processa risposte inbound
python3 argos.py search DEALER     → Scrape → CoVe → PDF per richiesta specifica
python3 argos.py send-dossier D P  → Invia PDF a dealer
python3 argos.py test              → Test E2E completo
python3 argos.py health            → Health check sistema
python3 argos.py status            → Stato pipeline
```

### 2.5 LLM Cascade (già implementato, da stabilizzare)
```
1. OpenRouter Haiku (se credito disponibile)
2. OpenRouter Qwen 3.6 Plus :free
3. OpenRouter Llama 70B :free
4. OpenRouter Gemma 27B :free
5. Google Gemini Flash (API key separata)
6. Template fallback (ULTIMO resort)
```
Test automatico giornaliero: alle 7:00 testa tutti i provider e logga quale funziona.

### 2.6 Deploy
```bash
# Dal MacBook:
./deploy/sync.sh        # rsync → iMac (esclusi .env, node_modules, dossiers)
./deploy/restart.sh     # restart daemon via SSH
./deploy/healthcheck.sh # verifica daemon + DB + LLM + WA connesso
```

### 2.7 Monitoring
Ogni 30 minuti il daemon verifica:
- DB integrity (`PRAGMA integrity_check`)
- LLM funzionante (test call con 1 token)
- WA connesso
- Disk space
Se qualcosa fallisce → Telegram alert immediato al founder

---

## 3. FLUSSO DEALER END-TO-END

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  DISCOVERY   │────▶│  PROFILING    │────▶│  MESSAGGIO   │
│ (92 dealer)  │     │ (archetipo,  │     │ (Day 1, per- │
│              │     │  score, tier)│     │  sonalizzato)│
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  FEE TRACK   │◀────│  DOSSIER PDF │◀────│  INVIO WA    │
│ (€800-1200)  │     │ (scrape→cove │     │ (daemon API) │
│              │     │  →pdf)       │     │              │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │  RISPOSTA    │
                                          │ (auto-reply  │
                                          │  via LLM)    │
                                          └──────┬──────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                              CURIOSITY    VEHICLE_REQ    NEGATIVE
                              (rassicura)  (pipeline!)    (exit gentile)
```

---

## 4. PIANO DI IMPLEMENTAZIONE — Priorità

### Sprint 1: Infra solida (1 sessione)
- [ ] Unificare DB (merge schema MacBook + iMac)
- [ ] Deploy script (rsync + restart + healthcheck)
- [ ] Monitoring base (DB integrity + LLM health + WA status → Telegram)
- [ ] Test E2E che gira senza SSH timeout

### Sprint 2: Orchestratore (1-2 sessioni)
- [ ] `argos.py` CLI unificato
- [ ] Flusso outreach automatico (scheduler legge pipeline_actions)
- [ ] Response analyzer con LLM cascade stabile
- [ ] Conversazione multi-turn (non solo single reply)

### Sprint 3: Credibilità (1 sessione)
- [ ] Landing page review
- [ ] PDF dossier enterprise grade
- [ ] Google Business completato
- [ ] Facebook recuperato o Piano B

### Sprint 4: Dealer reali (solo dopo Sprint 1-3 green)
- [ ] Test E2E PASSA tutti i test
- [ ] Primo outreach TIER1 con sistema automatico
- [ ] Monitoring attivo 24/7

### Sprint 5: Crescita
- [ ] Discovery automatico (92 → filtra → profila → prioritizza)
- [ ] CoVe match veicolo↔dealer
- [ ] Programma affiliazione
- [ ] Scale a 20+ dealer

---

## 5. COSA NON FARE PIÙ

1. **MAI** deploy con `scp` di singoli file
2. **MAI** testare mandando messaggi dal telefono
3. **MAI** avere DB diversi su macchine diverse
4. **MAI** mandare a dealer reali senza test E2E green
5. **MAI** aggiungere script separati — tutto passa dall'orchestratore
6. **MAI** ignorare errori LLM/DB — monitoring attivo

---

## 6. DECISIONI DA PRENDERE COL FOUNDER

1. **Budget LLM**: ricaricare OpenRouter ($5-10) per avere Haiku stabile, o full-free con Qwen?
2. **Priorità**: infra first (Sprint 1) o dealer first (rischio ma veloce)?
3. **Facebook**: ricorso o nuovo account?
4. **Programma affiliazione**: quando iniziare a strutturarlo?
