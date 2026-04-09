---
name: finance-tracker
description: >
  Standard enterprise per financial tracking. Invocare per: revenue/expense tracking,
  cash flow analysis, pricing model, unit economics (CAC, LTV, payback),
  budget vs actuals, proiezioni finanziarie.
  Cash è realtà. Profit è opinione.
---

## Metriche chiave (sempre monitorate)

| Metrica | Formula | Target |
|---------|---------|--------|
| MRR/ARR | Monthly recurring revenue | + growth rate |
| Burn rate | Cash out per mese | Gross e net |
| Runway | Cash / burn rate mensile | > 12 mesi |
| CAC | Spesa S&M totale / nuovi clienti | < LTV/3 |
| LTV | ARPU medio × durata media | > CAC × 3 |
| Payback | CAC / gross margin mensile per cliente | < 12 mesi |

## Soglie di salute finanziaria

```
⚠️  Runway < 6 mesi:         raccogliere o tagliare costi immediatamente
🚨  LTV:CAC < 1:1:           si stanno comprando clienti in perdita
⚠️  Gross margin < 40% SaaS: problema strutturale, non di crescita
🚨  Monthly churn > 5%:      crisi retention — la crescita è un cerotto
```

## Analisi pricing model

Per ogni cambiamento di pricing, modellare:
```
1. Attuale:    revenue = [clienti] × [ARPU]
2. Proposto:   [nuovi clienti proiettati] × [nuovo ARPU]
3. Breakeven:  clienti necessari al nuovo prezzo = revenue attuale
4. Downside:   se perdiamo X% dei clienti, il revenue è ancora positivo?
5. Strategico: il pricing signal corrisponde al positioning?
```

## Output monthly review

```
P&L vs budget:     actual vs. pianificato, spiegazione varianza
Cash flow:         balance apertura / entrate / uscite / balance chiusura
3 metriche mosse:  cosa è successo e perché
Outlook prossimo:  flussi grandi attesi in/out
```
