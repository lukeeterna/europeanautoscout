# REPORT S268 — FASE 2 PDF (DoD #2/#3) + item (c) PAVIMENTI

Branch: s210/audit-master-plan. Fonte: codice + run reale. NO rete (fixture).

## FATTO (VERDE)
DoD #2/#3 chiusi: 2 PDF reali committati, generati dalla fixture committata
`tests/fixtures/it_dist_bmw_serie3_2021.json` (scrape AS24.it 2026-06-11, cap 20 pagine).

- `tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf` (6484 byte)
  N=13, L3, no_verdict=False, conf=**bassa**, banda **€33.200–39.950** (spread €6.75k su ~36k).
- `tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf` (6453 byte)
  N=5, L3, **NO_VERDICT** (config esatta sotto-rappresentata), nessuna banda fittizia.

Run E2E: `python3 -m tools.scripts.build_s268_dossier` → rc=0 (log `/tmp/s268.txt`).

## MODIFICHE
- `tools/scripts/pdf_generator_enterprise.py`:
  - `VehicleData`: +`it_band_low/high`, `it_confidence`, `it_width_nature`, `it_n_by_level`,
    `it_scrape_date`, `it_is_floor`, `margine_netto_low/high`.
  - Wiring `generate_dossier_from_data`: legge `band_low/high/confidence/width_nature/n_by_level/
    scrape_date` da `_it_distribution`; INTERVALLO margine via
    `evaluate_margin(prezzo_de, band_low)..(band_high)` (margin_gate.py:54, pura).
  - `_create_it_distribution_section` rilavorata: **BANDA = prodotto** (headline "rifai il conto",
    banda+N+livello), NON mediana puntuale; riga confidenza+natura-banda (`n_by_level`);
    riga rilevazione (GAP-2). NO_VERDICT → label N+livello, NESSUNA banda fittizia.
  - `_create_margin_verdict_section`: prezzo IT = banda; MARGINE NETTO = **intervallo** low–high.
- `tools/scripts/build_s268_dossier.py` (NUOVO): pre-flight reportlab+fixture, 2 veicoli, 2 PDF.

## DELTA-2 (item c) — PAVIMENTI onesti NEL PDF
N dichiarato col `>=` + dichiarazione cap esplicita:
- verdetto:   ">=13 comparabili (campione cap 20 pagine / 325 annunci AS24.it, non esaustivo)".
- NO_VERDICT: ">=5 comparabili a config esatta sotto-rappresentata (campione non esaustivo)".
`it_is_floor=True` (default) marca N come pavimento, non totale mercato.

## NON FATTO (deferito S269 — fuori budget context @61%)
- **DELTA-3 / item 3 STATE.md**: registrare `BLOCKED-ON DoD#4: scrape ESAUSTIVA` + allineare header
  S264–S268. È SoT → innesca **Gate E `overwrite_sot`** (backup Rule 1d + `pending_review/<slug>.md`
  + `! python3 .harness/gate_e.py approve <slug>` da Luke). NON forzato.
- **DoD#4** resta BLOCKED: gate (min_n=8, soglie, 330i→NO_VERDICT) calibrato su campione CAP →
  logica sana ≠ dato sano. Sbloccabile solo dopo scrape esaustiva (no cap, fino a pagina corta).

## NOTA onestà
`prezzo_de` nei 2 PDF è ILLUSTRATIVO (demo): la BANDA IT è dato reale dalla fixture, il prezzo DE
è input dimostrativo dichiarato. Questi NON sono il primo dossier a un dealer reale (DoD#4 blocked).
