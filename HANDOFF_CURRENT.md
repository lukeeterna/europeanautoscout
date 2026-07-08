# HANDOFF — S303 — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: sbloccare pre-req 4a e completare BRIEF_A2 emendato — harvest dealer-URL → profiling (stop 10 ICP) → select seed=42. Zero invii.
- Esito: **UNITÀ A VERDE** (pre-req 4a RISOLTO + harvester `discover_dealers.py`, 45 candidati/3 richieste) + **bug B fixato** (`dealer_profile.fetch` rotto → `_fetch`, selftest 3/3). UNITÀ B (profiling) e C-select NON eseguite: chiusura per context-budget (60%→63%, vincolo #7). commit `f4761b6`.

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `f4761b6` 2026-07-08 17:33 · working-tree dirty (solo file auto-refresh SessionStart, NON miei): `.claude/NEXT_SESSION_PROMPT.md` · `STATE.md` · `state/rings.json`
- commit di questa sessione: `f4761b6` "S303 UNITÀ A: harvester dealer-URL (pre-req 4a risolto) + fix bug fetch dealer_profile" (3 file, +963/−3)
- NON pushato (regola S278: push bloccato finché scrub history secret non fatto).

### FATTO CHIAVE — pre-req 4a RISOLTO (fetch-di-prova reale, 1 richiesta)
- L'oggetto `seller` del `__NEXT_DATA__` AS24 ESPONE l'URL concessionario: `seller.links.infoPage` = `https://www.autoscout24.it/concessionari/<slug>?atype=C`. Anche `seller.id` (dealer_id stabile), `companyName`, `type`, `phones[]`.
- `daily_cap` `autoscout24_it` = **2000** (BRIEF_A2 dice 1000 = SBAGLIATO). BMW X5 ICP → 233 risultati/13 pagine; Porsche Macan → 789/42.
- Bug scoperto: `AutoScoutScraper.fetch()` è rotto (`super().fetch` inesistente post-refactor base→`_fetch`). Il path `--url` di `dealer_profile.py` crashava → fix a `_fetch`. Limiti scraper INVARIATI.

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
| 6-7 | approve HITL dossier -> invio PDF | UNVERIFIED |
| 8 | contract -> sign_url | BLOCKED (freeze esterno) |
| BM | base-mercato IT fidata | VERIFIED |

### GATE A DEALER REALE
[A] liceità canale primo contatto = CONFERMATO LUKE 2026-06-16 · [E] trasparenza AMBRA (Azzurra) = CHIUSO (commit 118343b) · [D] base-mercato fidata = VERIFIED. Residuo bloccante = E2E TEST_FOUNDER verde (1/6-7/9B) + Luke "pienamente soddisfatto".

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
UNITÀ B — profiling: per ogni candidato in `data/pool_icp/_candidates.json` eseguire `python3 tools/dealer_profile.py --url "<info_page>" --out data/pool_icp/<slug>.json`; arbitro filtro = `stock_count` (=numberOfResults); STOP a 10 ICP validi (stock<20 ∧ top_brands⊆premium ∧ no BEV) o guard 80% (1600). PRIMA verificare che la pagina `/concessionari/<slug>` esponga `numberOfResults` nel `__NEXT_DATA__` (path `--url` NON E2E-verificato su pagina dealer reale in S303: solo ast+selftest; `_fetch` provato live).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- UNITÀ C: `tools/select_pilot_dealer.py` NON esiste ancora — da scrivere (ordine stabile per dealer_id, random seed=42 → SELECTED.json, idempotente).
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico WA/HITL. Anello 8 sign_url — freeze fisico.

### BACKLOG (differito, NON prerequisito del primo invio)
- Parità gate/runtime `/send` `approved_ts` (gated su autonomia-invio, STATE.md §3).
- `AutoScoutScraper.fetch()` override morto: pulire/rimuovere (oggi aggirato da `_fetch`, non urgente).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- Il fetch-di-prova mai fatto in S302 era il vero sblocco: bastava 1 richiesta. Fatta → pre-req 4a risolto, harvester scritto, 45 candidati reali in 3 richieste (cap 2000, margine enorme).
- Bug latente su UNITÀ B: `dealer_profile --url` sarebbe crashato al primo uso reale (fetch rotto). Scoperto e fixato PRIMA di sprecare richieste; ma il path `--url` end-to-end su una pagina dealer NON è ancora verificato live (deferito B): rischio residuo = la pagina `/concessionari/<slug>` potrebbe NON esporre `numberOfResults` come la pagina di ricerca. Da verificare al 1° profiling.
- Discovery limitata a `--max-dealers 40` per budget: pool completo (13-14 modelli, guard 1600) si ottiene con `--max-dealers 0`.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (ICP S292: micro <20, TIER A/B, €25-90k, 2018-2023, no BEV) · docs/briefs/BRIEF_A2_piano_scrape_pool_icp.md (correggere cap 1000→2000) · STATE.md §3 (gate dealer reale) · memory/s303_a2_unblocked_harvester_fetch_bug.md
