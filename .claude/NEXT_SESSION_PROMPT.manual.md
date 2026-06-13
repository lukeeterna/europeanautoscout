# BRIEF CC — ARGOS · ROADMAP S273→S275 verso DAY-1 (primo dossier reale a dealer vero)
# Branch s210/audit-master-plan · Fonte verita': codice + git. Chat NON e' fonte.

## >>> S273 PARZIALE — ITEM A NON chiuso (handoff su context-gate). DETTAGLIO: .claude/REPORT_S273.txt
## FINDING S273: la fixture committata (325) era TRONCATA dal cap DEEP_PAGES=20. Verification scrape
## (results_per_page=1, max_pages=50) = 770 listing e terminato AL CAP (pagina vuota NON raggiunta) ->
## pool reale >770. Calibrazione 330i NO_VERDICT(n=5)/320d(n=13) era su MEZZO pool = INVALIDA.
## S273-cont = build_it_fixture DEEP_PAGES->80 su path NUOVO (Rule 1d) + 3 GATE DI VALIDITA' (ADD-1/2/3
## sotto) che PRECEDONO il fidarsi dei numeri. Re-test s271, commit. POI ITEM B/C/D sotto.
## (Le 2 azioni Luke una-tantum qui sotto restano pendenti: lanciale via '!'.)

## >>> INTEGRAZIONE S273-cont (Luke 2026-06-13, validata sui dati da CC — additiva all'azione unica)
## Il finding S273 e' piu' grande di "ricalibra 330i": 3 conclusioni empiriche del pivot (config-esatta
## mai N>=8 / min_n scatta a L3 / "alta" e' codice morto) sono state ratificate sul pool 325 = MEZZO
## mercato. Sono claim sul MERCATO, non sul codice -> vanno ri-misurate sul pool pieno PRIMA di fidarsene.
##
## ADD-1 — RE-DERIVA l'intera tabella L0..L3, non solo la 330i.
##   Sul pool esaustivo misura ESPLICITAMENTE la profondita' a config ESATTA (L0/L1) per le famiglie
##   LIQUIDE (320d xDrive, 318d). Domanda decisiva: una tocca N>=8 a L0/L1 sul pool pieno?
##   SI -> "config esatta e' morta" si ROVESCIA parz. e "alta" NON e' codice morto: banda STRETTA L0/L1,
##        non larga L3. Il prodotto guadagna precisione reale.   NO -> il pivot regge anche sul pool vero.
##   Documenta la tabella L0..L3 COMPLETA, non solo il delta 330i. E' la base empirica dell'intero pivot.
##
## ADD-2 — il sito PAGINA-CAPPA? (PRIMA di alzare DEEP_PAGES a 80 e inseguire la pagina vuota).
##   La verification scrape S273 ha pagina 50 ANCORA piena = indistinguibile tra "pool enorme" e "cap >50".
##   GAP VERIFICATO (CC): il break base_scraper.py:374 usa len(page_listings) RAW, NON len(all_listings)
##   unici (dedup :364-366). Una pagina-di-DUPLICATI al cap (20 raw, 0 nuovi) NON rompe -> il build_it_fixture
##   attuale NON distingue pool-esaurito da cap-a-duplicati. Quindi "pagina vuota" nuda e' insufficiente.
##   TERMINATORE in ordine di robustezza:
##     (a) PRIMA verifica get_total_pages(html) a pagina 1 (base_scraper.py:333-336 lo legge gia' e clampa
##         max_pages): se AS24 espone il totale -> fatto terminale = "raggiunto total_pages dichiarato",
##         piu' pulito e cheap della probe. Se ritorna None -> (b).
##     (b) probe pagina alta (es. 200): se hard-cappa (vuoto/dup/errore) -> "esaustivo" INDEFINIBILE, unita'
##         onesta = "N annunci che il portale ESPONE per query+sort", dichiarata come tale.
##     (c) termina su ZERO nuovi listing_id su 2-3 pagine consecutive (non sulla prima vuota); FLAG
##         "hard-cap sospetto" se n si ferma a numero tondo (1000/2000) o compaiono listing_id duplicati.
##   Documenta QUALE dei tre: cambia il significato della tabella ADD-1 (pool vero vs fetta-max-esposta).
##
## ADD-3 — il `sort` (RISCRITTO da CC: gia' VERIFICATO sul codice, non e' un bias di prezzo).
##   FATTO: sort="standard" (autoscout_scraper.py:415; base_scraper.py:295-315 non lo sovrascrive ->
##   default tiene). NON e' price_asc -> lo scenario "fixture 325 = meta' economica, bande troppo basse"
##   e' INFONDATO. Inoltre fixture(2026-06-11) e verification(2026-06-13) sono snapshot DIVERSI a 2 giorni:
##   con sort=rilevanza (ri-rankabile, non chiave deterministica) NON puoi dedurre la direzione del bias dal
##   delta 325->770. => NON inseguire un bias-prezzo (non esiste). Azione: DICHIARA il campione come
##   relevance-ordered nel meta della nuova fixture e chiudi la COMPLETEZZA via ADD-2. Niente reorder.
##
## ADD-4 — onesta' di FONTE (stessa classe dell'header-margine S270). PRECONDIZIONE: VERIFICA prima.
##   La banda = "prezzi RICHIESTI su AutoScout24.it", non "prezzo mercato Italia"; richiesto != transato
##   (i dealer trattano al ribasso) -> banda su richiesti SOVRASTIMA il ricavo realizzabile -> gonfia il
##   margine (parz. compensato dal prezzo_de anch'esso negoziabile; sui premium lo sconto IT in valore
##   assoluto probabilmente domina). FIX di sola ETICHETTA, NON modello di sconto (paralisi = fallimento
##   opposto, fuori da Day-1):
##   PRECOND (CC, anti-spreco): LEGGI prima la stringa header reale in pdf_generator_enterprise.py /
##     it_market_price.py. NON verificato che l'headline oggi dica "Prezzo mercato Italia"; potrebbe gia'
##     essere neutra -> se lo e', il rename #1 e' no-op, resta solo #2.
##   1. SE header over-dichiara ("Banda mercato IT"/"Prezzo mercato Italia") -> "Fascia prezzi richiesti AS24.it".
##   2. Riga-limite nel dossier: "Fascia su prezzi RICHIESTI (annunci), non di transazione; i prezzi
##      realizzati sono tipicamente inferiori." Dichiarazione, NON correzione numerica. Haircut = POST-Day-1.
##   Luke (dominio) giudica se lo scarto conta sul caso reale ITEM C.
##
## ORDINE: ADD-2 (get_total_pages / probe / dedup) PRIMA di scegliere DEEP_PAGES. Poi scrape esaustiva UNICA fresca ->
## ADD-1 (tabella L0..L3 completa) -> falsifica 330i sul pool vero. ITEM C (dossier reale) NON parte
## finche' ADD-1/2/3 non hanno dato una base-mercato fidata.

