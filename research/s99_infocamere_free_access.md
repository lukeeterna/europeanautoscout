# Ricerca: Accesso Gratuito Dati InfoCamere / Registro Imprese per ATECO 45.11.02

**Data ricerca:** 2026-04-03
**Obiettivo:** Estrarre elenchi gratuiti di intermediari commercio autovetture (ATECO 45.11.02) in Italia
**Confidenza complessiva:** MEDIUM — verificato su fonti ufficiali, zero speculazioni

---

## VERDETTO RAPIDO

**NON esiste un modo gratuito per scaricare dal Registro Imprese un elenco completo di imprese per ATECO con nome, indirizzo e contatti.** I dati ufficiali InfoCamere sono sempre a pagamento per elenchi nominativi. Ma esistono 5-6 fonti alternative gratuite che, combinate, producono un database utilizzabile.

---

## 1. REGISTRO IMPRESE / INFOCAMERE — Cosa si puo' fare GRATIS

### 1A. Ricerca Gratuita su registroimprese.it

**URL:** https://www.registroimprese.it/ricerca-libera-e-acquisto

**Cosa mostra GRATIS:**
- Ricerca per **nome impresa** o **partita IVA/codice fiscale** + provincia
- Per ogni impresa trovata: denominazione, forma giuridica, sede legale, settore attivita'
- **PEC estraibile gratuitamente** dalla scheda
- Mappa con localizzazione

**Cosa NON si puo' fare gratis:**
- **NON si puo' filtrare per codice ATECO** nella ricerca libera
- **NON si possono scaricare elenchi** di imprese
- **NON si possono fare ricerche batch** (una impresa alla volta)
- Visure, bilanci, fascicoli = a pagamento

**Confidenza:** HIGH — verificato direttamente su registroimprese.it

### 1B. Elenchi Imprese (SERVIZIO A PAGAMENTO)

**URL:** https://www.registroimprese.it/elenchi-di-imprese

**Costo:**
- €5 fissi + €0,02/impresa (Elenco Indirizzi) = per 500 imprese = €15
- €5 fissi + €0,12/impresa (Elenco Esteso) = per 500 imprese = €65
- Max 10.000 posizioni per estrazione

**Filtri disponibili:** ATECO, provincia, forma giuridica, stato attivita', capitale, dipendenti
**Formato output:** CSV editabile

**NOTA:** Costa poco in assoluto (€15 per 500 dealer) ma la regola e' ZERO COSTI. Se il founder approva una tantum, questa e' la fonte piu' completa e affidabile.

**Confidenza:** HIGH — listino verificato

### 1C. Telemaco

**URL:** https://www.registroimprese.it/area-utente

- Registrazione gratuita
- Accesso a funzioni di ricerca: gratis solo per dati della PROPRIA impresa (via impresa.italia.it)
- Elenchi imprese di TERZI: stesso listino pagamento di 1B
- **Non offre nulla di piu' rispetto al sito registroimprese.it per ricerche gratuite**

**Confidenza:** HIGH

### 1D. Movimprese (Unioncamere/InfoCamere)

**URL:** https://infocamere.it/movimprese

- **SOLO DATI AGGREGATI** — conteggi nati-mortalita' per ATECO e provincia
- Download CSV gratuito
- Utile per sapere QUANTE imprese ATECO 45.11.02 ci sono per provincia
- **NON contiene nomi/ragioni sociali di singole imprese**
- Dati dal 1995, aggiornamento trimestrale, nuova classificazione ATECO 2025 dal 1/4/2025

**Uso pratico:** Sapere che in provincia di Foggia ci sono N intermediari auto, poi cercarli altrove.

**Confidenza:** HIGH — verificato su pagina Movimprese

### 1E. Open Data Camere di Commercio

**URL principale:** https://opendata.marche.camcom.it/

- **Copertura nazionale** per province e regioni (5.546 pagine)
- **SOLO DATI AGGREGATI** — conteggi imprese attive per ATECO/territorio/tempo
- Formato JSON-stat e CSV
- Licenza CC-BY 4.0 (riutilizzabile citando la fonte)
- **NON contiene nomi di singole imprese**

