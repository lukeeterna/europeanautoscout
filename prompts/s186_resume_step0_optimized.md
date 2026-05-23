# S186 — Resume PoC plate-detector EU (paletti Luke applicati)

**Contesto S185**: STEP 0 chiuso a 60% context per saturazione Read multimodal manuale.
6/35 foto ispezionate, 1 targa DE autentica confermata (`428982234890_02` "M·XC 573E"),
4 NO, 29 non ispezionate. Esito S185 = D (STEP 0 incompleto, no GO/NO-GO).

**Sessione fresca + time-box 45 min + check a 30 min**. Se context si avvicina a
saturazione prima di chiudere STEP 0 → fermati e handoff pulito (pattern S185 ok).

## Paletti Luke (vincoli operativi S186)

1. **Pre-filter Vision OCR PRIMA di qualsiasi Read multimodal** — inverti ordine S185.
   Lo script gira su tutte le foto candidate, produce shortlist (box plate-like, conf >
   soglia). Read multimodal SOLO sulla shortlist. Niente ri-saturazione.
2. **Stop-condition hard**: se dopo pre-filter risultano <3 targhe DE/IT autentiche
   confermate visivamente su tutto il pool → ESITO C definitivo. NO STEP 1/2.
   Scrivi resume S187 ESITO C e ferma.
3. **Bias-aware**: il segnale R1 + S185 (1/6 targhe vere finora) orienta verso C.
   Se il pre-filter conferma, NON forzare STRADA 1.
4. **Foto Baum obbligatoria**: `raw_autoscout24_de_39d64c65e9de_00.jpg` inclusa nel
   pool come fail-case R1 di confronto diretto (cartello promo dealer in posizione
   targa).
5. **Addendum chiusura S186**: anche se GATE PASS, NON integrare `image_sanitizer.py`.
   Scrivi solo prompt resume S187 differenziato sui 3 esiti. Decisione integrazione
   = Luke, su ispezione visiva immagini in `/tmp/poc_yolo_eu_out/`.
6. **Gate visivo finale = Luke** sui crop annotati.

## STEP 0-bis (max 15 min) — pre-filter programmatico + gate visivo shortlist

### Pool foto
- Locale MacBook: `/tmp/s185_inspect/` (35 jpg ereditati S185, 11 listings × _00/_02/_03)
- **AGGIUNGI obbligatoriamente** `raw_autoscout24_de_39d64c65e9de_00.jpg` se non già
  in pool (Baum fail-case R1)
- Verifica: `ls /tmp/s185_inspect/ | grep 39d64c65e9de` → deve includere `_00`. Se no,
  rsync da iMac.

### Pre-filter
1. Esegui `python3 /tmp/s185_vision_prefilter.py` (già scritto S185, regex DE/IT
   strict + loose con esclusioni dealer/marketing). Output `/tmp/s185_prefilter.json`.
2. Stampa sommario: n_files con candidate / 35, top 10 per conf strict.
3. Se 0 candidate strict → loose-only review. Se 0 anche loose → ESITO C immediato
   (Vision non vede nessuna targa, plate-EU non risolverebbe perché Vision non guida
   il sanitizer attuale).

### Gate visivo shortlist (Read multimodal SOLO qui)
- Max 10 file shortlist, batch da 5. Per ognuno classifica:
  - `TARGA_VERA` (DE/IT autentica, no promo, no watermark, anche angolata/parziale)
  - `CARTELLO_PROMO` (es. "BMW PREMIUM SELECTION", "Spar-Deal")
  - `WATERMARK_URL` (es. `baum-automobile.de`)
  - `SLIDE_MARKETING` (catalog AS24)
  - `ALTRO` (no plate-like in foto)
- Conta `TARGA_VERA`. Stop condition <3 → ESITO C.

### Sample noto ereditato S185
- `428982234890_02` = TARGA_VERA "M·XC 573E" (render BMW, retro centro-sx,
  bbox ~x:225-415 / y:370-415 su 1280×806). Conta nel ≥3 totali.

## STEP 1 — Modello EU plate-detector HF (max 10 min, SOLO se STEP 0-bis ≥3 vere)

- MCP `mcp__claude_ai_Hugging_Face__hub_repo_search` sort=downloads. Query:
  - "german license plate yolo"
  - "EU license plate detection"
  - "ANPR European yolov8"
