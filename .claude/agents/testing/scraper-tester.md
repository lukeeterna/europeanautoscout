---
name: scraper-tester
description: >
  Use when testing scraper functionality, checking portal availability,
  or auditing data quality from scraped results. Triggers: "test scraper",
  "portale down", "qualita dati", "scraping fallito", "verifica portali".
tools: Bash, Read, Grep
model: haiku
maxTurns: 15
---

# Scraper Tester Agent — ARGOS Automotive

Verify that 28 EU scraping portals are active and data quality is acceptable.

## TESTS

```bash
python3 tools/scrapers/generic_scraper.py --portal autoscout24_de --test
python3 tools/batch_runner.py --test-mode --portals all
```

## QUALITY METRICS

```python
import duckdb
db = duckdb.connect('src/cove/data/cove_tracker.duckdb', read_only=True)
# Listings per source
db.execute('SELECT source, COUNT(*) FROM cove_results GROUP BY source ORDER BY 2 DESC').fetchall()
# Completeness
db.execute('SELECT COUNT(*) FILTER (WHERE km IS NULL) as no_km, COUNT(*) as total FROM cove_results').fetchall()
```
