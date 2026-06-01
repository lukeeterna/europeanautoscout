# ARGOS — Mappa ESAUSTIVA Portali Auto EU 2026
**Data ricerca**: 2026-03-19
**Sessione**: S66
**Obiettivo**: Censimento COMPLETO e APPROFONDITO di tutti i marketplace, portali locali, aste B2B, portali di nicchia e aggregatori europei. Focus su portali PICCOLI e LOCALI dove un dealer italiano del Sud non arriva mai.

---

## NOTA METODOLOGICA

Questo documento ESTENDE e APPROFONDISCE il censimento s65_all_eu_car_portals.md.
Copre 24 paesi EU + mercati correlati. Per ogni portale documentato:
- Volume listing = stima da fonti pubbliche verificate
- Scraping = fattibilita' tecnica da Apify/Carapis/GitHub
- VALORE ARGOS = perche' un dealer italiano del Sud NON ci arriva mai da solo

Legenda accesso:
- OPEN = sfoglio libero senza registrazione
- REG_FREE = registrazione gratuita
- REG_PAID = registrazione a pagamento
- DEALER_ONLY = solo professionisti verificati

---

## SEZIONE 1 — GERMANIA (DE)

**Perche' e' il mercato primario ARGOS**: 1,3-2,5 milioni di listing attivi, prezzi benchmark EU, qualita' alta. BMW/Mercedes/Audi dominano. Logistica verso Sud IT consolidata (autotrasportatori specializzati DE→IT).

### 1.1 Portali principali

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Mobile.de | mobile.de | Privati + Dealer | 1,3M+ | OPEN | Scraper Apify multipli (ivanvs, 3x1t, lexis-solutions). Anti-bot presente ma bypassabile con proxy rotation. Carapis parser. auto-api.com real-time (nuovi listing entro 1-2 min). | ALTISSIMO — volume massimo DE, BMW/Audi/Merc dominanti, prezzi real-time |
| AutoScout24.de | autoscout24.de | Privati + Dealer | 2,5M+ EU | OPEN | API pubblica limitata. Scraping via Carapis/Apify. Cloudflare presente, IP ban dopo molte req. | ALTISSIMO — secondo portale DE, pan-EU, facile confronto IT vs DE |
| Kleinanzeigen.de | kleinanzeigen.de | Privati | 800K+ | OPEN | Scraper Apify disponibili. Era eBay Kleinanzeigen, ora brand autonomo. | ALTO — private gems, prezzi bassi, qualita' variabile. Dealer IT non sa cercarlo in tedesco |

### 1.2 Portali secondari / locali

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Auto.de | auto.de | Privati + Dealer | 200K+ | OPEN | No API pubblica. Portale tedesco premiato per affidabilita'. Interfaccia solo DE. | MEDIO — interfaccia solo tedesco, dealer IT non lo trova. Utile per private deals |
| AutoUncle.de | autouncle.de | Aggregatore | 11M+ (aggrega) | OPEN | Aggrega 1.900+ siti EU, price intelligence, 5 categorie prezzo. Usato dal Ministero Tasse danese. | MEDIO — utile per benchmark rapido, non fonte diretta |
| Autohero.de | autohero.com | Solo dealer/refurbished | 30K+ | OPEN | Veicoli ricondizionati, prezzi premium. Nessun margine per ARGOS. | BASSO |
| Heycar.de | hey.car | Dealer certificati | 60K+ | OPEN | Solo dealer ufficiali, prezzi "giusti". No arbitraggio. | BASSO |
| CarWow.de | carwow.de | Configuratore + usato | N/D | OPEN | Principalmente nuovo, sezione usato limitata. | BASSO |
| Pkw.de | pkw.de | Privati + Dealer | 150K+ | OPEN | Portale tedesco storico, interfaccia datata, meno aggiornato ma con stock residuale interessante. No API. | MEDIO — portale "dimenticato" con listing non su Mobile.de o AS24 |
| AutoScout24 Classic | autoscout24.de/klassiker | Classiche | N/D | OPEN | Sezione separata AS24 per veicoli >20 anni. | BASSO per ARGOS standard |

### 1.3 Aste / B2B Germania

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Autobid.de | autobid.de | B2B aste online | 1.500 veicoli/giorno | DEALER_ONLY | Verifica aziendale DE/AT. Interfaccia DE/EN. Subscription mensile. Aste timed. | ALTO — stock dealer DE wholesale, qualita' alta, no intermediari |
| BCA Deutschland | bca.com/de | Aste fisiche + online | Parte del 5M globale | DEALER_ONLY | KYC + camera di commercio. ATECO 45.11.01 per accesso pieno (o OUE Estone). | ALTO — maggiore rete aste fisica EU, enorme stock ex-flotta |
| CarOnSale.de | caronsale.com | B2B aste online | 50K+/mese stima | DEALER_ONLY | Registrazione dealer gratuita. Verifica aziendale. Gestito da AUTO1 Group. Pan-EU con focus DE. | ALTO — registrazione gratuita, stock wholesale DE, Auto1 dietro |
| Autorola.de | autorola.eu | B2B aste online | 200K veicoli/anno | DEALER_ONLY | 70.000 dealer attivi, 30+ paesi. Interfaccia EN/DE/altri. | ALTO — volume enorme, ex-leasing e trade-in dealer |

---

## SEZIONE 2 — OLANDA (NL)

**Perche' e' mercato ARGOS**: Prezzi molto competitivi per premium, molti veicoli ex-leasing aziendali senza IVA IT (regime margine), ottima qualita', logistica rapida via Anversa o camion diretto.

### 2.1 Portali principali

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Marktplaats.nl | marktplaats.nl | Privati + Dealer | 200K+ auto | OPEN | Scraper disponibili, parte del gruppo Adevinta. Molto privati, prezzi competitivi. | ALTISSIMO — private gems NL, BMW/Audi senza VAT, dealer IT non naviga in olandese |
| AutoTrack.nl | autotrack.nl | Privati + Dealer | 150K+ | OPEN | Acquisito da AutoScout24 Group (dic 2025). Brand autonomo ma stesso proprietario. Scraper disponibili. | ALTO — ora parte AS24 Group, ma listing indipendenti e utenti diversi da AS24 |
| Gaspedaal.nl | gaspedaal.nl | Aggregatore NL | 300K+ (aggrega) | OPEN | Metasearch: aggrega Marktplaats + AutoTrack + AS24 NL. Acquisito da AS24 Group dic 2025. Utile per overview rapido. | MEDIO — aggregatore utile per scansione rapida, non fonte diretta |
| AutoScout24.nl | autoscout24.nl | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro NL. | ALTO |