- Top-3 candidate: verifica README (training set EU/DE), license (MIT/Apache),
  size (<100MB), formato (`.pt` ultralytics o `.onnx`).
- Se nessun candidato chiaramente EU-trained → usa miglior generic-plate trained su
  dataset Roboflow (30k+ images) e dichiaralo esplicitamente. NON inventare modello.
- Scarica iMac `/tmp/eu_plate_*.pt` via curl + sha256 sanity.

## STEP 2 — Comparativa EU vs Apple Vision (max 15 min, SOLO se STEP 1 done)

Refactor `/tmp/poc_yolo_plate.py` (S184 esistente) in `/tmp/s186_poc_eu_vs_vision.py`:
- Input: sample STEP 0-bis confermati TARGA_VERA + foto Baum fail-case
- Detector A: modello EU STEP 1
- Detector B: Apple Vision OCR (`src/cove/vision_ocr.py` `detect_text_regions`)
- Output per sample:
  - Tabella: `| file | label_step0 | EU_n_box | EU_conf | EU_bbox | EU_ms | Vision_n_text | Vision_text_plate | Vision_bbox | Vision_ms |`
  - Annotate JPG: verde=EU box, rosso=Vision box, label sopra
  - Salva `/tmp/poc_yolo_eu_out/<file>.jpg` + zip `/tmp/poc_yolo_eu_out.zip`

Eseguire su iMac via SSH (ultralytics+torch+cv2 installati lì, S184).

## Output sessione richiesti (ordine)

1. Sommario pre-filter Vision OCR (n_files candidati / 35 totali)
2. Tabella shortlist con label visivo (TARGA_VERA / CARTELLO_PROMO / WATERMARK_URL /
   SLIDE_MARKETING / ALTRO)
3. Verdict STEP 0-bis: ≥3 TARGA_VERA → procedi STEP 1+2. <3 → ESITO C stop.
4. Se procedi: modello EU STEP 1 (nome HF + size + license + sha256)
5. Se procedi: tabella comparativa + zip annotate STEP 2
6. Resume S187 differenziato sui 3 esiti (vedi sotto), salvato in
   `prompts/s187_*.md` + memory entry
7. NO integrazione `image_sanitizer.py`

## Resume S187 differenziato (preparare a fine S186 in ogni caso)

### ESITO A — EU >> Vision su targhe vere
**S187 piano**: integrazione canale OR YOLO-EU in Stage 3 `image_sanitizer.py`.
**Prerequisito hard non negoziabile**:
- backup datato `image_sanitizer.py` + `vision_ocr.py` prima patch
- UAT su 30+ foto post-integration PRIMA di dichiarare ring #4 verde
- NO production-ready su 5-8 sample (memory `feedback_smoke_test_not_uat_gate.md`)
- code-reviewer agent invocato pre-commit
- Day 1 Stile Car (2026-06-03, ~10gg) NON gate-flippa su PoC verde, solo su UAT 30+

### ESITO B — EU ≈ Vision o peggio
**S187 piano**: STRADA 2 alert + flag manual_review nel metadata dossier
- Campo `plate_detection_status` ∈ {detected, missing, low_confidence}
- Missing/low → notifica Telegram + `manual_review=true` nel DB
- Luke gate visual prima invio dealer (1 dossier 1 click approve)
- **BACKLOG promosso #1**: `upstream-filter-AS24-slides`

### ESITO C — STEP 0-bis <3 TARGA_VERA
**S187 piano**: NESSUN plate-detector. PoC plate-EU CHIUSO.
- Sostituzione: `promo_card_detector` (cartello dealer in posizione targa)
- + `upstream_slide_filter` (skip slide marketing AS24 a scraping time, prima del
  DB insert in `vehicle_images`)
- Sanitizer Stage 3 best-effort, dossier con campo "targa: N/A (cartello dealer)"
  + `manual_review=true` se cartello-promo non detected

## Budget context S186 target
- Apertura: ~25-30%
- Pre-filter programmatico → riduce drasticamente Read multimodal
- Target chiusura <55%
- A 30 min check-point: stato anche se incompleto
- A 45 min: stop hard

## Artefatti S185 ereditati
- `/tmp/s185_inspect/` (35 jpg, MacBook)
- `/tmp/s185_vision_prefilter.py` (pronto)
- iMac: `/tmp/koushim_yolov8_plate.pt`, `/tmp/poc_yolo_plate.py`, ultralytics+torch+cv2
