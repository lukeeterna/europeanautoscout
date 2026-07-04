# S296 · UNITÀ A DONE (verde) → resume UNITÀ B (3 PDF di prova)

## STATO
- **UNITÀ A = COMPLETA E VERDE, committata.** 13 edit applicati (12 sul generatore + 1 re-wire sorgente banda).
- **UNITÀ B = da fare a sessione fresca** (chiusa per soglia context, vincolo #6 anti-PARTIAL).

## COSA È STATO FATTO (verificato, non narrato)
File toccati (backup 1d in `*.bak-s296`):
- `tools/it_market_price.py` — `get_it_distribution` ora emette **`fallback_declared`** in OGNI ramo di ritorno (n==0 e n>=1): `bool((relaxation_level==3) and not no_verdict)`. È la banda "DALLA FONTE".
- `tools/scripts/pdf_generator_enterprise.py` — 12 edit: VehicleData +3 campi (`country_code`,`fraud_doc_obtained`,`fallback_declared`); `_fraud_source_certainty` CLASSE-REGIME; note banda con provenienza (`_prov`); NO_VERDICT esplicito; footer×2 → "Azzurra — assistente di Luca Ferretti"; riga verifica km "Coerenza dati/VIN" + "Verifica km alla fonte" (mai "Superato"); status ambra; `_create_fraud_leva_section`; assembly popola i 3 campi da `it_dist`/`best`.

## 2 ADATTAMENTI RATIFICATI (mandato↔disco riconciliati)
1. **Banda**: `gate_it_band` (validate_band.py) NON è nel runtime (scrape indipendente). La fonte reale che alimenta il PDF è `get_it_distribution` → emesso lì `fallback_declared` con semantica identica al gate (L0-L2 esatto, L3 adiacente). PDF lo LEGGE (`vehicle.fallback_declared`), non ricalcola.
2. **Certezza CLASSE-REGIME (C-GATE-FONTE-001=(b))**: `_fraud_source_certainty` mappa country_code→classe INTERNAMENTE ma l'OUTPUT nel PDF mostra SOLO autonomo/su-richiesta/contrattuale/commerciale + grado A/B/C. MAI RDW/Car-Pass/Histovec/TÜV/paese. Verificato via grep anti-leak sul diff = 0 match.

## GATE PASSATI
- `python3 -c "import ast; ast.parse(...)"` entrambi = PASS · smoke import = OK.
- grep anti-leak sulle righe `+` del diff = zero literal paese/registro.

## UNITÀ B — DA FARE (artifact-layer, done = 3 PDF apribili su disco)
Pattern: `tools/scripts/build_s268_dossier.py` (costruisce `_it_distribution` inline / chiama `get_it_distribution(fixture_path=...)` e invoca il generatore). Generare 3 PDF:
- **(a) 330i REALE fallback dichiarato** — fixture geo-pura Serie3 (memory `s293_scrape_esaustivo_geopuro_serie3.md`, fixture cont4). Atteso: banda con "banda su configurazione adiacente, campione trim N=<x>" + certezza documento (classe-regime).
- **(b) sintetico NO_VERDICT** — `_it_distribution` con `no_verdict=True`, `band_low/high=None`. Atteso: blocco "Campione insufficiente per una banda affidabile — nessuna banda emessa". Banda NON nuda.
- **(c) sintetico exact-config** — `relaxation_level<=2`, band piena, `fallback_declared=False`. Atteso: "banda a configurazione esatta".
Done-B = `ls -la` dei 3 path incollato. Verifica VISIVA = Luke apre i PDF.

## NOTE
- `.bak-s296` sono i restore point 1d (git è comunque restore: pre-edit = `git show 65fc586:<path>`). Rimovibili.
- Push resta bloccato (secret in history, S278) → commit LOCALE.
- Non toccare STATE.md/rings.json/NEXT (auto-generati).
