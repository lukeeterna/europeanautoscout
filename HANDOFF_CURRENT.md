# HANDOFF — S304 — 2026-07-08 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: WRITE-CODE
- Mandato: BRIEF_A2 UNITÀ B (profiling 45 candidati, STOP a 10 ICP) + C-SELECT (seed=42). Zero invii.
- Esito: **UNITÀ B NON eseguita — STOP a B0 per blocco strutturale**. B0 gate `numberOfResults` = SÌ (`stock_count=100` sul 1° candidato), ma scoperto blocco: l'estrattore inietta `make` dalla QUERY, non dall'item → `top_brands`/`top_models` = null su OGNI dealer-page → filtro ICP `brand TIER A/B` inoperabile. Profilare i 45 = 0 ICP garantiti (avvitamento). Fix = adattamento parsing = mandato nuovo (B0 lo pre-autorizza). Fatti: FASE 0 verde, brief corretto, path `--url` riparato (era rotto in S303). 1 richiesta AS24 consumata (B0).

### VERITÀ GIT
- branch `s210/audit-master-plan` · HEAD `9ddce24` 2026-07-08 17:47 · working-tree dirty (SOLO file auto-refresh SessionStart, NON miei): `.claude/NEXT_SESSION_PROMPT.md` · `STATE.md` · `state/rings.json`
- commit di questa sessione: `6fac46d` (BRIEF_A2 fix cap 1000→2000 + get_stats→property stats) · `9ddce24` (dealer_profile fix import path `--url`, selftest 3/3). NON pushati (regola S278).

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
NUOVO MANDATO estrattore: in `_json_ld_to_listing` (autoscout_scraper.py:720 `make=make`) e `_next_data_to_listing` (:905 `make=make`), quando il `make` param è vuoto (dealer-page), derivare il brand DALL'ITEM: JSON-LD `item.get("brand"/"manufacturer")` o `name`; `__NEXT_DATA__` `vehicle.get("make"/"makeId")`. Fatto esterno di verifica = `python3 tools/dealer_profile.py --url "<info_page 1° candidato>"` ritorna `top_brands` NON-null. Solo dopo, ri-lanciare UNITÀ B.

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- UNITÀ B/C bloccate finché estrattore non deriva brand per-item (mandato nuovo sopra). Non re-tentabile a codice invariato: darebbe 0 ICP.

### BACKLOG (differito, NON prerequisito del primo invio)
- `name`/`location` profilo null sul dealer-page (seller_name non popolato dai listing propri) — verificare se serve al filtro ICP o solo cosmetico.

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- B0 ha fatto il suo lavoro: ha intercettato PRIMA di bruciare 45 richieste un blocco che il selftest offline S303 non poteva vedere (make iniettato da query, non da item — root cause strutturale, Rule #11).
- `stock_count` (via `numberOfResults`) e `no BEV` (via fuel_type per-item) FUNZIONANO; solo il criterio brand è rotto. Il fix è chirurgico (2 punti nominati sopra), non riscrittura.
- Ogni candidato in `_candidates.json` porta già `first_seen_model` (es. "Porsche:Macan") = garanzia che stocka ≥1 modello premium: valutare se usarlo come seed-brand invece/oltre al parse-page.
- Nessun invio, nessun Day-1 generato. 1 sola richiesta AS24 (B0).

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/briefs/BRIEF_A2_piano_scrape_pool_icp.md (corretto S304) · docs/ROADMAP.md · data/pool_icp/_candidates.json (45 candidati, 3 richieste S303)