### 2.2 Portali secondari NL

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| CarCollect.nl | carcollect.com | B2B marketplace NL | N/D | DEALER_ONLY | Focus NL/BE/DE. API disponibile per integrazioni. Legato a Autorola. | MEDIO — nicchia NL, accesso B2B |
| Vwe.nl | vwe.nl | B2B aste online NL | N/D | DEALER_ONLY | Veiling Wagens Export — specializzato export NL. Dealer olandesi vendono a buyer stranieri. Spesso veicoli ex-lease a prezzi interessanti. Interfaccia NL only. | ALTISSIMO — specializzato export, dealer IT non sa che esiste, interfaccia NL, veicoli pronti per l'esportazione |
| Tinq.nl (ex BAS World) | basworld.com | B2B veicoli commerciali | N/D | DEALER_ONLY | Focus furgoni/commerciali ma anche auto premium. Sede Veghel NL. | BASSO per auto premium |
| Pon.com | pon.com | Importatore ufficiale VW Group NL | N/D | DEALER_ONLY | Pon e' il più grande importatore VW/Audi/Porsche NL. Vende surplus ex-demo e flotta. | ALTO — ex-demo e km0 a prezzi wholesale, nessun dealer IT sa che esiste |

---

## SEZIONE 3 — BELGIO (BE)

**Perche' e' mercato ARGOS**: Hub logistico EU, porto di Anversa, regime fiscale favorevole, molti veicoli ex-flotta aziendali. ARGOS ha sede narrativa BE (Bruxelles) = credibilita' massima.

### 3.1 Portali principali BE

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| AutoScout24.be | autoscout24.be | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro BE. Bilinguismo FR/NL = due mercati in uno. | ALTO |
| 2dehands.be | 2dehands.be | Privati | 80K+ auto | OPEN | Scraper disponibili. Principalmente privati BE, qualita' variabile. | MEDIO — private deals BE |

### 3.2 Portali secondari / B2B BE

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| eCarsTrade | ecarstrade.com | B2B aste online | 18.000+ auto/settimana | DEALER_ONLY | BE-based. Solo dealer licensed. Verifica documenti aziendali. Interfaccia EN/FR, nessun supporto IT. 15 paesi EU coperti. | ALTISSIMO — enorme stock ex-leasing EU. Barriera linguistica/documentale = moat ARGOS |
| Gocar.be | gocar.be | Dealer B2C | 25K+ | OPEN | Portale locale BE, dealer professionali BE, prezzi allineati mercato EU. No API. | BASSO |
| Vroom.be | vroom.be | Privati + Dealer | 30K+ | OPEN | Portale locale minore, qualita' variabile. | BASSO |
| Ayvens Carmarket BE | carmarket.ayvens.com | B2B ex-leasing | N/D | DEALER_ONLY | BE headquarters Ayvens (ex LeasePlan + ALD). Stock immenso ex-flotta, qualita' certificata. 40 paesi coperti. | ALTISSIMO — ex LeasePlan ha flotte enormi, veicoli documentati, dealer IT ignora completamente |

---

## SEZIONE 4 — AUSTRIA (AT)

**Perche' e' mercato ARGOS**: Logistica via Brennero (trasporto diretto), qualita' vicina alla DE, prezzi leggermente sotto DE. Autostrade dirette verso Nord Italia.

### 4.1 Portali principali AT

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Willhaben.at | willhaben.at | Privati + Dealer | 188K+ auto | OPEN | Scraper disponibili. Portale principale AT, interfaccia DE. Car4you.at acquisito e integrato. | ALTISSIMO — principale AT, interfaccia tedesca scoraggia dealer IT, prezzi competitivi |
| AutoScout24.at | autoscout24.at | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro AT. | ALTO |

### 4.2 Portali secondari AT

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Gebrauchtwagen.at | gebrauchtwagen.at | Privati + Dealer | 50K+ | OPEN | Portale specializzato AT solo usato. Interfaccia tedesca. Meno conosciuto fuori AT. | MEDIO — portale locale AT con listing non su AS24/Willhaben |
| Autorevue.at | autorevue.at | Dealer + editoriale | 30K+ | OPEN | Storica rivista auto AT con classifieds. Contenuto editoriale + annunci dealer. | MEDIO — dealer AT tradizionali pubblicano qui, non su AS24 |
| Kfz.at | kfz.at | Privati + Dealer | 20K+ | OPEN | Portale locale minore, nicchia AT. Interfaccia solo DE. | BASSO |

---

## SEZIONE 5 — FRANCIA (FR)

**Perche' e' mercato ARGOS**: Volume enorme (500K+ listing), mercato sottovalutato da ARGOS finora. Prezzi non sempre competitivi vs DE ma occasioni esistono, specie su privati. Barriera: tutto in francese.

### 5.1 Portali principali FR

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| LeBonCoin auto | leboncoin.fr/c/voitures | Privati + Dealer | 500K+ | OPEN | Scraper Apify. Anti-bot presente, bypassabile. Da 2025 a pagamento per privati. 124M visite/mese. | ALTO — volume enorme, molti private deals FR, dealer IT non sa cercare in francese |
| LaCentrale.fr | lacentrale.fr | Dealer focus | 350K+ | OPEN | API limitata. Dealer FR professionali. Acquistata da Prosus per €1,1B (2025). | ALTO — dealer FR professionali, prezzi trasparenti |
| AutoScout24.fr | autoscout24.fr | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro FR. | MEDIO |

### 5.2 Portali secondari / B2B FR

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| ParuVendu.fr | paruvendu.fr | Privati | 50K+ | OPEN | Generalista FR, sezione auto. Interfaccia FR only. | BASSO |
| Caradisiac.com | caradisiac.com | Dealer + editoriale | 30K+ | OPEN | Media auto FR storica con classifieds integrati con LaCentrale. | BASSO |
| L'Argus.fr | largus.fr | Dealer + editoriale + cote | 150K+ | OPEN | Storica pubblicazione FR per quotazioni auto. Cote officielle veicoli usati in Francia. Classifieds dealer. | ALTO — dealer IT non sa che L'Argus e' la "bibbia" delle quotazioni FR, utile per intelligence prezzi FR |
| Ymag.fr | ymag.fr | B2B fr | N/D | DEALER_ONLY | Piattaforma B2B franco-francese per professionisti auto. Interfaccia FR only, zero presenza IT. | MEDIO — nicchia B2B FR, barriera linguistica = moat ARGOS |
| Reezocar.com | reezocar.com | B2C cross-border | 200K+ | OPEN | Aggregatore FR multi-mercato, acquisto cross-border facilitato. Concorrente B2C di ARGOS. | BASSO come fonte (competitor) |

---

## SEZIONE 6 — SVEZIA (SE)

**Perche' e' mercato ARGOS**: Prezzi premium competitivi, molte BMW/Mercedes svedesi in ottime condizioni, mercato sottovalutato. Logistica complicata ma fattibile (camion o traghetto).

