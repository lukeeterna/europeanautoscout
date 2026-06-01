---
name: outreach-day1
description: >
  Genera o valida messaggio Day 1 per dealer italiano. Carica quando Luke
  dice "genera day 1", "messaggio per [dealer]", "outreach", "contatta dealer",
  o nomina un dealer specifico per primo contatto. NON caricare per follow-up
  Day 3+ o per analisi CoVe.
---

# Outreach Day 1 — Template fisso (prime 5 dealer, zero LLM)

## Template

**Variante A — se days_on_market disponibile:**
```
Buongiorno, sono Luca Ferretti.
Ho notato che la sua {MODELLO} {ANNO} a €{PREZZO} e' il prezzo piu' alto
tra i {MODELLO} {ANNO} che trovo su AutoScout24 in Italia,
ed e' in listing da {GIORNI} giorni.
Volevo capire se e' una scelta precisa sull'auto o se sta valutando di muoverla.
Luca
```

**Variante B — se days_on_market IS NULL (fallback):**
```
Buongiorno, sono Luca Ferretti.
Ho notato che la sua {MODELLO} {ANNO} a €{PREZZO} e' il prezzo piu' alto
tra i {MODELLO} {ANNO} che trovo su AutoScout24 in Italia in questo momento.
Volevo capire se e' una scelta precisa sull'auto o se sta valutando di muoverla.
Luca
```

## Variabili — da dove vengono
- `{MODELLO}`: vehicle_listings.model (es. "X3 xDrive20d")
- `{ANNO}`: vehicle_listings.year
- `{PREZZO}`: vehicle_listings.price (formato €XX.XXX)
- `{GIORNI}`: vehicle_listings.days_on_market — se NULL usa Variante B

## Regole messaggio
- Se non hai TUTTI e 3 i dati certi (MODELLO, ANNO, PREZZO) → NON generare
- Se "prezzo piu' alto" non e' verificabilmente vero → usa altra osservazione reale
- MAI: "Germania", "estero", "import", "premium", "cerco auto", "opportunita'"
- MAI call-to-action: zero "attendo riscontro", zero "posso inviarle"
- MAI emoji, link, allegati nel Day 1
- Firma secca: solo "Luca"
- Citare il veicolo specifico del dealer e' PERMESSO (osservazione su di lui)
- Dichiarare cosa fa Luca / dove cerca → VIETATO (attiva filtro anti-spam)

## Gotchas
- "Diversi mesi" al posto di "{GIORNI} giorni" → VIETATO, usa numero esatto
- Ogni numero nel messaggio deve essere verificabile dal dealer su AS24
- Se campione benchmark < 5 listing → non dire "media", di' "tra i [N] che trovo oggi"
- Il messaggio non e' generato da LLM per i primi 5 dealer — e' template + 4 variabili SQL

## Query benchmark (verifica "prezzo piu' alto")
```sql
SELECT make, model, year, price, km
FROM vehicle_listings
WHERE source = 'autoscout24_it'
  AND make = '{MAKE}' AND model LIKE '%{MODELLO_BASE}%' AND year = {ANNO}
ORDER BY price DESC
LIMIT 10;
```
Se il listing del dealer non e' il piu' alto → non usare questa affermazione, trovane un'altra vera.
