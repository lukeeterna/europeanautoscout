# S69 — Deep Research: Scoring & Intelligence Systems Enterprise-Grade

**Data**: 2026-03-20
**Scope**: Come funzionano i migliori sistemi di scoring/pricing/intelligence in 7 settori
**Obiettivo**: Estrarre pattern architetturali applicabili a CoVe Engine ARGOS

---

## 1. REAL ESTATE — Zillow Zestimate & Redfin Estimate

### 1.1 Zillow Zestimate

**Architettura**: Neural network (dal 2017, rimpiazza il precedente ensemble). Dal 2019 usa anche CNN addestrate su milioni di foto di case per valutare qualita visiva.

**Fonti dati**:
- County e tax assessor records
- Feed diretti da centinaia di MLS (Multiple Listing Services)
- Listing price, descrizione, comparable
- Tax assessments, vendite precedenti
- Market trends stagionali
- Foto degli interni (CNN addestrate su milioni di immagini)

**Gestione uncertainty**:
- Pubblica SEPARATAMENTE accuracy on-market vs off-market
- On-market median error: **1.83%** (2025)
- Off-market median error: **7.01%** (2025)
- Questo e fondamentale: il sistema AMMETTE che senza dati freschi l'errore e 4x

**Miglioramento storico**: 4-5% errore mediano (2020) → 1.83% (2025)

**Fattori pesati regionalmente**: Vista acqua +30% a Miami, +15% in Colorado → i pesi cambiano per mercato locale. Aggiornamento: settimanale (off-market), giornaliero (on-market).

**Lezione per ARGOS**: Separare SEMPRE confidence on-data (veicolo con storico completo) da off-data (veicolo con dati parziali). Non mescolare mai le due metriche.

### 1.2 Redfin Estimate

**Architettura**: Proprietario ML, basato su 500+ data points per proprieta.

**Fonti dati**:
- Accesso completo ai MLS (Redfin e un broker, quindi ha dati di prima parte)
- 500+ feature: vista acqua, strada trafficata, quartiere, ecc.
- Miliardi di data points aggregati su 92 milioni di case USA

**Accuracy**:
- On-market: **1.99%** median error (2025)
- Off-market: **7.64%** median error
- Aggiornamento: giornaliero (on-market), settimanale (off-market)

**Processo miglioramento**: Centinaia di esperimenti A/B, test e re-test di modelli, incorporazione continua di nuovi dati.

**Lezione per ARGOS**: Redfin ha accuracy migliore perche e un BROKER con dati di prima parte (come ARGOS che ha accesso diretto ai portali). Chi ha i dati grezzi vince.

### 1.3 Pattern comune Real Estate

| Aspetto | Zillow | Redfin | Pattern |
|---------|--------|--------|---------|
| Modello | Neural Network | Proprietary ML | Deep learning su tabular data |
| Data points | 250+ fonti | 500+ features | Piu dati = meglio |
| On-market error | 1.83% | 1.99% | ~2% e il benchmark |
| Off-market error | 7.01% | 7.64% | 4x peggio senza dati freschi |
| Aggiornamento | Daily/Weekly | Daily/Weekly | Frequenza = accuracy |
| Regional | 100+ zone USA | Per mercato | SEMPRE localizzare |

---

## 2. FINANCIAL TRADING — Bloomberg/LSEG (ex-Refinitiv)

### 2.1 Bloomberg Terminal

**Architettura**: "Ticker Plant" — infrastruttura di ingestione dati che processa milioni di update/secondo con uptime 24/7 (meno outage di AWS storicamente).

**Aggregazione multi-source**:
- Feed diretti da exchange globali
- Dati company financials raccolti manualmente, scrubbed, standardizzati
- Alternative data (satellite, social, shipping) tramite ALTD function
- Dati concordati (concordance = mapping tra identificatori diversi per lo stesso asset)

**Gestione conflitti**:
- Bloomberg NON rivela pubblicamente l'algoritmo di risoluzione conflitti
- Approccio noto: **Golden Copy** — una versione "autorevole" viene selezionata come riferimento
- I dati vengono normalizzati per accounting standard diversi (GAAP vs IFRS)