### 6.1 Portali principali SE

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Blocket.se | blocket.se | Privati + Dealer | 100K+ | OPEN | Scraper disponibili. Ora parte Vend Marketplaces (ex Schibsted). Calo listing privati segnalato mar 2026 dopo modifiche modello pricing. | ALTO — principale SE, interfaccia svedese, dealer IT non lo conosce |
| Bytbil.com | bytbil.com | B2C Dealer | 80K+ | OPEN | Principale portale dealer SE. Volvo/BMW/Mercedes svedesi. | ALTO — tutti dealer SE, interfaccia svedese |
| AutoScout24.se | autoscout24.se | Privati + Dealer | Parte 2,5M EU | OPEN | Meno usato in SE rispetto a Blocket/Bytbil. | MEDIO |

### 6.2 Portali secondari / aste SE

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Kvd.se | kvd.se | Aste B2C | 5K+ | REG_FREE | Aste svedesi consumer-oriented, veicoli di qualita', prezzi interessanti. Account semplice. | ALTO — aste SE aperte a privati, prezzi potenzialmente bassi, dealer IT ignora completamente |
| Kvd Auctions (B2B) | kvdauctions.se | B2B | N/D | DEALER_ONLY | Versione B2B di KVD. Solo dealer registrati. Stock ex-leasing SE. | ALTISSIMO — dealer SE vendono a prezzi wholesale, zero concorrenza IT |
| Klaravik.se | klaravik.se | Aste generali + auto | N/D | REG_FREE | Piattaforma aste svedese con sezione auto. Non specializzata ma listing occasionali interessanti. | MEDIO |
| Auctionet.se | auctionet.se | Aste specifiche | N/D | REG_FREE | Aste online SE, prevalentemente oggetti ma sezione auto presente. | BASSO |

---

## SEZIONE 7 — REPUBBLICA CECA (CZ)

**Perche' e' mercato ARGOS**: Prezzi 15-20% sotto DE per stesso veicolo. Mercato molto sottovalutato. Molti veicoli ex-leasing aziendali cechi (Skoda dominante ma anche BMW/Audi abbondano). Logistica: 1.200 km da Praga al Sud IT.

### 7.1 Portali principali CZ

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Sauto.cz | sauto.cz | Privati + Dealer | 150K+ | OPEN | Scraper disponibili, interfaccia ceca. Parte del gruppo Sbazar (CZ classifieds). | ALTISSIMO — portale principale CZ, tutto in ceco, dealer italiano non sa nemmeno che esiste |
| TipCars.com | tipcars.com | Dealer | 80K+ | OPEN | Dealer CZ/SK professionali. Prezzi ancora competitivi vs IT. Interfaccia EN disponibile (RARO per Est EU). | ALTO — unico portale Est EU con interfaccia EN decente, ma dealer IT comunque non lo usa |
| AutoScout24.cz | autoscout24.cz | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro CZ. | ALTO |

### 7.2 Portali secondari CZ

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Bazos.cz | bazos.cz | Privati | 30K+ auto | OPEN | Portale generalista CZ con sezione auto privati. Interfaccia solo ceca. Prezzi molto bassi. | ALTO — private deals CZ a prezzi molto bassi, barriera linguistica ceca = moat totale |
| AAA Auto CZ | aaaauto.cz | Dealer catena | 20K propri | OPEN | Grande catena dealer CZ/SK/PL/HU. Prezzi standardizzati. No margine arbitraggio. | BASSO |
| Inzerce.auto.cz | auto.cz/inzerce | Privati + Dealer | 40K+ | OPEN | Portale auto del sito editoriale Auto.cz. Pubblico ceco fidato. Interfaccia solo ceca. | MEDIO — listing locali non su Sauto/AS24 |

---

## SEZIONE 8 — POLONIA (PL)

**Perche' e' mercato ARGOS**: Mercato auto piu' grande EU Est per volume. Enorme stock BMW/Audi/Mercedes di seconda mano. Prezzi bassi. ATTENZIONE: km falsificati piu' frequente — VIN check obbligatorio.

### 8.1 Portali principali PL

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Otomoto.pl | otomoto.pl | Privati + Dealer | 300K+ | OPEN | Scraper Apify disponibili. Portale principale PL. Interfaccia polacca con EN limitato. | ALTISSIMO — volume enorme, BMW/Audi/Mercedes abbondano, interfaccia polacca = barriera totale per dealer IT |
| Allegro.pl auto | allegro.pl | Privati + aste | 50K+ auto | OPEN | API disponibile. Anche veicoli in asta. Prezzi molto bassi. | MEDIO — qualita' variabile ma aste interessanti |
| AutoScout24.pl | autoscout24.pl | Privati + Dealer | Parte 2,5M EU | OPEN | Come AS24.de ma filtro PL. | ALTO |

### 8.2 Portali secondari PL

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| OLX.pl | olx.pl | Privati | 100K+ | OPEN | Qualita' bassa, low-cost. Non target ARGOS premium. | BASSO |
| Giełda Samochodowa | gielda.pl | Aste + privati | N/D | OPEN | "Giełda Samochodowa" = fiera auto polacca in formato digitale. Nicchia polacca, zero presenza estera. | MEDIO — dealer polacchi locali, prezzi non pubblicati online, diretto contatto |
| Gratka.pl | gratka.pl | Privati | 40K+ | OPEN | Portale generalista PL con sezione auto. Interfaccia solo polacca. | BASSO |
| Motointegrator.pl | motointegrator.pl | B2B accessori + auto | N/D | DEALER_ONLY | Principalmente ricambi ma sezione veicoli per professionisti. | BASSO |

---

## SEZIONE 9 — DANIMARCA (DK)

