# ARGOS — Mappa Completa Portali Auto EU
**Data ricerca**: 2026-03-19
**Obiettivo**: Censimento TUTTI i marketplace/portali dove trovare veicoli premium per ARGOS

---

## NOTA METODOLOGICA

Ricerca multi-source: WebSearch live + dati industry. Per ogni portale:
- Volume listing = stima da fonti pubbliche (dichiarate dai portali o da analisti)
- Scraping = fattibilita' tecnica documentata da Apify/Carapis/GitHub
- Rilevanza ARGOS = focus su BMW/Mercedes/Audi 2018-2023, prezzi DE competitivi vs IT

---

## SEZIONE A — MARKETPLACE PER PAESE (Privati + Dealer)

### GERMANIA (mercato primario ARGOS)

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Mobile.de | mobile.de | Privati + Dealer | 1.3M+ annunci | SI — Apify scraper multipli disponibili (ivanvs, 3x1t, lexis-solutions), Carapis parser, auto-api.com. Anti-bot: presente ma bypassabile con proxy rotation | Gratuito sfoglio, inserzione a pagamento | ALTA — volume massimo DE, prezzi real-time, BMW/Audi/Merc dominanti. Fonte primaria ARGOS |
| AutoScout24.de | autoscout24.de | Privati + Dealer | 2.5M+ annunci EU | SI — API pubblica limitata, scraping via Carapis/Apify. Protezione: Cloudflare, IP ban dopo molte req. | Gratuito sfoglio | ALTA — secondo portale DE, copertura pan-EU, facile confronto IT vs DE |
| eBay Kleinanzeigen | kleinanzeigen.de | Privati | 800K+ auto | SI — scraper Apify disponibile | Gratuito | MEDIA — molti privati, prezzi piu' bassi, qualita' variabile. Utile per private gems |
| Auto.de | auto.de | Privati + Dealer | 200K+ | Limitato — no API pubblica | Gratuito | MEDIA — portale locale tedesco, utenti fidati (premiato dai tedeschi) |
| Autohero.de | autohero.com | Solo dealer/refurbished | 30K+ | Limitato | Gratuito sfoglio | BASSA — prezzi piu' alti, veicoli ricondizionati, no arbitraggio |
| Heycar.de | hey.car | Dealer certificati | 60K+ | No API pubblica | Gratuito | BASSA — solo dealer ufficiali, prezzi "giusti" senza margine per ARGOS |

**Strategia DE**: Mobile.de + AutoScout24.de = copertura 95% mercato tedesco. eBay Kleinanzeigen per private gems.

---

### PAESI BASSI (secondo mercato ARGOS)

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Marktplaats.nl | marktplaats.nl | Privati + Dealer | 200K+ auto | SI — scraper disponibili, parte del gruppo eBay Classifieds | Gratuito | ALTA — principale portale NL, molto privati, prezzi competitivi. Molte BMW/Audi NL senza VAT |
| AutoTrack.nl | autotrack.nl | Privati + Dealer | 150K+ | SI — ora parte AutoScout24 Group (dic 2025) | Gratuito | ALTA — acquisito da AutoScout24 dic 2025, integrazione in corso. Rimane brand autonomo |
| Gaspedaal.nl | gaspedaal.nl | Aggregatore | 300K+ (aggrega altri) | SI — metasearch, aggrega Marktplaats + AutoTrack + AS24 | Gratuito | MEDIA — utile per overview ma non fonte diretta, usa fonti primarie |
| AutoScout24.nl | autoscout24.nl | Privati + Dealer | Parte del 2.5M EU | Vedi DE | Gratuito | ALTA — stessi annunci DE ma filtrabile per NL |

**Nota**: AutoTrack e Gaspedaal sono ora AutoScout24 Group (acquisizione dic 2025). Brand separati ma stesso proprietario.

---

