# HANDOFF — dae7b0a1-6bec-4486-9bb7-d0dcd667f803 — 2026-07-14 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: FIX-RS 4 filiali Autotorino + riconcilia provenienza in data/recon/mandatari/roma.json; U2 sintesi pilota 3 province (Potenza/Treviso/Roma).
- Esito: UNITÀ A (riconciliazione provenienza) + UNITÀ B (fix RS) committate in af4bab0. U2 (sintesi) NON eseguita: guard context >60% al write → U2-v3 rinviata a sessione successiva.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD b8431ae 2026-07-14 (auto-close hook) · working-tree dirty
- commit di questa sessione: **af4bab0** "recon-mandatari Roma: riconcilia provenienza (caveat 12/10 -> 11/11) + fix RS 4 filiali Autotorino" (parent di b8431ae, in history)
- dirty non-miei (effimeri, NON committati da me): .claude/NEXT_SESSION_PROMPT.md, vos-out/decisions.jsonl, data/pool_icp/_backup_reapply_20260708T171250Z/
- untracked MIO non committato: docs/briefs/SINTESI_PILOTA_MANDATARI.md = **draft v1 SUPERATO** (nomenclatura "IN-TARGET" vietata da spec U2-v3). Lasciato untracked di proposito → prossima sessione = CASO 1 (edit correttivo).

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da state/rings.json last_status)
1 = UNVERIFIED
2 = PASS
9A = PASS
9B = UNVERIFIED
5 = PASS
6-7 = UNVERIFIED
8 = BLOCKED
BM = PASS

### GATE A DEALER REALE (OUTPUT VERBATIM)
[#1 Day1] = UNVERIFIED (APERTO) · [#6-7 invio PDF] = UNVERIFIED (APERTO) · [#8 sign_url] = BLOCKED-ON dealer reale

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Applicare U2-v3 a docs/briefs/SINTESI_PILOTA_MANDATARI.md (CASO 1 = edit correttivo del draft già su disco): nomenclatura LEAD/QUALIFICABILE/CONTATTABILE, ICP={solo-anagrafe}, escludere probabile-agente-di-concessionaria (visibile con nota off-ICP), telefono PZ/TV = "n/d" mai 0, proiezione ~100 province SOLO da riga COPERTURA → commit "U2 v3: metrica target corretta (comparabilità + ICP)". Numeri già ricalcolati da disco (vedi NOTE).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
[#8 sign_url] BLOCKED-ON dealer reale.

### BACKLOG (differito, NON prerequisito del primo invio)
- Backfill telefono per Potenza e Treviso (harvest non eseguito → CONTATTABILI non comparabile).
- Stabilire universo PagineGialle per PZ e TV (prerequisito alla proiezione rollout).
- Footprint linguistico non harvestato (PZ/TV/RM).

### NOTE PER IL GIUDICE
- UNITÀ A: riconteggio da disco 11 scheda-diretta / 8 serp-snippet / 3 websearch-noncamerale (+6 NON-ARRICCHIBILE) = 28; su 22 con-P.IVA = 11 scheda / 11 serp+websearch. test-sospetto 0 hit → caveat "12/10" era mis-conteggio AGGREGATO, corretto a "11/11". Campo riconciliazione_provenienza aggiunto con prova.
- UNITÀ B: 4 righe P.IVA 01559111008 (idx array 0-based 18-21 = 1-based 19-22) RS → "AUTOTORINO ROMA S.P.A."; storia preservata in rs_precedente ("Mercedes-Benz Roma S.p.A.", acquisizione gruppo Autotorino gen-2024). Checksum P.IVA invariato (4). 0 RS Mercedes residue.
- Numeri U2-v3 pronti (da disco): LEAD-QUALIFICABILI (solo-anagrafe) PZ=19 TV=22 RM=11; CONTATTABILI-SUBITO PZ=n/c TV=n/c RM=4; VERIFICATI=0 ovunque; %non-operative PZ=2,4% TV=7,5% RM=3,6%; COPERTURA con fonte solo RM (<14%, 28/«>200»), PZ/TV N/D → proiezione omessa.
- DISCORDANZA disco vs assunto giudice: "STATO è solo-RM" è FALSO su disco — stato popolato TV 27/40, RM 12/28, PZ 1/42.
- Un auto-close hook ha creato b8431ae DOPO il commit di mandato af4bab0 (nessun impatto: af4bab0 resta in history).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 segmento/geografia) · docs/briefs/SINTESI_PILOTA_MANDATARI.md (draft v1, da portare a v3) · data/recon/mandatari/{roma,potenza,treviso}.json
