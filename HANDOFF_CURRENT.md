# HANDOFF — auto-20260710T173320Z — 2026-07-10 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE (gate validate_day1 + suite; nessun anello E2E toccato)
- Mandato: cablare la rete direzione-servizio (check (vi) + fixture colpevole v2) e rigenerare Day-1 Visauto v3.
- Esito: UNITÀ 1 CHIUSA verde e committata (0fbd672). UNITÀ 2 (rigenerazione v3) NON iniziata — rinviata a sessione fresca per context budget (chiusura a 60%, checkpoint UNITÀ 1 rispettato).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 0fbd672 2026-07-10 · working-tree dirty (NON miei: STATE.md, state/rings.json, .claude/NEXT_SESSION_PROMPT.md = auto-hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = artefatto pre-esistente all'avvio)
- commit di questa sessione: 0fbd672 "UNITÀ1: check (vi) direzione-servizio in validate_day1 — v2 = fixture colpevole" (solo validate_day1.py + tools/tests/test_validate_day1.py)

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
UNITÀ 2 — correggere PRIMA il compositore `tools/generate_day1.py` SYSTEM_PROMPT (righe ~78-81 dicono ancora "danneggia i CLIENTI del concessionario": genererebbe un v3 colpevole che il nuovo check (vi) boccia). Nuovi vincoli: gancio = proteggere gli ACQUISTI/permute del dealer dalla frode km; marche dal profilo come FATTO senza aggettivi di pregio/valore; opt-out come istruzione al dealer. Poi `python3 tools/generate_day1.py --profile data/pool_icp/SELECTED.json --out data/day1/visauto_treviso_day1_v3.txt` (max 3 retry). Done = gate exit 0 sul v3 CON check (vi) attivo. Provider LLM giù → BLOCKED onesto, nessun v3 su disco.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Gate [A]: E2E TEST_FOUNDER 393314928901 verde + Luke "pienamente soddisfatto" (anelli 1/6-7/9B UNVERIFIED).
- Anello 8: sign_url firmato dal dealer reale.
- OK esplicito di Luke sul testo Day-1 prima di qualunque invio.
- UNITÀ 2 runtime AMBRA: generazione v3 richiede un provider non-Anthropic raggiungibile (GROQ/cascata). Se giù → BLOCKED onesto (pattern S307).

### BACKLOG (differito, NON prerequisito del primo invio)
- `/send` non impone `approved_ts` (garanzia HITL nel caller) — gated su autonomia-invio.
- 6-7 E2E su iMac (gate HITL fastapi + PDF a TEST_FOUNDER 393314928901).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- UNITÀ 1 VERDE VERIFICATA (output grezzo): suite `test_validate_day1` 8/8 (puliti a/h→exit0, vi-a/vi-b→exit1); `test_day1_provenance_gate` 15/15 no-regress; gate CLI su `visauto_treviso_day1_v2.txt` ora FAIL con 2 (vi) nominate ('auto in vendita' + 'danno ai clienti del concessionario'), exit 1. Baseline pre-modifica era v2 PASS (exit 0) — flip atteso.
- FASE 0 lessico [A]: NESSUNA micro-azione di riformulazione eseguita. La riga-gate (30) dice già `[A] = APERTO/BLOCKED-ON`; il `= CHIUSO` su quella riga è legato a [E], non ad [A]. Le uniche righe con "CHIUSO" vicino ad [A] (7, 45) lo NEGANO/documentano il falso-verde S310 — sono verbale d'incidente, non asserzioni di stato. Riformularle avrebbe corrotto il verbale (over-reach del "in qualunque senso"). Disco già univoco sull'asse-asserzione.
- ROOT del falso-verde v2: il compositore in `generate_day1.py` (righe 78-81) contiene proprio il gancio vietato ("danneggia i CLIENTI del concessionario"). Finché non lo si corregge (UNITÀ 2), ogni rigenerazione rinasce colpevole. Il gate (vi) ora lo intercetta a valle.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md · docs/briefs/ · .claude/rules/communication.md · kb/dominio/frode_km_verifica.md · STATE.md §3 · tools/generate_day1.py (compositore) · validate_day1.py (gate (vi))