### BELGIO

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| AutoScout24.be | autoscout24.be | Privati + Dealer | Parte del 2.5M EU | Vedi DE | Gratuito | ALTA — BE e' mercato vicino DE, molti veicoli con regime margine favorevole |
| 2dehands.be | 2dehands.be | Privati | 80K+ auto | SI — scraper disponibili | Gratuito | MEDIA — principalmente privati belgi, qualita' variabile |
| Vroom.be | vroom.be | Privati + Dealer | 30K+ | Limitato | Gratuito | BASSA — portale locale minore, limitata copertura premium |
| Gocar.be | gocar.be | Dealer | 25K+ | No API pubblica | Gratuito | BASSA — dealer belgi, prezzi spesso gia' allineati al mercato EU |

---

### AUSTRIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Willhaben.at | willhaben.at | Privati + Dealer | 188K+ annunci auto | SI — scraper disponibili | Gratuito | ALTA — principale portale AT, molti veicoli premium austriaci a prezzi interessanti |
| Car4you.at | car4you.at | Dealer | Parte di Willhaben (acquisito) | SI — ora parte willhaben | Gratuito | ALTA — ora integrato in willhaben, stesso bacino |
| AutoScout24.at | autoscout24.at | Privati + Dealer | Parte del 2.5M EU | Vedi DE | Gratuito | ALTA — AT e' mercato di transito per import DE→IT via Brennero |

**Nota**: Car4you.at e' stato acquisito da Willhaben. Ora un'unica piattaforma.

---

### FRANCIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| LeBonCoin auto | leboncoin.fr/c/voitures | Privati + Dealer | 500K+ annunci auto, 124M visite/mese totali (marzo 2025) | SI — scraper Apify. Anti-bot: presente, bypassabile | Da 2025: a pagamento per privati | MEDIA — volume enorme ma prezzi FR spesso allineati a IT. Utile per private deals rari |
| LaCentrale.fr | lacentrale.fr | Dealer focus | 350K+ listing verificati | SI — API limitata | Gratuito sfoglio | MEDIA — dealer FR, prezzi professionali. Acquistata da Prosus per €1.1B (2025) |
| AutoScout24.fr | autoscout24.fr | Privati + Dealer | Parte del 2.5M EU | Vedi DE | Gratuito | MEDIA — FR meno interessante per arbitraggio vs DE |
| ParuVendu.fr | paruvendu.fr | Privati | 50K+ auto | Limitato | Gratuito | BASSA — portale generalista FR, auto di qualita' variabile |
| Caradisiac.com | caradisiac.com | Dealer + contenuto | 30K+ | No API | Gratuito | BASSA — piu' editoriale, listing integrato con LaCentrale |

---

### SVEZIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Blocket.se | blocket.se | Privati + Dealer | 100K+ auto | SI — scraper disponibili. NOTA: calo listing privati riportato marzo 2026 | Gratuito | ALTA — Svezia ha prezzi auto premium competitivi, molto export verso IT |
| Bytbil.com | bytbil.com | B2C Dealer | 80K+ | Limitato | Gratuito | ALTA — principale portale dealer SE, Volvo/BMW/Mercedes svedesi |
| Kvd.se | kvd.se | Aste B2C | 5K+ | No API pubblica | Account richiesto | MEDIA — aste svedesi, veicoli di qualita', prezzi interessanti |

**Nota**: Blocket e' ora parte di Vend Marketplaces (ex Schibsted Marketplaces). Calo listing privati segnalato marzo 2026 dopo modifiche al modello.

---

### DANIMARCA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| BilBasen.dk | bilbasen.dk | Privati + Dealer | 90K+ | SI — scraper Apify | Gratuito | MEDIA — DK ha tasse auto altissime, prezzi gonfiati localmente. Meno utile per export |
| DBA.dk | dba.dk | Privati | 70K+ | SI — scraper disponibili | Gratuito | BASSA — principalmente privati DK, mercato distorto da tassazione |
| Biltorvet.dk | biltorvet.dk | Dealer | 50K+ | No API | Gratuito | BASSA — dealer DK, stesse considerazioni fiscali |

**Nota**: La Danimarca ha le tasse piu' alte su auto in EU (fino al 150% di registration tax). Prezzi locali gonfiati. Importare da DK non ha senso per ARGOS.

---

### NORVEGIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| FINN.no | finn.no/car | Privati + Dealer | 80K+ | SI — scraper disponibili | Gratuito | BASSA — NO non e' UE, IVA complicata, extra-EU burocrazia. Mercato EV dominato. Non target ARGOS |

---

### FINLANDIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Nettiauto.com | nettiauto.com | Privati + Dealer | 60K+ | Limitato | Gratuito | BASSA — FI lontana logisticamente, prezzi non competitivi vs DE |
| Tori.fi | tori.fi | Privati | 30K+ auto | Limitato | Gratuito | BASSA — generalista FI, auto di qualita' variabile |

---

### REPUBBLICA CECA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Sauto.cz | sauto.cz | Privati + Dealer | 150K+ | SI — scraper disponibili | Gratuito | ALTA — CZ ha prezzi molto competitivi, molte BMW/Audi/Skoda di qualita'. Mercato sottovalutato |
| TipCars.com | tipcars.com | Dealer | 80K+ | Limitato | Gratuito | MEDIA — dealer CZ/SK, prezzi professionali ma ancora competitivi vs IT |
| AAA Auto | aaaauto.cz | Dealer catena | 20K+ propri | No | Gratuito sfoglio | BASSA — grande catena, prezzi standardizzati, nessun margine |
| AutoScout24.cz | autoscout24.cz | Privati + Dealer | Parte EU | Vedi DE | Gratuito | ALTA — stessa piattaforma, filtro CZ |

**Nota**: CZ e' mercato B di ARGOS. Prezzi 15-20% sotto DE per stesso veicolo. Logistica: 1.200km da Praga a Salerno.

---

### POLONIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Otomoto.pl | otomoto.pl | Privati + Dealer | 300K+ | SI — scraper Apify disponibile | Gratuito | ALTA — PL e' il piu' grande mercato auto EU Est, enorme volume BMW/Audi/Mercedes di seconda mano |
| Allegro.pl auto | allegro.pl | Privati + aste | 50K+ auto | SI — API disponibile | Gratuito sfoglio | MEDIA — principalmente privati polacchi, qualita' variabile, ma prezzi molto bassi |
| OLX.pl | olx.pl | Privati | 100K+ | SI | Gratuito | BASSA — qualita' molto bassa, low-cost. Non target ARGOS |

**Nota**: PL e' tra i mercati piu' interessanti per volume. Rischio: km falsificati piu' frequente. Sempre VIN check obbligatorio.

---

### UNGHERIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Hasznaltauto.hu | hasznaltauto.hu | Privati + Dealer | 120K+ | SI — scraper disponibili (parte Schibsted) | Gratuito | MEDIA — prezzi HU competitivi, ma qualita' misto. Utile per VW/Audi ex-lease aziendali |
| Jofogás.hu | jofogas.hu | Privati | 80K+ | Limitato | Gratuito | BASSA — generalista, qualita' bassa |

---

### ROMANIA / BULGARIA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| AutoVit.ro | autovit.ro | Privati + Dealer | 100K+ | SI | Gratuito | BASSA — Romania non e' mercato ARGOS (est Europa, km sospetti) |
| Mobile.bg | mobile.bg | Privati + Dealer | 80K+ | Limitato | Gratuito | BASSA — Bulgaria, stesse considerazioni. Non target ARGOS |

---

### REGNO UNITO

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| AutoTrader UK | autotrader.co.uk | Privati + Dealer | 400K+, 44M visite/mese | SI — API disponibile per dealer, scraper Apify | Gratuito sfoglio | BASSA — UK non EU post-Brexit. IVA/doganale complessa. Non target primario ARGOS |
| PistonHeads.com | pistonheads.com | Dealer + enthusiast | 80K+ premium | SI — scraper | Gratuito | BASSA — stesse considerazioni Brexit. Utile solo per supercar/classiche rare |
| Motors.co.uk | motors.co.uk | Dealer | 400K+ (syndica con Gumtree) | Limitato | Gratuito | BASSA — UK post-Brexit, non target |
| CarGurus UK | cargurus.co.uk | Privati + Dealer | 200K+ | Limitato | Gratuito | BASSA — UK, stesse considerazioni |

