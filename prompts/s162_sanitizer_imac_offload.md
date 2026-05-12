# S162 — Sanitizer offload su iMac via SSH (resume da S161 BLOCKED)

## Contesto

S161 BLOCKED strutturale: `PaddleOCR()` init fail su MacBook macOS 11 Big Sur — `paddle/libs/libcommon.dylib` ha `LC_BUILD_VERSION minos=12.3 sdk=12.3` (Monterey). Pattern S159 → S160 → S161 stesso blocker = sunk cost fallacy locale.

S160 closure "stack-green" era false-positive (misurato `import paddleocr` top-level lazy, non `PaddleOCR()` init).

**Decisione (S161, vincolo 11 pattern strutturale)**: STOP path locale, offload su iMac via SSH (path A originale S159).

## Pre-condizioni verificate (S161)

- iMac `ssh imac` raggiungibile, macOS Monterey 12.7.4 (compatibile paddle 3.x)
- iMac ha `/usr/local/bin/python3.11` (sweet spot paddleocr 3.5, conferma S159 research)
- iMac NO Homebrew, NO venv paddleocr esistente — setup greenfield
- MacBook venv `~/.argos-sanitizer-venv/` lasciato in place (270MB, future ispezioni)

## Goal S162

Sanitizer-as-CLI su iMac: MacBook PDF generator chiama `ssh imac python sanitize_batch.py < input_img > output_img` per ogni immagine. Output: PDF dossier con targhe/watermark mascherati visibilmente.

## Timebox

60min totali, hard stop context 50%.

## Step 1 — Setup venv iMac (15min)

```bash
ssh imac '/usr/local/bin/python3.11 -m venv ~/.argos-sanitizer-venv && source ~/.argos-sanitizer-venv/bin/activate && pip install --upgrade pip'
```

Install combo verificato S160 (compatibile Monterey 12.7.4):
```bash
ssh imac 'source ~/.argos-sanitizer-venv/bin/activate && pip install "opencv-python==4.7.0.72" "numpy<2" "paddleocr==3.5.0" "paddlepaddle==3.0.0"'
```

Verifica init reale (NON solo import top-level — lezione S161):
```bash
ssh imac '~/.argos-sanitizer-venv/bin/python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_textline_orientation=True, lang=\"en\")
print(\"PaddleOCR init OK\")
"'
```

**Gate Step 1**: output `PaddleOCR init OK` senza traceback. Se fail → STOP, diagnostica dylib.

## Step 2 — Warmup modelli iMac (5min)

Primo `PaddleOCR()` scarica modelli PP-OCRv4 (~50-100MB) da BCE/Azure. Eseguire una volta:

```bash
ssh imac '~/.argos-sanitizer-venv/bin/python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_textline_orientation=True, lang=\"en\")
import pathlib
models = list((pathlib.Path.home() / \".paddlex\").rglob(\"*.pdparams\"))
print(f\"models: {len(models)} files\")
"'
```

**Gate Step 2**: ≥3 file `.pdparams` in `~/.paddlex/` su iMac.

## Step 3 — Deploy `image_sanitizer.py` su iMac (15min)

Copia il modulo esistente MacBook → iMac:
```bash
scp /Users/macbook/Documents/combaretrovamiauto-enterprise/tools/scripts/image_sanitizer.py imac:~/argos_sanitizer.py
```

Crea wrapper CLI batch `~/argos_sanitize_cli.py` su iMac (stdin path lista → stdout JSON con output paths):

```python
#!/usr/bin/env python3
"""CLI sanitizer batch — stdin: una immagine path per riga. stdout: JSON {input: output_path}."""
import sys, json, os
from pathlib import Path
sys.path.insert(0, str(Path.home()))
from argos_sanitizer import sanitize_image  # adapter da definire matching API attuale

results = {}
for line in sys.stdin:
    img_path = line.strip()
    if not img_path or not os.path.exists(img_path):
        continue
    out_path = sanitize_image(img_path)
    results[img_path] = out_path
print(json.dumps(results))
```

