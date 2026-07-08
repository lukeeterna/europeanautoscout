# HANDOFF — S305 — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: fix estrattore brand — derivare il brand DALL'ITEM (non dal query-param) così che dealer_profile.py produca top_brands non-null sulle dealer-page. SOLO questo fix + verifica.
- Esito: **FIX VERDE + VERIFICATO**. `_json_ld_to_listing`/`_next_data_item_to_listing`: quando `make` query è vuoto derivano il brand dall'item (JSON-LD brand/manufacturer · NEXT_DATA vehicle.make/makeId · ultimo=title match ESATTO su lista chiusa MAKE_SLUG; makeId numerico scartato; nessuna fonte → brand=""). Selftest esteso a/b/c verde. Regressione BM INVARIATA (n_priced=323, n_by_level {0:2,1:3,2:4,3:20}). E2E car-lux-srl → top_brands NON-null [Audi, Mercedes-Benz, smart, Porsche, Alfa Romeo, Fiat, DS Automobiles, Lamborghini]. 1 richiesta AS24 consumata.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `682b034` 2026-07-08 18:01 · working-tree dirty (SOLO file auto-refresh SessionStart, NON miei): `.claude/NEXT_SESSION_PROMPT.md` · `STATE.md` · `state/rings.json`
- commit di questa sessione: `682b034` (autoscout_scraper deriva brand dall'item + tools/tests/test_make_derivation.py). NON pushato (regola S278).

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
Ri-lanciare UNITÀ B (profiling 45 candidati → STOP a 10 ICP) in sessione fresca, ora che l'estrattore deriva brand per-item. Fatto esterno di verifica = per ≥1 candidato profilato `top_brands` intercetta un brand TIER-A/B → filtro ICP operativo (>0 ICP). Poi C-SELECT (seed=42). Zero invii.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- nessuno (blocco S304 estrattore RISOLTO S305).

### BACKLOG (differito, NON prerequisito del primo invio)
- `top_models`/`example_vehicles` null sul dealer-page: il `model` è iniettato da query (make="" → model="" sulla dealer-page), non derivato dall'item. Fuori scope estrattore-brand (mandato nuovo se serve al filtro ICP; il tier ICP dipende dal brand, non dal model → probabilmente NON bloccante).
- `name`/`location` profilo null: seller_name non popolato dai listing propri sulla dealer-page.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Fix chirurgico a 2 punti nominati (S304 li aveva pre-identificati) + helper `_canonical_make`/`_make_from_title`. Nessun allargamento: HTML-card fallback (:1069/:1190) NON toccato — fuori dai 2 punti del mandato (CHECKPOINT rispettato).
- Disciplina anti-invenzione preservata: campi strutturati dell'item = dato reale (anche brand non-ICP come "smart"/"DS Automobiles" compaiono, corretti); solo il title-parse è ristretto alla lista chiusa MAKE_SLUG con match word-boundary (no fuzzy). makeId numerico scartato per non inquinare.
- Regressione BM verificata INVARIATA per costruzione (il gate legge una fixture statica, non ri-scrape) e confermata a runtime: n_by_level {0:2,1:3,2:4,3:20}.
- Backup Rule 1d: `~/.argos-backups/autoscout_scraper.py.bak-S305` (size 60009, mtime pre-azione).
- Nessun invio, nessun Day-1 generato. 1 sola richiesta AS24 (E2E car-lux-srl).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/briefs/BRIEF_A2_piano_scrape_pool_icp.md · docs/ROADMAP.md · data/pool_icp/_candidates.json (45 candidati) · tools/dealer_profile.py · tools/tests/test_make_derivation.py
