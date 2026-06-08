# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-08T12:00:36Z` · sessione `cae1b94f-eaa3-4899-a64c-bc7b954f710d` · commit auto: committed: e77f48f

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.