**Nota UK**: Post-Brexit, importare da UK in IT richiede sdoganamento + IVA all'importazione. Costo aggiuntivo €2.000-4.000 per veicolo. NON target per ARGOS standard.

---

### SPAGNA

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| Coches.net | coches.net | Privati + Dealer | 160K+, 11.9M visite/mese (lug 2025) | SI — scraper | Gratuito | BASSA — ES mercato interno, prezzi non competitivi vs DE. Non fonte ARGOS |
| Milanuncios.com | milanuncios.com | Privati | 353K+ auto | SI | Gratuito | BASSA — principalmente privati ES, qualita' variabile |
| Wallapop auto | wallapop.com | Privati | 211K+ auto | SI | Gratuito | BASSA — localissimo, bassa qualita' per premium |
| AutoScout24.es | autoscout24.es | Privati + Dealer | Parte EU | Vedi DE | Gratuito | BASSA — stessa piattaforma, filtro ES |

---

### ITALIA (per benchmark prezzi IT)

| Portale | URL | Tipo | Volume listing | Scraping/API | Costo accesso | Rilevanza ARGOS |
|---------|-----|------|----------------|--------------|---------------|-----------------|
| AutoScout24.it | autoscout24.it | Privati + Dealer | 500K+ annunci IT | SI — scraper Apify, Carapis | Gratuito | ALTA — benchmark obbligatorio per calcolare spread DE→IT |
| Subito.it auto | subito.it | Privati + Dealer | 400K+ | SI — scraper disponibili | Gratuito | ALTA — stessa funzione benchmark. Molti dealer Sud IT pubblicano qui |
| Automobile.it | automobile.it | Dealer | 200K+ | Limitato | Gratuito | ALTA — dealer professionali IT, ottimo per benchmark prezzi professionali |
| AutoUncle.it | autouncle.it | Aggregatore | Aggrega tutti portali IT | No API pubblica | Gratuito | MEDIA — utile per overview rapido prezzi IT benchmark |
| Autoplaza.it | autoplaza.it | Privati + Dealer | 50K+ | Limitato | Gratuito | BASSA — portale minore IT |

---

## SEZIONE B — PORTALI B2B / ASTE (Solo Dealer/Professionisti)

