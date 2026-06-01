# Roadmap: ARGOS — Dal VIN Reale al Dossier Reale

## Overview

Phases 1-3 built ARGOS technical foundation (validazione tool, schema DB, GRADE+PDF Enterprise). Phase 4 generates the first dossier for Stile Car. **FASE 0 (Credibility infrastructure)** and **FASE 5 (Outreach protocol 4-layer)** added 2026-05-13 post-S11c-strategic founder closure (Q1-Q11): persona frontman fittizio AI "Luca Ferretti", cash-only no documento, scope nazionale wave-based, anti-Bolidem positioning. Phase 6 AMBRA agent autonomy.

**Wiki cross-link** (single source of truth strategia + decisioni):
- `~/venture-os/wiki/projects/ARGOS/STRATEGY.md` — 6 sezioni (persona, 4-layer outreach, contenuti, compliance, pipeline test, refs)
- `~/venture-os/wiki/projects/ARGOS/DECISIONS.md` — 25 entry ADR lean (23 DECIDED + 1 OPEN-ipotesi + 1 SUPERSEDED)
- `~/venture-os/wiki/projects/ARGOS/README.md` — indice navigazione wiki

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)
- Phase 0: Pre-requisite infrastructure added retroactively (S11d 2026-05-13)
- Phase 5: Outreach protocol added retroactively (S11d 2026-05-13)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 0: Credibility Infrastructure** - Landing cleanup, foto AI gen, WA Business profile, Google Business Profile, recensioni soft (S165 ARGOS)
- [x] **Phase 1: Validazione Tool Gratuiti** - Test every free data source against real VINs from DuckDB (completed 2026-03-24)
- [x] **Phase 2: Schema DB + Detail Enricher** - Build DuckDB vehicle_listings/images schema and V2 enricher (completed 2026-03-24)
- [x] **Phase 3: ARGOS GRADE + PDF Enterprise V2** - Grading system A-E and dossier generation with real data (completed 2026-03-25)
- [ ] **Phase 4: Primo Outreach Stile Car** - Generate BMW X3 dossier and send Day 1 message to Domenico
- [ ] **Phase 5: Outreach Protocol 4-Layer** - Pipeline test 5-step (S166) + dealer-intel scraping (S167) + skill /outreach-day1 + HITL gating (S168)
- [ ] **Phase 6: AMBRA Agent — WA Autonomo** - Transform wa-daemon into human-like autonomous agent (multi-msg, imperfezioni, debounce, knowledge base, anti-ban)

## Phase Details

### Phase 0: Credibility Infrastructure
**Goal**: Layer 0 outreach infrastructure ready PRIMA qualsiasi dealer reale (Wave 1) — landing cleanup, foto AI persona, WA Business profile, Google Business Profile, recensioni soft
**Depends on**: Founder closure 2026-05-13 (Q1-Q5 chiusi via `FOUNDER-DECISIONS-2026-05-13.md`)
**Requirements**: CRED-01 landing cleanup, CRED-02 foto AI gen, CRED-03 WA Business setup, CRED-04 GBP, CRED-05 recensioni soft
**Success Criteria** (what must be TRUE):
  1. Landing `argos-automotive.pages.dev` rimossi tutti claim falsi ("10 anni esperienza", "P.IVA in corso") → riformulazione 3 pilastri verificabili (D-05 patch in wiki/DECISIONS.md)
  2. Foto profilo "Luca Ferretti" AI-generated custom (Midjourney/Flux €30 una-tantum) coerente cross-canale, NON stock library pubblica
  3. WA Business profile display name "Luca Ferretti — ARGOS Automotive", foto AI coerente, NO disclosure pseudonimo (D-OPEN-Q1 closure)
  4. Google Business Profile setup con service area Italia (no physical location), brand ARGOS™ only, NO P.IVA esposta (D-OPEN-Q2 cash-only)
  5. Recensioni soft seed: 3-5 review da contatti pre-ARGOS validati genuine (D-12 opzione c), no review fake
