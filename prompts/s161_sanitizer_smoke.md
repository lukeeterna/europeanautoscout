# S161 — Smoke E2E sanitizer + visual PDF inspection (post S160 stack-green)

**Stato post-S160**: stack `~/.argos-sanitizer-venv/` operativo con `opencv-python==4.7.0.72 + numpy==1.26.4 + paddleocr==3.5.0`. `_find_sanitizer_python()` con timeout 30s seleziona correttamente il venv. **Manca**: smoke E2E che produca PDF con immagini realmente sanitizzate + verifica visuale.

**Goal S161**: smoke pipeline E2E completata con PDF dossier che mostra `[SANITIZER]/[OCR]/[INPAINT]` log + targhe/watermark mascherati visivamente.

**Timebox**: 30min totali, hard stop a context 50%.

---

## Step 1 — Warmup modelli PaddleOCR (5min, idempotente)

Primo `import paddleocr` con `PaddleOCR()` scarica modelli PP-OCRv4 (~50-100MB) da BCE/Azure. Eseguire warmup FUORI dalla pipeline per evitare stallo apparente nel run E2E:

```bash
~/.argos-sanitizer-venv/bin/python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_textline_orientation=True, lang='en')
print('models OK', list((__import__('pathlib').Path.home() / '.paddlex').rglob('*.pdparams'))[:3])
"
```

Verifica: `~/.paddlex/` deve contenere file `.pdparams` post-warmup (size totale > 50MB).

## Step 2 — Smoke E2E full (15min wall clock atteso)

```bash
cd ~/Documents/combaretrovamiauto-enterprise
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 40000 --dealer "Smoke S161" 2>&1 | tee /tmp/argos_s161_smoke.log
```

Wall clock atteso: scraping ~10s + CoVe scoring ~30 listing × 7s/listing ≈ 3-4min + PDF generation con sanitizer 6 img × ~15s ≈ 1.5min ≈ **5-6min totali post-warmup**.

**Verifica nel log**:
- `[SANITIZER] Using /Users/macbook/.argos-sanitizer-venv/bin/python (has PaddleOCR)` ✓
- `[OCR] N text region(s) to mask` ripetuto per img > 0 ✓
- `[INPAINT] NK pixels masked` (TELEA, eventualmente LaMa se installato) ✓
- `SANITIZED: argos_<id>_NN.jpg` non `INTERIOR:` né RAW passthrough

## Step 3 — Visual inspection PDF (5min)

```bash
ls -lt dossiers/*.pdf | head -1
open "<latest_pdf>"
```

Verifica visuale:
- Targhe blur/mask ✓
- Watermark dealer tedesco rimosso ✓
- Logo "ARGOS" oro basso-sx presente ✓
- Size PDF > 3MB (immagini full-res ancora embedded) ✓

## Step 4 — Closure (5min)

1. `BACKLOG.md` → marker FIXED S161 sull'entry "Image Sanitizer (PaddleOCR) NON OPERATIVO"
2. `HANDOFF.md` → STATO CORRENTE S161 VERDE
3. `MEMORY.md` → entry S161 (con riferimento path-C combo working)
4. Commit `feat(s161): sanitizer paddleocr smoke E2E verde + visual inspection`

## Stop criteria

- VERDE: log mostra `[OCR]` + PDF >3MB + visual mask verificato su almeno 1 immagine
- ARANCIONE: warmup OK ma OCR detection 0/6 → defer escalation (modelli o config PP-OCR tuning)

## NON fare in S161

- NO Day 1 reale (regola `feedback_no_live_without_test.md`)
- NO modifiche `image_sanitizer.py` finché non identifichi causa specifica failure

## Refs

- `.planning/s160_path_c_working_combo.md` (creato S160) — combo cv2 4.7 + numpy 1.26 + paddleocr 3.5 motivazioni
- `s159_partial_blocker.md` — path A/B/C/D analysis originale
- `feedback_decision_support.md` — pattern decisione tecnica unica motivata
