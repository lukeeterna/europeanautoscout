# FONTI_MANDATARI — anagrafe nazionale mandatari auto (ATECO 45.11.02 + 45.19.02)

> Ricognizione fonti GRATUITE per costruire un'anagrafe di mandatari/intermediari auto in Italia.
> Sessione READ-ONLY: solo GET pubblici, ZERO contatto imprese, ZERO acquisti/abbonamenti (G-ZEROCOST).
> Generato: 2026-07-10 · branch s210/audit-master-plan.
> **Autorità dei conteggi = pagina letta live (URL citato).** Dato non letto direttamente = marcato `[NON VERIFICATO]`.

---

## 1. Mapping ATECO 2007 → 2025 (VERIFICATO live da CC su codiceateco2025.it)

Storia classificazione: ATECO 2007 → ATECO 2022 (stessi codici 6 cifre nel settore 45) → **ATECO 2025** (in vigore 1° gen 2025, operativa 1° apr 2025).

**La corrispondenza NON è 1:1 — è 1→3** (i vecchi codici sono stati smontati separando ingrosso da dettaglio usato/nuovo). Entrambi i codici 2007 risultano **OBSOLETO** in ATECO 2025.

| ATECO 2007 | Descrizione (verbatim) | Successori ATECO 2025 (verbatim) |
|---|---|---|
| **45.11.02** | "Intermediari del commercio di autovetture e di autoveicoli leggeri (incluse le agenzie di compravendita)" | **46.18.41** "Attività di intermediari del commercio all'ingrosso di automobili e autoveicoli leggeri" · **47.92.21** "Attività di servizi di intermediazione per il commercio al dettaglio specializzato di autoveicoli e motocicli di seconda mano" · **47.92.31** "Attività di servizi di intermediazione per il commercio al dettaglio specializzato di autoveicoli, esclusi articoli di seconda mano" |
| **45.19.02** | "Intermediari del commercio di altri autoveicoli (incluse le agenzie di compravendita)" | **46.18.42** (ingrosso altri autoveicoli) · **47.92.21** (come sopra) · **47.92.31** (come sopra) |

- Fonte letta live (CC, WebFetch): https://codiceateco2025.it/45.11.02 · https://codiceateco2025.it/45.19.02
- Fonte ufficiale primaria (NON letta — XLSX binario): ISTAT "Corrispondenza bidirezionale 2025 vs 2022" → https://www.istat.it/wp-content/uploads/2025/02/Corrispondenza-bidirezionale-2025-vs-2022-IT.xlsx (pagina indice: https://www.istat.it/notizia/la-tabella-di-corrispondenza-tra-le-classificazioni-ateco-2025-e-ateco-2022/). Il match successori 2025 sopra è verificato su codiceateco2025.it, **[NON VERIFICATO in incrocio sul XLSX ISTAT]** — se serve prova ufficiale, aprire il file e cercare "45.11.02"/"45.19.02" nella colonna 2022.

**Implicazione operativa**: un'anagrafe attuale (post-migrazione) NON si interroga più su 45.11.02/45.19.02 (ora a zero), ma sui **cinque** codici 2025 successori: 46.18.41, 46.18.42, 47.92.21, 47.92.31.

---

## 2. Directory web gratuite — conteggi e ACCESSIBILITÀ

### 2a. codiceateco2025.it — ACCESSIBILE (letto live)
Espone il conteggio **nazionale** per codice e data. **NON** espone breakdown regione/provincia, **NON** espone i record delle singole imprese.

| Codice | Data rilevamento | N. imprese | URL |
|---|---|---|---|
| 45.11.02 | 06/04/2025 | **5.175** | https://codiceateco2025.it/45.11.02 |
| 45.11.02 | 22/05/2025 | **5.193** | https://codiceateco2025.it/45.11.02 |
| 45.11.02 | 08/11/2025 | 0 (migrati ai codici 2025) | " |
| 45.19.02 | 06/04/2025 | **166** | https://codiceateco2025.it/45.19.02 |
| 45.19.02 | 22/05/2025 | **164** | https://codiceateco2025.it/45.19.02 |
| 45.19.02 | 08/11/2025 | 0 (migrati) | " |

