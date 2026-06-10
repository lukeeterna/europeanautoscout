================================================================================
 REPORT SESSIONE S262  +  NEXT PROMPT S263
 ARGOS Automotive — 10 giugno 2026
================================================================================

--------------------------------------------------------------------------------
 PARTE 1 — REPORT S262 (anello PDF margin gate)  ✅ VERDE
--------------------------------------------------------------------------------

OBIETTIVO (isolato, non negoziabile):
  Chiudere l'anello PDF del margin gate — T1/T2/T3 — SENZA toccare il probe pool
  IT (rimandato a S263). L'anello era il fatto terminale mai prodotto su questo asse.

COSA HO FATTO (3 file sorgente):

  1. tools/on_demand_runner.py — RUNNER SPEC-AWARE
     - La chiamata al margin gate ora passa variant/fuel/transmission/power a
       get_it_distribution -> comparabili dello STESSO trim (non piu' mediana fusa).
     - Aggiunto skip NO-VERDICT: se n < min_n il veicolo NON puo' mai uscire PASS
       in produzione (continue + log esplicito).

  2. tools/margin_e2e.py — GOTCHA FUEL CHIUSO (stesso giro)
     - fuel 'unknown' -> None anche qui (era latente a riga 39).
     - Stessa classe del bug "mediana fusa": input non normalizzato che
       over-restringe i comparabili a fuel="unknown" (=0 match), perche'
       derive_trim_family NON normalizza 'unknown'. Radice identica.

  3. tools/scripts/pdf_generator_enterprise.py — RAMO NO_VERDICT NEL PDF
     - VehicleData: aggiunti campi relaxation_level (L0-L3) e no_verdict (bool).
     - Mapping it_dist -> VehicleData: se no_verdict=True forza
       margin_decision='NO_VERDICT'.
     - _create_margin_verdict_section: branch a 3 vie (PASS / REJECT / NO_VERDICT)
       con N e livello REALI nella label (non 0/'-' di default).

--------------------------------------------------------------------------------
 EVIDENZE E2E (DoD — fatti terminali reali, Rule 1b)
--------------------------------------------------------------------------------

[T1] VETO PRODUZIONE INTATTO (non-regressione)
  Comando:  python3 -m tools.margin_gate
  Exit:     0
  Output reale:
    === Falsificazione X1 (DoD #3) ===
      chiavi_in_mano      = 21795
      spread_lordo        = 1067  (atteso 1067)
      dealer_floor (12%)  = 2743  (atteso ~2743)
      surplus             = -1676  (atteso ~-1676)
      DECISIONE           = REJECT  (atteso REJECT)
      OK: X1 correttamente REJECT
    === Sanity PASS branch ===
      DECISIONE           = PASS  (atteso PASS)
      OK: PASS e margine netto >= pavimento dealer
    TUTTI I TEST PASSATI
  -> Il gate di produzione non ha regressioni.

[T2] PDF REJECT NEL REPO
  Path:  dossiers/ARGOS_BMW_X1_2021_S262_T2_REJECT_20260610_152043.pdf
  Size:  6277 bytes
  Veicolo iniettato: X1 founder (chiavi 21795 / mercato IT 22862, friction 0)
  Verdict cell renderizzata (ultima riga tabella, colonna NOTE):
    'REJECT — sotto pavimento dealer'
  -> CoVe alto + margine REJECT + decisione finale REJECT.

[T3] PDF NO-VERDICT NEL REPO  (CHECK CHIAVE peer review)
  Path:  dossiers/ARGOS_BMW_M340_2021_S262_T3_NOVERDICT_20260610_152043.pdf
  Size:  6291 bytes
  Veicolo iniettato: pool thin (no_verdict=True, n=2, relaxation_level=3)
  Verdict cell renderizzata (ultima riga tabella, colonna NOTE):
    'NO-VERDICT — comparabili insufficienti (N=2, livello L3)'
  -> N e livello sono REALI (N=2, L3), NON 0/'-' di default. Verificato leggendo
     la cella esatta che reportlab disegna nel PDF.

  Nota metodo: pypdf bloccato da PEP 668 (no install) e content-stream reportlab
  FlateDecode (grep inaffidabile). Verifica fatta chiamando direttamente
  _create_margin_verdict_section con gli stessi VehicleData e leggendo
  tbl._cellvalues[-1][-1] — e' ESATTAMENTE la stringa che finisce nel PDF, e la
  sezione e' inclusa (PDF generati 6277/6291 B con margin_decision truthy).

  Harness T2/T3: /tmp/s262_harness.py (throwaway, via generate_dossier_from_data
  in-process — bypassa il veto `return None` del runner reale).

--------------------------------------------------------------------------------
 COMMIT / PUSH
--------------------------------------------------------------------------------
  9fb7824  S262: chiude anello PDF margin gate (spec-aware runner + ramo NO_VERDICT)
  2666e30  S262 DONE marker in resume prompt -> next = S263 probe pool IT
  Branch:  s210/audit-master-plan  (pushato su origin)
  Files:   tools/on_demand_runner.py, tools/margin_e2e.py,
           tools/scripts/pdf_generator_enterprise.py
  PDF in dossiers/ = gitignored (evidence locale, non versionata).

--------------------------------------------------------------------------------
 STATO / VINCOLI RISPETTATI
--------------------------------------------------------------------------------
  - Anello chiuso ISOLATO. Probe pool IT NON toccato (resta S263).
  - min_n = 8 NON ratificato (ratifica dopo dati probe S263).
  - Context chiuso ~57% (sotto soglia 60%).
  - Implementazione in main context (no delega — S258: subagent esauri' context).



================================================================================
 PARTE 2 — NEXT PROMPT S263  (sessione separata, solo dopo anello verde)
 PROBE PROFONDITA' POOL IT
================================================================================

INQUADRAMENTO (peer review): NESSUN ESITO "FALLISCE".
  - Esito A -> lo scraping enterprise ripaga: lo costruisci con convinzione.
  - Esito B -> ti risparmia l'autostrada verso un pozzo vuoto e ti dice che il
    prodotto e' un VERDETTO A BANDE ("questa auto sta nella fascia alta/bassa del
    mercato IT per la sua configurazione") — comunque vendibile a un dealer.
  Scopri QUALE prodotto stai costruendo. Vale mezza sessione e va PRIMA di
  qualsiasi riga di stealth scraping.

DOMANDA UNICA:
  Aumentando la profondita' di scraping, le famiglie ESATTE si riempiono (N>=8)
  o il mercato IT non le contiene?

METODO (idempotente, throwaway, NO infra nuova):
  - Famiglie target:
      320d xDrive 2021, 318d 2021, 330i petrol 2021, M340 2021
  - Per ciascuna:
      AutoScoutScraper("autoscout24_it").scrape_model  con anno +-2, paginazione
      profonda.
  - Conta N con le STESSE chiavi del gate: derive_trim_family + _match a OGNI
    livello L0->L3.
  - OUTPUT = una riga per famiglia:   L0=.. L1=.. L2=.. L3=..
    (NON un N generico: 320d 2021 ne conta ~12, ma 320d xDrive 2021 diesel a L0
     ne conta 2 — il numero che decide e' quello che vede il gate.)

ESITI:
  - Esito A (N>=8 a L0-L1)  -> B3: industrializza lo scraper IT; DoD su
    famiglie-con-N, non su listing totali.
  - Esito B (N=1-3 pescando tutto) -> verdetto a BANDE, NON mediana puntuale.
    NON costruire stealth.

VINCOLI S263:
  - NON toccare cove_engine_v4.py. Nessuna azione esterna (dealer/WA).
  - min_n=8 si ratifica QUI, con i dati del probe.
  - Probe isolato: niente stealth/scaling/mobile.de in questa sessione.

RIFERIMENTI:
  - PLAN.md = source-of-truth.
  - Dettaglio completo in: .claude/NEXT_SESSION_PROMPT.manual.md (sezione S263).
================================================================================
