# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S128 — 2026-04-16

---

## S128 COMPLETATA — Phase 2 Minima Implementata + E2E PASS

### Cosa è stato fatto

7 componenti Phase 2 minima implementati e testati:
1. **SQL schema** — `opt_out` + `validation_log` + `lia_log` su iMac dealer_network.sqlite
2. **`signal_event.py`** — oggetto unificato (anchor esatto, GATE-ICP-001, SIGNAL-FRESH-001, opt-out GDPR)
3. **GATE-ICP-001** — env vars `ARGOS_ICP_MIN_RATIO`/`ARGOS_ICP_CORE_RATIO` (default 0.20/0.30)
4. **SIGNAL-FRESH-001** — env var `ARGOS_SIGNAL_TTL_DAYS` (default 14)
5. **Rule L4** — 6 nuove rule in `validator.py`: CRED-SEQUENCE-001, NO-OFFER-DAY1-001, TEMPLATE-EXACT-RENDERING-001, LEX-SELFAUTH-001, LEX-SCARCITY-001, BRAND-SELFPROMO-001
6. **`hypothesis_routing.json`** — 9 archetipi → 1 ipotesi specifica ciascuno
7. **`batch_generator.py`** — genera candidati + invia digest Telegram

**Test results:** 37/37 validator PASS | 6/6 E2E checkpoint su TEST_FOUNDER PASS
**Digest Telegram inviato.** Nessun dealer reale contattato.

### File creati/modificati
```
.claude/skills/human-first-outreach/scripts/signal_event.py    ← NUOVO
.claude/skills/human-first-outreach/scripts/batch_generator.py ← NUOVO
.claude/skills/human-first-outreach/assets/hypothesis_routing.json ← NUOVO
wa-intelligence/validator.py                                   ← ESTESO (+6 rule L4, log_to_db)
dealer_network.sqlite (iMac)                                   ← +opt_out cols, +validation_log, +lia_log
```

---

## S127 COMPLETATA — ARCHITETTURA `human-first-outreach` SATURATA

### Cosa è stato fatto

Sessione interamente architetturale. Tre round di critica incrociata tra Claude Code locale
e Claude Web (sessione separata con accesso a research 2026 esterna).

**Risultato:** architettura della skill `human-first-outreach` portata a livello enterprise-grade.
Nessun codice scritto. Nessun dealer contattato. Pipeline non ancora testata E2E.

### Decisioni architetturali chiave (tutte in memory/MEMORY.md)

**G1-G6 riviste:** G4 cambiato completamente (aged inventory, non new listing), G5 wording GDPR-compliant con {data_source}, G1 con 3 campi audit aggiuntivi.

**Phase 2 minima — 7 componenti (scope implementazione S128):**
1. `signal_event` unificato (G4+G5+G1 in un oggetto)
2. `GATE-ICP-001` con env vars `ARGOS_ICP_MIN_RATIO` / `ARGOS_ICP_CORE_RATIO`
3. `SIGNAL-FRESH-001` con env var `ARGOS_SIGNAL_TTL_DAYS`
4. `CRED-SEQUENCE-001` + `NO-OFFER-DAY1-001`
5. `TEMPLATE-EXACT-RENDERING-001`
6. Hypothesis routing table (9 archetipi → 1 ipotesi specifica ciascuno)
7. Batch generation + digest Telegram 08:00

**Phase 3 (dopo 30 messaggi shadow reali):** L5 LLM-as-judge, mv_market_insights,
geographic routing, SEQ-NOEXIT, TONE rules, CONTENT-NUMBERS-SOURCED-001.

**Quality gate irrevocabile:** nessun outreach finché E2E test non passa su TEST_FOUNDER
con dati CoVe reali, immagini sanitizzate, numeri verificabili su cove_tracker.duckdb.

### Stato pipeline

- **NESSUN dealer contattato**
- WA daemon: UNREACHABLE all'avvio S127 (iMac offline — verificare in S128)
- `conversations` manca ancora `opt_out` e campi accessori

---

## S129 DEVE INIZIARE DA

**Phase 2 minima è COMPLETA.** Il prossimo step è il **primo shadow mode su dealer reale.**

1. **Autorizzazione founder richiesta** — decidere quale dealer reale avviare in shadow mode
   Candidati (score > 7.5, persona noto): Car Plus (RAGIONIERE), Stile Car (RELAZIONALE), Sa.My. Auto (TECNICO)
2. **Signal reale da AutoScout24** — scraper `tools/on_demand_runner.py` per ottenere `days_on_market` reale del dealer scelto
3. **Stock reale per GATE-ICP-001** — query cove_tracker.duckdb o scrape stock del dealer
4. **Primo messaggio shadow** — batch_generator con dealer reale, dry-run prima, Luke approva dal Telegram digest
5. **Invio via wa-daemon** — solo dopo approvazione esplicita Luke

**NON fare in S129 (Phase 3):** L5, mv_market_insights, geographic routing, SEQ-NOEXIT.

**Signal su cui fare scrape per il dealer scelto:**
- AutoScout24.it → cerca dealer per città/nome → rileva auto stagnanti (>60gg, invariate)
- Comanda `python3 tools/on_demand_runner.py --dealer "Car Plus" --budget 50000 --marca BMW`

---

## File chiave

```
wa-intelligence/validator.py                        ← estendere con nuove rule L4
wa-intelligence/wa-daemon.js                        ← interfaccia /send
src/cove/image_sanitizer.py                         ← sanitizzazione immagini PDF
tools/scripts/pdf_generator_enterprise.py           ← generatore PDF da aggiornare
data/training/archetypes_v2.json                    ← 10 archetipi (Phase 2 usa top 9)
dealer_network.sqlite (iMac)                        ← DB outreach + conversations
cove_tracker.duckdb (iMac)                          ← dati CoVe per signal_event
/Users/macbook/Downloads/HANDOFF_human-first-outreach_skill.md  ← handoff originale skill
```