Totale pre-migrazione (apr 2025): **≈ 5.341 imprese** sui due codici 2007 a livello nazionale.

### 2b. registroaziende.it — NON ACCESSIBILE (Cloudflare bot-wall)
Espone (da cache Google) breakdown per regione/provincia + schede singole imprese — MA:
- WebFetch → **HTTP 403**.
- Browser reale (Playwright) → pagina "Esecuzione della verifica di sicurezza" (Cloudflare challenge, Ray ID `a1924c7baa34ee76`). Bloccato anche da browser.
- URL: https://registroaziende.it/ateco/45.11.02 · https://registroaziende.it/ateco/45.19.02
- **Non aggirabile zero-cost senza tecniche di bypass anti-bot** (fuori scope: sarebbe evasione, il mandato ammette solo GET pubblici non aggressivi).

### 2c. tuttodati.it → tuttodati.com — NON ACCESSIBILE (redirect rotto)
- `tuttodati.it/ateco/45.11.02` → 301 → `www.tuttodati.com/ateco/45.11.02` → **HTTP 404**. Percorso ATECO non risolvibile.

### 2d. Atoka (atoka.io) — ESCLUSO
Freemium a pagamento con ricerche molto limitate → viola G-ZEROCOST. Non testato.

**Sintesi §2**: l'unica directory gratuita machine-accessibile (codiceateco2025.it) dà **solo totali nazionali**, senza geografia né record per-riga. Le directory che darebbero il drill-down provinciale e le singole imprese (registroaziende.it, tuttodati) sono **bloccate** (Cloudflare / 404).

---

## 3. Open data ufficiali — censimento (nessun download eseguito)

| Dataset | Fonte / URL | Copertura geo | Granularità ATECO | Formato | Verdetto |
|---|---|---|---|---|---|
| Imprese Attive per Territorio/Settore/Tempo | CCIAA Marche via dati.gov.it — https://www.dati.gov.it/dataset/imprese-attive-in-italia-per-territorio-settore-ateco-e-tempo-frequenza-mensile · CSV https://opendata.marche.camcom.it/data/Stock-Imprese-Attive-Italia.csv | Tutte le province/regioni IT | **Solo SEZIONE (1 lettera, es. "G")** — NON 6 cifre | CSV/JSON, CC BY 4.0 | Inservibile per isolare 45.11.02: granularità troppo grossa |
| ISTAT ASIA (DICA_ASIAUE1P) | http://dati.istat.it/Index.aspx?DataSetCode=DICA_ASIAUE1P | Comuni | **2 cifre (divisione 45)** — NON 6 cifre `[NON VERIFICATO su pagina]` | Web/export | Insufficiente (divisione, non sottocategoria) |

**Conclusione §3**: **nessun open data ufficiale gratuito espone il livello a 6 cifre ATECO** necessario per isolare i mandatari (45.11.02/45.19.02 o successori). Il massimo gratuito è sezione (G) o divisione (45).

---

## 4. Fallback a pagamento (una riga, NON indagato)

Esiste l'elenco ufficiale a 6 cifre ATECO per provincia: **Telemaco / Registro Imprese (InfoCamere)** — https://www.registroimprese.it · https://telemaco.infocamere.it. Richiede registrazione + diritti di segreteria. **Costi NON indagati; attivabile solo su decisione esplicita di Luke (G-ZEROCOST).**

---

## 5. Limiti dichiarati per fonte (sintesi)

