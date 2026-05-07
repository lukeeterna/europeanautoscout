# S160 — Risolvere blocker sanitizer cv2 dylib (post S159 PARTIAL)

**Stato**: S159 ha installato venv `~/.argos-sanitizer-venv/` con paddleocr 3.5 + paddlepaddle 3.0 + opencv 4.9, ma `import paddleocr` fallisce su MacBook (macOS 11) per `libtesseract.5.dylib` built per macOS 12.0.

**Goal S160**: rendere sanitizer operativo. Day 1 reale Stile Car bloccato fino a quando questo non è verde.

**Timebox**: 45min totali, hard stop a context 50%.

---

## Step 1 — Tentativo B (10min) — skip opencv-contrib-python

Verifica se paddleocr 3.5 funziona senza contrib:

```bash
~/.argos-sanitizer-venv/bin/pip uninstall -y opencv-contrib-python
~/.argos-sanitizer-venv/bin/python -c "import paddleocr; print('OK', paddleocr.__version__)"
```

**Esito GREEN**: `OK 3.5.0` → procedi Step 3 (smoke test sanitizer)
**Esito RED**: `ImportError: cv2 / libtesseract` → procedi Step 2 (path A)

## Step 2 — Tentativo A (30min) — sanitizer su iMac via SSH

Se Step 1 fallisce, sposta sanitizer su iMac (macOS 12.7.4 compat):

1. SSH iMac, crea venv stesso pattern:
   ```bash
   ssh gianlucadistasi@192.168.1.2 "/usr/local/bin/python3.11 -m venv ~/.argos-sanitizer-venv && \
     ~/.argos-sanitizer-venv/bin/pip install --prefer-binary paddleocr paddlepaddle opencv-contrib-python pillow numpy"
   ```
2. Verifica `import paddleocr` su iMac
3. Modifica `_sanitize_photo()` in `tools/scripts/pdf_generator_enterprise.py` line ~1582 per:
   - rsync immagine raw a iMac `/tmp/argos_sanitize_in/`
   - SSH execute sanitize_image via venv iMac
   - rsync risultato back a MacBook `/tmp/argos_sanitize_out/`
   - **OR (più semplice)**: spostare TUTTA la PDF generation su iMac come PM2 process, MacBook trigger via HTTP

**Decisione architetturale**: se Step 2 attivo, valutare se PDF generation interamente su iMac sia path canonical (riusa infra PM2 + tailscale). Altrimenti SSH sync round-trip è ~3-5s/img × 6 = 18-30s overhead per dossier.

## Step 3 — Smoke test sanitizer (10min, solo se Step 1 o 2 verde)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
python3 tools/on_demand_runner.py --marca BMW --budget 40000 --dealer "Smoke S160"
```

**Verifica nel log**:
- `[SANITIZER] Using ~/.argos-sanitizer-venv/bin/python (has PaddleOCR)` ✓
- `[OCR] N text region(s) to mask` ✓
- `[INPAINT] NK pixels masked` ✓
- `SANITIZED: argos_<id>_NN.jpg` (NON `INTERIOR:` o assenza)

**Visual inspection PDF**:
- Aprire PDF generato, verificare che almeno 1 immagine sia stata sanitizzata
- Ricerca visiva: targhe blur ✓, watermark dealer rimosso ✓, logo "ARGOS" oro in basso-sx ✓

## Step 4 — Closure (5min)

1. Update `BACKLOG.md` → marker FIXED S160 sull'entry "Image Sanitizer (PaddleOCR) NON OPERATIVO"
2. Update `HANDOFF.md` → STATO CORRENTE S160 VERDE
3. Update `MEMORY.md` → entry S160 closure
4. Commit `fix(s160): sanitizer paddleocr operativo via [path B|A]`
5. Push

## Stop criteria

- VERDE: smoke test produce PDF con almeno 1 immagine sanitizzata visualmente verificata
- ARANCIONE: tutti i path (B, A, C) falliscono → escalation a Luke con proposta D (Docker) o downgrade scope (manual photo crop pre-PDF, no OCR)

## NON fare in S160

- NO Day 1 reale automatico (regola `feedback_no_live_without_test.md`)
- NO refactor PDF generator beyond _find_sanitizer_python e _sanitize_photo
- NO Docker setup (defer escalation Luke)

## Refs

- `s159_partial_blocker.md` — analisi 4 path alternativi
- `s159_paddleocr_research.md` — Python 3.11 sweet spot, Intel Mac
- `feedback_context_budget_gate.md` — closure forzata >50% context
- `feedback_decision_support.md` — pattern analisi+raccomandazione
