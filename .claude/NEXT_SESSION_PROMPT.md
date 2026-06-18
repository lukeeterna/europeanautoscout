# Breadcrumb ripartenza — STATE.md è il source-of-truth

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Prossima sessione = [A1] E2E 6-7 su TEST_FOUNDER (DEDICATA, budget pieno)

→ Incolla **docs/RECOVERY_PROMPT_S282.md** (router freddo + prompt operativo [A1]).

Chiuso in S281: [A0] WA daemon `connected` (verificato via probe reale); token applicati su iMac .env.
Routing: STATE.md → docs/ROADMAP.md → docs/briefs/BRIEF_A_e2e_67_testfounder.md.

## Come riprendere
1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>` — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md` + incolla `docs/RECOVERY_PROMPT_S282.md`