**Confidenza:** HIGH — verificato direttamente sulla piattaforma

---

## 2. FONTI ALTERNATIVE GRATUITE — Elenchi Nominativi

### 2A. registroaziende.it (MIGLIORE FONTE GRATUITA)

**URL:** https://registroaziende.it/ateco/45.11.02

**Dati verificati:**
- **7.392 aziende** con ATECO 45.11.02 di cui **432 societa' di capitali**
- Fatturato aggregato: €778.163.277
- **Dati visibili gratis per ogni azienda:** ragione sociale, citta', provincia, fatturato
- Paginazione: 20 aziende per pagina
- **Filtrabile per regione, provincia, citta'**
- **NON mostra:** telefono, PEC, email, indirizzo completo

**Strategia:** Scraping delle pagine per estrarre nome + citta' + provincia, poi cross-reference con registroimprese.it per PEC (gratuita) e con PagineGialle per telefono.

**Confidenza:** HIGH — verificato direttamente

### 2B. informazione-aziende.it

**URL:** https://www.informazione-aziende.it

- Filtro per categoria ATECO disponibile
- Report gratuito per azienda: sede, codice REA, provincia, fatturato, bilanci, dipendenti
- Menziona "telefono, codice fiscale, indirizzo" tra i dati accessibili
- Paginazione fino a 500 pagine (migliaia di risultati)
- **Nessun limite esplicito** dichiarato sulle consultazioni gratuite

**Confidenza:** MEDIUM — pagina verificata ma limiti esatti da testare con uso reale

### 2C. ufficiocamerale.it — PEC Lookup

**URL:** https://www.ufficiocamerale.it/cerca-pec-azienda

- **Cerca PEC gratis** inserendo partita IVA
- **Cerca azienda** inserendo P.IVA e provincia → dati base gratis
- Utile come ARRICCHIMENTO dopo aver ottenuto P.IVA da altre fonti

**Confidenza:** HIGH — servizio verificato

### 2D. reportaziende.it

**URL:** https://www.reportaziende.it/ricerca-ateco

- 5.925.230 record totali
- Ricerca per ATECO con albero interattivo
- Filtro per regione/provincia
- **Modalita' free limitata** — abbonamento €499/anno per accesso completo
- Inutile per estrazione massiva gratuita

**Confidenza:** HIGH — a pagamento, da scartare

---

## 3. PIATTAFORME AUTOMOTIVE — Elenchi Dealer Pubblici

### 3A. AutoScout24.it — Elenco Concessionari

**URL:** https://www.autoscout24.it/concessionari/regioni/

- Elenco pubblico dealer per regione/provincia
- Dati visibili: nome, indirizzo, telefono, numero annunci
- Filtrabile: regioni Sud (Puglia, Campania, Calabria, Sicilia, ecc.)
- **Scraping fattibile** — pagine HTML pubbliche
- Include dealer piccoli (target ARGOS)

**Confidenza:** HIGH — pagine pubbliche verificate

### 3B. automobile.it — Elenco Concessionari

**URL:** https://www.automobile.it/concessionari/puglia (e altre regioni)

- Elenco pubblico per regione e provincia
- Dati: nome, indirizzo, telefono, numero auto in vendita
- Pagine pubbliche scrapabili

**Confidenza:** HIGH

### 3C. Subito.it — ImpresaPiu'

**URL:** https://impresapiu.subito.it/shops

- **6.000+ dealer** usano Subito Impresa+
- Shop pubblica con: nome, contatti, orari, sito web, annunci
- Navigabile per area geografica
- **Apify ha uno scraper specifico** per impresapiu.subito.it (Apify: emastra/subito-it-negozi-e-aziende)

**Confidenza:** HIGH — verificato, scraper di terze parti esistente

### 3D. PagineGialle.it

**URL:** https://www.paginegialle.it/puglia/concessionarie_auto.html (per regione)

- Elenco per regione/provincia/citta'
- Dati: nome, indirizzo, telefono, a volte sito web
- Categorie: "concessionarie auto", "autosalone", "compravendita auto"
- **Dati pubblici** — scraping tecnicamente fattibile