**Importante**: verifica firma reale `image_sanitizer.py` MacBook (potrebbe avere classe `ImageSanitizer` invece di funzione `sanitize_image`). Adattare wrapper di conseguenza.

## Step 4 — Client MacBook (15min)

Modifica `tools/scripts/pdf_generator_enterprise.py` per chiamare iMac via SSH invece di subprocess locale Python:

Pattern target (intorno alla chiamata `_find_sanitizer_python()` + sanitize, ~line 1568):
1. Salva immagini scaricate in `/tmp/argos_sanitize_in/`
2. Apri SSH a iMac: `ssh imac '~/.argos-sanitizer-venv/bin/python ~/argos_sanitize_cli.py'` con stdin = lista path
3. Trasferisci `/tmp/argos_sanitize_in/*.jpg` su iMac `~/tmp/argos_sanitize/` (scp o rsync)
4. Esegui CLI batch
5. Recupera output con `scp imac:~/tmp/argos_sanitize/sanitized_*.jpg /tmp/argos_sanitize_out/`
6. Embed in PDF

**Alternativa stateless** (preferibile, no scp roundtrip): `ssh imac` con base64 stdin/stdout per ogni immagine. Costo: ~2× transfer overhead ma elimina rsync sync. Decisione: dipende da tempo. Default: `rsync` se ≥3 immagini, single SSH base64 se 1.

## Step 5 — Smoke E2E (10min)

```bash
cd ~/Documents/combaretrovamiauto-enterprise
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 40000 --dealer "Smoke S162" 2>&1 | tee /tmp/argos_s162_smoke.log
```

**Verifica nel log**:
- `[SANITIZER] Using ssh imac (offload Monterey)` ✓
- `[OCR] N text region(s) to mask` ripetuto per img > 0 ✓
- `SANITIZED: argos_<id>_NN.jpg` non RAW passthrough ✓

**Verifica visuale**:
```bash
open "$(ls -t dossiers/*.pdf | head -1)"
```
- Targhe blur/mask ✓
- Watermark dealer tedesco rimosso ✓

## Step 6 — Closure (5min)

1. `BACKLOG.md` → FIXED S162 entry sanitizer
2. `HANDOFF.md` → STATO CORRENTE S162 VERDE
3. `MEMORY.md` → entry S162 + invalida S160/S161
4. Commit `feat(s162): sanitizer offload iMac SSH — paddle dylib bypass macOS 11`

## Stop criteria

- **VERDE**: log mostra `[OCR]` con detection > 0 + PDF >3MB + visual mask verificato + Day 1 reale Stile Car unblocked
- **ROSSO** (se fail Step 1): diagnostica dylib iMac. Se paddle non funziona neanche su Monterey → escalation Luke per scelta alternativa (EasyOCR PyTorch, tesseract semplice, Docker iMac)

## NON fare in S162

- NO tentativi paddle su MacBook (chiusa S161, vincolo 11)
- NO Day 1 reale (regola `feedback_no_live_without_test.md`)
- NO refactor `image_sanitizer.py` oltre il wrapper CLI minimo

## Refs

- `s161_blocked_strutturale.md` — root cause + decisione offload
- `s159_paddleocr_research.md` — Intel Mac + Python 3.11 sweet spot validation
- `.planning/s160_path_c_working_combo.md` — combo cv2/numpy/paddleocr da replicare su iMac

## Architettura risultante post-S162

```
MacBook (macOS 11)              iMac (Monterey 12.7.4)
─────────────────────           ───────────────────────
pdf_generator_enterprise.py  →  SSH → ~/.argos-sanitizer-venv/bin/python
  (scarica immagini)                    argos_sanitize_cli.py
  (chiama SSH client)                     paddleocr 3.5 + paddle 3.0
                              ←  return sanitized images
  (embed in PDF)
```

Pattern stateless on-demand (CLAUDE.md): no daemon iMac, no porte aperte, SSH solo quando serve.
