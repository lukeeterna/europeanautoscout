# S82 — Feature Gap Analysis: Strumenti e Servizi ARGOS vs Competitor
## Cosa offrire a un dealer del Sud Italia che nessun competitor offre oggi
**Data**: 2026-03-24
**Ricerca per**: Definire roadmap prodotto differenziante per ARGOS Automotive

---

## PREMESSA: IL PUNTO DI PARTENZA

**Cosa fa il dealer oggi senza ARGOS (fai-da-te):**
- Naviga AutoScout24.de o Mobile.de senza account premium
- Non legge tedesco → vede solo annunci con foto, ignora dettagli
- Fa un bonifico internazionale a un privato o dealer DE senza garanzie
- Affronta COC, traduzione documenti, F24 IVA, immatricolazione in autonomia
- Costo totale fai-da-te stimato: €1.700-2.500 per veicolo (logistica + burocrazia + rischio)
- Tempo: 3-8 settimane dalla ricerca alla targa IT

**Cosa fa il competitor B2C (Bolidem/Autotedesche/Importami):**
- Aspetta che il cliente porti il link del veicolo da AutoScout24
- Ispeziona il veicolo (€121-299 upfront)
- Gestisce logistica + burocrazia
- Portali usati: 2-3 (AS24, Mobile.de)
- Fee upfront anche senza consegna

**Cosa fa ARGOS oggi:**
- Scouting proattivo su 73 portali EU (28 attivi E2E)
- CoVe scoring bayesiano su ogni veicolo
- Success fee €800-1.200 (zero upfront)
- B2B dealer dedicato Sud Italia

**Gap critico da colmare:** zero track record, zero recensioni, zero strumenti visibili per il dealer.

---

## ANALISI FEATURE: 20 STRUMENTI/SERVIZI DIFFERENZIANTI

Ordinati per: **Impatto sul dealer** (1-10) × **Fattibilita' ZERO COST** × **Unicita' vs competitor**

---

### FEATURE 1 — Scheda Veicolo Branded per Rivendita (PDF Dealer-Ready)
**Descrizione**: Quando ARGOS consegna un veicolo, fornisce anche una scheda tecnica professionale in italiano, con foto HD, dati tecnici, storia sintetica, km verificati, garanzia COC, pronta da stampare o inviare al cliente finale del dealer.

**Il dealer non deve fare nulla**: riceve un documento che puo' consegnare direttamente al suo cliente.

**Analogia**: Come un agente immobiliare che consegna al compratore un dossier fotografico della casa. Il dealer diventa piu' professionale agli occhi del suo cliente finale.

**Costo ARGOS**: Zero. Usa il PDF generator gia' esistente (`tools/scripts/pdf_generator_enterprise.py`), adattato per il formato dealer-facing (non ARGOS-facing).

**Competitor lo fa?**: NO. Bolidem/Autotedesche danno solo il veicolo. Zero materiale marketing.

**Unicita'**: ALTA — nessun broker o importatore IT fornisce questo.

**Impatto dealer**: 9/10 — risolve un pain point reale: il dealer deve creare lui le schede per AutoScout24.it o per i clienti in showroom.

**Fonti**: MotorK.io analisi annunci usato IT, DEKRA servizi dealer.

---

### FEATURE 2 — Controllo Recall EU Gratuito (KBA + Car-Recalls.eu)
**Descrizione**: Per ogni veicolo proposto, ARGOS verifica automaticamente se e' soggetto a campagne di richiamo attive nel database KBA (Kraftfahrt-Bundesamt DE) e nel database EU Car-Recalls.eu (basato su RAPEX/Safety Gate).

**Output per il dealer**: "BMW X3 VIN DE-xxx — NESSUN RECALL ATTIVO. Verificato KBA 2026-03-24."

**Il dealer non sa che esiste questa verifica**: per lui e' un valore aggiunto invisibile che aumenta fiducia.

**Costo ARGOS**: Zero. KBA pubblica database pubblico. Car-recalls.eu ha VIN check gratuito. Scraper gia' nell'infrastruttura ARGOS.

**Competitor lo fa?**: NO. Nessun mandatario IT include verifica recall nella sua offerta standard.

**Unicita'**: ALTA.

**Impatto dealer**: 8/10 — evita che il dealer rivenda un veicolo con recall pendente, esponendosi a responsabilita' legale.