**Pesi per affidabilita**: Bloomberg usa una gerarchia implicita:
1. Feed exchange diretti (massima affidabilita)
2. Filing regolamentari (SEC, ESMA)
3. Company disclosures
4. Terze parti verificate
5. Alternative data (peso minore, ma crescente)

**Dati mancanti**: Interpolazione, peer comparison, o esplicitamente marcati come "N/A" — MAI inventati.

**Lezione per ARGOS**: Il concetto di **Golden Copy** e direttamente applicabile. Quando 3 portali danno 3 prezzi diversi per lo stesso VIN, serve una gerarchia di affidabilita. Mobile.de > AutoScout24 > piccoli portali locali.

### 2.2 LSEG (ex-Refinitiv)

**Consolidazione**: Aggregazione di multiple fonti per lo stesso strumento con:
- Display desktop intuitivi
- Symbology e reference per uso machine
- Monitoraggio attivo di metriche: accuracy, timeliness, completeness

**Data Quality Metrics**: LSEG traccia esplicitamente 3 dimensioni:
1. **Accuracy** — il dato e corretto?
2. **Timeliness** — il dato e recente?
3. **Completeness** — ci sono campi mancanti?

**Lezione per ARGOS**: Implementare le stesse 3 metriche per ogni listing scraping. Un listing con prezzo ma senza km e "incomplete". Un listing di 30 giorni fa e "stale".

---

## 3. INSURANCE/AUTOMOTIVE — KBB, NADA, Edmunds

### 3.1 Kelley Blue Book (KBB)

**Fonti dati**: 250+ fonti, 3.0 TRILIONI di data points (dichiarati).

**Fattori di valutazione**:
- Private party sales e dealer transactions
- Condizione veicolo (da "excellent" a "fair")
- Mileage
- Market fluctuation locale
- Trend stagionali
- Make/Model/Trim/Options

**Variazioni regionali**: Valori regionalizzati per 100+ aree USA, aggiornati settimanalmente. Differenze basate su supply/demand locale e pricing trends per ZIP code.

**Punto chiave**: KBB e molto reattivo a cambiamenti di domanda locale → edge nei mercati volatili.

### 3.2 NADA Guides

**Fonti dati**: Dealer, aste veicoli, manufacturer, listing online.

**Metodo**: Focus su wholesale e auction data → valori piu stabili e conservativi. Usato come benchmark dai dealer e dalle banche per finanziamenti.

**Differenza vs KBB**: NADA piu stabile (basato su wholesale), KBB piu reattivo (basato su retail). Per valutazione dealer, NADA e piu rilevante perche riflette il prezzo di acquisto, non il prezzo di vendita.

### 3.3 Edmunds (True Market Value / Suggested Price)

**Team**: 20+ statistici, data scientist, PhD dedicati alla valutazione.

**Fonti dati**: Download settimanale da DMS (Dealer Management System) di 5.000+ dealership USA.

**Metodo**: Analisi di milioni di data points: supply, demand, incentivi, opzioni, transazioni recenti nella zona. Calcolo di scenari multipli per arrivare a:
- Dealer trade-in value
- Dealer retail value
- Private party value

**Lezione per ARGOS**: La separazione in 3 valori (acquisto dealer, vendita dealer, privato) e esattamente quello che CoVe deve fare. Il prezzo su Mobile.de e il "retail asking price DE". Il prezzo target ARGOS e il "wholesale import price IT". La fee si calcola sul delta.

### 3.4 Pattern comune Insurance/Automotive

| Provider | Fonti | Aggiornamento | Focus |
|----------|-------|---------------|-------|
| KBB | 250+ fonti, 3T datapoints | Settimanale | Retail, reattivo |
| NADA | Dealer + aste | Mensile | Wholesale, stabile |
| Edmunds | 5.000 DMS dealer | Settimanale | Transaction-based |

---

## 4. E-COMMERCE — Amazon Buy Box & Dynamic Pricing

### 4.1 Amazon Buy Box (Featured Offer)

**Importanza**: 80%+ delle vendite passano dal Buy Box.

**Fattori dell'algoritmo** (2025, aggiornato):

