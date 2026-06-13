════════════════════════════════════════════════════════════════════════════
 REPORT SESSIONE — S273-cont · ARGOS · 2026-06-13
 Branch: s210/audit-master-plan · Commit: e6b564e (pushato su origin)
 Obiettivo: ITEM A / ADD-2 — rendere fidabile il pool di mercato IT prima di
 fidarsi della calibrazione 330i/320d (gate DoD#4-ii verso Day-1).
════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────
1. ESITO IN UNA RIGA
────────────────────────────────────────────────────────────────────────────
ADD-2 NON chiuso, ma DISINNESCATO un errore di rotta: la diagnosi del brief
(over-collection = bug dedup) era falsa. La causa vera e' strutturale (loop
pre-vincolato) + il "totale di mercato" dichiarato da AS24 e' INSTABILE per un
A/B test. Tutte le fixture esistenti sono inquinate. Niente calibrazione finche'
non si fissa il pool. Lavoro parziale onesto committato. No PARTIAL: handoff pieno.

────────────────────────────────────────────────────────────────────────────
2. EVIDENZE E2E (dati reali, non narrazione)
────────────────────────────────────────────────────────────────────────────

[E1] PROBE pagina 1 — AS24 espone i totali nel __NEXT_DATA__
  Comando: fetch singolo URL fixture (BMW Serie 3 2019-2023, sort=standard, IT)
  URL:  https://www.autoscout24.it/lst/bmw/3er-(alle)?atype=C&cy=I&...&sort=standard&...
  Output reale (/tmp/s273_add2_out.txt, /tmp/s273_add2b.txt):
     HTML len            = 787931 bytes
     JSON-LD listing pag1 = 0      (strategia 1 non rende piu' nulla -> usa __NEXT_DATA__)
     parse_listings() pag1 = 19
     pageProps.numberOfResults = 416
     pageProps.numberOfPages   = 22
     pageProps.numberOfOcsResults = 0
  -> Pool IT dichiarato dalla query = ~416 su 22 pagine. NON >770.

[E2] BUILD esaustivo con override get_total_pages — over-collection RIPRODOTTA
  Comando: python3 -m tools.scripts.build_it_fixture  (DEEP_PAGES=60)
  Log reale (/tmp/s273_build.log):
     "Pagine totali rilevate: 54"          <- get_total_pages a pag.1 = 54 (NON 22!)
     "Pagina 1/54: 19 listing (19 totali unici)"
     "Pagina 22/54: 20 listing (343 totali unici)"
     "Pagina 59/54: 11 listing (834 totali unici)"   <- gira OLTRE il "54"
     "Pagina 60/54: 11 listing (834 totali unici)"
     "Completato BMW Serie 3: 834 listing in 60 pagine"
  -> Due fatti: (a) il loop ignora il clamp e arriva a 60; (b) il totale dichiarato
     e' 54 qui contro 22 nel probe di 6 minuti prima, STESSA URL.

[E3] CONFRONTO che prova l'instabilita' (A/B test)
     probe 13:1x : numberOfPages = 22 , numberOfResults = 416
     build 13:10 : get_total_pages = 54
     pageProps contiene il flag: isEuWideCountExperimentActive
  -> AS24 alterna conteggio IT vs EU-wide tra richieste. Il "totale" non e' un
     fatto terminale stabile.

[E4] STATO REPO a fine sessione
     git commit e6b564e (3 files, +116/-4) pushato 40ea9ac..e6b564e
     fixture over-collected 834 RIMOSSA (era additiva _s273.json, mai committata)
     PDF demo tests/dossiers_s268/ restaurati da Luke (git pulito)
     Pre-commit ARGOS: Python syntax OK, checks passed

────────────────────────────────────────────────────────────────────────────
3. ANALISI ROOT CAUSE (perche' over-collection 770 e 834)
────────────────────────────────────────────────────────────────────────────
base_scraper.py:310  ->  for page_num in range(1, max_pages + 1):
base_scraper.py:335  ->      if total_pages < max_pages: max_pages = total_pages

Il range() e' costruito UNA volta con max_pages iniziale (=DEEP_PAGES=60). La
riassegnazione di max_pages dentro il loop NON ricostruisce il range -> cambia
solo la variabile usata nel LOG ("Pagina 59/54"). Il loop fa sempre 60 iterazioni.
Oltre l'ultima pagina IT reale, AS24 serve listing di PADDING/recommendation con
id NUOVI: il dedup-by-id (:364) li accetta -> il pool si gonfia (343 a pag.22 ->
834 a pag.60). Il break short-page :374 (dedup raw-vs-unico citato dal brief) e'
IRRILEVANTE: non viene mai raggiunto prima del cap.

CONSEGUENZA SULLE FIXTURE:
   325 (committata, DEEP_PAGES=20)  -> troncata (20/22 pagine ~ ma gia' con padding)
   770 (verifica S273)              -> over-collected (cap 50)
   834 (build S273-cont)            -> over-collected (cap 60)
Nessuna = pool IT vero. Pool IT vero stimato ~416 (lettura 22-pagine del probe).

────────────────────────────────────────────────────────────────────────────
4. RIFLESSIONI BASATE SUI DATI (non opinioni)
────────────────────────────────────────────────────────────────────────────
R1. "Pool di mercato" NON e' una grandezza assoluta: e' definito dal portale e
    oggi e' soggetto a un A/B (IT vs EU-wide). Il prodotto ARGOS vende una banda
    "prezzi mercato IT". Se la banda poggia su un totale che il portale stesso fa
    oscillare 416<->? e che include padding EU-wide, la banda non e' robusta.
    Implicazione Day-1: la banda va calcolata su listing FILTRATI per country=IT,
    non sul conteggio dichiarato. Il filtro country diventa load-bearing, non
    cosmetico. (Da verificare sui dati: il padding ha davvero country!=IT?)

R2. Il brief aveva una diagnosi precisa ma sbagliata (dedup raw-vs-unico). Seguirla
    alla lettera avrebbe portato a "fixare :374" — un fix inutile che avrebbe
    lasciato l'over-collection intatta e prodotto l'ennesima fixture gonfia
    creduta vera. Il dato (log E2) ha smentito il piano. Lezione operativa: il
    terminatore va VALIDATO sul log della scrape reale, mai dedotto dal codice a
    mente. (Coerente con vincolo #10: output verificato > verosimile.)

R3. Il fix corretto tocca base_scraper.py = 28 portali. A budget di fine sessione
    NON si tocca un file condiviso load-bearing: rischio di rompere scraper che
    oggi funzionano (CLAUDE.md S157). Spostato a S273-cont2 con no-regression test
    su 1 portale DE come gate. Questa e' la scelta sicura, non la lenta.

R4. Costo-zero rispettato: nessuna libreria, nessun servizio. Il dato (numberOfPages)
    era gia' nell'HTML che lo scraper scarica — l'abbiamo solo letto.

────────────────────────────────────────────────────────────────────────────
5. NEXT PROMPT — S273-cont2 (copia-incolla a inizio sessione)
────────────────────────────────────────────────────────────────────────────
Leggi .claude/REPORT_S273_cont.txt e .claude/REPORT_SESSIONE_S273cont.txt.
Branch s210/audit-master-plan. Fonte verita' = codice + git + log scrape, NON chat.

STEP (ordine non comprimibile):
1. FIX loop-bound base_scraper.py: il range(1, max_pages+1) e' pre-vincolato ->
   il clamp get_total_pages e' no-op. Aggiungi, DOPO aver processato la pagina:
   `if total_pages is not None and page_num >= total_pages: break`. Mantieni il
   break short-page :374. No-regression: gira 1 scrape su 1 portale DE noto e
   verifica che n_listing NON crolli a zero e che si fermi all'ultima pagina vera.

2. NEUTRALIZZA l'instabilita' EU-wide (decidi sui DATI, non a mente):
   - Confronta 2 risposte pagina-1 e guarda isEuWideCountExperimentActive + i
     listing[].country: il padding oltre pag.~22 ha country!=IT?
   - Opzione (a): forza il conteggio IT (header/cookie che disattiva l'experiment).
   - Opzione (c) ROBUSTA: ignora il totale dichiarato; termina dopo 2-3 pagine
     consecutive con ZERO nuovi listing_id IT; FILTRA il pool a country=IT.
   Documenta quale scegli e perche' (cambia il significato della banda).

3. Ricostruisci la fixture vera (path _s273.json) col terminatore scelto.
   Atteso ~400-450 listing IT, pagina-finale reale raggiunta (non il cap).

4. ADD-1: ricomputa tabella L0..L3 COMPLETA sul pool vero (non solo 330i). Le
   famiglie liquide (320d xDrive, 318d) toccano N>=8 a config esatta L0/L1?
   Falsifica/conferma: 330i ancora NO_VERDICT? min_n=8 regge?

5. ADD-4: leggi le label header+riga-banda dai 2 PDF rigenerati da test_s271
   (pypdf, gia' installato), NON dal grep (e' cieco, stringa costruita dinamica).
   Se dicono "mercato Italia"/"Banda mercato IT" -> rinomina "Fascia prezzi
   richiesti AS24.it" + assert anti-drift in test_s271 + riga-limite "Fascia su
   prezzi RICHIESTI (annunci), non di transazione".

6. Re-test (test_it_distribution_fixture al nuovo path + test_s271 5/5) -> commit.
   POI ITEM B (demo canonico vs campione = DECISIONE LUKE) e ITEM C (1 dossier
   reale, richiede 1 auto DE reale fornita da Luke).

PENDENTE LUKE / CC:
- gate_e overwrite_sot-dc04f63aaf APPROVATO. RESTA (prima azione S274): CC ri-fa
  l'Edit della riga-indice in MEMORY.md (il file-memoria topic e' gia' scritto).

INVARIATO: system python3 mai .venv. No scope creep oltre il fix #1. ITEM C
dipende da 1 auto reale di Luke (dipendenza voluta). Chiudi a 60%. No PARTIAL.
════════════════════════════════════════════════════════════════════════════
