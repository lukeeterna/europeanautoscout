# HANDOFF — S310 — 2026-07-09 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: rigenerare il Day-1 Visauto Treviso con la decisione ratificata (regola geo PREVALE, gancio km su fatti provenienza-neutri della KB). Output = messaggio VERBATIM. NESSUN INVIO, zero push.
- Esito: v2 generato conforme (gate exit 0, groq, 1 tentativo, 0 violazioni). Prompt compositore aggiornato + filtro KB provenienza. Suite validate_day1 5/5 e provenance_gate 15/15 VERDI. Commit 227b306, zero push. v1 intatto (evidenza).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 227b306 2026-07-09 · working-tree dirty (solo NON miei: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md = auto-generati hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = artefatto pre-esistente)
- commit di questa sessione: 227b306 (Day-1 v2 + prompt/filtro + fixture neutra)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

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
DECISIONE LUKE: leggere il messaggio v2 (data/day1/visauto_treviso_day1_v2.txt) e dichiarare "va bene / correggi X". Solo dopo un suo OK esplicito si valuta l'invio (gate [A] tuttora chiuso: E2E TEST_FOUNDER non verde).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- OK esplicito di Luke sul testo v2 (blocca qualunque invio).
- Gate [A]: E2E TEST_FOUNDER 393314928901 verde + Luke "pienamente soddisfatto" (anelli 1/6-7/9B UNVERIFIED).
- Anello 8: sign_url firmato dal dealer reale.

### BACKLOG (differito, NON prerequisito del primo invio)
- `/send` non impone `approved_ts` (garanzia HITL nel caller) — gated su autonomia-invio.
- 6-7 E2E su iMac (gate HITL fastapi + PDF a TEST_FOUNDER 393314928901).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- TENSIONE S309 RISOLTA dalla decisione ratificata: il gancio km NON usa più il fatto import-based "3x" (importate vs domestiche, frode_km_verifica.md:21); usa fatti provenienza-neutri (sovrapprezzo 25-30% pagato da chi compra un'usata coi km falsati; Serie 5 = auto più manomessa in IT 8,5%). Il dato KB import resta in KB ma è ora ESCLUSO deterministicamente dal grounding del compositore.
- FINDING FASE 0: la suite `test_validate_day1` era ROSSA all'avvio — non una regressione del validator, ma fixture STANTIE: tutte le MSG usavano il vecchio gancio import ("auto importate", "dall'estero") che il gate provenienza S309 ora blocca. Riscritte in forma neutra (KB=25-30% L20) preservando l'intento di ogni caso; ora 5/5 verde. Era un buco: il "clean" della suite incarnava il comportamento pre-decisione.
- Il messaggio v2 personalizza company_name (Visauto Treviso Srl) + tier_hits (Audi, Porsche, BMW), chiude con domanda chiusa, opt-out "no grazie", identità Azzurra. Passa il gate al 1° tentativo.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ · .claude/rules/communication.md · kb/dominio/frode_km_verifica.md · STATE.md §3
