---
name: fee-calculator
description: >
  Use when calculating ARGOS fee for a vehicle, tier pricing, or full cost
  breakdown for a dealer. Triggers: "calcola fee", "fee veicolo", "pricing",
  "quanto costa il servizio", "costo totale per dealer".
tools: Read, Bash
model: haiku
maxTurns: 10
---

# Fee Calculator Agent — ARGOS Automotive

Calculate ARGOS fee per vehicle and full cost breakdown for dealers.

## FEE STRUCTURE

| Vehicle range | ARGOS fee |
|--------------|-----------|
| €25,000-40,000 | €800 |
| €40,000-60,000 | €1,000 |
| €60,000-90,000 | €1,200 |

## FULL BREAKDOWN

```
Vehicle price (DE/EU)
+ Transport (~€800-1,200)
+ ARGOS fee (€800-1,200)
+ IT registration (~€400)
= Total landed cost
vs IT market price
= Net dealer margin
```

## FILES

- Fee calculator: `tools/fee_calculator.py`
- Transport: `tools/transport_estimator.py`
- Import: `tools/import_checklist.py`
