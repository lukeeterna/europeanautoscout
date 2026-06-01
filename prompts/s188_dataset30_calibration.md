# S188 — Calibrazione H2 su dataset 30 + decisione pivot P0

## Contesto da S187 (consolidato)

**Verdetto S187**: piano P0 `upstream_slide_filter` architect H2-only **strutturalmente non implementabile** su sample 10 (recall slide 50%, precision 67%, F1 0.57). Stessa keyword (`BMW PREMIUM SELECTION`, `BMW Gebrauchte Automobile`) appare sia in SLIDE sia in AUTO → discriminazione text-only impossibile.

**Findings architect (correzioni prompt S187 originale)**:
1. File target NON `tools/scrapers/autoscout_scraper.py` ma `src/cove/detail_enricher_v2.py:454-462`
2. DB NON SQLite ma DuckDB `src/cove/data/cove_tracker.duckdb`, tabella `vehicle_images`
3. H1 URL/CDN pattern scartato (tutte AS24 identiche `prod.pictures.autoscout24.net/listing-images/...`)
4. Safety net `image_sanitizer.py:947-958` `MIN_OUTPUT_SIZE_RATIO=0.20` cattura già slide pure

**Decisione Luke S187 close**: dataset 30 + filtri shared per validare statisticamente F1=0.57 prima di abortire P0.

## Storage persistente

- `/Volumes/MontereyT7/argos-poc/S187/inputs/` — 29 jpg numerati `01_…` → `30_…` (1 listing senza immagine valida)
- `/Volumes/MontereyT7/argos-poc/S187/vision_output/preflight.json` — Vision OCR + density per ognuno
- `/Volumes/MontereyT7/argos-poc/S187/preflight.py` — script eseguibile via `~/.argos-sanitizer-venv/bin/python3`
- `/Volumes/MontereyT7/argos-poc/S187/_archive_run_10/` — run 10-sample originale archiviato

**Anti-pattern fixed**: artefatti PoC ARGOS in `/Volumes/MontereyT7/argos-poc/S{NNN}/` (T7 persistente), NON `/tmp/` (cleared at reboot). BACKLOG #S187-1.

## Rubrica filtri shared (Luke + Claude usano la stessa)

### SLIDE (tutte true)
- Auto NON è soggetto principale oppure è ritagliata/inserita come elemento grafico
- Testo grosso al centro/alto = titolo di brochure/card
- Sfondo NON realistico (gradient, white-box studio finto, grafica brand)
- Logo certified (BMW Premium Selection, Hyundai Promise, Junge Sterne, Das WeltAuto, Audi Approved, Mercedes-Benz Certified) usato come ELEMENTO GRAFICO dominante, NON come watermark

### AUTO (tutte true)
- Auto è soggetto principale
- Sfondo realistico (showroom, piazzale, garage, strada, anche se editato/cropped/white-replaced)
- Eventuali testi/loghi dealer = watermark (piccoli, in angolo, OVERLAY sovrapposto)
- Brand certified eventualmente presente come testo overlay, non card

### AMBIGUA
- Solo se neanche un umano riesce a decidere. Usare raramente.

**Regola d'oro**: la differenza SLIDE vs AUTO-con-watermark è **dove sta il soggetto**. Se l'auto è la prima cosa che vedi = AUTO (anche con watermark grosso). Se vedi prima il titolo/grafica brand e l'auto è secondaria/inserita = SLIDE.

## Tabella 29 sample (auto-class corrente)

| # | listing_id | density | auto-class | testo Vision (sample) |
|---|---|---|---|---|
| 1 | autoscout24_de_2db4ffc7c44a | 0.054 | PROMO_HIT | '10' |
| 2 | autoscout24_de_66fa1cab6e74 | 0.085 | NO_PROMO | 'AUTOHAUS REBMANN GMBH' |
| 3 | autoscout24_de_bbb7cc13df01 | 0.037 | NO_PROMO | 'emobie' (garbled) |
| 4 | autoscout24_de_853516cff2ac | 0.016 | NO_PROMO | 'icicara' |
| 5 | autoscout24_de_2d122ffe2231 | 0.094 | PROMO_HIT | 'Autohaus Müller GmbH & Co. KG' |
| 6 | (no image) | — | ERROR | — |
| 7 | autoscout24_de_6173fa3cd781 | 0.026 | PROMO_HIT | 'CLOPPENBURG' |
| 8 | autoscout24_de_2107712cae21 | 0.028 | PROMO_HIT | 'BMW PREMIUM SELECTION' |
| 9 | autoscout24_de_24b73f603680 | 0.000 | ZERO | (empty) |
| 10 | autoscout24_de_2dbabd12692f | 0.049 | NO_PROMO | 'GEMO.' |
| 11 | autoscout24_de_1ce5e0ab6c1a | 0.026 | NO_PROMO | 'BMW Gebrauchte Automobile' |
| 12 | autoscout24_de_7366dfce8d2b | 0.010 | NO_PROMO | 'BMW Gebrauchte Automobile' |
| 13 | autoscout24_de_2f25e7642d97 | 0.051 | PROMO_HIT | 'Autohaus Schmidt' |
| 14 | autoscout24_de_aec2e66ca73f | 0.031 | NO_PROMO | 'GRUPPE' |
| 15 | autoscout24_de_894a3261231e | 0.033 | NO_PROMO | 'Autohaus Isernhagen' |
| 16 | autoscout24_de_85f254a602a0 | 0.032 | NO_PROMO | 'KAMUX 6' |
| 17 | autoscout24_de_2b651feb3853 | 0.073 | NO_PROMO | 'CARMAX' |
| 18 | autoscout24_de_ea03175104f5 | 0.035 | NO_PROMO | 'BMW:' |
| 19 | autoscout24_de_59e1b2f41181 | 0.006 | NO_PROMO | 'AUTOHAUS ROYAL' |
| 20 | autoscout24_de_546199951ab3 | 0.005 | NO_PROMO | 'Sportline' |
| 21 | autoscout24_de_be041c83ae1b | 0.001 | NO_PROMO | 'a Moletal s' |
| 22 | autoscout24_de_3e00f97ac603 | 0.057 | NO_PROMO | 'AnSeenG' |
| 23 | autoscout24_de_ace2da9ad09e | 0.038 | NO_PROMO | 'AUTOHAUS RANALDI' + 'Hyundai Promise' |
| 24 | autoscout24_de_1f68718c0ab8 | 0.029 | NO_PROMO | 'Autoland Celle' |
| 25 | autoscout24_de_f95a27793875 | 0.034 | NO_PROMO | 'autohaus briem' + 'ein starkes team' |
| 26 | autoscout24_de_6a7ff027bc52 | 0.023 | NO_PROMO | 'BMW Gebrauchte Automobile' + 'Freude erleben' |
| 27 | autoscout24_de_de1bba38e1ea | 0.000 | ZERO | (empty) |
| 28 | autoscout24_de_b9ff933faf3a | 0.065 | NO_PROMO | 'Autohaus DRESSMAN GmbH' |
| 29 | autoscout24_de_9f222b8d5e8a | 0.041 | NO_PROMO | 'INTERBERGER Autohaus' |
| 30 | autoscout24_de_2e89b83d7ff1 | 0.047 | PROMO_HIT | 'FABA Mönchengladbach' |

