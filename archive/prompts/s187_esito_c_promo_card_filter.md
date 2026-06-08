# S187 — ESITO C confermato: promo_card_detector + upstream_slide_filter

**Esito S186 (2026-05-23)**: STEP 0-bis chiuso con verdict **C**.
PoC plate-detector EU **CHIUSO definitivamente**.

## Evidence S186 (pre-filter Vision OCR su 35 foto + gate visivo 5)

| File | Vision candidate | Classificazione |
|------|------------------|-----------------|
| `428982234890_02` | "ME XC 573E)" 0.30 | TARGA_VERA (render BMW retro) |
| `428982234890_00` | "M UJ769E" 0.50 | SLIDE_MARKETING ("BILDER FOLGEN") |
| `7baf14b1aac8_00` | "M XC 573E" 0.30 | SLIDE_MARKETING (Wernecke + BMW PS) |
| `19bc9cf651e5_03` | "20 m" 0.50 | CARTELLO_PROMO (Carmax banner) |
| `39d64c65e9de_00` | nessuna | CARTELLO_PROMO (Baum fail-case R1) |

**TARGA_VERA totali: 1/35** < soglia 3 → ESITO C.

**Pattern strutturale (vincolo 11 trigger)**:
- 4/5 top-candidate Vision = slide marketing/cartello dealer
- 30/35 zero candidate = foto auto fisiche senza targa visibile o sfocata
- Il problema operativo NON è "Vision non vede targhe" — è "i dealer DE caricano slide BMW Premium Selection + cartello promo in posizione targa fisica"
- R1 Koushim NO-GO (memory `poc_yolo_plate_round1_koushim_nogo.md`) + S185 1/6 + S186 1/35 = **trend lineare bias confermato**

## S187 piano (raccomandazione singola motivata, vincolo 3)

### Workstream P0 — `upstream_slide_filter` a scraping time (BACKLOG #1 promosso)

**Obiettivo**: skip slide marketing AS24 (BMW Premium Selection / Bilder folgen / Garantie /
Spar-Deal / banner finanziamento) **prima** del DB insert in `vehicle_images`.

**Where**: `tools/scrapers/autoscout_scraper.py` — funzione/punto dove le URL
immagine vengono inserite in `vehicle_images`.

**How** (proposta, da validare con architect agent S187):
1. Heuristic 1 (fast, no OCR): URL/CDN path pattern AS24 catalog vs dealer-upload.
   AS24 catalog renders hanno path differente da foto dealer (verificare con campione 10 listing).
2. Heuristic 2 (Vision OCR su 1° foto solo, lazy): se text-density >threshold E include
   `["BMW PREMIUM SELECTION", "BILDER FOLGEN", "PREMIUM SELECTION", "GARANTIE", "Spar-Deal",
   "finanzieren ab", "Aktionszins", "Abbildung ähnlich"]` → flag `is_promo_slide=true`.
3. Skip insert se `is_promo_slide=true`.

**Cost**: Vision OCR locale macOS = €0 (S163 stack già operativo). Zero impatto budget.

**Pre-flight obbligatorio**: campione 20 listing su 3 dealer DE diversi, manuale review
hit-rate (true skip vs false skip foto vera).

### Workstream P1 — `promo_card_detector` Stage 3 sanitizer

**Obiettivo**: rilevare cartello dealer/promo *in posizione targa* su foto auto fisiche
(es. Baum: cartello "PREMIUM SELECTION / Garantiert V" al posto targa anteriore;
Carmax: banner sotto + logo a SX auto, ricorrenza multi-posizione testo dealer).
Quando detected → coperture watermark + flag `manual_review=true`.

**Nota da gate visivo Luke S186**: testo/logo dealer ricorre in **più posizioni** sulla
stessa foto (Carmax: banner basso + watermark laterale). `promo_card_detector` deve
cercare ricorrenza pattern, non solo singolo rettangolo. Aumenta confidence detection
quando stesso brand-token compare 2+ volte.

**Where**: `src/cove/image_sanitizer.py` Stage 3 (post Vision text-region detection).

**How** (proposta):
- Sub-rectangle detection nella regione targa attesa (centro-basso paraurti anteriore o
  retro), aspect ratio ~4:1 stretto, contrast alto vs auto body.
- Se sub-rect detected E Vision OCR su quel sub-rect rileva text con keywords promo
  ("BMW PREMIUM SELECTION", "BILDER FOLGEN", "GARANTIERT", logo dealer detected) →
  classify as `promo_card`.
- Coverage watermark + metadata `plate_detection_status=promo_card_detected`.

**Skip strutturale**: NO YOLO plate-detector EU. Conferma S186.

### Workstream P2 — Dossier metadata

**Obiettivo**: dossier `tools/scripts/pdf_generator_enterprise.py` aggiunge campo
`targa: N/A (cartello dealer detected)` o `targa: N/A (foto AS24 catalog)` con
`manual_review=true` se P0/P1 detected promo/card.

**Where**: `pdf_generator_enterprise.py` template + DB schema `dossier_metadata`.

## Vincoli S187 hard

1. **NO integrazione plate-detector EU** (ESITO C definitivo, no comeback).
2. **Backup datato** prima patch `autoscout_scraper.py` + `image_sanitizer.py` +
   `pdf_generator_enterprise.py`.
3. **UAT su 30+ foto post-integration PRIMA di ring #4 verde** (memory
   `feedback_smoke_test_not_uat_gate.md`). NO production-ready su 5-8 sample.
4. **code-reviewer agent invocato pre-commit** su ogni patch P0/P1/P2.
5. **Day 1 Stile Car (2026-06-03, ~10gg)** NON gate-flippa su patch P0/P1 verdi —
   solo su UAT 30+ foto E2E (scrape→sanitizer→dossier).
6. **architect agent OBBLIGATORIO** prima implementazione P0 (decisione strutturale
   scraping pipeline). Delegation-first regola #0.

## Time-box S187 suggerito

- P0 design (architect) + pre-flight 20 listing: max 30 min
- P0 implementazione + UAT 20 listing: max 60 min
- P1+P2 differiti a S188+ se P0 verde

## Riferimenti

- Memory: `poc_yolo_plate_round1_koushim_nogo.md`, `s185_poc_eu_step0_interrupted_handoff_s186.md`
- DECISIONS: D-32 sanitizer (closure in arrivo via ESITO C path)
- File pool S186: `/tmp/s185_inspect/` (35 jpg ereditati)
- Pre-filter script: `/tmp/s185_vision_prefilter.py`
- Pre-filter JSON output: `/tmp/s185_prefilter.json`

## ⚠️ Bias-aware self-check (vincolo 4)

**Cosa potrebbe rompere S187 piano a 30/60/90gg**:
- (30gg) Heuristic 1 URL/CDN path pattern AS24 cambia → falsi negativi slide
- (60gg) `promo_card_detector` Stage 3 over-trigger su auto fisiche con riflessi su
  paraurti → falsi positivi coverage targhe vere
- (90gg) UAT 30 foto non rappresentativa di varianza dealer Sud Italia post-Day 1 →
  drift hit-rate
- **Dove sovradimensiono**: P1 sub-rectangle detection può essere over-engineered. Path
  più semplice: flag `manual_review=true` SEMPRE quando Vision rileva keyword promo
  in foto e Luke approva 1-click via dashboard.

**Assunzione nascosta da validare in S187**: il 30/35 zero candidate sono effettivamente
foto auto vere senza targa visibile. Da verificare: sample manuale 10 file zero-candidate
per confermare (Read multimodal batch piccolo).
