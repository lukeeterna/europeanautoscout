# AUDIT E2E ARGOS — codice reale vs MASTER PLAN
> Sessione S210 · 2026-06-01 · branch `s210/audit-master-plan`
> Metodo: trust-but-verify. Ogni claim verificato su file/righe/output reali. NESSUN fix in questa sessione.
> Workspace confermato REALE: `~/Documents/combaretrovamiauto-enterprise` (path invariato).

Legenda: **[VERIFICATO]** girato/letto su dati reali · **[PARZIALE]** esiste ma incompleto/non testato · **[DA FARE]** non esiste · **[BUG NOTO]** esiste ma rotto.

---

## FASE 1 — ACQUISIZIONE DEALER

### Scraper s206 Marche + i 4 telefoni — [PARZIALE], ma il MASTER sbaglia la fonte
- `research/s206_marche_register/prospect_list.csv`: **135 righe, TUTTE `portale=autoscout24`**, 4 con telefono.
- I 4 telefoni: Dellerbastore Sas `+393343438688`, MB Motorsport `+393272785160`, Auto Simeone `+393358229775`, Ghiraldo & Autoin `+393346464547` — **tutti e 4 da AutoScout24**, non da Subito/Automobile.it.
- `EXECUTION_REPORT.md`: `subito: 0 listing`, `automobile.it: 0 listing`. **Subito/Automobile.it hanno prodotto ZERO**, non 4.

**Sono reali o artefatti di parsing su 403/404? → REALI, non artefatti. [VERIFICATO]**
- `tools/s206_marche_scraper.py:187-201`: HTTP 200 → `resp.text`; **403/503/429/altro → ritornano `""` (stringa vuota)**. Nessun parsing di pagine d'errore: una pagina 403/404 non produce mai un record.
- Telefono estratto dal campo JSON `seller.phone` in `__NEXT_DATA__` (`:420`), poi `normalize_phone()` (`:250-272`) che **accetta solo formato mobile/fisso italiano** (10 cifre `3`/`0`, o 9 cifre `3`). I 4 numeri sono `+39 33x...` validi → coerenti con campo strutturato, non con rumore di pagina.

**DELTA vs MASTER PLAN:**
1. MASTER (`STATO_COMPONENTI.md:27`): *"I 4 telefoni vengono da Subito/Automobile.it"* → **FALSO**. Vengono da AS24; Subito/Automobile.it = 0 listing.
2. MASTER: *"AS24 non espone seller.phone"* → vero in generale, ma **AS24.it ESPONE `seller.phone` per i dealer con profilo pubblico** (4 su 135). Il claim assoluto è impreciso.
3. La domanda del MASTER "controllare che non siano artefatti 403/404 PRIMA di chiamarli" → **risolta: NON sono artefatti.** Il gating 403→"" lo esclude per costruzione.

### Sales Agent automatizzato — [PARZIALE]
- ESISTE: `wa-intelligence/response-analyzer.py` (agente "AMBRA", persona `Luca Ferretti` `:67`, system prompt `:341-385`).
- KB pre-addestrata ASSEMBLATA: `wa-intelligence/argos_knowledge_base.md` (318 righe: 17 obiezioni, 5 archetipi, leve scarsità), caricata a runtime (`:260-289`).
- **NON è "automatizzato senza founder"**: pattern HITL obbligatorio — ogni risposta passa da approvazione Telegram prima dell'invio (`:13-17` "ZERO risposte automatiche").
- **n8n: ASSENTE.** Nessun workflow `.json`. Solo menzione futura in `research/s78`. Stack reale = PM2 + launchd.

**DELTA:** MASTER descrive un "sales agent automatizzato" outbound. Reale = agente **reattivo + HITL**, non un outbound autonomo. Il GATE-CAMPO (conversione su campione) resta **non validato**: 0 dealer reali contattati.

### corpus_register.md — [VERIFICATO committato, ma contenuto fuori-scopo]
- `research/s206_marche_register/corpus_register.md`, commit `5ac1214`, branch `s206/marche-register`.
- Header: **"Totale frasi estratte: 223"** (non 171), "Fonte: AutoScout24.it + Subito.it + Automobile.it".
- **DELTA contenuto:** le frasi sono frammenti-equipaggiamento AS24 troncati a metà (es. `"forgiati M doppi raggi st"`, `"LED (DI SERIE)<br />- M Drive Pro [1MB]..."`, codici-optional BMW). **NON è linguaggio-dealer conversazionale** utile per una "traccia colloquio". È un dump di liste-dotazioni.
- "Fonte AS24+Subito+Automobile.it" nell'header è **fuorviante**: tutte le citazioni reali hanno `[fonte: autoscout24]` (Subito/Automobile.it = 0).

