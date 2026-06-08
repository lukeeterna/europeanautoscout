# S188 RESUME PROMPT — Fix over-mask D-32 sanitizer ARGOS

> **Incolla questo prompt in nuova sessione Claude Code. Context vuoto assunto. Idempotente: rieseguibile senza side-effect.**

---

## 0. Identità sessione

- **Progetto**: ARGOS Automotive (vehicle scouting B2B EU→IT)
- **Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- **Branch**: `master`
- **Data riferimento**: 2026-05-25 (precedente sessione)
- **Sessione corrente**: S188
- **Deadline business**: Day 1 Stile Car 2026-06-03 (8gg da 25/05)

## 1. Vincolo context — NON NEGOZIABILE

- Esegui `/context` al turno 1, turno 5, turno 10
- Soglia 50% → no nuovo scope, findings → BACKLOG
- Soglia 60% → chiusura ordinata con handoff S189 strutturato (vincolo #6 CLAUDE.md, vincolo #7)
- Se prompt resume parte già >35%: prune skill/memorie non rilevanti PRIMA di STEP 0
- Stato dirty repo preservato come safety: NO `git stash`, NO `git checkout --`, NO commit automatici

## 2. Pre-flight verifica idempotente

Esegui SEMPRE come primo passo, prima di qualsiasi modifica:

```bash
# Verifica working tree dirty preservato S187
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git status --short tools/scripts/pdf_generator_enterprise.py src/cove/image_sanitizer.py
# Atteso: " M tools/scripts/pdf_generator_enterprise.py" + " M src/cove/image_sanitizer.py"
# SE PULITO → STOP, qualcuno ha committato/scartato, leggi git log master -5 prima di procedere

# Verifica venv sanitizer + smoke import
~/.argos-sanitizer-venv/bin/python -c "from src.cove.image_sanitizer import sanitize_image; from src.cove.vision_ocr import get_vision_ocr; print('ok')"
# Atteso: "ok" exit 0
# SE FAIL → diagnosi venv pyobjc prima di STEP 0 (lezione S160→S161 false-positive lazy import)

# Verifica sample T7 montato + presenti
ls /Volumes/MontereyT7/argos-poc/S187/inputs/05.jpg /Volumes/MontereyT7/argos-poc/S187/inputs/03.jpg
# SE T7 unmounted → mount + verifica os.path.ismount('/Volumes/MontereyT7')

# Verifica output validator S187 (per side-by-side UAT)
ls /tmp/argos_validator_d32/uat/argos_val_03_00.jpg /tmp/argos_validator_d32/uat/argos_val_05_00.jpg
# SE assenti → rigenera STEP 0-bis (sanitize_image su sample 03+05 con seller_name="Felix")
```

## 3. Reading order obbligatorio

In ordine, prima di agire:

1. `prompts/s188_overmask_fix_d32.md` — handoff completo S187→S188, 4-step + anti-loop
2. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s187_closure_overmask_nogo.md` — root cause + UAT findings Luke
3. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/sanitizer_isolation_test_plate_invisible_to_vision.md` — 4 fail mode strutturali D-32
4. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s183_a2_closure_overmask_diagnosis_handoff_s183b.md` — pattern over-mask noto pre-S187
5. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s179b_uat_nogo_handoff_s183.md` — prima ricaduta over-mask 3/3 NO-GO
6. `.claude/rules/cove.md` + `.claude/rules/security.md` — vincoli terminologia + security

## 4. Stato ereditato S187 (immutable, fact-checked)

### 4.1 Implementer + Validator: VERDE strutturale 8/8
- `generate_opportunity_dossier:1119` invoca `_sanitize_photo` PRIMA `apply_watermark` (fail mode #1 D-32 CHIUSO)
- `_find_sanitizer_python:1567` probe `paddleocr` → `from src.cove.image_sanitizer import sanitize_image`
- `_sanitize_photo` accetta `seller_name` param
- `image_sanitizer.py` branding ARGOS `draw.text` rimosso (no doppio watermark)
- 6 issue code-reviewer risolti

### 4.2 UAT visual Luke 5 sample T7 BMW DE: NO-GO

| Sample | Verdict Luke | Dettaglio testuale |
|--------|--------------|--------------------|
| 01.jpg | SKIP corretto | thumbnail 28KB <30KB threshold input |
| 03.jpg | AMBIGUO | "buona parte testo coperta" — residuo da chiarire S188 STEP 0 |
| 04.jpg | PASS | targa coperta con successo |
| 05.jpg | **FAIL over-mask** | rettangolo piccolo OK targa + rettangolo grande inutile sovrapposto auto |
| 09.jpg | PASS | no operazione (no-targa, solo portatarga vuoto) |

### 4.3 File dirty NON committati
- `tools/scripts/pdf_generator_enterprise.py` +27/-8
- `src/cove/image_sanitizer.py` +258/-14
- Commit SOLO se S188 UAT 5/5 PASS pixel-level

## 5. Root cause over-mask (verificato da memory S183-bis)

Vision OCR `_detect_text_regions` è text-detector generico:
- Trova SIA regioni TARGET (targa, watermark dealer, seller name)
- Trova SIA regioni NON-TARGET (testo dashboard interno, etichette pneumatico, cluster HUD, navigation overlay)
- Mask builder NON discrimina → wipa anche regioni legittime auto

Pattern ricaduta: S179b → S183 → S183-bis → S183-ter → S187 → S188 = 5 iterazioni stesso bug strutturale.

## 6. STEP S188

### STEP 0 — Verdict sample 03 (richiede Luke)

Side-by-side comparison:
```bash
open /tmp/argos_validator_d32/uat/argos_val_03_00.jpg /Volumes/MontereyT7/argos-poc/S187/inputs/03.jpg
```

Chiedi a Luke quale testo è rimasto visibile nel sanitized (logo dealer, URL, telefono, scritte cruscotto, etichetta auto, altro). Da risposta classifica 03 PASS o FAIL e aggiorna scoreboard.

### STEP 1 — Diagnosi over-mask sample 05 (evidence collection, no agent)

Dump Vision OCR raw su sample 05 per coordinate rettangoli rilevati:
```bash
~/.argos-sanitizer-venv/bin/python <<'PY'
from src.cove.vision_ocr import get_vision_ocr
import json
ocr = get_vision_ocr()
regions = ocr.detect_text('/Volumes/MontereyT7/argos-poc/S187/inputs/05.jpg', conf_min=0.30)
for r in regions:
    print(json.dumps({
        'text': r.get('text', ''),
        'bbox': r.get('bbox', None),
        'conf': r.get('confidence', None),
        'area_pct': None,  # calcolare post hoc
    }))
PY
```

Output atteso: lista regioni con coordinate. Identifica visualmente quale corrisponde al "rettangolo grande inutile" che copre auto. Salva dump in `/tmp/s188_05_vision_dump.json` per uso STEP 2.

### STEP 2 — Patch filter logic (delega architect → implementer)

Decisione tecnica filter — basata su STEP 1 evidence, NON a priori:
- Se rettangolo grande inutile ha bbox aspect_ratio simile a auto features (es. HUD largo+basso) → filter geometrico (aspect ratio + area_pct min/max)
- Se rettangolo grande inutile è testo cruscotto leggibile (es. "BMW", "ConnectedDrive") → filter semantico (regex whitelist target: pattern targa EU + URL dealer + telefono, blacklist auto-brand text)

Brief architect con dati STEP 1 inline. NO patch senza evidence. NO multi-path A/B.

### STEP 3 — Re-UAT 5 sample T7

Rigenera `/tmp/argos_validator_d32/uat/` con patch STEP 2 applicata:
```bash
~/.argos-sanitizer-venv/bin/python <<'PY'
from src.cove.image_sanitizer import sanitize_image
import os
SAMPLES = ['01', '03', '04', '05', '09']
OUTPUT = '/tmp/argos_validator_d32/uat/'
os.makedirs(OUTPUT, exist_ok=True)
for s in SAMPLES:
    inp = f'/Volumes/MontereyT7/argos-poc/S187/inputs/{s}.jpg'
    out = sanitize_image(inp, output_dir=OUTPUT, listing_id=f'val_{s}', image_index=0, seller_name='Felix')
    print(f'{s}: {out}')
PY
```

Apri Finder per UAT visual Luke 5/5 binario:
```bash
open /tmp/argos_validator_d32/uat/
```

Gate: 5/5 PASS pixel-level Luke. <5/5 → NO commit, escalation STEP 5.

### STEP 4 — Commit scoped SE 5/5 PASS

```bash
git add tools/scripts/pdf_generator_enterprise.py src/cove/image_sanitizer.py
git commit -m "fix(D-32): sanitizer invocato in generate_opportunity_dossier + over-mask filter

- _find_sanitizer_python probe Vision (S163) non più PaddleOCR
- _sanitize_photo accetta seller_name
- generate_opportunity_dossier riusa pattern generate_dossier_from_data
- image_sanitizer: rimosso branding ARGOS interno (apply_watermark lo fa)
- filter mask regions: [DESCRIVERE FILTER STEP 2]
- UAT visual Luke 5/5 PASS su sample T7 BMW DE

Refs: prompts/s188_overmask_fix_d32.md, memory/s187_closure_overmask_nogo.md"
# NO push fino verifica Luke
```

### STEP 5 — Anti-loop gate (se UAT NO-GO ancora)

S188 = ULTIMA iterazione fix incrementale dopo 5 ricadute. NO-GO → NON aprire S189-bis-bis. Pivot strategico, decisione singola dopo VOS deep research:

```bash
# Prompt Claude.ai esterno o skill VOS deep research per scegliere pivot:
```

#### Prompt Claude.ai esterno pre-confezionato (se serve second opinion)
```
Sono Luke (Gianluca Di Stasi), founder ARGOS Automotive (vehicle scouting B2B EU→IT).
Dopo 5 iterazioni fallite (S179b/S183/S183-bis/S183-ter/S187/S188) di sanitizer
image plate+dealer-watermark via Vision OCR Apple Framework + masking,
ho UAT pixel-level NO-GO ricorrente per pattern over-mask
(detector text-only generico maska anche regioni legittime auto).

Vincoli:
- Zero cost (€240/mese Claude Code, no subscription paid aggiuntive)
- macOS 11 Big Sur (no upgrade OS), wheel ML stack limitate
- Free-tier first (no API cloud paid)
- Deadline 9gg da decisione
- Dataset: foto AS24 dealer DE laterali/posteriori, ~20-50% mostrano targa frontale

Pivot candidate (tu valuta):
1. HITL: Luke review manuale ogni PDF pre-invio dealer (tempo Luke ~5min/PDF, ~20 PDF/mese)
2. Foto manufacturer stock: sostituire foto venditore EU con foto BMW/MB stock
   (no targa, no watermark, ma perde dettaglio veicolo reale)
3. Plate-detector dedicato free-tier: YOLO-plate-EU pretrained
   (poll HF Hub paper search per modelli license-permissive verificati 2026)

Output richiesto:
- raccomandazione singola motivata con dati (NON lista A/B/C)
- 3 rischi concreti del path scelto a 30/60gg
- exit criteria misurabile per validare pivot success
```

#### Skill VOS deep research alternativa
Se preferisci internal: `Skill(skill="vos-scout", args="plate-detector free-tier macOS 11 compatible 2026")`.

## 7. PASS criteria S188 binari

- [ ] STEP 0: sample 03 verdict chiarito (PASS o FAIL motivato)
- [ ] STEP 1: dump Vision OCR sample 05 salvato `/tmp/s188_05_vision_dump.json`
- [ ] STEP 2: patch filter applicata, syntax valida (`python3 -c "import ast; ast.parse(open(F).read())"`)
- [ ] STEP 3: 5/5 sample sanitized produced, file size 50-500KB sensible range
- [ ] UAT pixel-level Luke: 5/5 PASS binario (no ambigui, no FAIL)
- [ ] STEP 4: commit SOLO se UAT verde
- [ ] STEP 5: pivot decision SE NO-GO, no S189 incrementale

## 8. Vincoli operativi (CLAUDE.md cross-ref)

- **Vincolo #1 fact check**: ogni claim tecnico verificato con `--help` o doc upstream
- **Vincolo #3 no liste A/B**: raccomandazione singola motivata, mai "scegli tu"
- **Vincolo #4 critica strutturale**: 4 punti autocritica dopo ogni proposal
- **Vincolo #6 no PARTIAL**: sessione verde o handoff S189 con prompt resume identico struttura
- **Vincolo #7 context**: gate 50/60% obbligatorio
- **Vincolo #8 preflight**: `pip install --dry-run` se installi blacklist libs
- **Vincolo #10 verificato > verosimile**: smoke real, non claim
- **Vincolo #13 pre-action D-XX**: nessun progetto DECISIONS.md target qui, skip

## 9. Out-of-scope espliciti

NON toccare in S188:
- `generate_dossier_from_data` (rings 1-3 verified S157)
- `generate_vehicle_sheet` PDF render (ring 4 verified)
- `cove_engine_v4.py` (terminology IMMUTABLE)
- Scrapers (verificati S157, listing produzione)
- `wa-daemon` o `dashboard` (no D-32 dependency)

Working tree dirty OUT-OF-SCOPE (NON committare in commit S188):
- `on_demand_runner.py`, `dealer_discovery/config.py`, `auth.py` — modifiche pre-esistenti non-D-32

## 10. Handoff S189 template (SE NO-GO)

Se S188 chiude NO-GO, scrivi `prompts/s189_resume_prompt.md` con identica struttura (10 sezioni) + esito pivot decision STEP 5 + nuova deadline aggiornata.

NO PARTIAL/ARANCIONE — verde o handoff strutturato.
