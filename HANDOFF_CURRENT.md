# HANDOFF — auto-20260709T174202Z — 2026-07-09 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE (edit handoff + template chiusura; nessun codice-prodotto toccato)
- Mandato: correggere il "falso-verde" gate [A]. Verità trovata: il falso-verde viveva nel LAYER-RENDER incollato al giudice, NON su disco.
- Esito: prova discriminante → `git log b82ee1a..HEAD -- HANDOFF_CURRENT.md` VUOTO (blob a b82ee1a IDENTICO a HEAD); il disco mostra [A]=UNVERIFIED, MAI "= CHIUSO". [A] reso esplicito su disco. Regola render-verbatim cablata in `.claude/commands/chiudi-ordinatamente.md`. UNITÀ 2+3 rinviate a sessione fresca (context budget).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD a7b2b63 (pre-commit sessione) · working-tree dirty (NON miei: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md = auto-hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = artefatto pre-esistente)
- commit di questa sessione: handoff [A] esplicito + regola render-verbatim (vedi git log)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da state/rings.json last_status — non re-narrare)
| # | Anello | last_status |
|---|--------|-------------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | PASS |
| 9A | approve -> send | PASS |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | PASS |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED |
| BM | base-mercato IT fidata | PASS |
(STATE.md mappa PASS→VERIFIED solo per display; la sorgente autoritativa è last_status qui sopra.)

### GATE A DEALER REALE (OUTPUT VERBATIM — non re-narrare)
[A] = APERTO/BLOCKED-ON — E2E TEST_FOUNDER mai eseguito (anelli 1/6-7/9B UNVERIFIED); glue Day-1→queue_outbound(phase='DAY1') inesistente · [E] trasparenza deployata = CHIUSO ('Azzurra', 118343b) · [D] base-mercato = VERIFIED

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Sessione fresca — UNITÀ 2: check (vi) deterministico in validate_day1 che boccia (a) verifica-km sullo STOCK/auto-in-vendita del destinatario e (b) claim di danno ai SUOI clienti; fixture colpevole `data/day1/visauto_treviso_day1_v2.txt` DEVE fallire il nuovo check (violazione nominata). Poi UNITÀ 3: rigenerare v3 (gancio = proteggere acquisti/permute del dealer dalla frode km).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Gate [A]: E2E TEST_FOUNDER 393314928901 verde + Luke "pienamente soddisfatto" (anelli 1/6-7/9B UNVERIFIED).
- Anello 8: sign_url firmato dal dealer reale.
- OK esplicito di Luke sul testo Day-1 prima di qualunque invio.

### BACKLOG (differito, NON prerequisito del primo invio)
- `/send` non impone `approved_ts` (garanzia HITL nel caller) — gated su autonomia-invio.
- 6-7 E2E su iMac (gate HITL fastapi + PDF a TEST_FOUNDER 393314928901).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- FALSO-VERDE = LAYER-RENDER, non disco. Il render S310 incollato asseriva [A]=CHIUSO ×2 (campo 4 "= CHIUSO" + campo 5 "gate [A] comunque chiuso"), ma il blob HANDOFF a b82ee1a è IDENTICO a HEAD e mostra [A]=UNVERIFIED. Nessun edit post-hoc su disco. Root cause = prosa riformulata nel render.
- FIX cablato: regola render-verbatim in `.claude/commands/chiudi-ordinatamente.md` (REGOLE FERME + sezioni STATO E2E/GATE): campi gate/anelli = OUTPUT VERBATIM di comando, MAI prosa; gate non raggiunto = "= APERTO/BLOCKED-ON", MAI "= CHIUSO".
- UNITÀ 1 come formulata (correggere falso-verde su disco) DECADE: disco già corretto. Eseguita solo la riga chiarificatrice [A] (approvata).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ · .claude/rules/communication.md · kb/dominio/frode_km_verifica.md · STATE.md §3
