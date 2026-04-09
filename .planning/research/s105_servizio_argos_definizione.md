# S105 -- Definizione Servizio ARGOS Automotive: Modelli, Flussi, Costi, Protezione Fee

**Data:** 2026-04-09
**Confidenza complessiva:** MEDIUM-HIGH
**Fonti:** Bolidem.it, Importami.com, eCarsTrade.com, Belastingdienst.nl, RDW.nl, USP.gv.at, Fiscomania.com, ACI.gov.it, alVolante.it, codice-civile/brocardi.it, ricerche S84/S99 interne

---

## 1. MODELLI DI SERVIZIO COMPETITOR -- ANALISI DETTAGLIATA

### 1A. BOLIDEM -- Fee Strutturate Step-by-Step

**Fonte:** [bolidem.it/servizi](https://www.bolidem.it/servizi/) | Confidenza: HIGH

Bolidem opera come mandatario B2C con fee upfront per ogni step. Il cliente trova l'auto, Bolidem gestisce.

| Step | Servizio | Fee | Cosa include |
|------|----------|-----|-------------|
| 1 | Chiamata e trattativa | EUR 20 | Contatto venditore, negoziazione prezzo, verifica disponibilita' |
| 2 | Ispezione video | EUR 299 | Video chiamata con venditore, controllo visivo, report condizioni |
| 3a | Accompagnamento ritiro | EUR 950 | Documenti export, targhe export (costo targhe escluso), monitoraggio, assistenza giorno ritiro |
| 3b | Trasporto bisarca | da EUR 1.790 | Consegna a domicilio, monitoraggio completo, verifica documenti |
| 4 | Pratiche immatricolazione IT | EUR 150 (opzionale) | Guida immatricolazione, supporto documentale |
| Extra | Supplemento SUV/4x4 | +EUR 120 | Maggiorazione dimensioni |
| Extra | Supplemento furgoni L1H1 | +EUR 240 | Maggiorazione dimensioni |

**Flusso di pagamento Bolidem:**
- Il cliente paga Bolidem PRIMA di ogni step (upfront)
- Il pagamento del veicolo va DIRETTAMENTE dal cliente al venditore ("il pagamento e' fatto direttamente al venditore, mai a Bolidem")
- Bolidem NON tocca i soldi del veicolo -- incassa solo le sue fee per servizi

**Costo totale tipico per il cliente Bolidem:**
- Scenario ritiro autonomo: EUR 20 + 299 + 950 + 150 = **EUR 1.419** (+ costo targhe export EUR 105-420)
- Scenario trasporto bisarca: EUR 20 + 299 + 1.790 + 150 = **EUR 2.259**

**Punto critico:** Bolidem incassa EUR 1.269-2.109 PRIMA che il cliente abbia l'auto. Se l'affare salta dopo l'ispezione, il cliente ha perso EUR 319. Nessun success-fee.

### 1B. IMPORTAMI -- Fee Percentuale

**Fonte:** [importami.com/en/how-it-works](https://www.importami.com/en/how-it-works/) | Confidenza: HIGH

| Voce | Dettaglio |
|------|-----------|
| Fee servizio | 4% del prezzo auto (+IVA), minimo EUR 750 (+IVA) |
| Soglia minimo | Auto < EUR 18.750 = fee minima EUR 750+IVA = EUR 915 |
| Su auto EUR 35.000 | 4% = EUR 1.400 + IVA = EUR 1.708 |
| Su auto EUR 50.000 | 4% = EUR 2.000 + IVA = EUR 2.440 |

**Flusso di pagamento Importami:**
Due modalita':
1. **Il cliente compra direttamente** -- Importami gestisce trasporto e pratiche, il cliente paga il venditore
2. **Importami compra per conto del cliente** -- tramite contratto formale di mandato, Importami paga il venditore con fondi anticipati dal cliente

**Servizio completo:** Importami gestisce trasporto + immatricolazione + consegna con targa italiana. Il cliente riceve auto pronta.

**Punto critico per ARGOS:** Su auto premium (EUR 35-50k), Importami costa EUR 1.700-2.440 vs ARGOS EUR 800-1.200. ARGOS e' significativamente piu' economico, MA il confronto non e' diretto perche' Importami gestisce anche trasporto e immatricolazione (chiavi in mano).

### 1C. eCarsTrade -- Piattaforma Aste B2B

**Fonte:** [ecarstrade.com/howitworks](https://ecarstrade.com/howitworks) | Confidenza: HIGH

| Voce | Dettaglio |
|------|-----------|
| Registrazione | Gratuita, verifica docs aziendali in 1 giorno lavorativo |
| Deposito | Obbligatorio (rimborsabile se smetti) |
| Fee | Commissione variabile per asta + paese origine (non pubblica) |
| Pagamento | Solo bonifico da conto aziendale, pagamento completo prima della preparazione |
| Account manager | Dedicato dopo onboarding |
| Veicoli | Provenienti da societa' leasing, banche, flotte, altri dealer |
| Prezzo medio | ~EUR 9.000 (fascia bassa, no premium) |
| Interfaccia | Solo inglese |

**Flusso di pagamento eCarsTrade:**
1. Dealer vince asta
2. Dealer paga intero importo (prezzo + commissione) via bonifico a eCarsTrade
3. eCarsTrade prepara il veicolo e organizza consegna
4. eCarsTrade paga il proprietario originale (leasing/fleet)

**Punto critico:** eCarsTrade fa da intermediario finanziario: i soldi del dealer passano da eCarsTrade. Questo richiede struttura societaria, conti separati, compliance finanziaria. ARGOS NON dovrebbe replicare questo modello.

### 1D. Confronto Mandatario Immobiliare (come riferimento)

**Fonte:** Art. 1743 c.c., [brocardi.it](https://www.brocardi.it/codice-civile/libro-quarto/titolo-iii/capo-x/art1743.html) | Confidenza: HIGH

Il mandatario/agente immobiliare:
- Riceve mandato di ricerca da acquirente o mandato di vendita da venditore
- Ha diritto all'esclusiva per legge (art. 1743 c.c.) salvo deroga esplicita
- Provvigione dovuta al momento della conclusione dell'affare (success fee)
- Clausola penale per bypass (tipicamente 50-100% della provvigione)
- L'agente NON tocca i soldi della transazione (salvo caparra confirmatoria)

**Lezione per ARGOS:** Il modello immobiliare e' il piu' vicino ad ARGOS. Il procacciatore trova l'opportunita', il cliente compra direttamente, il procacciatore incassa la fee a compravendita avvenuta. La protezione e' data dal contratto di incarico con clausola penale.

---

## 2. FLUSSO DI PAGAMENTO -- I 3 SCENARI ARGOS

### SCENARIO A: Solo Scouting (RACCOMANDATO per il lancio)

```
ARGOS trova l'auto (scraping 28+ portali)
    |
    v
ARGOS produce Dossier (prezzo, margine, fraud check, foto, contatto venditore)
    |
    v
ARGOS invia Dossier al dealer
    |
    v
Dealer decide: "La voglio" / "Non mi interessa"
    |
    [Se SI]
    v
Dealer contatta il venditore DE DIRETTAMENTE (coordinate fornite da ARGOS)
    |
    v
Dealer negozia, paga il venditore DE via bonifico diretto
    |
    v
Dealer organizza trasporto (autonomamente o con suggerimenti ARGOS)
    |
    v
Dealer riceve l'auto, la immatricola (autonomamente o tramite agenzia pratiche)
    |
    v
Dealer paga ARGOS la fee (EUR 800-1.200) entro 15 giorni dall'acquisto
```

**Chi paga cosa:**
| Voce | Paga | A chi | Quando |
|------|------|-------|--------|
| Prezzo auto | Dealer | Venditore DE | Al momento dell'acquisto (bonifico diretto) |
| Trasporto | Dealer | Trasportatore | Alla consegna |
| Pratiche immatricolazione | Dealer | Agenzia pratiche / Motorizzazione | Alla pratica |
| Fee scouting ARGOS | Dealer | ARGOS | Entro 15 gg dall'acquisto |

**Vantaggi Scenario A:**
- ARGOS non tocca MAI i soldi del veicolo (zero rischio finanziario)
- Zero bisogno di conto fiduciario o struttura complessa
- Operabile anche con prestazione occasionale (< EUR 5.000/anno) o P.IVA forfettaria
- Il dealer mantiene pieno controllo sull'acquisto
- Modello identico al procacciatore d'affari immobiliare

**Rischio Scenario A:**
- Il dealer puo' bypassare ARGOS (riceve il dossier, contatta da solo, non paga)
- Mitigazione: contratto con clausola penale + non rivelare venditore prima della conferma (vedi sezione 6)

**SERVONO:**
- Contratto di incarico scouting (GIA' ESISTE: `tools/materiali/contratto_incarico_scouting.html`)
- P.IVA o regime prestazione occasionale
- Conto bancario per ricevere fee

### SCENARIO B: Import Chiavi-in-Mano (SCONSIGLIATO per ora)

```
ARGOS trova l'auto
    |
    v
Dealer approva e trasferisce ad ARGOS: prezzo auto + costi stimati + fee
    |
    v
ARGOS paga il venditore DE (con fondi del dealer)
    |
    v
ARGOS organizza trasporto, paga il trasportatore
    |
    v
ARGOS gestisce burocrazia export DE
    |
    v
ARGOS consegna auto al dealer (immatricolata o da immatricolare)
    |
    v
ARGOS rendiconta: prezzo auto + costi reali + fee, rimborsa eventuale eccedenza
```

**Problemi Scenario B:**
| Problema | Gravita' | Dettaglio |
|----------|----------|-----------|
| Serve P.IVA attiva e ATECO specifico | ALTA | ATECO 46.18.41 (procacciatori affari) o 45.11.01 (commercio auto) |
| Serve conto fiduciario o separato | ALTA | I fondi del dealer NON possono stare sul conto personale |
| Responsabilita' per danni durante trasporto | ALTA | Se l'auto si danneggia, ARGOS e' responsabile |
| Anticipo fondi dealer | ALTA | Il dealer deve fidarsi al punto da anticipare EUR 30-50k |
| Compliance fiscale complessa | ALTA | Fatturazione intra-UE, reverse charge, regime margine |
| Assicurazione professionale necessaria | MEDIA | RC professionale per attivita' di intermediazione |

**Verdetto:** Scenario B richiede struttura societaria (SRL), conto dedicato, assicurazione RC, e complessita' fiscale che ARGOS non ha al lancio. DA NON IMPLEMENTARE fino a quando non ci sono 20+ operazioni completate con Scenario A.

### SCENARIO C: Hybrid -- ARGOS Negozia, Dealer Paga Direttamente (SECONDO STEP)

```
ARGOS trova l'auto
    |
    v
ARGOS negozia col venditore DE (per conto del dealer)
    |
    v
ARGOS ottiene prezzo concordato e condizioni
    |
    v
Dealer paga DIRETTAMENTE il venditore DE (ARGOS fornisce coordinate bancarie)
    |
    v
ARGOS coordina trasporto: identifica trasportatore, negozia prezzo
    --> Dealer paga DIRETTAMENTE il trasportatore
    |
    v
ARGOS coordina burocrazia: identifica agenzia pratiche, supervisiona
    --> Dealer paga DIRETTAMENTE l'agenzia
    |
    v
ARGOS incassa SOLO la fee scouting (EUR 800-1.200)
```

**Vantaggi Scenario C:**
- ARGOS non tocca mai i soldi (come Scenario A)
- Ma offre valore aggiunto (negoziazione, coordinamento)
- Giustifica fee piu' alta (EUR 1.000-1.200) perche' il dealer non deve fare nulla
- Zero complessita' finanziaria per ARGOS

**Limiti Scenario C:**
- Richiede competenza linguistica (tedesco/inglese per negoziare)
- Richiede rete di contatti (trasportatori, agenzie pratiche)
- Piu' tempo per operazione rispetto a Scenario A

**RACCOMANDAZIONE:**
1. **Lancio (0-5 operazioni):** Scenario A puro -- scouting + dossier + contatto venditore
2. **Crescita (5-20 operazioni):** Scenario C -- scouting + negoziazione + coordinamento
3. **Scala (20+ operazioni):** Valutare Scenario B con SRL e struttura adeguata

---

## 3. COSTI REALI PER NAZIONE DI ORIGINE

### Tabella Riepilogativa -- Tutti i Costi di Acquisto Cross-Border

| Paese | Trasporto bisarca --> Sud IT | Documenti export specifici | Tasse/fee specifiche | Tempo medio | Confidenza |
|-------|---------------------------|--------------------------|---------------------|------------|------------|
| **DE** (Germania) | EUR 650-1.000 | Abmeldung (EUR 5-15), Fahrzeugbrief (Teil I+II), COC | Ausfuhrkennzeichen EUR 105-420 (targhe export) | 14-21 gg | HIGH |
| **NL** (Olanda) | EUR 800-1.100 | RDW export (EUR ~10), Kentekenbewijs, Vrijwaringsbewijs, NAP rapport | Export plates EUR ~75 (14 gg validita'), BPM refund possibile | 14-25 gg | MEDIUM-HIGH |
| **BE** (Belgio) | EUR 750-1.000 | DIV cancellation (gratuita, solo restituzione targa), Car-Pass obbligatorio | Exit plates tipo X EUR 75 (30 gg) + assicurazione ~EUR 200 | 14-25 gg | MEDIUM |
| **AT** (Austria) | EUR 600-850 | Abmeldebescheinigung, Zulassungsschein/Typenschein | NoVA refund richiedibile dal venditore (pro-rata, entro 5 anni), Vignetta EUR 12.40 | 14-18 gg | HIGH |
| **FR** (Francia) | EUR 750-1.000 | Carte grise, Certificat de cession, Controle technique (se > 4 anni) | Nessuna tassa export specifica | 18-25 gg | MEDIUM |
| **SE** (Svezia) | EUR 1.200-1.500 | Avregistreringsbevis, Registreringsbevis (Part I+II) | Ferry EUR 120 (Goteborg-Kiel), contachilometri in "mil" (1 mil = 10 km) se ante-2020 | 21-30 gg | MEDIUM |

### Dettaglio per Paese

#### GERMANIA (DE) -- Fonte primaria, 80%+ delle operazioni

**Fonte:** [newsauto.it](https://www.newsauto.it/guide/importare-auto-germania-guida-privati-2025-588780/), research S84, S99 | Confidenza: HIGH

| Voce | Costo | Chi paga | Note |
|------|-------|----------|------|
| Abmeldung (cancellazione targa DE) | EUR 5-15 | Venditore DE | Presso Zulassungsstelle |
| Targhe export (Ausfuhrkennzeichen) DIY | EUR 105-145 | Acquirente | Targhe + tassa + assicurazione RC 15 gg |
| Targhe export tramite agenzia | EUR 150-420 | Acquirente | Auto Empire: EUR 416.50 (30gg) / EUR 178.50 (5gg) |
| Trasporto bisarca --> Sud Italia | EUR 650-1.000 | Acquirente | Macingo, GoTrasporti, Car4Passion |
| COC (se necessario) | EUR 0-300 | Acquirente | BMW EUR 179 (EUROCOC), spesso gia' incluso |
| Contratto vendita (Kaufvertrag) | EUR 0 | - | Modello standard gratuito |

**Documenti necessari dal venditore DE:**
1. Fahrzeugbrief (Zulassungsbescheinigung Teil II) -- originale, fondamentale
2. Abmeldebescheinigung (certificato cancellazione targa)
3. TUV/HU Bericht (certificato revisione, utile ma non obbligatorio per IT)
4. Kaufvertrag firmato (contratto vendita)
5. COC (Certificate of Conformity) -- se disponibile

#### OLANDA (NL)

**Fonte:** [rdw.nl](https://www.rdw.nl/en/import-export-transit/exporting-a-vehicle), [belastingdienst.nl](https://www.belastingdienst.nl/wps/wcm/connect/bldcontenten/belastingdienst/individuals/cars/bpm/refund_of_bpm/refund_if_the_vehicle_is_exported) | Confidenza: MEDIUM-HIGH

| Voce | Costo | Note |
|------|-------|------|
| RDW export registration | EUR ~10 | Online o presso RDW station |
| Export plates (14 gg validita') | EUR ~75 | Targhe bianche con lettere nere |
| Assicurazione temporanea MTPL | EUR ~100 | Obbligatoria per guidare via |
| BPM refund | Variabile (centinaia-migliaia EUR) | Richiedibile se immatricolato dopo 16/10/2006. Va al VENDITORE, non all'acquirente. Puo' essere usato come leva di negoziazione prezzo |

**BPM Refund -- dettaglio importante:**
Il BPM (tassa di registrazione olandese) e' rimborsabile al momento dell'export. L'importo dipende dall'eta' e dal tipo di veicolo. Per un SUV premium 2020-2022, il rimborso puo' essere EUR 2.000-8.000. Ma il rimborso va al proprietario registrato (venditore NL), NON all'acquirente italiano. Questo dato e' utile per negoziare un prezzo piu' basso: "Sai che ti rimborsano il BPM quando esporti, vero?"

#### BELGIO (BE)

**Fonte:** [mobilit.belgium.be](https://mobilit.belgium.be/en/road/registration-and-deregistration/export-vehicle-transit), [vdbtransit.com](https://www.vdbtransit.com/en/transitplaten) | Confidenza: MEDIUM

| Voce | Costo | Note |
|------|-------|------|
| DIV cancellation | EUR 0 (solo restituzione targa per posta o di persona a Bruxelles) | DIV = Direction pour l'Immatriculation des Vehicules |
| Exit plates tipo X (30 gg) | EUR 75 | Via DIV office Bruxelles o transit agent |
| Assicurazione exit plates | EUR ~200 | Media, obbligatoria |
| Car-Pass | EUR 0 (gia' esistente) | Storico km OBBLIGATORIO in Belgio -- documento molto utile |

**Vantaggio BE:** Il Car-Pass belga e' uno dei migliori sistemi anti-frode km in Europa. Se l'auto viene dal Belgio, il rischio odometro e' significativamente piu' basso.

#### AUSTRIA (AT)

**Fonte:** [usp.gv.at](https://www.usp.gv.at/en/themen/steuern-finanzen/weitere-steuern-und-abgaben/normverbrauchsabgabe-nova.html), [nagler.at](https://www.nagler.at/en/news/nova-refund-when-transferring-a-vehicle-abroad/) | Confidenza: HIGH

| Voce | Costo | Note |
|------|-------|------|
| Abmeldebescheinigung | EUR 5-15 | Come Germania |
| Uberstellungskennzeichen (targhe transit) | EUR 50-100 | Piu' economiche che in DE |
| NoVA refund | Variabile, pro-rata sul valore residuo | Richiedibile entro 5 anni, va al venditore registrato. Dal 2016 anche per privati |

**NoVA Refund -- dettaglio:**
Il NoVA (Normverbrauchsabgabe) e' una tassa di consumo austriaca. E' rimborsabile pro-rata quando il veicolo viene esportato. Come per il BPM olandese, va al venditore -- utile come leva di negoziazione.

#### FRANCIA (FR)

| Voce | Costo | Note |
|------|-------|------|
| Carte grise (cancellazione) | EUR 0 | Procedura gratuita online (histovec.interieur.gouv.fr) |
| Certificat de cession | EUR 0 | Modulo CERFA 15776 gratuito |
| Controle technique | EUR 50-80 | Obbligatorio se > 4 anni, va fatto dal venditore |
| Nessuna tassa export specifica | EUR 0 | |

**Confidenza:** MEDIUM -- dati da training, non verificati su fonte primaria recente.

#### SVEZIA (SE)

| Voce | Costo | Note |
|------|-------|------|
| Avregistrering (cancellazione) | EUR ~15 | Presso Transportstyrelsen |
| Exportregistreringsbevis | EUR ~30 | Certificato export |
| Ferry Goteborg-Kiel (auto+conducente) | EUR 120 | Se drive-it-home |
| Trasporto bisarca via ferry | Incluso nel prezzo bisarca | |

**ATTENZIONE SE:** Le auto svedesi ante-2020 possono avere il contachilometri in "mil" svedesi (1 mil = 10 km). Verificare SEMPRE.

---

## 4. TRIP CALCULATOR / STRUMENTI ESISTENTI NEL PROGETTO

### 4A. Transport Estimator (`tools/transport_estimator.py`)

**Stato:** FUNZIONANTE, con dati per 19 paesi EU e 5 citta' IT target.

| Caratteristica | Valore |
|----------------|--------|
| Paesi coperti | 19 (DE, NL, BE, AT, FR, SE, DK, NO, FI, PL, CZ, RO, PT, EE, LV, LT, BG, HR, SI, SK, HU) |
| Citta' IT target | Eboli, Salerno, Napoli, Roma, Milano |
| Metodi trasporto | Bisarca (EUR 0.45/km), Carrello (EUR 0.55/km), Drive (EUR 0.22/km) |
| Include vignette | SI (AT, CH, SI, CZ) |
| Include ferry | SI (FI, SE) |
| Logica raccomandazione | Veicolo > EUR 40k = bisarca, distanza > 2000 km = bisarca, < 800 km = drive |

**Lacune identificate (da S84):**
- Mancano destinazioni Puglia (Foggia, Bari, Lecce, Taranto) -- CRITICO per target dealer Sud
- Mancano destinazioni Calabria (Cosenza, Reggio Calabria)
- Non calcola costi volo per drive-it-home
- Non calcola pedaggi italiani specifici
- Vignetta AT a EUR 11 (dovrebbe essere EUR 12.40 nel 2026)

### 4B. Fee Calculator (`tools/fee_calculator.py`)

**Stato:** FUNZIONANTE, con 3 tier di servizio.

| Tier | Nome | Fee Default | Include |
|------|------|-------------|---------|
| 1 | Scouting Only | EUR 800 | Scheda ARGOS, VIN check, contatto venditore |
| 2 | Import Basic | EUR 1.000 | Tutto Tier 1 + perizia videocall + supporto documentale |
| 3 | Import Premium | EUR 1.500 | Tutto Tier 2 + ispezione on-site + gestione trasporto + chiavi in mano |

**Nota critica:** Il Tier 3 a EUR 1.500 non e' sostenibile come Scenario A (solo scouting). Il Tier 3 presuppone Scenario B/C dove ARGOS gestisce trasporto e pratiche. Per il lancio, solo Tier 1 (EUR 800-1.000) e' realistico.

### 4C. Import Checklist (`tools/import_checklist.py`)

**Stato:** FUNZIONANTE, completo per tutti i 19 paesi. Genera checklist personalizzata per paese con:
- Documenti necessari per export (specifici per paese)
- Procedura IVA (reverse charge B2B vs regime margine)
- Trasporto (targhe export, assicurazione)
- Immatricolazione IT (Motorizzazione, PRA, IPT)
- Warning specifici (rischio frode odometro per RO/BG/LV/LT/HU/PL, taxi/noleggio per HR/SI, contachilometri mil per SE)

### 4D. Materiali Esistenti

| File | Stato | Uso |
|------|-------|-----|
| `tools/materiali/contratto_incarico_scouting.html` | COMPLETO, professionale | Contratto Scenario A (Art. 1-9, success fee, limitazione responsabilita') |
| `tools/materiali/ricevuta_prestazione_occasionale.html` | ESISTENTE | Per prestazioni < EUR 5.000/anno |
| `tools/materiali/calcolatore_margine_import.html` | ESISTENTE | Tool interattivo per dealer |
| `tools/materiali/import_eu_6_step.html` | ESISTENTE | Guida 6 step per dealer |
| `tools/materiali/5_obiezioni_5_risposte.html` | ESISTENTE | Gestione obiezioni dealer |

**Verdetto strumenti:** Il progetto ha GIA' gli strumenti necessari per il lancio con Scenario A. Non mancano componenti critici. Servono solo aggiornamenti minori (destinazioni Puglia nel transport estimator, vignetta AT aggiornata).

---

## 5. MARKUP E REVENUE MODEL

### 5A. Scenario A -- Solo Scouting (Revenue Minima)

| Voce | Importo | Note |
|------|---------|------|
| Fee scouting | EUR 800-1.200 | Unica fonte di revenue |
| **Revenue per operazione** | **EUR 800-1.200** | |
| Costo operativo ARGOS | ~EUR 0 (strumenti gratuiti, LLM free tier) | |
| **Margine netto ARGOS** | **EUR 800-1.200** | ~100% margine |

### 5B. Scenario C -- Scouting + Coordinamento (Revenue Media)

| Voce | Importo | Note |
|------|---------|------|
| Fee scouting + coordinamento | EUR 1.000-1.200 | Fee base piu' alta per servizio esteso |
| Markup trasporto | EUR 100-200 | Trasporto costa EUR 700-900, ARGOS addebita EUR 900-1.000 |
| Markup agenzia pratiche | EUR 50-100 | Agenzia costa EUR 150-250, ARGOS addebita EUR 250-300 |
| **Revenue per operazione** | **EUR 1.150-1.500** | |

**E' giusto il markup?**

Il markup sui servizi coordinati e' giustificato se ARGOS:
1. Ha negoziato tariffe migliori con trasportatori (volume discount)
2. Ha verificato l'affidabilita' del trasportatore/agenzia
3. Ha gestito la comunicazione e risolto problemi
4. Ha risparmiato TEMPO al dealer (il dealer non deve cercare trasportatore)

Un markup del 15-20% sui servizi coordinati e' standard nel settore (benchmark: agenzie viaggi business 10-20%, property management 8-12%). EUR 100-200 su un trasporto da EUR 800 = 12-25% markup. Accettabile.

### 5C. Confronto Revenue con Competitor

| Servizio | Revenue per operazione | Modello |
|----------|----------------------|---------|
| ARGOS Scenario A | EUR 800-1.200 | Success fee |
| ARGOS Scenario C | EUR 1.150-1.500 | Success fee + markup servizi |
| Bolidem (ritiro) | EUR 1.269-1.419 | Fee upfront (il cliente rischia di piu') |
| Bolidem (bisarca) | EUR 2.109-2.259 | Fee upfront |
| Importami (su EUR 35k) | EUR 1.708 | 4% + IVA |
| eCarsTrade | EUR 350 + commissioni asta | Per transazione |

**Analisi:** ARGOS con Scenario A ha revenue comparabile a Bolidem ritiro, ma con il vantaggio del success fee. Il dealer non rischia nulla. Se ARGOS evolve a Scenario C, la revenue si avvicina a Bolidem bisarca ma resta inferiore -- il che va bene perche' ARGOS e' B2B (volume) vs Bolidem B2C (one-shot).

### 5D. Proiezione Revenue Mensile

| Fase | Operazioni/mese | Fee media | Revenue mensile | Revenue annua |
|------|----------------|-----------|----------------|---------------|
| Lancio (mesi 1-3) | 1-2 | EUR 900 | EUR 900-1.800 | ~EUR 15.000 |
| Crescita (mesi 4-6) | 3-5 | EUR 1.000 | EUR 3.000-5.000 | ~EUR 48.000 |
| Trazione (mesi 7-12) | 5-10 | EUR 1.000 | EUR 5.000-10.000 | ~EUR 90.000 |
| Scala (anno 2) | 10-20 | EUR 1.000 | EUR 10.000-20.000 | ~EUR 180.000 |

**Nota:** Queste sono proiezioni, NON previsioni. La fase di lancio e' la piu' critica: se i primi 3-5 dealer non convertono, il modello va rivisto.

---

## 6. PROTEZIONE DELLA FEE -- COME EVITARE IL BYPASS

### 6A. Il Rischio

Il dealer riceve il dossier ARGOS con:
- Marca/modello/anno/km/prezzo
- Link all'annuncio o nome venditore
- Contatto diretto del venditore

Senza protezione, il dealer puo':
1. Contattare il venditore direttamente
2. Acquistare senza informare ARGOS
3. Non pagare la fee

### 6B. Strategie di Protezione (dalla piu' efficace alla meno)

#### 1. CONTRATTO CON CLAUSOLA PENALE (efficacia: ALTA)

Il contratto di incarico scouting (GIA' ESISTENTE nel progetto) include:

- **Art. 4:** "Il compenso e' dovuto per ogni veicolo effettivamente acquistato a seguito della segnalazione dell'Incaricato"
- **Art. 8:** "I dati forniti nel dossier sono confidenziali e destinati esclusivamente al Committente"

**Da aggiungere al contratto:**

```
Art. 10 — Clausola di Esclusiva e Penale

10.1 Il Committente si impegna a non contattare autonomamente i venditori
     segnalati dall'Incaricato nel dossier, ne' a concludere l'acquisto
     del veicolo segnalato senza corrispondere il compenso pattuito.

10.2 In caso di violazione dell'Art. 10.1, il Committente riconoscera'
     all'Incaricato, a titolo di penale, un importo pari a [EUR 2.000 /
     doppio del compenso pattuito], salvo il diritto al risarcimento
     del maggior danno.

10.3 L'obbligo di cui all'Art. 10.1 permane per [90 / 180] giorni dalla
     data di consegna del dossier, anche in caso di recesso dal presente
     incarico.
```

**Base legale:** Art. 1382 c.c. (clausola penale). La penale e' legittima e non richiede prova del danno. Deve essere proporzionata (la Cassazione puo' ridurla se eccessiva -- benchmark immobiliare: 50-100% della provvigione).

**Confidenza:** HIGH -- la clausola penale e' standard nel settore immobiliare e applicabile per analogia.

#### 2. MODELLO "NO REVEAL UNTIL COMMITMENT" (efficacia: MEDIA-ALTA)

**Come funziona:**
1. Nel dossier iniziale, ARGOS mostra: marca, modello, anno, km, prezzo, foto, fraud check, stima margine
2. NON mostra: nome venditore, link annuncio, citta' esatta, contatto
3. Il dealer conferma interesse ("la voglio")
4. Solo DOPO la conferma scritta (anche via WA), ARGOS rivela i dati del venditore
5. La conferma scritta vale come accettazione dell'incarico e obbligo di fee

**Pro:** Il dealer non puo' bypassare perche' non ha le informazioni per farlo fino a che non si e' impegnato.
**Contro:** Il dealer potrebbe non fidarsi ("come faccio a sapere che l'auto esiste davvero?"). Soluzione: nel dossier mostrare foto reali, VIN parziale (primi 11 caratteri), citta' generica ("zona Monaco di Baviera").

#### 3. WATERMARK SUL DOSSIER (efficacia: BASSA)

Watermark con nome dealer + data sul PDF. Non impedisce il bypass ma crea tracciabilita'. Se il dealer condivide il dossier con un concorrente, il watermark identifica la fonte.

**Gia' implementato:** Il PDF generator (`tools/scripts/pdf_generator_enterprise.py`) genera dossier personalizzati per dealer. Aggiungere watermark e' semplice.

#### 4. TRACCIAMENTO ACQUISTO (efficacia: BASSA-MEDIA)

ARGOS monitora l'annuncio dopo aver inviato il dossier. Se l'annuncio sparisce (venduto) e il dealer non comunica l'acquisto, ARGOS contatta il dealer: "Ho notato che il veicolo X e' stato venduto. L'hai acquistato tu?"

**Pro:** Crea accountability passiva.
**Contro:** L'annuncio puo' sparire per altri motivi. Non e' prova di acquisto.

### 6C. RACCOMANDAZIONE PROTEZIONE FEE

**Per il lancio:**
1. Contratto di incarico scouting firmato PRIMA dell'invio del primo dossier
2. Modello "no reveal" per i primi 2-3 dossier (finche' si costruisce fiducia)
3. Dopo 2-3 operazioni riuscite: rivelare tutto nel dossier (la fiducia e' il miglior lock-in)

**La realta' del Sud Italia:** Un dealer del Sud che bypassa un fornitore e' un dealer che si brucia la reputazione. Nel tessuto micro-imprenditoriale del Sud, la reputazione e' piu' potente di qualsiasi contratto. Il rischio di bypass e' reale ma contenuto dalla dinamica sociale.

---

## 7. ASPETTI FISCALI E LEGALI ARGOS

### 7A. Regime Fiscale ARGOS

**Fonte:** [fidocommercialista.it](https://fidocommercialista.it/partita-iva-per-procacciatore-daffari), [fiscozen.it](https://www.fiscozen.it/guide/partita-iva-procacciatore-daffari/) | Confidenza: HIGH

| Opzione | Limiti | Tassazione | Adempimenti | Per ARGOS |
|---------|--------|------------|-------------|-----------|
| Prestazione occasionale | < EUR 5.000/anno, non abituale | Ritenuta 20% dal committente + bollo EUR 2 se > EUR 77.47 | Solo ricevuta (NO fattura, NO P.IVA) | Lancio (prime 3-5 operazioni) |
| P.IVA forfettaria | < EUR 85.000/anno fatturato | 5% primi 5 anni, poi 15% (su 62% del fatturato) | Fattura, registri, dichiarazione | Crescita (da 6+ operazioni) |
| P.IVA ordinaria | Nessun limite | IRPEF 23-43% scaglioni | Fattura, IVA, registri, dichiarazione | Scala |

**ATECO consigliato:** 46.18.41 -- "Procacciatori d'affari di vari prodotti senza prevalenza di alcuno" (dal 2025 unificato con agenti commerciali). Coefficiente redditivita' forfettaria: 62%.

**Calcolo tasse su EUR 1.000 di fee con forfettario 5%:**
- Base imponibile: EUR 1.000 x 62% = EUR 620
- Imposta: EUR 620 x 5% = EUR 31
- INPS Gestione Commercianti: ~EUR 250/trimestre fisso + % su reddito
- **Netto incassato:** ~EUR 920 su EUR 1.000 (nei primi 5 anni, escludendo INPS fisso)

**ATTENZIONE:** L'iscrizione INPS Gestione Commercianti comporta un contributo fisso minimo di ~EUR 1.000/anno anche con fatturato zero. Questo e' un costo fisso da considerare nel break-even.

### 7B. Prestazione Occasionale -- Dettaglio per il Lancio

Per le prime 3-5 operazioni (< EUR 5.000/anno), ARGOS puo' operare con ricevuta per prestazione occasionale.

**Requisiti:**
- Attivita' NON abituale e NON professionale
- Reddito annuo da prestazioni occasionali < EUR 5.000
- Non serve P.IVA
- Ritenuta d'acconto 20% applicata dal committente (dealer)
- Il dealer versa la ritenuta all'Erario
- Marca da bollo EUR 2 su ricevute > EUR 77.47

**Il contratto di incarico scouting gia' esistente cita "prestazione di servizi informativi" -- compatibile con prestazione occasionale.**

**Limite:** A EUR 1.000/fee, 5 operazioni = EUR 5.000 = limite raggiunto. Dalla sesta operazione serve P.IVA.

---

## 8. SINTESI OPERATIVA -- IL SERVIZIO ARGOS DEFINITO

### Modello di Servizio Definitivo (Lancio)

**Nome:** Scouting e Segnalazione Veicolo (NON "importazione", NON "mandato di acquisto")
**Natura giuridica:** Procacciamento d'affari / segnalazione (art. 1742 c.c. e seguenti)
**Regime fiscale:** Prestazione occasionale (lancio) --> P.IVA forfettaria (crescita)

**Cosa ARGOS fa:**
1. Ricerca veicoli premium su 28+ portali EU
2. Analisi CoVe (prezzo, fraud check, storico, scoring)
3. Produzione dossier professionale con stima margine dealer
4. Fornitura contatto diretto venditore EU
5. (Opzionale, Scenario C) Negoziazione e coordinamento

**Cosa ARGOS NON fa:**
- NON acquista il veicolo
- NON tocca i soldi della transazione
- NON trasporta il veicolo
- NON gestisce la burocrazia di immatricolazione
- NON garantisce il veicolo

**Fee:** EUR 800-1.200 success fee, pagabile entro 15 gg dall'acquisto effettivo.

**Protezione fee:**
- Contratto di incarico firmato prima del primo dossier
- Clausola penale (EUR 2.000 o doppio della fee)
- No-reveal dei dati venditore fino a conferma interesse
- Riservatezza dati dossier (Art. 8 contratto esistente)

---

## 9. COSTI TOTALI PER OPERAZIONE -- IL PROSPETTO DEALER

### Esempio: BMW X3 xDrive20d 2022, 70.000 km, da Germania

| Voce | Min | Max | Chi paga | A chi |
|------|-----|-----|----------|-------|
| Prezzo veicolo (DE) | EUR 32.000 | EUR 35.000 | Dealer | Venditore DE |
| Trasporto bisarca DE --> Sud IT | EUR 650 | EUR 1.000 | Dealer | Trasportatore |
| COC (se necessario) | EUR 0 | EUR 179 | Dealer | EUROCOC / costruttore |
| Traduzione giurata | EUR 100 | EUR 180 | Dealer | Traduttore |
| Costi fissi immatricolazione | EUR 111 | EUR 111 | Dealer | ACI / Motorizzazione |
| IPT (140 kW, con maggiorazione) | EUR 456 | EUR 594 | Dealer | Provincia |
| Agenzia pratiche (opzionale) | EUR 80 | EUR 250 | Dealer | Agenzia |
| **Fee ARGOS** | **EUR 800** | **EUR 1.200** | **Dealer** | **ARGOS** |
| **TOTALE COSTO DEALER** | **EUR 34.197** | **EUR 38.514** | | |

| Voce | Importo |
|------|---------|
| Prezzo vendita IT (stima) | EUR 38.500 - EUR 40.900 |
| Costo totale dealer (media) | EUR 36.355 |
| **Margine netto dealer** | **EUR 2.145 - EUR 4.545** |
| Margine/ora dealer (2.5 ore lavoro) | **EUR 858 - EUR 1.818/ora** |

---

## 10. FONTI E CONFIDENZA

| Area | Confidenza | Fonti principali |
|------|-----------|------------------|
| Modello Bolidem | HIGH | [bolidem.it/servizi](https://www.bolidem.it/servizi/), web scraping diretto |
| Modello Importami | HIGH | [importami.com/en/how-it-works](https://www.importami.com/en/how-it-works/) |
| Modello eCarsTrade | HIGH | [ecarstrade.com/howitworks](https://ecarstrade.com/howitworks) |
| Costi export DE | HIGH | S84 ricerca interna + [newsauto.it](https://www.newsauto.it/guide/importare-auto-germania-guida-privati-2025-588780/) |
| Costi export NL (BPM) | HIGH | [belastingdienst.nl](https://www.belastingdienst.nl/wps/wcm/connect/bldcontenten/belastingdienst/individuals/cars/bpm/refund_of_bpm/refund_if_the_vehicle_is_exported) |
| Costi export AT (NoVA) | MEDIUM-HIGH | [nagler.at](https://www.nagler.at/en/news/nova-refund-when-transferring-a-vehicle-abroad/) |
| Costi export BE (DIV) | MEDIUM | [mobilit.belgium.be](https://mobilit.belgium.be/en/road/registration-and-deregistration/export-vehicle-transit) |
| Costi export FR | LOW-MEDIUM | Training data, non verificato 2026 |
| Costi export SE | LOW-MEDIUM | Training data + dati interni |
| Costi immatricolazione IT | HIGH | S99 ricerca interna + [alvolante.it](https://www.alvolante.it/da_sapere/legge-e-burocrazia/importare-un-auto-dall-estero-costi-tempi-e-tasse-381577) |
| Margini reali DE vs IT | HIGH | S99 ricerca interna + AutoScout24 |
| Regime fiscale procacciatore | HIGH | [fidocommercialista.it](https://fidocommercialista.it/partita-iva-per-procacciatore-daffari), [fiscozen.it](https://www.fiscozen.it/guide/partita-iva-procacciatore-daffari/) |
| Clausola penale (art. 1382 c.c.) | HIGH | [brocardi.it](https://www.brocardi.it/codice-civile/libro-quarto/titolo-iii/capo-x/art1743.html) |
| Protezione fee / no-reveal | MEDIUM | Prassi settore immobiliare, analogia |
| Proiezioni revenue | LOW | Stime, non basate su dati reali ARGOS |
| Strumenti esistenti nel progetto | HIGH | Lettura diretta del codice |

---

## 11. GAP E AZIONI NECESSARIE

### Da fare PRIMA del lancio:

| Azione | Priorita' | Stato |
|--------|-----------|-------|
| Aggiungere Art. 10 (clausola penale) al contratto scouting | ALTA | DA FARE |
| Aggiungere destinazioni Puglia/Calabria a transport_estimator.py | MEDIA | DA FARE |
| Aggiornare vignetta AT a EUR 12.40 | BASSA | DA FARE |
| Decidere regime fiscale (occasionale vs P.IVA) | ALTA | DA DECIDERE col commercialista |
| Verificare se il Tier 3 del fee_calculator e' realistico | MEDIA | Probabilmente NO per il lancio |

### Da fare DOPO le prime 5 operazioni:

| Azione | Trigger |
|--------|---------|
| Apertura P.IVA forfettaria | Superamento EUR 5.000 fatturato |
| Accordi volume con trasportatori | 3+ trasporti/mese dalla stessa rotta |
| Evoluzione a Scenario C (coordinamento) | Dealer richiedono servizio piu' completo |
| Valutazione Scenario B (chiavi in mano) | 20+ operazioni, SRL, compliance fiscale |

---

**Fine documento -- ARGOS Servizio Definizione v1.0**