| Fattore | Peso stimato | Note |
|---------|-------------|------|
| **Landed Price** (prodotto + shipping) | ALTO | Non il prezzo piu basso in assoluto, ma competitivo |
| **Fulfillment method** (FBA vs FBM) | ALTO | FBA fortemente favorito |
| **Seller performance metrics** | ALTO | Order defect rate, late shipment rate |
| **Inventory depth** | MEDIO | Stock disponibile |
| **Historical track record** | MEDIO | Longevita e consistenza del venditore |
| **Feedback rating** | MEDIO | Recensioni positive |
| **Delivery speed** | MEDIO-ALTO | Prime-eligible favorito |
| **Account age** | BASSO-MEDIO | Vendor esperti vs nuovi |

**Trust scoring**: Un venditore con track record eccellente puo mantenere il Buy Box ANCHE con prezzo leggermente piu alto di un competitor nuovo. Il sistema premia l'affidabilita dimostrata nel tempo.

**AI Personalization (2025)**: Buy Box ora personalizzato per acquirente basato su:
- Location
- Order history
- Delivery preferences
- Seller proximity a magazzini locali

**Lezione per ARGOS**: Il concetto di "seller reliability score" e applicabile ai portali: un portale con storico di listing accurati (prezzi reali, km verificati) dovrebbe avere peso maggiore nel CoVe score. AutoScout24 dealer verificato > annuncio privato su piattaforma minore.

---

## 5. USED CAR MARKET INTELLIGENCE — Sistemi Specifici

### 5.1 DAT/Schwacke (Germania — Gold Standard)

**Posizione**: SilverDAT 3 e IL software di riferimento per concessionari tedeschi. Equivalente di KBB/NADA per il mercato DE.

**Metodo di valutazione**:
- Basato su **report reali di vendita dai dealer** (NOT offer prices da internet)
- Considera completamente equipaggiamento standard e opzionale
- Valuta condizione veicolo vs riparazioni necessarie
- Fornisce previsione valore futuro

**SilverDAT WebScan**: Monitoraggio comparativo da exchange internet (Mobile.de, AutoScout24) → confronta prezzo DAT vs prezzo mercato.

**Innovazione EV**: Primo sistema standardizzato a considerare State of Health (SoH) della batteria nella valutazione EV.

**API**: WSDL disponibile su webservices.eurotaxglass.com (SOAP API, non REST).

**Lezione per ARGOS**: DAT usa dati di VENDITA REALE, non di LISTING. Questo e il gold standard. Per ora ARGOS usa listing prices (che sono asking prices, non transaction prices). La differenza puo essere 5-15%. Notare questo nel CoVe score come "listing_premium_adjustment".

### 5.2 Eurotax / Glass's (Pan-Europeo — Autovista Group → J.D. Power)

**Copertura**: 30 paesi europei. Acquisita da J.D. Power.

**Servizi**:
- Valuation data per date correnti, passate e future
- Stima mileage
- Dati tecnici e fleet management
- Estimating, bodyshop e dealer management systems

**Dati di mercato (maggio 2025)**:
- Auto 3 anni mantiene 50.8% del prezzo da nuova (media EU)
- Ibridi: vendita piu rapida (35.5 giorni medi UK)
- Ibridi: retention valore piu alta dopo 3 anni

**Lezione per ARGOS**: Eurotax/Glass's e il benchmark pan-europeo. Il dato "50.8% retention a 3 anni" e utile come reality check per le valutazioni CoVe.

### 5.3 AutoScout24 Valuation Tool

**Metodo**: Big data-based tool che confronta asking prices con stime calcolate internamente.

**Algoritmo probabile** (da ricerca accademica su dati AS24):
- XGBoost regressor come backbone (gradient boosting su decision tree)
- Outlier detection density-based su 3 sottospazi: Price-Mileage, Price-Age, Price-Power
- I due indicatori primari di deprezzamento: km e eta