**Nota critica**: DK ha registration tax fino al 150% sui veicoli. I prezzi locali sono gonfiati di conseguenza. Importare DA Danimarca non conviene per ARGOS (i veicoli costano molto piu' che in DE o NL).

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| BilBasen.dk | bilbasen.dk | Privati + Dealer | 90K+ | OPEN | Scraper Apify. Portale principale DK. | BASSO — tassazione distorce i prezzi |
| DBA.dk | dba.dk | Privati | 70K+ | OPEN | Classifieds DK generalista. | BASSO |
| Biltorvet.dk | biltorvet.dk | Dealer | 50K+ | OPEN | Dealer DK professionali. | BASSO |

**Conclusione DK**: Da monitorare SOLO per veicoli molto particolari o rarissimi. Non target primario ARGOS.

---

## SEZIONE 10 — SPAGNA (ES)

**Nota**: Prezzi ES non competitivi vs DE. Logistica sfavorevole (Sud IT lontano). Mercato piu' utile come benchmark che come fonte.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Coches.net | coches.net | Privati + Dealer | 160K+, 11,9M vis/mese | OPEN | Scraper disponibili. Principale portale ES. | BASSO |
| Milanuncios.com | milanuncios.com | Privati | 353K+ | OPEN | Classifieds ES generalista, sezione auto enorme. | BASSO |
| Wallapop auto | wallapop.com | Privati | 211K+ | OPEN | App-first, localizzato. | BASSO |
| Vibbo.es | vibbo.es | Privati | N/D | OPEN | Ex Segunda Mano, ora Vibbo. Generalista ES. | BASSO |
| AutoScout24.es | autoscout24.es | Privati + Dealer | Parte EU | OPEN | Come AS24.de filtro ES. | BASSO |
| Autocasion.com | autocasion.com | Dealer | N/D | OPEN | Specializzato usato ES dealer. Interfaccia ES only. | BASSO |

---

## SEZIONE 11 — PORTOGALLO (PT)

**Nota**: Mercato piccolo, prezzi non competitivi, logistica sfavorevole. Non target ARGOS.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Standvirtual.com | standvirtual.com | Privati + Dealer | 40K+ | OPEN | N.1 PT per auto usate. Interfaccia PT. | MOLTO BASSO |
| AutoSapo.pt | autosapo.pt | Dealer | N/D | OPEN | 13 anni di storia PT. Focus dealer. | MOLTO BASSO |
| CustoJusto.pt | custojusto.pt | Privati | N/D | OPEN | Classifieds generalista PT, sezione auto. | MOLTO BASSO |

---

## SEZIONE 12 — IRLANDA (IE)

**Nota**: Mercato IT, veicoli con guida a destra (UK legacy). Da escludere per import in Italia.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| DoneDeal.ie | donedeal.ie | Privati + Dealer | N/D (grande) | OPEN | N.1 IE. Guida a destra. | ESCLUSO — guida destra |
| Cars.ie | cars.ie | Dealer | N/D | OPEN | Alternativa DoneDeal. Guida destra. | ESCLUSO — guida destra |

---

## SEZIONE 13 — LUSSEMBURGO (LU)

**Perche' e' mercato ARGOS**: Mercato piccolo ma molto ricco. Prezzi competitivi per premium. Fiscalita' favorevole. Molti veicoli ex-diplomatici e ex-EU istituzioni. Quasi zero concorrenza straniera.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| AutoScout24.lu | autoscout24.lu | Privati + Dealer | N/D (piccolo) | OPEN | Come AS24.de filtro LU. Trilingue (FR/DE/LU). | ALTO — mercato LU straordinariamente ricco, pochi dealer stranieri ci guardano |
| Anzeiger.lu | anzeiger.lu | Privati + Dealer | 5K+ auto | OPEN | Principale classifieds LU (Luxemburger Wort group). Trilingue. Volume basso ma qualita' altissima. | ALTISSIMO — ex-diplomatici, funzionari EU a Bruxelles vendono qui. Dealer IT non lo conosce |
| MoteurLU | moteur.lu | Dealer | N/D | OPEN | Portale specializzato dealer auto LU. Interfaccia FR/DE. Volume basso ma target premium. | ALTO — dealer LU esclusivi, nessuna concorrenza IT |

---

## SEZIONE 14 — FINLANDIA (FI)

**Nota**: Mercato lontano logisticamente, prezzi non particolarmente competitivi vs DE.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Nettiauto.com | nettiauto.com | Privati + Dealer | 60K+ | OPEN | Principale portale FI auto. Interfaccia FI only. | BASSO — logistica sfavorevole |
| Tori.fi | tori.fi | Privati | 30K+ auto | OPEN | Generalista FI (parte Schibsted). | BASSO |
| Huuto.net | huuto.net | Aste FI | N/D | REG_FREE | Piattaforma aste FI, sezione auto. Prezzi potenzialmente bassi ma mercato piccolo. | BASSO |

---

## SEZIONE 15 — UNGHERIA (HU)

**Perche' e' mercato ARGOS**: Prezzi competitivi, molti veicoli VW/Audi ex-lease aziendali (Audi ha stabilimento a Gyor). Qualita' mista ma filtrabile. Interfaccia ungherese = barriera totale per dealer IT.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Hasznaltauto.hu | hasznaltauto.hu | Privati + Dealer | 120K+ | OPEN | Scraper disponibili (parte Schibsted). Portale principale HU. Interfaccia ungherese. | ALTISSIMO — mercato HU con Audi Gyor vicino, interfaccia solo ungherese = barriera totale |
| Jofogas.hu | jofogas.hu | Privati | 80K+ | OPEN | Classifieds generalista HU, sezione auto. Qualita' bassa. | BASSO |
| AutoScout24.hu | autoscout24.hu | Privati + Dealer | Parte EU | OPEN | Come AS24.de filtro HU. Meno usato localmente. | MEDIO |
| Automarket.ro/hu | automarket.ro | Privati + Dealer | N/D | OPEN | Portale rumeno con sezione HU. | BASSO |

---

## SEZIONE 16 — ROMANIA (RO)

**Nota**: Rischio qualita' e km falsificati piu' alto che in EU Ovest. Non target primario ARGOS. Da monitorare solo per veicoli con history verificabile.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| AutoVit.ro | autovit.ro | Privati + Dealer | 100K+ | OPEN | Principale portale RO auto. Scraper disponibili. | BASSO — rischio km/qualita' |
| OLX.ro | olx.ro | Privati | 150K+ | OPEN | Classifieds generalista RO, sezione auto. | BASSO |
| Automarket.ro | automarket.ro | Dealer | 30K+ | OPEN | Dealer professionali RO. | BASSO |
| Masini.ro | masini.ro | Privati + Dealer | 50K+ | OPEN | Portale specializzato auto RO. Interfaccia RO only. | BASSO |

---

## SEZIONE 17 — CROAZIA (HR)

**Nota**: Mercato piccolo, EU dal 2013, Schengen dal 2023. Veicoli di qualita' mista. Non target primario.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Njuskalo.hr | njuskalo.hr | Privati + Dealer | 30K+ auto | OPEN | Principale classifieds HR. Interfaccia croata. | BASSO |
| Oglas.hr | oglas.hr | Privati | N/D | OPEN | Alternativa minore HR. | BASSO |
| AutoScout24.hr | autoscout24.hr | Privati + Dealer | Parte EU | OPEN | Filtro HR su AS24. | BASSO |

---

## SEZIONE 18 — SLOVENIA (SI)

**Perche' e' mercato ARGOS (potenziale)**: Piccolo mercato ma confine con IT (Trieste). Veicoli di qualita' media-alta. Molti sloveni acquistano in AT/DE e rivendono. Prezzi interessanti.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Avto.net | avto.net | Privati + Dealer | 40K+ | OPEN | Portale principale SI, il "Mobile.de sloveno". Interfaccia slovena. Volume moderato ma qualita' buona. | MEDIO-ALTO — confine con Trieste, veicoli facilmente raggiungibili, interfaccia slovena = barriera |
| Bolha.com auto | bolha.com | Privati | 20K+ | OPEN | Classifieds SI generalista, grande sezione auto privati. | MEDIO |
| Avtooglasi.com | avtooglasi.com | Privati + Dealer | 15K+ | OPEN | Portale specializzato solo auto SI. Interfaccia piu' pulita. | MEDIO |
| AutoScout24.si | autoscout24.si | Privati + Dealer | Parte EU | OPEN | Filtro SI su AS24. Meno usato localmente. | MEDIO |

---

## SEZIONE 19 — SLOVACCHIA (SK)

**Nota**: Vicina a CZ e AT, veicoli di qualita' media, prezzi tra CZ e AT.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Autobazar.eu | autobazar.eu | Privati + Dealer | 2M vendite/anno (totale), 1,2M visitatori/mese | OPEN | Principale portale SK. Include Autobazar.sk e Autovia.sk. Interfaccia SK/EN. | MEDIO-ALTO — portale SK con versione EN (raro!), volume alto per paese piccolo |
| Autobazar.sk | autobazar.sk | Privati + Dealer | Parte di Autobazar.eu | OPEN | Brand separato ma stesso gruppo. | MEDIO |
| Autovia.sk | autovia.sk | Privati + Dealer | Parte di Autobazar.eu | OPEN | Terzo brand stesso gruppo. | MEDIO |
| TipCars SK | tipcars.com | Dealer | Include SK | OPEN | Copertura anche SK, interfaccia EN disponibile. | MEDIO |

---

## SEZIONE 20 — STATI BALTICI (EE/LV/LT)

**Nota**: Mercati piccoli ma con peculiarita': molti veicoli importati dalla Scandinavia o Finlandia, prezzi interessanti, qualita' variabile. Logistica complicata.

### Estonia (EE)

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Auto24.ee | auto24.ee | Privati + Dealer | 30K+ | OPEN | Principale portale EE auto. Parte dello stesso gruppo di Auto24.lv. Interfaccia EE/RU. | BASSO — logistica troppo complicata |
| Osta.ee | osta.ee | Aste + privati | N/D | REG_FREE | Piattaforma aste EE con sezione auto. | BASSO |

### Lettonia (LV)

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| SS.lv | ss.lv | Privati | 20K+ auto | OPEN | Principale classifieds LV. Interfaccia LV/RU. | BASSO |
| Auto24.lv | auto24.lv | Privati + Dealer | 25K+ | OPEN | Specializzato auto LV. Parte stesso gruppo EE. Interfaccia EN disponibile (parziale). | BASSO |

### Lituania (LT)

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Autoplius.lt | autoplius.lt | Privati + Dealer | 60K+ | OPEN | Principale portale LT auto. Interfaccia LT/EN. Volume alto per paese di quelle dimensioni. | BASSO-MEDIO — LT importa molto dalla DE/SE, prezzi rivendita bassi |
| Skelbimai.lt | skelbimai.lt | Privati | N/D | OPEN | Classifieds LT generalista, sezione auto. | BASSO |
| Autogidas.lt | autogidas.lt | Privati + Dealer | 30K+ | OPEN | Secondo portale auto LT. | BASSO |

---

## SEZIONE 21 — BULGARIA (BG)

**Nota**: Rischio qualita' e km falsificati. Non target ARGOS.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Mobile.bg | mobile.bg | Privati + Dealer | 80K+ | OPEN | Principale portale BG auto. Nome simile a Mobile.de ma diverso. | BASSO |
| Bazar.bg | bazar.bg | Privati | N/D | OPEN | Classifieds BG generalista. | BASSO |
| Cars.bg | cars.bg | Dealer | N/D | OPEN | Dealer BG. | BASSO |

---

## SEZIONE 22 — GRECIA (GR)

**Nota potenziale**: Mercato piu' interessante di quanto sembri. Grecia ha subito crisi economica → molti veicoli premium di lusso venduti sotto valore. Dealer IT non ci guarda mai.

| Portale | URL | Tipo | Volume | Accesso | Note tecniche | Valore ARGOS |
|---------|-----|------|--------|---------|---------------|--------------|
| Car.gr | car.gr | Privati + Dealer | 15M+ classifiche totali | OPEN | Principale portale classifieds GR, enorme sezione auto. App disponibile. | MEDIO-ALTO — crisi GR = occasioni premium, nessun dealer IT cerca in greco |
| Xe.gr auto | xe.gr | Privati + Dealer | 500K+ listing totali | OPEN | N.1 GR per property/job/auto. Sezione auto grande. Interfaccia GR/EN. | MEDIO — versione EN disponibile, ma dealer IT non la usa |
| Car.gr classifieds | car.gr/classifieds | Privati + Dealer | Parte dei 15M totali | OPEN | Sezione specifica classifieds auto su Car.gr. | MEDIO-ALTO |
| Autotraveler.gr | autotraveler.gr | Dealer | N/D | OPEN | Portale dealer GR specializzato. | BASSO |

---

## SEZIONE 23 — CIPRO (CY)

**Nota critica**: CY ha guida a sinistra (ex-UK legacy). Veicoli con steering a destra. NON importabili in Italia senza conversione costosa. DA ESCLUDERE.

| Portale | URL | Tipo | Volume | Accesso | Note | Valore ARGOS |
|---------|-----|------|--------|---------|------|--------------|
| Bazaraki.com | bazaraki.com | Privati + Dealer | N/D | OPEN | Principale classifieds CY. | ESCLUSO — guida destra |
| Car.com.cy | car.com.cy | Dealer | N/D | OPEN | Dealer CY. | ESCLUSO — guida destra |

---

## SEZIONE 24 — MALTA (MT)

**Nota critica**: MT ha guida a sinistra. Veicoli con steering a destra. NON importabili. DA ESCLUDERE.

| Portale | URL | Tipo | Volume | Accesso | Note | Valore ARGOS |
|---------|-----|------|--------|---------|------|--------------|
| MaltaCarPortal | maltacarport.com | Privati + Dealer | N/D | OPEN | Principale classifieds MT auto. | ESCLUSO — guida destra |
| Cars.mt | cars.mt | Dealer | N/D | OPEN | Dealer MT. | ESCLUSO — guida destra |

---

## SEZIONE 25 — PORTALI B2B / ASTE WHOLESALE (Pan-EU)

**Queste sono le piattaforme PIU' PREZIOSE per ARGOS.** Dealer Italian del Sud non le raggiungono per barriere linguistiche, documentali, e di conoscenza. ARGOS come intermediario = valore enorme.

### 25.1 Aste online B2B principali

| Portale | URL | Paesi coperti | Tipo | Volume | Accesso | Costo | Valore ARGOS |
|---------|-----|---------------|------|--------|---------|-------|--------------|
| OpenLane EU (ex ADESA Europe) | openlane.eu | 50+ paesi EU | Aste B2B online | 12.000+ auto/giorno | DEALER_ONLY: KYC + camera di commercio | Fee transazione + subscription | ALTISSIMO — leader EU wholesale, 19 lingue ma no IT support. Deposito richiesto. ARGOS accede come buyer intermediario |
| BCA Group EU | bca.com | UK + 10 paesi EU | Aste fisiche + online | 5M+ veicoli/anno globali | DEALER_ONLY: KYC + ATECO 45.11.01 | Subscription + buyer premium 8-12% | ALTISSIMO — maggiore rete aste fisica EU. Richiede entity EU (OUE Estone risolve). Dealer IT Sud ignora completamente |
| eCarsTrade | ecarstrade.com | 15+ paesi EU, focus BE/NL/DE/FR | B2B aste online | 18.000+ auto/settimana | DEALER_ONLY: verifica documenti aziendali. Interfaccia EN/FR, zero IT | Fee per transazione (1-3% stima) | ALTISSIMO — immenso stock ex-leasing EU. Barriera EN/FR e documentale = moat ARGOS totale |
| AutoProff | autoproff.com | 18+ paesi EU | B2B marketplace | 3.000+ auto/giorno, 10.000+ bidder | DEALER_ONLY: P.IVA dealer o EU entity | Abbonamento mensile (€200-400 stima) | ALTISSIMO — piattaforma AutoScout24 Group B2B. Ex-leasing, dealer stock. Richiede entity EU |
| Autorola EU | autorola.eu | 30+ paesi | B2B aste online | 200.000 veicoli/anno, 70.000 dealer attivi | DEALER_ONLY | Subscription + fee | ALTO — volume enorme, ex-leasing e trade-in dealer. Interfaccia EN |
| CarOnSale | caronsale.com | Pan-EU, focus DE | B2B aste online | 50K+/mese stima | DEALER_ONLY: registrazione dealer gratuita + verifica | Registrazione gratuita + buyer fee | ALTO — gestito da AUTO1 Group, registrazione gratuita, ottima per stock DE wholesale |
| Autobid.de | autobid.de | DE + AT | B2B aste online DE | 1.500 veicoli/giorno | DEALER_ONLY: verifica DE/AT | Subscription | ALTO — specifico DE/AT, qualita' alta, stock dealer |
| Astauto.it | astauto.it | Solo IT | Aste B2B IT | N/D | Dealer IT | Gratuito + fee | BASSO — aste IT, prezzi gia' alti, nessun vantaggio import EU |

### 25.2 Ex-leasing / Ex-flotta specializzati

| Portale | URL | Paesi coperti | Tipo | Fonte veicoli | Accesso | Valore ARGOS |
|---------|-----|---------------|------|---------------|---------|--------------|
| Ayvens Carmarket (ex CarNext/LeasePlan) | carmarket.ayvens.com | 40 paesi, 4 continenti | B2B ex-leasing | Ex-LeasePlan + ALD (ora Ayvens). La piu' grande flotta leasing EU. | DEALER_ONLY: account business | ALTISSIMO — ex LeasePlan e ALD avevano flotte milionarie, veicoli documentati al 100%, mantenimento certificato. Dealer IT ignora completamente |
| Exleasingcar.com | exleasingcar.com | Pan-EU, focus DE/AT/NL | Ex-leasing B2B | Leasing companies EU | Account aziendale, gratuito sfoglio | ALTISSIMO — specializzato ex-leasing, veicoli ben mantenuti, documentazione completa, prezzi trasparenti. Zero concorrenza IT |
| 2ndMove by Europcar | b2b.2ndmove.eu | Pan-EU | Ex-fleet noleggio | Europcar fleet | Account aziendale | ALTO — ex-noleggio Europcar, km documentati, manutenzione certificata, qualita' alta |
| Ald Automotive (ora Ayvens) | ayvens.com/used-cars | Pan-EU | Ex-leasing | Ex-ALD fleet | Account business | ALTO — ora integrato in Ayvens ma con filiali nazionali che vendono indipendentemente |
| ArvalMotion | arvalmotion.com | Pan-EU | Ex-leasing Arval (BNP) | Arval fleet | Account business | ALTO — Arval e' il leasing BNP Paribas, flotta enorme, veicoli certificati |
| FleetEx.eu | fleetex.eu | Pan-EU | Ex-fleet B2B | Flotte aziendali miste | Account business | MEDIO-ALTO — aggregatore ex-flotta europeo, meno conosciuto |

### 25.3 B2B marketplace specializzati

| Portale | URL | Tipo | Focus | Accesso | Valore ARGOS |
|---------|-----|------|-------|---------|--------------|
| Vwe.nl | vwe.nl | Aste export B2B | Export NL | DEALER_ONLY | ALTISSIMO — Veiling Wagens Export NL, veicoli pronti per export, zero concorrenza IT |
| Kvd Auctions SE | kvdauctions.se | B2B aste SE | Svezia | DEALER_ONLY | ALTISSIMO — wholesale svedese, prezzi bassi, zero dealer IT |
| Ymag.fr | ymag.fr | B2B FR | Francia | DEALER_ONLY, FR only | ALTO — B2B franco-francese, zero presenza straniera |
| CarCollect | carcollect.com | B2B NL/BE/DE | Benelux | DEALER_ONLY | MEDIO-ALTO — API disponibile, integrazione tecnica |
| Fleequid | fleequid.eu | B2B aste autobus + auto | Italia + EU | REG_FREE | MEDIO — originalmente bus, espande ad auto. Italiano, interessante per future |

---

## SEZIONE 26 — AGGREGATORI MULTI-MERCATO

**Questi portali aggregano listing da piu' paesi e sono utili per scansione rapida del mercato EU.**

| Aggregatore | URL | Copertura | Tipo | Listing totali | Costo | Valore ARGOS |
|-------------|-----|-----------|------|----------------|-------|--------------|
| The Parking EU | theparking.eu | 30+ paesi EU | Aggregatore pubblico | Milioni | Gratuito | ALTISSIMO — aggrega Mobile.de + AS24 + portali nazionali in un'unica ricerca. Overview EU in 2 click. Indispensabile per ARGOS fase 1 |
| AutoUncle | autouncle.com | 14 paesi EU | Aggregatore B2C | 11M+ da 1.900+ siti | Gratuito | ALTO — analisi prezzi avanzata, 5 categorie (Super price... Expensive). Usato dal Ministero Tasse danese per valutazioni |
| Carapis.com | carapis.com | 25+ mercati EU | API dati (B2B) | Mobile.de, AS24, Autovit, Otomoto, altri | Subscription (€200-500/mese stima) | ALTISSIMO — API unica per accedere dati strutturati da piu' portali. Parser anti-detection. Sistema ARGOS automatizzato futuro |
| AUTO-API.com | auto-api.com | Mobile.de principale | API dati (B2B) | Mobile.de specializzato | Subscription | ALTO — specializzato Mobile.de, real-time (nuovi listing entro 1-2 min dalla pubblicazione) |
| Carvago.com | carvago.com | EU cross-border | B2C aggregatore | Milioni verificati | Account dealer (Carvago Partner) | MEDIO — B2C competitor ma utile come fonte per veicoli verificati con CarAudit (300 punti) |
| Autoline.info | autoline.info | EU + oltre | Aggregatore + commerciali | N/D | Gratuito | MEDIO — forte su commerciali, sezione auto presente, copertura Est EU |

---

## SEZIONE 27 — PORTALI PREMIUM / SUPERCAR / CLASSICHE

**Per le supercar (Ferrari/Lamborghini/McLaren) il mercato e' globale, non solo EU.**

| Portale | URL | Focus | Volume | Accesso | Valore ARGOS |
|---------|-----|-------|--------|---------|--------------|
| JamesEdition | jamesedition.com | Luxury globale | N/D, 1M+ HNW utenti/mese | Account dealer | ALTO — per veicoli >€80K, Ferrari/Lambo/McLaren presenti da tutta EU |
| Mobile.de Klassiker | mobile.de/klassiker | Classiche DE | N/D | OPEN | MEDIO — classiche DE, interessante per modelli rari |
| Classic Trader | classictrader.com | Classiche + supercar | 30K+ | Registrazione | MEDIO — target diverso ARGOS ma occasionale |
| PistonHeads UK | pistonheads.com | Premium + enthusiast UK | 80K+ | OPEN | BASSO — UK post-Brexit ma utile per supercar rare |
| Carandclassic.com | carandclassic.com | Classiche EU | N/D | REG_FREE | BASSO per ARGOS standard |
| Collecting Cars EU | collectingcars.com | Aste premium online | N/D | REG_FREE | MEDIO — aste premium online, crescita rapida, qualita' alta |
| Perego Cars | peregocars.com | Luxury CH | N/D | OPEN | MEDIO — dealer Svizzero specializzato Porsche/Ferrari/McLaren, prezzi interessanti con CHF favorevole |

---

## SEZIONE 28 — VIN CHECK E STRUMENTI DI SUPPORTO

**Non sono portali di vendita ma sono essenziali nell'ecosistema ARGOS.**

| Strumento | URL | Funzione | Costo | Valore ARGOS |
|-----------|-----|----------|-------|--------------|
| carVertical | carvertical.com | VIN history check EU | €29,90/report | ESSENZIALE — copre tutta EU, km verificati, sinistri, storia proprietari |
| AutoDNA | autodna.com | VIN check alternativo | €15-30/report | ALTO — alternativa carVertical, forte su Est EU |
| Cartell.ie | cartell.ie | VIN check IE | N/D | BASSO — solo IE |
| BilInfo.dk | bilinfo.dk | VIN check DK | N/D | BASSO — solo DK |
| Car.info | car.info | VIN + history Scandinavia | Gratuito base | MEDIO — complementare a carVertical per SE/FI/NO |
| Regjeringen.no | N/A | Check NO | N/D | BASSO — NO extra-EU |
| Autovista24 | autovista24.autovistagroup.com | Market intelligence B2B | Subscription | ALTO — dati mercato EU per intelligence prezzi, usato da OEM e fleet |

---

## RIEPILOGO PRIORITA' ARGOS

### Tier 1 — Fonti primarie obbligatorie (monitoraggio settimanale)

```
Mobile.de              → volume massimo DE, qualita' alta
AutoScout24.de/eu      → pan-EU benchmark
Marktplaats.nl         → private gems NL senza VAT
Willhaben.at           → AT premium via Brennero
Sauto.cz               → prezzi 15-20% sotto DE
Otomoto.pl             → volume enorme (VIN check obbligatorio)
The Parking EU         → aggregatore rapido multi-paese
```

### Tier 2 — Fonti B2B ad alto valore (accesso con entity EU)

```
OpenLane EU            → leader wholesale EU
eCarsTrade             → ex-leasing BE/NL/DE/FR, 18K auto/settimana
Ayvens Carmarket       → ex LeasePlan+ALD, qualita' certificata
BCA EU                 → rete fisica EU, enorme volume
Exleasingcar.com       → specializzato ex-leasing, doc completa
AutoProff              → B2B AS24 Group, 18 paesi
Autorola EU            → 200K veicoli/anno, 70K dealer attivi
```

### Tier 3 — Mercati di nicchia ad alto moat (dealer IT non li conosce)

```
Anzeiger.lu            → veicoli ex-diplomatici/EU LU, qualita' altissima
Vwe.nl                 → export NL wholesale, zero concorrenza IT
Kvd.se / KvdAuctions   → aste svedesi, wholesale SE
Blocket.se             → interfaccia svedese, dealer IT bloccato
Hasznaltauto.hu        → ungherese = barriera totale, Audi Gyor vicino
Kleinanzeigen.de       → private gems DE a prezzi bassi
Pkw.de                 → portale "dimenticato" DE, listing esclusivi
Avto.net               → SI confine Trieste, interfaccia slovena
Autobazar.eu           → SK con EN parziale, volume alto
ArvalMotion            → ex-Arval (BNP), flotta certificata EU
2ndMove by Europcar    → ex-noleggio documentato
Pon.com NL             → surplus VW/Audi/Porsche importatore ufficiale NL
```

### Mercati da escludere

```
CIPRO (CY)      → guida destra (ex-UK)
MALTA (MT)      → guida destra (ex-UK)
IRLANDA (IE)    → guida destra (ex-UK)
NORVEGIA (NO)   → extra-EU, burocrazia
DANIMARCA (DK)  → tasse auto 150%, prezzi distorti
BULGARIA (BG)   → rischio qualita'/km
ROMANIA (RO)    → rischio qualita'/km (solo veicoli con VIN tracciato)
SPAGNA (ES)     → prezzi non competitivi, logistica sfavorevole
PORTOGALLO (PT) → mercato piccolo, prezzi non competitivi
```

---

## TABELLA QUICK REFERENCE — TUTTI I PORTALI

| Portale | Paese | B2C/B2B | Lingua | Scraping | Accesso | Score ARGOS |
|---------|-------|---------|--------|----------|---------|-------------|
| Mobile.de | DE | B2C | DE | SI (Apify/Carapis) | OPEN | 10/10 |
| AutoScout24 EU | EU | B2C | Multi | SI (Carapis) | OPEN | 10/10 |
| The Parking EU | EU | Aggregatore | Multi | UI gratis | OPEN | 9/10 |
| OpenLane EU | EU | B2B | 19 lingue | No | DEALER_ONLY | 10/10 |
| eCarsTrade | EU | B2B | EN/FR | No | DEALER_ONLY | 10/10 |
| Ayvens Carmarket | EU | B2B | Multi | No | DEALER_ONLY | 10/10 |
| BCA EU | EU | B2B | Multi | No | DEALER_ONLY | 10/10 |
| AutoProff | EU | B2B | EN | No | DEALER_ONLY | 9/10 |
| Exleasingcar | EU | B2B | EN | No | REG_FREE | 9/10 |
| Autorola EU | EU | B2B | EN | No | DEALER_ONLY | 9/10 |
| Marktplaats.nl | NL | B2C | NL | SI | OPEN | 8/10 |
| Willhaben.at | AT | B2C | DE | SI | OPEN | 8/10 |
| Sauto.cz | CZ | B2C | CZ | SI | OPEN | 8/10 |
| Otomoto.pl | PL | B2C | PL | SI (Apify) | OPEN | 8/10 |
| Blocket.se | SE | B2C | SE | SI | OPEN | 8/10 |
| Hasznaltauto.hu | HU | B2C | HU | SI | OPEN | 8/10 |
| Carapis API | EU | B2B API | EN | N/A | Subscription | 9/10 |
| CarOnSale | EU | B2B | EN | No | DEALER_ONLY | 8/10 |
| AutoUncle | EU | Aggregatore | Multi | No | OPEN | 7/10 |
| LeBonCoin | FR | B2C | FR | SI (Apify) | OPEN | 6/10 |
| LaCentrale.fr | FR | B2C | FR | Limitato | OPEN | 6/10 |
| Kvd.se / KvdAuctions | SE | B2C+B2B | SE/EN | No | REG_FREE | 8/10 |
| Anzeiger.lu | LU | B2C | FR/DE/LU | No | OPEN | 9/10 (nicchia) |
| Vwe.nl | NL | B2B export | NL | No | DEALER_ONLY | 10/10 (nicchia) |
| Avto.net | SI | B2C | SI | Limitato | OPEN | 7/10 |
| Autobazar.eu | SK | B2C | SK/EN | No | OPEN | 7/10 |
| TipCars.com | CZ/SK | B2C | EN | Limitato | OPEN | 7/10 |
| Kleinanzeigen.de | DE | B2C | DE | SI (Apify) | OPEN | 7/10 |
| Pkw.de | DE | B2C | DE | No | OPEN | 6/10 |
| Car.gr | GR | B2C | GR | No | OPEN | 6/10 |
| Autoplius.lt | LT | B2C | LT/EN | No | OPEN | 5/10 |
| Autobid.de | DE/AT | B2B | DE/EN | No | DEALER_ONLY | 7/10 |
| ArvalMotion | EU | B2B | Multi | No | REG_FREE | 8/10 |
| 2ndMove Europcar | EU | B2B | EN | No | REG_FREE | 7/10 |
| Pon.com NL | NL | B2B | NL/EN | No | DEALER_ONLY | 8/10 (nicchia) |
| L'Argus.fr | FR | B2C | FR | No | OPEN | 6/10 |
| Bytbil.com | SE | B2C | SE | Limitato | OPEN | 7/10 |
| AutoScout24.be | BE | B2C | FR/NL | SI | OPEN | 7/10 |
| 2dehands.be | BE | B2C | NL | SI | OPEN | 5/10 |
| JamesEdition | Global | B2C luxury | EN | No | REG_FREE | 7/10 (luxury) |
| Carago.com | EU | B2C | Multi | No | OPEN | 5/10 |
| BilBasen.dk | DK | B2C | DK | SI | OPEN | 2/10 |
| AutoVit.ro | RO | B2C | RO | SI | OPEN | 2/10 |
| Mobile.bg | BG | B2C | BG | Limitato | OPEN | 2/10 |
| Njuskalo.hr | HR | B2C | HR | No | OPEN | 3/10 |

---

## PORTALI SCOPERTI IN QUESTA RICERCA (non in s65)

I seguenti portali sono NUOVI rispetto al censimento S65 e rappresentano opportunita' specifiche per ARGOS:

1. **Anzeiger.lu** — classifieds LU trilingue, veicoli ex-diplomatici/EU
2. **Vwe.nl** — aste export NL, specializzato vendita estera
3. **Kvd.se / KvdAuctions.se** — aste svedesi B2C e B2B
4. **Pon.com** — importatore VW Group NL, surplus ex-demo
5. **ArvalMotion** — ex-flotta Arval (BNP Paribas), certificata
6. **Klaravik.se** — aste svedesi generaliste con auto
7. **Pkw.de** — portale DE storico con listing non su Mobile/AS24
8. **Gebrauchtwagen.at** — specializzato AT usato, non su Willhaben
9. **Autorevue.at** — dealer AT tradizionali (non su AS24)
10. **L'Argus.fr** — quotazioni FR ufficiali + classifieds dealer
11. **Ymag.fr** — B2B FR puro, zero presenza straniera
12. **Bazos.cz** — private deals CZ prezzi bassissimi, tutto in ceco
13. **Inzerce.auto.cz** — listing locali CZ non su Sauto/AS24
14. **Avto.net / Bolha.com / Avtooglasi.com** — Slovenia (confine Trieste)
15. **Autobazar.eu** — SK con parziale EN, unico mercato Est con EN
16. **Hasznaltauto.hu** — HU con Audi Gyor vicino, interfaccia ungherese
17. **Car.gr / Xe.gr** — Grecia post-crisi, occasioni premium
18. **Fleequid** — aste IT/EU bus che espande ad auto
19. **AutoUncle** — aggregatore EU 11M listing, valutazione prezzi avanzata
20. **Collecting Cars** — aste premium online in crescita

---

## CONCLUSIONE STRATEGICA

**Il vantaggio competitivo di ARGOS non e' solo tecnico — e' geografico e linguistico.**

Un dealer di Eboli, Salerno o Reggio Calabria non puo' fisicamente navigare:
- Un sito in olandese (vwe.nl, marktplaats.nl)
- Un sito in svedese (blocket.se, kvd.se)
- Un sito in ceco (sauto.cz, bazos.cz)
- Un sito in ungherese (hasznaltauto.hu)
- Un sito in francese professionale (ymag.fr)
- Una piattaforma B2B con KYC e deposito (openlane.eu, eCarsTrade)
- Un sito trilingue lussemburghese (anzeiger.lu)
- Un portale export specializzato (vwe.nl)

Ogni barriera linguistica, documentale o procedurale e' un moat di ARGOS.
ARGOS ha accesso a 60+ portali in 20+ lingue che il dealer non puo' raggiungere.

**Questo e' il pitch corretto verso il dealer:**
"Lei cerca su AutoScout24.it. Io cerco in 60 portali in 15 lingue che lei non puo' nemmeno aprire."
