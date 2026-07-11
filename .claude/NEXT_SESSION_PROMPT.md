════════════════════════════════════════════════════════════
NEXT SESSION — ARGOS — HARVESTER DEALER FB: DEEP-EXTRACT (fix INCERTA→IN-TARGET)
════════════════════════════════════════════════════════════

STATO CHIUSURA (sessione 2026-07-11, context 60%)
- UNITÀ 1 = CANDIDATI (non PROMOSSO). Harvester scritto, Big-Sur-verificato,
  RUN eseguito su account Profile 12. 0 IN-TARGET su 3 province.
- Commit: a2f50da (modulo) + commit output pilota + questo handoff.

FIX BIG SUR RIUSABILE (già nel modulo, VERIFICATO):
- Playwright node bundlato = minos 13.5 → dyld crash su macOS 11.7.
- Soluzione: PLAYWRIGHT_NODEJS_PATH=/usr/local/bin/node (system node minos 11.0)
  + channel="chrome" (no download Chromium). NON ri-litigare.

AUTH FB (VERIFICATO):
- Account scraping = FB uid 61582178245756 (account bare, sacrificabile).
- Loggato in Chrome "Profile 12" (google=ilcombeeretrasher). NB: STESSO uid del
  profilo Default → l'identità FB è la stessa a prescindere dal profilo Chrome.
- Lanciare con: --chrome-profile "Profile 12".

DIAGNOSI ONESTA (perché 0 IN-TARGET — NON è il canale):
- Il canale TROVA dealer: 49 Pagine concessionarie a cap basso (Milano13/Roma15/
  Napoli21), categoria confermata 27/30.
- IL COLLO è il detail-scraper: legge solo /about (body 333-1434 char = scarno)
  → telefono 4/30, città 0/30, sito 1/30, modelli 0/30 → tutto INCERTA.
- CAUSE: (a) modelli Tier A/B stanno nei POST/foto, non in /about;
         (b) telefono/sito/indirizzo stanno nel blocco Contatti/Intro (DOM profondo
            o vista m.facebook.com), non nel testo /about letto ora.

PROSSIMA UNITÀ (deep-extract in tools/recon/harvest_dealers_fb.py):
1. scrape_page_detail: leggere ANCHE il feed post (scroll basso) e scansionare il
   testo post per keyword Tier A/B → popola modelli_osservati.
2. Contatti: m.facebook.com/<slug>/about o sezione about_contact_and_basic_info
   per telefono/sito/indirizzo strutturati.
3. Ri-run pilota 3 province, STESSA SOGLIA: >=3 IN-TARGET nuovi con telefono in
   >=1 provincia → PROMOSSO → poi UNITÀ 2 (docs/briefs/SINTESI_DEALER_FB.md).
4. Fonte-B PagineGialle: già implementata, si attiva sola sugli IN-TARGET.

VINCOLI INVARIATI: G-ZEROCOST · PUSH VIETATO (S278) · Gate E protetto (MEMORY/
DECISIONS/PLAN/*.db/CLAUDE) · output no-overwrite per provincia (1d) ·
riconteggio-madre da disco · accept-edits OFF (rispondi '1').

PENDING GATE E (sessione precedente): index memory FB = packet
overwrite_sot-dc04f63aaf. Da aggiornare a PROMOSSO: reference_fb_harvest_auth.md
(aggiungere --chrome-profile "Profile 12" + PLAYWRIGHT_NODEJS_PATH).
════════════════════════════════════════════════════════════
