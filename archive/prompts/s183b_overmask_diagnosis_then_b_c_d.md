# S183-bis RESUME — Diagnosi over-mask → GATE B → C → D

> Sessione precedente 2026-05-21 (S183 CTO Opus): GATE A2 redesign chiuso VERDE.
> Commit `tools/scripts/s183_autogen_zones.py` + 10 zones.json.
> Closure ordinata su gate vincolo #6: A5 baseline ha rivelato **bug strutturale test golden** che richiede diagnosi prima di GATE B.

## Stato verified (input prossima sessione)

### Committati S183 (commit hash da prossimo `git log`)
- `tools/scripts/s183_autogen_zones.py` — redesign senza plate_zone_fallback
- `tests/uat_golden/g{01..10}_*.zones.json` — 10 zones.json puliti (36 zone totali)

### Untracked pending GATE D commit
- `assets/argos_logo.png` (5541 bytes, GATE A1)
- `tests/uat_golden/g{01..10}_*.jpg` (10 golden samples raw)
- `tests/uat_golden/uat_criteria.md` (GATE A4)
- `tests/uat_golden/overlay/g{01..10}_*_overlay.png` (output script A2)
- `tests/uat_golden/baseline_s183*.log` (baseline run output)
- `tests/test_sanitizer_golden.py` (GATE A4, ripristinato post-edit)

### Out-of-scope dirty pre-esistente
- `.planning/*.md`, `.claude/settings.json`, ~50 prompts/s*.md (D) → NON toccare in S183-bis

## Day 1 Stile Car deadline
- Target: **2026-06-03** (13 giorni dal handoff oggi 2026-05-21)
- Tempo residuo realistico (lun-sab, no domenica): ~11 giorni lavorativi
- Gating sanitizer D-32: GATE B+C+D + dossier rigenerazione + UAT visual finale Luke

## GATE PRIMO: Diagnosi over-mask auto_features (NUOVO, prima di B1/B3)

### Fail mode loggato in baseline S183
A5 baseline pytest 10/10 FAIL non per "PII not modified" MA per `auto_features OVER-MASKED ratio 0.59-0.83 > 0.02`.

### Root cause confermato (sessione S183, ~14:30 reasoning)
1. `sanitize_image` fa banner crop top 18-23% + bottom 80-87% → `sanitized.size != original.size` (esempio: 1440x1080 → 1440x680)
2. Test golden linea 95-96: `if sanitized.size != original.size: sanitized = sanitized.resize(original.size, Image.LANCZOS)` → resize back a 1440x1080 stretching verticale
3. Test compara `original.crop((x1,y1,x2,y2))` vs `sanitized.crop((x1,y1,x2,y2))` con stessi pixel coords
4. Dopo resize back, pixel y=216 in sanitized = (216/1080)*680 + 200 (crop offset) = 336 in original
5. Quindi auto_features in sanitized post-resize y=216-842 corrisponde a area original y=336-856 → contenuto **shiftato** → 60-83% diff > 2%

→ **Test golden gate è strutturalmente broken** (assume sanitize_image preserva geometria; sanitizer S179b NON la preserva per design).

### 3 path correzione (decisione richiesta a Luke PRIMA di GATE B)

**Path 1 — fix test (refactor _resolve_zone post-crop)**:
- `sanitize_image` API ritorna optional `(path, crop_metadata={'top':int, 'bottom':int})` invece di solo `path: str`
- Test usa metadata per applicare auto_features zone su region POST-crop
- Backward compat: caller esistenti ignorano return tuple secondo elemento (default None)
- Costo: ~60 min refactor + test update + run sanitize_all_images smoke
- PRO: gate test rigoroso anti over-mask preservato
- CONTRO: scope sanitizer touch + smoke regression rischio

**Path 2 — disabilita auto_features check (gate solo PII modified)**:
- Commenta blocco linee 112-125 test_sanitizer_golden.py
- BACKLOG entry S184+ per fix completo Path 1
- Costo: ~5 min
- PRO: sblocca GATE A5 baseline = 10/10 PASS atteso post-patch B
- CONTRO: regression over-mask Day 1+ non rilevata automaticamente (rischio: dealer riceve foto con auto features distrutte = perdita valore listing)

**Path 3 — workaround tolerance (AUTO_TOLERANCE 0.02 → 0.85)**:
- Modifica costante linea 34
- Costo: ~1 min
- PRO: gate banale verde
- CONTRO: gate inutile (85% pixel diff accettato = qualsiasi sanitize passa)

**Raccomandazione CTO**: **Path 2 + BACKLOG Path 1**. Rationale:
- Day 1 deadline 11gg lavorativi: Path 1 mangia 1-1.5 giorni (refactor sanitize_image API ha rischio regression su sanitize_all_images)
- UAT visual Luke su sample sanitized post-patch B = gate vero qualità (memory `feedback_smoke_test_not_uat_gate.md`)
- Path 3 = falsa rassicurazione, peggio di nessun gate

**Autocritica Path 2**:
- Assunzione: UAT visual Luke detecta over-mask auto features? SI (Luke vede macchina spappolata = no-go evidente)
- Rompe a 30gg: produzione 100+ dossier, UAT visual non scala. Mitigazione: Path 1 in S184 prima di scaling oltre 5 dossier/settimana
- Sovradimensiono: NO, sto evitando scope creep

