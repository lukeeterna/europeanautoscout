# S173 ARGOS — CCIAA harvest target D-28 + AMBRA P3 code retune (parallel, no founder gate)

**Sessione precedente**: S172 chiusa VERDE — P0 AMBRA-AUDIT.md + P1 RESEARCH-MICRODEALER-COMMISSIONE.md scritti. Context 64% → handoff strutturato.

**Finding strutturale dominante S172** (3 evidenze convergenti): target D-28 micro-dealer commissione P.IVA forfettaria è **digitalmente silente**. Tutti i canali pubblici testati (Telegram, FB Groups, Reddit/forum, AS24 directory) hanno ROI basso. Path validato per intercettarli = CCIAA ATECO database + mystery shopper Layer 2 fisico.

---

## LEGGI PRIMA

- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/AMBRA-AUDIT.md` (10 sezioni, gap-to-D27/D28 con file:line)
- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/RESEARCH-MICRODEALER-COMMISSIONE.md` (4 agent results + Agent 4 AS24 list)
- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/DECISIONS.md` (D-26/D-27/D-28 canonical)

---

## ROADMAP CTO S173 → S176

| Sessione | Scope | Founder gate | Effort | Gating per |
|----------|-------|--------------|--------|------------|
| **S173** | CCIAA harvest + AMBRA P3 code retune + Layer 3 mocks | NO | ~2h | sblocca S174 + S175 |
| S174 | wa-daemon duplicate verify + V6 messaggi 3+3 founder pick | SI fisico TEST_FOUNDER | ~1h | sblocca S176 |
| S175 | Mystery shopper Layer 2 pilot fisico (3 dealer) | SI founder 1-2gg | ~2gg founder | sblocca calibration TARGET_LEXICON |
| S176 | E2E 15-step TEST_FOUNDER handoff Layer 2→3 | SI founder fisico | ~2h | **Day 1 reale dealer** |

---

## PIANO S173 (3 task parallel-ish)

### Task A — CCIAA harvest target list D-28 (~45min)

**Path**: registroimprese.it Telemaco gratuito OR camera commercio APIs pubbliche.

Verifica fattuale richiesta (vincolo #1):
1. WebFetch `https://www.registroimprese.it` per individuare endpoint search free-tier
2. Filtro target:
   - Codice ATECO **45.11.01** (commercio autoveicoli leggeri)
   - Regione: Puglia, Campania, Calabria, Basilicata (D-14 wave 1)
   - Forma giuridica: ditta individuale + s.r.l.s. + s.n.c. (esclude S.p.A. = target wrong)
   - Anno costituzione: ≥2018 (esclude family business decennali multi-stock)

Output: `data/s173_cciaa_target_d28.csv` con colonne `[denominazione, partita_iva, codice_ateco, regione, provincia, comune, forma_giuridica, anno_costituzione, regime_iva_dichiarato_if_visibile]`.

**Fallback se Telemaco free-tier non sufficiente**:
- `infocamere.it` pubblico → directory ditte ATECO
- `ufficiocamerale.it` aggregatore third-party
- Pagine gialle filtro categoria "autosaloni" (signal più povero ma free)

**Target dimensione output**: 50-200 dealer raw. Ranking interno: HIGH (s.r.l.s. + ditta individuale post-2018) / MEDIUM (s.r.l. piccola 2015+) / LOW (resto).

### Task B — AMBRA P3 code retune (~45min)

Modifiche concrete da AMBRA-AUDIT.md sezione 6:

#### B1. `wa-intelligence/response-analyzer.py`

- **Line 305-353 PROMPT_MODULES**:
  - Aggiungere variante `identity_post_handoff` per Layer 3 (dealer ha già sentito di Argos via Layer 2 mystery shopper)
  - Condizionalizzare ban "ARGOS" parola: `if handoff_source != 'mystery_shopper'`
  - Nuovo modulo `<TARGET_LEXICON>` (placeholder, sarà popolato S175 da interviste offline)
- **Line 356 `build_system_prompt(archetype, cls_type)`**: aggiungere param `handoff_source='cold'` retrocompat
- **Line 375 `ResponseValidator`**: passare context `post_handoff` al validator → check #2 banned "ARGOS" condizionale
- **Line 1353 `auto_approve_and_send`**: leggere `deal.handoff_source` da schema deal, propagare a build_system_prompt