---

## FASE 2 — CONTENUTI — [DA FARE] (coerente col MASTER)
- **Nessuna** pipeline di generazione contenuti (video/reel/caption) dentro il repo ARGOS. Nessun `build_video.py`, `generate_reel`, `video_gen` in `src/`/`tools/`.
- `build_video.py` + `storyboard.json` vivono su **FLUXION** (`/Volumes/MontereyT7/FLUXION`, fuori repo), tarati sul verticale parrucchiere, non auto-premium.
- **DELTA: nessuno** — il MASTER già lo dichiara placeholder. Riuso per ARGOS = da tarare, zero righe oggi.

---

## FASE 3 — SOURCING

### AS24 source=DE / __NEXT_DATA__ — [VERIFICATO] (ma nome parametro sbagliato nel MASTER)
- `tools/scrapers/autoscout_scraper.py`: il mercato tedesco si seleziona con **`cy=D`** (`:59` `COUNTRY_CY_PARAM`, URL `:472`), **NON `source=DE`** come scrive il MASTER (`:43`).
- Parsing `__NEXT_DATA__` ATTIVO: `:705-744`, naviga `props.pageProps.listings[]`. Funziona da IP italiano.
- **DELTA:** il meccanismo è reale; il nome del parametro nel MASTER (`?source=DE`) è errato → usare `cy=D`.

### Quanti portali REALMENTE integrati — [PARZIALE]
- `tools/scrapers/config.py` `PORTALS`: **~9-10 portali** con scraper attivo (AS24 DE/NL/BE/AT/FR/SE/IT, mobile.de, willhaben, leboncoin). Scraper concreti reali: solo `autoscout_scraper.py` + `mobile_de_scraper.py`; gli altri via `generic_scraper.py` (profili regex).
- `portal_profiles.py`: 68 `SearchProfile` regex — usabili via generic, **non testati singolarmente**.
- Subito/Automobile.it: **NON integrati** (0 in config).
- **DELTA:** `identity.md` "28 portali" = overclaim; "100+ portali" del MASTER = **target, non stato**. Coerente con la nota del MASTER.

### CoVe v4 testato su volume reale — [VERIFICATO] (MASTER è troppo prudente)
- `src/cove/cove_engine_v4.py`: soglie `DEALER_PREMIUM=0.75` (`:53`), `VIN_CHECK=0.60` (`:56`), `λ=0.25` (`:70`); formula `confidence = mu_total − lam·sigma_total − fraud_penalty` (`:658`). **Confermata.**
- `cove_tracker.duckdb` → `cove_results`: **2.955 righe**, `analyzed_at` da **2026-03-05** a **2026-05-28**.
- **DELTA:** la nota MASTER *"confermare se untested in practice"* è **superata**: ~3.000 listing reali su ~3 mesi. CoVe v4 NON è untested.

---

## FASE 4 — CERTIFICATO + SANITIZER

### Generatore certificato/dossier — [VERIFICATO]
- `tools/scripts/pdf_generator_enterprise.py`: `generate_opportunity_dossier` (`:1129`), `generate_vehicle_sheet` (`:215`) con sezioni hero/summary/scoring/"7 Criteri ARGOS Premium Verified"/financial/gallery.
- PDF reali prodotti in `/dossiers/` (es. `ARGOS_BMW_X3_2021_TEST_S192_*.pdf`). Funziona (dipende da `reportlab`, altrimenti fallback testo).
- Nota: branding "Protocollo ARGOS™" sta in `payment_handler.py`, non nel PDF (che usa "ARGOS Automotive").

### Sanitizer + plate-detection — [BUG NOTO mitigato cambiando approccio]
- Metodo: **Apple Vision OCR** (`vision_ocr.py:99-107`) + regex `_is_plate_format()` (`image_sanitizer.py:89-105`). NON cv2, NON Koushim, **NON un plate-detector europeo dedicato**.
- Il bug "watermark-URL preso per targa" è stato **abbandonato, non risolto**: S183 (`tools/scripts/s183_autogen_zones.py:94-99`) RIMUOVE la classificazione targa via Vision (fail mode faro→targa) e passa a **mascheratura deterministica della fascia inferiore ~12%**.
- **DELTA:** il MASTER dice "bug noto ancora aperto / serve modello plate-EU". Reale: la detection-targa è stata **eliminata** a favore di una copertura cieca della zona bassa. Quindi non c'è più il falso-positivo watermark, ma **non c'è nemmeno un vero plate-detector**: se la targa non è nella fascia bassa, non viene coperta. Strato fragile, da non dichiarare "fatto".
- Invocazione: **SÌ**, il sanitizer è chiamato dal generatore (`pdf_generator_enterprise.py:1197-1212` → `_sanitize_photo` `:1608`). Non è codice isolato.

