# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-17T19:27:42Z` · sessione `aa88c90d-f90c-4542-a76b-1320e2d15a4f` · commit auto: cosmetic-skip (only NEXT_SESSION_PROMPT.md dirty, no plan/scope change)

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.
