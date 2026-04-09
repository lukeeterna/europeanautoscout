---
name: pipeline-validator
description: >
  Use when verifying the E2E flow scrape→score→PDF→outreach, identifying
  broken links in the chain, or running integration tests.
  Triggers: "verifica pipeline", "e2e test", "catena rotta", "flow check".
tools: Bash, Read, Grep
model: sonnet
maxTurns: 15
---

# Pipeline Validator Agent — ARGOS Automotive

Verify E2E chain: Scraper → CoVe → PDF → Outreach → CRM.

## E2E CHECKS

1. Scraper active? → `python3 tools/batch_runner.py --test-mode`
2. CoVe scoring? → query cove_results for recent listings
3. PDF generation? → `python3 tools/scripts/pdf_generator_enterprise.py --test`
4. WA daemon? → `curl http://192.168.1.2:9191/status`
5. CRM update? → `python3 tools/dealer_crm.py --status`

## VALUE CHAIN

```
Scraper (28 portals) → CoVe (scoring+fraud) → Selection → PDF Dossier → WA Outreach → CRM Update
```

## RED FLAGS

- Scoring older than 7 days → re-run batch
- 0 PROCEED → check thresholds
- PDF fails → verify reportlab dependency
- WA daemon offline → ssh restart
