# S111 — Image Sanitizer v3 Implementation + Soft Launch Resume

## Contesto

S110 ha completato la ricerca e validazione del sistema di sanitizzazione foto per i dossier dealer.
Lo stack e' stato testato su 10+ foto reali da 4 dealer diversi con risultati positivi.
Il soft launch (Fasi 0-4) e' stato bloccato dalla priorita' sanitizer.

## Prerequisiti

- iMac ONLINE, WA CONNECTED, PaddleOCR + LaMa installati
- PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`
- Leggere: `memory/MEMORY.md` sezione S110
- Foto test in: `/tmp/argos_paddle_results/` su MacBook, `/tmp/argos_paddle_lama_test/` su iMac
- PDF generator v2 gia' deployato su iMac

---

## FASE 1 — Implementare image_sanitizer_v3.py (PRIORITA' MASSIMA)

**Skill:** `/backend-architect`
**Agent:** `gsd-executor`

Riscrivere `src/cove/image_sanitizer.py` con la pipeline validata:

### Pipeline 5 stadi

```
Stage 0: Classificatore interno/esterno (DA COSTRUIRE — heuristic v1/v2 fallito)
Stage 1: Crop banner portale (altezza configurabile per portale)
Stage 2: PaddleOCR PP-OCRv4 text detection (~2.7s)
Stage 3: Inpainting — TELEA per aree piccole (<30K px²), LaMa crop per grandi
Stage 4: Post-processing OCR re-verification + alert TG se residui
```

### Classificatore interni — approccio consigliato

Le heuristic OpenCV (sky ratio, variance, etc.) sono FALLITE 0/10.
Approccio alternativo da provare:
- **Per indice foto**: portali EU ordinano tipicamente foto 0-3 = esterne, 4+ = miste
- **Per dimensione foreground rembg**: se rembg rimuove >70% = interno (gia' rembg installato)
- **MobileNetV3-Small** fine-tuned (2.5MB, ~50ms, BSD) — se le heuristic continuano a fallire

### Configurazione

```python
# Soglie testate e validate
PADDLE_DET_THRESH = 0.2
PADDLE_BOX_THRESH = 0.35
PADDLE_CONF_MIN = 0.25
PADDLE_TEXT_MIN_LEN = 2
DILATE_KERNEL = (11, 11)
DILATE_ITERATIONS = 3
TELEA_RADIUS = 12
LARGE_AREA_THRESHOLD = 30000  # px² — sopra usa LaMa crop
LAMA_CROP_PADDING = 50
LAMA_MAX_SIDE = 512
ALERT_CONFIDENCE_THRESHOLD = 0.70
```

### Init modelli (UNA VOLTA al boot)

```python
from paddleocr import PaddleOCR
from simple_lama_inpainting import SimpleLama

ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False,
                det_db_thresh=0.2, det_db_box_thresh=0.35)
lama = SimpleLama()
```

### Interfaccia da preservare

Il PDF generator chiama `sanitize_all_images(listing_id, db_path, output_dir)`.
Questa interfaccia DEVE restare identica. Solo il processing interno cambia.

---

## FASE 2 — Alert Telegram

**Skill:** `/backend-architect`

Quando il sanitizer non e' sicuro al 100%:
- Confidence < 70% → manda foto PRIMA + DOPO su Telegram
- Riflesso rilevato (zona cofano scura con alta varianza) → alert obbligatorio
- Post-OCR trova testo residuo → alert

Usare il bot TG gia' attivo (config in .env su iMac).

```python
# Endpoint: https://api.telegram.org/bot{TOKEN}/sendPhoto
# chat_id dal .env
```

---

## FASE 3 — Test E2E sanitizer + PDF

Dopo implementazione:
1. Generare PDF con listing `autoscout24_de_83adee60eed0` (KORDICK) + sanitizer v3
2. Generare PDF con listing `autoscout24_de_76ea612e8f49` (BMW PS) + sanitizer v3
3. Verificare: ZERO testo dealer nelle foto del PDF
4. Verificare: foto interni INALTERATE
5. Verificare: tempo totale dossier < 2 minuti

---

## FASE 4 — Soft Launch Resume (da S110)

Se sanitizer OK:

0. Test WA reale su TEST_FOUNDER (business hours 8-20)
1. Recovery Car Plus MANUALE da telefono
2. Import 13 dealer enriched nel DB
3. Soft launch 1 dealer: Stefano Auto FG
4. Outreach scaglionato 1/giorno

Dettagli in: `prompts/s110_soft_launch_outreach.md`

---

## Gap noti

- `tools/on_demand_runner.py` NON deployato su iMac — serve rsync
- Classificatore interni da costruire (heuristic fallito)
- Riflessi cofano: irrisolvibile automaticamente → alert TG

## File chiave

```
Sanitizer attuale:    src/cove/image_sanitizer.py (da riscrivere)
PDF generator:        tools/scripts/pdf_generator_enterprise.py (v2, deployato)
Test results:         /tmp/argos_paddle_results/ (MacBook)
                      /tmp/argos_paddle_lama_test/ (iMac)
Raw photos:           ~/Documents/app-antigravity-auto/dossiers/safe_images/raw/ (iMac)
Prompt soft launch:   prompts/s110_soft_launch_outreach.md
```

## Deps su iMac (gia' installate)

```
paddlepaddle 3.0.0
paddleocr 3.4.0
simple-lama-inpainting
craft-text-detector (MIT, backup se PaddleOCR fallisce)
rembg (MIT, per classificatore interni se serve)
```
