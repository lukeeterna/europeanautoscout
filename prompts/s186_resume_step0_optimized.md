# S186 — Resume PoC plate-detector EU (STEP 0 ottimizzato + STEP 1+2)

**Contesto S185 chiusura**: sessione chiusa al ~59% context (vincolo #7) durante
STEP 0 Read-multimodal. 6/35 foto ispezionate visivamente:
- **1 sample confermato**: `raw_autoscout24_de_428982234890_02.jpg` — targa DE
  autentica "M·XC 573E" (render BMW "Abbildung ähnlich", retro centro-sx)
- 4 NO:
  - `1c29ca01cdb2_02`+`_03`: BMW iX3 nera, frontale rimosso / laterale, no targa
  - `39d64c65e9de_02`: close-up ruota Bridgestone (no targa)
  - `39d64c65e9de_03`: BMW X3 Baum, **targa sostituita da cartello promo
    "BMW PREMIUM SELECTION GECHECKT & GARANTIERT"** + watermark URL (pattern S184)
  - `428982234890_03`: slide marketing pura (Premium Selection checklist)
- 29/35 non ispezionati

**Insight strutturale**: dominio AS24 con dealer DE (Baum, Autohaus Isernhagen,
Wernecke) mostra 3 pattern ricorrenti:
1. Foto stock-render BMW ufficiali ("Abbildung ähnlich") → targa generica DE renderizzata
2. Foto reali dealer con targa SOSTITUITA da cartello promo
3. Slide marketing (_03 spesso) → skip upstream

**Pre-filter già pronto**: `/tmp/s185_vision_prefilter.py` (Vision OCR + regex
plate DE/IT su `/tmp/s185_inspect/` 35 file). NON eseguito S185.

## STEP 0-bis OTTIMIZZATO (max 10 min) — pre-filter programmatico

1. `python3 /tmp/s185_vision_prefilter.py` → output `/tmp/s185_prefilter.json`
   con candidate plate text + bbox per ogni file. Stampa sommario.
2. Read multimodal SOLO sui file con candidate strict (regex DE/IT match) o
   loose ad alta conf. Max 10 file → ~5 batch.
3. Conferma visiva targa autentica vs cartello promo/watermark. Annota
   bbox approssimato manualmente (X/Y su 1280×806 o nativo).
4. Sample noto già confermato S185: `raw_autoscout24_de_428982234890_02.jpg`
   "M·XC 573E" (retro centro-sx, ~x:225-415 / y:370-415 su 1280×806).

**Stop condition invariata**: se confermati totali <3 → triggera ESITO C addendum
(no plate-detector, S187 = cartello-promo-detector + upstream filter slide AS24).

## STEP 1 — Modello EU plate-detector HF (max 8 min)

- MCP `mcp__claude_ai_Hugging_Face__hub_repo_search` query suggerite:
  - "german license plate yolo"
  - "EU license plate detection"
  - "ANPR European"
  - "yolov8 plate europe"
- Top-3 sort=downloads, ispeziona README + files (license MIT/Apache, size <100MB,
  formato `.pt` ultralytics-compatibile o `.onnx`).
- Scarica su iMac `/tmp/eu_plate_*.pt` via curl + sha256 sanity.
- Se nessun candidato chiaramente EU-trained → usa miglior generic (yolov8-plate
  generico Roboflow trained su 30k+ images) e dichiaralo esplicitamente.

## STEP 2 — Comparativa EU vs Apple Vision (max 15 min)

Refactor `/tmp/poc_yolo_plate.py` (esistente da S184) in `/tmp/s186_poc_eu_vs_vision.py`:
- Input: sample STEP 0-bis confermati
- Detector A: modello EU STEP 1
- Detector B: Apple Vision OCR (`src/cove/vision_ocr.py` o inline detect_text_regions)
- Output per ogni sample:
  - tabella: `| file | EU n_box | EU conf | EU bbox | EU ms | Vision n_text | Vision text matching plate regex | Vision bbox | Vision ms |`
  - annotate JPG: verde=EU box, rosso=Vision box, overlay su immagine
  - salva `/tmp/poc_yolo_eu_out/<file>.jpg` + zip `/tmp/poc_yolo_eu_out.zip`

Eseguire su iMac via SSH (ultralytics+torch+cv2 installati lì, S184).

## GATE addendum S185 — 3 esiti differenziati

### ESITO A — GATE PASS (EU >> Vision su targhe vere)
**S187 piano**: integrazione canale OR YOLO-EU in Stage 3 `image_sanitizer.py`.
**Prerequisito esplicito**:
- backup datato `image_sanitizer.py` + `vision_ocr.py` prima patch
- UAT su **30+ foto** post-integration PRIMA di dichiarare ring #4 verde
- NO production-ready su 5-8 sample (autocritica S184 R1 + memory
  `feedback_smoke_test_not_uat_gate.md`)
- code-reviewer agent invocato pre-commit
- Day 1 Stile Car (2026-06-03, 11 giorni rimanenti) NON gate-flippa su PoC pulito,
  solo su UAT 30+ verde

### ESITO B — EU ≈ Vision o peggio
**S187 piano**: STRADA 2 alert + flag manual_review.
- Patch metadata dossier: campo `plate_detection_status` ∈ {detected, missing, low_confidence}
- Se missing/low_confidence → notifica Telegram + flag `manual_review=true` nel DB
- Luke gate visual prima di invio dealer (1 dossier 1 click approve)
- BACKLOG promosso **#1**: `upstream-filter-AS24-slides` (filtra slide marketing
  Premium Selection/Garantie/Wartungsfreiheit upstream a `image_downloader.py`,
  prima del DB insert in `vehicle_images`)

### ESITO C — STEP 0-bis non trova ≥3 targhe vere
**S187 piano**: NESSUN plate-detector.
- Dominio reale ARGOS = poche targhe personali (la maggioranza dei retro è
  cartello-promo dealer o stock-render senza targa montata)
- Sostituzione: `promo_card_detector` (cartello promo dealer in posizione targa)
  + `upstream_slide_filter` (skip slide marketing AS24 a scraping time)
- Sanitizer Stage 3 = best-effort, dossier con campo "targa: N/A (cartello dealer)"

## Vincoli ereditati S185 (invariati)
- NO integrazione, NO modifiche `image_sanitizer.py` ANCHE SE GATE PASS in S186
- Decisione integrazione = Luke su S187 separato
- Tutto su iMac via SSH per modello EU (libs lì)
- Script `/tmp/`, mai in `src/`
- Output Luke download via `/tmp/*.zip`

## Budget context S186
- Apertura: skill + memory + prompt ~25-30%
- Pre-filter Vision OCR programmatico → riduce drasticamente costo Read multimodal
- Target chiusura <55% (sotto vincolo #7 con margine)
- Se a 30 min STEP 2 non finito → check-point handoff S187 con dati parziali

## Output sessione richiesti
1. Sommario pre-filter Vision OCR (n_files con plate candidate / 35)
2. Sample finali confermati STEP 0-bis (≥3 o stop condition trigger)
3. Modello EU STEP 1 (nome HF + size + license + sha256)
4. Tabella comparativa STEP 2 + zip annotate
5. Verdetto raccomandato ESITO A/B/C motivato sui dati
6. Memory update `poc_yolo_plate_round2_eu_*.md`