**ProbSAINT (ricerca accademica 2024, dati AS24 + Mobile.de)**:
Modello stato dell'arte per pricing auto usate con uncertainty:
- **Architettura**: SAINT (Self-Attention and Inter-Sample Attention) → transformer per dati tabular
- **Training data**: ~2 milioni di record (luglio 2018 - agosto 2022)
- **Features**: 65 (55 categoriche, 7 numeriche, 3 date)
- **Output**: Predice MEDIA (mu) e VARIANZA (sigma) direttamente → uncertainty nativa
- **Confidence**: C = 1 - (sigma/mu)
- **Performance**: MAPE 5.3%, MAE ~1.782 EUR
- **Funzionalita unica**: "Probabilistic Dynamic Forecasting" — predice distribuzione prezzo per diverse durate di listing

**Lezione per ARGOS**: ProbSAINT dimostra che un modello che predice sia prezzo sia uncertainty (come CoVe gia fa con Bayesian confidence) e superiore a modelli che predicono solo il prezzo. La formula C = 1 - (sigma/mu) e elegante e potrebbe sostituire o complementare il Bayesian posterior di CoVe.

### 5.4 carVertical (Vehicle History)

**Fonti**: 1.000+ database in 45+ paesi.

**Tipi di fonte**:
- Registri nazionali e polizia
- Database INTERPOL
- Istituzioni finanziarie
- Piattaforme classificati
- Database assicurativi e leasing

**Gestione conflitti dati**:
1. Error correction (fix inconsistenze da data entry manuale)
2. Standardizzazione (traduzione + categorizzazione)
3. Validazione statistica (ML per anomaly detection)
4. Per km: confronto con benchmark "mileage tipico" per modello ed eta

**Certificazione**: ISO/IEC 27001:2017

**API B2B**: Disponibile, VIN-based, integrazione REST.

**Pricing**: ~29.90 EUR/report singolo, sconti volume per dealer.

### 5.5 API di Mercato Auto Disponibili

| Provider | Tipo | Copertura | Prezzo | Note |
|----------|------|-----------|--------|------|
| **Eurotax/Autovista** | Valuation | 30 paesi EU | Enterprise (migliaia/anno) | Gold standard EU, SOAP API |
| **DAT SilverDAT** | Valuation + VIN | DE primario | Enterprise | Il benchmark tedesco |
| **carVertical** | Vehicle History | 45 paesi | ~30 EUR/report | VIN decoder + history |
| **Vehicle Databases** | Market Value | US focus | Trial disponibile | Condizione-based |
| **MarketCheck** | Listing Data | US primario | Tiered | Il piu grande DB listing |
| **CarsXE** | Market Value | Multi | API pricing | Real-time estimates |
| **Zyla Labs** | EU Used Car Prices | Europa | Pay-per-call | Aggregatore EU |
| **Black Book** | Wholesale/Auction | US | Enterprise | Dati aste reali |
| **Carapis** | Listing Aggregation | EU | ~300-600/mese | Scraping aggregato |
| **KBB API** | Valuation | US | Enterprise | Il benchmark US |
| **Edmunds API** | Valuation | US | Enterprise | TMV (transaction-based) |

---

## 6. BAYESIAN SCORING IN PRODUZIONE — Esempi Reali

### 6.1 Stripe Radar (Fraud Detection)

**Il caso studio piu documentato di scoring Bayesian-like in produzione.**

**Architettura evoluzione**:
- Pre-2022: Wide & Deep ensemble (XGBoost + DNN)
- Post-2022: Pure DNN-only, architettura "multi-branch" ispirata a ResNeXt
- "Network-in-Neuron": computazioni splittatein branch distinti per feature representation

**Scala**:
- Processa $1.4 trilioni/anno in pagamenti
- Valuta 1.000+ caratteristiche per transazione
- Decisione in <100ms
- False positive rate: 0.1% su miliardi di pagamenti legittimi

**Cold-start per nuovi merchant**:
- Radar usa la rete globale Stripe come prior: anche un merchant nuovo beneficia dei pattern di frode appresi da TUTTI i merchant
- Questo e esattamente un approccio Bayesian: il prior e costruito dalla rete, il posterior si aggiorna con i dati specifici del merchant

**Calibrazione**:
- Training time ridotto dell'85% (< 2 ore) permettendo esperimenti multipli/giorno
- 10x aumento dati di training → miglioramenti significativi
- 100x expansion in corso
- Rilascio modelli 3x piu veloce grazie ad automated training

