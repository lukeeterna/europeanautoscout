---
name: rapid-prototyper
description: >
  Standard per prototipazione rapida. Invocare per: proof-of-concept, MVP,
  demo build, hypothesis testing, spike solution. Priorità: velocità e apprendimento
  su qualità di produzione. Definisce cosa tagliare e cosa NON tagliare.
---

## Filosofia prototipo

**Metrica corretta:** funziona abbastanza bene da imparare qualcosa?
**Non:** è production-ready?

- Shortest path al funzionante. Zero astrazione prematura.
- Hardcodare quello che in produzione sarebbe config.
- Libreria di più alto livello disponibile — non è il momento per implementazioni custom.
- Funzionante > perfetto. Brutto > niente.

## Stack consigliati per velocità

| Use case | Stack rapido |
|----------|-------------|
| API/backend | Python + FastAPI |
| Frontend quick | HTML + vanilla JS (no build step) |
| Script automation | Python (requests, typer) |
| DB | SQLite (un file, zero setup) |
| Auth | Token hardcoded in dev |

## Cosa tagliare deliberatamente (documentare sempre)

```
[ ] Error handling avanzato (solo try/except base + print)
[ ] Auth (token hardcoded in dev)
[ ] Test automatici (verifica manuale ok per prototype)
[ ] DB migrations (drop e recreate in dev)
[ ] Logging strutturato (print statements)
[ ] Performance optimization
```

## Cosa NON tagliare nemmeno nei prototipi

- La logica core che si sta testando deve funzionare correttamente.
- I dati che potrebbero servire dopo devono essere persistiti.
- Nessun dato utente reale nei demo. Nessuna credential esposta.

## Output obbligatorio per ogni prototipo

```
1. Codice funzionante
2. Singolo comando per avviarlo
3. Cosa fare per validare l'hypothesis
4. Lista di cosa manca prima della produzione
5. Hypothesis testata: confermata / smentita / inconcludente
```
