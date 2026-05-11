# S160 — Path C working combo: cv2 4.7 + numpy 1.26 + paddleocr 3.5

**Date**: 2026-05-11
**Sprint**: S160 (recovery post S159 PARTIAL)
**Status**: 🟢 Stack-green / 🟡 Smoke E2E visual deferred → S161

## Problema risolto

S159 aveva venv `~/.argos-sanitizer-venv/` con `opencv-contrib-python 4.9` ma `import paddleocr` falliva: `libtesseract.5.dylib` built per macOS 12, MacBook è macOS 11.

S160 ha testato 3 path opencv compat:
- **Path B**: rimuovi `opencv-contrib-python`, tieni `opencv-python 4.9` → `import paddleocr` OK ma `import cv2` fallisce (`libvmaf.1.dylib` macOS 12 embed nella main wheel)
- **Path B2**: `opencv-python 4.8.1.78` → wheel `macosx_10_16_x86_64` MA `numpy.core.multiarray failed to import` (ABI incompat con numpy 2.x)
- **Path C (GREEN)**: `opencv-python==4.7.0.72 + numpy<2` → tutto importa, paddleocr 3.5 classe inizializzabile

## Combo verificata

```
opencv-python==4.7.0.72
numpy==1.26.4
paddleocr==3.5.0
paddlepaddle==3.0.0
paddlex==3.5.1
pillow==12.2.0
```

Tutte in `~/.argos-sanitizer-venv/` (Python 3.11.11 Homebrew Intel).

## Motivazione tecnica

1. **opencv-python 4.7.0.72**: ultima major prima del switch toolchain Apple a macOS 12 SDK (4.8+). Wheel `cp37-abi3-macosx_10_16_x86_64.whl` compat macOS 11.
2. **numpy<2**: opencv-python 4.7.x compilato contro numpy 1.x ABI. Numpy 2.x rompe import.
3. **paddlepaddle 3.0 requires numpy** (senza upper bound): accetta sia 1.x che 2.x.
4. **paddleocr 3.5 lazy-imports cv2**: `import paddleocr` da solo non triggera cv2 binding, ma `PaddleOCR()` + sanitize sì.

## Fix applicato a `pdf_generator_enterprise.py`

`_find_sanitizer_python()` aveva `timeout=10` su subprocess `import paddleocr`. Misurato wall time:

```bash
$ /usr/bin/time -p ~/.argos-sanitizer-venv/bin/python -c "import paddleocr; print('ok')"
ok
real        14,85
```

→ `timeout=30` per coprire margine.

## Cosa NON verificato in S160

- Smoke E2E con sanitize reale su immagine downloadata (PaddleOCR primo run scarica ~50-100MB modelli PP-OCRv4 da BCE/Azure — wall clock ~5-10min). Pipeline killata prematuramente a 13min mentre era in CoVe scoring (assunzione errata: pipeline hung su modelli, in realtà processing 20+ listing × ADAC lookup).
- Visual inspection PDF post-sanitize (targhe blur, watermark mask)
- `simple-lama-inpainting` NON installato (graceful via try/except in `_get_simple_lama`, TELEA-only path)

## Path forward S161

Vedi `prompts/s161_sanitizer_smoke.md`. Step 1 = warmup modelli PaddleOCR fuori pipeline, evita stallo apparente nel run E2E. Step 2-3 = smoke + visual.

## Lezioni operative S160

1. **Sub-dylib bundling è root cause vera**: opencv 4.8+ embed `.dylibs/libvmaf` `libtesseract` built per macOS 12 anche se wheel principal dichiara 10.16. Verifica empirica >> claim metadata.
2. **numpy 2.x compat ABI**: opencv 4.10+ è la prima major numpy-2-compat. Soluzione `numpy<2` evita upgrade opencv.
3. **PaddleOCR first-run download è PROGRESSIVO non istantaneo**: ~50-100MB su BCE/Azure CDN, può durare minuti. Warmup separato evita confusione "pipeline hung".
4. **Kill prematuro = spreco lavoro**: prima di SIGTERM, verificare se processo è genuinely hung (CPU 0%, syscall stuck) vs progressing slow (CPU > 0%, file descriptor activity). PID 83761 era state R con CPU activity progressiva = non hung.
5. **Pipeline `| tail -80` bufferizza fino EOF**: non usare per debug live, usa `| tee` o redirect file.

## Riferimenti

- `s159_partial_blocker.md` — analisi path A/B/C/D originale
- `feedback_decision_support.md` — pattern decisione tecnica
- `feedback_context_budget_gate.md` — closure forzata