#### B2. `wa-intelligence/argos_knowledge_base.md`

- Sezione COSTI: aggiungere sotto-sezione **"Modello commissione"** (variante D-28 — fee €800-1.200 trasferita su cliente finale + commissione micro-dealer trattenuta)
- Sezione FISCALITA': aggiungere sotto-sezione **"Regime forfettario"** (esenzione reverse charge TD17)
- Sezione OBIEZIONI: riscrivere obiezione "Ho già fornitore" → "Lavoro su richiesta cliente, non tengo stock"
- Sezione GARANZIA: chiarire money-back ARGOS-funded (D-15), NON dealer-funded

#### B3. `wa-intelligence/state_machine.py`

- Aggiungere flag `is_mystery_primed: bool` in deal record (NON nuovo stato FSM — evitare blast radius, vedi critica strutturale AMBRA-AUDIT sez 8.4)
- Helper `dealer.is_post_handoff() -> bool` legge il flag

#### B4. Schema deal record

- Migration additive: `ALTER TABLE deals ADD COLUMN handoff_source TEXT DEFAULT 'cold' CHECK (handoff_source IN ('cold', 'mystery_shopper', 'referral'))`
- Backfill default `'cold'` per deal pre-S173

### Task C — Layer 3 unit mocks (~30min)

Nuovo file `tests/test_ambra_layer3.py` con 3 conversation mocks (specifica AMBRA-AUDIT sez 6.3):

1. **Mock 1 — Reactive identity**: dealer scrive "ah sì Argos, mi ha detto X". AMBRA deve rispondere con identity post-handoff (NO self-introduction, NO ban "ARGOS").
2. **Mock 2 — Skeptical objection**: dealer "boh non mi convince". AMBRA usa obiezione "non mi fido" + KB micro-dealer.
3. **Mock 3 — Cost question**: dealer "quanto costa". AMBRA usa COSTI variante commissione (NO margine, NO €4-7k premium).

Validation: ogni mock check (a) no "ARGOS" presente if handoff_source=cold, OK if mystery_shopper, (b) lessico target presente (almeno 2 termini D-28), (c) ResponseValidator pass.

---

## VINCOLI S173

- **#5 zero-cost**: CCIAA Telemaco free-tier o alternativa free
- **#6 mai PARTIAL**: se Task A blocca, deliverable parziale = CCIAA empty + Task B+C completi
- **#7 context budget**: `/context` ogni 5 turni, sopra 60% chiudi
- **#1 verifica fattuale**: registroimprese.it endpoint reali, no inventati
- **#13 pre-action check**: D-28 + D-27 cite in proposte
- **CLAUDE.md ARGOS**: NO nuove skill/agent — TaskC test mocks è dentro pipeline esistente
- **TEST_FOUNDER <TEST_FOUNDER_NUM>**: NON inviare nulla in S173 (no founder gate richiesto)

---

## OUTPUT ATTESI S173

1. `data/s173_cciaa_target_d28.csv` — 50-200 dealer Sud forfettari pre-classificati
2. `wa-intelligence/response-analyzer.py` — patch B1 commit
3. `wa-intelligence/argos_knowledge_base.md` — patch B2 commit
4. `wa-intelligence/state_machine.py` — patch B3 commit
5. Schema migration `migrations/s173_handoff_source.sql`
6. `tests/test_ambra_layer3.py` — 3 mocks passanti
7. Aggiornamento `AMBRA-AUDIT.md` sezione 6 → marcare "P3 completed S173"
8. Commit unico `S173 — AMBRA P3 retune + CCIAA target harvest D-28` su master

---

## CHIUSURA S173

Se tutti 7 output verdi → MEMORY entry sintetica + handoff S174.

Se Task A fallisce (CCIAA gated/blocked) → Task B+C verdi, Task A defer S174 con path alternativo verificato (pagine gialle / scraping Subito profili impresapiu / OpenCorporates EU free-tier).

Se context >60% durante S173 → chiudi con handoff S173-bis (lavoro residuo).