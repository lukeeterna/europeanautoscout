# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-16T16:19:31Z` · sessione `f174e348-cf08-483b-bae6-b1a283252b70` · commit auto: no-changes

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.