## STATO INGRESSO (S272 CHIUSA verde — ITEM 1 durabilita' DoD#4-i)
- commit f50d4b0 + ff4763a su origin. test_s271_render_artifact.py 5/5 (rigenera da fixture in
  tempdir, ricomputa i bound dalle helper, asserisce stream pypdf). Falsifier verificato: header
  con margine band_low (falso-PASS S268) -> test 320d FAIL. test_s269 6/6. DoD#4(i) DURABILE-chiuso.
- 2 AZIONI LUKE PENDENTI (una-tantum, dettaglio in .claude/REPORT_S272.txt):
  1) Gate E pointer indice MEMORY.md: `! python3 .harness/gate_e.py approve overwrite_sot-dc04f63aaf`
     (file-memoria topic gia' scritto; manca solo la riga-indice). Poi CC ri-fa l'Edit una volta.
  2) Restore 2 PDF demo (diff SOLO timestamp): `! git checkout -- tests/dossiers_s268/`.

# INQUADRAMENTO (non saltarlo): l'ENGINE (banda+verdetto+artefatto onesto) e' chiuso e durabile (S272).
# Day-1 = lo stesso engine alimentato da UN caso reale con scrape COMPLETE. NON serve fixare lo
# short-page sui 28 portali ne' automatizzare il sourcing DE: quelli gateano lo SCALING, non Day-1.
# Per UN dossier ti puoi permettere uno scrape lento-ma-completo (results_per_page=1, tecnica S264,
# una volta) e sourcing DE manuale (Luke sceglie 1 auto reale).
# REGOLA DANNO-ZERO: nessun dossier va a un dealer se la sua banda poggia su scrape sotto-raccolto
# (short-page) o cap-troncato. Il dealer rifa il conto: piu' comparabili di quanti dichiari = credibilita'
# (= prodotto) morta al primo contatto. SECONDO danno: non farti BLOCCARE da AS24.it (perdi la fonte).

