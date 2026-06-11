# BRIEF CC — ARGOS · S267 — FASE 2 PDF (DoD #2/#3) su fixture committata
# Branch s210/audit-master-plan · Fonte verità: codice + git + STATE.md. Chat NON è fonte.

## EREDITATO DA S266 (VERDE — non riaprire)
DoD #1 CHIUSO: fixture reale committata `tests/fixtures/it_dist_bmw_serie3_2021.json` (325 listing
AS24.it, scrape_date 2026-06-11). `get_it_distribution(..., fixture_path=...)` carica raw da disco
(no rete) e usa lo scrape_date della fixture. Test `tools/tests/test_it_distribution_fixture.py` rc=0.
Builder ri-eseguibile: `tools/scripts/build_it_fixture.py`. Debito riproducibilità S264 chiuso.

Numeri reali (dalla fixture): **320d xDrive 2021** N=13 L3 verdetto banda €33.200–39.950 conf=bassa
(fusione_trim); **330i 2021** N=5 L3 **NO_VERDICT** (indeterminato). Gate composto S265 confermato sul vero.

## FASE 2 — DA FARE (DoD #2/#3, BLOCKED-ON solo lavoro PDF, no rete)
`tools/scripts/pdf_generator_enterprise.py` · `_create_margin_verdict_section` + `_create_it_distribution_section`:
- Aggiungi campi a `VehicleData`, leggili da `best['_it_distribution']` (righe ~1980-1986).
- Mostra: BANDA (band_low–band_high) oltre la mediana · N+livello · MARGINE-INTERVALLO
  `evaluate_margin(prezzo_de, band_low)`..`evaluate_margin(prezzo_de, band_high)` (firma:
  `tools/margin_gate.py:54`, pura) · data-scrape (GAP-2) · riga d'onestà se L3 (n_by_level, width_nature)
  · se NO_VERDICT → label N+livello, niente banda fittizia.
- I 2 PDF reali si generano DALLA FIXTURE (no rete): 320d xDrive (verdetto) + 330i (NO_VERDICT). NEL REPO, path incollato.

## DoD S267
1. PDF reale nel repo 320d xDrive L3 N=13: banda+N+livello+margine-INTERVALLO+data-scrape+riga onestà. Path.
2. PDF reale nel repo 330i N=5: NO_VERDICT con N+livello reali. Path.
3. STATE.md header allineato a S264/S265/S266 (diff-first, Gate E `overwrite_sot` → packet+approve).

## REGOLE
- NON delegare a subagent (S258). Main context, output E2E > /tmp/s267.txt 2>&1.
- Rule 1d: backup verificato prima di overwrite SoT. SoT diff-first, edit = ultimo passo.
- NON reintrodurre precisione finta. NON allargare scope (no fix short-page, no mobile.de).
- Brief originale completo: `.claude/NEXT_SESSION_PROMPT.manual.md`. Report S266: `.claude/REPORT_S266.md`.
