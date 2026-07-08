# BRIEF A.2 — Piano-scrape POOL dealer ICP (SOLO CARTA — nessuna richiesta parte qui)

> Scritto S301. Autorità dati = codice/git. Questo è un PIANO, non un'esecuzione.
> Esecuzione = sessione dedicata con budget (rate-limited). NON avviare scrape leggendo questo file.

## Obiettivo
Costruire un POOL di dealer candidati e filtrarlo all'ICP, per alimentare UNITÀ B
(`validate_day1.py`) con `dealer_profile.json` REALI. Su disco oggi c'è 1 solo dealer
(RossettoMotors, 28 listing → NON ICP micro-<20): serve un pool fresco.

## ICP (docs/ROADMAP.md S292 — fonte autoritativa, qui solo puntatore)
- Micro-dealer **stock < 20** (soglia dura, dal `stock_count` = `numberOfResults` AS24).
- Tutta Italia. Anni **2018–2023**. Prezzo **€25–90k**. **No BEV**.
- TIER A: Porsche Macan/Cayenne, Range Rover Sport/Velar/Evoque, Audi Q7/Q8, BMW X5, Mercedes GLE/GLC.
- TIER B: Audi A6, BMW Serie 5, Mercedes Classe E, Porsche Panamera.

## Fonte + percorso
- Portale: `autoscout24_it` (`tools/scrapers/config.py`: base `https://www.autoscout24.it`,
  `results_per_page=20`, `max_pages=10`, `rate_limit 4–10s`). Scraper VERIFICATO, IMMUTABILE.
- **Non** esiste oggi un enumeratore di dealer: si arriva al dealer PARTENDO dai listing.
- Due fasi:
  - **FASE 1 — DISCOVERY (harvest dealer dai listing ICP)**: per ciascun modello ICP,
    query nazionale AS24 con filtri anno 2018–2023 e prezzo 25–90k; da ogni card di annuncio
    si raccoglie `seller_name` + URL pagina concessionario (slug `/concessionari/<slug>` o
    equivalente esposto dal listing). Output FASE 1 = set di dealer candidati DISTINTI
    (dedup su URL/slug). NB: il parser attuale (`AutoScoutScraper.parse_listings`) espone
    `seller_name`/`seller_location`; **verificare a runtime** che l'URL/slug del concessionario
    sia presente nel `__NEXT_DATA__` — se assente, è un pre-req da aggiungere al parser (flag
    come dipendenza, NON assumerlo risolto).
  - **FASE 2 — PROFILING (stock reale per candidato)**: per ogni dealer candidato,
    `python3 tools/dealer_profile.py --url "<dealer_url>" --out data/pool_icp/<slug>.json`.
    Il campo `stock_count` (= `numberOfResults` dichiarato da AS24, null-discipline) è
    l'ARBITRO del filtro micro-<20. `top_brands` verifica il mix premium.

## Stima richieste vs cap
- Cap: `daily_request_cap` — il blocco `autoscout24_it` NON lo ridefinisce → **default ereditato
  da `PortalConfig` = **2000** (verificato S302/S303 su config.py:104; leggere a runtime con `stats['daily_cap']`, property)**.
- FASE 1: 13 modelli ICP (9 TIER A + 4 TIER B) × fino a `max_pages=10` = **≤130 richieste**.
  Realistico meno (molte query esauriscono prima di pagina 10 con i filtri anno+prezzo).
- FASE 2: 1 fetch per candidato (`extract_profile` fa una `fetch`) → **N richieste = N candidati**.
  Con ~50–150 candidati distinti attesi → **≤150 richieste**.
- **Totale ≤ ~280 richieste << cap 2000**. Rate 4–10s → runtime ordine ~30–60 min. Margine ampio;
  resta sotto cap anche raddoppiando i modelli.

## Criteri di stop (falsificabili)
1. Per query modello: STOP a pagina vuota o a `max_pages=10` (il minore).
2. DISCOVERY: STOP quando i dealer candidati distinti ≥ **60** (pool sufficiente al primo batch),
   oppure quando tutti i 13 modelli sono esauriti.
3. GLOBALE: STOP se `stats['daily_count']` (property) raggiunge **80% del cap (1600)** (guard, mai forzare oltre).
4. PROFILING: salta candidato se `fetch` ≠ 200 o `stock_count` null (dealer non profilabile → log, non ritentare in loop).

## Output atteso
- `data/pool_icp/*.json` = N `dealer_profile.json` (uno per candidato profilato).
- Filtro ICP applicato a valle (deterministico, su campi del profilo):
  `stock_count < 20` AND `top_brands ⊆ {Porsche,Range Rover,Land Rover,Audi,BMW,Mercedes}` AND (no BEV).
- Risultato = **lista dealer ICP** (attesi pochi: micro-<20 è raro sul totale) pronti come input a
  `validate_day1.py` (profilo → messaggio → gate).

## Pre-requisiti / rischi da chiudere PRIMA dell'esecuzione (flag, non assunti)
- [ ] URL/slug concessionario presente nel `__NEXT_DATA__` del listing (verificare; se no, estendere parser).
- [ ] Filtri anno/prezzo supportati nella query AS24 dallo scraper attuale (verificare `build query`/params).
- [x] `daily_request_cap` effettivo del portale IT = **2000** (property `stats['daily_cap']`, verificato S302/S303).
- [ ] Scrivere `data/pool_icp/` (mkdir) e gitignore se i JSON non vanno versionati.

## NON in questo brief (defer)
- Selezione del veicolo-hook per il Day-1 (UNITÀ B a valle, con profilo reale).
- Scelta del dealer specifico da contattare (decisione Luke / HITL sotto soglia 10).
