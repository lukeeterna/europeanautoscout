# HANDOFF — recon-leve-day1-FASE0 — 2026-07-10 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: READ-ONLY (nessun file creato/modificato; solo letture disco + 1 decisione di scope a Luke)
- Mandato: ricognizione leve Day-1 su ~20 dealer ICP (solo GET pubblici, ZERO contatto) → dati per chiusura messaggio Day-1.
- Esito: STOP a FASE 0 per BLOCCO-DISCORDANZA su 2 premesse (falsificate dal disco) + budget context. Scope ratificato da Luke: "7 ICP + scrape nuova". UNITÀ 1/2 NON iniziate (nessuno stato PARTIAL).

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD 15897f0 2026-07-10 · working-tree dirty (NON miei: STATE.md + state/rings.json + .claude/NEXT_SESSION_PROMPT.md = auto-hook; data/pool_icp/_backup_reapply_20260708T171250Z/ = artefatto pre-esistente all'avvio)
- commit di questa sessione: nessuno (READ-ONLY: niente da committare)
- PUSH STATUS VERBATIM: `git rev-list --count origin/s210/audit-master-plan..HEAD` = 224 · `## s210/audit-master-plan...origin/s210/audit-master-plan [ahead 224]` · push NON eseguito (VIETATO S278)

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/chat (SUPERSEDED)

### STATO E2E (OUTPUT VERBATIM da `state/rings.json` last_status — non re-narrare)
| # | last_status |
|---|-------------|
| 1 | UNVERIFIED |
| 2 | PASS |
| 9A | PASS |
| 9B | UNVERIFIED |
| 5 | PASS |
| 6-7 | UNVERIFIED |
| 8 | BLOCKED |
| BM | PASS |

### GATE A DEALER REALE (OUTPUT VERBATIM — non re-narrare)
[A] = APERTO/BLOCKED-ON — E2E TEST_FOUNDER mai eseguito (anelli 1/6-7/9B UNVERIFIED); glue Day-1→queue_outbound(phase='DAY1') inesistente · [E] trasparenza deployata = CHIUSO ('Azzurra', 118343b) · [D] base-mercato = VERIFIED

### PROSSIMO PASSO (singolo, falsificabile, fatto esterno)
UNITÀ 1 recon-leve su 7 dealer ICP-VALID (scope Luke): scrivere estensione estrazione per-annuncio (km + timestamp + testo-segnali-fiducia + canali-contatto — oggi assenti nel parser) → scrape fresca dei 7 a rate-limit invariato → 7 JSON in data/recon/dealer_levers/{seller_id}.json + conteggio copertura campi. Fatto terminale = 7 JSON su disco con copertura dichiarata (fetch falliti nominati, MAI riempiti a mano).

### BLOCKED-ON (fatti esterni irraggiungibili in sessione)
- Gate [A]: E2E TEST_FOUNDER 393314928901 verde + Luke "pienamente soddisfatto" (anelli 1/6-7/9B UNVERIFIED). [invariato, fuori scope recon]
- Anello 8: sign_url firmato dal dealer reale.
- OK esplicito di Luke sul testo Day-1 v4 prima di qualunque invio.

### BACKLOG (differito, NON prerequisito del primo invio)
- Portare il pool ICP da 7 a 20 richiede NUOVA discovery (discover_dealers.py) = più richieste portale (aumento aggressività di rete che il mandato recon VIETA). Deferito: Luke ha scelto "7 ICP + scrape nuova", non l'espansione a 20.
- `/send` non impone `approved_ts` (garanzia HITL nel caller) — gated su autonomia-invio.
- 6-7 E2E su iMac (gate HITL fastapi + PDF a TEST_FOUNDER 393314928901).

### NOTE PER IL GIUDICE (osservazioni da segnalare a Luke)
- **BLOCCO-DISCORDANZA #1 (numerosità)**: la premessa "20 dealer dall'indice/pool esistente" è FALSA sul disco. `data/pool_icp/_profiling_run.json` → `icp_valid: 7`, `stopped_reason: CANDIDATES_EXHAUSTED` (45 candidati profilati, 7 ICP-VALID). SELECTED = 5. Non esistono 20 dealer nel pool. → Luke ha ratificato scope "7 ICP + scrape nuova".
- **BLOCCO-DISCORDANZA #2 (dato per-annuncio assente)**: anche per i 7 esistenti il dettaglio che il mandato vuole (annunci con modello/anno/km/prezzo + timestamp + segnali-fiducia + contatti) NON è persistito. I `dealer_*.json` hanno `example_vehicles: []`, `top_models: null`. `tools/dealer_profile.py:aggregate_profile` estrae solo make/model/year/price (max 2 example) e NON estrae km-per-annuncio / timestamp / testo-annuncio / canali-contatto. → UNITÀ 1 richiede CODICE NUOVO (dichiarato PRIMA di scriverlo, FASE 0.3) + scrape fresca.
- **I 7 ICP-VALID (unico universo disponibile)** — tutti stock ≤20 ✓, tutti ≥1 tier-hit ✓ · location=null in tutti (NON persistita → "geografia Italia intera" NON verificabile dal pool; i nomi suggeriscono Treviso/Trento/Latina ma è inferenza, non dato):
  1. 13099 Visauto Treviso Srl — stock 12 — Audi/Porsche/BMW  [SELECTED]
  2. 13287560 Bernabei Automobili — stock 10 — Porsche/BMW  [SELECTED]
  3. 29628436 Eurocar Tech/Centro Porsche Trento — stock 12 — Porsche  [non-SELECTED]
  4. 30777412 Auto Postumia — stock 13 — Mercedes/Audi/Porsche/BMW  [SELECTED]
  5. 34208 Scotti Srl — stock 15 — Porsche/Mercedes/BMW/Audi  [SELECTED]
  6. 43994037 Centro Porsche Latina — stock 11 — Porsche/BMW/Audi  [non-SELECTED]
  7. 50677798 Auto Giannini — stock 13 — Porsche/BMW/Audi  [SELECTED]
- **Chiusura per budget**: context 55% al momento della decisione (vincolo #7 chiude a 60%; CHECKPOINT mandato: >60% → chiudi UNITÀ 1 da sola). UNITÀ 1 = codice-nuovo + 7 scrape + copertura = non compibile sotto soglia senza sforare o rischiare implementazione non verificata (#10/#1). Chiuso al confine di decisione, non a metà scrape → nessun PARTIAL.

### INVENTARIO RIUSO (per UNITÀ 1 prossima sessione — paths verbatim)
- Scrape pagina-dealer: `tools/dealer_profile.py` → `extract_profile(url)` riusa `tools/scrapers/autoscout_scraper.py:AutoScoutScraper._fetch(url)` + `parse_listings` + `get_total_pages`. Rate-limit interno di `_fetch()` IMMUTABILE (nessun aumento aggressività).
- Accesso bande prezzo: `tools/it_market_price.py` → `get_it_distribution(make, model, year, km, target_variant=..., fixture_path=...)`. Percentili p25/p75 ratificati (banda), gate composto no_verdict.
- Pool ICP: `data/pool_icp/` (SELECTED.json · dealer_*.json · _profiling_run.json · _candidates.json).
- CODICE NUOVO da scrivere (dichiarato): estensione estrazione per-annuncio (km + timestamp/data-pubblicazione DOVE il portale lo espone [copertura da MISURARE] + testo-annuncio per match segnali-fiducia lista-chiusa + canali contatto) — il `Listing`/`parse_listings` attuale NON porta timestamp né testo-descrizione né trust-signals.

### DOVE STA LA STRATEGIA (puntatori, non ri-sintetizzare)
docs/ROADMAP.md (S292 + ORIZZONTI POST-PILOTA) · docs/briefs/ · .claude/rules/communication.md · tools/dealer_profile.py · tools/it_market_price.py · data/pool_icp/_profiling_run.json · STATE.md §3