### Secretazione-fonte — [VERIFICATO ma PASSIVA]
- Implementata come campo vuoto, non come gate: `VehicleData.from_opportunity()` forza `source_url=""` e `source_country="Europa"` (`:164`). Docstring "ZERO riferimenti alla location" (`:1142`, `:1246`). Filename PDF senza paese/portale.
- **DELTA:** è una **redazione passiva** (il campo non viene mai popolato), **non** uno "sblocco-dopo-pagamento". Il commento `image_sanitizer.py:13` ("source revealed ONLY after fee payment") è una regola di business **non implementata come flusso**.

---

## FASE 5 — PAGAMENTO — [PARZIALE: infra sì, GATING no]
- ESISTE: `src/marketing/payment_handler.py` (`mark_paid()` `:251`, fatture SEPA + Revolut), `comm-broker/deal_state_machine.py` (7 stati `offer_sent→...→delivered`), contratto S177/S178 via Cloudflare Worker `argos-proxy` con `sign_url` (firma digitale funzionante).
- **MANCANTE — il nodo critico:** **nessun gating "rilascio-fonte SOLO post-pagamento-confermato".** `mark_paid()` chiude il dealer in `dealer_leads` ma **non rilascia alcun campo sorgente/posizione**. La transizione `payment_confirmed → transport_scheduled` non esegue alcun rilascio-URL. Revolut link "non operativo, richiede API Revolut Business" (`:174`).
- Stack FLUXION (Stripe + Worker WebCrypto + D1 idempotenza): **non riusato** in ARGOS; valutazione di riuso ancora da fare.
- **DELTA:** il MASTER definisce questo il meccanismo che "protegge il ricavo" → **è il pezzo più scoperto.** La leva primaria del modello (secretazione-fonte sbloccata a pagamento) **NON esiste come codice**, solo come commento.

---

## DB — split-brain MacBook/iMac — [VERIFICATO, ancora presente]
- `dealer_network.sqlite` locale (root repo): tabelle `dealers` + `market_*`; **`dealers` = 18 righe; tabella `messages` ASSENTE.**
- `comm-broker/bridge.sqlite`: **vuoto** (0 tabelle).
- DB autorevole con `messages` = su **iMac**, path hardcoded in 6+ file: `wa-intelligence/deploy.sh:26-27` (`gianlucadistasi@192.168.1.2` + `app-antigravity-auto`), `validator.py:24`, `telegram-handler.py:42`, `scheduler.py:29`, `db_utils.py:12`, `dashboard/db.py:16`.
- **DELTA:** split-brain **confermato presente**. `dealers` (MacBook, 18) vs `messages` (iMac) ancora separati. Coerente con `research/s101:19`.

---

## SINTESI SECCA — dove l'handoff dice una cosa e il codice un'altra

1. **Telefoni Marche**: MASTER "4 telefoni da Subito/Automobile.it" → in realtà **tutti e 4 da AutoScout24**; Subito/Automobile.it = **0 listing**.
2. **AS24 non espone seller.phone**: assoluto falso → **AS24.it lo espone per i dealer con profilo pubblico** (4/135).
3. **Parametro sourcing**: MASTER `?source=DE` → reale **`cy=D`**.
4. **CoVe "untested in practice"**: superato → **2.955 run reali** (2026-03-05 → 05-28).
5. **Sales agent "automatizzato senza founder"**: reale = **reattivo + HITL Telegram obbligatorio**; nessun outbound autonomo, **n8n assente**.
6. **Plate-detection "bug aperto, serve modello EU"**: reale = detection-targa **rimossa** (S183), sostituita da **mascheratura cieca fascia bassa** → niente falso-positivo, ma niente vero detector.
7. **Secretazione-fonte**: MASTER la implica attiva ("rivelata dopo pagamento") → reale = **redazione passiva** (campo vuoto), **nessun gate**.
8. **GATING pagamento → rilascio fonte**: il nodo che "protegge il ricavo" → **NON esiste in codice** (solo commento). Pezzo più scoperto del sistema.
9. **corpus_register.md**: "223 frasi, fonte AS24+Subito+Automobile.it" → reale = **frammenti-dotazioni AS24 troncati**, AS24-only, **non linguaggio-dealer** per traccia colloquio.
10. **"28/100+ portali"**: reale = **~9-10 scraper attivi** + 68 profili regex non testati singolarmente; Subito/Automobile.it non integrati.
11. **Workspace**: confermato `~/Documents/combaretrovamiauto-enterprise` (path NON cambiato).