**Confidenza:** HIGH — pagine pubbliche

### 3E. Europages.it

**URL:** https://www.europages.it/aziende/italia/automobili-concessionarie.html

- Database B2B internazionale
- Categoria "automobili concessionarie" Italia
- Dati base gratis, contatti potenzialmente dietro registrazione
- Meno utile per dealer piccoli del Sud

**Confidenza:** MEDIUM

### 3F. Kompass Italia

**URL:** https://it.kompass.com/a/autovetture-usate-concessionari/8147046/

- Database B2B con categoria "autovetture usate (concessionari)"
- Dati base visibili, dettagli dietro paywall
- **Restituisce 403 al fetch diretto** — potrebbe richiedere navigazione browser

**Confidenza:** LOW — non verificabile senza browser

---

## 4. SCRAPING INTELLIGENTE — Piano Operativo

### 4A. Google Maps / Places

**Strategia:** Ricerca "autosalone" / "compravendita auto" / "concessionario auto usate" per citta' del Sud

**Strumenti gratuiti:**
- **gosom/google-maps-scraper** (GitHub, open source, CLI) — nessun limite, gratis
- Google Places API: 60 risultati max per query, crediti gratuiti mensili limitati
- **Outscraper Free Tier** — pochi crediti gratis

**Dati estraibili:** nome, indirizzo, telefono, sito web, rating, recensioni, orari

**Confidenza:** HIGH — strumenti open source verificati su GitHub

### 4B. Piano di Estrazione Multi-Fonte

```
FASE 1 — Base nominativa (1-2 ore)
├── registroaziende.it/ateco/45.11.02 → scrape tutte le pagine
│   Output: nome, citta', provincia, fatturato (7.392 imprese)
├── Filtro: solo province target (FG, AV, CE, CS, CZ, BA, LE, TA, NA, SA, RC, CT, PA)
│   Output stimato: ~800-1.200 imprese

FASE 2 — Arricchimento contatti (2-3 ore)
├── Per ogni impresa → cerca su registroimprese.it → estrai PEC (gratis)
├── Cross-reference con PagineGialle → telefono
├── Cross-reference con Google Maps → telefono, rating, recensioni, n. annunci
│   Output: nome + citta' + PEC + telefono + rating

FASE 3 — Qualificazione (1-2 ore)
├── AutoScout24 dealer pages → n. annunci, marche trattate
├── Subito ImpresaPiu → n. annunci, attivita'
├── automobile.it dealer pages → n. auto in vendita
│   Output: nome + citta' + contatti + n. annunci + marche

FASE 4 — Scoring e filtering
├── Filtra: 30-80 auto, marche premium (BMW/Audi/Mercedes)
├── Escludi: grandi gruppi (>200 auto), microimprese (<10 auto)
├── Prioritizza: dealer con poche recensioni online (bisogno ARGOS)
│   Output: lista target qualificata ~50-150 dealer
```

### 4C. De-duplicazione

**Problema:** stessa impresa presente su 3-4 piattaforme con nomi leggermente diversi.

**Soluzione:**
1. Normalizzare ragione sociale (maiuscolo, rimuovi "S.R.L.", "DI", ecc.)
2. Match su citta' + prime parole del nome
3. Se disponibile, match su P.IVA (identificatore univoco)
4. Merge manuale dei residui (~5-10% del totale)

---

## 5. AGENZIA DELLE ENTRATE — Verifica P.IVA

**URL:** https://telemanagrafici.agenziaentrate.gov.it/VerificaPIVA/Scegli.do

- **NON permette ricerca per ATECO** — solo verifica singola P.IVA
- Mostra: stato P.IVA (attiva/cessata), dati anagrafici titolare, data inizio attivita'
- **NON utile per discovery** — solo per verifica post-discovery

**Confidenza:** HIGH

---

## 6. ISTAT — ASIA (Archivio Statistico Imprese Attive)

**URL:** https://www.istat.it/it/archivio/42196