| Portale | URL | Paesi coperti | Tipo | Volume | Accesso | Costo | Rilevanza ARGOS |
|---------|-----|---------------|------|--------|---------|-------|-----------------|
| AutoProff | autoproff.com | Pan-EU (18 paesi) | B2B marketplace | 3.000+ auto/giorno, 10.000+ bidder | Registrazione dealer, verifica P.IVA | Abbonamento mensile (non dichiarato pubblicamente, stima €200-400/mese) | ALTA — piattaforma B2B AutoScout24 Group. Ex-leasing, dealer stock. Richiede P.IVA dealer IT o EU entity |
| eCarsTrade | ecarstrade.com | Pan-EU, focus BE/NL/DE/FR | B2B aste online | 18.000+ auto settimanali | Solo dealer licensed. Registrazione + verifica documenti aziendali. Interface EN/FR, nessun supporto IT | Registrazione gratuita + fee per transazione (non dichiarata — stima 1-3% del prezzo) | ALTA — enorme stock ex-leasing EU. Barriera: documentazione, nessun supporto IT. ARGOS si differenzia qui |
| OpenLane (ex ADESA Europe) | openlane.eu | Pan-EU | Aste B2B wholesale | Migliaia lot/settimana | Dealer registrato, deposito richiesto | Fee per transazione + subscription | ALTA — ex ADESA, leader EU wholesale. Deposito alto. ARGOS puo' accedere come buyer intermediario |
| BCA Group | bca.com | UK + 10 paesi EU | Aste fisiche + online | 5M+ veicoli/anno globali | Registrazione: KYC + camera di commercio. ATECO 45.11.01 per accesso pieno | Subscription + buyer premium (8-12%) | ALTA — maggiore rete aste fisica EU. Richiede ATECO italiano o EU company. OUE Estone risolve questo |
| CarOnSale | caronsale.com | Pan-EU (Germania focus) | B2B aste online | N/D (stima 50K+/mese) | Registrazione dealer gratuita. Verifica aziendale | Gratuito registrazione + buyer fee | ALTA — registrazione gratuita, pan-EU, gestito da Auto1 Group. Ottima per veicoli DE wholesale |
| AUTO1 / Autohero (wholesale) | auto1.com | Pan-EU | Wholesale B2B | 30.000+ auto proprie | Account dealer + verifica | Prezzi fissi no aste | MEDIA — AUTO1 compra/rivende a prezzi fissi. Meno margine per ARGOS ma accesso rapido |
| Manheim Europe | manheim.com | UK + alcuni EU | Aste fisiche | Grande volume UK | Dealer registrato | Fee per transazione | BASSA — principalmente UK. Post-Brexit complicato |
| CarCollect | carcollect.com | NL + BE + DE | B2B marketplace NL | N/D | Registrazione dealer | API disponibile per integrazioni | MEDIA — focus NL/BE, piattaforma tecnica con API. Buona per dealer NL |
| Astauto.it | astauto.it | Solo IT | Aste B2B IT | N/D | Dealer IT | Gratuito + fee | BASSA — aste IT, prezzi gia' alti, nessun vantaggio import EU |
| Autobid.de | autobid.de | DE + AT | B2B aste DE | N/D | Dealer registrato | Subscription | MEDIA — specifico DE/AT, stock dealer di qualita' |
| Exleasingcar.com | exleasingcar.com | Pan-EU | Ex-leasing B2B | N/D | Account aziendale | Gratuito sfoglio | ALTA — specializzato ex-leasing, veicoli ben mantenuti, documentazione completa. Ottimo per ARGOS |
| 2ndMove by Europcar | b2b.2ndmove.eu | Pan-EU | Ex-fleet Europcar | Migliaia auto/mese | Account aziendale | N/D | ALTA — veicoli ex-noleggio Europcar, km documentati, manutenzione certificata. Qualita' alta |
| Autoprice.eu | autoprice.eu | Pan-EU | B2B price intelligence | N/D | Account | Subscription | MEDIA — aggregatore prezzi B2B, utile per intelligence ma non fonte veicoli |
| Carmarket (ex CarNext/LeasePlan) | carmarket.com | Pan-EU | Ex-leasing Ayvens | N/D | Account business | N/D | ALTA — ex-LeasePlan + ALD (ora Ayvens). Veicoli ex-leasing di qualita', documentati. Rebrand 2024-2025 |

---

## SEZIONE C — PORTALI OEM (Certified Pre-Owned)

| Portale | URL | Marchio | Tipo | Volume | Accesso | Costo | Rilevanza ARGOS |
|---------|-----|---------|------|--------|---------|-------|-----------------|
| BMW Premium Selection | bmw.it/usato, bmw-selection.com | BMW | CPO dealer autorizzati | N/D (solo dealer BMW) | Solo dealer BMW autorizzati | N/A per acquirenti privati/broker | BASSA — stock solo presso concessionarie BMW ufficiali. Prezzi CPO = premium elevato. Nessun margine |
| Mercedes-Benz Certified | mercedes-benz.it/usato | Mercedes | CPO dealer autorizzati | N/D | Solo dealer MB autorizzati | N/A | BASSA — stesse considerazioni BMW |
| Audi Approved Plus | audi.it/usato | Audi | CPO dealer autorizzati | N/D | Solo dealer Audi autorizzati | N/A | BASSA — prezzi CPO non lasciano margine a ARGOS |
| Das WeltAuto | dasweltauto.it | VW Group | CPO multi-brand | N/D | Solo dealer VW Group | N/A | BASSA — VW/Seat/Skoda, non target premium ARGOS |
| Spoticar | spoticar.it | Stellantis | CPO multi-brand | N/D | Solo dealer Stellantis | N/A | BASSA — Peugeot/Citroen/Fiat, non target ARGOS |
| Porsche Approved | porsche.com/approved | Porsche | CPO | N/D | Solo dealer Porsche | N/A | BASSA — prezzi Porsche CPO non arbitraggiabili |

