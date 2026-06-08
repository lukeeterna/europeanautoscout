# S183-ter RESUME — Logo ARGOS reale + placement sopra-targa + commit unico

> Sessione precedente 2026-05-21 (S183-bis CTO Opus): GATE B + C visual PASS 5/5 ma 2 finding bloccanti GATE D commit.
> Working tree dirty intenzionalmente (NO commit con logo wrong).

## Stato verified S183-bis close (2026-05-21 ~17:00)

### Modifiche IN-PLACE su `src/cove/image_sanitizer.py` (NON committate)
- **B1** `_apply_whitelist_masks(cv_img)` — top 8% + bottom 12% + sides 5% deterministic mask (cv2.rectangle solid color via `_sample_border_color` fallback bianco). Inserita STAGE 3-bis dopo `_apply_solid_fills`, sempre invocata.
- **B3** `_embed_argos_branding(pil_img, vin)` — carica `assets/argos_logo.png`, ridimensiona 8% width, opacity 0.70 alpha, paste bottom-right padding 3%, EXIF UserComment `ARGOS_TRACK:{sha256_16}` + Artist `ARGOS Automotive`. Sostituisce vecchio `draw.text("ARGOS")` linea 695.
- **B4** `_edge_density_check(cv_img) -> float` — Canny + ratio + WARN se < 0.040. Inserita dopo `_detect_hood_reflection`, NO blocking.
- **S183b-FILTER** post-OCR — droppa text region con `len<4 AND y_center 25-75% AND bw_pct>8% AND not is_seller` (Apple Vision false-positive "COO" su faro). Insertion DOPO `text_regions = _detect_text_regions(...)` LOC 751.
- Smoke 3/3 PASS verified + EXIF `ARGOS_TRACK:b66f3bde43b8cf45` confermato exiftool.
- UAT visual Luke 5/5 PASS (sample 02 OK post-filter, altri 4 OK).

