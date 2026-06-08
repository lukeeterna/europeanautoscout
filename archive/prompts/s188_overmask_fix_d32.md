# S188 — Fix over-mask D-32 sanitizer (UAT NO-GO ricaduta)

## Stato ereditato da S187
- Implementer DONE: `generate_opportunity_dossier:1119` ora invoca `_sanitize_photo` prima `apply_watermark` (fail mode #1 D-32 CHIUSO strutturalmente)
- Validator 8/8 PASS, 5 issue non-blocking (dead code, stale env var/comment, working tree dirty)
- UAT visual Luke 5 sample T7 BMW DE → **NO-GO 1/5 FAIL over-mask + 1/5 ambiguo**
- Working tree: 2 file modificati NON committati
  - `tools/scripts/pdf_generator_enterprise.py` +27/-8 (sanitize loop, seller_name, _find_sanitizer probe Vision)
  - `src/cove/image_sanitizer.py` +258/-14 (3-verdict classifier, branding ARGOS rimosso)

## UAT findings Luke S187
| Sample | Verdict | Dettaglio |
|--------|---------|-----------|
| 01.jpg | SKIP | thumbnail 28KB <30KB threshold, comportamento corretto |
| 03.jpg | AMBIGUO | "buona parte testo coperta" — residuo da chiarire S188 step 0 |
| 04.jpg | PASS | targa coperta con successo |
| 05.jpg | **FAIL** | rettangolo piccolo OK targa + rettangolo grande inutile sovrapposto auto |
| 09.jpg | PASS | no operazione su no-targa (solo portatarga vuoto) |

## Root cause over-mask (pattern noto)
Memory ricaduta:
- `s179b_uat_nogo_handoff_s183.md` — Pillow refactor NO-GO 3/3
- `s183_a2_closure_overmask_diagnosis_handoff_s183b.md` — auto_features check shifta pixel
- `s183b_close_visual_pass_handoff_s183ter.md` — logo placement errato (logo NON va su auto, va sopra targa)
- `sanitizer_isolation_test_plate_invisible_to_vision.md` — Vision OCR text-only generico

Vision OCR `_detect_text_regions` trova SIA regioni "da maskare" (targa, watermark, seller text) SIA regioni "da NON maskare" (testo interno dashboard, etichette auto). Mask builder non discrimina.

## Step S188

### STEP 0 — Chiarire sample 03 ambiguo
Apri `/tmp/argos_validator_d32/uat/argos_val_03_00.jpg` + originale `/Volumes/MontereyT7/argos-poc/S187/inputs/03.jpg` side-by-side.
Determinare: testo residuo è leak dealer (FAIL hard) o testo legittimo auto (PASS).

### STEP 1 — Diagnosi over-mask sample 05
Pre-flight: cosa rileva Vision OCR su `/Volumes/MontereyT7/argos-poc/S187/inputs/05.jpg`?
```
~/.argos-sanitizer-venv/bin/python -c "
from src.cove.vision_ocr import get_vision_ocr
regions = get_vision_ocr().detect_text('/Volumes/MontereyT7/argos-poc/S187/inputs/05.jpg', conf_min=0.30)
for r in regions: print(r)
"
```
Identificare quale regione è il "rettangolo grande inutile" → coordinate + testo letto + confidence.

### STEP 2 — Filter logic
Patch `image_sanitizer.py::_detect_text_regions` per scartare regioni non-target:
- Whitelist target: targa (plate pattern), watermark dealer (logo+url+telefono), seller name (blocklist)
- Blacklist mask: testo dashboard interno auto, etichette pneumatico, cluster auto features (HUD, navigation overlay)

Decisione tecnica chiusura: filter geometrico (aspect ratio + area %) o filter semantico (regex contenuto testo)? Architect deciderà dopo STEP 1 evidence.

### STEP 3 — Re-UAT 5 sample
Stessa procedura S187 — gate 5/5 PASS pixel-level Luke. Se ROSSO ancora, escalation S189 con architect-VOS deep research alternative inpaint (LaMa Colab ricontrollato S163).

### STEP 4 — Commit scoped SE 5/5 PASS
```
git add tools/scripts/pdf_generator_enterprise.py src/cove/image_sanitizer.py
git commit -m "fix(D-32): sanitizer invocato in generate_opportunity_dossier + over-mask filter"
```
NO push fino approvazione Luke.

## Vincoli
- Sample T7 reali OBBLIGATORIO (no /tmp/ sintetici, lezione `feedback_smoke_test_not_uat_gate.md`)
- Day 1 Stile Car deadline 2026-06-03 (8gg da oggi 2026-05-25)
- Context budget gate 50% applicato (vincolo #7)
- NO 4° progetto attivo, NO scope creep verso S188-bis senza chiudere over-mask

## Critica strutturale anti-loop
Pattern S179b → S183 → S183-bis → S183-ter → S187 → S188 = 5 iterazioni stesso bug over-mask. Se S188 non chiude pixel-VERDE, escalation NON è un'altra iterazione S189 incrementale — è pivot strategico:
- Path 1: HITL gate Luke pre-invio PDF (no fix software, accetta limit Vision OCR)
- Path 2: foto venditore EU sostituite con stock manufacturer photos (D-30 BACKLOG)
- Path 3: VOS deep research plate-detector dedicato free-tier (S186 esito C riaperto)

S188 = ultima iterazione fix incrementale. Oltre, pivot.
