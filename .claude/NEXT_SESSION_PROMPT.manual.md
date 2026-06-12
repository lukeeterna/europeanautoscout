# BRIEF CC — ARGOS · S272 — render-verify COMMITTATO (durabilita') -> STATE.md -> scrape esaustiva
# Branch s210/audit-master-plan · Fonte verita': codice + git. Chat NON e' fonte.

## STATO INGRESSO (S271 CHIUSA verde, pushata — verde REALE, non S268-finto)
- commit e39536b + a926f43 + 9d4546c su origin. Arco coerenza S268->S271 sostanzialmente finito:
  Frankenstein morto, false-PASS ucciso in 2 layer (verdetto + header), breakeven derivato,
  CoVe separato dall'affare, demo verificato sullo STREAM reale (13/13).
- BUCO DI DURABILITA' (verificato git ls-files): il render-verify che ha dato la prova
  d'artefatto e' in /tmp/s271_render_verify.py, NON committato. Il committato
  tests/test_s269_band_verdict.py testa SOLO la LOGICA delle helper (zero pypdf/PDF),
  NON il WIRING (helper -> cella-PDF). Il Frankenstein S268 e' nato proprio dal wiring
  (helper giuste, _create_financial_analysis_v2 renderizzata prima trascinava la mediana
  morta) -> un unit-test di logica NON lo prende. Finche' la prova d'artefatto non e' in
  suite, "demo che resta pulito" (il senso del filone S268) NON e' raggiunto.
- AMBIENTE: build+test girano SOLO con system python3 (reportlab 4.4.10 + pypdf 6.13.2);
  .venv NON ha reportlab. Eseguire con `python3` di sistema, NON .venv, o falliscono spurii.

## ITEM 1 (PRIMO — chiude la durabilita' di DoD#4-i) — render-verify COMMITTATO
Promuovi il render-verify /tmp a test committato che difende dal WIRING.
- NUOVO tests/test_s271_render_artifact.py (no rete, deterministico, system py3, pypdf gia' c'e'):
  1. Rigenera i 2 PDF dalla fixture committata in una TEMP dir (tempfile, NON sovrascrivere i
     demo committati in tests/dossiers_s268/).
  2. RICOMPUTA gli attesi dalle helper (_header_margin_envelope, evaluate_margin, _band_verdict)
     -> NON hardcodare "4.284" come stringa magica (disciplina S266: invarianti STRUTTURALI, non N
     cablati). Cosi' il test sopravvive a un cambio-fixture (ITEM 3 lo cambiera').
  3. Asserzioni STRUTTURALI sullo stream pypdf:
     - header 320d CONTIENE il bound_inf ricomputato (=margine a max(band_low,breakeven)) + suffisso
       "(se prezzo IT >= <breakeven>)"; header NON contiene il margine a band_low se status!=PASS
       (il falso-PASS d'header);
     - 330i NO_VERDICT: ZERO cifre-margine in header E in tabella-verdetto (suppressione totale);
     - nota distribuzione: "L0:.. L1:.. L2:.. L3:.." INTERA (FIX-B non clippato);
     - whole-page: nessun "38.799"/"Media mercato"/"900" (mediana morta + flat-fee legacy).
  4. Normalizza whitespace prima del match (reportlab+pypdf inietta spazi spuri): es. "4.284"=="4 284".
- Commit del test. Da qui la regressione di WIRING e' presa SENZA lettura esterna.
- Riferimento pronto: /tmp/s271_render_verify.py (header-scoping gia' corretto, da generalizzare a recompute).
=> SOLO dopo ITEM 1 committato: DoD#4 punto (i) e' DURABILE-chiuso.

## ITEM 2 — STATE.md align (GATED Gate E overwrite_sot)
- PRE-CHECK OBBLIGATORIO prima di editare: STATE.md e' hand-edit o GENERATO da state/refresh.sh?
  (memoria S243: tabella anelli generata leggendo rings.json). Se GENERATO -> NON editarlo a mano,
  correggi sorgente/template + rilancia refresh.sh.
- Rule 1d: backup verificato-per-stat PRIMA. Diff-first. Edit ULTIMO.
- Slug Gate E NON esiste ancora (i 3 overwrite_sot esistenti puntano a MEMORY.md): si genera al
  PRIMO Edit su STATE.md -> packet in .harness/pending_review/<slug>.md -> Luke
  `! python3 .harness/gate_e.py approve <slug>` -> RE-Edit (token una-tantum).
- Allinea header S245->S264->S269->S271 + registra BLOCKED-ON DoD#4(ii).

## ITEM 3 — DoD#4(ii) scrape esaustiva (gate empirico mercato vero vs artefatto scraper)
- Definisci "esaustiva" (fatto terminale = pagina corta) PRIMA di lanciare. min_n=8.
- AVVISO durabilita': la scrape esaustiva PUO' invalidare il demo committato — se la 330i ha un
  pool reale oltre il cap (>min_n), SMETTE di essere NO_VERDICT e il suo PDF cambia. NON e'
  regressione: e' il test che si risolve (NO_VERDICT-330i = artefatto del cap 20-pagine, non del
  mercato). Quando la fixture-cap e' sostituita dall'esaustiva -> ri-committa fixture + 2 PDF +
  RICOMPUTA le asserzioni di ITEM 1 (bound alla fixture corrente, by design — per questo ITEM 1
  ricomputa invece di cablare).

## MAPPA VERSO PRODUCTION (non mossa — i 2 gate empirici restano, prima che un dealer veda nulla)
1. scrape esaustiva (mercato vero vs artefatto scraper; NO_VERDICT-330i, min_n=8) = ITEM 3.
2. prezzo_de REALE al posto dell'illustrativo nel dossier.

## INVARIATO
- DoD#4 sblocco = (i)[DURABILE-chiuso dopo ITEM 1 committato] AND (ii)[scrape esaustiva].
- NON allargare scope (no short-page, no mobile.de, no nuova feature). NON delegare task atomici
  a subagent. Output E2E > /tmp/s272.txt. Chiudi a 60% context.
- FINE SESSIONE OBBLIGATORIO: MEMORY.md + .claude/REPORT_S272.txt (progressi+evidenze E2E+next
  prompt, UN file) aperto con `open -a TextEdit` + handoff + commit/push.
