# S191 — Commit dirty sanitizer come pre-filter soft

> Sessione S190 chiusa VERDE 2026-05-26 con commit `7002a42` HITL approval gate.
> S191 chiude la coda lunga: commit dei 2 file dirty pre-esistenti S187/S188
> come pre-filter soft (best-effort, NON è più il gate anti-leak — quello è HITL).

---

## 0. Identità sessione

- **Progetto**: ARGOS Automotive
- **Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- **Branch**: `master`
- **Data riferimento**: 2026-05-26 (S190 closure), S191 prossima sessione
- **Deadline business**: Day 1 Stile Car 2026-06-03 (sbloccata su gate-leak da S190)

## 1. Stato post-S190

### Commit applicato (master)
```
7002a42 feat(S189+S190): HITL approval gate dossier pre-invio WA
554+/3-  7 files
```

### Working tree dirty (2 file pre-esistenti S187/S188)
```
src/cove/image_sanitizer.py               (+266 / -... =) 266+ righe
tools/scripts/pdf_generator_enterprise.py (+39  / -... =)  39+ righe
```

### Stato pipeline
- E2E gate HITL VERDE: bypass impossibile, race-safe, path traversal blocked
- Day 1 Stile Car SBLOCCATO axis gate-leak
- Sanitizer over-mask **non più blocker** post-pivot S188 (HITL è il gate)
- Sanitizer rimane "soft pre-filter" — Luke vede già foto puliti per maggioranza

## 2. Obiettivo S191

Committare i 2 file dirty come **pre-filter soft**, con commit message che:
- Documenta che NON è più il gate (HITL S190 è il gate)
- Spiega cosa fanno gli aggiornamenti S187 (fix invocazione sanitizer)
- Non promette over-mask risolto (Luke vede comunque PDF in HITL pre-invio)

## 3. STEP S191

### STEP 0 — Pre-flight

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git log --oneline -3                                       # 7002a42 in HEAD
git status --short src/cove/ tools/scripts/                # 2 file dirty
git diff --stat src/cove/image_sanitizer.py tools/scripts/pdf_generator_enterprise.py
```

### STEP 1 — Read context delta su 2 file

```bash
git diff src/cove/image_sanitizer.py | head -150
git diff tools/scripts/pdf_generator_enterprise.py | head -80
```

Identifica:
- Cosa fa il delta `image_sanitizer.py` (probabile: fix invocazione S187 + filter G logic)
- Cosa fa il delta `pdf_generator_enterprise.py` (probabile: integration sanitizer call site)

### STEP 2 — Code-review delegata (vincolo CLAUDE.md #0)

Delega `code-reviewer` sui 2 diff. Focus:
- Sanitizer NON deve regredire baseline (5/5 sample T7 S188 net zero ok)
- Pillow-only stack (no PaddleOCR/Vision Framework regression)
- No crash su missing fields
- Big Sur macOS 11 compat

Se issue HIGH → fix prima del commit (anti-pattern S190 false-confident pre-commit replicato).

### STEP 3 — Smoke test su 1 sample T7

```bash
# Verifica sanitizer chiamabile + non crasha
~/.argos-sanitizer-venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from cove.image_sanitizer import sanitize_image
out = sanitize_image('/Volumes/MontereyT7/argos-poc/S188/sample_01.jpg', seller_name='TestSeller')
print('SANITIZE_OK', out)
"
```

### STEP 4 — Commit scoped

```bash
git add src/cove/image_sanitizer.py tools/scripts/pdf_generator_enterprise.py
git commit -m "feat(S187+S191): sanitizer pre-filter soft + invocation fix

- image_sanitizer.py: fix invocazione S187 (chiamata reale da
  generate_opportunity_dossier), filter G logic Pillow-only stack,
  +266 righe (vedi git diff per dettaglio).
- pdf_generator_enterprise.py: integration call site sanitizer
  pre-embed images, +39 righe.

CONTEXT: post-S190 HITL approval gate (commit 7002a42) il sanitizer
NON è più il gate anti-leak. Luke approva manualmente ogni dossier
pre-invio WA. Sanitizer resta pre-filter best-effort.

Baseline UAT S188 5/5 sample T7: filter G net zero gain. Non si
promette over-mask risolto — quello è gestito da HITL review Luke.

Refs: prompts/s191_sanitizer_dirty_commit.md, memory s188_closure_pivot_hitl.md"

git push origin master
```

### STEP 5 — Verify working tree clean (in-scope)

```bash
git status --short src/cove/ tools/scripts/
# Atteso: vuoto
```

### STEP 6 — Memory update + closure

Aggiungi memory `s191_closure_sanitizer_committed.md` + index MEMORY.md.

## 4. PASS criteria S191

- [ ] STEP 0 pre-flight verde
- [ ] STEP 1 diff context capito
- [ ] STEP 2 code-review PASS o issue fixati
- [ ] STEP 3 smoke 1 sample T7 verde
- [ ] STEP 4 commit + push
- [ ] STEP 5 working tree clean (in-scope)
- [ ] STEP 6 memory entry

## 5. Out-of-scope espliciti S191

- ❌ Risolvere over-mask sanitizer (gestito da HITL, baseline accepted)
- ❌ Fix BUG-S189-INFRA-1 / INFRA-2 (sessione dedicata, consenso Luke)
- ❌ Backfill approval_user (BACKLOG S190-BL-1)
- ❌ Touch cove_engine_v4.py, scrapers, daemon

## 6. Time-box S191

Sessione corta: target ~20min execution. Se context >40% chiudere e handoff.

## 7. Dopo S191

- Day 1 Stile Car 2026-06-03 ready su axis gate-leak
- Workflow operativo: founder genera dossier → daemon registra PENDING →
  Luke approva dashboard → daemon invia → dealer riceve

## 8. Vincoli CLAUDE.md applicati

- #0 delegation-first: code-reviewer STEP 2
- #4 critica strutturale: smoke STEP 3 prima commit, NON trust pre-existing changes
- #6 no PARTIAL: 6/6 verde o handoff strutturato
- #7 context budget: chiudere ~40% (S190 lesson)
