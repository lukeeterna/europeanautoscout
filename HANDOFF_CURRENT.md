# HANDOFF — S300 (UNITÀ A.1 verde · A.2/B bloccati su input Luke) — 2026-07-07 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: capability Day-1 personalizzato — (A) dealer_profile da scrape pubblico → (B) generatore+gate anti-invenzione → (C) E2E TEST_FOUNDER.
- Esito: **UNITÀ A.1 VERDE** (estrattore deterministico + selftest 3/3 PASS). A.2 e B fermati su DUE input esterni di Luke non forniti (URL dealer + testo esatto scheletro ratificato). C non iniziata (per mandato defer a sessione fresca).

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `44c877e` 2026-07-07 · working-tree dirty (solo file auto-refresh SessionStart)
- commit di questa sessione: `44c877e` "session-close: UNITÀ A.1 — estrattore profilo dealer AS24 deterministico (selftest 3/3 PASS)"
- dirty NON mio (auto-refresh SessionStart, non committato): `STATE.md` · `state/rings.json` · `.claude/NEXT_SESSION_PROMPT.md`
- NON pushato (regola S278: push bloccato finché scrub history secret non fatto).

### UNITÀ A.1 — ESTRATTORE PROFILO DEALER (verde)
- `tools/dealer_profile.py` (nuovo, 204 righe). Due livelli:
  - `aggregate_profile(listings, declared_total)` — FUNZIONE PURA testabile, dove vive la disciplina anti-invenzione.
  - `extract_profile(url)` — glue su `AutoScoutScraper.fetch + get_total_pages + parse_listings` (scraper VERIFICATO, non reimplementato). Limiti scraper IMMUTABILI non toccati.
- Regola ferrea implementata: campo assente = `null`, MAI stimato.
  - `stock_count` = SOLO `numberOfResults` dichiarato da AS24; `len(listings)` di una pagina = floor parziale → NON usato come stima; assente → null.
  - `top_segment` = `null` (AS24 Listing non espone campo segmento → nessuna fonte, no euristica). `top_models` porta il fatto presente.
  - `example_vehicles` = solo annunci con marca+modello+anno+prezzo TUTTI presenti (max 2).
- Prova (grezzo): `python3 tools/dealer_profile.py --selftest` → `SELFTEST PASS (3 casi: aggregazione, null-discipline, no-stima stock_count)`.
- CLI: `--url` (live) · `--html-file --country` (offline) · `--out` · `--selftest`.
- Distinzione da `tools/profile_dealers_s106.py` (che STIMA archetipo/premium_pct): qui NESSUNA stima — è il punto.

### STATO E2E (da STATE.md, verbatim — non re-narrare)
| # | Anello | Stato |
|---|--------|-------|
| 1 | invio Day1 WA | UNVERIFIED |
| 2 | classifier intent (AMBRA) | VERIFIED |
| 9A | approve -> send | VERIFIED |
| 9B | reject -> abort | UNVERIFIED |
| 5 | generazione dossier PDF | VERIFIED |
| 6-7 | approve HITL dossier -> invio PDF | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (freeze esterno) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE (da STATE.md §3)
- [A] liceità canale primo contatto = CONFERMATO LUKE 2026-06-16 (non più bloccante)
- [E] trasparenza AMBRA deployata = CHIUSO (commit 118343b, ARGOS_ASSISTANT='Azzurra')
- [D] base-mercato fidata = VERIFIED (BM smoke PASS)
- Residuo bloccante invio reale = E2E TEST_FOUNDER verde (anelli 1/6-7/9B UNVERIFIED) + Luke "pienamente soddisfatto".

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Luke fornisce i DUE input mancanti → poi A.2 (`python3 tools/dealer_profile.py --url <URL> --out <profilo>.json`) + costruzione UNITÀ B (generatore + `validate_day1.py`).
1. **URL AS24 pubblico del dealer** su cui girare A.2 (Done-A = JSON profilo verbatim + path).
2. **Testo esatto dello scheletro ratificato** per B (claim fissi: leva anti-frode "circa 3x, fonte commerciale"; opt-out "no grazie"; slot {dealer_name},{stock_hint},{vehicle_hook}). NON inventabile da CC senza violare il gate anti-invenzione stesso.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Input Luke: URL dealer + testo scheletro ratificato (sopra).
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico su WA/HITL (UNITÀ C, defer a sessione fresca per mandato).
- Anello 8 (sign_url firmato dal dealer reale) — freeze fisico.

### BACKLOG (differito, NON prerequisito del primo invio)
- Parità gate/runtime `/send` `approved_ts` (gated su autonomia-invio, STATE.md §3).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Il generatore Day-1 ESISTENTE (`.claude/skills/human-first-outreach/scripts/batch_generator.py::generate_day1_message` + `get_dealer_stock_from_db` fallback "assume stock generico {total:20,BMW:4...}") **INVENTA**: scrive "Ho visto il suo stock, tratta BMW e premium" da mappa archetipo, non da dati reali. È esattamente l'anti-pattern che UNITÀ B deve rendere impossibile. Da NON riusare per B; B parte da `aggregate_profile` (campi verificati) + gate di forma.
- `tools/profile_dealers_s106.py` NON riusabile per A: stima archetipo/premium_pct (opposto della regola A).
- `tools/validate_band.py` e altri 4 file usano pattern `validate_*` → riferimento di forma per `validate_day1.py` (UNITÀ B.3).
- FASE 0 reality-check tutta verde: HEAD atteso, wa_status=connected (0/20), limiti scraper presenti+intatti (rate_limit_min/max_s, daily_request_cap=1000/2000, max_workers=3).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
STATE.md §3 (gate dealer reale) · docs/ROADMAP.md · .claude/rules/communication.md (CRED-SEQUENCE-001 / NO-OFFER-DAY1-001: prezzo NON nel Day-1) · MEMORY.md (feedback_cold_message_honest_as_dossier, s4_day1_vehicle_first_compositore)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/handoff (SUPERSEDED)
