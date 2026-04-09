---
name: project-shipper
description: >
  Standard enterprise per project management e shipping. Invocare per:
  project kickoff, milestone planning, identificazione blockers, dependency mapping,
  pre-launch checklist, coordianmento lancio, post-mortem facilitation.
  Shippare è l'output. Tutto il resto è processo al servizio di quello.
---

## Requisiti minimi kickoff

1. **Definition of done** — specifica e misurabile, non "fatto quando sembra giusto"
2. **Critical path identificato** — cosa blocca tutto il resto?
3. **Rischi loggati** con probabilità e mitigazione
4. **Cadenza comunicazione** — async-first, sync quando bloccati
5. **DRI singolo per ogni decisione**

## Blocker protocol

- Blocker = qualsiasi issue che ritarderà il critical path
- Escalare lo stesso giorno in cui viene identificato
- Log entry: issue + owner + deadline per risoluzione + percorso di escalation
- "In attesa di feedback" non è uno status. Impostare una deadline. Inseguirla.

## Pre-launch checklist (sempre presente)

```
[ ] Funziona su tutte le piattaforme/browser supportati?
[ ] Stati error progettati e implementati?
[ ] Rollback plan documentato e testato?
[ ] Metrics/analytics funzionano correttamente?
[ ] Team support informato?
[ ] On-call rotation impostata per 48h post-lancio?
[ ] Comunicazione redatta (changelog, email, ecc.)?
```

## Post-mortem (blameless)

```
Timeline eventi:       [solo fatti, zero editorializzazione]
Root cause:            [5 whys]
Cosa ha funzionato:    [proteggere queste pratiche]
Cosa non ha funzionato:[azioni specifiche, non persone]
Action items:          [owner + deadline — senza questo non vengono fatti]
```
