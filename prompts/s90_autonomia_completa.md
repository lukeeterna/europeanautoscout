# S90 — Autonomia Completa: Cron + Fresh Scrape + Galleria PDF

## Contesto

S89 ha reso la pipeline E2E funzionante. Il pipeline_orchestrator gira e produce dossier.
MA il founder ha detto: "il sistema deve girare DA SOLO".
Ora serve: cron automatico, fresh scrape periodico, fix qualita' foto, galleria PDF.

## Cosa funziona (NON toccare salvo bug)
```
src/cove/pipeline_orchestrator.py    ← E2E testato, 14 transizioni, 1 DOSSIER_READY
src/cove/detail_enricher_v2.py       ← Layer 4 foto, replace vecchie, fino a 20 foto
src/cove/image_sanitizer.py          ← crop top 18% + blur watermark
src/cove/dossier_standard.py         ← mandatory/important/optional checks
src/cove/seller_contact.py           ← email EU venditore, follow-up Day 3/7
tools/scripts/pdf_generator_enterprise.py ← 10 fix S89
wa-intelligence/wa-daemon.js         ← LIVE, DEKRA rimosso
src/cove/cove_engine_v4.py           ← NON MODIFICARE
```

## Priorita' S90 — rendere il sistema HANDS-OFF

### 1. Cron pipeline_orchestrator sull'iMac (CRITICO)
Il pipeline_orchestrator deve girare ogni 4 ore sull'iMac senza intervento.
```
# Setup cron:
ssh gianlucadistasi@192.168.1.2
crontab -e
0 */4 * * * cd ~/Documents/app-antigravity-auto && python3 src/cove/pipeline_orchestrator.py >> logs/pipeline.log 2>&1
```
- Verificare che i path siano corretti sull'iMac
- SCP dei file aggiornati prima del cron setup
- Alert Telegram se il run fallisce

### 2. Filtro thumbnail nel sanitizer (CRITICO)
Foto < 30 KB dopo download sono thumbnail inutili → scure/irriconoscibili nel PDF.
Fix: nel sanitizer, skip immagini < 30 KB dopo download. Nel PDF, mostrare solo foto > 30 KB.

### 3. Fresh scrape multi-modello (IMPORTANTE)
55/68 annunci nel DB sono scaduti (pagine 404). Serve:
- Scrape fresco di BMW X3, Mercedes GLC, Audi Q5, Porsche Macan
- Da AS24 DE/NL/BE/AT, mobile.de, AutoTrack NL
- Almeno 30 listing freschi PROCEED per alimentare la pipeline
- Lo scraper esiste gia' (`tools/scrapers/`) — lanciarlo

### 4. Galleria foto multi-pagina nel PDF (IMPORTANTE)
Il PDF mostra solo 3 foto in 1 riga. Per un dealer servono almeno 8-12.
Fix: aggiungere pagina(e) di galleria dopo la copertina:
- 2x3 griglia per pagina = 6 foto/pagina
- 2-3 pagine galleria = 12-18 foto
- Solo foto > 30 KB (HD)

### 5. Day 3 follow-up TIER0 (30/03 — DOMANI)
Lo scheduler automatico dovrebbe mandare i follow-up ai 3 TIER0.
- Verificare che funzioni
- Se non funziona: debug
- Se funziona: procedere con TIER1

### 6. Seller email discovery + contatto automatico (DOPO)
`seller_email_discovery.py` esiste ma non e' collegato.
Quando un veicolo arriva a ENRICHED con < 8 foto:
- Scoprire email venditore (Impressum, Google)
- Mandare email automatica richiedendo foto HD
- Questo e' gia' nel pipeline_orchestrator (process_enriched) ma mai testato

## Test di successo S90
```
Il founder NON tocca nulla per 7 giorni.
La pipeline:
1. Scrappa nuovi annunci ogni giorno
2. Li processa automaticamente (CoVe → enrich → grade → PDF)
3. Manda i dossier al daemon WA che li consegna ai dealer
4. Alert Telegram per ogni DOSSIER_READY
5. Il founder vede solo i risultati finali
```

## Infra
```
iMac: ssh gianlucadistasi@192.168.1.2 (deploy via SCP)
PM2: wa-daemon (:9191), dashboard (:8080)
DB DuckDB: src/cove/data/cove_tracker.duckdb
DB daemon: /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite
Pipeline log: logs/pipeline.log
Cron: da installare
```

## Regole
- Il sistema deve girare DA SOLO — MAI fare a mano quello che il codice deve fare
- Ogni fix va nel codice, non nella sessione
- cove_engine_v4.py NON MODIFICARE
- ZERO SOURCE nelle foto/PDF
- Audit visivo PDF obbligatorio dopo ogni modifica al generatore