**Nota su CPO**: I portali OEM non sono fonti per ARGOS. I veicoli CPO hanno prezzi premium che eliminano il margine. Utili SOLO come benchmark prezzo IT per modelli specifici.

---

## SEZIONE D — PORTALI SPECIALIZZATI (Premium / Supercar / Classiche)

| Portale | URL | Tipo | Volume | Accesso | Costo | Rilevanza ARGOS |
|---------|-----|------|--------|---------|-------|-----------------|
| Classic Trader | classictrader.com | Classiche + supercar | 30K+ | Registrazione | Gratuito sfoglio | BASSA — target diverso da ARGOS (veicoli >20 anni o supercar >€100K) |
| Bring a Trailer (BaT) | bringatrailer.com | Aste classiche/collectors | 450+ lot/settimana, ~$853M fatturato annuo | Account registrato | Buyer premium ~5% | BASSA — mercato USA-centric, veicoli collector. Non scalabile per ARGOS |
| James Edition | jamesedition.com | Luxury marketplace globale | N/D, 1M+ utenti HNW/mese | Account | Inserzione a pagamento | BASSA — per veicoli >€80K, target diverso |
| DuPont Registry | dupontregistry.com | Luxury/exotic USA | N/D | Account | Abbonamento | BASSA — prevalentemente USA, non EU |
| Hemmings | hemmings.com | Classiche USA | N/D | Account | Abbonamento | BASSA — USA, classiche americane |
| Classic.com | classic.com | Aggregatore classiche | Aggrega BaT + altri | Gratuito | Gratuito | BASSA — solo classiche |
| Carvago.com | carvago.com | Cross-border B2C EU | Milioni veicoli verificati | Account dealer (Carvago Partner) | Commissione su vendita | MEDIA — si rivolgono a consumatori finali (B2C), ma ARGOS potrebbe usarli come fonte per trovare veicoli verificati. CarAudit™ include ispezione 300 punti |
| The Parking | theparking.eu | Aggregatore pan-EU | Milioni annunci da piu' portali | Gratuito | Gratuito | ALTA — aggrega Mobile.de + AS24 + portali nazionali in un'unica ricerca. Ottimo per overview rapido |
| USCar-Trader | uscar-trader.com | Import USA→EU | N/D | Account | N/D | BASSA — veicoli USA, non target ARGOS |

---

## SEZIONE E — AGGREGATORI / STRUMENTI DATI

| Strumento | URL | Tipo | Copertura | Costo | Rilevanza ARGOS |
|-----------|-----|------|-----------|-------|-----------------|
| Carapis.com | carapis.com | API dati automotive (25+ mercati) | Mobile.de, AS24, Autovit, Otomoto, altri | Subscription (pricing non dichiarato — stima €200-500/mese) | ALTA — API unica per accedere dati strutturati da piu' portali. Parser Mobile.de con anti-detection. Ideale per futuro sistema ARGOS automatizzato |
| AUTO-API.com | auto-api.com | API aggregata | Mobile.de principalmente | Subscription | ALTA — specializzato Mobile.de, dati real-time (nuovi listing entro 1-2 min dalla pubblicazione) |
| CarGurus EU | cargurus.co.uk | B2C con price intelligence | UK principalmente, espansione EU | Gratuito sfoglio | BASSA — price intelligence utile ma mercato UK |
| Apify car scrapers | apify.com | Scraper as-a-service | Mobile.de, AS24, Otomoto, altri | Pay-per-use (stima €0.10-0.50 per 1000 listing) | ALTA — soluzione tecnica rapida, nessuna infrastruttura da gestire |
| Car.info | car.info | VIN lookup + history | Scandinavia principalmente | Gratuito base | MEDIA — utile per history check complementare a carVertical |
| AutoUncle.it | autouncle.it | Aggregatore prezzi IT | Tutti portali IT | Gratuito | ALTA — ottimo benchmark rapido prezzi IT senza registrazione |
| Motorwatch.co.uk | motorwatch.co.uk | Price tracker UK | AutoTrader + PH + Cinch | Gratuito | BASSA — UK only |

