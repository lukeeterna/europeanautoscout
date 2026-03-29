# S92 — Fix Plate Detection + Pipeline Autonoma + Day 3 TIER0

## Contesto

S91 ha portato il sistema a 8 DOSSIER_READY con sanitizer V8 (OpenCV+EasyOCR).
Il founder ha APPROVATO tutto TRANNE la copertura targhe che non e' precisa.
Il testo dealer (nomi, indirizzi) viene coperto bene da EasyOCR.
Le targhe EU vengono rilevate da OpenCV contour+HSV ma con falsi positivi/negativi.

## Cosa funziona (APPROVATO dal founder)
```
- EasyOCR text detection per nomi dealer → APPROVATO
- Blackout testo dealer → APPROVATO
- Banner bottom con ARGOS AUTOMOTIVE → APPROVATO
- PDF prezzi + grade badge → APPROVATO
- Price index 4 chiavi → FUNZIONANTE
- Pipeline 8 DOSSIER_READY → FUNZIONANTE
- 4 cron attivi iMac → FUNZIONANTE
- URL dedup (20→2-8 foto) → FUNZIONANTE
```

## Problema: Plate Detection non precisa

OpenCV contour+HSV rileva rettangoli bianchi ma:
- Falsi positivi: rileva parti bianche dell'auto come "targhe"
- Falsi negativi: non rileva targhe sporche/angolate/scure
- La barra ARGOS finisce in punti sbagliati

### Soluzioni da ricercare e implementare

1. **Plate detection con posizione attesa**: le targhe EU sono sempre nel bottom 30% dell'immagine + centro. Filtrare per posizione.

2. **YOLO pre-trained per EU plates**: esistono modelli YOLO pre-trainati per targhe EU scaricabili gratuitamente. Ultralytics YOLO con model hub.

3. **Haar cascade EU plates**: OpenCV Haar cascade specifico per targhe EU — meno preciso di YOLO ma piu' leggero.

4. **Approccio ibrido**: OpenCV HSV+contour filtrato per posizione (bottom 30%, center 80%) + conferma con aspect ratio EU (4.7:1).

5. **Fallback intelligente**: se nessuna targa trovata, mettere barra ARGOS nel bottom 8% centro (dove la targa e' quasi sempre).

### Vincolo
- La barra deve avere scritta "ARGOS" (mai barra nera vuota)
- Zero costi (no API cloud)
- Deve girare su iMac (Python 3.9, no GPU)

## Altre priorita' S92

### 2. Pipeline scoring autonomo (CRITICO)
Il pipeline_orchestrator non fa CoVe scoring — aspetta che qualcuno lo faccia manualmente.
Aggiungere: per ogni DISCOVERED con price>0, fare enrichment + CoVe scoring automatico.
Obiettivo: il cron ogni 4h deve processare tutto senza intervento.

### 3. Day 3 follow-up TIER0 (30/03)
- Messaggi pronti in `dossiers/messaggi_day3_pronti.md`
- Outreach scheduler installato — dovrebbe mandare alert Telegram alle 9:00
- Verificare invio + risposta dealer

### 4. Piu' foto per listing
- Molti listing hanno solo 2 foto uniche (AS24 salva 10 risoluzioni della stessa)
- L'enricher scarica gia' fino a 20 foto dalla detail page
- Verificare che il dedup URL non sia troppo aggressivo

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2 (deploy via SCP)
Cron: 4 job (pipeline, scraper, outreach, tunnel)
DB DuckDB: 311 listing (8 DOSSIER_READY)
DB CRM: 3 TIER0 CONTACTED
Deps iMac: easyocr, opencv-python, numpy<2, duckdb, reportlab, Pillow
```

## Test di successo S92
```
- Targhe coperte PRECISAMENTE con barra ARGOS su 90%+ delle foto frontali
- Pipeline cron processa DISCOVERED→DOSSIER_READY senza intervento
- Day 3 follow-up inviato ai 3 TIER0
- Almeno 1 risposta dealer
```
