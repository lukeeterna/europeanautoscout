---
name: argos-validator
description: >
  Validazione dati ARGOS: verifica che ogni dato usato in messaggi, dossier,
  e comunicazioni sia VERO e ATTUALE. Controlla veicoli su AS24.de,
  prezzi di mercato, dati dealer, claim nei messaggi.
  TRIGGER su: "verifica veicolo", "controlla prezzo", "valida messaggio",
  "check dati", "esiste ancora", "prezzo reale", "verifica claim",
  "audit messaggio", "fact check".
version: 1.0.0
allowed-tools: Bash, Read, Write, Agent
---

# ARGOS™ Validator — Verifica Dati Reali

## SCOPO
Verificare che OGNI dato usato nelle comunicazioni ARGOS sia:
1. VERO (non inventato)
2. ATTUALE (non vecchio di settimane)
3. VERIFICABILE (il dealer può controllare)

## COMANDI

### `veicolo <marca> <modello> <anno> <prezzo_claim>`
Verifica che un veicolo con quelle caratteristiche ESISTA su AS24.de al prezzo indicato.

```python
# Cerca su AutoScout24.de con filtri
# URL: https://www.autoscout24.de/lst/{marca}/{modello}?atype=C&cy=D&fReg={anno}&...
# Verifica: esiste almeno 1 listing entro ±10% del prezzo claim?
# Output: CONFERMATO (link listing) | NON TROVATO | PREZZO DIVERSO (reale: €X)
```

### `prezzo-it <marca> <modello> <anno>`
Verifica il prezzo medio in Italia per confronto col claim DE.

```python
# Cerca su AutoScout24.it
# Calcola media e range prezzi
# Output: media €X, range €Y-€Z, N listing trovati
```

### `messaggio <dealer_name>`
Audita un messaggio WA prima dell'invio:

Checklist:
- [ ] Il veicolo citato ESISTE su AS24.de? (verifica link)
- [ ] Il prezzo DE è REALE? (±10%)
- [ ] Il prezzo IT è REALE? (±10%)
- [ ] Il margine calcolato è CORRETTO? (DE + trasporto + costi vs IT)
- [ ] Il nome dealer è scritto CORRETTAMENTE?
- [ ] La città è GIUSTA?
- [ ] Le recensioni citate sono VERE? (numero e rating)
- [ ] Lo stock citato è ATTUALE? (controlla su Subito/AS24)
- [ ] ZERO buzzword vietate? (piattaforma, algoritmo, scouting, CoVe, AI)
- [ ] ZERO link nel Day 1?
- [ ] Max 4-5 righe?
- [ ] Framework V3 CHI-PERCHE'-CHIEDI rispettato?

Output: PASS | FAIL + lista problemi

### `dossier <pdf_path>`
Audita un PDF dossier prima dell'invio:

Checklist:
- [ ] Foto sanitizzate (no targhe visibili, no branding dealer)
- [ ] Prezzo coerente con mercato
- [ ] Grade/score coerente con dati
- [ ] Dealer watermark corretto
- [ ] Nessun dato inventato
- [ ] Layout leggibile

### `claim <affermazione>`
Verifica una singola affermazione:
- "BMW X3 2022 a €28.500 in Germania" → cerca su AS24.de
- "In Puglia la stessa auto parte da €36.000" → cerca su AS24.it
- "34 recensioni 4.9/5" → controlla su Google Maps/AS24

## FONTI DI VERIFICA
```
AS24.de:  https://www.autoscout24.de/lst/{marca}/{modello}?atype=C&cy=D
AS24.it:  https://www.autoscout24.it/lst/{marca}/{modello}?atype=C&cy=I
Mobile.de: https://suchen.mobile.de/fahrzeuge/search.html?...
Google Maps: ricerca diretta nome dealer
```

## REGOLE
- MAI approvare un messaggio con dati non verificati
- Se il veicolo non esiste più → segnalare e proporre alternativa
- Se il prezzo è cambiato → aggiornare prima dell'invio
- Ogni verifica deve avere timestamp (i prezzi cambiano)
- Usare resilient_fetcher.py per fetch
- Salvare log verifiche in data/validation_log.json

## RIFERIMENTI
```
research/s94_MESSAGGI_DEFINITIVI_V3.md  ← messaggi da validare
tools/scrapers/resilient_fetcher.py     ← fetch anti-bot
tools/scrapers/autoscout_scraper.py     ← scraper AS24
src/cove/cove_engine_v4.py              ← scoring (NON MODIFICARE)
```
