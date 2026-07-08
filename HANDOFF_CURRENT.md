# HANDOFF — S306 — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: BRIEF_A2 UNITÀ B (profiling 45 candidati → STOP a 10 ICP) + UNITÀ C-SELECT (seed=42). Zero messaggi, zero invii, zero push.
- Esito: **B+C VERDI**. 45/45 profilati, **7 ICP-validi** (candidati ESAURITI prima di 10 — nel pool esistono solo 7 micro-dealer <20 con brand TIER A/B). 50 richieste totali « guard 1600. C-SELECT riproducibile 2× → **Centro Porsche Latina** (seller_id 43994037). Nessun invio, nessun push.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `e531964` 2026-07-08 · working-tree dirty SOLO file NON miei (`.claude/NEXT_SESSION_PROMPT.md` auto-refresh, `.claude/scheduled_tasks.lock` transiente)
- commit di questa sessione: `e531964` (tools/profile_pool_icp.py + tools/select_pilot_dealer.py + data/pool_icp/*.json, 11 file). **NON pushato** (regola S278). Pre-commit PASS (nessun secret).

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
| 8 | contract -> sign_url | BLOCKED (freeze esterno) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE
[A] liceità canale primo contatto = CONFERMATO LUKE 2026-06-16 · [E] trasparenza AMBRA = CHIUSO (118343b) · [D] base-mercato = VERIFIED. Residuo bloccante = E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto".

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Generare il dossier CoVe sul dealer selezionato (Centro Porsche Latina, seller_id 43994037, data/pool_icp/SELECTED.json) — fatto esterno di verifica = PDF dossier prodotto su disco con ≥1 veicolo TIER-A/B del suo stock. Nessun invio (resta gated su E2E TEST_FOUNDER + Luke soddisfatto).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- nessuno per B/C (chiuse). Invio a dealer reale resta gated su E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto".

### BACKLOG (differito, NON prerequisito del primo invio)
- `name`/`location`/`top_models`/`example_vehicles` NULL su tutti i 7 profili ICP: sulla dealer-page i listing propri non popolano seller_name/location e il model è iniettato da query (make/model="" → vuoti). Fuori scope del filtro ICP (che dipende da stock_count + brand, entrambi presenti). Se serve località/veicoli-esempio per il dossier → mandato estrattore separato.
- BEV non decidibile a livello dealer-profile (nessun campo fuel esposto): esclusione BEV gestita a discovery (fuel D,G) + rinviata a vehicle-selection. NON inventato.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- **STOP a 10 non raggiunto per realtà di mercato, non per bug**: dei 45 candidati solo 7 sono micro-dealer <20 con brand TIER A/B. Gli altri 38 hanno stock ≥20 (dealer grandi: 100/257/288...) — visibili nel log `_profiling_run.json`. stopped_reason=CANDIDATES_EXHAUSTED.
- **Arbitro filtro = numberOfResults** (mai len()): stock_count viene da `_last_declared_results` del __NEXT_DATA__. Disciplina anti-invenzione: campo assente = null → il vincolo non è soddisfatto (mai stimato).
- **Limiti scraper IMMUTABILI onorati**: istanza scraper CONDIVISA tra candidati → rate-limit interno reale (4-10s config AS24) + burst-pause 31-38s ogni 5 richieste + 1 retry HTTP 504 gestito. `daily_request_cap` effettivo=2000 verificato (il 1000 in config.py è di leboncoin_fr, non AS24).
- **C-SELECT riproducibile per costruzione**: ordine stabile per seller_id + `random.Random(42).choice`. 2 run identiche verificate a runtime (stesso seller_id 43994037).
- **CONFERMA no-push**: branch ahead 198 di origin, nessun push eseguito. History del branch contiene ancora secret (S278) → push resta VIETATO fino a scrub + rotazione token.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/briefs/BRIEF_A2_piano_scrape_pool_icp.md · docs/ROADMAP.md · data/pool_icp/SELECTED.json (dealer scelto) · data/pool_icp/_profiling_run.json (shortlist 7 + contatore) · data/pool_icp/dealer_*.json (7 profili ICP) · tools/profile_pool_icp.py · tools/select_pilot_dealer.py
