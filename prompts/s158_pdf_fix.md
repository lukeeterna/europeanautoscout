# S158 — PDF dossier fix (5KB → dossier dealer-grade)

**Sessione**: S158 (clean context start)
**Scope**: fix `tools/scripts/pdf_generator_enterprise.py` — il dossier generato S157 era 5,296 bytes nonostante 6 immagini scaricate OK (≥18KB cad). Template non incorpora binarie. Risultato: PDF inutilizzabile per Day 1 reale.
**Tempo stimato**: ~45min autonomo (timebox 60min)
**Rischio dealer**: ZERO — nessun outreach, nessun messaggio.
**Path critico**: sblocca S159 (test founder interattivo) → S160 (Day 1 reale Stile Car).

---

## Pre-condizioni S158

| Check | Verifica |
|-------|----------|
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh ... "curl -s localhost:9191/status"` → `connected` |
| tailscaled standalone | `ssh ... "ps aux \| grep tailscaled \| grep -v grep"` mostra PID |
| PM2 daemons | `ssh ... "pm2 list"` (con PATH fix) → argos-wa-daemon + argos-cf-monitor online |
| Pipeline E2E S157 OK | `python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 35000 --dealer "S158_PRECHECK"` → PDF generato (anche se 5KB) |

🛑 Se KO: recovery via `docs/ops/tailscaled-runbook.md` PRIMA, poi S158.

---

## Phase 1 — Riproduzione + diagnosi PDF generator (~15min)

### 1.1 Genera PDF di test S157 (baseline)
```bash
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 35000 --dealer "S158_BASELINE" 2>&1 | tail -20
ls -la dossiers/ARGOS_BMW_*S158_BASELINE*.pdf dossiers/ARGOS_BMW_*S158_BASELINE*.json | tail -5
```
Atteso: PDF ~5KB, JSON ~5KB con `vehicles[].image_urls` populated.

### 1.2 Ispeziona PDF struttura
```bash
file dossiers/ARGOS_BMW_*S158_BASELINE*.pdf
# Estrai testo per verificare contenuto
pdftotext dossiers/ARGOS_BMW_*S158_BASELINE*.pdf - 2>&1 | head -40 || echo "pdftotext non disponibile"
# Conta immagini embedded
pdfimages -list dossiers/ARGOS_BMW_*S158_BASELINE*.pdf 2>&1 | head -20 || echo "pdfimages non disponibile"
```

### 1.3 Leggi pdf_generator_enterprise.py
```bash
wc -l tools/scripts/pdf_generator_enterprise.py
head -60 tools/scripts/pdf_generator_enterprise.py
grep -nE "image|Image|reportlab|weasyprint|pdfkit|fpdf" tools/scripts/pdf_generator_enterprise.py | head -30
```

Identifica:
- Engine PDF (reportlab / weasyprint / pdfkit / fpdf2 / altro)
- Codice che inserisce immagini nel PDF
- Eventuale `try/except` che skippa silenziosamente le immagini

### 1.4 Hypothesis check
```bash
# Cerca log "Image OK: N bytes" della run S157 — significa immagini scaricate, ma poi non incluse?
# Verifica path immagini scaricate
ls /tmp/argos_*pdf*/*.jpg /tmp/argos_*pdf*/*.webp 2>/dev/null | head -5
# Verifica se sanitizer le ha cancellate
grep -nE "sanitiz|tmp.*image|os.remove|shutil" tools/scripts/pdf_generator_enterprise.py | head -10
```

### 1.5 Documenta findings
Crea `.planning/S158-PDF-DIAGNOSIS.md` con:
- Engine PDF + versione lib
- Path codice rotto (file:line)
- Hypothesis: (a) immagini scaricate ma path errato in template, (b) sanitizer cancella prima di embed, (c) template HTML/PDF non ha `<img>` tag, (d) reportlab Image() flow non chiamato, (e) altro
- Reproduction step-by-step

---

## Phase 2 — Fix mirato (~25min)

### Caso A: path immagini errato
Verifica `image_urls` nel JSON dossier vs path filesystem usato nel template.

### Caso B: sanitizer cancella troppo presto
Riordina flow: download → embed in PDF → sanitize/cleanup. Mai cleanup prima di PDF write.

### Caso C: template HTML manca img tag
Aggiungi `<img src="{{vehicle.image_path}}" />` con alt + size constraints.

### Caso D: reportlab Image() non chiamato
Aggiungi `from reportlab.platypus import Image` + `flowables.append(Image(path, width=400, height=300))` per ogni immagine.

### Caso E: altro
Documenta in BACKLOG, propone alternative minimal (pillow-to-PDF concat se template è troppo broken).

---

## Phase 3 — Validation (~15min)

### 3.1 Test rigenerazione
```bash
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 35000 --dealer "S158_VALIDATION" 2>&1 | tail -10
# GREEN GATE: PDF size > 200KB (dossier dealer-grade con 6 immagini ~20KB cad embedded)
ls -la dossiers/ARGOS_BMW_*S158_VALIDATION*.pdf
```

### 3.2 Cross-brand test
```bash
python3 tools/on_demand_runner.py --marca Mercedes --modello "GLC" --budget 45000 --dealer "S158_VALIDATION_MB" 2>&1 | tail -10
ls -la dossiers/ARGOS_Mercedes_*S158_VALIDATION_MB*.pdf
# GREEN GATE: PDF size > 200KB
```

### 3.3 Visual inspection
```bash
# macOS open PDF
open dossiers/ARGOS_BMW_*S158_VALIDATION*.pdf
```
Luke conferma visivamente:
- Tutte le immagini sono visibili nel PDF
- Layout dealer-grade (no template breaking)
- Numeri prezzo/km/anno visibili
- Brand ARGOS visibile

🔴 Se non green: documenta `.planning/S158-PARTIAL.md` + hypothesis fix S158-bis.

---

## Phase 4 — Docs + commit (~5min)

- [ ] `.planning/S158-PDF-DIAGNOSIS.md`: findings + fix applicato
- [ ] `BACKLOG.md`: marca "PDF dossier size 5KB sospetto" → ✅ FIXED S158
- [ ] `HANDOFF.md`: STATO CORRENTE → S158 CHIUSO VERDE
- [ ] Memory `s158_pdf_fix.md` entry
- [ ] Commit: `fix(s158): pdf dossier embed images correctly` o variant
- [ ] Push

---

## Phase 5 — STOP (regola feedback_no_live_without_test.md)

🛑 NESSUN prompt S159 auto-creato. Luke deciderà next sprint:
- **S159 TEST FOUNDER INTERATTIVO** (CON Luke davanti, smoke E2E con dossier reale S158)
- **Iteration PDF** (se PARTIAL S158)
- **Altro sprint**

---

## Vincoli S158

- ✋ NO outreach dealer reale
- ✋ NO messaggi WA a numeri ≠ TEST_FOUNDER
- ✋ NO modificare `src/cove/cove_engine_v4.py` (rule cove.md)
- ✋ NO modificare scraper `tools/scrapers/autoscout_scraper.py` (già verde S157)
- ✋ Timebox 60min — se non risolto, documenta PARTIAL e ferma

---

## Out of scope S158

- Test founder interattivo → S159
- Day 1 dealer reale → S160
- CoVe engine refactor → defer
- Health monitoring → defer
- Day 1 sequence revision V4 → defer
- Context budget gate (3 componenti hook/regola/statusline) → sprint dedicato S160+

---

## Target di fine S158

✅ PDF dossier > 200KB (dealer-grade) con tutte 6 immagini embedded e visibili
✅ Cross-brand test verde (BMW + Mercedes)
✅ Visual inspection Luke confermato
✅ Diagnosis + fix documentati
✅ Commit pushato
✅ S158 CHIUSO VERDE in HANDOFF + MEMORY

❌ NON in S158: outreach, Day 1, founder test, V4 messaggi, context budget gate

---

## Riferimenti

- File principale: `tools/scripts/pdf_generator_enterprise.py`
- Issue rilevato: S157 entry HANDOFF "PDF 5,296 bytes con 6 immagini ≥18KB"
- BACKLOG entry: "PDF dossier size 5KB sospetto (rilevato S157)"
- Pipeline E2E già verde: vedi MEMORY S157

---

## Resume path se compaction

Stato in TaskCreate da Phase 1. Se compaction:
1. Leggi questa entry + ultima MEMORY S158
2. Verifica diagnosis salvata `.planning/S158-PDF-DIAGNOSIS.md`
3. Riprendi da Phase 2 (fix) o Phase 3 (validation) in base a stato
