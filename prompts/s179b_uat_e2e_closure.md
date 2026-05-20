# S179b — Closure UAT + E2E sanitizer Pillow refactor (BLOCKER Day 1 Stile Car)

> Sessione precedente S179 (2026-05-20): implementer return VERDE (refactor `image_sanitizer.py` -73 righe + `vision_ocr.py` +9 regex trim) + smoke 3/3 PASS in `/tmp/s179_uat/`. Closure interrotta su gate context budget 50%. Modifiche NON committate, working tree dirty.

## Stato input verificato (leggi PRIMA)

1. Memory `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s179_implementer_done_uat_pending.md` (closure parziale S179)
2. Prompt originale `prompts/s179_sanitizer_d32_pillow_refactor.md` (piano completo, STEP 4-7 residui)
3. Memory `s176_partial_step4_6_green_d32_sanitizer_blocker.md` (regression evidence X1 paraurti/targa/25e)

## Pre-flight (~2min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git status --short src/cove/  # atteso: M image_sanitizer.py + M vision_ocr.py
wc -l src/cove/image_sanitizer.py src/cove/vision_ocr.py  # atteso: 929 + 230
ls -lh /tmp/s179_uat/  # atteso: 3 file 167-182KB (se cancellati, ri-run smoke STEP 2)
```

Se working tree clean (modifiche committate da Luke offline): STOP, leggi git log per stato e adatta gli step.

## STEP 0 — Code-review agent (~5min, context isolato)

Vincolo project ARGOS: non-trivial >20 righe + nuove funzioni richiede `code-reviewer` PRIMA del commit.

Delega:
```
Agent(subagent_type="code-reviewer", prompt="
Review diff src/cove/image_sanitizer.py + src/cove/vision_ocr.py (S179 D-32 refactor LaMa→Pillow).

Scope check:
- _apply_solid_fills() correctness (BGR↔RGB conversion, bbox clamping, padding logic)
- _sample_border_color() bias (bbox interno domina mean se outer ring troppo stretto)
- KEEP_WORDS coverage trim BMW/Mercedes/Audi
- vision_ocr.py TRIM_PATTERN regex false-positive risk (matcha 'a25e' per esempio?)
- Memory leak / cv2-PIL conversion overhead
- Backward compat sanitize_image() signature

Output: PASS|FAIL+issues JSON. NON committare. NON modificare file.
")
```

Se PASS → STEP 1. Se FAIL critical → fix prima di STEP 1.

## STEP 1 — UAT visual Luke side-by-side (~10-15min Luke fisico)

```bash
mkdir -p /tmp/s179b_uat/{input,output_v3_lama_legacy,output_v4_pillow}
# Sample da test S176 BMW X1 (se cache iMac disponibile)
# Fallback: 5 sample raw existenti
for i in 00 01 02 03 04; do
  cp dossiers/safe_images/raw/raw_autoscout24_de_1c29ca01cdb2_${i}.jpg /tmp/s179b_uat/input/
done

# Run sanitizer NEW (post-refactor)
python3 -c "
from src.cove.image_sanitizer import sanitize_image
import glob
for p in sorted(glob.glob('/tmp/s179b_uat/input/*.jpg')):
    idx = int(p[-6:-4])
    out = sanitize_image(p, '/tmp/s179b_uat/output_v4_pillow/', listing_id='s179b_uat', image_index=idx, seller_name='Auto Schmidt')
    print(f'{p} -> {out}')
"

# Open UAT folders per Luke ispezione visiva
open /tmp/s179b_uat/input/ /tmp/s179b_uat/output_v4_pillow/
```

**Criteri GO (Luke conferma 5/5)**:
- ✅ Targa coperta (no leak PII)
- ✅ Watermark venditore "Auto Schmidt" / dealer signage coperto
- ✅ Auto features intatte: modello (X1/X3/...), trim (xDrive 25e/30d/40i), brand (BMW/Mercedes)
- ✅ Nessun artefatto strutturale: paraurti/portellone/finestrini intatti
- ✅ Rectangle solido color-matched (no buchi neri evidenti, no sfondi bianchi)

**NO-GO trigger**: anche 1 sample con bbox eccessivo (copre logo BMW) o color mismatch evidente → STEP 0a diagnosi:
- Bbox padding (12px non-seller / 20px seller) troppo aggressivo?
- TRIM_PATTERN regex match fallisce su trim specifico?
- vision_ocr seller match false-positive su brand text?

## STEP 2 — E2E pipeline integrato (~10min)

```bash
python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 25000 --dealer "TEST_FOUNDER" --max 5
# Atteso: PDF in dossiers/ARGOS_BMW_X1_*_TEST_FOUNDER_*.pdf
ls -lt dossiers/ARGOS_BMW_X1_*.pdf | head -1
# Open PDF verifica foto inserite nelle sezioni veicolo
open dossiers/ARGOS_BMW_X1_*_TEST_FOUNDER_*.pdf
```

**Criteri GO E2E**: PDF generato senza errori, foto presenti in sezioni veicolo, qualità immagini coerente con UAT STEP 1.

## STEP 3 — Commit + push + sync iMac (~5min)

```bash
git add src/cove/image_sanitizer.py src/cove/vision_ocr.py
git commit -m "$(cat <<'EOF'
feat(S179): sanitizer D-32 Pillow-only refactor (LaMa→rectangle solid)

- Remove _inpaint_image (cv2.TELEA + SimpleLama) + _build_inpaint_mask
- Add _apply_solid_fills() Pillow rectangle direct on text bboxes
- Add _sample_border_color() 3px ring color match
- Extend KEEP_WORDS: BMW/Mercedes/Audi trim codes (25e, 30d, m340i, 45tdi, etc.)
- Add vision_ocr.py TRIM_PATTERN regex catch-all (^[a-z]?\d{2,3}[a-z]{1,5}$)
- Remove dead code: _get_simple_lama, LAMA_*/TELEA_RADIUS/LARGE_AREA_THRESHOLD

Fixes S176 regression: BMW X1 paraurti deformato, xDrive 25e inghiottita.
Compliance D-25 (Pillow-only inpaint stack), D-32 (founder decision closed).

Diff: image_sanitizer.py 1002→929 (-73), vision_ocr.py 221→230 (+9).

Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>
EOF
)"
git push origin master
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"
```

## STEP 4 — Memory closure + BACKLOG update + handoff Day 1 (~5min)

Crea memory `s179_sanitizer_pillow_verde.md` (chiusura D-32, UAT+E2E PASS, commit hash).

Update `BACKLOG.md`: spostare "🟠 PRIORITÀ 2 — S179 sanitizer refactor D-32" sotto sezione `## CLOSED` con ref commit hash.