---

## RIEPILOGO STRATEGICO PER ARGOS

### Mercati prioritari (ordine)

```
1. GERMANIA (DE)      — Mobile.de + AutoScout24.de — volume massimo, prezzi benchmark, qualita' alta
2. PAESI BASSI (NL)   — Marktplaats + AutoTrack — veicoli NL spesso senza VAT IT, buon arbitraggio
3. BELGIO (BE)        — AS24.be + 2dehands — prossimita' DE, regime fiscale favorevole
4. AUSTRIA (AT)       — Willhaben — veicoli austriaci ben mantenuti, logistica via Brennero
5. REPUBBLICA CECA    — Sauto.cz + AS24.cz — prezzi 15-20% sotto DE, mercato sottovalutato
6. POLONIA (PL)       — Otomoto — volume enorme, prezzi bassi (attenzione km)
7. SVEZIA (SE)        — Blocket + Bytbil — veicoli svedesi premium, logistica complicata
```

### Mercati da escludere

```
X DANIMARCA    — Tasse auto altissime (150% registration tax), prezzi distorti
X NORVEGIA     — Extra-EU, burocrazia, mercato EV
X UK           — Post-Brexit, sdoganamento, extra costi €2.000-4.000
X ROMANIA/BG   — Rischio qualita' e km falsificati
X SPAGNA/FR    — Prezzi non competitivi vs DE, logistica costosa
```

### Stack tecnico consigliato per ARGOS data sourcing

```
FASE 1 (attuale — manual):
  - Mobile.de: ricerca manuale filtrata per BMW/Mercedes/Audi, 2018-2023, <80K km, <€30K
  - AutoScout24.de: stesso filtro
  - The Parking: overview rapido multi-paese
  - Sauto.cz: mercato CZ sottovalutato

FASE 2 (semi-automatizzato):
  - Carapis.com API: parser Mobile.de strutturato, aggiornamento real-time
  - Apify scrapers: AS24.de + Marktplaats + Otomoto
  - AutoUncle.it: benchmark automatico prezzi IT
  - Costo stimato: €300-600/mese per 10.000-50.000 listing monitorati

FASE 3 (automatizzato full):
  - Pipeline: Carapis API → filtro CoVe → notifica Telegram → proposta dealer
  - Costo target: €500/mese infrastruttura per copertura 7 mercati
```

### Portali B2B prioritari per accesso diretto

```
PRIORITY 1: eCarsTrade — enorme stock EU, registrazione accessibile, barriera linguistica = moat ARGOS
PRIORITY 2: Exleasingcar.com — ex-leasing qualita', documentazione completa
PRIORITY 3: Carmarket.com (Ayvens) — ex LeasePlan/ALD, flotte certificate, qualita' alta
PRIORITY 4: CarOnSale — registrazione gratuita, stock DE wholesale
PRIORITY 5: OpenLane (ADESA) — leader EU wholesale, deposito richiesto (capex)
PRIORITY 6: BCA — fisico+online, richiede ATECO 45.11.01 o EU entity (OUE Estone)
```

---

## TABELLA SINTETICA — QUICK REFERENCE

