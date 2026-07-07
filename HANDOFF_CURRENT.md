# HANDOFF — S299 (UNITÀ C + D done, verdi) — 2026-07-07 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: coda S298 leggera — (C) provenienza numeri PDF dal template + (D) rimozione blockquote stale STATE.md
- Esito: **C VERDE** · **D VERDE**. Nessun blocker nuovo.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD atteso = commit di chiusura S299 (successivo a `58b0875`)
- committati (file nominati, MAI `git add -A`): `tools/it_market_price.py` · `tools/validate_band.py` ·
  `tools/scripts/pdf_generator_enterprise.py` · `tests/dossiers_s296/ARGOS_DEMO_S296_a_330i_REAL_fallback.pdf` ·
  `STATE.md` · `state/rings.json`
- NON committati (untracked, restore-point Rule 1d): `*.bak-S299-*` (it_market_price/validate_band/pdf_generator/STATE)
- NON committato: `.claude/NEXT_SESSION_PROMPT.md` (timestamp auto SessionStart)
- NON pushato (regola S278: push bloccato finché scrub history secret non fatto).

### UNITÀ C — TEMPLATE BEVE DALLA FONTE (verde)
- Il copy "325 annunci / cap 20 pagine / non esaustivo" era HARDCODED in `pdf_generator_enterprise.py::_create_it_distribution_section`.
- Fix a catena (fonte→template, nessun ricalcolo parallelo):
  1. `it_market_price.py::_load_fixture` ora ritorna anche `meta` (era `(raw, scrape_date)` → `(raw, scrape_date, meta)`).
  2. `get_it_distribution` propaga in `dist`: `n_priced` (fixture meta o `len(pool)` live), `pages_scraped`, `terminated_by_empty`.
  3. `tools/validate_band.py::level_prices_from_pool` aggiornato all'unpack a 3 (era il 2° caller di `_load_fixture`, si era rotto → fixato).
  4. `VehicleData` + mapping `generate_dossier_from_data`: nuovi campi `it_n_priced/it_pages_scraped/it_terminated_by_empty`.
  5. Template: `_sample` costruito dai campi fonte → esaustivo="scrape esaustivo: N annunci IT su P pagine, terminato a pagina vuota".
  6. Doppia etichetta rimossa: riga 1447 `f'Documento richiesto: {cert_note}.'` → `f'{cert_note}.'` (`cert_note` già porta "Documento ottenuto —").
- Rigenerato SOLO `tests/dossiers_s296/ARGOS_DEMO_S296_a_330i_REAL_fallback.pdf`. **Done-C verificato (estratto pypdf, verbatim)**:
  `323` PRESENTE · `325`/`cap 20 pagine`/`non esaustivo` ASSENTI · `scrape esaustivo` PRESENTE ·
  `Documento richiesto: Documento ottenuto` (doppia label) ASSENTE. Riga PDF:
  `>=20 comparabili (scrape esaustivo: 323 annunci IT su 21 pagine, terminato a pagina vuota)`.
- Regressione BM: `python3 tools/tests/test_base_mercato_gate.py` exit 0 (n_priced=323 pages=21 terminated=True, n_by_level={0:2,1:3,2:4,3:20}).
- Rule 1d: backup `.bak-S299-*` per i 3 .py toccati (verificati size>0, fuori /tmp).

### UNITÀ D — BLOCKQUOTE STALE (verde)
- STATE.md righe 20-32 (prosa "S273-cont base-mercato NON affidabile (cap-truncated)") RIMOSSA — contraddiceva la tabella generata (BM=VERIFIED).
- Sostituita con UNA riga: "> Stato gate = tabella generata sotto (`state/refresh.py`). Non scrivere stato a mano in questo file."
- `python3 state/refresh.py S299` exit 0 → 8 anelli invariati, **BM=VERIFIED** confermato. Backup 1d STATE.md pre-edit.

### BLOCKED-ON (invariati, fatti esterni)
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico su WA/HITL.
- Anello 8 (sign_url firmato dal dealer reale) — freeze fisico.
- Parità gate/runtime `/send` `approved_ts` — gated su autonomia-invio.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/handoff (SUPERSEDED)
