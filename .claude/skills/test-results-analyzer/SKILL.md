---
name: test-results-analyzer
description: >
  Standard enterprise per analisi risultati test. Invocare per: investigazione
  fallimenti CI, identificazione test flaky, analisi gap copertura,
  quality trend reporting, test suite health assessment, root cause regressions.
---

## Triage fallimento CI

```
1. Test flaky?         Passa al retry? Fallisce intermittentemente?
2. Vera regressione?   Quando ha iniziato a fallire? Cosa è cambiato?
3. Issue ambiente?     Fallisce localmente? Solo in CI?
4. Issue dati?         Test data deterministico? Dipendenze timing?
```

## Classificazione test flaky

| Tipo | Causa | Fix |
|------|-------|-----|
| Type A | Timing-dipendente (async senza proper await) | Fix immediato |
| Type B | State-dipendente (dipende da test precedente) | Fix immediato |
| Type C | Environment-dipendente (CI vs locale) | Environment parity |
| Type D | Data-dipendente (valori random/date-based) | Mocking |

## Copertura: metrica giusta

La copertura % totale è una vanity metric. La copertura dei **CRITICAL PATHS** è la metrica reale.

Assicurare copertura per:
- Ogni chiamata API esterna + i suoi failure modes
- Ogni transizione della state machine
- Ogni calcolo finanziario
- Ogni check auth/permission
- Ogni mutazione dati distruttiva

## Quality trend report

```
Week [N] Quality Report

TEST SUITE HEALTH:
- Total: [N] (+/- da scorsa settimana) | Pass rate: [%] (target: >98%)
- Flaky: [N] | Avg CI time: [min] (target: <5min)

COVERAGE:
- Overall: [%] | Critical paths: [%]

TOP FAILURES (per frequenza):
1. [test name]: [N] fallimenti, hypothesis: [root cause]

ACTION ITEMS:
- [fix] — Owner: [X] — Due: [data]
```