| Portale | Paese | B2C/B2B | Scraping | Costo | Score ARGOS |
|---------|-------|---------|----------|-------|-------------|
| Mobile.de | DE | B2C | SI (Apify/Carapis) | Gratis | 10/10 |
| AutoScout24.de | DE/EU | B2C | SI (Carapis) | Gratis | 10/10 |
| The Parking | EU | Aggregatore | Gratis UI | Gratis | 9/10 |
| Marktplaats.nl | NL | B2C | SI | Gratis | 8/10 |
| Willhaben.at | AT | B2C | SI | Gratis | 8/10 |
| Sauto.cz | CZ | B2C | SI | Gratis | 8/10 |
| Otomoto.pl | PL | B2C | SI (Apify) | Gratis | 7/10 |
| Blocket.se | SE | B2C | SI | Gratis | 7/10 |
| eCarsTrade | EU | B2B | No (solo dealer) | Fee transazione | 9/10 |
| Exleasingcar | EU | B2B | No (account) | N/D | 8/10 |
| Carmarket (Ayvens) | EU | B2B | No (account) | N/D | 8/10 |
| CarOnSale | EU | B2B | No (dealer) | Gratis reg. | 8/10 |
| AutoProff | EU | B2B | No (dealer) | Subscription | 7/10 |
| OpenLane | EU | B2B | No (dealer+deposito) | Fee | 7/10 |
| BCA | EU | B2B | No (ATECO req.) | Subscription | 6/10 |
| AutoTrack.nl | NL | B2C | SI | Gratis | 7/10 |
| Bytbil.com | SE | B2C | Limitato | Gratis | 7/10 |
| LeBonCoin | FR | B2C | SI | Gratis sfoglio | 5/10 |
| LaCentrale.fr | FR | Dealer | Limitato | Gratis | 5/10 |
| Hasznaltauto.hu | HU | B2C | SI | Gratis | 5/10 |
| AutoScout24.it | IT | B2C | SI | Gratis | 9/10 (benchmark) |
| Automobile.it | IT | Dealer | Limitato | Gratis | 8/10 (benchmark) |
| Subito.it | IT | B2C | SI | Gratis | 8/10 (benchmark) |
| Carapis.com | EU | API | N/A (e' l'API) | Subscription | 9/10 (infra) |
| AutoUncle.it | IT | Aggregatore | No (UI) | Gratis | 7/10 (benchmark) |

---

## FONTI RICERCA

- [Marlog Europe — Best European Websites for Used Cars](https://marlog-europe.com/blog/find-your-dream-vehicle-the-best-european-websites-for-used-cars/)
- [NerdBot — Best B2B Car Marketplaces Europe 2026](https://nerdbot.com/2026/01/05/the-best-b2b-car-marketplaces-in-europe-2026/)
- [TechBullion — Best Marketplaces Wholesale Vehicles Europe 2026](https://techbullion.com/best-marketplaces-for-wholesale-used-vehicles-in-europe-2026/)
- [AIM Group — Blocket calo listing privati marzo 2026](https://aimgroup.com/2026/03/18/sharp-decline-in-private-used-car-listings-on-sweden-based-blocket/)
- [AIM Group — AutoScout24 acquires AutoTrack e Gaspedaal dic 2025](https://aimgroup.com/2025/12/03/autoscout24-acquires-netherlands-based-autotrack-and-gaspedaal/)
- [AIM Group — LaCentrale acquisita da Prosus €1.1B 2025](https://aimgroup.com/2025/09/26/olx-group-to-buy-france-based-auto-marketplace-la-centrale-for-1-3b/)
- [OpenPR — eCarsTrade B2B platform](https://www.openpr.com/news/4383218/what-makes-ecarstrade-a-go-to-b2b-car-auction-platform)
- [Dealcar.io — Portali Spagna 2025](https://www.dealcar.io/en/blog/mejores-portales-para-vender-coches-en-espana)
- [Apify — Mobile.de scraper](https://apify.com/ivanvs/mobile-de-scraper/api)
- [Carapis — Mobile.de parser](https://carapis.com/parsers/mobile.de/intro)
- [AIM Group — LeBonCoin comincia a far pagare venditori auto 2025](https://aimgroup.com/2025/04/22/lbc-brings-in-charges-for-vehicle-sellers/)
- [AutoProff B2B platform](https://www.autoproff.com/)
- [eCarsTrade](https://ecarstrade.com/)
- [CarOnSale](https://www.caronsale.com/)
- [OpenLane (ex ADESA)](https://openlane.eu)
- [BCA Group](https://www.bca.com/)
- [Carvago](https://carvago.com/)
- [The Parking EU](https://www.theparking.eu/)
- [Vend Marketplaces (ex Schibsted)](https://vend.com/brands/mobility)
- [AIM Group — OtoMoto.pl one of Europe's surprising auto giants](https://aimgroup.com/2017/03/02/otomoto-pl-one-of-europes-surprising-auto-giants/)