**Lezione per ARGOS**: Il pattern "network prior → merchant-specific posterior" e esattamente applicabile. CoVe puo usare tutti i dati di mercato raccolti (prior) e poi raffinare per specifico dealer/modello/mercato (posterior). Il cold-start si risolve con un prior informativo costruito dai dati aggregati.

### 6.2 FICO Score (Credit Scoring)

**Architettura**: Non Bayesian puro, ma scoring pesato con fattori:
- Payment history: 35%
- Amounts owed: 30%
- Length of credit history: 15%
- New credit: 10%
- Credit mix: 10%

**Gestione cold-start**: "Thin file" consumers senza storia creditizia sono il principale challenge. Soluzioni:
- Alternative data (affitto, utenze) come proxy
- VantageScore compete con FICO usando piu alternative data

**Lezione per ARGOS**: I pesi fissi e trasparenti (35/30/15/10/10) hanno il vantaggio della spiegabilita. Per ARGOS, i pesi del CoVe score dovrebbero essere documentati e spiegabili al dealer: "Questo veicolo ha score 87/100 perche: km verificati (+25), prezzo sotto media mercato (+20), storico pulito (+15), ecc."

### 6.3 Bayesian Experimental Design (BED) in Manufacturing

**Principio**: Selezione adattiva di esperimenti basata su risultati precedenti, usando acquisition function che massimizza il contenuto informativo.

**Applicazioni reali**: Material science, additive manufacturing, laser processing, fluid dynamics, biotechnology.

**Cold-start**: I ricercatori hanno dimostrato che "calibrated early insights possono essere generati entro 5-7 giorni mantenendo esplicita umilta epistemica." Questo con solo 5-10 data points iniziali.

**Lezione per ARGOS**: Anche con 10-20 veicoli analizzati, CoVe puo dare stime calibrate SE mantiene uncertainty bounds espliciti. La chiave e non fingere certezza che non si ha.

### 6.4 Bayesian Networks in Oil & Gas

**BP ACE platform + SOCAR digital**: Usano modelli probabilistici, framework fuzzy-Bayesian ibridi, e reinforcement learning per gestire produzione sotto incertezza.

**Vantaggi BN**: Gestiscono naturalmente:
- Variabili mancanti
- Tipi di dati misti (categorici + numerici)
- Ragionamento sotto informazione incompleta

**Lezione per ARGOS**: Quando mancano dati (es. km non dichiarati, storico parziale), un Bayesian Network puo comunque dare una stima ragionata usando le variabili disponibili, con confidence calibrata automaticamente.

---

## 7. CROSS-BORDER ARBITRAGE DETECTION

### 7.1 Crypto/DeFi Arbitrage

**Il settore piu avanzato per detection algoritmica di price differentials.**

**Metodi**:
- **Vector Error Correction Models (VECM)**: Cattura cross-market adjustment su dati high-frequency (10min intervals)
- **CNN su dati real-time**: Deep learning per identificare discrepanze prezzo e eseguire trade
- **Moore-Bellman-Ford modificato**: Trova cicli di arbitraggio su grafi di exchange
- **ML + Statistical Methods**: Probabilita che le condizioni di mercato attuali generino arbitraggio profittevole

**Speed**: Le gap di prezzo si comprimono sempre piu velocemente man mano che il mercato matura. Pre-positioning del capitale e velocita di esecuzione sono critici.

### 7.2 Retail Cross-Border (Oliver Wyman)

**Dato chiave**: Rischio arbitraggio = **20% medio** per beni branded in Europa. Per grocery: >30 miliardi EUR di esposizione commerciale.

**Strategie difensive** (lato venditore):
- Armonizzazione prezzi completa
- Pricing corridors (differenziali abbastanza piccoli da non giustificare trasporto)
- Team centralizzato per trade-spend cross-country

### 7.3 Used Car Cross-Border EU

**Dati reali 2025**:
- Germania: +0.4% sopra media EU per prezzi auto
- Italia: -0.3% sotto media EU
- Il delta nominale DE→IT sembra piccolo, MA:
  - Tassazione diversa (IVA, IPT, bollo)
  - Pricing-to-market (dealer IT fanno ricarico superiore)
  - Disponibilita: modelli premium piu comuni in DE che in Sud Italia