**Fonti**: [car-recalls.eu](https://car-recalls.eu/vin-check-recalls/), [KBA recall database](https://www.kba.de/EN/Themen_en/Marktueberwachung_en/Rueckrufe_en/Rueckrufdatenbank_en/rueckrufdatenbank_inhalt_en.html).

---

### FEATURE 3 — Verifica Odometro Multi-Source (autoDNA + VinCheck EU)
**Descrizione**: Per ogni veicolo proposto, ARGOS incrocia il chilometraggio dichiarato con i database storici di autoDNA (26 paesi, 15 anni di dati) e VinCheckEurope.eu. Segnala discrepanze.

**Output per il dealer**: "50.058 km dichiarati — COERENTI con 3 interventi di manutenzione registrati. Nessuna anomalia odometro."

**Problema che risolve**: Il dealer del Sud Italia che importa da solo rischia di comprare un'auto con km manomessi (odometer rollback). In Germania questo e' reato ma avviene. Il dealer poi lo rivende e viene coinvolto in contenzioso.

**Costo ARGOS**: autoDNA offre report gratuiti base. VinCheckEurope.eu e vinspy.eu hanno tier gratuiti. Per volumi >10/mese: costo marginale €2-5/veicolo (ma la ricerca pregressa S65 indica di trovare il modo free).

**Competitor lo fa?**: Bolidem non lo menziona esplicitamente. eCarsTrade raccomanda VIN check ma non lo include nella fee. Nessuno include verifica multi-source nei materiali consegnati al dealer.

**Unicita'**: ALTA.

**Impatto dealer**: 9/10 — il rischio legale di rivendere auto con km falsificati e' uno dei pain point piu' acuti del dealer usato IT.

**Fonti**: [autoDNA](https://www.autodna.com/), [VinCheckEurope](https://vincheckeurope.eu/), [eCarsTrade VIN check guide](https://ecarstrade.com/blog/best-vin-decoders-for-car-history).

---

### FEATURE 4 — Alerta Stock Personalizzata per Dealer (Push Proattivo)
**Descrizione**: Il dealer comunica ad ARGOS i suoi criteri preferiti (es. "BMW X3/X5 2020+, max 60.000km, max €35k DE, diesel"). ARGOS monitora i 73 portali EU in tempo reale e invia un WhatsApp al dealer entro 24h da quando compare un veicolo che corrisponde.

**Analogia**: Come il sistema di alert di AutoScout24, ma su 73 portali simultaneamente, con CoVe score gia' calcolato, in italiano, con margine stimato gia' incluso.

**Esempio messaggio**: "Domenico, BMW X5 xDrive30d 2021, 48k km. DE €38.900, IT ~€44k. Margine stimato €3.100 netti per lei. Tengo ferma 48h per la sua risposta. Vuole il dossier completo?"

**Il dealer non deve cercare nulla**: ARGOS viene da lui, non lui da ARGOS.

**Costo ARGOS**: Zero. I scraper esistono gia'. Il sequencer e CRM esistono.

**Competitor lo fa?**: NESSUNO. Questo e' il cuore del vantaggio SCOUTING PROATTIVO. Ma la feature "alert personalizzato per profilo dealer" e' ancora piu' specifica e potente.

**Unicita'**: MASSIMA — differenziatore #1 di ARGOS.

**Impatto dealer**: 10/10.

---

### FEATURE 5 — Stima Costo Totale Import (Fee Calculator Trasparente)
**Descrizione**: Prima ancora di proporre il veicolo, ARGOS calcola e comunica al dealer il costo totale reale: prezzo veicolo DE + trasporto bisarca + COC se mancante + traduzione documenti + F24 IVA + IPT + bollo + fee ARGOS. Tutto in un numero unico.

**Output per il dealer**: "Il suo costo all-in per questa BMW e': €37.200. La revende a €41.500. Guadagno netto: €3.100 prima dei costi showroom."

**Problema che risolve**: Il dealer che importa da solo non sa calcolare il costo totale. Spesso scopre costi nascosti dopo aver gia' impegnato il capital. Con ARGOS vede tutto prima.

**Costo ARGOS**: Zero. `tools/fee_calculator.py` e `tools/transport_estimator.py` esistono gia'.

**Competitor lo fa?**: Importami espone il 4%+IVA ma non include logistica. Bolidem espone fee separate per ogni step. eCarsTrade non include immatricolazione. Nessuno da' un unico numero all-in.

**Unicita'**: ALTA.

**Impatto dealer**: 9/10 — la trasparenza totale e' un differenziatore enorme con un target (Sud Italia family business) che diffida per default dei costi nascosti.

**Fonti**: [eCarsTrade import Italy guide](https://ecarstrade.com/blog/how-to-import-a-car-to-italy), [alVolante import guide](https://www.alvolante.it/da_sapere/legge-e-burocrazia/importare-un-auto-dall-estero-costi-tempi-e-tasse-381577).

---

### FEATURE 6 — Dossier Veicolo con Delta Prezzo IT (Market Intelligence)
**Descrizione**: Ogni proposta ARGOS include un mini-report con: prezzo medio IT dello stesso modello (da AS24.it), prezzo DE corrente, delta calcolato, trend 30 giorni (sale/scende), tempo medio di vendita IT per quel modello.

**Esempio**: "BMW X3 xDrive20d 2022 — Prezzo medio IT AS24: €37.088. Prezzo DE trovato: €34.140. Delta: +€2.948 (+8.6%). Tempo medio vendita IT: 23 giorni. Trend: stabile."

**Analogia settore real estate**: Come quando un agente immobiliare consegna al compratore i "comparables" — vendite simili in zona — per giustificare il prezzo. Usato da ogni broker B2B serio.

**Costo ARGOS**: Zero. CoVe e Market Index gia' calcolano questo. Il PDF generator gia' lo include nel dossier dealer-facing.

**Competitor lo fa?**: NO. Bolidem e Autotedesche non danno intelligence di mercato. eCarsTrade ha solo prezzo asta, zero context IT.

**Unicita'**: ALTA.

**Impatto dealer**: 9/10 — il dealer RAGIONIERE e TECNICO decidono solo con numeri. Questa feature e' decisive per loro.

---

### FEATURE 7 — Gestione Documentale Chiavi in Mano (COC + Traduzione + F24)
**Descrizione**: ARGOS gestisce tutta la burocrazia dell'import: ottiene COC se mancante (via EuroCOC o direttamente dal brand), organizza traduzione certificata in italiano, compila F24 IVA intra-UE con il commercialista del dealer, coordina immatricolazione via STA (Sportello Telematico Automobilista).

**Il dealer non tocca carta**: riceve il libretto italiano.

**Problema che risolve**: La burocrazia e' il pain point #1 del dealer che importa. COC mancante, documenti in tedesco non tradotti, F24 compilato male = blocco immatricolazione + ritardi settimane.

**Costo ARGOS**: COC via EuroCOC: €80-150 (ma spesso incluso nel prezzo acquisto). Traduzione: €50-80. Questi costi si assorbono nella fee €800-1.200 o si aggiungono al costo totale comunicato upfront.

**Competitor lo fa?**: Bolidem: pratiche amministrative +€150 opzionale. Importami: incluso. Autotedesche: incluso. MA nessuno di questi serve dealer B2B — lo fanno per privati.

**Unicita'**: MEDIA (per i privati esiste, per i dealer B2B nessuno lo fa sistematicamente).

**Impatto dealer**: 8/10 — soprattutto per i dealer del Sud dove le pratiche burocratiche sono piu' lente e dispendiose.

**Fonti**: [EuroCOC](https://www.eurococ.eu/en/), [praticheauto.online](https://praticheauto.online/blog/articles/importazione-e-immatricolazione-auto-estera-guida-2025), [COC-Online](https://www.coc-online.com/blogs/post/how-to-register-an-imported-vehicle-in-italy-importance-of-the-coc).

---

### FEATURE 8 — Garanzia Convenzionale Attivabile (via ConformGest / AutoProtetta)
**Descrizione**: ARGOS negozia un accordo con un provider di garanzia convenzionale (es. ConformGest IT o AutoProtetta) per offrire al dealer la possibilita' di attivare una garanzia meccanica sul veicolo importato, con il brand ARGOS (o in white label), a costo marginale.

**Il dealer rivende con garanzia**: "Auto tedesca certificata ARGOS + garanzia meccanica 12 mesi" = premium di prezzo +€800-1.500.

**Struttura possibile**: ARGOS porta il veicolo, dealer sceglie se attivare garanzia a €200-400 aggiuntivi (copertura guasti meccanici, soccorso ACI, vettura sostitutiva). Il dealer rivende con garanzia e la scarica sul cliente finale a +€600-900.

**Costo ARGOS**: Setup accordo commerciale (zero cash outlay). Costo garanzia a carico del dealer o del cliente finale.

**Competitor lo fa?**: ConformGest e AutoProtetta esistono per il mercato IT, ma nessun mandatario/broker include una partnership strutturata con questi provider nella propria offerta B2B.

**Unicita'**: ALTA — crea un prodotto bundled che aumenta il margine del dealer sulla rivendita.

**Impatto dealer**: 8/10 — il dealer che rivende con garanzia chiede di piu' e vende piu' velocemente.

**Fonti**: [ConformGest](https://www.conformgest.it/), [AutoProtetta](https://www.autoprotetta.it/), [4dealer.it garanzia legale](https://www.4dealer.it/garanzia-legale-auto-usate/).

---

### FEATURE 9 — Score Qualita' Foto (Valutazione Listing Automatica)
**Descrizione**: ARGOS valuta automaticamente la qualita' delle foto dell'annuncio originale DE (numero foto, angoli presenti, qualita' risoluzione, presenza foto interni/esterni/motore/pneumatici). Segnala se la documentazione fotografica e' insufficiente prima dell'acquisto.

**Output**: "Annuncio ha 18 foto: completo. Mancano: foto pneumatici posteriori, foto vano bagagli. Richiedere al venditore prima dell'acquisto."

**Problema che risolve**: Il dealer che acquista da remoto non vede il veicolo fisicamente. Una documentazione fotografica incompleta nasconde danni. ARGOS fa da "occhi" del dealer.

**Costo ARGOS**: Zero. Il detail enricher gia' scarica le foto. Aggiungere logica di scoring foto e' sviluppo interno.

**Competitor lo fa?**: AUTO1 CAT usa AI per rilevare danni (enterprise). Nessun broker IT lo fa.

**Unicita'**: ALTA nel segmento broker IT.

**Impatto dealer**: 7/10.

---

### FEATURE 10 — Finestra di Esclusiva 48h per Dealer Partner
**Descrizione**: Quando ARGOS trova un'opportunita' di qualita' alta (CoVe score >= 0.80), la presenta in esclusiva al dealer piu' in linea con il profilo del veicolo per 48h. Solo dopo il silenzio viene proposta ad altri dealer in pipeline.

**Messaggio al dealer**: "Domenico, questa BMW X5 la tengo per lei nelle prossime 48h. Se non mi risponde entro domani sera, la giro ad un altro concessionario in zona. Mi dice si' o no?"

**Psicologia**: Scarsita' reale, non artificiale. Il dealer sente di avere un vantaggio competitivo esclusivo. Incentiva a rispondere rapidamente.

**Costo ARGOS**: Zero. E' una regola operativa, non un costo tecnologico.

**Competitor lo fa?**: NO. Le piattaforme B2B (BCA, eCarsTrade) sono aste pubbliche — chiunque vede. Nessun broker IT offre esclusiva temporanea.

**Unicita'**: ALTA.

**Impatto dealer**: 9/10 — crea senso di partnership privilegiata e urgency reale.

---

### FEATURE 11 — Report Mensile Stock Intelligence (cosa si muove nella tua zona)
**Descrizione**: ARGOS invia al dealer partner un report mensile con: modelli piu' venduti nella sua provincia (da AS24.it + Automobile.it), prezzi medi locali, tempo medio vendita per segmento, trend stagionali. Non e' il veicolo che stiamo cercando: e' il mercato della sua zona.

**Esempio**: "Aprile 2026 — Provincia FG. BMW Serie 3 diesel: +12% richiesta, tempo medio vendita 18 giorni. Range Rover Evoque: mercato saturo, evitare. BMW X5 2020+: gap offerta/domanda ampio, opportunita' alta."

**Analogia**: Come i "market report" mensili che i migliori agenti immobiliari mandano ai proprietari di immobili anche quando non stanno trattando nulla. Mantiene la relazione attiva.

**Costo ARGOS**: Zero. I dati vengono dagli scraper esistenti. Il PDF generator crea il report.

**Competitor lo fa?**: NO. INDICATA e JATO lo fanno ma costano migliaia di euro/anno e sono per grandi gruppi. Nessun broker piccolo/medio lo fa.

**Unicita'**: ALTA.

**Impatto dealer**: 8/10 — mantiene la relazione calda nei periodi senza acquisti attivi. Il dealer vede ARGOS come fonte di intelligence, non solo come "quello che trova le macchine".

**Fonti**: [Autorola/INDICATA Italy](https://www.autorolagroup.com/italiandealers_june2023/).

---

### FEATURE 12 — Verifica VIN Decode Gratuita (Specifiche Tecniche Complete)
**Descrizione**: ARGOS include nel dossier il VIN decode completo: allestimento esatto, optional di fabbrica, omologazione EU, data prima immatricolazione, mercato di destinazione originale (DE/NL/FR/AT). Evidenzia se il veicolo e' stato originariamente venduto in un mercato diverso dalla Germania (es. ex-Belgio = COC piu' semplice).

**Costo ARGOS**: vindecoder.eu offre 20 lookup gratuiti. stat.vin offre EU VIN decode gratuito. Per volumi: API a basso costo.

**Competitor lo fa?**: Non in modo strutturato. eCarsTrade raccomanda VIN check ma non lo include nel servizio standard.

**Unicita'**: MEDIA (la tecnologia esiste, ma bundled nel servizio ARGOS e' unica).

**Impatto dealer**: 7/10 — evita sorprese su optional mancanti o mercato di origine diverso.

**Fonti**: [vindecoder.eu](https://vindecoder.eu/api/), [stat.vin](https://stat.vin/vin-decoding/europe-italy).

---

### FEATURE 13 — Trasporto Coordinato con Bisarca (Zero Gestione per il Dealer)
**Descrizione**: ARGOS coordina il trasporto dalla Germania al concessionario del dealer. Il dealer non deve trovare un trasportatore, non deve pagare anticipi, non deve seguire logistica. ARGOS gestisce tutto e comunica giorno e ora di arrivo con 24h di anticipo.

**Costo**: Il trasporto (€600-1.000 DE→Sud IT) e' incluso o comunicato esplicitamente nel fee calculator come costo separato. Il dealer lo valuta anticipatamente.

**Competitor lo fa?**: Bolidem offre trasporto bisarca come opzione a pagamento (+€840). Autotedesche include trasporto. Importami include logistica. MA nessuno lo fa per dealer B2B in modo strutturato nel Sud.

**Unicita'**: MEDIA (esiste nel B2C, unica nel B2B dealer Sud).

**Impatto dealer**: 8/10 — il dealer del Sud non conosce i trasportatori DE→IT. Coordinare da solo richiede 5-10 ore di lavoro e rischio.

**Fonti**: [alVolante import guide](https://www.alvolante.it/da_sapere/legge-e-burocrazia/importare-un-auto-dall-estero-costi-tempi-e-tasse-381577).

---

### FEATURE 14 — Accesso a Portali B2B Non Accessibili al Dealer Singolo
**Descrizione**: Molte aste B2B EU (BCA, OpenLane, CarOnSale, eCarsTrade) richiedono ATECO 45.11.01, deposito cauzionale, account verificato, lingua tedesca/inglese. Il dealer del Sud Italia non puo' accedere direttamente. ARGOS accede per lui e porta le opportunita' da questi portali privilegiati.

**Messaggio al dealer**: "Questa Mercedes e' su un'asta B2B professionale che lei non puo' aprire. Ci accedo io e la compro per lei."

**Costo ARGOS**: Account gia' esistenti o da attivare. Zero per il dealer.

**Competitor lo fa?**: eCarsTrade e' direttamente una di queste piattaforme. BCA richiede ATECO. Ma nessun broker B2B IT offre accesso a TUTTE queste piattaforme come servizio bundled.

**Unicita'**: ALTA nel posizionamento (pochi la comunicano cosi' esplicitamente).

**Impatto dealer**: 8/10 — il dealer capisce immediatamente che ARGOS apre porte che lui non puo' aprire da solo.

**Fonti**: [ricerca S65 dealer portals](research/s65_dealer_portals_intelligence.md), [S66 all EU portals](research/s66_all_eu_portals_2026.md).

---

### FEATURE 15 — Storico Prezzi 12 Mesi (Trend e Stagionalita')
**Descrizione**: Per ogni veicolo proposto, ARGOS include un grafico/tabella con l'andamento del prezzo medio dello stesso modello negli ultimi 12 mesi. Evidenzia se il prezzo e' ai minimi stagionali (ottimo per comprare) o ai massimi (aspettare).

**Esempio**: "BMW X3 xDrive20d 2022 — Prezzo medio DE: Jan €36.5k → Feb €35.8k → Mar €34.1k. Trend: -6.7% in 3 mesi. OTTIMO momento di acquisto."

**Analogia commodities**: Come i broker di petrolio o metalli che mostrano ai clienti il grafico prezzi prima di ogni acquisto. Crea credibilita' immediata e giustifica l'urgenza.

**Costo ARGOS**: Zero. I dati sono negli scraper storici + Market Price Index gia' esistente.

**Competitor lo fa?**: NO. Nessun mandatario IT offre trend storici. Questa e' intelligence da player enterprise (INDICATA, JATO, DAT) non da broker individuali.

**Unicita'**: MASSIMA nel segmento broker italiano.

**Impatto dealer**: 8/10 — il dealer RAGIONIERE e TECNICO amano i dati storici. Li aiuta a decidere in modo razionale.

---

### FEATURE 16 — Foto HD Professionali (Scaricate e Organizzate)
**Descrizione**: Per ogni veicolo proposto, ARGOS scarica e organizza tutte le foto HD dell'annuncio originale in una cartella condivisa (Google Drive o WeTransfer). Il dealer riceve un link con 30-60 foto pronte da usare per il suo annuncio su AS24.it senza dover fotografare il veicolo all'arrivo.

**Il dealer riceve**: veicolo + foto gia' pronte per pubblicare l'annuncio.

**Problema che risolve**: Il dealer che acquista un'auto usata deve fotografarla per poterla rivendere. Se le foto del venditore DE sono gia' di qualita', perche' rifarle? ARGOS le consegna organizzate.

**Costo ARGOS**: Zero. Il image_downloader.py esiste gia' (`tools/scrapers/image_downloader.py`).

**Competitor lo fa?**: NO. I concorrenti non pensano alla rivendita del dealer — consegnano solo il veicolo.

**Unicita'**: ALTA — pensare alla vita DOPO la consegna e' un cambio di paradigma.

**Impatto dealer**: 7/10 — risparmia 2-3 ore di lavoro per annuncio.

---

### FEATURE 17 — Briefing Veicolo Vocale (WA Voice 60 sec)
**Descrizione**: Quando ARGOS propone un veicolo, invia anche un messaggio vocale di 60 secondi su WhatsApp con il riassunto: "Ciao Domenico, ho trovato una BMW X3 per lei. 50.000km, diesel, 2022, in ottime condizioni. In Germania a 34.000 euro. Sul mercato italiano un pezzo uguale non si trova sotto i 37.000. Margine per lei circa 3.000 netti. Vuole vedere il dossier completo?" Tono umano, non commerciale.

**Psicologia**: I messaggi vocali nel Sud Italia hanno tasso di apertura 3-4x superiore ai testi. Percepiti come piu' autentici, meno "venditori".

**Costo ARGOS**: Zero. La ricerca S18 ha identificato edge-tts (Diego Neural IT) + infrastruttura WA esistente.

**Competitor lo fa?**: NO. Nessun competitor usa voice note come touchpoint proattivo.

**Unicita'**: MASSIMA.

**Impatto dealer**: 9/10 — differenziatore di formato oltre che di contenuto.

**Fonti**: [research tts voip S18](research/project_tts_voip_chiamate_automatiche_2026-03-18.md).

---

### FEATURE 18 — Confronto Costo Fai-da-Te vs ARGOS (Calcolatore Interattivo)
**Descrizione**: Un documento (PDF o pagina web) che mostra al dealer, inserendo solo il prezzo del veicolo target, la differenza esatta tra: (A) import fai-da-te con tutti i costi reali, (B) import via ARGOS con fee success.

**Output tipo**:
```
Veicolo: BMW X3 €34.000 DE

FAI-DA-TE:          ARGOS:
Logistica: +€900    Logistica: inclusa
COC: +€120          COC: inclusa
Traduzione: +€70    Traduzione: inclusa
F24+IPT: +€450      F24+IPT: gestita
Tempo: 6 settimane  Tempo: 2-3 settimane
Rischio: 100% suo   Rischio: 0% (no win, no pay)
Totale extra: €1.540 Fee ARGOS: €1.000
RISPARMIO ARGOS: €540 + zero rischio + 3 settimane prima
```

**Costo ARGOS**: Zero. E' un documento. Il fee_calculator.py lo genera.

**Competitor lo fa?**: NO. Nessuno mette nero su bianco il confronto diretto con il fai-da-te perche' non hanno la struttura success-fee.

**Unicita'**: ALTA — solo chi ha success-fee puo' fare questo confronto in modo onesto.

**Impatto dealer**: 9/10 — il dealer RAGIONIERE decide su questo tipo di analisi.

---

### FEATURE 19 — Lista Modelli ad Alta Rotazione per la Zona del Dealer
**Descrizione**: Prima di proporre veicoli, ARGOS analizza lo stock corrente del dealer su AS24.it e i modelli piu' richiesti nella sua provincia (da ricerche utenti). Propone solo modelli che in quella zona vendono velocemente.

**Esempio per Foggia**: "In provincia FG i modelli a piu' alta rotazione sono: BMW Serie 3 diesel (vendita media 19 giorni), Mercedes Classe C (25 giorni), BMW X3 (23 giorni). Evito di proporre SUV di lusso sopra €60k che in zona hanno mercato limitato."

**Costo ARGOS**: Zero. Dati da AS24.it gia' nello scraper.

**Competitor lo fa?**: NO. I competitor B2C trovano la macchina che il cliente chiede — non ragionano per zona del dealer.

**Unicita'**: ALTA.

**Impatto dealer**: 8/10 — il dealer non vuole stock che non riesce a ruotare. Questa feature dimostra che ARGOS conosce il suo mercato locale.

---

### FEATURE 20 — Garanzia di Risposta Entro 24h (SLA Comunicato)
**Descrizione**: ARGOS si impegna pubblicamente (nella proposta e sul sito) a rispondere a qualsiasi richiesta del dealer entro 24h lavorative. Non e' una feature tecnologica: e' un impegno operativo comunicato esplicitamente che crea aspettativa positiva e differenzia da competitor informali.

**Analogia**: Come i SLA nel B2B enterprise (AWS, Salesforce). Il dealer sa cosa aspettarsi.

**Costo ARGOS**: Zero (e' una regola operativa).

**Competitor lo fa?**: Bolidem non ha SLA comunicati. eCarsTrade e' una piattaforma automatizzata. Nessun broker IT individuale ha SLA espliciti.

**Unicita'**: MEDIA (ma rara nel segmento micro-broker italiano).

**Impatto dealer**: 7/10 — costruisce fiducia, soprattutto per il dealer che diffida e vuole sapere che c'e' un referente disponibile.

---

## TABELLA RIEPILOGATIVA — PRIORITA' DI IMPLEMENTAZIONE

| # | Feature | Impatto | Costo | Unicita' | Priorita' |
|---|---------|---------|-------|----------|-----------|
| 4 | Alert stock personalizzato per profilo dealer | 10 | Zero | Massima | P0 |
| 10 | Finestra esclusiva 48h per dealer partner | 9 | Zero | Alta | P0 |
| 17 | Briefing vocale WA (60 sec) | 9 | Zero | Massima | P0 |
| 1 | Scheda veicolo branded per rivendita | 9 | Zero | Alta | P0 |
| 5 | Stima costo totale all-in (fee calculator) | 9 | Zero | Alta | P0 |
| 18 | Confronto fai-da-te vs ARGOS | 9 | Zero | Alta | P0 |
| 3 | Verifica odometro multi-source | 9 | Basso | Alta | P1 |
| 2 | Controllo recall EU (KBA + Car-Recalls.eu) | 8 | Zero | Alta | P1 |
| 6 | Dossier con delta prezzo IT (market intel) | 9 | Zero | Alta | P0 |
| 11 | Report mensile stock intelligence | 8 | Zero | Alta | P1 |
| 8 | Garanzia convenzionale attivabile | 8 | Zero setup | Alta | P2 |
| 7 | Gestione documentale chiavi in mano | 8 | Basso | Media | P1 |
| 13 | Trasporto coordinato (zero gestione dealer) | 8 | Incluso | Media | P1 |
| 14 | Accesso portali B2B non accessibili | 8 | Zero | Alta | P0 |
| 19 | Lista modelli alta rotazione per zona | 8 | Zero | Alta | P1 |
| 15 | Storico prezzi 12 mesi (trend) | 8 | Zero | Massima | P1 |
| 9 | Score qualita' foto annuncio | 7 | Zero | Alta | P2 |
| 16 | Foto HD organizzate per rivendita | 7 | Zero | Alta | P1 |
| 12 | VIN decode completo (optional/allestimento) | 7 | Basso | Media | P1 |
| 20 | SLA risposta 24h (impegno comunicato) | 7 | Zero | Media | P0 |

---

## CLUSTER STRATEGICI: COME COMUNICARLE AL DEALER

### CLUSTER A — "Non trovi questo da nessun altra parte" (Scouting + Intelligence)
Feature 4, 14, 15, 11, 19
**Pitch**: "Cerco su 73 portali in 15 lingue che lei non puo' aprire. Le mando un alert personalizzato quando trovo quello che cerca, con trend di prezzo e analisi della sua zona. Nessun altro fa questo."

### CLUSTER B — "Zero rischio, zero lavoro" (Success Fee + Gestione)
Feature 7, 13, 5, 18, 20
**Pitch**: "Paga solo quando ha la macchina in mano. Io gestisco tutto: burocrazia, trasporto, COC, immatricolazione. Lei riceve le chiavi."

### CLUSTER C — "Piu' margine sulla rivendita" (Materiali + Garanzia)
Feature 1, 8, 16, 6
**Pitch**: "Con ogni macchina le do la scheda tecnica professionale in italiano, le foto HD pronte per l'annuncio, e la possibilita' di attivare una garanzia convenzionale che le permette di chiedere €800 in piu' al cliente finale."

### CLUSTER D — "Compra sicuro" (Verifica + Recall + Odometro)
Feature 2, 3, 9, 12
**Pitch**: "Ogni veicolo viene controllato: km verificati su 26 paesi, nessun recall pendente, optional di fabbrica confermati. Se c'e' qualcosa che non va, non glielo propongo."

---

## COMPETITOR ESISTENTI — FEATURE MAP

| Feature | Bolidem | Autotedesche | Importami | eCarsTrade | AUTO1 | ARGOS |
|---------|---------|--------------|-----------|------------|-------|-------|
| Scouting proattivo | No | No | No | Aste | No | SI |
| Success fee | No | No | No | No | No | SI |
| B2B dealer | No | No | No | Parziale | Inverso | SI |
| Alert personalizzato | No | No | No | No | No | SI |
| Scheda rivendita | No | No | No | No | No | SI |
| Recall check | No | No | No | Raccomanda | No | SI |
| Odometro multi-source | No | No | No | Raccomanda | No | SI |
| Market intel zona | No | No | No | No | No | SI |
| Storico prezzi 12m | No | No | No | No | No | SI |
| COC + burocrazia | +€150 | SI | SI | No | No | SI |
| Trasporto | +€840 | SI | SI | No | SI | SI |
| Foto HD rivendita | No | No | No | No | SI | SI |
| Garanzia convenzionale | No | No | No | No | No | SI* |
| Esclusiva 48h | No | No | No | No | No | SI |
| Fee calculator all-in | No | No | No | Parziale | No | SI |

*In sviluppo/partnership da attivare

---

## ROADMAP IMPLEMENTAZIONE

### Sprint 0 (OGGI — gia' pronto o quasi)
- Feature 4: Alert personalizzato → CRM + sequencer gia' esistente
- Feature 6: Delta prezzo IT → CoVe + PDF generator gia' integrati
- Feature 1: Scheda rivendita → adattare PDF generator (dealer-facing, non ARGOS-facing)
- Feature 5: Fee calculator all-in → `fee_calculator.py` gia' esiste
- Feature 18: Confronto fai-da-te vs ARGOS → creare PDF template
- Feature 20: SLA 24h → comunicare nella proposta e sul sito

### Sprint 1 (settimana 2-3)
- Feature 2: Recall check → scraper KBA + car-recalls.eu
- Feature 3: Odometro multi-source → integrare autoDNA o vincheckeurope
- Feature 16: Foto HD organizzate → image_downloader.py gia' esiste, organizzare in cartelle dealer
- Feature 14: Accesso portali B2B → comunicare come vantaggio nel pitch
- Feature 11: Report mensile → template PDF mensile con dati AS24.it
- Feature 7: Gestione documentale → checklist + partner COC/traduzione

### Sprint 2 (mese 2)
- Feature 15: Storico prezzi → Market Index + dati storici scraper
- Feature 19: Modelli alta rotazione per zona → analisi AS24.it per provincia
- Feature 9: Score qualita' foto → logica scoring sul detail enricher
- Feature 12: VIN decode → integrare vindecoder.eu o stat.vin
- Feature 13: Trasporto coordinato → accordo con bisarca DE→IT

### Sprint 3 (mese 3+)
- Feature 8: Garanzia convenzionale → contattare ConformGest / AutoProtetta per accordo B2B
- Feature 10: Esclusiva 48h → regola operativa nel CRM (flag dealer priority)
- Feature 17: Briefing vocale WA → edge-tts + wa-daemon integration

---

## FONTI COMPLETE

- [DEKRA Italia valutazione usato](https://www.dekra.it/it/gestione-e-valutazione-parco-usato/)
- [ConformGest garanzie usato](https://www.conformgest.it/)
- [AutoProtetta garanzia post-acquisto](https://www.autoprotetta.it/)
- [4dealer.it garanzia legale](https://www.4dealer.it/)
- [Car-Recalls.eu VIN check EU](https://car-recalls.eu/vin-check-recalls/)
- [KBA recall database DE](https://www.kba.de/EN/Themen_en/Marktueberwachung_en/Rueckrufe_en/Rueckrufdatenbank_en/rueckrufdatenbank_inhalt_en.html)
- [autoDNA odometro storico](https://www.autodna.com/)
- [VinCheckEurope odometer history](https://vincheckeurope.eu/)
- [vindecoder.eu API free](https://vindecoder.eu/api/)
- [eCarsTrade VIN check tools](https://ecarstrade.com/blog/best-vin-decoders-for-car-history)
- [eCarsTrade import Italy guide](https://ecarstrade.com/blog/how-to-import-a-car-to-italy)
- [COC certificate EuroCOC](https://www.eurococ.eu/en/)
- [COC registration Italy](https://www.coc-online.com/blogs/post/how-to-register-an-imported-vehicle-in-italy-importance-of-the-coc)
- [praticheauto.online immatricolazione 2025](https://praticheauto.online/blog/articles/importazione-e-immatricolazione-auto-estera-guida-2025)
- [alVolante import guide](https://www.alvolante.it/da_sapere/legge-e-burocrazia/importare-un-auto-dall-estero-costi-tempi-e-tasse-381577)
- [INDICATA Italy dealer intelligence](https://www.autorolagroup.com/italiandealers_june2023/)
- [vAuto Stockwave wholesale sourcing](https://www.vauto.com/products/stockwave/)
- [AUTO1 CAT AI damage detection](https://www.auto1-group.com/press/pressrelease/auto1-group-sets-new-standards-with-its-inhouse-ai-powered-damage-detection-technology/)
- [MotorK annunci usato Italia](https://www.motork.io/it/come-fare-annuncio-online-auto-usata/)
- [eCarsTrade marketing dealer strategies](https://ecarstrade.com/blog/marketing-strategies-for-car-dealerships)
