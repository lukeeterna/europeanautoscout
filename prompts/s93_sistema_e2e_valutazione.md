# S93 — Valutazione Sistema E2E + Email Foto HD + Comunicazione Dealer

## Contesto

S92 ha portato il sanitizer a V15 (YOLO + LaMa + verify). La pipeline auto-score funziona.
ZERO risposte dai 3 dealer TIER0 contattati il 27/03.
Il founder vuole: valutare il sistema completo, poi concentrarsi sulla comunicazione.

## Cosa funziona (deployato su iMac)
```
- Sanitizer V15: YOLO plate detection + LaMa inpainting + OCR verify
- Pipeline auto-score: DISCOVERED → enrich → CoVe → SCORED/REJECTED
- 4 cron attivi (pipeline, scraper, outreach, tunnel)
- LaMa model scaricato su iMac (196MB)
- yolov5 installato su iMac
```

## Priorita' S93

### 1. Generare 10 PDF dossier completi (CRITICO)
- Selezionare 10 listing diversi (mix BMW X3, GLC, Q5, Macan)
- Far girare la pipeline completa: scrape → CoVe → enrich → sanitize → PDF
- Per ogni PDF valutare:
  - Qualita' foto sanitizzate (testo dealer rimosso? targa coperta? artefatti?)
  - Completezza dati (prezzo, km, anno, VIN, fuel, transmission)
  - CoVe score e grade
  - Margine stimato
  - Presentazione complessiva (layout, leggibilita')
- Documentare i risultati in una tabella
- Identificare i problemi sistematici (non i singoli casi)

### 2. Email automatica richiesta foto HD
- Implementare invio email da ferretti.argosautomotive@gmail.com
- Trigger: listing ENRICHED con < 6 foto o foto bassa risoluzione
- Template email: professionale, in tedesco/inglese, chiede foto HD + VIN
- Integra nel pipeline_orchestrator come step tra ENRICHED e DATA_COMPLETE

### 3. Comunicazione dealer (STRATEGICO)
- Day 3 per TIER0 (doveva partire 30/03) — verificare outreach_scheduler
- Analizzare: perche' zero risposte? Messaggio sbagliato? Timing? Target?
- Preparare messaggi Day 7 (FOMO lieve o uscita dignitosa)
- Valutare se contattare TIER1 in parallelo

### 4. Problemi noti (bassa priorita')
- MobileDeScraper non funziona
- Mercedes GLC slug (AS24 sub-models)
- Procar-type reflections (limite fisico LaMa)

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2 (deploy via SCP)
Cron: 4 job (pipeline, scraper, outreach, tunnel)
DB DuckDB: src/cove/data/cove_tracker.duckdb
DB CRM: dealer_network.sqlite
Deps iMac: easyocr, opencv-python, numpy<2, duckdb, reportlab, Pillow, yolov5, LaMa (torch.jit)
Email: ferretti.argosautomotive@gmail.com (da configurare per invio automatico)
```

## Test di successo S93
```
- 10 PDF dossier generati e valutati con rating 1-5
- Media qualita' >= 3.5/5
- Email foto HD funzionante e integrata nel pipeline
- Day 3/7 messaggi inviati ai TIER0
- Almeno 1 risposta dealer (anche negativa)
- Decisione: TIER1 outreach SI/NO
```
