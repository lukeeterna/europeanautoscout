# HANDOFF — fff4aca6-cf4a-4d09-8f18-a78ce607a464 — 2026-07-14 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: READ-ONLY (repo) — research + fact-check
- Mandato: valutare il dossier deep-research (giudice Claude.ai) sul segmento intermediari auto "su mandato" IT — 3 province Potenza/Treviso/Roma — e verificarne i claim contro fonti primarie.
- Esito: dossier verificato via 3× research-fact-checker. Struttura ATECO 2025 e impianto GDPR CONFERMATI; 3 refusi fattuali + 1 dato UNVERIFIABLE isolati (vedi NOTE). Nessun file repo toccato (artefatto in /tmp). U2-v3 pilota mandatari resta il prossimo passo (invariato).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD d1f7cdc 2026-07-14 (auto-close hook) · working-tree dirty
- commit di questa sessione: **nessuno** (READ-ONLY sul repo)
- dirty già presenti all'avvio (NON miei, NON committati): .claude/NEXT_SESSION_PROMPT.md, vos-out/decisions.jsonl, data/pool_icp/_backup_reapply_20260708T171250Z/, docs/briefs/SINTESI_PILOTA_MANDATARI.md (draft v1 SUPERATO, da portare a v3)

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
Applicare U2-v3 a docs/briefs/SINTESI_PILOTA_MANDATARI.md (CASO 1 = edit correttivo del draft già su disco): nomenclatura LEAD/QUALIFICABILE/CONTATTABILE, ICP={solo-anagrafe}, escludere probabile-agente-di-concessionaria (visibile con nota off-ICP), telefono PZ/TV = "n/d" mai 0, proiezione ~100 province SOLO da riga COPERTURA → commit "U2 v3: metrica target corretta". Numeri già ricalcolati da disco (vedi NOTE handoff precedente in git history b8431ae).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
[#8 sign_url] BLOCKED-ON dealer reale.

### BACKLOG (differito, NON prerequisito del primo invio)
- Backfill telefono per Potenza e Treviso (harvest non eseguito → CONTATTABILI non comparabile).
- Stabilire universo PagineGialle per PZ e TV (prerequisito alla proiezione rollout).
- Footprint linguistico non harvestato (PZ/TV/RM).
- Recuperare il numero reale imprese ATTIVE ATECO 2025 (46.18.41/47.92.21/47.92.31) per PZ/TV/RM+Italia da fonte Movimprese/InfoCamere consultabile (oggi UNVERIFIABLE — vedi NOTE).

### NOTE PER IL GIUDICE
- FACT-CHECK dossier mandatari (fonte: 3× research-fact-checker, 2026-07-14). CONFERMATI: ATECO 2025 operativa dal 1°apr2025; codici 46.18.41/47.92.21/47.92.31 (intermediari) e 46.71.10/47.81.10 (con stock); GDPR → per email/WA a persone fisiche e ditte individuali serve CONSENSO opt-in (art.130 Codice Privacy lex specialis, ribadito Garante prov. ott-2025), legittimo interesse NON valido; soft opt-in art.130 c.4 solo cliente esistente+servizi analoghi.
- REFUSI DA CORREGGERE nel dossier (verificati vs fonte primaria): (1) Linee guida spam Garante = G.U. n.174 del 26 lug 2013 (Delibera n.330), NON "n.230 del 3 ott 2013"; (2) Ad Library API versione corrente = v25.0, NON v23.0; (3) `limit` max 2000 NON documentato ufficialmente da Meta (fonti divergono 1000/2000/5000).
- DATO UNVERIFIABLE spacciato per fatto: "Italia 46.18.41 = 5.346 imprese" → nessuna fonte pubblica; da trattare n/d finché non reperito su Movimprese.
- RISERVA GDPR: esclusione persone giuridiche da "interessato" (D.L. 201/2011) ≠ via libera allo spam verso S.r.l. → art.130 Titolo X resta applicabile al "contraente".
- Artefatto sessione (fuori repo): /tmp/dossier_mandatari_giudice.md (dossier giudice verbatim + nota-verifica in coda). Backup handoff: HANDOFF_CURRENT.bak-20260714T152332Z.md.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 segmento/geografia) · docs/briefs/SINTESI_PILOTA_MANDATARI.md (draft v1, da portare a v3) · data/recon/mandatari/{roma,potenza,treviso}.json
