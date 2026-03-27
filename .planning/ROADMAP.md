# Roadmap: ARGOS — Dal VIN Reale al Dossier Reale

## Overview

Four phases take ARGOS from hypothesis to first dealer contact. Phase 1 validates every free tool against real VINs before any code is written around them. Phase 2 builds the data infrastructure that persists enriched listings and images. Phase 3 assembles ARGOS GRADE and the enterprise PDF that makes the dossier credible. Phase 4 generates the BMW X3 dossier for Stile Car and sends the first Day 1 message to Domenico.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Validazione Tool Gratuiti** - Test every free data source against real VINs from DuckDB (completed 2026-03-24)
- [x] **Phase 2: Schema DB + Detail Enricher** - Build DuckDB vehicle_listings/images schema and V2 enricher (completed 2026-03-24)
- [x] **Phase 3: ARGOS GRADE + PDF Enterprise V2** - Grading system A-E and dossier generation with real data (completed 2026-03-25)
- [ ] **Phase 4: Primo Outreach Stile Car** - Generate BMW X3 dossier and send Day 1 message to Domenico
- [ ] **Phase 6: AMBRA Agent — WA Autonomo** - Transform wa-daemon into human-like autonomous agent (multi-msg, imperfezioni, debounce, knowledge base, anti-ban)

## Phase Details

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

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Validazione Tool Gratuiti | 4/4 | Complete | 2026-03-24 |
| 2. Schema DB + Detail Enricher | 2/2 | Complete | 2026-03-24 |
| 3. ARGOS GRADE + PDF Enterprise V2 | 2/2 | Complete | 2026-03-25 |
| 4. Primo Outreach Stile Car | 0/1 | Not started | - |
| 6. AMBRA Agent — WA Autonomo | 0/5 | Not started | - |