**Step diagnosi closure**: Luke approva Path scelto → applica + procede GATE B.

## GATE B — Patch sanitizer (~90 min post-diagnosi)

Vedi `prompts/s183_resume_a2_b_c_d.md` sezione GATE B dettaglio originale.

**Scope ridotto post pre-flight S183**:
- ✅ **B1 `_apply_whitelist_masks`**: top 8% + bottom 12% + sides 5% deterministic (skip interior). Insert BEFORE `_apply_solid_fills` (image_sanitizer.py:656).
- ❌ **B2 `_get_plate_zone`**: SKIP — pre-flight S183 ha confermato Vision NON detecta targhe + color signature false positive. Bbox fisso fallback = rimosso. Plate detection vera ML → BACKLOG S184+.
- ✅ **B3 `_embed_argos_branding`**: sostituisce attuale draw.text "ARGOS" linea 695 con `assets/argos_logo.png` 8% width opacity 0.70 bottom-right + EXIF SHA256 tracking.
- ✅ **B4 `_edge_density_check`**: log WARN only, no blocking.

**Funzioni esistenti verificate (sanitizer 929 LOC base intatta)**:
- `_is_interior_photo(image_path, image_index)` linea 227 ✓
- `_sample_border_color(pil_img, bbox, sample_px=3)` linea 330 ✓
- `_apply_solid_fills(cv_img, text_regions, crop_top=0)` linea 349 ✓
- `sanitize_image(image_path, output_dir, listing_id, image_index, seller_name)` linea 528 ✓ (aggiungi `vin: str = None` per B3 EXIF payload)

**Delega protocollo VOS REGOLA #0**: GATE B = 4 sub-task indipendenti → considera `Task(subagent_type='implementer')` con brief preciso (pseudocode già in s183_resume_a2_b_c_d.md GATE B). Decisione delega VS diretto = scope creep risk: implementer ha access a Bash/Edit ma necessita brief Big Sur compliant + venv path.

## GATE C — UAT visual Luke 5/5 (~30 min MANUAL)

```bash
mkdir -p /tmp/s183b_uat
~/.argos-sanitizer-venv/bin/python -c "
from src.cove.image_sanitizer import sanitize_image
import glob, os
for i, p in enumerate(sorted(glob.glob('tests/uat_golden/g0[1-5]_*.jpg'))):
    sanitize_image(p, '/tmp/s183b_uat/', listing_id='s183b_uat', image_index=i, seller_name='Autohaus Isernhagen', vin='WBA-TEST-VIN')
"
open /tmp/s183b_uat/
```

Luke valuta contro `tests/uat_golden/uat_criteria.md` C1-C5 binari:
- 5 NO consecutivi su tutti 5 sample → PASS → GATE D
- 1+ YES su 1+ sample → FAIL → diagnosi gate B → S183-ter

Verifica EXIF:
```bash
exiftool /tmp/s183b_uat/*.jpg | grep -E "User Comment|Copyright|Image Description"
```

## GATE D — Commit unico finale (~15 min)

```bash
git add assets/argos_logo.png \
        tests/uat_golden/g*.jpg \
        tests/uat_golden/uat_criteria.md \
        tests/uat_golden/baseline_s183*.log \
        tests/uat_golden/overlay/ \
        tests/test_sanitizer_golden.py \
        src/cove/image_sanitizer.py

git commit -m "feat(S183-bis): whitelist sanitizer B1 + ARGOS branding B3 (Day 1 unblock)

- _apply_whitelist_masks: top 8% + bottom 12% + sides 5% deterministic
- _embed_argos_branding: logo 8% width opacity 0.70 + EXIF SHA256 tracking
- _edge_density_check: log WARN se ratio < 0.40
- tests/uat_golden/ 10 sample + zones.json + uat_criteria.md + overlay
- tests/test_sanitizer_golden.py PII hash diff (auto_features check
  $DECISION_PATH applicato)

Fixes S179b UAT NO-GO 3/3 + S183-bis Day 1 Stile Car unblock 2026-06-03."

git push origin master
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"

# Rigenera dossier Stile Car
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"
```

UAT visual PDF finale Luke → Day 1 unblock signal.

## Vincoli HARD S183-bis

- Big Sur AVX1: SEMPRE `~/.argos-sanitizer-venv/bin/python`, MAI `python3` sistema
- NO commit prima di GATE C UAT visual 5/5 PASS
- NO scope creep oltre diagnosi over-mask + GATE B (B1+B3+B4) + C + D
- Pre-action check D-32 su ogni modifica codice
- Smoke programmatico ≠ UAT visual (memory `feedback_smoke_test_not_uat_gate.md`)
- Gate context budget #7: 50% chiudi pulito + handoff S183-ter

## Context budget atteso S183-bis

- Diagnosi over-mask + decisione Luke: +5% (read MEMORY + AskUserQuestion)
- GATE B patch (delega implementer): +15% (brief + review)
- GATE C UAT + EXIF: +5%
- GATE D commit + push + dossier: +10%
- **Target close**: ≤40% AI context

## Out-of-scope DEFERRED S184+

- Path 1 fix test golden (refactor sanitize_image API crop metadata)
- Plate detection vera (ML/CV plate recognition)
- Email seller raw photos
- Ricontatto 4 dealer burned
- Multi-seller whitelist tuning
- Edge density flag review manual queue