## Workflow S188

### STEP 1 — Ground truth Luke su 29 (rubrica shared sopra)

Aprire `/Volumes/MontereyT7/argos-poc/S187/inputs/` in Finder. Per ogni file `01_…` → `30_…` (skip #6 ERROR), classificare SLIDE / AUTO / AMBIGUA. Output formato:
```
01=SLIDE
02=SLIDE
03=AUTO
...
```

### STEP 2 — Confusion matrix + F1 stat-significativo

Script `/Volumes/MontereyT7/argos-poc/S187/calibrate.py` (DA CREARE in S188): input ground truth + preflight.json → compute:
- True/False Positive/Negative
- Recall, Precision, F1
- Keyword breakdown (quali keyword catturano quali SLIDE; quali keyword presenti anche in AUTO)
- Density distribution per categoria (slide vs auto vs ambigua)

### STEP 3 — Decisione pivot (gate)

Se F1 ≥ 0.75 su 29 → procedi P0 architect con keyword pool aggiornata + DuckDB ALTER + patch `detail_enricher_v2.py`.
Se F1 < 0.75 → **abortire P0 upstream_slide_filter**, pivot a:
- Nuovo P0 = patch `generate_opportunity_dossier` per invocare sanitizer (fix fail mode #1 D-32 da memory `sanitizer_isolation_test_plate_invisible_to_vision.md`)
- P1 `promo_card_detector` Stage 3 con keyword pool estesa come flag `manual_review=true` (NON skip)
- P2 dossier metadata `manual_review_required`

### STEP 4 — Update memory + commit prompt S189

Aggiorna `s187_*` memory + DECISIONS.md ARGOS con esito calibrazione. Prompt S189 con scope ridotto post-decisione.

## Vincoli hard S188

- NO commit fino a F1 calcolato
- NO ALTER TABLE DuckDB prima di gate STEP 3
- Architect agent NON va re-invocato (piano S187 già completo, manca solo calibrazione)
- code-reviewer agent invocato SOLO se F1≥0.75 e si procede patch
- UAT visivo Luke = ground truth, NON skippabile

## Time-box S188

- STEP 1 (Luke ground truth 29 file): 8-12 min
- STEP 2 (calibrate.py + run): 10 min
- STEP 3 (decisione pivot): 5 min
- Totale: ~25-30 min

## Riferimenti

- Prompt origine: `prompts/s187_esito_c_promo_card_filter.md`
- Memory S187: `~/.claude/projects/.../memory/s187_*.md` (DA CREARE)
- Architect output: tabella findings 1-6 + piano 7-step (vedi history S187)
- DECISIONS ARGOS: D-32 sanitizer (S187 close pending S188 gate)

## Critica strutturale 4 punti S188

1. **Assunzione nascosta**: il dataset BMW DE 30 è rappresentativo della varianza che vedremo on Day 1 Stile Car. Potrebbe non esserlo (Stile Car compra Audi/Mercedes anche, varianza brand-certified diversa).
2. **30/60/90gg**: (30gg) keyword pool calibrata su 30 BMW DE deriva e perde recall su Audi/Mercedes (60gg) AS24 cambia layout slide marketing (es. nuovi programmi certificati) (90gg) sanitizer downstream cambia comportamento, MIN_OUTPUT_SIZE_RATIO non più affidabile.
3. **Pattern errore noto**: S159/S183-ter ripetuti — proposte tecniche su intuizione non verificata. S187 ha già intercettato il pattern una volta (architect text_density 0.15 inapplicabile). S188 deve calibrare PRIMA di patch.
4. **Dove sovradimensiono**: 30 sample potrebbe essere overkill se le metriche su 29 effettivi mostrano già F1 chiaramente sotto 0.75. Stop-rule: dopo classificazione Luke, se 10 prime classificazioni mostrano già ≥4 mismatch keyword-driven, abort early e pivot.
