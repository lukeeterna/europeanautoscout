# HANDOFF — S4-OPS sessione 3 — riconciliazione DB dealer (VALUTA-poi-BUILD)

**DB DEALER = DISGIUNTI (decisione a monte necessaria) — gate NON dà via libera a FASE 2**

> 0 dealer in comune tra commerciale e social. Non è un problema di plumbing: i due rami
> hanno profilato negozi DIVERSI. La join non va costruita finché non si decide a monte
> COME le due popolazioni si incontrano (scelta di discovery, non di riconciliazione DB).

---

## FASE 1 — VALUTA (read-only, nessuna modifica)

### Punto 1 — store, tabelle, PK (sono TRE, non due)

| Store | File | Tabella dealer | PK | N dealer | Ruolo |
|---|---|---|---|---|---|
| Commerciale S4 | `data/dealers.db` | `dealers` | `dealer_id TEXT` | **1** | gap/observations/profiles (AS24) |
| Social + CRM | `dealer_network.sqlite` | `dealers` | `dealer_id TEXT` | **18** | anagrafica + `dealer_operational_profile` (FB/IG) |
| CRM lead | `data/db/dealer_network.duckdb` | `dealer_leads` | `id INTEGER` | **1** | 1 sola riga MOCK di test (S26) |

Tabelle collegate (PK):
- `data/dealers.db`: `dealer_profiles(dealer_id)`, `dealer_gaps(dealer_id)`, `vehicle_observations(dealer_id, vehicle_key)`.
- `dealer_network.sqlite`: `dealer_operational_profile(dealer_id)`, `operational_anchors`, `market_listings`...

### Punto 2 — la chiave-dealer è la STESSA tra i DB? → NO, identificatori DIVERSI

5 chiavi-esempio per DB:

| `data/dealers.db` (slug-AS24) | `dealer_network.sqlite` (social_id) |
|---|---|
| `rossettomotors-srl` | `stile_car_fg` |
| *(unico dealer presente)* | `2f_motors_cs` |
| | `gp_cars_ta` |
| | `samy_auto_cs` |
| | `auto_carfora_ce` |

Schema chiave diverso: commerciale = slug-URL AS24 (`<ragsoc>-srl`); social = `<nome>_<provincia>` o
`<NOME>_AUTO_001`. Non confrontabili come stringa.

### Punto 3 — OVERLAP? → ZERO

Criterio di match testato: **nome** (`name LIKE '%ossetto%'`) e **sito** (`website LIKE`).
- `rossettomotors-srl` (l'unico dealer commerciale) **NON** è in `dealer_network.sqlite`: 0 match su nome/sito.
- Nessuno dei 18 social (`stile_car`, `gp_cars`, `2f_motors`...) compare in `data/dealers.db`.
- Il lead DuckDB è `TEST DEALER - Centro BMW Premium` (Napoli, id 300) — mock, disgiunto da entrambi.

**Dealer in comune: 0** (intersezione vuota anche al massimo teorico: 1 commerciale × 18 social).

## Verdetto gate: **DISGIUNTI**

Le tre popolazioni profilano negozi diversi:
- ramo **commerciale S4** → 1 solo dealer profilato via AS24 (`rossettomotors-srl`): ha gap
  premium-tedesco 10/28, 28 observations PRESENT, brand BMW/Volvo/VW;
- ramo **social** → 18 dealer del CRM originario, di cui 5 con profilo FB/IG popolato;
- non si sono mai incrociati sullo stesso negozio reale.

Per mandato (gate): **STOP — NON costruire join.** FASE 2 NON eseguita. Nessun DB modificato,
nessun backup necessario (read-only). Nessuna tabella-ponte: con 0 match certi sarebbe una mappa vuota.

## Cosa serve a monte (decisione di Luke, non plumbing)

La fonte unica Day-1 è impossibile finché i due rami non puntano agli STESSI dealer. Due strade
(scelta di scope, non tecnica):
- **(A)** girare il profiling commerciale AS24 sui 18 dealer del social → riempie `data/dealers.db`
  con le stesse chiavi-negozio, e a quel punto serve una mappa slug-AS24 ↔ social_id sui match certi;
- **(B)** girare i collector social sui dealer commerciali man mano che il ramo AS24 ne profila di nuovi.

In entrambi i casi la chiave d'incontro reale è **nome+sito** o **nome+telefono** (gli unici campi
condivisibili). Ma è una decisione di discovery: quali dealer sono il bersaglio comune.

## Garanzie
- **0 colonne PII** lette/scritte (solo conteggi, chiavi, nomi-negozio e categorie già pubbliche).
- Read-only integrale: nessun `Write`/`Edit`/`>` su DB. Solo `SELECT`/`.schema`/`DESCRIBE`.
- Additivo: CoVe e ramo scraper non toccati.
- Idempotenza FASE 2: N/A (non eseguita).

## File nominati (solo questo report; commit locale, no push)
- `HANDOFF_CURRENT.md`
