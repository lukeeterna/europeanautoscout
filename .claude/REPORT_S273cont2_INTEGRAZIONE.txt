════════════════════════════════════════════════════════════════════════════
 S273-cont2 — INTEGRAZIONE VALIDATA (Luke judge + CC code-check) · 2026-06-13
 Additiva agli STEP di .claude/REPORT_S273_cont.txt. Questi correggono ordine,
 gate, architettura. Fonte: codice + log E2/E3 sessione S273-cont.
════════════════════════════════════════════════════════════════════════════

VERDETTO CC sulla critica Luke (motivato sui dati):
- A/B instabilita' (22 vs 54): VALIDATO (E3 + flag isEuWideCountExperimentActive).
- CORR-1 (STEP1 = pulito-in-apparenza, ~32 pag padding a total=54): VALIDATO (log E2).
- CORR-2/3 (filtro geo nel layer ARGOS): VALIDI ma AFFILATI -> vedi FINDING-NUOVO sotto.
- CORR-4 (ADD-1 = prima misura pulita del bedrock, non ricalcolo): VALIDATO.
- CORR-5 (padding comprime lo spread, opposto a ieri): VALIDO COME IPOTESI, NON misurato.
  Da quantificare in S273-cont2 (mediana prezzo padding vs IT-core). NON spacciare per fatto.

★ FINDING-NUOVO CC (cambia l'implementazione di CORR-2/3):
  Il campo `country` salvato NON e' un discriminatore utilizzabile.
  - base_scraper.py:361  lst.country = self.config.countries[0]  -> forza "IT"
  - autoscout_scraper.py:723  _json_ld_to_listing(..., country=country) = country del PORTALE
  => OGNI listing autoscout24_it ha country="IT" a prescindere dalla sede reale.
  Il ramo CORR-2 "SI -> filtro country funziona" e' MORTO in partenza: un test
  "ZERO country!=IT" passerebbe SEMPRE -> falsa sicurezza.
  Il discriminatore geo va ESTRATTO dal raw __NEXT_DATA__ (item seller/location/zip)
  PRIMA dell'overwrite, e PERSISTITO come campo nuovo (es. listing_location_country
  o seller_zip). Il parser legge gia' seller_data (:695) ma NON la sua sede -> sotto-task.

ORDINE CORRETTO S273-cont2 (non comprimibile):
0. PROBE GEO (PRIMA di tutto, decide tutto): fetch pagina 1 e pagina ~40, estrai dal
   raw pageProps.listings[] un campo location/zip/countryCode per listing + prezzo.
   Domande terminali sui DATI:
     (a) esiste un campo geo affidabile nel raw? (se no: trovarlo prima di proseguire)
     (b) i listing oltre pag.~22 sono geo!=IT? (CORR-2: SI->discrimina; NO->il padding
         e' IT-servito-EU-wide, serve altro discriminatore)
     (c) mediana prezzo padding vs IT-core: il padding COMPRIME il comp? (CORR-5 quantificato)
1. FIX loop-bound base_scraper (SOLO guardrail anti-runaway, 28 portali, no-regress 1 DE):
   dopo process pagina  if total_pages is not None and page_num >= total_pages: break.
   NON e' la definizione del pool (total_pages instabile). Tieni break short-page :374.
2. PERSISTI il campo geo trovato in (0a) dal raw (parser autoscout, prima dell'overwrite).
3. FILTRO comparabili = geo==IT nel layer COMP ARGOS (it_market_price/selezione comp),
   NON in base_scraper. Completezza = "fetch piu' profonda aggiunge ZERO nuovi listing_id
   geo==IT" (zero-new sul set FILTRATO, post-hoc) -> robusto anche se padding INTERLACCIATO.
   Il totale dichiarato dal portale = SEMPRE non-fidato.
4. Ricostruisci fixture vera (path _s273.json) col terminatore zero-nuovi-IT + filtro geo.
5. ADD-1: tabella L0..L3 COMPLETA sul pool pulito (320d xDrive, 318d toccano N>=8 a L0/L1?).
   Falsifica 330i / min_n=8. Documenta se REGGE o si rivede (puo' essere BUONA notizia).
6. ADD-4 al render (non grep): label header/banda -> "Fascia prezzi richiesti AS24.it" + assert.
7. GATE nel repo (test fixture-validation): RIFIUTA un pool non-fidato. Asserzioni:
   - terminatore dichiarato = "zero-nuovi-IT" (NON "totale-portale" ne' "cap");
   - ZERO listing con geo!=IT sul CAMPO GEO REALE (non lo country overwritten) -> else FAIL;
   - metadato "completezza-validata: +N pagine = 0 nuovi IT geo" presente -> else FAIL.
8. Re-test (fixture + test_s271 5/5) -> commit + PUSH. POI ITEM B/C/D.

DECISIONE CC: niente judge (ridondante, converge), niente research (non e' stack/versioni
ma misura empirica = STEP 0). Azione = questo next-prompt. ITEM C (dossier reale) NON precede
una baseline pulita+filtrata+completezza-validata: un comp sporco fa dire "no" a un dealer su
un'auto buona (CORR-5).

PENDENTE: gate_e overwrite_sot-dc04f63aaf approvato -> CC ri-fa Edit indice MEMORY.md (1a azione).
INVARIATO: system python3 mai .venv. 60% context. No PARTIAL. Push sempre.
════════════════════════════════════════════════════════════════════════════