| Fonte | Gratuita | Machine-accessibile | Breakdown provinciale | Record per-riga (denom./comune/P.IVA) |
|---|---|---|---|---|
| codiceateco2025.it | Sì | Sì | **No** | **No** |
| registroaziende.it | Sì | **No (Cloudflare)** | Sì (da browser umano) | Sì (da browser umano) |
| tuttodati | Sì | **No (404)** | ? | ? |
| Open data CCIAA/ISTAT | Sì | Sì | Sì (ma solo sezione/divisione) | **No** |
| Telemaco/InfoCamere | **No (paid)** | Sì | Sì | Sì |

---

## 6. VERDETTO FATTIBILITÀ UNITÀ 2 (pilota per-riga 3 province) — coi numeri davanti

Il pilota UNITÀ 2 richiede: estrazione **per-riga** (denominazione · comune · P.IVA · URL sorgente) da **≥2 directory gratuite**, + dedup, + verifica a campione. Sulla base di §2–§3:

- **Nessuna fonte gratuita machine-accessibile espone record per-riga a 6 cifre ATECO.** codiceateco2025.it dà solo totali nazionali; open data solo sezione/divisione.
- Le uniche fonti gratuite con dettaglio per-riga (registroaziende.it, tuttodati) sono **bloccate** (Cloudflare bot-wall verificato anche da browser; 404) — accessibili solo a un umano dietro browser, non estraibili a batch senza bypass anti-bot (fuori scope).
- Non è nemmeno determinabile "la provincia più densa" da fonte gratuita: **nessuna gratuita espone il breakdown provinciale** dei due codici.

→ **La copertura gratuita è INSUFFICIENTE per un'anagrafe per-riga enterprise-grade.** UNITÀ 2 come specificata NON è eseguibile zero-cost con le fonti trovate. Vedi BLOCCO-DECISIONE sotto.

---

## 7. BLOCCO-DECISIONE per Luke (scelta di scope, non tecnica)

Con i numeri di §2–§6, l'anagrafe per-riga gratuita è bloccata. Le strade (decisione di Luke):

- **A) Fonte ufficiale a pagamento** (Telemaco/InfoCamere): dà 6 cifre × provincia × record. Viola G-ZEROCOST → serve sì esplicito + verifica costi.
- **B) Raccolta manuale-umana** dalle directory dietro browser (registroaziende.it apribile a mano): Luke/operatore copia le pagine-provincia; zero-cost ma non automatizzabile e lento.
- **C) Ridefinire la fonte-primaria dei mandatari**: non partire dall'anagrafe ATECO ma dallo scraping già in casa (i portali auto ARGOS già mappati) per identificare intermediari attivi sul web — allineato a UNITÀ 2 "classificazione mandatario-attivo-web", ma cambia il punto di partenza.

Nessuna delle tre è tecnica: è scope. Non procedo oltre senza decisione.

---

## 8. PILOTA per-riga — esiti provincia (aggiornato per provincia lavorata)

> Enrichment P.IVA via lookup pubblici per-nome (reportaziende.it / ufficiocamerale.it / directory Infocamere-derivate). Validazione checksum con python-stdnum. Verifica-campione seed dichiarato. ZERO contatto, ZERO costi, ZERO bypass 403/Cloudflare.

### 8a. Potenza (PZ) — 2026-07-10 — **PROMOSSA ad anagrafe**
- **Righe**: 42 · **con P.IVA**: 22 (4 pre-esistenti + 18 nuove da subagent research, tetto 45 fetch)
- **P.IVA valide (checksum stdnum it.iva)**: **22/22** (0 invalide, 0 duplicati)
- **NON-ARRICCHIBILI**: 20 righe (motivi per-riga nel JSON: nessun match / tetto fetch / franchising senza P.IVA propria / solo sito aziendale)
- **Verifica-campione** (seed=42, 10 righe): **9 SI / 0 NO / 1 NON-VERIFICABILE** (Quality Cars — nessun match PZ). Soglia ≥8/10 **RAGGIUNTA**.
  - **CAVEAT**: cross-check eseguito su `ufficiocamerale.it` (dati Infocamere, stessa base Registro Imprese) perché la ricerca gratuita `registroimprese.it` è JS-only, non GET-fetchabile → NON aggirata. Fonte-proxy equivalente, da ratificare Luke.