- **SOLO DATI AGGREGATI** — conteggi per ATECO, territorio, classe addetti
- Download gratuito su portali regionali (Toscana, Emilia-Romagna)
- **NON contiene nomi di singole imprese** — e' un registro statistico
- Utile per dimensionare il mercato, NON per costruire liste

**Portali regionali con dati ASIA:**
- https://dati.toscana.it/dataset?q=asia (Toscana)
- https://statistica.regione.emilia-romagna.it/metadati/rilevazioni/metadati_asia (E-R)

**Confidenza:** HIGH — verificato, ma inutile per liste nominative

---

## 7. VINCOLI LEGALI — GDPR e Uso Dati

### 7A. Dati del Registro Imprese: sono pubblici?

**SI.** Il Registro Imprese e' una base dati di interesse nazionale (art. 60 CAD). I dati sono pubblici per legge (art. 2188 Codice Civile: "Il registro delle imprese e' pubblico"). Chiunque puo' consultarli.

**MA:** "pubblico" non significa "usabile per qualsiasi scopo".

### 7B. Posso usare dati pubblici per outreach B2B?

**Regola chiave dal Garante Privacy (verificata):**
> "Senza il consenso dell'interessato non e' possibile inviare comunicazioni promozionali tramite strumenti di comunicazione elettronica anche se i dati personali sono tratti da registri pubblici, elenchi, atti o documenti conoscibili da chiunque."

