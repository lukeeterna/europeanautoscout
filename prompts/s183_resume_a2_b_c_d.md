# S183 RESUME — A2 zones.json + A5 baseline + B patch + C UAT + D commit

> Sessione precedente (2026-05-20): GATE A1 + A3 + A4 chiusi VERDE.
> Closure prematura su gate context budget vincolo #7 (50%).
> NON ripartire da zero — leggi stato verified PRIMA.

## Stato verified (input prossima sessione)

### File pronti
- `assets/argos_logo.png` 200x80 RGBA transparent (Helvetica 42pt "ARGOS™" + shadow)
- `tests/uat_golden/g01..g10` 10 sample (5 Isernhagen + 5 mixed seller diff)
- `tests/uat_golden/uat_criteria.md` 5 criteri binari C1-C5 + 5/5 NO=PASS rule
- `tests/test_sanitizer_golden.py` pytest con PII hash diff + auto-features tolerance 2%
- Commit pending: NESSUNO (working tree dirty pre-esistente fuori scope S183)

### Sample mapping (sample_index → file)
| idx | file | seller atteso | image_index per sanitize_image |
|-----|------|---------------|--------------------------------|
| 1 | g01_isernhagen_smoke_00.jpg | Autohaus Isernhagen | 0 |
| 2 | g02_isernhagen_smoke_01.jpg | Autohaus Isernhagen | 1 |
| 3 | g03_isernhagen_smoke_02.jpg | Autohaus Isernhagen | 2 |
| 4 | g04_isernhagen_raw_00.jpg | Autohaus Isernhagen | 0 |
| 5 | g05_isernhagen_raw_01.jpg | Autohaus Isernhagen | 1 |
| 6 | g06_mixed_030c.jpg | <unknown, Luke compila A2> | 0 |
| 7 | g07_mixed_39d6.jpg | <unknown, Luke compila A2> | 0 |
| 8 | g08_mixed_4289.jpg | <unknown, Luke compila A2> | 0 |
| 9 | g09_mixed_76ea.jpg | <unknown, Luke compila A2> | 0 |
| 10 | g10_mixed_7baf.jpg | <unknown, Luke compila A2> | 0 |

### Gate A1+A3+A4 commit candidate (DA NON COMMITTARE prima di A5 baseline VERDE)
```
git add assets/argos_logo.png tests/uat_golden/ tests/test_sanitizer_golden.py
```
Differito: commit unico finale GATE D, post A5+B+C tutti VERDE.

## GATE A2 — Luke MANUAL zones.json compilation (~30 min)

Per ognuno dei 10 file `g01..g10`, crea `tests/uat_golden/<file>.zones.json`:

```json
{
  "image": "g01_isernhagen_smoke_00.jpg",
  "seller_name": "Autohaus Isernhagen",
  "image_index": 0,
  "pii_zones": [
    {"x1": 580, "y1": 695, "x2": 860, "y2": 740, "type": "watermark_plate"},
    {"x1": 0, "y1": 950, "x2": "W", "y2": "H", "type": "footer_brand_row"},
    {"x1": 600, "y1": 745, "x2": 830, "y2": 770, "type": "tagline"}
  ],
  "auto_features_zone": {"x1": 0.30, "y1": 0.20, "x2": 0.70, "y2": 0.78}
}
```

**Regole zones.json**:
- `pii_zones`: bbox pixel assoluti (int) o "W"/"H" per estensione massima
- `auto_features_zone`: bbox relative 0.0-1.0 (frazione w/h) — standard pattern listing dealer
- `type` libero: `watermark_plate` / `footer_brand_row` / `tagline` / `dealer_signage` / etc.
- Coordinate manuali Preview.app: cmd+L su Preview mostra coords cursore

**Tool aiuto Luke**:
```bash
~/.argos-sanitizer-venv/bin/python -c "
from PIL import Image
for i in range(1, 11):
    files = sorted(__import__('glob').glob(f'tests/uat_golden/g{i:02d}_*.jpg'))
    if files:
        img = Image.open(files[0])
        print(f'g{i:02d}: {files[0].split(\"/\")[-1]} size={img.size}')
"
```

**Time-box A2: 30 min**. Se >45 min → semplifica: solo `pii_zones` su 5 sample Isernhagen (g01-g05), skip mixed g06-g10 → ridotto sample set ma sblocca pipeline.

## GATE A5 — Baseline pytest run (~5 min)

```bash
~/.argos-sanitizer-venv/bin/python -m pytest tests/test_sanitizer_golden.py -v 2>&1 | tee tests/uat_golden/baseline_s179b.log
```

**Expected**: 10/10 FAIL (o 5/5 se solo Isernhagen) → conferma sanitizer S179b corrente NON copre PII zones. Baseline catturato.

