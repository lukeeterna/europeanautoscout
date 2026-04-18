# Sprint S132 — COMPLETATO 2026-04-18

## Task 1: Fix scraper slug Mercedes + BMW sedan — DONE ✓
commit 96c3865 — MODEL_SLUG aggiornato con pattern `{model}-(alle)`

## Task 2: Fix seller_name nei listing IT — DONE ✓
commit 96c3865 — INSERT include seller_name (companyName AS24)

## Task 3: E2E demo su TEST_FOUNDER — DONE ✓
msg_id: out_1776522749347_25z8o | 2026-04-18 16:29 IT
Pipeline validata: scrape → CoVe PROCEED 0.8425 → template 4-var → daemon send

## Regressione make/model — DONE ✓ (fix S136)
- Bug: 3 listing AS24.it con make/model vuoti (test S132 con params empty)
- Fix: `src/cove/scraper_cove_pipeline.py` — `_persist_to_duckdb` usa listing.make/model come primary, pipeline params come fallback
- Cleanup: 3 record corrotti eliminati da DuckDB
- Verifica: 11 listing AS24.it con make valido (count > 0 ✓)

---

## Prossimo sprint — da definire con founder

Dealer reali pronti quando:
1. Risposta TEST_FOUNDER entro 23 Aprile 2026 (o silenzio = pipeline OK)
2. Primo outreach dealer reale (Sud Italia, BMW X3/X1/Audi Q5)

Candidati (da BACKLOG.md):
- Fix seller_city (item.location disponibile, mai estratto)
- Espansione portali IT (mobile.it, subito.it)
- Scraper Classe C / Serie 3 live test
