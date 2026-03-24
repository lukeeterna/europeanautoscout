# ARGOS Automotive — Dal VIN Reale al Dossier Reale

## What This Is

ARGOS Automotive e' un servizio B2B di vehicle scouting EU→IT per concessionari family-business del Sud Italia. Trova veicoli premium (BMW/Mercedes/Audi/Porsche) su 73 portali EU, li verifica con scoring bayesiano (CoVe), e li propone ai dealer con dossier completo e success fee €800-1.200. Questo milestone valida la pipeline end-to-end con dati reali prima del primo contatto dealer.

## Core Value

Il dealer riceve un dossier con dati che non trova da nessun'altra parte — verificati, reali, e pronti per la rivendita. Se anche UN dato e' inventato, il sistema non vale nulla.

## Requirements

### Validated

- ✓ Scraper 28 portali EU E2E — existing (tools/scrapers/)
- ✓ CoVe Engine v4 scoring bayesiano — existing (src/cove/cove_engine_v4.py)
- ✓ Fraud detection — existing (src/cove/fraud_flags.py)
- ✓ Market Price Index + ADAC — existing (src/cove/market_price_index.py, adac_price_reference.py)
- ✓ CRM dealer 12 target — existing (tools/dealer_crm.py, dealer_network.sqlite)
- ✓ PDF generator enterprise — existing (tools/scripts/pdf_generator_enterprise.py)
- ✓ WA daemon — existing (wa-intelligence/wa-daemon.js)
- ✓ Dashboard — existing (wa-intelligence/dashboard/app.py)
- ✓ Landing page GRUPPO EU — existing (landing/, argos-automotive.pages.dev)
- ✓ Messaging V2 per archetipo — existing (research/s73_messaging_v2.md)

### Active

- [ ] Validazione tool gratuiti con VIN reali (freevindecoder, car-recalls, KBA, DAT consumer, garanzia BMW)
- [ ] Schema DB vehicle_listings + vehicle_images in DuckDB
- [ ] Detail Enricher V2 che salva dati verificati
- [ ] ARGOS GRADE A-E basato su dati reali
- [ ] PDF Enterprise V2 con foto reali, grading, 7 criteri verificati
- [ ] Dossier BMW X3 2022 reale per Stile Car
- [ ] Primo messaggio Day 1 a Domenico (Stile Car) con dossier allegato

### Out of Scope

- DEKRA/officina fisica — serve dopo 3-5 deal completati, non ora
- TCO calculator IT — nice-to-have, non bloccante per primo outreach
- Alert stock personalizzato — richiede dealer attivo, non abbiamo ancora il primo
- Garanzia convenzionale partnership — troppo presto
- SilverDAT/Schwacke API — viola guardrail zero costi
- Facebook pagina — non bloccante per primo deal
- Secondo/terzo dealer — prima validare con Stile Car

## Context

- 83 sessioni di sviluppo completate (S1→S82)
- 6 deep research globali S82: piattaforme mondiali, grading systems, dealer tools, inspection standards, strumenti gratuiti, DEKRA/DAT
- Veicolo gia' identificato: BMW X3 xDrive20d 2022, 50.058km, €34.140 DE, margine ~€2.948, confidence 0.84, CLEAN
- listing_id: autoscout24_de_b0d65f095510
- Dealer target: Stile Car (Orta Nova FG), Domenico, archetipo NARCISO, WA 333-4254654
- NESSUN tool gratuito e' stato mai testato con VIN reale — tutti i dati nelle research sono ipotesi
- WA daemon potenzialmente offline (smartphone in ripristino S82)

## Constraints

- **Budget**: ZERO — tutto deve essere gratuito o gia' pagato. Nessuna API a pagamento.
- **Infra**: iMac (ssh 192.168.1.2) + MacBook locale. Python 3.13, Node v22.
- **DB**: DuckDB (cove_tracker.duckdb) + SQLite (dealer_network.sqlite)
- **CoVe**: cove_engine_v4.py NON MODIFICARE — solo invocare
- **Tempo**: Il primo outreach deve partire il prima possibile. Ogni giorno perso e' un giorno in cui il listing BMW X3 puo' essere venduto.
- **Credibilita'**: Nel Sud Italia non c'e' una seconda chance. Il primo dossier DEVE essere impeccabile.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Validare tool gratuiti PRIMA di costruire | Evita costruire su ipotesi false | — Pending |
| ARGOS GRADE A-E (non numerico) | Standard BCA/NAAA adattato, nessuno in Italia lo ha | — Pending |
| Solo dati verificati nel dossier | Un dato inventato = credibilita' persa per sempre | — Pending |
| Stile Car come primo dealer | NARCISO, gia' importa EU, piu' ricettivo a novita' | — Pending |
| Success fee (no upfront) | Unico differenziatore vs tutti i competitor | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-24 after initialization*
