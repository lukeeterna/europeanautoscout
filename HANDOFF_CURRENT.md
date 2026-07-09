# HANDOFF — S309 — 2026-07-09 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: addendum al fix gate Day-1 — bloccare perifrasi estero/import nel validator + test sintetici; incollare verbatim la regola communication.md; aggiungere vincolo provenienza nel prompt del generatore; NON rigenerare il messaggio.
- Esito: gate `FORBIDDEN_PROVENANCE` (check v) attivo; test 15/15 PASS; prompt #7 = divieto totale provenienza (endorsement perifrasi rimosso da #4/#7). Il msg S308 ora FALLISCE il gate (atteso). Nessuna rigenerazione. Commit 5019cf6, zero push.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 5019cf6 2026-07-09 · working-tree dirty (solo NON miei: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md = auto-generati hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = artefatto pre-esistente)
- commit di questa sessione: 69f20f1 (Day-1 gen S308) · 2194c76 (handoff S308) · 5019cf6 (gate provenienza S309)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### REGOLE GEO — VERBATIM DA DISCO (per decisione Luke+giudice: la regola sta o è stale?)
- `.claude/rules/communication.md:21` → `- MAI: "veicolo EU" "ROI" "pipeline" "piattaforma" "algoritmo" "reimportazione"`
- `CLAUDE.md:17` (progetto) → `- Day 1: MAI "Germania", "import", "premium", "cerco auto", "estero"`
- MOTIVAZIONE scritta accanto: ASSENTE in entrambe (nessun commento inline). Il razionale implicito vive nella sequenza-credibilità Sud Italia (non firmare da "broker import"), ma NON è documentato accanto alla regola.

### STATO E2E (da STATE.md, verbatim)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED |
| 9A | approve -> send | VERIFIED |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (sign_url firmato da dealer reale) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE
[A] E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto" = anelli 1/6-7/9B UNVERIFIED · [E] trasparenza deployata = CHIUSO ('Azzurra', 118343b) · [D] base-mercato = VERIFIED

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
DECISIONE LUKE: la regola geo (communication.md:21 / CLAUDE.md:17) STA o è stale? Solo dopo la sua risposta si rigenera il Day-1 Visauto col prompt+gate aggiornati.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Decisione Luke sulla regola geo (blocca la rigenerazione del messaggio).
- TENSIONE STRATEGICA da risolvere con Luke: il FATTO KB `frode_km_verifica.md:21` ("auto importate 6,3% vs 2,1% domestiche = rischio >3x") è INTRINSECAMENTE sulla provenienza import. Un divieto TOTALE di riferirsi alla provenienza NEUTRALIZZA il gancio km del Day-1 (la statistica perde il soggetto). Va deciso: (a) la regola geo prevale e il gancio km cambia, oppure (b) si concede un riferimento minimo controllato. CC non risolve da solo (scope strategico).
- Anello 8: sign_url firmato dal dealer reale.

### BACKLOG (differito, NON prerequisito del primo invio)
- `/send` non impone `approved_ts` (garanzia HITL nel caller) — gated su autonomia-invio.
- 6-7 E2E su iMac (gate HITL fastapi + PDF a TEST_FOUNDER 393314928901).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Buco chiuso: il validator NON controllava affatto la provenienza (solo garanzia/certificato). Ecco perché "fuori mercato italiano" passava. Ora check (v) copre diretti + perifrasi; test 15/15.
- Il prompt #7 ora VIETA la provenienza ma #4 (stat "circa 3 volte") resta OK solo perché ho tolto il legame esplicito "sulle auto che arrivano da fuori mercato italiano" — vedi TENSIONE sopra: il legame è reale nel dato KB.
- data/day1/visauto_treviso_day1.txt NON toccato (evidenza): ora fallirebbe il gate. Regen solo post-decisione.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ · .claude/rules/communication.md · kb/dominio/frode_km_verifica.md · STATE.md §3
