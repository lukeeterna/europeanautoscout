# HANDOFF — auto-20260708T190623Z — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: cablare nel filtro ICP l'esclusione dei concessionari ufficiali di rete + ri-selezione seed=42 sul pool corretto (zero rete/invii/push).
- Esito: filtro OFFICIAL_NETWORK attivo (test 6/6 verde) · re-apply 7 profili → 5 ICP-validi, 2 Centro Porsche esclusi · re-select seed=42 doppio run identico → Visauto Treviso Srl (13099). Commit 1da438e, no push.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 1da438e 2026-07-08 · working-tree dirty (solo file NON miei: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md = auto-generati SessionStart hook; data/pool_icp/_backup_reapply_* = artefatto Rule 1d)
- commit di questa sessione: 1da438e "BRIEF_A2 UNITÀ A+B: filtro ICP esclude concessionari ufficiali di rete + ri-select seed=42"

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED |
| 9A | approve -> send | VERIFIED |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (fatto esterno: sign_url firmato da dealer reale) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE
[A] E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto" = anelli 1/6-7/9B UNVERIFIED · [E] trasparenza deployata = CHIUSO (LIVE ROOT 'Azzurra', commit 118343b) · [D] base-mercato fidata = VERIFIED (BM smoke)

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
6-7 E2E: gate HITL dossier su iMac + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale). Prima azione che innesca Gate E classe outreach_real.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Anello 8: sign_url firmato dal dealer reale (HITL fisico).
- Invio a dealer REALE: gate tecnici (E2E TEST_FOUNDER verde + Luke soddisfatto).

### BACKLOG (differito, NON prerequisito del primo invio)
- `/send` non impone `approved_ts` (garanzia HITL vive nel caller): far rispettare approved_ts all'endpoint o instradare ogni invio nel bridge — gated su autonomia-invio, NON ora.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Bug latente chiuso: `select_pilot_dealer.load_icp_profiles()` caricava TUTTI i dealer_*.json ignorando `_icp.is_icp` → S306 aveva selezionato "Centro Porsche Latina" (concessionario UFFICIALE di rete). Ora rispetta il flag; il file escluso resta su disco ma non entra nel pool.
- Pattern "BMW <City>" implementato come `\bbmw\s+\w+` (idem Mercedes-Benz): sui 7 profili è inerte (nessun company_name contiene "bmw"/"mercedes-benz"), ma su nomi multimarca che elencano il brand nel nome darebbe falso-positivo di esclusione — esclusione conservativa, coerente col mandato "zero rete ufficiale". Rivedibile se emerge un caso reale.
- Re-select su pool 5 → Visauto Treviso Srl (13099), multimarca indipendente (Audi/Volvo/Peugeot/Fiat/Dacia/Porsche/BMW), official_network_match=None.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ (BRIEF_A2) · STATE.md §3 (gate legale/trasparenza)
