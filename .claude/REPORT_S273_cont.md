S273-cont — ITEM A / ADD-2 — HANDOFF su context-gate (58%, no PARTIAL)
Branch s210/audit-master-plan. Fonte verita': codice + git + /tmp/s273_build.log + /tmp/s273_add2*.txt.

== FINDING PRINCIPALE (ribalta sia S273 che il piano ADD-2) ==
AS24 ESPONE i totali nel __NEXT_DATA__.props.pageProps (stesso blob gia' parsato per i listing):
  numberOfResults, numberOfPages, numberOfOcsResults.
MA due problemi rendono il terminatore (a) NON affidabile da solo:

(1) ROOT CAUSE VERA dell'over-collection — bug base_scraper, NON il dedup.
    base_scraper.py:310  `for page_num in range(1, max_pages + 1)` : il range e' PRE-VINCOLATO
    alla creazione del for. Il clamp a :335-336 (`max_pages = total_pages`) riassegna la variabile
    DOPO che il range esiste -> cambia solo il DISPLAY del log ("Pagina 59/54"), NON il numero di
    iterazioni. => get_total_pages clampa il log ma NON ferma la paginazione. La scrape gira sempre
    fino a DEEP_PAGES e raccoglie il PADDING che AS24 serve oltre l'ultima pagina reale (id NUOVI,
    ~16-20/pag, il dedup-by-id non li ferma). Questo spiega 770 (S273) e 834 (S273-cont) vs pool ~416.
    NB: l'ADD-2 del brief attribuiva l'over-collection al dedup raw-vs-unique (:374). Falso: il :374
    e' irrilevante perche' il loop non termina mai prima del cap. La causa e' il range pre-bound.

(2) IL TOTALE DICHIARATO E' INSTABILE tra richieste (A/B experiment).
    Probe ore 13:1x: numberOfResults=416, numberOfPages=22.
    Build  ore 13:10 (minuti dopo, STESSA query/URL): get_total_pages=54.
    In pageProps c'e' `isEuWideCountExperimentActive` -> AS24 alterna conteggio IT vs EU-wide.
    => "numberOfPages dichiarato" NON e' un fatto terminale stabile. Terminatore (a) cade.

== CONSEGUENZE ==
- Le fixture 325 (committata), 770 (verif S273), 834 (build S273-cont) sono TUTTE inquinate da
  over-collection di entita' diversa. NESSUNA e' il pool IT vero. Pool IT reale ~416 (lettura 22-pag).
- La fixture 834 prodotta stamattina e' stata RIMOSSA (era it_dist_..._s273.json, additiva mai committata).
- La calibrazione 330i/320d resta INVALIDA: va rifatta su pool IT vero, dopo i fix sotto.

== STATO ALBERO (modifiche NON committate, progresso parziale corretto-ma-insufficiente) ==
- tools/scrapers/autoscout_scraper.py : AGGIUNTO override get_total_pages() che legge
  numberOfPages/numberOfResults dal __NEXT_DATA__ + stash _last_declared_results/_pages.
  CORRETTO (legge dato reale) ma INSUFFICIENTE: non ferma il loop (vedi bug #1) e legge un totale
  instabile (vedi #2). Tenere, ma NON basta.
- tools/scripts/build_it_fixture.py : OUT->path nuovo _s273.json, DEEP_PAGES 20->60, meta arricchito
  (declared_results/pages, terminator, sort=standard, price_field). Path/meta OK; il dato prodotto NO.
- ADD-3 GIA' CHIUSO: sort="standard" (relevance), nessun price-bias. Dichiarato in meta. Niente reorder.
- ADD-4 NON fatto (label header/banda sul render + eventuale rename "Fascia prezzi richiesti AS24.it").

== RESUME S273-cont2 — ORDINE ==
1. FIX loop-bound in base_scraper.py (tocca 28 portali -> cautela, tieni il break short-page :374).
   Sostituisci il range pre-bound con terminazione che RISPETTA il clamp: dopo aver processato la
   pagina, `if total_pages is not None and page_num >= total_pages: break`. Test no-regressione su 1
   portale DE. Questo da solo elimina il padding SE total_pages fosse stabile.
2. NEUTRALIZZA l'instabilita' EU-wide (#2). Opzioni da valutare su codice/dato reale (NON a mente):
   (a) bloccare l'experiment: header/cookie che forza conteggio IT (ispeziona cosa cambia tra le 2
       risposte 22 vs 54 — confronta pageProps.isEuWideCountExperimentActive e i listing.country);
   (b) terminatore (c) ROBUSTO indipendente dal totale: STOP dopo K=2-3 pagine consecutive con ZERO
       nuovi listing_id IT, FLAG hard-cap se n si ferma a numero tondo. + filtra per country=IT i
       listing raccolti (il padding EU-wide ha country!=IT? VERIFICARE sui dati).
   Decidi (a) vs (c) sui DATI, documenta quale e perche' (cambia il significato del pool).
3. Ricostruisci la fixture vera (path _s273.json), POI ADD-1: tabella L0..L3 completa, falsifica 330i.
4. ADD-4: leggi label header+riga-banda dai 2 PDF rigenerati da test_s271 (pypdf); se "mercato Italia"
   -> "Fascia prezzi richiesti AS24.it" + assert anti-drift in test_s271 + riga-limite "prezzi RICHIESTI".
5. Re-test (test_it_distribution_fixture punta al nuovo path; test_s271), commit fixture+codice+REPORT.
6. POI ITEM B (demo canonico vs campione, DECISIONE LUKE) e ITEM C (1 dossier reale, input Luke).

== 2 AZIONI LUKE UNA-TANTUM (ancora pendenti dal brief S272) — lancia via '!' ==
  ! python3 .harness/gate_e.py approve overwrite_sot-dc04f63aaf   (poi CC ri-fa l'Edit indice MEMORY)
  ! git checkout -- tests/dossiers_s268/                          (PDF demo: diff = solo timestamp)

== INVARIATO ==
system python3 mai .venv. No scope creep (no short-page-28-portali oltre il fix #1, no mobile.de, no
sourcing auto). ITEM C dipende da 1 auto reale fornita da Luke. Chiudi a 60%. No PARTIAL.