## SEQUENZA (3 sessioni, NON una - non comprimere, no PARTIAL):
##   S273 = ITEM A (calibrazione) [+ ITEM B se avanza budget]
##   S274 = ITEM C (1 dossier reale end-to-end) - richiede 1 input reale da Luke
##   S275 = ITEM D (STATE.md) - housekeeping, NON gatea Day-1

## ITEM A (S273) - CALIBRAZIONE: lo scrape completo dice se il gate e' mercato o artefatto
Gate empirico DoD#4(ii). Famiglia vetrina (BMW Serie 3 2021), scrape ESAUSTIVO:
- "esaustivo" = fatto terminale = PAGINA VUOTA raggiunta SENZA cap (rimuovi max_pages per QUESTA run,
  override results_per_page=1 come S264, locale, non-mutante via object.__setattr__).
- CAVEAT RATE-LIMIT (verifica PRIMA di lanciare, su codice reale): results_per_page=1 = ~325 richieste;
  le costanti di produzione (DAILY_LIMIT=30, sleep, Semaphore) possono bloccare la run O farti bloccare
  da AS24.it. Riconcilia: run deliberata one-off, con throttle, FUORI dal daily-limit ma SENZA martellare.
  Se il rischio-blocco e' reale, FERMA e segnala a Luke prima di bruciare l'accesso.
- Ricomputa la tabella S264 (L0..L3, N per famiglia) sul pool NON troncato.
- FALSIFICA o conferma: 330i resta NO_VERDICT a config esatta, o era il cap? min_n=8 regge sui numeri completi?
- Persisti il pool esaustivo come NUOVA fixture committata.
- Ri-gira test_s271_render_artifact: ricomputa i bound da solo (by design) -> resta verde sulla nuova
  fixture; se il verdetto 330i cambia, il suo PDF cambia: NON e' regressione, e' il test che si risolve.
  Documenta il delta.
ESITO: sai se i verdetti sono veri sul mercato, non su una fetta. Chiudi a 60%.

## ITEM B (S273 se avanza, senno' S273-bis) - DEMO: canonico o campione? (DECISIONE LUKE prima di codice)
I 2 PDF in tests/dossiers_s268/ sono CAMPIONI (esempi di resa) o il DOSSIER CANONICO che mostrerai?
- Campione -> nessuna azione (il test rigenera in tempdir).
- Canonico -> assert in test_s271 "demo committato == rigenerato (timestamp a parte)": un drift
  codice-vs-PDF-mostrato viene preso. (L'incidente di sovrascrittura S272 prova che driftano.)

## ITEM C (S274) - UN DOSSIER REALE END-TO-END = il candidato Day-1
INPUT DA LUKE (se assente -> CC parca BLOCKED-ON-LUKE-INPUT e FERMA, non inventa):
- 1 annuncio DE reale (URL + prezzo + spec: modello/trim/anno/km/alimentazione/drivetrain).
  Sourcing manuale. NON automatizzare il sourcing per Day-1.
CC poi, in PRODUZIONE reale (NON fixture):
- Scrape COMPLETO AS24.it dei comparabili per QUELLA config esatta (results_per_page=1, fino a pagina
  vuota, no cap, throttle come ITEM A: e' UN'auto, lento-ma-completo te lo puoi permettere una volta).
- prezzo_de REALE (annuncio Luke) al posto dell'illustrativo.
- Genera il dossier reale -> render-verify pypdf E lettura umana dell'artefatto (lo stesso rituale che ha
  preso il Frankenstein): banda, verdetto, riga d'onesta', margine-intervallo coerenti e onesti SU DATO VERO?
ESITO: il primo dossier reale, verificato come artefatto. Questo porti a Day-1.

## ITEM D (S275) - STATE.md align (GATED Gate E) - housekeeping, ULTIMO, NON gatea Day-1
[invariato: pre-check hand-edit vs refresh.sh (memoria S243); Rule 1d backup-per-stat; diff-first; slug
Gate E si genera al primo Edit; allinea header S245->S272 + BLOCKED-ON DoD#4(ii)]. Falla quando comoda.

## INVARIATO
- NON allargare scope (no fix short-page-28-portali, no mobile.de, no automazione sourcing = tutti
  SCALING, non Day-1). NON delegare a subagent task atomici. system python3, MAI .venv.
  Output E2E > /tmp/s273.txt. Chiudi a 60% context. No PARTIAL.
- ITEM C dipende da Luke che fornisce 1 auto reale: dipendenza VOLUTA (sourcing a mano = edge di
  dominio), non un buco. Non automatizzare il sourcing per partire.
