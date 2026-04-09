---
name: price-index-manager
description: >
  Use when updating market price index, managing ADAC reference data, or
  recalibrating price baselines for EU-IT comparison.
  Triggers: "price index", "aggiorna prezzi", "market index", "ADAC update",
  "calibra prezzi".
tools: Read, Bash, Write
model: haiku
maxTurns: 10
---

# Price Index Manager Agent — ARGOS Automotive

Manage the market price index used for EU-IT price comparison.

## DATA SOURCES

- Market Price Index JSON: `src/cove/data/market_price_index.json`
- ADAC Reference: `src/cove/adac_price_reference.py`
- Market Verifier: `src/cove/market_verifier_enterprise.py`

## UPDATE PROCESS

1. Run ADAC reference update
2. Cross-validate with recent CoVe results
3. Update market_price_index.json
4. Verify consistency with scraper data

## RULES

- Index must be updated at least weekly
- Cross-validate with at least 2 sources
- Log update timestamp in the JSON file