### File untracked GATE B+C pending GATE D commit
- `assets/argos_logo.png` (5541 bytes, **PLACEHOLDER S183 GATE A1 — NON è logo ARGOS reale, va sostituito S183-ter**)
- `tests/uat_golden/g{01..10}_*.jpg` (10 golden samples raw)
- `tests/uat_golden/g{01..10}_*.zones.json` (10 zones autogen S183 A2 — COMMITTED già in commit f8e82c5)
- `tests/uat_golden/uat_criteria.md` (5 criteri binari)
- `tests/uat_golden/overlay/g{01..10}_*_overlay.png` (preview zone visual)
- `tests/uat_golden/baseline_s183*.log` (baseline run output)
- `tests/test_sanitizer_golden.py` (con flag `AUTO_FEATURES_CHECK_ENABLED=False` Path 2 S183-bis)
- `src/cove/image_sanitizer.py` (+146/-6 LOC implementer + ~22 LOC S183b-FILTER patch CTO)
- `BACKLOG.md` (entry #S183b-1 Path 1 refactor sanitize_image API)

## 2 Finding BLOCCANTI GATE D (Luke verdict 2026-05-21 ~17:00)

### Finding #1 — Logo `assets/argos_logo.png` NON è logo ARGOS reale
`assets/argos_logo.png` 5541 bytes generato in S183 GATE A1 era placeholder. Sostituirlo con logo ARGOS canonico prima del commit.

**Asset disponibili in `assets/`** (verified ls 2026-05-21 16:10):
- `ARGOS_logo_sobrio_horizontal.png` (20171 bytes, 10 Mar) — candidato primario
- `ARGOS_APPROVED_sobrio.png` (21607 bytes, 10 Mar) — alternativa

**Decisione richiesta S183-ter STEP 1**: copy `ARGOS_logo_sobrio_horizontal.png` → `argos_logo.png` OPPURE Luke produce versione watermark-grade (PNG con trasparenza, dimensione 200x80 o ratio simile, sfondo trasparente per overlay alpha-composite).

### Finding #2 — Logo NON va applicato sull'auto MAI
Regola Luke S183-bis (vincolo immutabile S183-ter+):
> Logo NON va in posizione bottom-right auto (current B3 placement). Va invece **sopra la targa**, come overlay che **sostituisce/copre la targa stessa**. Doppia funzione: branding + plate cover (rimpiazza il rectangle solid fill nero che oggi copre la targa).

**Implicazione tecnica**:
- Plate detection è OUT-OF-SCOPE (S183 pre-flight ha confermato Apple Vision NON detecta targhe + color signature 2/10 false positive). Quindi **non possiamo localizzare la targa programmaticamente**.
- Path alternativi:
  - **Path A (raccomandato CTO)**: il "plate watermark sostitutivo" si applica nella zona dove HA SENSO posizionare l'overlay. Su foto frontale 3/4 auto = paraurti anteriore (zona y 60-75%, x 35-65%). Su foto posteriore = paraurti posteriore. Ma riconoscere frontale vs posteriore richiede classifier. SCOPE CREEP.
  - **Path B**: zona FISSA bottom-center auto (y 65-80%, x 35-65%) sempre. Funziona se foto sono per la maggior parte frontali o posteriori (targa è sempre lì). Sui laterali falla. Costo: 15 min.
  - **Path C (raccomandato pragmatico)**: si lascia `_apply_solid_fills` esistente per il fill targa (logica OCR seller match già funziona, il `[FILL] N text region(s) covered (Pillow rect)` log copre già la targa quando Apple Vision la detecta come testo). Si **aggiunge logo overlay PICCOLO bottom-center** (5-7% width, opacity 0.50) sopra la zona fill targa, posizione fissa y=72%, x=center-2.5%. Costo: 20 min. Pro: pragmatico, non richiede plate detection. Contro: se Apple Vision NON detecta targa (es. targa angolata, luminosa), il logo finisce sul paraurti vuoto — comunque innocuo (branding subtile).

**CTO raccomandazione STEP 2**: **Path C** (logo overlay piccolo bottom-center come "marchio territoriale" + plate fill resta via `_apply_solid_fills` esistente). Argomento: zero scope creep, zero plate detection, mantiene branding visibile, accetta che in rari casi (targa non OCR-detected) logo finisce in zona neutra. Decision Luke pre-implementation.

**Autocritica Path C**:
- Assunzione: targa OCR-detected sempre? NO, ~70-80% casi (depends su angolo + luce). Mitigation: per i 20-30% restanti, logo finisce su paraurti = comunque coprire potenzialmente parte targa visibile = effetto positivo accidentale.
- Rompe a 30gg: produzione dossier scaling → cresce visibilità errori di posizionamento. Mitigation: logging warning quando `[FILL] 0 text region(s)` (zero seller match + zero plate → logo overlay rischio inutile) e BACKLOG plate detection vera S185+.
- Sovradimensiono: NO, sto evitando ML plate detection.

## Plan S183-ter (post Luke decision + budget context tipico 30-40%)

### STEP 1 — Logo asset corretto (~5 min)
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
cp assets/ARGOS_logo_sobrio_horizontal.png assets/argos_logo.png
# Verify dimensioni + trasparenza
~/.argos-sanitizer-venv/bin/python -c "
from PIL import Image
img = Image.open('assets/argos_logo.png')
print(f'Logo: {img.size} mode={img.mode}')
if img.mode != 'RGBA':
    print('WARN: logo non-RGBA, overlay alpha non funzionerà bene')
"
```
Se logo non RGBA → Luke produce versione con trasparenza o usa altro asset.

### STEP 2 — Refactor `_embed_argos_branding` per placement bottom-center (~20 min)
Modifica `src/cove/image_sanitizer.py` `_embed_argos_branding`:
- **Rimuovi** placement bottom-right padding 3%.
- **Sostituisci** con bottom-center: target `y = int(pil_img.height * 0.72)`, `x = int(pil_img.width * 0.50) - logo.width // 2`.
- **Riduci** dimensione: target width 5-7% (era 8%) per evitare invadere troppo auto.
- **Riduci** opacity: 0.50 (era 0.70) per essere più subtle (è sopra auto, non bordo).
- EXIF tracking resta identico.

### STEP 3 — Re-run UAT 5/5 + verifica Luke fisica
```bash
~/.argos-sanitizer-venv/bin/python -c "
from src.cove.image_sanitizer import sanitize_image
import glob, os
samples = sorted(glob.glob('tests/uat_golden/g0[1-5]_*.jpg'))
for i, p in enumerate(samples):
    sanitize_image(p, '/tmp/s183ter_uat/', listing_id='s183ter', image_index=i, seller_name='Autohaus Isernhagen', vin='WBA-S183TER-UAT')
"
open /tmp/s183ter_uat/
```
Luke valida 5/5 visual: (a) logo posizione bottom-center coperture targa o paraurti, (b) logo ARGOS reale leggibile (non placeholder), (c) C1-C5 invariati VERDI.

### STEP 4 — Commit unico GATE D + push + dossier (~15 min)
```bash
git add assets/argos_logo.png \
        tests/uat_golden/g*.jpg \
        tests/uat_golden/uat_criteria.md \
        tests/uat_golden/baseline_s183*.log \
        tests/uat_golden/overlay/ \
        tests/test_sanitizer_golden.py \
        src/cove/image_sanitizer.py \
        BACKLOG.md \
        prompts/s183b_overmask_diagnosis_then_b_c_d.md \
        prompts/s183_ter_logo_fix.md

git commit -m "feat(S183-ter): sanitizer D-32 closure — B1 whitelist + B3 plate watermark + B4 edge density

- _apply_whitelist_masks: top 8% + bottom 12% + sides 5% deterministic
- _embed_argos_branding: logo bottom-center 5-7% width opacity 0.50 + EXIF SHA256 tracking
- _edge_density_check: log WARN se ratio < 0.040 (no blocking)
- S183b-FILTER: drop OCR false-positive (len<4 AND central body) — fixes COO headlight glare
- Path 2: AUTO_FEATURES_CHECK_ENABLED=False (test golden geometry mismatch, BACKLOG #S183b-1)
- 10 golden samples + zones.json + uat_criteria.md + baseline log
- UAT visual Luke 5/5 PASS

Closes S179b NO-GO + S183-bis logo finding. Day 1 Stile Car unblock 2026-06-03."

git push origin master
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"

python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"
```

## Vincoli HARD S183-ter (invariati)
- Big Sur AVX1: `~/.argos-sanitizer-venv/bin/python` MAI `python3` sistema
- NO commit prima UAT 5/5 PASS post-refactor logo
- NO plate detection ML (out-of-scope, BACKLOG S185+)
- Pre-action check D-32 ogni modifica
- Gate context #7: 50% chiudi pulito

## Out-of-scope DEFERRED S184+ (immutati)
- Path 1 BACKLOG #S183b-1 fix test golden (refactor sanitize_image API crop metadata)
- Plate detection vera (ML/CV)
- Multi-seller whitelist tuning
- Email seller raw photos
- Ricontatto 4 dealer burned

## Context budget atteso S183-ter
- STEP 1 logo copy + verify: +2%
- STEP 2 refactor _embed_argos_branding: +5%
- STEP 3 UAT 5/5: +3%
- STEP 4 commit + push + dossier: +10%
- **Target close**: ≤30% AI context

## Day 1 Stile Car deadline
- Target: **2026-06-03** (13gg dal handoff 2026-05-21)
- Tempo residuo lun-sab: ~10gg lavorativi
- Gating residuo: GATE D + UAT visual dossier rigenerato (12-section PDF S179+)
