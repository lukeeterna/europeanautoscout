---
name: feedback-synthesizer
description: >
  Standard per sintesi feedback utenti. Invocare per: sintetizzare ticket support,
  recensioni, interviste, survey, commenti NPS. Contiene framework di categorizzazione,
  regole anti-bias e formato output strutturato.
---

## Protocollo di sintesi

1. Leggere TUTTO il feedback prima di categorizzare qualsiasi cosa.
2. Identificare temi ricorrenti (3+ menzioni = pattern degno di nota).
3. Distinguere: bug report / feature request / friction UX / value complaint.
4. Quantificare dove possibile: "17/42 utenti hanno menzionato X" > "molti utenti".
5. Preservare citazioni verbatim per il feedback più impattante/specifico.
6. Notare cosa NON è menzionato ma ci si aspetterebbe.

## Framework categorizzazione

| Categoria | Definizione | Priorità |
|-----------|------------|---------|
| **Blocker** | Impedisce completamento task core | Massima |
| **Friction** | Rende il task più difficile del necessario | Media |
| **Request** | Utenti vogliono di più | Priorità = frequenza × fit strategico |
| **Praise** | Cosa funziona (proteggere nelle modifiche) | — |
| **Confusion** | Incomprensione del prodotto | UX o comunicazione |

## Bias da correggere attivamente

- **Minoranza vocale:** verificare se il feedback forte rappresenta volume o solo intensità.
- **Recency bias:** non pesare il feedback recente sopra pattern consolidati senza motivo.
- **Channel bias:** ticket support tendono al negativo, le recensioni agli estremi.

## Output obbligatorio

```
Executive summary (max 3 frasi)

Tabella insight prioritizzati:
| Categoria | Insight | Frequenza | Citazione rappresentativa |

Azioni raccomandate (specifiche, non vaghe):
- [azione] → Owner: [X] → Impatto atteso: [Y]
```
