# HANDOFF — S295 — 2026-07-04 16:00 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: cablare validate_band.py (gate-soglia-N deterministico) + test sintetico, poi re-scrape pool IT BMW Serie3 2021 e instradare 330i nel gate. Chiude Gate [3].
- Esito: Unità A DONE e committata (gate + suite 3/3 verde). Unità B/C NON completate — chiusura forzata da context budget (vincolo #7 @60%) col re-scrape ancora in corso.

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 90919c7 (auto-close hook) · sopra d586f03 (Unità A) · working-tree dirty: .claude/NEXT_SESSION_PROMPT.md
- commit di questa sessione: d586f03 "S295: validate_band.py — gate-soglia-N deterministico banda prezzo IT (Unità A)"

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (da STATE.md a session-start, verbatim)
1 UNVERIFIED · 2 VERIFIED · 9A VERIFIED · 9B UNVERIFIED · 5 VERIFIED · 6-7 UNVERIFIED · 8 BLOCKED
(nessun anello E2E toccato in questa sessione)

### GATE A DEALER REALE
[A] base-mercato BMW Serie3 = pool geo-puro verificato S293 (332 IT); leveling 330i ANCORA da chiudere via gate
[E] E2E 6-7 = UNVERIFIED (non toccato)
[D] Day-1 reale = BLOCKED (invariato: gate qualitativo Luke + E2E verde)

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
Unità B: `python3 -m tools.scripts.s273cont4_exhaustive_geo` (NO `timeout`, non esiste su Big Sur) → verifica falsificabile `n_priced ≈ 332`. Se ~0 = fix S294 fallito, STOP. Se ok, fixture in `tests/fixtures/it_dist_bmw_serie3_2021_s273cont4.json`.

### UNITÀ C (dopo B, falsificabile)
`from tools.validate_band import gate_it_band` →
`gate_it_band("BMW","Serie 3",2021,km,"petrol",target_variant="330i",fixture_path=<fixture>)`
→ incolla `n_by_level` (L0-L3) + `verdict` + `band_low/band_high` + `fallback_declared`. La banda esce SOLO dal gate.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Nessuno tecnico. Unità B/C interrotte da context budget, NON da blocco esterno: riprendibili subito in sessione fresca.
- NOTA: un processo scrape (PID 6291) era ancora vivo alla chiusura; il RAW pool viene persistito presto (`tests/fixtures/..._RAW.json`). Verificare/ripulire a inizio prossima sessione prima di ri-lanciare.

### BACKLOG (differito, NON prerequisito del primo invio)
- Nessun nuovo item aperto in S295.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- BLOCCO-DISCORDANZA PASS: fix S294 (4955401) committato pulito; `raw_to_listing` chiama il parser canonico `_next_data_item_to_listing` (autoscout_scraper.py:799). Il re-scrape gira codice corretto.
- Unità A è il deliverable strutturale ("il gate NON si salta") ed è VERDE+committata; Unità B/C sono la verifica E2E del fix e "possono aspettare" (da mandato).
- soglia_n=8 NON inventata: importata da it_market_price.MIN_N_DEFAULT (ratificata Luke S265). Gate mappa L0-L2=config esatta, L3=fallback adiacente (fallback_declared).
- Rule 1d rispettata: validate_band.py = path nuovo additivo, nessuna sovrascrittura di source-of-truth; HANDOFF sovrascritto con backup verificato in /tmp.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 segmento/geo/anni) · tools/it_market_price.py (leveling+_decide) · tools/validate_band.py (gate banda) · tools/scripts/s273cont4_exhaustive_geo.py (re-scrape geo-puro)