**Wiki ref**: `STRATEGY.md` sez 2 Layer 0 (table asset + action S165)
**Plans**: TBD S165 ARGOS

### Phase 5: Outreach Protocol 4-Layer
**Goal**: Layer 1+2+3 outreach protocol operativo end-to-end — dealer-intel scraping Wave 1 (TIER 0/1) + skill `/outreach-day1` HITL + 1-deal eccellenza primi 1-3 dealer
**Depends on**: Phase 0 (credibility) + Phase 4 (primo outreach Stile Car validato come TEST_FOUNDER caso 0)
**Requirements**: OUT-05 dealer-intel scraping, OUT-06 outreach-day1 skill upgrade, OUT-07 HITL gating, OUT-08 pipeline test 5-step
**Success Criteria** (what must be TRUE):
  1. **Pipeline test 5-step su TEST_FOUNDER pass** (D-11): smoke send Day 1, response interest, response STOP, response no-reply Day 7, edge case bug — TUTTE 5 fasi green + 0 messaggi sbagliati 14gg = trigger primo dealer reale
  2. **dealer-intel componente MVP** (S167 ARGOS): Google Maps scrape Wave 1 province TIER 1 (Salerno, Bari, Foggia, Catania, Cosenza), filter D-14 commissione informale (stock 3-10), output `dealer-targets.jsonl` ≥50 leads qualificati
  3. **skill /outreach-day1 upgrade** (S168 ARGOS): variant per macro-area (D-14) + anchor frase anti-Bolidem (D-20), compliance check pre-send (opt-out STOP, no claim verificabili, firma "Luca Ferretti", no menzione prezzo)
  4. **HITL primi 20 dealer reali enforced** (D-07): founder approve/edit/reject ogni outbound Day 1/3/7, throughput 3-5 dealer/giorno
  5. **1-deal eccellenza primi 1-3 dealer** (D-15): dossier full-spec (D-16 + D-18) + money-back guarantee DEKRA (D-OPEN-Q5) + follow-up 30gg → trigger raccomandazione/passaparola Sud Italia
**Wiki ref**: `STRATEGY.md` sez 2 (4-layer outreach) + sez 5 (pipeline test) + sez 1 (persona deflection table)
**Plans**: TBD S166-S168 ARGOS

**Mapping sessione ARGOS post-S11d**:
- S165 → Phase 0 (credibility infrastructure)
- S166 → Phase 5 sub-task 1 (pipeline test 5-step TEST_FOUNDER)
- S167 → Phase 5 sub-task 2 (dealer-intel MVP)
- S168 → Phase 5 sub-task 3+4+5 (skill /outreach-day1 + HITL + primo dealer reale)

### Phase 1: Validazione Tool Gratuiti
**Goal**: Every free data tool is tested with real VINs and we know exactly what each returns
**Depends on**: Nothing (first phase)
**Requirements**: TOOL-01, TOOL-02, TOOL-03
**Success Criteria** (what must be TRUE):
  1. At least 3 real PROCEED VINs from DuckDB have been run against each tool (freevindecoder, car-recalls.eu, KBA, DAT consumer, BMW/MB/Audi warranty portals)
  2. A documented matrix exists showing what each tool actually returns vs what it claimed — no tool is assumed to work
  3. Tools confirmed working can be called via scraping or REST with zero cost — integration path is clear
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Extract real VINs from AutoScout24 detail pages, produce test_vins.json
- [x] 01-02-PLAN.md — Test VIN-decode tools: freevindecoder.eu, NHTSA API, DAT consumer
- [x] 01-03-PLAN.md — Test recall and warranty tools: car-recalls.eu, KBA, BMW warranty, RDW
- [x] 01-04-PLAN.md — Consolidate results into TOOL_VALIDATION.md validation matrix

