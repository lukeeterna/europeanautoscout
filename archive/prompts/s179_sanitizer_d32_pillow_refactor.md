# S179 — Sanitizer D-32 refactor Pillow-only (BLOCKER Day 1 Stile Car)

> Prerequisito: leggi memory `s178_contract_e2e_verde.md` (E2E contract chiuso) + `s176_partial_step4_6_green_d32_sanitizer_blocker.md` (regression evidence) + decisione `D-32 / D-25` in DECISIONS.md.
> Quando eseguire: prima sessione utile lun-sab 9-19 IT.

## Stato ereditato

- ✅ Pipeline E2E contract (scrape→CoVe→PDF→send→sign→pay) VERDE su TEST_FOUNDER (S178)
- ❌ BLOCKER unico Day 1 Stile Car reale: sanitizer LaMa produce hallucination strutturale (S176: BMW X1 paraurti deformato, targa scomparsa, "xDrive 25e" inghiottita)
- 📋 Decisione D-32 (DECISIONS.md): refactor `src/cove/image_sanitizer.py` con `PIL.ImageDraw.rectangle()` solid fill — no LaMa, no PaddleOCR mask espansa
- 📋 Compliance D-25 Pillow-only stack (no OpenCV/LaMa/PaddleOCR generativo)

## STEP 1 — Audit sanitizer attuale (~10min)

```bash
wc -l src/cove/image_sanitizer.py src/cove/vision_ocr.py 2>/dev/null
grep -nE 'lama|inpaint|paddle|cv2|opencv|generate' src/cove/image_sanitizer.py | head -20
```

Identifica:
- Funzione `_inpaint_with_lama()` o equivalente da sostituire
- Pipeline entry (`sanitize_image()`?) e signature attesa
- Test esistenti `tests/test_sanitizer*.py`

## STEP 2 — Implementazione `_draw_solid_fill()` (~30min)

Sostituisci LaMa inpaint con rectangle Pillow solido (color match border medio per blending naturale):

```python
from PIL import Image, ImageDraw, ImageStat

def _draw_solid_fill(img: Image.Image, bbox: tuple[int,int,int,int]) -> Image.Image:
    """Coprire bbox con rettangolo solido color medio bordo (D-32, D-25)."""
    x1, y1, x2, y2 = bbox
    # Sample 3px border per color naturale
    border_box = (max(0,x1-3), max(0,y1-3), min(img.width,x2+3), min(img.height,y2+3))
    border_crop = img.crop(border_box)
    avg = ImageStat.Stat(border_crop).mean[:3]
    fill_color = tuple(int(c) for c in avg)
    out = img.copy()
    draw = ImageDraw.Draw(out)
    draw.rectangle([x1, y1, x2, y2], fill=fill_color)
    return out
```

Mantieni Apple Vision OCR (S163) per detection bbox watermark venditore. Whitelist features auto (`X1|X3|X5|Serie|xDrive|sDrive|BMW|Mercedes|Audi|AMG|M Sport|M\\d|\\d\\.\\d`) per NON mascherare identità auto.

## STEP 3 — Pre-flight `pip install --dry-run` (vincolo 8)

```bash
python3 -m pip install --dry-run --report - --ignore-installed Pillow 2>&1 | tail -5
```

Verifica wheel Big Sur compatible. Pillow è già installato, skip se versione attiva ≥9.5.

## STEP 4 — Test regression visual side-by-side (~20min)

3 sample known-bad da S176:
```bash
mkdir -p /tmp/s179_sanitizer_test/{input,output_v3_lama,output_v4_pillow}
# Copia 3 originali da dossiers/safe_images/ o dal cache S176 BMW X1 posteriore
cp src/cove/data/cache_images/<bmw_x1_*> /tmp/s179_sanitizer_test/input/
# Run sanitizer NEW
python3 -c "from src.cove.image_sanitizer import sanitize_image; from pathlib import Path; [sanitize_image(p, '/tmp/s179_sanitizer_test/output_v4_pillow/') for p in Path('/tmp/s179_sanitizer_test/input').glob('*.jpg')]"
# UAT visivo: open output
open /tmp/s179_sanitizer_test/
```

Criteri GO:
- Targa coperta (no leak)
- Watermark venditore coperto
- Auto features intatte (modello/trim/brand visibili)
- Nessun artefatto strutturale (paraurti/portellone intatti)

NO-GO trigger: anche 1 sample con artefatto → diagnosi (bbox espansione, whitelist mancante)

## STEP 5 — Test E2E pipeline sanitizer integrato (~15min)

```bash
python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 25000 --dealer "TEST_FOUNDER" --max 5
ls -la dossiers/ARGOS_BMW_X1_*.pdf
# Open PDF e verifica foto in sezioni veicolo
```

## STEP 6 — Sync iMac (~5min)

```bash
git add src/cove/image_sanitizer.py tests/test_sanitizer*.py
git commit -m "S179 D-32: sanitizer Pillow-only refactor (LaMa→rectangle solid)"
git push origin master
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"
```

## STEP 7 — Memory + handoff Day 1 reale

Se VERDE 3/3 sample: memory `s179_sanitizer_pillow_verde.md` close D-32, **Day 1 Stile Car SBLOCCATO**.
Prompt resume `prompts/s180_day1_stile_car_reale.md` con: dealer profile Stile Car, archetipo persona, V6 messaggio template, gate HITL pre-send (D-07), check daemon biz-hours 9-19 IT lun-sab.

Se ROSSO: handoff `prompts/s179b_*` con diagnosi precisa (bbox false positive? whitelist incompleta? Vision OCR drift?).

## Reference rapide

- D-32 sanitizer Pillow rectangle (DECISIONS.md)
- D-25 Pillow-only stack no OpenCV (DECISIONS.md)
- S176 regression evidence: X1 posteriore paraurti/targa/xDrive 25e
- Apple Vision OCR S163 (mantieni detection, cambia solo fill)
- Pipeline scope: NON toccare CoVe Engine v4, NON toccare scraper, NON toccare PDF generator
