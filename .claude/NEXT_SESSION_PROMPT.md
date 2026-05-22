# S183-quater — D-32 OCR false-positive fix (cherry-pick selettivo da S183-bis snapshot)

> 2026-05-22 close HARD_STOP 88%. Path C-pragmatic eseguito. UAT 3/5 PASS, **NO commit GATE D**.

## Stato close 2026-05-22

### Eseguito
- snapshot S183-bis dirty → `/tmp/image_sanitizer_s183bis_snapshot.py`
- `git checkout HEAD -- src/cove/image_sanitizer.py` (= f8e82c5 pre-S183-bis)
- `rm assets/argos_logo.png` (placeholder untracked)
- UAT 5/5 D-32 puro → `/tmp/s183ter_uat_d32pure/`

### UAT visual verdict
- 00 (g01): ✅ targa coperta, ARGOS testo bottom-left
- 01 (g02): ⚠️ targa OK ma OCR sospetto su grille
- **02 (g03): ❌ REGRESSION** — 2 BIG rect grigi invadono muso (OCR false-positive "Autohaus Isemhagen" su edge auto, no whitelist D-32 hardcoded)
- 03 (g04): ✅
- 04 (g05): ✅
**Score 3/5**, NO commit.

### Working tree
- `src/cove/image_sanitizer.py`: PULITO (= HEAD f8e82c5)
- `assets/argos_logo.png`: rimosso
- `tests/uat_golden/g*.jpg` + zones.json + uat_criteria.md + overlay/ + baseline*.log: untracked, committabili in S183-quater
- `tests/test_sanitizer_golden.py`: untracked
- `BACKLOG.md`: dirty (#S183b-1)
- Snapshot S183-bis B1+B3+B4+S183b-FILTER preservato `/tmp/image_sanitizer_s183bis_snapshot.py`

## Finding strutturale
D-32 spec (DECISIONS.md linea 845-874) prescrive **whitelist hardcoded** modelli/trim/brand MAI implementata in HEAD. S183-bis B1 (top/bottom/sides masks) era approssimazione incompleta — manca filter OCR detection vs whitelist semantica.

Root cause sample 02 regression: Apple Vision OCR matcha "Autohaus Isemhagen" (I→o) su zone non-testuali, `_apply_solid_fills` copre senza filtro semantic.

## Plan S183-quater (target ≤40% context close)

### Research-first (vincolo feedback_research_before_cto_autonomous_action.md)
1. Re-read DECISIONS.md linea 845-874 D-32 spec completa
2. Read `/tmp/image_sanitizer_s183bis_snapshot.py` → estrai selettivo:
   - **B1 whitelist_masks** (top 8% + bottom 12% + sides 5%): KEEP
   - **B3 _embed_argos_branding**: DROP (scope D-25/S185, non D-32)
   - **B4 edge density check**: KEEP (validation no-block)
   - **S183b-FILTER OCR drop** (len<4 AND central body AND not is_seller): KEEP essential per fix sample 02
3. Add D-32 whitelist hardcoded: `BMW X1/X3/X5/Serie3/Serie5`, `Mercedes Classe C/E/GLC/GLE`, `Audi A4/Q5`, trim `xDrive/quattro/AMG/M-Sport/S line`, brand `BMW/Audi/Mercedes-Benz/Volkswagen/Porsche`

### Sequence
1. Cherry-pick patch su HEAD `src/cove/image_sanitizer.py` (B1+B4+FILTER, no B3)
2. Implementa D-32 whitelist hardcoded come filter pre-`_apply_solid_fills`
3. UAT 5/5 venv su g01-g05, target 5/5 PASS visual Luke
4. Se PASS: commit GATE D unico (image_sanitizer.py + tests/uat_golden/ + BACKLOG.md) + push + ssh imac git pull + dossier BMW X3 Stile Car
5. D-25 image-shield (grid 3×3 + crop 65% + HSV + JPEG 72) → BACKLOG S185 post-Day-1

### Time budget
- Research: 10min | Cherry-pick + whitelist: 25min | UAT: 10min | Commit+push+dossier: 15min | Handoff: 5min
- Total ≤65min, ≤40% context

## Vincoli HARD
- venv `~/.argos-sanitizer-venv/bin/python`
- NO commit pre UAT 5/5 PASS Luke
- NO plate detection ML (BACKLOG S185)
- NO scope D-25 in S183-quater
- Gate 50% chiudi
- Delegation-first se patch >50 righe

## Day 1 Stile Car
- Deadline: **2026-06-03** (12gg, ~9gg lavorativi lun-sab — Luke OFF domenica)
- Gating: S183-quater GATE D + dossier BMW X3
- Rischio: >1 sessione → deadline scivola 2026-06-10

## Files critici
- `/tmp/image_sanitizer_s183bis_snapshot.py` — recovery snapshot S183-bis
- `/tmp/s183ter_uat_d32pure/` — UAT 5 sample D-32 puro (3 PASS, 2 FAIL)
- `/tmp/s183ter_research.md` — research consolidato D-25 + D-32 + Pillow + GDPR
- `~/venture-os/wiki/projects/ARGOS/DECISIONS.md` linea 845-874 — D-32 spec

## Memorie applicate sessione 2026-05-22
- feedback_research_before_cto_autonomous_action.md (creata + applicata)
- feedback_context_budget_gate.md (close ordinata)
- feedback_smoke_test_not_uat_gate.md (UAT visual 5/5 vincolo)
- vincolo CLAUDE.md #1 verifica fattuale (D-25 finding via grep DECISIONS.md)
- vincolo CLAUDE.md #4 critica strutturale 4 punti (verdetto C-pragmatic)
- vincolo CLAUDE.md #6 mai PARTIAL (handoff strutturato close)
