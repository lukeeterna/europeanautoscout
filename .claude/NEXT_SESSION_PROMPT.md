# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-09T10:08:22Z` · sessione `1e3cf5cf-afdc-44f3-a548-cc4bb8bd5018` · commit auto: committed: ac651ee

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.
