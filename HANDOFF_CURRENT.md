# HANDOFF — recon-mandatari U1 verifica-campione Roma — 2026-07-13 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE (solo dati: JSON verifica-campione; nessun codice pipeline)
- Mandato: U1 verifica-campione Roma (10 righe stratificate, Fonte-B indipendente per-riga) → gate promozione anagrafe mandatari.
- Esito: **Roma PROMOSSA** — 9/10 MATCH-OK, 1 INCERTA, 0 KO (soglia ≥8/10). U2 SINTESI 3 province NON avviata (gate context #7). Potenza/Treviso invariate (PROMOSSE).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD e7f749b (2026-07-13, "FB harvester CHIUSO → portale-first", sessione SUCCESSIVA) · working-tree dirty: `.claude/NEXT_SESSION_PROMPT.md`, `vos-out/decisions.jsonl`, untracked `data/pool_icp/_backup_reapply_20260708T171250Z/` — NON miei (effimeri/altre sessioni), non committati.
- commit di questa sessione: **a8e67c7** (`data/recon/mandatari/roma_campione.json`, +125) — in history, pre-commit PASS.
- PUSH: NON eseguito (VIETATO S278). ahead di origin.
- Backup Rule 1d: nessun .bak creato — roma.json solo LETTO, output su file NUOVO roma_campione.json.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da state/rings.json last_status)
#1 invio Day1 WA: UNVERIFIED
#2 classifier intent (AMBRA): PASS
#9A approve -> send: PASS
#9B reject -> abort: UNVERIFIED
#5 generazione dossier PDF: PASS
#6-7 approve HITL dossier -> invio PDF al dealer: UNVERIFIED
#8 contract -> sign_url: BLOCKED [blocked_on: sign_url firmato dal dealer reale — fatto esterno non raggiungibile in-sessione]
#BM base-mercato IT fidata: PASS

### GATE A DEALER REALE (OUTPUT VERBATIM da rings.json)
[#1 Day1] = UNVERIFIED (APERTO) · [#6-7 invio PDF] = UNVERIFIED (APERTO) · [#8 sign_url] = BLOCKED-ON dealer reale

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
U2 SINTESI PILOTA 3 province (Potenza/Treviso/Roma) → `docs/briefs/SINTESI_PILOTA_MANDATARI.md`: tabella colonne fisse + riga COPERTURA-con-fonte (senza copertura = niente proiezione rollout). Prerequisito già soddisfatto: 3 province PROMOSSE.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- #8 sign_url firmato da dealer reale (HITL fisico Luke o terzo).

### BACKLOG (differito, NON prerequisito)
- **RS stantia idx 18-21** (P.IVA 01559111008): correggere `ragione_sociale_camerale` da "MERCEDES-BENZ ROMA S.P.A." → "AUTOTORINO ROMA S.P.A." in roma.json prima uso operativo.
- Footprint linguistico web ("su commissione") non harvest-ato (Potenza/Treviso/Roma).
- Backfill telefono Potenza/Treviso (0% harvest lì); campo STATO solo-RM.
- Anomalie: idx6 Gold Car (2 P.IVA), idx12 Autodardo (2 entità).

### NOTE PER IL GIUDICE
- U1: idx3 F.G. AUTO era camerale=None → RS identificata via Fonte-B (SAS di Aureli C.M.); upgrade riga. idx9 stato "in liquidazione" da fonte camerale NON riconfermato da directory (flag). idx18 = caso RS-stantia scovato dal campione (voluto).
- Discordanza metadata roma.json: caveat dice "12 serp/10 scheda" ma tag provenienza_qualita per-riga = 11/11 (usati i tag per-riga).
- HANDOFF precedente era stale (diceva "verifica-campione NON eseguita"): rigenerato con U1 DONE.

### DOVE STA LA STRATEGIA (puntatori)
docs/briefs/FONTI_MANDATARI.md §8 · data/recon/mandatari/{potenza,treviso,roma}.json · data/recon/mandatari/roma_campione.json (verifica U1)
