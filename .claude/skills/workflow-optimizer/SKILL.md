---
name: workflow-optimizer
description: >
  Standard enterprise per ottimizzazione workflow di sviluppo. Invocare per:
  velocizzare pipeline CI/CD, migliorare code review process, identificare
  bottleneck nei processi, automazione opportunità, developer experience.
  Il tempo developer è la risorsa più costosa. Eliminare gli sprechi.
---

## Metodologia audit workflow

```
1. Misurare:    dove va effettivamente il tempo? (non dove le persone pensano)
2. Identificare sprechi: attese, rework, context switching, ownership non chiara
3. Prioritizzare bottleneck: fixare il vincolo, non le cose facili
4. Automatizzare: qualsiasi cosa fatta allo stesso modo > 3 volte
5. Misurare di nuovo: il cambiamento ha effettivamente aiutato?
```

## Target CI/CD pipeline

```
Target:   PR pipeline < 5 minuti
Metodi:
  - Parallelizzare test suite (non seriali)
  - Cache: dipendenze, build artifact, Docker layers
  - Fail fast: lint + type-check PRIMA di test lenti
  - Changed-file detection: non eseguire tutto su ogni PR
```

## Health code review

| Metrica | Sano | Rotto |
|---------|------|-------|
| Avg review time | < 4h | > 24h |
| PR size | < 400 righe | > 400 righe |
| Blockers | Nitpick = non-blocking | Tutto è blocking |

## Audit riunioni

Per ogni riunione ricorrente: quale decisione fa questa riunione? Cosa succede se la cancelliamo?
- Nessuna risposta chiara → cancellare e vedere cosa si rompe
- Solo condivisione informazioni → sostituire con update scritto async
- Decisione necessaria → tenere, ma ridurre a min attendees + agenda rigida

## Matrice priorità automazione

```
Alta frequenza × Alto costo = automatizzare immediatamente
Alta frequenza × Basso costo = automatizzare quando conveniente
Bassa frequenza × Alto costo = documentare e templatizzare
Bassa frequenza × Basso costo = lasciare manuale
```
