# Canali Discovery Dealer Auto Italia via Social e Directory - 2026

**Ricerca:** 2026-04-09
**Obiettivo:** Trovare e profilare concessionari family-business (30-80 auto, brand premium) in tutta Italia
**Contesto:** 700 dealer gia' trovati su Subito.it, servono canali aggiuntivi
**Confidenza complessiva:** MEDIUM-HIGH (mix di fonti verificate e stime)

---

## EXECUTIVE SUMMARY

Google Maps (via Outscraper o gosom/google-maps-scraper) e' il canale con il miglior rapporto dati/sforzo ed e' il punto di partenza obbligato. Fornisce nome, telefono, indirizzo, sito web, recensioni -- tutto cio' che serve per il primo contatto. AutoScout24 e Automobile.it hanno directory dealer pubbliche scrappabili per arricchire i dati. Instagram e' utile per profilazione (capire come comunica il dealer, che auto tratta) ma NON per discovery primaria. Facebook e PagineGialle hanno valore marginale. WhatsApp Business Directory non e' disponibile in Italia.

**Stima volume totale raggiungibile: 2.000-3.000 dealer unici** combinando tutti i canali, di cui 300-500 nel target ARGOS (family-business, premium, Sud).

---

## 1. GOOGLE MAPS / GOOGLE BUSINESS PROFILE

### Perche' e' il canale #1

Google Maps e' il canale con il dataset piu' completo e strutturato per dealer auto in Italia. Ogni business ha: nome, indirizzo completo, telefono, sito web, orari, rating, numero recensioni, foto, coordinate GPS. Non c'e' nessun altro canale che fornisca tutto questo in un singolo posto.

### Dati estraibili per ogni dealer

| Campo | Disponibilita' | Utilita' ARGOS |
|-------|----------------|----------------|
| Nome business | Sempre | Identificazione |
| Telefono | ~90% | Contatto diretto |
| Indirizzo completo | Sempre | Geolocalizzazione |
| Sito web | ~70% | Cross-referencing |
| Rating (1-5) | Sempre | Quality signal |
| Numero recensioni | Sempre | Dimensione/attivita' |
| Testo recensioni | Estraibile | Profilazione (importatore?) |
| Orari apertura | ~85% | Timing outreach |
| Foto | Sempre | Dimensione showroom |
| Coordinate GPS | Sempre | Mapping |
| Email | Con enrichment | Contatto alternativo |

### Query ottimali per ARGOS

```
"concessionario auto usate" + [citta'/provincia]
"autosalone" + [citta']
"vendita auto" + [citta']
"auto usate" + [citta']
"concessionaria BMW" + [citta']  (per trovare chi tratta premium)
"concessionaria Mercedes" + [citta']
```

**Stima volume:** 50-150 dealer per provincia, 1.500-3.000 totali per le 63 province target.

### Profilazione via recensioni

**Tecnica chiave:** cercare nelle recensioni parole come "Germania", "importazione", "tedesca", "dall'estero", "km certificati". Un dealer con queste recensioni e' gia' un importatore attivo = target perfetto ARGOS.

Esempio: se un dealer ha recensioni tipo "ottimo servizio, auto perfetta dalla Germania" o "ci ha trovato la BMW che cercavamo in Germania" -- questo dealer e' gia' nel business dell'import e puo' essere interessato a un fornitore affidabile.

### Tool: Outscraper (RACCOMANDATO per start)

- **Free tier:** 500 record/mese gratis [HIGH confidence - verificato su outscraper.com]
- **Oltre free tier:** ~$3/1.000 record
- **Python SDK:** `pip install outscraper` -- API semplice
- **Query format:** "concessionario auto usate, Foggia, Italia"
- **Enrichment:** email e social media profiles inclusi

**Strategia ottimale con 500 record gratis:**
- Mese 1: 7 province P1 (Sud core) = ~500 risultati
- Mese 2: 15 province P2 (Sud esteso + Isole) = 500 risultati (serve filtro)
- Mese 3: Centro Italia