Se inaspettato 1+ PASS → diagnosi: zone.json bbox sbagliato o PASS reale parziale. Verifica visualmente prima di GATE B.

## GATE B — Patch chirurgico image_sanitizer.py (~90 min)

3 funzioni additive (NO refactor 929 LOC base):

### B1 `_apply_whitelist_masks(cv_img, image_index)`

Inserisci PRIMA di `_apply_solid_fills` chiamata in `sanitize_image`:
- Top 8%: mask deterministic sempre
- Bottom 12%: mask deterministic sempre
- Sides 5% L+R: SOLO se `image_index < 4` (exterior)
- SKIP se `_is_interior_photo(image_index)` — interior preserva edge feature
- Color fill via `_sample_border_color` esistente

```python
def _apply_whitelist_masks(cv_img, image_index):
    if _is_interior_photo(image_index=image_index):
        return cv_img
    h, w = cv_img.shape[:2]
    pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    masks = [
        (0, 0, w, int(h * 0.08)),
        (0, int(h * 0.88), w, h),
    ]
    if image_index < 4:
        masks += [
            (0, 0, int(w * 0.05), h),
            (int(w * 0.95), 0, w, h),
        ]
    for x1, y1, x2, y2 in masks:
        fill_color = _sample_border_color(pil_img, (x1, y1, x2, y2), sample_px=3)
        cv2.rectangle(cv_img, (x1, y1), (x2, y2), fill_color, -1)
    return cv_img
```

**Caveat _is_interior_photo**: verifica se esiste in sanitizer corrente. Se no, definisci come `def _is_interior_photo(image_index): return image_index >= 6` (heuristic: foto 0-5 esterne, 6+ interne).

### B2 `_get_plate_zone(cv_img, vision_plate_result)`

Aggiunto in `_apply_solid_fills`. Estende bbox plate UPWARD 1.5×h per coprire watermark sovra-imposto. Fallback deterministico se conf <0.5.

```python
def _get_plate_zone(cv_img, vision_plate_result=None):
    h, w = cv_img.shape[:2]
    if vision_plate_result and vision_plate_result.get('confidence', 0) >= 0.5:
        bbox = vision_plate_result['box']
        plate_h = bbox[3] - bbox[1]
        return {
            'x1': bbox[0], 'y1': max(0, bbox[1] - int(plate_h * 1.5)),
            'x2': bbox[2], 'y2': bbox[3]
        }
    # Fallback: posizione plate frontale tipica 3/4 shot EU
    return {
        'x1': int(w * 0.35), 'y1': int(h * 0.62),
        'x2': int(w * 0.65), 'y2': int(h * 0.90)
    }
```

Integra in `_apply_solid_fills` aggiungendo fill rectangle su `plate_zone` con border color.

### B3 `_embed_argos_branding(pil_img, listing_id, vin, image_index)`

Asset path: `assets/argos_logo.png` (creato A1). Visible logo 8% width, opacity 0.70, bottom-right padding 2%. EXIF tracking SHA256 16-char + Copyright + ImageDescription.

```python
def _embed_argos_branding(pil_img, listing_id, vin, image_index):
    logo = Image.open("assets/argos_logo.png").convert("RGBA")
    target_w = int(pil_img.width * 0.08)
    ratio = target_w / logo.width
    logo = logo.resize((target_w, int(logo.height * ratio)), Image.LANCZOS)
    alpha = logo.split()[3]
    alpha = alpha.point(lambda p: int(p * 0.70))
    logo.putalpha(alpha)
    pad_x = int(pil_img.width * 0.02)
    pad_y = int(pil_img.height * 0.02)
    pos = (pil_img.width - logo.width - pad_x,
           pil_img.height - logo.height - pad_y)
    if pil_img.mode != 'RGBA':
        pil_img = pil_img.convert('RGBA')
    pil_img.paste(logo, pos, logo)
    pil_img = pil_img.convert('RGB')

    import hashlib, time
    payload = f"{listing_id}|{vin or 'NA'}|{image_index}|{int(time.time())}"
    argos_id = hashlib.sha256(payload.encode()).hexdigest()[:16]
    exif = pil_img.getexif()
    user_comment = b"ASCII\x00\x00\x00" + f"ARGOS-ID:{argos_id}".encode('ascii')
    exif[0x9286] = user_comment
    exif[0x010E] = f"ARGOS Dossier {listing_id}"
    exif[0x8298] = f"(c) {time.strftime('%Y')} ARGOS"
    return pil_img, exif, argos_id
```

**Caveat noto**: EXIF stripped da screenshot, preserved da file forward. Documentare in commit message.

**Signature `sanitize_image`**: aggiungi `vin: str = None` parametro keyword. Backward compat via default None.

### B4 `_edge_density_check(pil_img_orig, pil_img_sanitized)` — log WARN only, NO blocca