**Flussi cross-border osservati**:
- FR/DE → BG/RO: diesel a fine vita
- DE → IT: premium usato (il mercato ARGOS)
- AUTO1 Group: +2.7% uptick prezzi Q1 2025 grazie ad algorithmic bidding

**Frode cross-border**: 150.000 casi di km manipolati in transazioni cross-border 2023. Germania ha database centralizzato per odometro. Italia: nessun equivalente.

**Residual value trend 2025**: Calo in AT, FR, DE, IT, ES, CH, UK. Veicoli a 36 mesi/60.000km: -2.000 EUR year-on-year.

**Lezione per ARGOS**: L'arbitraggio DE→IT non e sul prezzo medio nazionale (quasi uguale). E su:
1. **Disponibilita**: BMW X5 M50d piu comuni in DE
2. **Condizione**: Autobahn vs citta = usura diversa
3. **Ricarico dealer IT**: 15-25% sopra wholesale
4. **Regime margine**: IVA non versata = 22% di vantaggio competitivo

---

## 8. SINTESI — Pattern Architetturali per CoVe Engine v5

### 8.1 Data Quality Framework (da Bloomberg/LSEG)

```
Per ogni listing raccolto, calcolare:
  ACCURACY:    prezzo coerente con mercato? (z-score)
  TIMELINESS:  eta del listing (ore/giorni)
  COMPLETENESS: campi presenti / campi totali

  QUALITY_SCORE = w1*accuracy + w2*timeliness + w3*completeness
  dove w1=0.4, w2=0.3, w3=0.3
```

### 8.2 Golden Copy Strategy (da Bloomberg)

```
Gerarchia affidabilita portali ARGOS:
  Tier 1 (gold): DAT/Schwacke, BCA aste (transaction prices)
  Tier 2 (silver): AutoScout24 DE, Mobile.de (dealer verificati)
  Tier 3 (bronze): AutoScout24 altri paesi, Willhaben, Otomoto
  Tier 4 (copper): Portali piccoli, Marktplaats, Blocket
  Tier 5 (tin): Annunci privati, piattaforme senza verifica

  Quando piu portali hanno lo stesso VIN:
    golden_price = weighted_average(prices, weights=tier_weights)
    confidence += bonus per consensus multi-portale
```

### 8.3 Uncertainty Quantification (da ProbSAINT + Zillow)

```
Per ogni valutazione CoVe:
  ON-DATA confidence  (veicolo con VIN check + multi-source) → target 90%+
  OFF-DATA confidence (veicolo con solo listing price) → target 60-70%

  PUBBLICARE SEMPRE la confidence band:
    "Prezzo stimato: 28.500 EUR (+/- 1.200 EUR, confidence 82%)"

  Formula ProbSAINT: C = 1 - (sigma / mu)
  dove sigma = std dev delle stime, mu = media delle stime
```

### 8.4 Multi-Value Output (da KBB/NADA/Edmunds)

```
Per ogni veicolo, calcolare 3 valori:
  1. WHOLESALE (prezzo asta/dealer DE) → il prezzo a cui ARGOS compra
  2. RETAIL IT (prezzo dealer IT equivalente) → il prezzo a cui il dealer vende
  3. MARGINE NETTO = retail_IT - wholesale_DE - fee_ARGOS - costi_import

  Separare: trade-in value, retail value, private party value
```

### 8.5 Cold-Start Resolution (da Stripe Radar)

```
Per modelli/mercati con pochi dati:
  PRIOR = distribuzione prezzo per (marca, segmento, anno, fascia_km)
  Costruito da TUTTI i veicoli raccolti globalmente

  POSTERIOR = prior aggiornato con dati specifici del modello/mercato

  Con 0 dati specifici: usa il prior (confidence bassa, ~50%)
  Con 5-10 listing: posterior inizia a divergere dal prior
  Con 50+ listing: posterior domina (confidence alta, ~85%+)
```

### 8.6 Trust Scoring per Portali (da Amazon Buy Box)

