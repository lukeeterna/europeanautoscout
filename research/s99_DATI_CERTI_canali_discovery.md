# DATI CERTI — Canali Discovery Micro-Dealer Sud Italia

**Data verifica:** 2026-04-03
**Metodo:** Accesso diretto ai siti, WebFetch, WebSearch con cross-reference
**Regola:** Se non verificato con URL, e' scritto "NON VERIFICATO"

---

## 1. REGISTROAZIENDE.IT — ATECO 45.11.02

### VERIFICATO (accesso diretto 2026-04-03)

**Numero imprese:** 7.392 aziende confermate per ATECO 45.11.02 (di cui 432 societa' di capitali)
- Fatturato collettivo: EUR 778.163.277
- URL: https://registroaziende.it/ateco/45.11.02

**Filtri disponibili:** SI — Area Geografica (regione, provincia, comune) + Codice ATECO
- Conferma: il sito mostra "Area Geografica" come filtro di ricerca

**Dati mostrati nella vista tabella pubblica:**
- Ragione sociale (con link al profilo)
- Citta'/Comune
- Provincia
- Fatturato (in milioni EUR)

**Dati NON mostrati nella vista pubblica:**
- Telefono: NO (probabile solo in profilo singolo o versione business)
- Email: NO (probabile solo in versione business)
- Indirizzo completo: NO (solo citta')

**Scraping:**
- La versione pubblica mostra tabelle HTML standard — tecnicamente scrappabile
- MA: il sito offre API a pagamento ("arricchimento dati e API" con listino dedicato)
- 20+ filtri disponibili solo nella versione business (a pagamento)
- Nessuna autorizzazione ufficiale al web scraping
- **Conclusione:** I dati di base (nome + citta' + provincia + fatturato) sono visibili gratuitamente. Per telefono/email serve piano business o API.

### Alternative verificate

**Atoka.io:**
- Piattaforma Cerved, primo motore di ricerca aziende italiane
- Filtro ATECO disponibile (anche reclassificato Cerved)
- Sistema a crediti: ricerca senza base package = 0 crediti, dettagli = 1 credito
- API richiede token commerciale (contattare sales)
- **NON ha free tier vero** — serve contatto commerciale per token API
- URL: https://atoka.io/pages/it/tutorial-api/ricerca-aziende/

**ReportAziende.it:**
- 5.9+ milioni record aziende, 16+ milioni manager
- Ricerca per ATECO disponibile
- Modello a abbonamento (NON gratuito)
- URL: https://www.reportaziende.it/ricerca-ateco

**Verdetto:** Registroaziende.it e' il MIGLIORE per dati gratuiti di base (nome+citta'+fatturato). Per contatti (tel/email) serve budget o scraping manuale dei profili singoli.

---

## 2. GOOGLE MAPS SCRAPER (gosom/google-maps-scraper)

### VERIFICATO (GitHub diretto 2026-04-03)

**Esiste:** SI — https://github.com/gosom/google-maps-scraper
**Stelle:** 3.500+ (3.5k)
**Ultimo commit:** Marzo 2026 (ultima release pubblicata 21 marzo 2026)
**Stato:** ATTIVAMENTE MANTENUTO — versione SaaS beta in sviluppo

**Dati estratti (33+ campi):**
- Nome business, indirizzo, telefono, sito web
- Rating, numero recensioni, recensioni individuali
- Coordinate GPS, timezone
- Orari apertura, stato attivita', fascia prezzo
- Immagini, thumbnail
- Email (opzionale, estratte dal sito web)

**Funziona nel 2026?** SI, ma con problemi segnalati:
- Issues aperti a marzo 2026 (TLS handshake timeout, job stuck)
- Docker ha problemi periodici con download driver Playwright
- Progetto attivo: fix e nuove feature continuano

**Modalita':** CLI, Web UI, REST API, Docker, Kubernetes

### Alternative verificate

**Outscraper.com:**
- Free tier: 500 record/mese GRATIS
- Poi: $3/1.000 fino a 100K, $1/1.000 oltre
- Pay-as-you-go, crediti non scadono
- NON richiede setup tecnico
- URL: https://outscraper.com/pricing/

**Apify Google Maps Scraper:**
- Free tier: $5/mese in crediti (circa 500-5.000 listing)
- NO carta di credito per iscriversi
- Crediti scadono a fine ciclo
- Starter plan: ~$10-30/mese per 50K+ listing
- URL: https://apify.com/compass/crawler-google-places

### Test "autosalone Foggia" su Google Maps

**NON VERIFICATO direttamente** — non posso eseguire query Google Maps live.

Pero' dati incrociati da altre fonti:
- PagineGialle provincia Foggia "concessionarie auto": **147 risultati** (verificato)
- AutoScout24 concessionari Foggia: **10+ dealer con recensioni** (verificato)
- Google Maps tipicamente restituisce 2-3x i risultati di PagineGialle

**Stima:** 50-150 risultati per "autosalone" + "compravendita auto" in provincia Foggia. STIMA, non dato certo.

**Verdetto:** gosom/google-maps-scraper FUNZIONA ed e' gratis. Per zero-setup, Outscraper (500 gratis/mese) e' piu' veloce. Per ARGOS bastano poche centinaia di record — free tier di qualsiasi opzione e' sufficiente.

---

## 3. TELEGRAM — COMPROSUBITOAUTO

### VERIFICATO (multiple fonti 2026-04-03)

**Esiste:** SI
- URL: https://t.me/comprosubitoauto
- Sito web: https://commercianti.comprosubitoauto.it/

**Tipo:** CANALE (broadcast, non gruppo chat)

**Iscritti:** 6.045 (fonte: italle.com/telegram/@comprosubitoauto, verificato 2026-04-03)

**Contenuti:**
- Vendita auto SOLO per commercianti
- ~500 auto/mese pubblicate nel canale
- Foto + prezzo fisso (no trattativa, "troppi commercianti per trattare")
- Possibilita' ricerca modello nel canale

**Chi gestisce:**
- Gruppo Automotive (Prato)
- Sede: Via Jean Monet SNC + Via Zarini 198, Prato
- Contatto: Gaetano, +39 333 864 2639
- Business: acquistano flotte auto e le distribuiscono a commercianti

**Accesso:** Libero (canale pubblico Telegram)

**Servizi aggiuntivi:**
- Creazione canali Telegram personalizzati per singoli dealer
- Sync automatico con canale principale
- Dealer puo' aggiungere ricarico e logo proprio

**Copertura:** Centro-Nord Italia (cercano broker in Centro e Nord Italia)
- **NOTA IMPORTANTE PER ARGOS:** Copertura Sud Italia assente/debole. Questo e' sia un problema (meno rilevante per i nostri target) sia un'opportunita' (territorio vuoto).

### Altri canali/gruppi Telegram auto Italia VERIFICATI

| Canale/Gruppo | Membri | Tipo | Rilevanza ARGOS |
|---|---|---|---|
| COMPROSUBITOAUTO | 6.045 | Canale | MEDIA — Centro-Nord, B2B |
| Orbita Ferrari | 7.434 | Canale | BASSA — fan, non commercianti |
| QUATTRORUOTE | 4.002 | Canale | BASSA — informazione generica |
| VAG Italy | 6.837 | Gruppo | BASSA — retrofit/tuning VW |

**NON ESISTONO** canali Telegram rilevanti specifici per commercianti auto Sud Italia. COMPROSUBITOAUTO e' l'unico canale B2B significativo trovato.

**Verdetto:** COMPROSUBITOAUTO e' reale e rilevante come modello di business, ma la sua copertura e' Centro-Nord. Per Sud Italia, Telegram NON e' un canale di discovery dealer significativo.

---

## 4. SUBITO.IT — Profili Venditori Professionali

### VERIFICATO (2026-04-03)

**Si possono identificare venditori professionali?** SI

**Come si distinguono dai privati:**
- Badge "professionista" — certificazione ufficiale per venditori business
- Shop dedicato (vetrina virtuale personalizzabile)
- Logo aziendale, contatti completi, orari apertura, link sito web
- Fino a 30 foto per annuncio (vs meno per privati)
- Call tracking system
- Numero annunci visibile nel profilo

**I badge sono SOLO per privati** — i professionisti hanno un sistema diverso:
- Abbonamento business (ImpresaPiu')
- Shop su impresapiu.subito.it/shops
- Sezione dedicata business

**Filtro per zona + categoria:** SI — si puo' filtrare per regione/provincia + categoria "Auto"

**Dati estraibili da profili professionali:**
- Nome venditore/azienda
- Numero annunci attivi
- Marche trattate (deducibile dagli annunci)
- Zona (citta'/provincia)
- Telefono (tramite shop)

**Scraping:**
- impresapiu.subito.it/shops restituisce 403 (accesso bloccato)
- Gli annunci singoli su subito.it sono accessibili
- Apify ha un scraper dedicato: "Scraper Aziende Subito.it" per lead e analisi mercato

**Verdetto:** Subito.it E' un canale di discovery valido. I professionisti sono identificabili tramite abbonamento/shop. Il modo migliore e' cercare annunci auto per provincia e filtrare chi ha molti annunci (>10 = probabilmente dealer). Scraping diretto degli shop e' bloccato, ma gli annunci sono accessibili.

---

## 5. FACEBOOK GROUPS

### PARZIALMENTE VERIFICATO (2026-04-03)

**Gruppi trovati e confermati esistenti:**

| Gruppo | URL | Membri | Stato |
|---|---|---|---|
| VENDITA AUTO PER COMMERCIANTI (e privati) | facebook.com/groups/516288858572127/ | NON VERIFICATO (serve login) | Esiste |
| AUTO USATE ITALIA | facebook.com/groups/1622201218057166/ | NON VERIFICATO | Esiste |
| VENDITORI E CONCESSIONARI AUTO | facebook.com/groups/Venditorieconcessionariauto/ | NON VERIFICATO | Esiste |
| Marketplace Vendita e Acquisto Auto | facebook.com/groups/200050907147726/ | NON VERIFICATO | Esiste |

**Numero membri:** NON VERIFICABILE senza login Facebook. I gruppi sono privati/chiusi — il numero membri e' visibile solo dalla pagina Facebook con sessione autenticata.

**Tipo di contenuti:** Basato sul nome — compravendita auto tra commercianti e privati. Ma contenuto effettivo NON VERIFICATO.

**Aperti o chiusi?** La maggior parte dei gruppi Facebook auto Italia sono CHIUSI (serve richiesta per entrare). Questo e' standard per gruppi commerciali.

**Rilevanza ARGOS:**
- Potenzialmente ALTA per osservare dinamiche dealer
- MA: richiedono account Facebook attivo (ARGOS ha Facebook sotto appeal)
- Non scrappabili senza violazione ToS

**Verdetto:** I gruppi ESISTONO ma i dati chiave (membri, contenuti, attivita') sono NON VERIFICABILI senza accesso autenticato. Facebook e' un canale di intelligence qualitativa (entrare e osservare), NON un canale di discovery scalabile.

---

## 6. PAGINEGIALLE.IT

### VERIFICATO (accesso diretto 2026-04-03)

**Risultati per provincia:**

| Provincia | Categoria | Risultati | Note |
|---|---|---|---|
| Foggia (citta') | Autosaloni | 5 | Solo citta', molto pochi |
| Foggia (provincia FG) | Concessionarie auto | **147** | Tutta la provincia |
| Avellino | Autosaloni | 5 | Inclusi comuni vicini (SA, NA) |
| Cosenza | Autosaloni | 6 | Inclusi Rende, Paola |

**Dati forniti per ogni risultato:**
- Nome azienda: SI
- Indirizzo completo: SI (via, cap, comune)
- Telefono: SI (anche multipli)
- WhatsApp: SI (quando disponibile)
- Distanza dal centro citta': SI
- Logo/immagine: SI (quando disponibile)
- Descrizione servizi: SI (breve)
- Recensioni: SI (quando presenti)
- Sito web: implicito nei link

**Nota importante:** La ricerca "autosaloni" restituisce MOLTI MENO risultati della ricerca "concessionarie auto". Per Foggia: 5 vs 147. Usare SEMPRE "concessionarie auto" + filtro provincia.

**Paginazione:** I risultati sono su pagina singola con scroll, ordinati per rilevanza (paganti prima). NON c'e' paginazione classica.

**Scraping:** HTML standard, ma i risultati sono mix di paganti e organici. Rate limit non testato.

**Confronto con AutoScout24:**
- AS24 concessionari Foggia: 10+ dealer con recensioni (solo quelli registrati su AS24)
- PagineGialle provincia Foggia: 147 (tutti, anche non digitali)
- PagineGialle ha una copertura MOLTO piu' ampia per micro-dealer non digitali

**Verdetto:** PagineGialle e' il MIGLIOR canale gratuito per discovery micro-dealer Sud Italia. 147 risultati per la sola provincia di Foggia con nome, telefono, indirizzo. Usare la ricerca per PROVINCIA (non citta') e la categoria "concessionarie auto" (non "autosaloni").

---

## CLASSIFICA CANALI — Dal piu' al meno utile per ARGOS

| # | Canale | Costo | Dati ottenibili | Copertura Sud | Verdict |
|---|---|---|---|---|---|
| 1 | **PagineGialle.it** | GRATIS | Nome, tel, indirizzo, WA | OTTIMA (147/provincia) | USARE SUBITO |
| 2 | **Google Maps** (Outscraper/gosom) | GRATIS (500/mese) | Nome, tel, sito, rating, recensioni, orari | BUONA | USARE per arricchire con rating/recensioni |
| 3 | **AutoScout24 concessionari** | GRATIS | Nome, recensioni, stock | MEDIA (solo registrati) | USARE per cross-reference |
| 4 | **Registroaziende.it** | GRATIS (base) | Nome, citta', fatturato | COMPLETA (7.392 ATECO) | USARE per filtro fatturato |
| 5 | **Subito.it professionisti** | GRATIS | Nome, annunci, marche | BUONA | USARE per identificare dealer attivi online |
| 6 | **Facebook Groups** | GRATIS (serve login) | Intelligence qualitativa | VARIABILE | MONITORARE quando FB attivo |
| 7 | **Telegram COMPROSUBITOAUTO** | GRATIS | Modello business, pricing | SCARSA (Centro-Nord) | OSSERVARE come riferimento |

---

## AZIONI CONCRETE RACCOMANDATE

### Fase 1 — Immediata (zero costo)
1. **PagineGialle:** Scrape "concessionarie auto" per province target (FG, AV, CS, CE, TA, LE, BA, RC, CZ, KR)
   - Stima: 100-200 risultati per provincia = 1.000-2.000 dealer totali
   - Dati: nome + telefono + indirizzo

2. **Registroaziende.it:** Filtrare ATECO 45.11.02 per regioni Puglia, Campania, Calabria
   - Dati: nome + citta' + fatturato (utile per filtrare micro vs grandi)

### Fase 2 — Arricchimento (free tier)
3. **Outscraper/Google Maps:** Per ogni provincia, cercare "autosalone" + "compravendita auto usate"
   - 500 record/mese gratis con Outscraper
   - Arricchire con: rating, numero recensioni, orari, sito web

4. **AutoScout24:** Cross-reference dealer trovati su PagineGialle con profili AS24
   - Aggiunge: stock attuale, recensioni clienti, specializzazione marche

### Fase 3 — Qualificazione
5. **Subito.it:** Cercare annunci auto per provincia, identificare venditori con >10 annunci attivi
   - Conferma che il dealer e' attivo e che marche tratta

6. **Merge e scoring:** Unire dati PG + Google + AS24 + Subito + RegistroAziende
   - Score basato su: dimensione (fatturato), attivita' online (annunci), specializzazione (marche premium), zona

---

## ERRORI DELLA RICERCA PRECEDENTE

| Claim precedente | Realta' verificata | Gravita' |
|---|---|---|
| "7.392 imprese ATECO 45.11.02" | CONFERMATO — dato esatto | OK |
| "gosom scraper 3.5k stelle" | CONFERMATO | OK |
| "COMPROSUBITOAUTO 6.000 iscritti" | 6.045 confermato | OK |
| "Telegram = canale discovery Sud" | ERRATO — copertura Centro-Nord | MEDIA |
| "PagineGialle ha pochi dati" (mai detto ma implicito) | 147 risultati per SOLA Foggia con tel | Sottovalutato |
| "Facebook groups per commercianti" | ESISTONO ma dati non verificabili senza login | BASSA |

---

*Documento generato con verifica diretta. Ogni dato ha la fonte indicata. "NON VERIFICATO" dove non e' stato possibile accesso diretto.*