### Phase 2: Schema DB + Detail Enricher
**Goal**: Verified listing data and images are persisted in DuckDB, ready for grading and dossier generation
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. DuckDB has a vehicle_listings table with all required fields (listing_id, vin, make, model, year, mileage, price_eu, price_it_estimate, source, url, detail_url, scraped_at) populated for PROCEED listings
  2. DuckDB has a vehicle_images table linking listing_id to image_url, image_type, downloaded status, and local_path
  3. Detail Enricher V2 runs against a PROCEED listing and writes enriched data (detail page fields + image URLs) to both tables without modifying cove_engine_v4.py
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Create vehicle_listings + vehicle_images DuckDB schema, seed from cove_results
- [x] 02-02-PLAN.md — Build Detail Enricher V2: AS24 VIN + image extraction, writes to both tables

### Phase 3: ARGOS GRADE + PDF Enterprise V2
**Goal**: A completed dossier for any PROCEED listing can be generated with real photos, ARGOS GRADE, 7 verified criteria, and financial analysis
**Depends on**: Phase 2
**Requirements**: GRADE-01, GRADE-02, GRADE-03, GRADE-04, PDF-01, PDF-02, PDF-03, PDF-04, PDF-05
**Success Criteria** (what must be TRUE):
  1. ARGOS GRADE A-E is computed for any PROCEED listing using weighted inputs (35% CoVe confidence, 20% fraud flags, 15% data completeness, 15% photos, 10% recall, 5% km history) and the grade is reproducible
  2. Recall status and VIN decode (specs, emissions, year) are automatically pulled and attached to the listing record
  3. Residual manufacturer warranty is checked via brand portal VIN lookup and recorded
  4. PDF Enterprise V2 opens with a prominent ARGOS GRADE badge, includes real HD photos from the listing, and shows only verified data in the "7 Criteri ARGOS Premium Verified" section
  5. PDF financial analysis shows EU price, chiavi-in-mano cost, and net dealer margin in EUR — no percentages, no source references, dealer watermark applied
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — ARGOS GRADE A-E calculator with weighted scoring + NHTSA recall integration
- [x] 03-02-PLAN.md — PDF Enterprise V2 with grade badge, real photos, 7 Criteri, financial analysis

**UI hint**: yes

### Phase 4: Primo Outreach Stile Car
**Goal**: Domenico at Stile Car receives a real, complete BMW X3 dossier and a personalized Day 1 WhatsApp message
**Depends on**: Phase 3
**Requirements**: OUT-01, OUT-02, OUT-03, OUT-04
**Success Criteria** (what must be TRUE):
  1. Dossier for BMW X3 xDrive20d 2022 (listing_id: autoscout24_de_b0d65f095510) is generated with all real verified data — no placeholders, no invented numbers
  2. Day 1 WhatsApp message for Domenico (NARCISO archetype) is max 5 lines, references the specific vehicle with real numbers, ends with a closed question
  3. WA daemon at 192.168.1.2:9191 is operational and message (with dossier attachment) is confirmed sent
  4. CRM entry for Stile Car is updated with outreach timestamp and Day 1 status
**Plans**: 1 plan

Plans:
- [ ] 04-01-PLAN.md — Day 1 NARCISO outreach script: verify dossier, send WA message, update CRM

### Phase 6: AMBRA Agent — WA Autonomo
**Goal**: wa-daemon + response-analyzer diventano un agente WA indistinguibile da umano (benchmark AMBRA: 90-95%), con anti-ban layer e architettura transport-agnostic
**Depends on**: Phase 4
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05
**Success Criteria** (what must be TRUE):
  1. wa-daemon invia 2-3 messaggi separati con typing indicator e 3-8s delay tra ognuno — MAI blocco unico
  2. response-analyzer genera risposte con imperfezioni umane (minuscole, intercalari, spazi irregolari) calibrate per archetipo
  3. Buffer debounce 15s per-dealer aggrega messaggi multipli in un'unica risposta — MAI risposte separate a burst
  4. Knowledge base ARGOS (FAQ servizio, costi, tempi, trasporto, garanzie, obiezioni) iniettata nel prompt LLM
  5. Anti-ban layer attivo: typing indicator proporzionale, recording indicator pre-vocale, delay log-normale, onWhatsApp check, business hours enforcement
