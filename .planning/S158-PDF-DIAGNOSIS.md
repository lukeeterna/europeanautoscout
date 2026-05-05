# S158 — PDF Dossier 5KB Diagnosis + Fix

**Data**: 2026-05-05
**Engine PDF**: ReportLab (`reportlab.platypus.SimpleDocTemplate` + `Image`)
**Sintomo**: PDF generato 5,289 bytes con 6 immagini scaricate OK (~10-22KB cad)

## Root cause (confermato)

Due bug compounded nel path `on_demand_runner` → `pdf_generator_enterprise.generate_dossier_from_data`:

### Bug A — URL non upgradato a full-res
**File**: `tools/scripts/pdf_generator_enterprise.py:1457` (`_download_image_to_temp`)
**Problema**: scarica l'URL così com'è. Il scraper AutoScout24 produce `image_urls` con suffix `/250x188.webp` (thumbnail). Risultato: download di thumbnail 9-22KB invece di full-res 100-300KB.

Esiste già `tools/scrapers/image_downloader._upgrade_url()` con regola `(r"/\d+x\d+\.webp", "/2560x1920.webp")` per AutoScout24 — MA viene usato SOLO da `generate_dealer_pdfs` (path alternativo non chiamato da on_demand_runner). Il path `generate_dossier_from_data` bypassa interamente `ImageDownloader`.

**Verifica empirica**:
```
curl https://prod.pictures.autoscout24.net/.../250x188.webp  → 22 KB
curl https://prod.pictures.autoscout24.net/.../2560x1920.webp → 140 KB ✅
```

### Bug B — Filtro hard-coded `> 30000` byte rifiuta tutto
**File**: `tools/scripts/pdf_generator_enterprise.py:236, 275, 301`
**Problema**: tre punti filtrano `[p for p in vehicle.local_image_paths if os.path.exists(p) and os.path.getsize(p) > 30000]`. Poiché Bug A produce file 9-22KB, **nessuna immagine** supera 30KB → `valid_imgs = []` → `_create_image_row` ritorna `None` → PDF senza immagini → 5KB.

## Reproduction step-by-step

```bash
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" \
    --budget 35000 --dealer "S158_BASELINE"
```

Log evidenzia il bug:
```
PDF> Image OK: 22141 bytes — -4e74-943d-838c5900a41d.jpg/250x188.webp
PDF> Downloaded 6 valid images from 10 unique URLs
PDF> Done. PDF at: ... (5,289 bytes)   ← NESSUNA IMG EMBEDDED
```

## Fix applicato (S158)

**Strategia**: apply URL upgrade in `_download_image_to_temp` — riusa logica già presente in `image_downloader.PORTAL_IMAGE_UPGRADES`. In questo modo:
- Immagini scaricate ~100-300KB (full-res)
- Passano naturalmente il filtro `> 30000`
- Filtro 30KB resta come safety contro thumbnail residuali / placeholder

Diff principale:
1. `_download_image_to_temp(url)`: prova prima URL upgradato (`_upgrade_url` per autoscout24/olx/finn/marktplaats/willhaben), fallback all'originale se 404/empty.
2. Filtro 30000 invariato (è una safety net corretta).

## Out of scope S158
- Image_url single fallback path (presente ma non triggerato in baseline)
- `generate_dealer_pdfs` path alternativo (già usa ImageDownloader correttamente)

## ⚠️ Issue collaterale RILEVATO durante S158 (defer)
**Image Sanitizer PaddleOCR NON operativo** — pre-existing bug ora esposto.

`_find_sanitizer_python()` non trova PaddleOCR su MacBook (`/usr/local/bin/python3.12`, `/usr/bin/python3`, `/usr/local/bin/python3.11` testati) → `_sanitize_photo()` ritorna `image_path` RAW passthrough. Log `[SANITIZER] 6/6 photos sanitized` è messaggio FUORVIANTE: il count include immagini RAW.

**Implicazione**: PDF S158 contengono foto full-res direttamente dal CDN AutoScout24 con watermark/branding dealer tedesco originario, targhe, numeri telefono visibili. **Violazione zero-source policy ARGOS**: un dealer Sud Italia capisce immediatamente da quale portale arriva l'opportunità.

**NOT FIXED in S158** (scope separato, decisione Context Budget Gate). Documentato BACKLOG.md. Da risolvere PRIMA di Day 1 reale dealer.

**Cosa fare (S158-bis o sprint dedicato)**:
1. Setup PaddleOCR su Python 3.12 (system) o venv `~/.argos-sanitizer-venv/`
2. Aggiungere venv path a `_SANITIZER_PYTHON` candidates
3. Bonus: fix messaggio log `[SANITIZER]` per riportare numeri reali (RAW vs sanitized)
4. Smoke + visual inspection PDF post-fix