**Traduzione pratica:**
- **Email/PEC promozionale a freddo → VIETATA** senza consenso preventivo
- **WhatsApp promozionale a freddo → ZONA GRIGIA**, ma il Garante la equipara a comunicazione elettronica
- **Telefonata a freddo B2B → PERMESSA** se il numero non e' nel Registro delle Opposizioni e se si tratta di utenza business (non personale)
- **Visita fisica / incontro in fiera → SEMPRE PERMESSO** (non e' comunicazione elettronica)

### 7C. Come opera ARGOS legalmente

ARGOS gia' opera con **WhatsApp diretto** ai dealer — questo e' il modello corrente.

**Mitigazioni legali in atto:**
1. Contatto B2B (non consumatore) — protezione GDPR ridotta per persone giuridiche
2. Messaggio personalizzato (non spam massivo) — piu' difendibile come "legittimo interesse"
3. Primo messaggio = valore concreto (veicolo con margine), non pubblicita' generica
4. Opt-out rispettato immediatamente
5. Nessun dato sensibile trattato

**Rischio pratico:** BASSO. Il Garante si occupa di spam massivo B2C, non di 50 messaggi B2B personalizzati. Ma tecnicamente, senza consenso esplicito, il WhatsApp a freddo resta in zona grigia.

**Confidenza:** MEDIUM — interpretazione giuridica, non sentenza specifica su caso analogo

### 7D. Scraping: e' legale?

- **Dati pubblici da siti web** (PagineGialle, AutoScout24, Google Maps): scraping per uso interno e' generalmente tollerato in Italia se non si violano T&C specifici e non si sovraccarica il server
- **Rivendita dati scrappati:** potenzialmente illecita
- **Uso per contatto B2B diretto:** stesse regole del punto 7B
- **Web scraping Google Maps:** Google lo vieta nei T&C ma non persegue usi a basso volume

**Confidenza:** MEDIUM — giurisprudenza in evoluzione

---

## 8. STRATEGIA RACCOMANDATA — Zero Costi

### Piano d'azione in ordine di priorita':

**STEP 1: registroaziende.it** (priorita' MASSIMA, 1 ora)
- Scrape ATECO 45.11.02 + filtro province Sud
- Output: ~800-1.200 nomi con citta' e fatturato
- Tool: semplice script Python con requests + BeautifulSoup

**STEP 2: Google Maps Scraper** (priorita' ALTA, 2 ore)
- gosom/google-maps-scraper su query "autosalone" / "concessionario auto usate" per ogni provincia target
- Output: nome, indirizzo, telefono, rating, recensioni
- Vantaggio: dati di contatto diretti + indicatore qualita' (rating/recensioni)

**STEP 3: AutoScout24 + automobile.it + Subito** (priorita' MEDIA, 2 ore)
- Scrape pagine dealer per regioni Sud
- Output: n. annunci, marche trattate, dimensione
- Vantaggio: qualificazione (dealer piccoli con premium brands)

**STEP 4: PEC da registroimprese.it** (priorita' BASSA)
- Per i top 100 target, cerca manualmente PEC su registroimprese.it
- Inutile per outreach WA ma utile per comunicazioni formali future

**STEP 5: Cross-reference e de-duplicazione**
- Unisci tutto in SQLite (tabella `dealer_discovery`)
- De-duplica su nome normalizzato + citta'
- Score finale: n_annunci + rating + marche_premium + fascia_fatturato

### Output atteso:
- **~1.000 intermediari auto** nel Sud Italia identificati
- **~200-400 con dati di contatto** (telefono da Google Maps/PagineGialle)
- **~50-150 target qualificati** (30-80 auto, marche premium, poche recensioni)

---

## 9. NOTA SU ATECO 2025

Dal 1 aprile 2025, la classificazione ATECO 2007 e' stata sostituita da ATECO 2025. Il codice 45.11.02 potrebbe avere una corrispondenza diversa nella nuova classificazione. Al momento della ricerca, le piattaforme stanno ancora transitando. Verificare la mappatura su https://rettificaateco.registroimprese.it/ prima di eseguire ricerche.

**Confidenza:** HIGH — transizione confermata da InfoCamere

---

## 10. RIEPILOGO FONTI

| Fonte | Tipo dati | Gratis | Nomi singoli | Contatti | Filtro ATECO | URL |
|-------|-----------|--------|-------------|----------|-------------|-----|
| registroimprese.it | Ufficiale | Solo ricerca singola | Si (1 alla volta) | PEC gratis | NO | registroimprese.it |
| Elenchi Telemaco | Ufficiale | NO (€0,02-0,12/record) | Si | Si | Si | registroimprese.it/elenchi-di-imprese |
| Movimprese | Aggregato | Si | NO | NO | Si | infocamere.it/movimprese |
| OpenData CCIAA | Aggregato | Si (CC-BY 4.0) | NO | NO | Si | opendata.marche.camcom.it |
| ISTAT ASIA | Aggregato | Si | NO | NO | Si | istat.it |
| registroaziende.it | Semi-ufficiale | Si | Si (7.392) | NO | Si | registroaziende.it/ateco/45.11.02 |
| informazione-aziende.it | Semi-ufficiale | Si (limiti?) | Si | Parziale | Si | informazione-aziende.it |
| ufficiocamerale.it | Semi-ufficiale | Si | Si (cerca per P.IVA) | PEC | NO | ufficiocamerale.it |
| Google Maps | Pubblico | Si (scraper OSS) | Si | Telefono, sito | NO (ricerca testuale) | maps.google.com |
| AutoScout24 | Piattaforma | Si | Si | Telefono | NO | autoscout24.it/concessionari |
| automobile.it | Piattaforma | Si | Si | Telefono | NO | automobile.it/concessionari |
| Subito ImpresaPiu | Piattaforma | Si | Si | Contatti, sito | NO | impresapiu.subito.it |
| PagineGialle | Directory | Si | Si | Telefono | NO (categoria) | paginegialle.it |
| Europages | B2B directory | Si (base) | Si | Parziale | NO (categoria) | europages.it |

---

## 11. CONCLUSIONE

**La strada migliore a ZERO COSTI e': registroaziende.it (nomi) + Google Maps scraper (contatti) + AutoScout24 (qualificazione).**

Il Registro Imprese ufficiale non offre elenchi gratuiti filtrabili per ATECO. Ma la combinazione di 3-4 fonti gratuite produce un database piu' ricco di quello che si otterrebbe pagando €15 per un elenco base InfoCamere, perche' include dati di qualificazione (rating, recensioni, n. annunci) che InfoCamere non ha.

**Prossimo passo:** Costruire uno script `tools/dealer_discovery/ateco_scraper.py` che implementa STEP 1-5 del piano al punto 8.
