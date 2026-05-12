# S162-v2 — Investigation alternative sanitizer non-paddle (post-fix iMac AVX1)

## Contesto

S161 BLOCKED paddle locale (macOS 11 dylib minos 12.3).
S162 original BLOCKED iMac (AVX1, paddle wheel macOS richiede AVX2).

Stack paddleocr = dead-end totale ARGOS (MacBook + iMac). Necessario cambio lib.

**Goal S162-v2**: investigation 30min produce raccomandazione singola motivata tra 3 path alternativi. NO execution. NO refactor `image_sanitizer.py`.

## Timebox

30min totali, hard stop context 50%.

## Pre-condizioni verificate

- iMac CPU AVX1 only — `ssh imac "sysctl -n machdep.cpu.features"` da eseguire come prima riga per registrare ground truth in log
- MacBook macOS 11.7.10 Big Sur, Python 3.13 base + venv 3.11 esistente
- Vincolo zero-cost (€240/mese, free-tier first)

## Decision matrix da compilare

| Path | Lib principale | AVX2 req | macOS 11 wheel | API compat sanitizer | Pre-flight `--dry-run` esito | Modello OCR detection accuracy targhe |
|------|----------------|----------|----------------|----------------------|------------------------------|---------------------------------------|
| B | EasyOCR (torch CPU) | ? | ? | ? | ? | ? |
| C | pytesseract (tesseract C++) | ? | ? | ? | ? | ? |
| D | pyobjc + Vision.framework | No (nativo) | Yes (built-in) | ? | N/A (system lib) | ? |

## Step 1 — Audit `image_sanitizer.py` esistente (10min)

Read `tools/scripts/image_sanitizer.py` per estrarre:
- API attualmente chiamata da `pdf_generator_enterprise.py` (firma input/output)
- Cosa fa il sanitizer concretamente: targhe blur? watermark mask? altro?
- Quante immagini per dossier (5-10 da MEMORY)
- Costo accuracy: cosa accetta come "good enough"?

**Output**: 5-righe summary requirement reale (non assumere quello che credo di sapere).

## Step 2 — Pre-flight `--dry-run` paths B + C (10min)

**Path B (EasyOCR + torch CPU)**:
```bash
~/.argos-sanitizer-venv/bin/pip install --dry-run --report /tmp/easyocr_dryrun.json --ignore-installed easyocr
```

Verifica nel JSON:
- `torch` wheel URL → tag `macosx_*` (ricerca minimo `macosx_11_*` o vecchio)
- `easyocr` versione + dipendenze (numpy, opencv compat)
- Total disk size stimato

Verifica dylib minos su wheel torch scaricato (NON installato):
```bash
pip download --no-deps --dest /tmp/torch_check torch
unzip -d /tmp/torch_extracted /tmp/torch_check/torch-*.whl
otool -l $(find /tmp/torch_extracted -name 'libtorch_cpu.dylib' | head -1) | grep -A4 LC_BUILD_VERSION
```

Se `minos > 11.x` → Path B BLOCKED. Se `minos ≤ 11.x` → procedi test init.

**Path C (pytesseract + tesseract brew)**:
```bash
which tesseract || brew list --formula | grep tesseract
~/.argos-sanitizer-venv/bin/pip install --dry-run --report /tmp/pytesseract_dryrun.json --ignore-installed pytesseract
```

Pre-flight tesseract binary:
```bash
tesseract --version  # se installato
```

Path C dipende su `tesseract` C++ binary da brew. Brew su macOS 11 = supportato? Verifica.

**Path D (pyobjc + Vision)**:
- `pyobjc` già installato in molti Python macOS default? `python3 -c "import objc"` test
- Vision framework richiede macOS 10.13+ (built-in da High Sierra). Big Sur 11.x OK.
- Verifica API: `VNRecognizeTextRequest` per OCR detection + bbox. Doc Apple developer.

## Step 3 — Test init reale paths che superano pre-flight (5min)

Per ogni path con pre-flight OK:
- Path B: `from easyocr import Reader; r = Reader(['en'], gpu=False); r.detect(test_img)` con immagine test
- Path C: `import pytesseract; pytesseract.image_to_data(test_img)` con immagine test  
- Path D: pyobjc snippet minimale Vision OCR + bbox extraction

**Gate verifica reale** (lezione S160 false-positive): init + smoke call con output non vuoto, NON solo import.

Test image: usa una immagine reale auto da `dossiers/` precedenti (BMW X3, targhe visibili). Path: `dossiers/ARGOS_BMW_X3_2022_Stile_Car.pdf` → estrai 1 immagine con `pdfimages`.

## Step 4 — Decision matrix + raccomandazione (5min)

Compila tabella decision matrix con dati reali (non assumption).

Scoring criteri:
- 40% — Funziona empiricamente su MacBook macOS 11 + AVX1 (no Illegal instruction)
- 30% — Detection accuracy targhe DE/IT in test
- 20% — Costo refactor `image_sanitizer.py` (LOC modificate, breaking changes)
- 10% — Robustezza 30/60/90gg (deprecation timeline lib, alternative future)

**Output S162-v2**: 1 paragrafo (max 200 parole) con raccomandazione singola motivata + plan execution S163 (30-60min stimati).

## Step 5 — Closure (no execution)

1. `HANDOFF.md` → STATO CORRENTE S162-v2 VERDE (investigation complete)
2. `MEMORY.md` → entry S162-v2 con decision matrix + raccomandazione
3. `prompts/s163_<lib_scelta>_execution.md` creato con plan execution
4. Commit `docs(s162-v2): investigation sanitizer alternatives — raccomandazione <X>`
5. NO modifiche codice ARGOS in S162-v2 (solo investigation + docs)

## Stop criteria

- **VERDE**: decision matrix compilata + raccomandazione + prompt S163 ready
- **ROSSO**: nessun path passa Step 3 (Illegal instruction OR import error OR dylib incompat) → escalation Luke per scelta degradata (cloud free-tier OCR, manual ROI hardcoded, skip sanitizer + manual review PDF prima invio)

## NON fare in S162-v2

- NO refactor `image_sanitizer.py` (solo Read)
- NO install reale lib (solo `--dry-run` + 1 test init per path)
- NO Day 1 reale (regola `feedback_no_live_without_test.md`)
- NO Path A retry (paddle dead-end strutturale, vincolo 11)

## Refs

- `feedback_false_positive_lazy_import.md` — pattern init reale come gate
- `s161_blocked_strutturale.md` — root cause paddle macOS 11
- `prompts/s162_sanitizer_imac_offload.md` — invalidato AVX1
- CLAUDE.md vincolo 8 — pre-flight env check obbligatorio per lib blacklist (estendere a tutte ML lib post lezione S159-S162)

## Architettura target post-S163 (preview)

```
MacBook (macOS 11, AVX1)
─────────────────────────
pdf_generator_enterprise.py
  → image_sanitizer.py (refactored su lib scelta S162-v2)
    → [OCR detection bbox]
    → [cv2 mask + inpaint]
  → embed PDF
```

Stateless locale. No SSH. No iMac dep per sanitizer (iMac resta per WA daemon + Funnel + altri servizi PM2).
