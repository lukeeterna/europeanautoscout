# BRIEF CC — ARGOS · S267 — FASE 2 PDF (DoD #2/#3) + chiusura gate (ratifica Luke S266)
# Branch s210/audit-master-plan · Fonte verità: codice + git + STATE.md. Chat NON è fonte.

## EREDITATO DA S266 (VERDE su DoD #1 — non riaprire la fixture)
DoD #1 CHIUSO: fixture reale committata `tests/fixtures/it_dist_bmw_serie3_2021.json` (325 listing
AS24.it, scrape_date 2026-06-11). `get_it_distribution(..., fixture_path=...)` carica raw da disco
(no rete), scrape_date dalla fixture. Test `tools/tests/test_it_distribution_fixture.py` rc=0.
Builder: `tools/scripts/build_it_fixture.py`. Debito riproducibilità S264 chiuso.

Numeri reali: **320d xDrive 2021** N=13 L3 → verdetto banda €33.200–39.950 conf=bassa (fusione_trim);
**330i 2021** N=5 L3 → **NO_VERDICT** (indeterminato).
GATE AFFERMATO-NON-PROVATO (ratifica Luke S266): i due punti NON discriminano il gate composto da un
`min_n` nudo. 320d passa con min_n 8 e 5; 330i cade su N e width insieme. I rami che PROVANO la
composizione (N>=8+indeterminato; confine N=6-7; incertezza_campione->media) NON sono toccati -> vedi (b).
325 e' un CAP `max_pages=20`, NON esaurimento -> 320d=13/330i=5 sono PAVIMENTI (vedi REPORT_S266.md).

## FASE 2 — PDF (DoD #2/#3, no rete, dalla fixture)
`tools/scripts/pdf_generator_enterprise.py` · `_create_margin_verdict_section` + `_create_it_distribution_section`:
- Aggiungi campi a `VehicleData`, leggili da `best['_it_distribution']` (righe ~1980-1986).
- Mostra: BANDA (band_low–band_high) oltre la mediana · N+livello · MARGINE-INTERVALLO
  `evaluate_margin(prezzo_de, band_low)`..`evaluate_margin(prezzo_de, band_high)` (`tools/margin_gate.py:54`, pura)
  · data-scrape (GAP-2) · riga d'onestà se L3 (n_by_level, width_nature) · NO_VERDICT -> label N+livello, no banda fittizia.
- TRASPARENZA in cima come PRODOTTO (banda+N+livello+"rifai-il-conto" headline), NON mediana puntuale con asterisco sotto.
  Il caso vetrina gira a `bassa`, spread €6.75k su ~36k (largo): e' il dominio onesto, non un difetto da nascondere.

## DoD S267
1. PDF reale nel repo 320d xDrive L3 N=13: banda+N+livello+margine-INTERVALLO+data-scrape+riga onestà. Path.
2. PDF reale nel repo 330i N=5: NO_VERDICT con N+livello reali. Path.
3. STATE.md header allineato a S264/S265/S266 (diff-first, Gate E `overwrite_sot` -> packet+approve).
4. (a) Incolla il fatto, non l'etichetta: `MIN_N_DEFAULT=8` + righe gate (`it_market_price.py:291-292`) nel REPORT.
5. (b) 3 test sintetici (in-memoria, NO rete) rc=0 che bloccano la tavola di verità. RACCOMANDATO:
   estrarre la decisione gate (oggi inline: `no_verdict`+`width_nature`+confidence) in funzione PURA
   `_decide(n, min_n, relaxation_level, spread_pool, spread_infra_trim, median)` e testarla diretta
   (forzare (N,width) a L3 via pipeline leveling e' fragile; la funzione pura blocca la verita').
   - T-A (falsificatore): N>=8 AND width=indeterminato -> DEVE NO_VERDICT. Togli braccio width -> T-A fallisce.
   - T-B (min_n=8 non 5): N=7 AND incertezza_campione -> DEVE NO_VERDICT (con min_n=5 passerebbe).
   - T-C (confine+ramo mai esercitato): N=8 AND incertezza_campione -> DEVE verdetto, confidence=media.
6. (c) Pool esaurito-o-cap: decidere (i) scrape profonda fino a pagina corta -> ri-committa fixture esaurita,
   OPPURE (ii) etichetta gli N come PAVIMENTI in PDF+REPORT. Non lasciarlo implicito (la catena S264->S266 poggia sul pool).
7. DoD#4 (primo dossier davanti a dealer reale) = decisione Luke, NON sessione tecnica. Gate (b) chiuso PRIMA di DoD#4.

## REGOLE
- NON delegare a subagent (S258). Main context, output E2E > /tmp/s267.txt 2>&1.
- Rule 1d: backup verificato prima di overwrite SoT. SoT diff-first, edit = ultimo passo.
- NON reintrodurre precisione finta. NON allargare scope (no fix short-page, no mobile.de).
- Report S266 (con CORREZIONE onestà + riconciliazione scrape): `.claude/REPORT_S266.md`.