```python
# Esempio Outscraper
from outscraper import ApiClient
client = ApiClient(api_key=os.environ['OUTSCRAPER_KEY'])
results = client.google_maps_search(
    'concessionario auto usate, Foggia, Italia',
    language='it',
    region='IT',
    limit=100
)
```

**Fonte:** [Outscraper Google Maps Scraper](https://outscraper.com/google-maps-scraper/) | Confidenza: HIGH

### Tool: gosom/google-maps-scraper (alternativa gratis illimitata)

- **Costo:** Gratis (MIT license), open source
- **GitHub:** 3.6k stelle, attivamente mantenuto nel 2026
- **Performance:** ~120 places/minuto con concurrency ottimizzata
- **Output:** CSV, JSON, PostgreSQL
- **Requisiti:** Docker (modo piu' semplice) o Go 1.25+
- **Problema noto S99:** problemi TLS su alcune configurazioni

```bash
# Docker
docker run -v $PWD/gmapsdata:/gmapsdata gosom/google-maps-scraper \
  -input queries.txt -results results.csv -exit-on-inactivity 3m
```

**File queries.txt:**
```
concessionario auto usate Foggia
concessionario auto usate Caserta
autosalone Cosenza
vendita auto usate Lecce
```

**Pro:** Illimitato, nessun costo. Email extraction inclusa.
**Contro:** Setup piu' complesso, richiede Docker, potenziale ban IP se aggressivo.

**Fonte:** [gosom/google-maps-scraper GitHub](https://github.com/gosom/google-maps-scraper) | Confidenza: HIGH

### Raccomandazione Google Maps

Usare Outscraper per le prime 500 query (province P1), poi gosom per volume. Cross-referenziare i risultati. Le recensioni sono la miniera d'oro per la profilazione.

---

## 2. AUTOSCOUT24 — Directory Dealer

### Struttura

AutoScout24 ha una directory pubblica di dealer organizzata per regione e citta':
- URL base: `https://www.autoscout24.it/concessionari/regioni/`
- 20 regioni italiane con mappa interattiva
- URL pattern: `/concessionari/regioni/[regione]/[citta']/`
- Esempio: `/concessionari/regioni/campania/napoli/`

### Dati disponibili per dealer

| Campo | Presente | Note |
|-------|----------|------|
| Nome business | Si | Sempre |
| Indirizzo | Si | Via + CAP + Provincia |
| Numero recensioni | Si | Es: "2083 Recensioni" |
| Link inventario | Si | Quante auto in stock |
| Contatti | Parziale | Link a pagina dettaglio |

### Scraping

- HTML server-side rendered (Next.js con SSR)
- Paginazione per citta' all'interno di ogni regione
- ToS proibiscono scraping senza autorizzazione scritta
- Rate limit consigliato: 10-15 secondi tra richieste

### Valore per ARGOS

ALTO per cross-referencing. Un dealer presente su AutoScout24 con poche auto in inventario e molte recensioni e' probabilmente un "su commissione" = target perfetto. Il numero di recensioni e' un proxy affidabile per l'attivita' e la dimensione.

**Stima volume:** 5.000-10.000 dealer in tutta Italia (AutoScout24 e' il marketplace #1 EU).

**Fonte:** [AutoScout24 Concessionari](https://www.autoscout24.it/concessionari/regioni/) | Confidenza: HIGH

---

## 3. AUTOMOBILE.IT — Directory Dealer

### Struttura

Automobile.it (di proprietà' del gruppo AutoScout24) ha una directory simile:
- URL base: `https://www.automobile.it/concessionari`
- Lista completa: `https://www.automobile.it/concessionari/italia`
- Per regione: `/concessionari/[regione]`
- Next.js con React components

### Dati disponibili

- Nome dealer
- Regione/provincia
- Ricerca per nome
- Sezione "Usato Garantito" con dealer certificati BMW Premium Selection, VW, Maserati Approved, Lexus Select, Mini Next

### Valore per ARGOS

MEDIO. Utile per identificare dealer con programmi "Usato Certificato" premium (BMW Premium Selection = potenziale target). Ma meno dati di contatto rispetto a Google Maps.

**Fonte:** [Automobile.it Concessionari](https://www.automobile.it/concessionari) | Confidenza: HIGH

---

## 4. INSTAGRAM

### Hashtag usati dai dealer auto italiani

**Hashtag generici alto volume (milioni di post):**
- #auto #car #bmw #mercedes #audi #ferrari #automotive #carsofinstagram

**Hashtag specifici dealer (migliaia-decine di migliaia):**
- #concessionario #concessionaria #autosalone
- #autoUsate #usatoGarantito #usatoCertificato
- #autotedesche #importauto
- #bmwusata #mercedesusata #audiusata

**Hashtag localizzati (centinaia):**
- #autoNapoli #concessionarioBari #autoCatania
- #autoSalerno #concessionarioLecce

### Profili tipo dealer 30-80 auto

| Metrica | Range tipico | Note |
|---------|-------------|------|
| Follower | 500-5.000 | Family business non ha grandi numeri |
| Post | 200-1.000 | 1-3 post/settimana con foto auto |
| Bio | Indirizzo + telefono + WA | Quasi sempre |
| Account type | Business | Verificabile da "contatti" button |
| Stories highlights | "Stock" "Consegne" "Recensioni" | Pattern comune |

**Esempi reali trovati:**
- @autosimeone — 2.500+ follower, Carovigno (BR), premium multibrand [HIGH]
- @msautomobili — 5.000+ follower, 400+ veicoli, consegna a domicilio [HIGH]
- @radicciauto_ferrari — 3.329 follower, Ferrari dealer Bari/Ancona [HIGH]
- @fratelli_manna — Napoli, auto usate, contenuti TikTok cross-posted [MEDIUM]

### Come distinguere dealer vs privato su Instagram

| Segnale | Dealer | Privato |
|---------|--------|---------|
| Account type | Business/Creator | Personal |
| Bio | Indirizzo fisico + P.IVA | Nessuno |
| Pulsante "Contatta" | Si (tel/email/mappa) | No |
| Post pattern | Foto auto singole, stile catalogo | Foto varie |
| Frequenza | 3-10 post/settimana | Irregolare |
| Highlights | "Stock" "Consegne" "Garanzia" | Vacanze etc |
| Caption | Prezzo + specifiche + "contattaci" | Narrativo |

### Scraping Instagram nel 2026

**Stato:** Instagram ha difese aggressive anti-bot nel 2026. Login wall obbligatorio, GraphQL offuscato, IP flagging rapido. Scripts semplici con requests/BeautifulSoup NON funzionano piu'.

**Opzioni:**

1. **Apify Instagram Scraper** (RACCOMANDATO)
   - Free tier: $5 crediti/mese = ~2.000 profili o post
   - Profile scraper: $2.60/1.000 risultati
   - Hashtag scraper: disponibile come actor separato
   - Estrae: bio, follower count, post count, contact info, recent posts
   - **Fonte:** [Apify Instagram Scraper](https://apify.com/apify/instagram-scraper) | Confidenza: HIGH

2. **Instagram Graph API** (ufficiale ma limitata)
   - Limite: 30 hashtag unici/settimana per account
   - Richiede Facebook Developer App
   - Solo hashtag search, no profile scraping di massa
   - Utile per monitoraggio, non per discovery
   - **Fonte:** [Instagram Graph API Guide](https://elfsight.com/blog/instagram-graph-api-complete-developer-guide-for-2026/) | Confidenza: HIGH

3. **Ricerca manuale** (per profilazione)
   - Cercare hashtag nella app IG
   - Visitare profili dealer trovati da Google Maps
   - Estrarre telefono/email dalla bio
   - Tempo: ~2 min per dealer

### Estrarre contatti da profilo IG

- **Bio:** quasi sempre contiene telefono e/o email
- **Pulsante Contatta:** su account Business mostra tel/email/indirizzo
- **Link in bio:** spesso Linktree o sito con contatti
- **DM:** non raccomandato per primo contatto B2B

### Valore per ARGOS

Instagram e' ECCELLENTE per profilazione (capire come comunica il dealer, che auto tratta, quanto e' attivo) ma MEDIOCRE per discovery primaria. Usare Google Maps per trovare il dealer, poi IG per profilare.

**Stima volume discovery puro via IG:** 200-400 dealer (basso, perche' molti piccoli dealer non hanno IG attivo)

---

## 5. FACEBOOK

### Pagine Facebook Dealer

La maggior parte dei dealer italiani ha una Pagina Facebook (anche piu' che Instagram). Ricerca: "concessionario auto [citta']" su Facebook Search.

### Facebook Marketplace

- I dealer vendono su Marketplace ma sono mescolati con privati
- Identificazione dealer: foto professionali, piu' annunci simili, link a pagina business
- NON scrappabile nel 2026: difese anti-bot avanzate (behavioral modeling, TLS fingerprinting, account risk scoring)
- Facebook cambia struttura ogni 3-6 settimane

### Gruppi Facebook B2B rilevanti

| Gruppo | Tipo | Membri stimati |
|--------|------|----------------|
| "VENDITA AUTO PER COMMERCIANTI (e privati)" | Compravendita B2B/B2C | Attivo |
| "Marketplace Vendita e Acquisto Auto" | Generico | Attivo |
| Cartrade Italia | B2B ingrosso | Pagina business |

**Nota:** I gruppi B2B veri (commerciante-a-commerciante) sono pochi e piccoli. La maggior parte dei gruppi sono B2C.

### Scraping Facebook nel 2026

**SCONSIGLIATO.** Facebook ha le difese anti-scraping piu' aggressive di tutti i social. Behavioral modeling, network fingerprinting, browser telemetry, account-level risk scoring. Costo di manutenzione altissimo (cambia ogni 3-6 settimane). Il rischio ban account e' alto.

### Valore per ARGOS

BASSO per discovery automatizzata. MEDIO per profilazione manuale (guardare la pagina FB di un dealer trovato altrove). I gruppi B2B possono essere utili per capire il mercato ma non per discovery dealer.

**Fonte:** [Facebook Scraper Python](https://www.promptcloud.com/blog/python-facebook-scraper/) | Confidenza: MEDIUM

---

## 6. PAGINEGIALLE.IT

### Query e struttura

- URL: `https://www.paginegialle.it/ricerca/concessionarie-auto/[provincia]`
- Risultati: ~147 per Foggia (verificato S99), variabile per provincia
- HTML standard, relativamente semplice da parsare

### Dati estraibili

| Campo | Presente | Note |
|-------|----------|------|
| Nome business | Si | Sempre |
| Indirizzo | Si | Completo |
| Telefono | Si | Sempre |
| Sito web | Parziale | ~50% |
| Email | Raro | Solo se inserita |
| Categoria | Si | "Concessionarie auto" etc |
| WhatsApp | Parziale | Alcuni dealer |

### Tool di scraping

1. **yellow-page-scraper-it** (GitHub)
   - Python + PyQt5, GUI
   - Estrae: nome, indirizzo, provincia, citta', CAP, telefono, WA, email, sito
   - 15 commit, 3 stelle, poco mantenuto
   - Input: CSV con "professione;localita'"
   - **Fonte:** [GitHub yellow-page-scraper-it](https://github.com/gautam132002/yellow-page-scraper-it) | Confidenza: MEDIUM

2. **Octoparse template** (no-code)
   - Template pre-costruito per PagineGialle
   - Free tier limitato
   - **Fonte:** [Octoparse PG Template](https://www.octoparse.com/template/crawler-lista-aziende-paginegialle) | Confidenza: MEDIUM

3. **Script custom** (Python requests + BeautifulSoup)
   - PagineGialle ha HTML relativamente pulito
   - Rate limit: ~1 richiesta ogni 5-10 secondi consigliato
   - robots.txt: verificare `/robots.txt` prima di procedere

### Aspetti legali

PagineGialle vieta esplicitamente "estrazione e riuso di tutto o parte sostanziale del database" nei ToS. Scraping sistematico viola i termini. Per uso interno non commerciale e volumi piccoli il rischio pratico e' basso, ma va tenuto presente.

### Alternative a PagineGialle

| Directory | URL | Note |
|-----------|-----|------|
| Pagine Bianche | paginebianche.it | Piu' orientato residenziale |
| Tuttocitta' | tuttocitta.it | Mappe + business |
| Cylex Italia | cylex.it | Directory business |
| Estrattoredati.com | estrattoredati.com | Tool scraping PG + GMaps |
| Infomotori Concessionari | infomotori.com/concessionari | Lista top dealer |
| Top Dealers Italia | topdealersitalia.it | Solo grandi dealer |

### Valore per ARGOS

MEDIO. Buona fonte secondaria per cross-referencing (telefono, indirizzo). Ma dati meno ricchi di Google Maps (no recensioni, no rating, no foto).

**Stima volume:** 3.000-5.000 risultati per "concessionarie auto" su tutta Italia.

---

## 7. WHATSAPP BUSINESS

### Directory WhatsApp Business

**NON disponibile in Italia.** La WhatsApp Business Directory esiste solo in Brasile al momento (aprile 2026). Non c'e' modo di cercare business italiani sulla directory WA.

**Fonte:** [WhatsApp Business Directory FAQ](https://faq.whatsapp.com/1257477678426227/?locale=it_IT) | Confidenza: HIGH

### Verificare se un numero e' WA Business

- **Senza inviare messaggio:** non esiste un modo ufficiale
- **Workaround:** salvare il numero in rubrica e verificare su WA se appare come "Account Business" con logo/catalogo. Ma richiede interazione manuale.
- **wa-daemon:** il daemon gia' attivo su iMac potrebbe verificare lo status del numero (Business vs Personal) tramite le API whatsapp-web.js, ma richiede implementazione ad hoc.

### Catalogo WA Business

Molti dealer usano il catalogo prodotti di WA Business per mostrare auto in vendita. Questo e' un segnale forte di dealer attivo e digitalmente maturo. Ma non c'e' modo di scoprirlo senza prima avere il numero.

### Valore per ARGOS

BASSO per discovery (impossibile cercare dealer). ALTO per qualificazione post-discovery: una volta trovato il numero via Google Maps/PagineGialle, verificare se ha WA Business con catalogo e' un ottimo segnale di fit.

---

## 8. ALTRE FONTI

### LinkedIn

- **Sales Navigator:** $895/anno -- FUORI BUDGET (zero costi)
- **Ricerca gratuita:** limitata a ~100 risultati/mese, filtri base
- **Query utile:** "titolare concessionario auto" + [regione]
- **Valore:** BASSO per discovery, MEDIO per trovare il nome del titolare (utile per personalizzare il messaggio WA)
- **Scraping:** LinkedIn blocca aggressivamente, rischio ban account

### TikTok

- Dealer italiani stanno arrivando su TikTok con video di auto e consegne
- Hashtag: #concessionaria #autoUsate #consegna #concessionario
- @fratelli_manna (Napoli): esempio di dealer attivo su TikTok
- **Caso cautela:** un TikToker dealer in Campania (Bacoli) con 900k follower coinvolto in scandalo auto mai consegnate -- il canale attira anche operatori poco seri
- **Valore:** BASSO. TikTok e' B2C e orientato a dealer grandi/showman. I family-business target ARGOS raramente sono su TikTok.

### AutoScout24 Directory (gia' trattato sopra)

Miglior directory dealer online in Italia. **Stima 5.000-10.000 dealer.**

### Automobile.it Directory (gia' trattato sopra)

Directory complementare, utile per dealer con programmi "Usato Garantito" premium.

### Piattaforme B2B scoperte

| Piattaforma | Tipo | Rilevanza ARGOS |
|-------------|------|-----------------|
| AutoInRete (Sermetra) | Marketplace B2B auto usate IT | ALTA -- dealer qui sono gia' nel B2B |
| Cartrade Italia | Ingrosso auto per commercianti | ALTA -- stessi target |
| AutomotiveGest | Network professionisti auto | MEDIA -- community |
| AUTO1.com | B2B marketplace (62 filiali IT) | BASSA -- modello opposto |
| CarOnSale | Aste B2B online | MEDIA -- dealer che comprano qui |

**Nota:** AutoInRete e Cartrade Italia sono fonti ECCELLENTI per trovare dealer gia' abituati al B2B. Verificare se hanno directory pubbliche.

---

## 9. STRATEGIA INTEGRATA RACCOMANDATA

### Ordine di esecuzione (ROI decrescente)

```
FASE 1 (Settimana 1): Google Maps via Outscraper
   500 record gratis → 7 province P1 (Sud core)
   Query: "concessionario auto usate [provincia]"
   Output: nome, tel, indirizzo, sito, rating, recensioni
   Volume stimato: 400-500 dealer unici

FASE 2 (Settimana 2): AutoScout24 + Automobile.it directory scraping
   Script Python con requests + BeautifulSoup
   Tutte le 20 regioni
   Output: nome, indirizzo, n.recensioni, inventario
   Volume stimato: 2.000-5.000 dealer
   
FASE 3 (Settimana 2-3): Merge e dedup
   Cross-referencing per nome + indirizzo + telefono
   Arricchimento: chi e' su entrambi Subito + AS24 = attivo
   Chi ha recensioni con "Germania/import" = target caldo

FASE 4 (Settimana 3): Google Maps via gosom per volume
   Province P2-P4 (illimitato, gratis)
   Con email extraction attiva
   Volume stimato: 1.500-2.500 aggiuntivi

FASE 5 (Continuo): Profilazione via Instagram
   Per ogni dealer nel top 100 target:
   - Cercare @handle su IG (dal sito web o Google "[nome dealer] instagram")
   - Verificare: attivita', tipo auto, tono comunicazione
   - Classificare archetipo (NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE)
   Volume: 100-200 profili verificati

FASE 6 (Opzionale): PagineGialle per riempire buchi
   Province dove Google Maps ha pochi risultati
   Script Python semplice
   Volume stimato: 500-1.000 aggiuntivi
```

### Cross-referencing

| Campo chiave | Fonte primaria | Fonte secondaria |
|--------------|---------------|------------------|
| Nome dealer | Google Maps | AutoScout24 |
| Telefono | Google Maps | PagineGialle |
| Indirizzo | Google Maps | AutoScout24 |
| N. auto in stock | Subito.it | AutoScout24 |
| Recensioni | Google Maps | AutoScout24 |
| Instagram | Sito web dealer | Google "[nome] instagram" |
| Brand trattati | Subito.it | AutoScout24 inventario |

### Merge strategy

```python
# Pseudocodice merge
def merge_dealer(gmaps, as24, subito, pg):
    # Match per: nome fuzzy (>85% similarity) OR telefono exact OR indirizzo fuzzy
    # Priority: Google Maps come record master
    # Arricchisci con: n.auto da Subito, recensioni da AS24, tel da PG
    # Score fit ARGOS: premium brands + size 30-80 + Sud + recensioni import
```

### Stima volume finale

| Canale | Dealer unici | Costo | Sforzo |
|--------|-------------|-------|--------|
| Google Maps (Outscraper) | 500 | Gratis (free tier) | Basso |
| Google Maps (gosom) | 2.000 | Gratis | Medio (setup Docker) |
| AutoScout24 directory | 3.000-5.000 | Gratis | Medio (scraper custom) |
| Automobile.it | 1.000-2.000 | Gratis | Medio |
| Subito.it (gia' fatto) | 700 | Gratis | Gia' completato |
| PagineGialle | 500-1.000 | Gratis | Medio |
| Instagram | 200-400 | $5 Apify o gratis manuale | Alto |
| Facebook | 100-200 | Gratis (manuale) | Alto |
| **TOTALE dopo dedup** | **2.500-4.000** | **$0-5** | **3-4 settimane** |

### Target ARGOS nel totale

Applicando i filtri (30-80 auto, brand premium, Sud Italia, family-business):
- **Stima dealer target:** 300-600 su 2.500-4.000 totali
- **Di cui gia' trovati:** 139 fit alto (da S104)
- **Incremento atteso:** 2-4x il database attuale

---

## 10. PITFALLS E AVVERTENZE

### Legali
- AutoScout24 vieta scraping nei ToS -- usare rate limit aggressivo, no rivendita dati
- PagineGialle vieta estrazione database -- rischio basso per uso interno
- Instagram ToS vietano scraping -- Apify e' il workaround "accettato" dal mercato
- Google Maps: scraping tollerato con volumi ragionevoli

### Tecnici
- gosom/google-maps-scraper: problemi TLS segnalati in S99 -- testare prima
- Instagram: login wall nel 2026, scripts semplici non funzionano
- Facebook: NON tentare scraping automatizzato, spreco di tempo
- Rate limiting: rispettare sempre delay tra richieste (5-15 sec)

### Strategici
- NON inseguire volume: 4.000 dealer grezzi non servono. 300 dealer profilati con fit alto SERVONO.
- Il valore e' nella profilazione, non nella lista. Chiunque puo' comprare una lista di dealer su InfoCamere per pochi euro.
- Le recensioni Google Maps sono la vera miniera: un dealer che riceve review "auto dalla Germania perfetta" vale 100x un nome+telefono generico.
- Instagram profilazione > Instagram discovery. Non cercare dealer SU Instagram, ma USA Instagram PER profilare dealer trovati altrove.

---

## FONTI

- [Outscraper Google Maps Scraper](https://outscraper.com/google-maps-scraper/) - FREE tier, dati, pricing
- [gosom/google-maps-scraper GitHub](https://github.com/gosom/google-maps-scraper) - 3.6k stelle, MIT
- [AutoScout24 Concessionari per regione](https://www.autoscout24.it/concessionari/regioni/)
- [Automobile.it Concessionari](https://www.automobile.it/concessionari)
- [Apify Instagram Scraper](https://apify.com/apify/instagram-scraper) - free tier $5/mese
- [Apify pricing](https://apify.com/pricing) - dettagli free tier
- [Instagram Graph API Guide 2026](https://elfsight.com/blog/instagram-graph-api-complete-developer-guide-for-2026/)
- [WhatsApp Business Directory FAQ](https://faq.whatsapp.com/1257477678426227/?locale=it_IT) - solo Brasile
- [yellow-page-scraper-it GitHub](https://github.com/gautam132002/yellow-page-scraper-it)
- [Octoparse PagineGialle Template](https://www.octoparse.com/template/crawler-lista-aziende-paginegialle)
- [Scrapfly Instagram Scraping 2026](https://scrapfly.io/blog/posts/how-to-scrape-instagram)
- [Facebook Scraper Python](https://www.promptcloud.com/blog/python-facebook-scraper/)
- [DealerLink TikTok per concessionari](https://www.dealerlink.it/come-usare-tiktok-per-concessionari/)
- [AutoInRete B2B](https://www.dealerlink.it/autoinrete-portale-web-b2b-acquisto-vendita-auto-usate-km0/)
- [TagsFinder hashtag auto](https://www.tagsfinder.com/it-it/related/auto/)
