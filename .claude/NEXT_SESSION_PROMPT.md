# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-26T21:52:00Z` · sessione `e4b82626-e69e-495a-9f1a-9999acb7f4b2` · commit auto: committed: 389c186

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.
