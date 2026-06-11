# BRIEF CC — ARGOS · S269 — DELTA-3 STATE.md (Gate E) + DoD#4 gate empirico
# Branch s210/audit-master-plan · Fonte verità: codice + git + STATE.md. Chat NON è fonte.

## CHIUSO IN S268 (VERDE — non riaprire)
**DoD #2/#3 — 2 PDF reali committati (commit 24eb9ab, pushed).**
- `tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf` (6484 byte) — N=13, L3, verdetto-banda,
  conf=bassa, banda €33.200–39.950 (spread €6.75k su ~36k = dominio onesto).
- `tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf` (6453 byte) — N=5, L3, NO_VERDICT, no banda fittizia.
- `tools/scripts/pdf_generator_enterprise.py`: BANDA p25-p75 = prodotto (no mediana puntuale),
  margine = INTERVALLO (`evaluate_margin` su band_low/high), N col `>=` (pavimento, cap esplicito),
  NO_VERDICT senza banda. `VehicleData` +8 campi. Wiring `generate_dossier_from_data` ~1953-2005.
- `tools/scripts/build_s268_dossier.py` (NUOVO) — pre-flight reportlab+fixture, no rete. Run:
  `python3 -m tools.scripts.build_s268_dossier` → rc=0 (log /tmp/s268.txt).
- Report: `.claude/REPORT_S268.md`.
- DELTA-2 (item c) PAVIMENTI: fatto NEL PDF (`it_is_floor=True`, `>=N`, "campione non esaustivo").
- NB: `prezzo_de` nei 2 PDF è ILLUSTRATIVO (banda IT = dato reale fixture; DE = input demo dichiarato).

## DA FARE S269
### DELTA-3 + item 3 — STATE.md (GATED Gate E `overwrite_sot`) — PRIORITÀ
STATE.md è SoT: l'edit innesca Gate E → BLOCCA + `pending_review/<slug>.md` + serve
`! python3 .harness/gate_e.py approve <slug>` da Luke. Procedura:
1. Rule 1d: backup verificato di STATE.md (stesso path, size>0, mtime precedente, fuori /tmp, citato).
2. Diff-first: mostra il diff PRIMA di scrivere.
3. Edit = ULTIMO passo. Due scritture, stessa natura SoT, stesso gate:
   (a) Allinea header STATE.md S245/S246 → S264–S268 (contenuto verificato presente DOPO, NON soglia righe).
   (b) Registra il BLOCKED-ON DoD#4 (testo esatto sotto).
   Testo DELTA-3 da inserire:
   "BLOCKED-ON DoD#4: scrape ESAUSTIVA (override results_per_page=1 fino a pagina corta, NESSUN cap
    max_pages) sulla famiglia vetrina, per falsificare che NO_VERDICT 330i e min_n=8 NON siano
    artefatti del cap. Finché non fatto: NO_VERDICT può essere falso-NO_VERDICT (rifiuto di affare
    reale). Fatto terminale = pagina corta raggiunta."

### DoD#4 = decisione Luke, NON sessione tecnica.
Gate (b) chiuso = LOGICA sana, NON dato sano. DoD#4 NON sbloccabile finché DELTA-3 non soddisfatto
(scrape esaustiva). Logica onesta ≠ verdetto onesto sul mercato vero.

## REGOLE
- NON delegare a subagent (S258). Main context, output E2E > /tmp/s269.txt 2>&1.
- Rule 1d: backup verificato-per-stat PRIMA di overwrite STATE.md. NON reintrodurre precisione finta.
- NON allargare scope: no fix short-page, no mobile.de, no nuova scrape in S269 (DELTA-3 = solo nomina del gate).
- Context budget: /context, chiudi a 60%.