- **Distribuzione classi** (euristica dichiarata: fuori-target=officina/carrozzeria/moto/ricambi/noleggio · probabile-agente=brand ufficiale/franchising · solo-anagrafe=P.IVA valida senza footprint web · non-classificabile=no P.IVA):
  - solo-anagrafe: **19** · fuori-target: **3** (Sanza Motors 47.83.10 moto · Carrieri Sandro carrozzeria · Officina & Service) · non-classificabile: **20** · probabile-agente-di-concessionaria: 0
  - **Footprint linguistico** ("su commissione"/"cerchiamo per te"/"su ordinazione"): NESSUNO raccolto — il testo dei siti per-riga NON è stato harvest-ato in questa passata → classe "mandatario-attivo-web" non assegnata (assenza dato, non assenza fenomeno).
- **File**: `data/recon/mandatari/potenza.json` (campi nuovi: piva · piva_valida · stato · ateco_rilevato · fonte_enrichment · classificazione · status)

### 8b. Treviso (TV) — 2026-07-11 — **PROMOSSA ad anagrafe**
- **Righe**: 40 · **con P.IVA**: 34 (0 pre-esistenti + 34 nuove da subagent research, tetto 45 fetch dichiarato)
- **P.IVA valide (checksum stdnum it.iva)**: **34/34** (0 invalide, 0 duplicati) → **85% delle 40 righe** con P.IVA valida
- **NON-ARRICCHIBILI**: 6 righe (idx 17 Auto-Da-MD&A, 18 Autodue, 26 Autosalone Teot, 27 Casagrande, 30 P.S. Group, 37 Magro Antonio — motivi: nessun match / 403-404 / persona fisica deceduta)
- **Verifica-campione** (seed=71, 10 righe idx 0,2,4,6,8,22,28,31,35,38): **10 SI / 0 NO / 0 NON-VERIFICABILE**. Soglia ≥8/10 **RAGGIUNTA**.
  - Indipendenza per-riga: fonte_B ≠ fonte_enrichment (Infocamere-derivate: reportaziende / bilancioaziende / misterimprese / prontoimprese). Esito verbatim per riga nel JSON `verifica_campione.esito_verbatim`.
- **Distribuzione classi** (euristica dichiarata: fuori-target=ATECO 45.20.x officina o nome soccorso/servizio-acquisto fuori-TV · probabile-agente=brand ufficiale nel nome o dealer SpA storico · solo-anagrafe=P.IVA valida ATECO commercio senza footprint web · non-classificabile=no P.IVA):
  - solo-anagrafe: **22** · probabile-agente-di-concessionaria: **6** (Campaner-Peugeot/Citroen · Automarca SpA · Carraro SpA · Autobavaria-BMW · Trevisauto-Saab · Basso-Ford) · fuori-target: **6** (Autostar 45.20.1 · Bianchi 45.20.1 · Activa 45.20.9 · Noicompriamoauto 82.99.09 sede-MI · Lezier 45.20.1 · Autosoccorso) · non-classificabile: **6**
  - **% con telefono**: **0%** (campo telefono NON harvest-ato in questa passata — assenza dato, non assenza fenomeno)
  - **Footprint linguistico** ("su commissione"/"cerchiamo per te"): NESSUNO raccolto → classe "mandatario-attivo-web" non assegnata (backlog).
  - **ATECO-mandatario esplicito trovati**: idx 9 Nicola Auto e idx 13 A27 espongono **46.18.41** (successore 2025 di 45.11.02 "intermediari") — unici 2 con codice-intermediario puro.