```python
def _edge_density_check(pil_img_orig, pil_img_sanitized):
    from PIL import ImageFilter
    edges_o = pil_img_orig.filter(ImageFilter.FIND_EDGES).convert('L')
    edges_s = pil_img_sanitized.filter(ImageFilter.FIND_EDGES).convert('L')
    THRESH = 50
    count_o = sum(1 for p in edges_o.getdata() if p > THRESH)
    count_s = sum(1 for p in edges_s.getdata() if p > THRESH)
    if count_o > 0:
        ratio = count_s / count_o
        if ratio < 0.40:
            log.warning(f"edge_density anomaly: sanitized/original = {ratio:.2%} — possible over-mask")
```

### B5 Run golden test post-patch

```bash
~/.argos-sanitizer-venv/bin/python -m pytest tests/test_sanitizer_golden.py -v
```

**Expected**: 10/10 PASS (o 5/5 se Luke ha solo fatto Isernhagen A2).

Se < 100% PASS → diagnosi quale patch B1/B2/B3 ha gap. Iterare patch SINGOLA modifica + ri-run pytest. NO multiple changes simultanee.

## GATE C — UAT visual Luke 5/5 (~30 min MANUAL)

```bash
mkdir -p /tmp/s183_uat
~/.argos-sanitizer-venv/bin/python -c "
from src.cove.image_sanitizer import sanitize_image
import glob
for i, p in enumerate(sorted(glob.glob('tests/uat_golden/g01_*.jpg tests/uat_golden/g02_*.jpg tests/uat_golden/g03_*.jpg tests/uat_golden/g04_*.jpg tests/uat_golden/g05_*.jpg'.split()))):
    sanitize_image(p, '/tmp/s183_uat/', listing_id='s183_uat', image_index=i, seller_name='Autohaus Isernhagen', vin='TEST')
"
open /tmp/s183_uat/
```

Luke valuta contro `tests/uat_golden/uat_criteria.md` C1-C5 binari:
- 5 NO consecutivi su tutti 5 sample → PASS → GATE D
- 1+ YES su 1+ sample → FAIL → diagnosi gate B → HANDOFF S183-bis

Verifica EXIF:
```bash
exiftool /tmp/s183_uat/*.jpg | grep -E "User Comment|Copyright|Image Description"
```

## GATE D — Commit + Day 1 unblock (~15 min)

Se B5 (10/10 pytest PASS) + C (5/5 UAT PASS):

```bash
git add assets/argos_logo.png tests/uat_golden/ tests/test_sanitizer_golden.py src/cove/image_sanitizer.py
git commit -m "$(cat <<'EOF'
feat(S183): whitelist sanitizer + golden test + ARGOS branding (Day 1 unblock)

- _apply_whitelist_masks: top 8% + bottom 12% + sides 5% deterministic
- _get_plate_zone: bbox upward extension 1.5x + fallback (w*0.35-0.65, h*0.62-0.90)
- _embed_argos_branding: 8% width logo opacity 0.70 bottom-right + EXIF SHA256 tracking
- _edge_density_check: log WARN se ratio sanitized/original < 0.40
- tests/uat_golden/ 10 sample + zones.json + uat_criteria.md
- tests/test_sanitizer_golden.py PII hash diff + auto-features 2% tolerance

Fixes S179b UAT NO-GO 3/3 (watermark plate area + footer brand row).
Baseline S179b 10/10 FAIL → post-patch 10/10 PASS.
EXIF caveat: stripped da screenshot, preserved da file forward.

Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>
EOF
)"
git push origin master
ssh imac "cd ~/Documents/app-antigravity-auto && git pull origin master"
```

Rigenera dossier Stile Car:
```bash
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"
```

UAT visual PDF finale + signal Luke Day 1 unblock.

## Out-of-scope DEFERRED (vincolo #6 closure pulita)

- Email seller raw photos → S184+
- Ricontatto 4 dealer burned → marketing sessione post Day 1
- Multi-seller whitelist tuning → S184+
- Edge density flag → review manual queue → S184+

## Vincoli HARD S183 resume

- Big Sur AVX1: SEMPRE `~/.argos-sanitizer-venv/bin/python`, MAI `python3` di sistema
- NO commit prima di B5 10/10 + C 5/5 PASS entrambi
- NO scope creep oltre A2+A5+B+C+D
- Gate context budget #7 al 50% → handoff S183-ter
- Pre-action check D-32 reference su ogni modifica codice
- Smoke ≠ UAT gate (vincolo memory `feedback_smoke_test_not_uat_gate.md`)

## Context budget atteso S183 resume

- A2 (Luke manual): 0% AI (offline)
- A5 baseline pytest: +3%
- B patch + ri-run: +20-25%
- C UAT visual + EXIF: +5%
- D commit + push + dossier rigenera: +10%
- **Target close**: ≤45% AI context
