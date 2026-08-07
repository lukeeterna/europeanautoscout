# ROADMAP-PRODUZIONE — ARGOS
scadenza: 2026-08-27 · fonte: git (mai memoria)

## Stato al 2026-08-01
branch: s210/audit-master-plan · HEAD: d3021d714c07e82367eeb0e5152e20583d245efd
gate [A] RESPINTO 31/07: Day1 template con falsa personalizzazione.

## Infrastruttura verificata — non riscoprire
- Daemon WA :9191 su iMac (PM2), finestra lun-sab 08:00-19:59 Europe/Rome, 20 invii/giorno
- gate_e.py: allowlist TEST_FOUNDER da os.environ; selftest 33/33 PASS
- .env.test: presente su iMac, NON in git
- rpo_lista_44.csv in data/recon/mandatari (gitignorata)
- CoVe v4: src/cove/cove_engine_v4.py — NON modificare
- Day1 v5 CTA verifica-targa: research/s94_MESSAGGI_DEFINITIVI_V3.md

## Già falsificato — non ritentare
1. UNVERIFIED in rings.json NON significa rotto: #1 e #6-7 hanno check_cmd null, campo machine-owned, non aggiornabile da refresh.
2. L'E2E verifica il TRASPORTO, non il CONTENUTO. Un E2E verde non apre il gate [A].
3. I 401 su /send erano la chiave WA presente solo sull'iMac, non credenziali morte.
4. Il 503 su /send non è l'orario: il business-hours restituisce 403.
5. PROTOCOLLO.md e vos_check.sh NON sono in lukeeterna/venture-os: la sorgente è fluxion-desktop.
6. FB scraping automatizzato, portali, bypass 403/Cloudflare: chiusi per sempre, non riaprire.

## Unità residue (in ordine di dipendenza)
U1 SECOND-BRAIN — revisione+integrazione di tools/second_brain.py (consegna Sol), tre dealer, tre messaggi al numero test. Criterio: se i tre messaggi non sono riconoscibilmente diversi, è un template. CORSIA: MACCHINA.
U2 SIGILLO — il founder dichiara se sono tre o uno. Owner: FOUNDER.
U3 COREUTILS+E2E — brew install coreutils, gnubin in PATH, pipeline scrape->CoVe->PDF fino in fondo. CORSIA: MACCHINA.
U4 RING-9B — reject->abort mai esercitato. CORSIA: MACCHINA.
U5 RPO — registrazione operatore, abbonamento annuale non frazionabile, liste valide 15 giorni. Owner: FOUNDER. Latenza burocratica: avviare appena U2 è verde.
U6 TELEMACO + INGEST v1 — CSV -> data/registry/, incrocio P.IVA, de-lordizzazione TV, SINTESI v5. Owner: FOUNDER poi MACCHINA.
U7 WA-HEARTBEAT — rilevare la sessione morta senza aspettare un invio fallito. Sol poi MACCHINA.
U8 PRIMO CONTATTO REALE — sottomissione RPO + invii. Owner: FOUNDER (GO).
U9 MANDATO FIRMATO — ring #6-7 e #8 su dealer reale. Traguardo 27/08.

## Coda non bloccante
- chiudi-ordinatamente ripuntato su docs/judge/STATE.md (invece di HANDOFF_CURRENT.md)
- env-fix residui: argos-proxy/src/lib/wa-daemon.ts, chaos_db_stress.py, chaos_test.sh, tools/test_ambra_5scenarios.py, tools/test_dossier_hitl_smoke.py
- PII di terzi in albero pubblico (155 occorrenze, 76 numeri, 31 file) = DECISIONE FOUNDER APERTA
- Rotazione numero test founder
- Nota marchio AutoScout24

## Corsie
REPO (Claude Code web, VM cloud, branch vos/<nome> + PR): nessun accesso a daemon/iMac/DB.
MACCHINA (CC locale): runtime, invii, deploy.
Mai in contemporanea sugli stessi file.