```
Per ogni portale, calcolare TRUST SCORE:
  - Storico accuracy (listing price vs prezzo finale vendita): 35%
  - Completezza dati (km, foto, VIN, storico): 30%
  - Volume e frequenza listing: 15%
  - Track record (anni di operazione, verifiche): 10%
  - Feedback community (segnalazioni frode): 10%

  TRUST_SCORE determina il peso del portale nella Golden Copy
```

### 8.7 Listing Premium Adjustment (da DAT/Schwacke)

```
CRITICO: I listing price NON sono transaction prices.

  listing_premium = (asking_price - actual_sale_price) / asking_price

  Valori tipici per mercato:
    DE dealer:    3-8% premium (prezzo esposto vs venduto)
    DE privato:   8-15% premium (piu negoziazione)
    IT dealer:    10-20% premium (mercato meno trasparente)
    Aste B2B:     0-2% premium (prezzo quasi reale)

  CoVe DEVE applicare questo sconto stimato per calcolare il prezzo reale
```

### 8.8 Arbitrage Detection Formula (da Crypto + Oliver Wyman)

```
Per ogni veicolo trovato su portale estero:

  SPREAD = price_IT_retail - price_source - costs_import
  SPREAD_PCT = SPREAD / price_source * 100

  Se SPREAD_PCT > 8% → OPPORTUNITY (margine dealer positivo dopo fee ARGOS)
  Se SPREAD_PCT > 15% → HIGH_OPPORTUNITY (margine eccellente)
  Se SPREAD_PCT < 5% → SKIP (margine troppo basso)
  Se SPREAD_PCT < 0% → ANOMALY (prezzo estero piu alto → possibile frode o errore)

  costs_import = trasporto (600-1000) + burocrazia (200-400) + fee_ARGOS (800-1200)
```

---

## 9. ERROR RATES BENCHMARK — Comparazione Cross-Settore

| Sistema | Settore | Median Error | Note |
|---------|---------|-------------|------|
| Zillow (on-market) | Real Estate | 1.83% | Con dati freschi |
| Zillow (off-market) | Real Estate | 7.01% | Senza dati freschi |
| Redfin (on-market) | Real Estate | 1.99% | Broker con dati prima parte |
| Redfin (off-market) | Real Estate | 7.64% | 4x peggio |
| ProbSAINT | Used Car | 5.3% MAPE | ~1.782 EUR MAE |
| KBB | Used Car | ~5-8% | Non pubblicato ufficialmente |
| Stripe Radar | Fraud | 0.1% FP | Su miliardi di transazioni |
| DAT/Schwacke | Used Car DE | ~3-5% | Basato su vendite reali |

**Target CoVe ARGOS**: MAPE < 8% per valutazioni on-data (con VIN e multi-source), < 15% off-data.

---

## 10. RACCOMANDAZIONI IMPLEMENTATIVE PER CoVe v5

### Priorita ALTA (implementare subito)
1. **Quality Score per listing** (accuracy + timeliness + completeness)
2. **Listing Premium Adjustment** (-5% DE dealer, -12% IT dealer)
3. **Confidence band separata** on-data vs off-data
4. **Arbitrage Spread Calculator** con threshold 8%/15%

### Priorita MEDIA (implementare entro S75)
5. **Portal Trust Score** (pesatura per affidabilita portale)
6. **Golden Copy** quando stesso VIN appare su piu portali
7. **Multi-value output** (wholesale DE / retail IT / margine netto)

### Priorita BASSA (roadmap S80+)
8. **ProbSAINT-like model** (SAINT transformer su dati tabular)
9. **Bayesian cold-start** (prior globale → posterior specifico)
10. **VECM per trend detection** (previsione direzione prezzi)

---

## FONTI

