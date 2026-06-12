# BRIEF CC — ARGOS · S272 — STATE.md align (Gate E) + DoD#4(ii) scrape esaustiva
# Branch s210/audit-master-plan · Fonte verita': codice + git. Chat NON e' fonte.

## STATO in ingresso (S271 CHIUSA verde, pushata)
- commit `e39536b` su origin/s210/audit-master-plan: dossier verdetto-affare coerente.
  - `tests/test_s269_band_verdict.py` 6/6 PASS (falsificatori band_verdict/header_envelope/no_verdict).
  - render-verify pypdf 13/13 sullo stream (one-shot `/tmp/s271_render_verify.py`, NON committato).
  - Header CONDIZIONATO = margine al break-even (4.284) + "(se prezzo IT >= 35.699)", MAI 1.785.
- pypdf 6.13.2 installato system python3 (--break-system-packages). Build gira con system python3 (NON .venv).
- DoD#4 punto (i) "dossier coerente verde+test" = CHIUSO. Resta SOLO punto (ii).

## DA FARE S272 (in ordine)
1. STATE.md align (GATED Gate E `overwrite_sot`):
   - Allinea header S245->S264->S269->S270->S271 + registra BLOCKED-ON DoD#4(ii) (scrape esaustiva).
   - Rule 1d: backup verificato-per-stat PRIMA dell'edit. Diff-first, Edit ULTIMO.
   - Lo slug Gate E NON esiste ancora: si genera al PRIMO attempt di Edit su STATE.md (i 3 slug
     overwrite_sot esistenti puntano a MEMORY.md, non STATE.md). Dopo l'attempt, Gate E scrive il
     packet in `.harness/pending_review/<slug>.md` -> Luke fa `! python3 .harness/gate_e.py approve <slug>`
     -> RE-attempt stessa Edit (token una-tantum).
   - NON edit STATE.md via refresh.sh? VERIFICA: STATE.md e' generato o hand-edit? (memoria S243 dice
     tabella anelli GENERATA da state/refresh.sh leggendo rings.json -> potrebbe NON essere edit a mano).
2. DoD#4 punto (ii): scrape ESAUSTIVA (l'altra meta' dello sblocco DoD#4). Definire cosa = "esaustiva"
   dal MASTER PLAN / SESSIONE_S268_REPORT_COMPLETO.txt prima di lanciare.

## INVARIATO
- DoD#4 sblocco = (i) dossier verde+test [FATTO] AND (ii) scrape esaustiva [PENDING].
- NON allargare scope: no fix short-page, no mobile.de, no nuova feature.
- NON delegare a subagent per task atomici. Output E2E > /tmp/s272.txt. Chiudi a 60% context.
