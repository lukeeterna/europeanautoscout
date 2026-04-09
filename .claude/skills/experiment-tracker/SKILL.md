---
name: experiment-tracker
description: >
  Standard enterprise per design e tracking esperimenti. Invocare per:
  A/B test design, hypothesis documentation, analisi risultati, calcolo
  significatività statistica, log esperimenti, sintesi apprendimenti.
  Esperimenti cattivi sprecano tempo. Quelli buoni compongono.
---

## Experiment card (obbligatoria prima di ogni test)

```yaml
ID: EXP-[numero]
Data: [start date]
Owner: [nome]
Status: DRAFT | RUNNING | CONCLUDED | ARCHIVED

HYPOTHESIS:
"Crediamo che [cambiamento] causerà [metrica] di [aumentare/diminuire] di [X%]
perché [meccanismo]. Sapremo di avere ragione quando [outcome misurabile specifico]."

SETUP:
  Control:         [descrizione]
  Variant:         [descrizione]
  Traffic split:   [%]
  Primary metric:  [KPI]
  Guard metrics:   [metriche che non devono degradarsi]
  Min sample size: [calcolato]
  Max duration:    [giorni]

RESULTS:
  Control:  [valore ± CI]
  Variant:  [valore ± CI]
  p-value:  [valore]
  Winner:   control | variant | nessuna differenza significativa

DECISION: ship | revert | iterate
LEARNING: [una frase di conoscenza trasferibile]
```

## Stopping rules

- Stop quando: significatività raggiunta AND sample minimo raggiunto
- Emergency stop: guard metric degrada > 10% in qualsiasi momento
- Stop a max duration anche se inconcludente (registrare come inconcludente)
- **MAI** fermarsi in anticipo perché il variant "sta ovviamente vincendo"