Verifica gate condition Day 1 Stile Car:
- ✅ S178 contract E2E (chiuso)
- ✅ S179 sanitizer (chiuso ora)
- ⚠️ HITL bypass P4-bis (D-07 violation) — verifica se ancora aperto, se SÌ è gate residuo
- ⚠️ Worker 401 INVALID_TOKEN P4-ter — verifica se ancora aperto

Se TUTTI VERDE: **NON auto-generare prompt Day 1 Stile Car** (vincolo `feedback_no_live_without_test.md`). Comunicare a Luke: "Sanitizer VERDE. Gate Day 1 Stile Car: [N] blocker residui = [lista]. Day 1 sbloccato quando Luke conferma."

Se HITL bypass o Worker 401 ancora aperti: handoff `prompts/s180_hitl_bypass_fix.md` o `prompts/s180_worker_auth_fix.md` come next blocker.

## Vincoli HARD S179b

- NO scope creep — solo closure S179. HITL bypass = ticket separato S180+.
- Context budget gate: se >50% al return code-reviewer → chiudi con handoff S179c, NON proseguire con UAT/E2E.
- NO auto-prompt Day 1 reale (`feedback_no_live_without_test.md`).
- Code-review PRIMA del commit (vincolo project).

## Outcome verde S179b

- Code-review PASS
- UAT 5/5 GO Luke fisico
- E2E pipeline PDF VERDE
- Commit pushed + iMac synced
- Memory closure + BACKLOG update
- Day 1 Stile Car gate status documentato (NO auto-prompt)

## Context budget atteso S179b

- Start: ~15-20% (lettura memory S179 + status check)
- STEP 0 code-review (isolato): +3%
- STEP 1-2 UAT+E2E: +10-15%
- STEP 3-4 commit + memory + handoff: +5%
- **Target close**: ≤45%
