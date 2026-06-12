# BRIEF CC — ARGOS · S271 — chiudi coerenza dossier (test + render-verify) poi COMMIT, poi STATE.md
# Branch s210/audit-master-plan · Fonte verita': codice + git. Chat NON e' fonte.
# Context budget S270 chiuso a 61% PRIMA di test+commit -> NESSUN commit-dossier fatto. Codice DIRTY, NON committato.

## STATO S270 (codice modificato, run rc=0, MA non verificato sul render ne' testato -> NON committare cosi')
FIX-A e FIX-B del brief precedente APPLICATI + cleanup build script. Build gira (rc=0, /tmp/s270_build.txt):
  - 320d: N=13 L3 conf=bassa band=33200-39950 -> CONDIZIONATO @ 35.699. PDF 6686 byte.
  - 330i: N=5 no_verdict=True band=25299-30900 -> margin verdict MINIMALE. PDF 6008 byte.
File modificati (git diff per vederli):
  - tools/scripts/pdf_generator_enterprise.py:
    * NUOVO helper puro `_header_margin_envelope(price_eu, band_low, band_high)` (dopo _margin_verdict_rows):
      inviluppo VALIDO status-aware. PASS->margine a band_low; CONDIZIONATO->margine a breakeven
      + "(se prezzo IT >= <be>)"; REJECT->"n.d." (regione valida vuota, MAI range). Ritorna (disp,bound_inf,status,be).
    * `_create_executive_summary`: header "Margine dealer (banda)" ora usa _header_margin_envelope
      (NO piu' range grezzo _ml.._mh che includeva 1.785). margin_cell = Paragraph (wrappa la condizione).
    * FIX-B `_create_it_distribution_section`: col NOTE (data[1:][2]) wrappata in Paragraph (it_note style).
    * FIX-B `_create_margin_verdict_section`: col NOTE wrappata in Paragraph; ultima riga (label verdetto)
      colore status-aware (verde PASS / rosso REJECT|NO_VERDICT / oro CONDIZIONATO).
  - tools/scripts/build_s268_dossier.py: RIMOSSI i `_margin_*` puntuali sul mediano (inerti). Resta solo
    `_margin_decision` (gate rendering sezione) + `_it_distribution`.

## ITEM 3 CERTIFIC — VERIFICATO, NESSUN RELABEL DOVUTO (grep fatto S270, chiuso)
grep CERTIFIC/certificat in pdf_generator_enterprise.py = 5 hit, NESSUNO adiacente al verdetto-affare:
  - :733 'CERTIFICATO' = riga TOTALE della ANALISI ARGOS (punteggio AUTO/CoVe, asse-AUTO, non l'affare)
  - :1253/:1279 "portale certificato"/"Portale EU certificato" = sezione verifica-fonte annuncio
  - :1357/:1363 fallback TEXT report (non il PDF). Header gia' separato in S269 ("Punteggio ARGOS"->"Qualita auto").
Criterio brief = "se sta accanto al verdetto-affare" -> non si applica. CHIUSO senza modifica.

## DA FARE S271 (in ordine; COMMIT = ultimo, gate su test+render verdi)
0. `pip install pypdf` (puro Python, Big Sur ok — NON era installato su MacBook S270). Verifica `--dry-run` se dubbi.
1. TEST committato (manca): crea `tests/test_s269_band_verdict.py` (no rete, rc=0, FALSIFICATORE):
   - 320d (price 29500, band 33200/39950) -> `_band_verdict` status=='CONDIZIONATO', round(breakeven)==35699;
   - caso che ATTRAVERSA il floor DEVE dare CONDIZIONATO, MAI 'PASS' secco (togliendo il ramo
     condizionato in _band_verdict il test DEVE fallire);
   - NO_VERDICT: `_margin_verdict_rows(VehicleData(no_verdict=True, banda settata))` -> len(rows)==3,
     nessuna cella con 'Spread'/'Surplus'/range banda (FASE 3 provata).
   - FIX-A header (INPUT VERIFICATI eseguendo il codice reale S270, usare ESATTAMENTE questi):
     * CONDIZIONATO: `_header_margin_envelope(29500,33200,39950)` -> status=='CONDIZIONATO',
       round(bound_inf)==4284 (NON 1785), disp contiene "35.699".
     * REJECT (banda interamente sotto floor): `_header_margin_envelope(35000,33000,36000)`
       -> status=='REJECT', disp=='n.d.', bound_inf is None.  [verificato: be=41949 > band_high]
     * PASS: `_header_margin_envelope(20000,30000,35000)` -> status=='PASS',
       round(bound_inf)==6291 == round(margine_netto a band_low).  [verificato]
     Falsificatore: forzando in _header_margin_envelope il ramo CONDIZIONATO a usare band_low il test DEVE fallire.
   Numeri 320d verificati ESEGUENDO il codice (non a mano) S270: breakeven 35699; margine@be 4283.86->4284;
   margine@band_high 7038.6->7039; margine@band_low 1785.0 (decision REJECT, per questo VIETATO nell'header).
2. RENDER verify con pypdf (commit-blocker, S269/S270 validati solo a layer-codice, MAI sullo stream):
   leggi i 2 PDF in tests/dossiers_s268/ e asserisci (testo pagina concatenato):
   - 320d: CONTIENE "4.284" E "(se prezzo IT >= 35.699)"; NON contiene "1.785"; NON "38.799"/"Media mercato"/"900";
     verifica FIX-B: "L0:" "L1:" "L2:" presenti INTERI (n_by_level non clippato).
   - 330i: nessun numero margine in header (atteso "n.d."); nessuna banda/margine nel verdetto (minimale).
   Falsificatore d'artefatto: se l'header rendesse "1.785" l'asserzione DEVE fallire.
   (Comando pronto provato S270 — pypdf.PdfReader + extract_text, vedi git stash/chat se serve.)
3. SOLO dopo 1+2 verdi: COMMIT. SOLO pdf_generator_enterprise.py + build_s268_dossier.py +
   tests/dossiers_s268/*.pdf + tests/test_s269_band_verdict.py. ESCLUDI STATE.md/state/rings.json (refresh.sh, non edit).
   ATTENZIONE git diff --check: i .pdf danno trailing-whitespace warning (vedi SESSION_DIRTY.md S269) -> usa
   `git -c core.whitespace=-trailing-space commit` o committa i pdf con `git add -f` accettando il warning (binari).

## ITEM FINALE — STATE.md (GATED Gate E overwrite_sot)
Allinea header S245->S264->S269->S270 + registra BLOCKED-ON DoD#4 (scrape esaustiva, testo in
SESSIONE_S268_REPORT_COMPLETO.txt [F]). Rule 1d: backup verificato-per-stat PRIMA. Diff-first. Edit ULTIMO.
Serve `! python3 .harness/gate_e.py approve <slug>` da Luke. Se a budget -> S272.

## INVARIATO
- DoD#4 NON sbloccabile finche': (i) dossier coerente verde+test, E (ii) scrape ESAUSTIVA fatta.
- NON allargare scope: no fix short-page, no mobile.de, no nuova scrape.
- NON delegare a subagent. Output E2E > /tmp/s271.txt 2>&1. Chiudi a 60% context.
