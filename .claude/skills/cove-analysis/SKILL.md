---
name: cove-analysis
description: >
  Analisi e scoring veicoli con CoVe Engine. Carica quando Luke dice
  "analizza veicolo", "score", "anomalia prezzo", "benchmark", "confidence",
  "PROCEED/SKIP", o quando stai lavorando su cove_tracker.duckdb o
  cove_engine_v4.py. NON caricare per invio messaggi o fix scraper.
---

# CoVe Analysis — Protocollo operativo

## Terminologia IMMUTABILE
- `recommendation` (MAI `verdict`)
- `analyzed_at` (MAI `created_at`)
- `confidence` 0.0-1.0
- Soglie: DEALER_PREMIUM=0.75 | VIN_CHECK=0.60 | DAILY_LIMIT=30
- `cove_engine_v4.py` → NON MODIFICARE — solo leggere e invocare

## Schema cove_tracker.duckdb
```
cove_results: listing_id, make, model, year, km, price,
              confidence, recommendation, analyzed_at
vehicle_listings: listing_id, source, make, model, year, km, price,
                  seller_name, seller_city, days_on_market, url
vehicle_images: listing_id, image_url, local_path
```

## Query frequenti

**Listing PROCEED con alta confidence:**
```sql
SELECT listing_id, make, model, year, km, price, confidence, analyzed_at
FROM cove_results
WHERE recommendation = 'PROCEED' AND confidence >= 0.75
ORDER BY confidence DESC, analyzed_at DESC
LIMIT 20;
```

**Benchmark prezzo per modello (listing IT attivi):**
```sql
SELECT make, model, year,
       COUNT(*) as n,
       MIN(price) as prezzo_min,
       MAX(price) as prezzo_max,
       ROUND(AVG(price)) as prezzo_medio,
       ROUND(AVG(km)) as km_medi
FROM vehicle_listings
WHERE source = 'autoscout24_it'
  AND make = ? AND model LIKE ? AND year = ?
GROUP BY make, model, year;
```
ATTENZIONE: questi sono listing ATTIVI, non venduto. Non dire "chiuse tra X e Y".

**Anomalia prezzo (listing sopra benchmark):**
```sql
WITH benchmark AS (
  SELECT make, model, year, AVG(price) as avg_price
  FROM vehicle_listings
  WHERE source = 'autoscout24_it'
  GROUP BY make, model, year
)
SELECT vl.listing_id, vl.seller_name, vl.price, b.avg_price,
       ROUND((vl.price - b.avg_price) / b.avg_price * 100, 1) as delta_pct
FROM vehicle_listings vl
JOIN benchmark b ON vl.make=b.make AND vl.model=b.model AND vl.year=b.year
WHERE vl.source = 'autoscout24_it'
  AND vl.price > b.avg_price * 1.05
ORDER BY delta_pct DESC;
```

## Connessione iMac (cove_tracker.duckdb e' su iMac)
```bash
ssh gianlucadistasi@192.168.1.12 "python3 -c \"
import duckdb
con = duckdb.connect('/path/to/cove_tracker.duckdb')
# esegui query
\""
```

## Regole output
- MAI CoVe/RAG/Claude/AI/Anthropic nei messaggi dealer
- Ogni numero riportato a Luke deve avere listing_id come fonte
- Se confidence < 0.60 → non usare per outreach
