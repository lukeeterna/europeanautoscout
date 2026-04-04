# ARGOS — Regole CoVe 2026

## Terminologia IMMUTABILE
- `recommendation` (MAI `verdict`)
- `analyzed_at` (MAI `created_at`)
- `confidence` 0.0-1.0
- DEALER_PREMIUM_THRESHOLD=0.75 | VIN_CHECK_THRESHOLD=0.60 | DAILY_LIMIT=30
- `cove_engine_v4.py` → NON MODIFICARE — solo leggere e invocare
- MAI: CoVe/RAG/Claude/Anthropic/embedding nei messaggi dealer

## Catena di valore
```
Scraper (28 portali) → CoVe Engine (scoring + fraud) → Opportunity Selection → Dealer Dossier
```
Se il lavoro non migliora questa catena E2E, stai facendo la cosa sbagliata.

## Regole dati e scraping
- MAI "CarFax EU" → "DAT Fahrzeughistorie / TUV report"
- MAI margine senza IVA → specificare sempre inclusa/esclusa
- MAI Handlergarantie → solo garanzia costruttore UE
- MAI DEKRA/DAT nei messaggi finche' non operativi
- Il valore ARGOS e' nei portali PICCOLI/NICCHIA
- Scraper SEMPRE persistenti — MAI CSS selectors, SOLO dati strutturati

## Principi
- 640 listing grezzi non sono valore. 20 opportunita' verificate con margine stimato SONO valore
- Spazzatura nei raw data e' NORMALE — serve motore che filtra
- Se un componente esiste, USALO. Non reinventarlo.