- **CAVEAT qualità**: idx 2 Sotreva Auto = P.IVA ora intestata a **EM 27 SRL in liquidazione** (ragione sociale cambiata); idx 22 Noicompriamoauto sede legale **Milano**; idx 28 Emmecar sede legale **Mantova** (presenza operativa Conegliano); idx 24 Autobavaria in liquidazione; idx 25 Trevisauto fallita (proc. 135/2018).
- **File**: `data/recon/mandatari/treviso.json` (campi: piva · piva_valida · stato · ateco_rilevato · fonte_enrichment · telefono_presente · classificazione · status=PROMOSSA)

### 8c. Roma (RM) — 2026-07-11 — **CANDIDATI** (enrichment completo; promozione gated su verifica-campione)
- **Righe**: 28 · **con P.IVA**: 22 (tutte nuove da subagent research; tetto fetch dichiarato per batch: 12+12+22)
- **P.IVA valide (checksum stdnum it.iva)**: **22/22** (0 invalide) → **78,6%** delle 28 righe · **distinte**: 19 (idx 18-21 = stessa entità `01559111008` MERCEDES-BENZ ROMA S.P.A., 4 filiali PagineGialle → dedup)
- **NON-ARRICCHIBILI**: 6 (idx 8 Automobili Zupi no-match ragione sociale · 10 Auto Giovanni P.IVA senza URL camerale · 11 Maurmotors nessuna scheda · 13 Micro Car Roma Sud P.IVA senza URL · 25 Panichi Auto 101 · 26 Rp Auto Srls)
- **⚠️ CAVEAT PROVENIENZA (rilevante per la promozione)**: 12 P.IVA da **serp-snippet/websearch** (ufficiocamerale.it ha risposto **403** al fetch diretto → numero letto dallo snippet, NON da pagina GET-fetchata); 10 da **scheda-diretta** (impresaitalia/fatturatoitalia/reportaziende/visura.pro). Checksum 22/22 OK ma **match-entità NON verificato indipendentemente** in questa passata.
- **Verifica-campione**: **NON eseguita** — sessione chiusa a context ~62% (vincolo #7) dopo l'enrichment. È l'**unico gate** rimasto per la promozione → prossima sessione.
- **Distribuzione classi** (euristica dichiarata, STATO di prima classe): solo-anagrafe **11** · probabile-agente-di-concessionaria **5** (idx 18-21 Mercedes-Benz Roma SpA/Autotorino + 23 Angelo Fiori SpA Stellantis/Renault) · fuori-target **5** (idx 1 G.M. Autoricambi 45.32 ricambi · 4 P.Auto Service officina BMW/Mini · 14 Autoservice Masciotra autosoccorso · 15 AFT Romani carrozzeria 45.20.2 · 27 Essedi noleggio camper) · **non-operativa 1** (idx 9 Centro Auto Roma SRL **in liquidazione**, esclusa dal target) · non-classificabile **6** · mandatario-attivo-web **0**
- **% con telefono**: **39%** (11/28) · **% non-operative**: **3,6%** (1/28)
- **Footprint linguistico**: NON harvest-ato (backlog, come Potenza/Treviso)
- **Nota geo**: idx 2 Autovillage sede legale Monterotondo (RM), idx 10 Auto Giovanni a Lunghezza (RM) — entrambi **dentro** provincia RM → nessun geo_flag di esclusione (a differenza dei casi MI/MN di Treviso)
- **File**: `data/recon/mandatari/roma.json` (campi: piva · piva_valida · stato · ateco_rilevato · telefono · fonte_enrichment · ragione_sociale_camerale · comune_sede_legale · geo_flag · provenienza_qualita · classificazione + `enrichment_meta` + `status=CANDIDATI`)

> **SINTESI PILOTA 3 PROVINCE**: NON eseguita in questa sessione (UNITÀ 3 richiedeva context ≤60% e Roma promossa; nessuna delle due condizioni). Passa alla sessione che chiude la verifica-campione Roma. Dati comparativi già pronti: Potenza 42/22 PROMOSSA, Treviso 40/34 PROMOSSA, Roma 28/22 CANDIDATI.
