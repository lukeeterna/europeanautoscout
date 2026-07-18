MANDATO: VALUTA-POI-BUILD. Prima VALUTA (FASE 0) contro il disco; procedi SOLO se regge.
Branch: s210/audit-master-plan · ARGOS_HARNESS_UNLOCK=1 al lancio · single-writer.
Se un passo richiede di andare oltre quelli elencati, FERMATI e riporta — non allargare lo scope.

CONTESTO: due cose in questa sessione, in ordine.
(1) CHIUSURA [A1]: il referto forense S285 ha stabilito che il punto 7 monolitico ("invio
    passato per Gate-E") è INSODDISFACIBILE su TEST_FOUNDER, perché gate_e.py whitelista
    39<TEST_FOUNDER_NUM> (gate_e.py:37,349 + commit 40a5d1e). Decisione Luke: spaccare il punto 7 in
    7a (meccanica d'invio, GIÀ verde stasera: commit 40a5d1e HTTP 200 msg_id
    out_1781986351333_evd8h) + 7b (breaker vivo su numero non-whitelist) e DECLASSARE 7b a
    gate-pre-dealer-reale (è già nei "3 gate a dealer reale"). Con questo, [A1] = VERDE.
(2) AVVIO FASE 1: aperto l'item [S4] Dealer Profiling (primo item dopo [A1]). Done-condition =
    sez.6 di docs/ARCHITETTURA_E2E.md. SOLO Fase 0 di scoping in questa sessione — niente build
    di S4 finché lo scoping non è verificato e approvato.

IDEMPOTENTE: la riscrittura di STATE/ROADMAP è una riconciliazione — se 7a/7b sono già presenti,
NON duplicare. Lo scoping S4 è sola lettura. Ri-eseguibile N volte senza doppioni né effetti.

═══ PARTE A — CHIUSURA [A1] (docs-only) ═══

A0. VERIFICA (riporta prima di scrivere):
    git rev-parse --short HEAD ; git status --porcelain ; git rev-parse --abbrev-ref HEAD
    Conferma in history: 40a5d1e (invio), 041e612 (claim falsa rimossa).
    Mostra le righe attuali del punto 7 in docs/briefs/BRIEF_A_e2e_67_testfounder.md.
    Mostra il blocco GENERATED rings in STATE.md (stato anello 6-7).
    → Se tree non-clean da lavoro non-hook, o HEAD inatteso → FERMATI e riporta.

A1. RISCRIVI il punto 7 in BRIEF_A (solo quel punto, non il resto della checklist):
    - 7a — MECCANICA D'INVIO: Day-1 consegnato a TEST_FOUNDER (HTTP 200 + msg_id). Stato: VERDE
      (commit 40a5d1e). Cita il msg_id come fatto terminale.
    - 7b — BREAKER VIVO: Gate-E blocca outreach_real su numero NON-whitelist (deny→packet→
      approve→consume), a vuoto, ZERO invio. Stato: DEFERITO a gate-pre-dealer-reale (già nei
      3 gate). NON è done-condition di [A1].
    Annota: il punto 7 monolitico era insoddisfacibile su TEST_FOUNDER per whitelist (gate_e.py:37).

A2. AGGIORNA STATE.md / rings:
    Se l'anello 6-7 si flippa a VERIFIED, deve passare per state/refresh.sh (il blocco è GENERATED,
    non editare a mano — serve ARGOS_HARNESS_UNLOCK=1). Done-condition [A1] = 7 punti con 7a verde
    + 7b deferito. Esegui refresh.sh <SESSION_ID> se e solo se il check dell'anello è reale e passa;
    altrimenti NON flippare a mano e riporta perché.

A3. Verifica che la ROADMAP rifletta [A1] chiuso e [S4] come item attivo corrente (è già scritto
    "primo item dopo [A1]"): conferma, non riscrivere se già coerente.

COMMIT A: solo i file docs nominati (BRIEF_A, STATE.md, eventuale ROADMAP), mai git add -A. No push.

═══ PARTE B — SCOPING FASE 1 [S4] (READ-ONLY, niente build) ═══

B0. Lo scopo è verificare che la sez.6 di ARCHITETTURA_E2E.md sia ESEGUIBILE col codice reale,
    PRIMA di costruire. NON costruire S4 in questa sessione.

B1. Leggi e riporta:
    - lo scraper AS24 esistente (tools/scrapers/ + tools/on_demand_runner.py): qual è la sua
      interfaccia reale? Accetta un URL pagina-DEALER (l'inventario di un dealer) o solo query di
      ricerca per veicolo? Mostra firma/parametri reali.
    - esiste già un concetto di "dealer" nel codice/DB (data/*.db, schema)? O va creato da zero?
    - templates.py generate_cold_day1(dealer_brands, source, dealer_name): quali campi accetta
      OGGI? Può già ricevere un dato di profilo (es. n° annunci, gap) o la firma va estesa?

B2. VERDETTO DI FATTIBILITÀ sulla sez.6:
    - le 5 done-condition di sez.6 sono raggiungibili riusando lo scraper AS24 com'è, o serve
      adattarlo (e quanto)? In particolare: lo scraper sa estrarre l'INVENTARIO di una pagina-dealer
      pubblica AS24, o sa solo cercare veicoli? Questo è il perno di S4.
    - il confine GDPR (solo dati commerciali, zero personali) è rispettabile con i campi che lo
      scraper già estrae? Mostra quali campi tornerebbero nel DB.
    - cosa MANCA esattamente da costruire (lista minima), e cosa si riusa.

B3. NON scrivere codice S4. NON creare data/dealers.db. NON scrapare un dealer reale.
    Solo: leggere il codice, e referto di fattibilità.

VERDETTO FINALE (poche righe):
  - [A1] chiuso? (7a verde + 7b deferito, anello 6-7 stato reale dopo refresh)
  - Fase 1 [S4] fattibile riusando AS24? SÌ / SÌ-CON-ADATTAMENTO (quale) / NO (perché)
  - lista minima di cosa costruire in S4, prossima sessione

VINCOLI: Parte A = docs-only (commit file nominati). Parte B = READ-ONLY (zero codice/scrape/DB).
Mai --no-verify / git add -A. Push bloccato ([F]) — non forzare. Ordine build 1→5 NON modificabile.
