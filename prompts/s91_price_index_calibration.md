# S91 — Calibrazione Price Index + Day 3 TIER0 + Audit Visivo PDF

## Contesto

S90 ha reso il sistema hands-off con 4 cron job attivi sull'iMac.
MA il CoVe trova 0 opportunita' perche' il Market Price Index ha solo 2 chiavi e 1170 price points.
I listing vengono scrappati e salvati in DuckDB, ma nessuno passa il filtro di margine.

## Cosa funziona (NON toccare salvo bug)
```
4 cron attivi sull'iMac (pipeline, scraper, outreach, tunnel)
122 listing in DuckDB (50 DISCOVERED, 55 SCORED, 15 ENRICHED, 2 DOSSIER_READY)
Scraper E2E: AS24 DE/NL/AT + mobile.de → CoVe → DuckDB funzionante
Outreach scheduler: 3 TIER0 Day 3 at 30/03
```

## Priorita' S91

### 1. Calibrare Market Price Index (CRITICO)
Il price index ha solo 2 chiavi (BMW_X3, ???). Serve:
- Ingestire i 49+ listing BMW X3 freschi nel price index
- Aggiungere chiavi per GLC, Q5, Macan
- Verificare che `estimate.ref_price` sia realistico per il mercato EU
- Dopo la calibrazione, rieseguire il CoVe sui 50 DISCOVERED → generare opportunita'

Path: `src/cove/data/market_price_index.json`, `src/cove/market_price_index.py`

### 2. Day 3 Follow-up TIER0 (30/03 — OGGI)
- L'outreach scheduler dovrebbe mandare alert Telegram alle 9:00
- Preparare messaggi Day 3 per i 3 TIER0 con SECONDO veicolo + foto HD
- Verificare: WA daemon live? Sessione attiva? Messaggio Day 1 ricevuto?
- Sequenza Day 3: "Foto HD + secondo veicolo" personalizzato per archetipo

### 3. Audit visivo galleria PDF (IMPORTANTE)
- La galleria multi-pagina e' stata aggiunta ma MAI testata visivamente
- Generare un dossier con 8+ foto e verificare il rendering
- Controllare: griglia allineata? Foto tagliate? Watermark ARGOS presente?

### 4. Verificare risultati scrape GLC/Q5/Macan (CHECK)
- Lo scrape dei 3 modelli e' stato lanciato in background in S90
- Verificare quanti listing sono stati salvati
- Se 0: debug (stessa factory/dedup issue? portale diverso?)

### 5. Pipeline run LIVE sull'iMac (TEST)
- Dopo la calibrazione del price index, lanciare:
  `python3 src/cove/pipeline_orchestrator.py`
- Obiettivo: almeno 5 listing devono passare DISCOVERED → SCORED → ENRICHED
- Generare almeno 1 nuovo dossier DOSSIER_READY

## Test di successo S91
```
- Price index con 4+ chiavi e 5000+ price points
- Almeno 10 listing PROCEED dopo CoVe re-scoring
- Day 3 follow-up inviato ai 3 TIER0
- Galleria PDF verificata visivamente
- Pipeline orchestrator processa nuovi listing senza errori
```

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2 (deploy via SCP)
Cron: 4 job attivi (pipeline, scraper, outreach, tunnel)
DB DuckDB: src/cove/data/cove_tracker.duckdb (122 listing)
DB CRM: dealer_network.sqlite (3 TIER0 CONTACTED)
```