### Real Estate
- [Zillow Zestimate Official](https://www.zillow.com/zestimate/)
- [Zillow Zestimate Accuracy 2026](https://agentsgather.com/zillow-estimates-how-accurate-are-zestimates-in-2026/)
- [How Accurate Is Zillow 2025](https://www.copperkeysolutions.com/blog/how-accurate-is-zillows-zestimate-in-2025-a-must-read-guide-for-home-buyers-and-sellers)
- [Redfin Estimate Official](https://www.redfin.com/redfin-estimate)
- [Redfin Estimate Accuracy](https://www.redfin.com/news/redfin-estimate-accuracy/)
- [Redfin vs Zillow 2026](https://www.realestateskills.com/blog/redfin-vs-zillow)

### Financial Trading
- [Bloomberg ALTD](https://www.bloomberg.com/company/stories/what-took-build-altd-bloomberg-terminal-alternative-data-function/)
- [Bloomberg System Design](https://www.systemdesignhandbook.com/guides/bloomberg-system-design-interview/)
- [Bloomberg 7 Powers](https://theterminalist.substack.com/p/bloombergs-7-powers-and-why-the-terminal)
- [LSEG Data Analytics](https://www.lseg.com/en/data-analytics)

### Insurance/Automotive Valuation
- [KBB vs NADA](https://www.indyautoman.com/blog/kelley-blue-book-vs-nada)
- [KBB vs NADA Guide](https://www.usedcars.com/kelley-blue-book-vs-nada-guides)
- [Edmunds TMV](https://www.edmunds.com/tmv.html)
- [Edmunds TMV Methodology (PDF)](http://static.ed.edmunds-media.com/unversioned/img/drc/Edmunds-True-Market-Value.pdf)

### E-commerce
- [Amazon Buy Box 2025](https://amazonsellerslawyer.com/blog/amazon-buy-box-algorithm-2025/)
- [Buy Box Algorithm Deep Dive](https://www.bebolddigital.com/blog/amazon-buy-box-algorithm)
- [Buy Box Strategy](https://www.cahoot.ai/amazon-buy-box-strategy/)

### Used Car Market Intelligence
- [DAT Used Vehicle Valuation](https://www.datgroup.com/products/used-vehicle-valuation/)
- [Schwacke List](https://www.cashforcars.de/en/blog-schwacke-list-calculate-car-value)
- [Eurotax/Glass's Products](https://autovistagroup.com/products-and-services/eurotax-data)
- [Glass's Guide](https://glass.co.uk/)
- [carVertical Data Sources](https://www.carvertical.com/en/blog/carvertical-data-sources)
- [carVertical B2B API](https://www.carvertical.com/en/business/api)
- [ProbSAINT Paper](https://arxiv.org/html/2403.03812v1)
- [AutoScout24 Price Rating Tool](https://aimgroup.com/2017/03/12/autoscout24-rolls-out-price-rating-tool-for-buyers/)

### Bayesian Scoring
- [Stripe Radar Technical](https://stripe.dev/blog/how-we-built-it-stripe-radar)
- [Stripe Radar ML Primer](https://stripe.com/guides/primer-on-machine-learning-for-fraud-protection)
- [Bayesian Score Calibration (arXiv)](https://arxiv.org/abs/2211.05357)
- [Progressive Bayesian Cold-Start (arXiv)](https://arxiv.org/pdf/2601.03299)
- [Federal Reserve Bayesian Fraud Simulator](https://www.federalreserve.gov/econres/feds/files/2025017pap.pdf)

### Cross-Border Arbitrage
- [Euronews Car Prices Europe 2025](https://www.euronews.com/business/2025/10/18/car-and-vehicle-prices-across-europe-how-much-is-it-in-your-country)
- [Oliver Wyman Cross-Country Arbitrage](https://www.oliverwyman.com/our-expertise/insights/2019/dec/retail-consumer-journal-vol-7/crosscountry-arbitrage.html)
- [Europe Used Car Market Trends 2025](https://autovista24.autovistagroup.com/news/mmu-how-did-europes-major-used-car-markets-perform-in-2025/)
- [Crypto Arbitrage ML (Wiley)](https://onlinelibrary.wiley.com/doi/full/10.1002/nem.70030)
- [Car Value API Providers 2025](https://vehicledatabases.com/articles/best-car-value-api-providers)
- [Car Price Data Marketplace](https://datarade.ai/data-categories/car-price-data)

### API Mercato Auto
- [Zyla Labs EU Used Car Prices API](https://zylalabs.com/api-marketplace/data/europe+used+cars+prices+database+api/2324)
- [MarketCheck API](https://docs.marketcheck.com/docs)
- [Vehicle Databases API](https://vehicledatabases.com/vehicle-market-value-api)