**Plans**: 5 plans

Plans:
- [ ] 06-01-PLAN.md — Multi-messaggio con delay + typing indicator (endpoint /send-multi)
- [ ] 06-02-PLAN.md — Prompt Haiku con imperfezioni umane + output JSON multi-msg
- [ ] 06-03-PLAN.md — Debounce 15s multi-input per-dealer con hard cap 45s
- [ ] 06-04-PLAN.md — Knowledge base ARGOS + iniezione nel prompt LLM
- [ ] 06-05-PLAN.md — Anti-ban layer: typing/recording indicator, delay log-normale, onWhatsApp check

## Operations Debt

Issues non legati a feature nuove ma a operations/scheduling code esistente.

- [ ] **OPS-01 — Scheduler market_intelligence.py orfano** (rilevato 2026-05-21, brief mattutino S183)
  - Root cause `market_listings=0` e `market_price_changes=0` in `dealer_network.sqlite`
  - `tools/scrapers/market_intelligence.py` esiste e funziona, ma NON è mai schedulato:
    - LaunchAgent `wa-intelligence/launchd/com.argos.scheduler.plist` punta a path utente sbagliato (`gianlucadistasi` non `macbook`) e DB sbagliato (`.duckdb` non `.sqlite`) → broken, non caricato in launchd
    - `ecosystem.config.js` PM2 gestisce solo wa-daemon, tg-bot, cf-monitor → market_intelligence non incluso
    - crontab utente vuoto per market
    - `ecosystem.market.config.js` referenziato nel docstring ma NON esiste sul filesystem
  - Fix raccomandato: aggiungere 4° app a `ecosystem.config.js` con `cron_restart: '0 5 * * 1-5'` (lun-ven 5am, allineato a docstring riga 14 di market_intelligence.py). PM2 supporta cron_restart nativo, riusa SHARED_ENV già configurato con ARGOS_DB_PATH corretto.
  - Cleanup: rimuovere LaunchAgent `com.argos.scheduler.plist` broken (path utente hardcoded, formato DB obsoleto).

- [ ] **OPS-02 — invisible_playwright candidato se bot detection emerge** (segnalato tool-scout 2026-W21)
  - Repo `feder-cr/invisible_playwright` (MIT, 328⭐) — stealth Firefox drop-in Playwright replace che passa bot detection test
  - Attivare SOLO se dopo fix OPS-01 lo scraper market_intelligence inizia a vedere HTTP 403/429/Cloudflare challenges su autoscout24/mobile.de
  - `base_scraper.py` ha già backoff 403/429 e `resilient_fetcher.py` ha 5 backend fallback — se basta, non introdurre nuova dipendenza
  - Trigger esplicito per migration: ≥2 portali con block-rate >20% su 7gg consecutivi

## Progress

**Execution Order:**
Phases 1→2→3→4 already done (tech foundation). Post-S11d: 0 (credibility) → 5 (outreach protocol) → 6 (AMBRA autonomy). Phase 0 added retroactively as pre-req for any Wave 1 outreach reale.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Credibility Infrastructure | 0/TBD | Not started (S165 ARGOS) | - |
| 1. Validazione Tool Gratuiti | 4/4 | Complete | 2026-03-24 |
| 2. Schema DB + Detail Enricher | 2/2 | Complete | 2026-03-24 |
| 3. ARGOS GRADE + PDF Enterprise V2 | 2/2 | Complete | 2026-03-25 |
| 4. Primo Outreach Stile Car | 0/1 | Not started | - |
| 5. Outreach Protocol 4-Layer | 0/TBD | Not started (S166-S168) | - |
| 6. AMBRA Agent — WA Autonomo | 0/5 | Not started | - |
