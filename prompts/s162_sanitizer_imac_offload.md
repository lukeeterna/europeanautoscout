# S162 — INVALIDATO post-fix iMac AVX1 (2026-05-12 13:30)

## ⛔ Prompt originale OBSOLETO

Plan originale: offload sanitizer iMac via SSH (path A originale S159, paddle 3.x compatibile Monterey).

**Bloccato da fact-check post-handoff**: iMac CPU AVX1 (no AVX2). paddlepaddle 3.x CPU wheel macOS x86_64 richiede AVX2 (wheel `noavx` distribuiti solo Linux/Windows). iMac Monterey 12.7.4 + AVX1 → `Illegal instruction` al primo tensor op anche se dylib carica.

Path A morto. Investigation alternative non-paddle necessaria PRIMA di nuovo execution sprint.

## ➡️ Usa S162-v2 (investigation)

Resume path corretto: `prompts/s162_v2_sanitizer_alternatives.md`

S162-v2 = sprint investigation 30min (no execution) per matrice scelta tra:
- Path B: EasyOCR (PyTorch CPU, no AVX2)
- Path C: Tesseract + ROI manual watermark coords
- Path D: Apple Vision Framework via pyobjc

Output S162-v2 = raccomandazione singola con decision matrix + pre-flight verificato. Solo dopo S162-v2 → S163 execution.

## Lezione cumulata (S159 → S160 → S161 → S162-obsolete)

Vincolo 1 (verifica fattuale) violato 4 volte di seguito sullo stesso problem space:
- S159: assumption "Intel Mac generic" → macOS 11 vs 12 cutoff non considerato
- S160: false-positive lazy import vs init reale
- S161: blocker identificato correttamente, ma raccomandazione S162 senza pre-check ISA
- S162-obsolete: AVX2 requirement noto in CLAUDE.md ("iMac 2012 no AVX2") mai consultato in fase planning

Pattern strutturale: planning ML stack su macOS Intel/AVX1 richiede matrice **{macOS minos, CPU ISA, ABI numpy, ABI Python}** verificata PRIMA di scrivere prompt execution, non durante.

Memory feedback: vedi `feedback_false_positive_lazy_import.md` (estesa per coprire anche pre-flight ISA).
