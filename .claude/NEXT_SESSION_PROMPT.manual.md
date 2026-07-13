════════════════════════════════════════════════════════════
NEXT SESSION — ARGOS — INDIVIDUAZIONE DEALER: PORTALE-FIRST (FB automatico CHIUSO)
════════════════════════════════════════════════════════════

DECISIONE FOUNDER (2026-07-13) — non ri-litigare
- Canale HARVESTER FB AUTOMATICO = CHIUSO. Pratiche borderline ESCLUSE:
  scraping contenuto protetto FB, evasione anti-bot (undetected-chromedriver,
  proxy rotazionali), OCR-per-aggirare-scramble. Motivo con dato: pilota 0/30
  IN-TARGET; il corpo-post è scramblato da Meta (misura di protezione); i tool
  anti-bot risolvono il muro sbagliato (login/IP), non lo scramble → esposizione
  ToS/legale/reputazionale per rendimento ~0. Anti-fossato per un business
  fondato sulla FIDUCIA del dealer.
- FB resta SOLO superficie di scoperta MANUALE (occhi umani), mai automatica.

METODO SCELTO — individuazione target a scala, etica e verificabile
- INVERTI L'IMBUTO: parti dallo STOCK, non dalle Pagine.
- Un annuncio premium (X5/Cayenne/GLE/Q7/…) venduto da un dealer IT su portali
  auto pubblici (AutoScout24/Subito/Automobile.it) È un dealer IN-TARGET, con la
  prova nell'annuncio. GROUP-BY-SELLER + dedup → centinaia di dealer qualificati,
  ciascuno già con il proprio stock premium.
- Supera i 2 difetti del pilota FB: pool inquinato eliminato (chi vende su portale
  auto è dealer auto per costruzione); modelli eliminati dallo scramble (il modello
  è nel dato strutturato dell'annuncio).

MANDATO PRIMARIO PROSSIMA SESSIONE: FIX-RS + RICONCILIA-PROVENIENZA + U2
- Portare "portale-first → group-by-seller" come metodo di individuazione target.
- RICONCILIA-PROVENIENZA = aggancio contatto: telefono NON sempre esposto sul
  portale (AS24 seller.phone reveal-gated, VERIFICATO memoria S208) → contatto da
  fonte seconda pulita (PagineGialle / Google categoria "concessionaria auto" /
  sito proprio del dealer, robots permettendo).
- NESSUNA SPECULAZIONE su "pronto": ESISTE già = scraper portali CoVe (orientati
  alla singola listing). DA COSTRUIRE (U2) = group-by-seller (listing→anagrafica
  dealer) + riconciliazione contatto. Estrarre lo scope esatto di FIX-RS /
  RICONCILIA-PROVENIENZA / U2 DAL DISCO (git/BACKLOG/docs) prima di scrivere codice.

STATO CODICE FB (da gestire allo scrub S278)
- Modulo tools/recon/harvest_dealers_fb.py vive su a2f50da → c669239 → 6673ce9
  (deep-extract eseguito: raw_signal 333-1434 → 1600-8100, ma modelli 0/30 per
  scramble). Branch s210/audit-master-plan AHEAD 244, MAI pushato = nulla è pubblico.
- Allo scrub S278 (pre-push): marcare il modulo per ESCLUSIONE dalla history,
  insieme ai secret. Lezioni conservate in BACKLOG: #FB-HARVEST-POOL-INQUINATO,
  #FB-POST-TEXT-OFFUSCATO.

VINCOLI INVARIATI: G-ZEROCOST · PUSH VIETATO (S278) · Gate E protetto (MEMORY/
DECISIONS/PLAN/*.db/CLAUDE) · riconteggio-madre da disco · accept-edits OFF ('1').
════════════════════════════════════════════════════════════
