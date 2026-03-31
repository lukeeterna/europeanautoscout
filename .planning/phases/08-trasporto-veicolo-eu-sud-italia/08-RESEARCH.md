# Phase 8: Trasporto Singolo Veicolo EU -> Sud Italia - Research

**Researched:** 2026-03-31
**Domain:** Logistica trasporto auto singola EU->IT, costi reali, burocrazia import
**Confidence:** MEDIUM-HIGH (dati incrociati da multiple fonti, preventivi reali marketplace)

## Summary

Il trasporto di un singolo veicolo premium (BMW X3, Audi Q5, Mercedes GLC, Porsche Macan) dalla Germania/Olanda/Belgio/Austria/Francia al Sud Italia ha 3 opzioni principali: fly & drive (EUR 250-500), bisarca condivisa (EUR 500-1.500), trasporto dedicato (EUR 800-3.000). Per il target ARGOS (dealer piccolo, 1 auto alla volta, veicoli EUR 20k-50k), il fly & drive e' quasi sempre la scelta piu' economica ma richiede 1-2 giorni di viaggio. La bisarca condivisa e' il compromesso costo/comodita' per chi non vuole guidare 12-18 ore.

ARGOS gia' dispone di un `transport_estimator.py` con tabelle distanze e costi calibrate. Questa ricerca valida e arricchisce quei dati con preventivi reali 2025-2026 e aggiunge la componente burocrazia (targhe, assicurazione, nazionalizzazione) che mancava.

**Primary recommendation:** Nel dossier dealer includere SEMPRE stima trasporto con 2 opzioni (fly & drive + bisarca), calcolata automaticamente dal transport_estimator.py. NON offrire trasporto come servizio ARGOS — indicare i marketplace (Macingo, Clicktrans) e la stima costo. Il dealer decide.

---

## Opzione 1: Fly & Drive (Ritiro Personale)

### Costi Volo Low-Cost (solo andata, prezzo medio 2025-2026)

| Rotta | Compagnie | Prezzo medio | Range |
|-------|-----------|-------------|-------|
| Napoli -> Monaco di Baviera | EasyJet, Lufthansa, Air Dolomiti | EUR 60-90 | EUR 30-180 |
| Napoli -> Francoforte | EasyJet, Ryanair, Lufthansa | EUR 50-80 | EUR 30-160 |
| Bari -> Monaco di Baviera | Ryanair, Lufthansa | EUR 50-80 | EUR 25-150 |
| Bari -> Francoforte | Ryanair | EUR 45-70 | EUR 25-130 |
| Catania -> Monaco di Baviera | EasyJet | EUR 55-90 | EUR 30-160 |
| Napoli -> Amsterdam | EasyJet, Transavia | EUR 60-100 | EUR 35-200 |
| Napoli -> Bruxelles | Ryanair, Brussels Airlines | EUR 40-70 | EUR 25-150 |
| Napoli -> Vienna | Ryanair, Wizz Air | EUR 40-70 | EUR 20-130 |
| Napoli -> Parigi (Beauvais/CDG) | Ryanair, EasyJet | EUR 40-80 | EUR 20-150 |

**Note:** Prenotando 2-3 settimane prima, voli low-cost EUR 30-60 sono realistici. Last minute sale a EUR 100-200. Solo bagaglio a mano (si va a ritirare un'auto, non serve valigia).

### Tempo di Guida (rotte principali verso Sud Italia)

| Rotta | Distanza km | Ore guida | Giorni realistici |
|-------|------------|-----------|-------------------|
| Monaco -> Napoli (via Brennero) | 1.280 | 12-13h | 1.5 giorni |
| Monaco -> Salerno/Eboli | 1.250 | 12h | 1.5 giorni |
| Monaco -> Bari | 1.400 | 14h | 1.5-2 giorni |
| Monaco -> Cosenza/Rende | 1.500 | 15h | 2 giorni |
| Francoforte -> Napoli | 1.580 | 15h | 2 giorni |
| Francoforte -> Bari | 1.700 | 16h | 2 giorni |
| Amsterdam -> Napoli | 1.930 | 19h | 2 giorni |
| Amsterdam -> Bari | 2.050 | 20h | 2-2.5 giorni |
| Bruxelles -> Napoli | 1.780 | 17h | 2 giorni |
| Vienna -> Napoli | 1.330 | 13h | 1.5 giorni |
| Parigi -> Napoli | 1.730 | 17h | 2 giorni |
| Stoccolma -> Napoli | 2.830 | 28h | 3 giorni |

**Nota reale:** Un guidatore solo fa massimo 8-10h/giorno con soste. Monaco->Napoli = partenza mattina, sosta notturna Bologna/Firenze, arrivo giorno dopo pranzo.

### Costi Carburante (diesel, veicolo tipo BMW X3 xDrive20d)

| Parametro | Valore |
|-----------|--------|
| Consumo medio autostradale BMW X3 diesel | 7.0 L/100km (fonte: Motor1 test 2025) |
| Prezzo diesel Germania (2025-2026) | EUR 1.55-1.65/L |
| Prezzo diesel Austria | EUR 1.50-1.60/L |
| Prezzo diesel Italia autostrada | EUR 1.70-1.80/L (self) |
| Prezzo diesel Francia | EUR 1.65-1.75/L |
| Prezzo diesel Olanda | EUR 1.70-1.85/L |
| **Media ponderata percorso misto** | **EUR 1.65/L** |

**Calcolo carburante per rotta tipo:**

| Rotta | km | Litri (7L/100km) | Costo carburante |
|-------|-----|-------------------|------------------|
| Monaco -> Eboli | 1.250 | 87.5 L | EUR 144 |
| Monaco -> Bari | 1.400 | 98 L | EUR 162 |
| Francoforte -> Napoli | 1.580 | 111 L | EUR 183 |
| Amsterdam -> Napoli | 1.930 | 135 L | EUR 223 |
| Amsterdam -> Bari | 2.050 | 143 L | EUR 237 |

### Pedaggi e Vignette

| Voce | Costo | Note |
|------|-------|------|
| **Vignetta Austria 10 giorni** | EUR 12.40 | Obbligatoria rotta Brennero. Digitale su shop.asfinag.at |
| **Vignetta Svizzera annuale** | CHF 40 (EUR 42) | Solo se rotta via CH (da evitare: Austria e' piu' economica) |
| **Vignetta Slovenia 7 giorni** | EUR 16 | Solo rotta via Ljubljana |
| **Vignetta Rep. Ceca 10 giorni** | EUR 16 | Solo rotta da PL/CZ |
| **Pedaggio Brennero (AT-IT)** | EUR 10.50 | Europabrucke (tratta speciale) |
| **Pedaggi autostrada Italia** | EUR 45-75 | Brennero->Napoli ~EUR 65, Brennero->Bari ~EUR 70 |
| **Pedaggi autostrada Francia** | EUR 40-80 | Se rotta da FR (Parigi->tunnel Frejus) |
| **Tunnel Frejus (FR-IT)** | EUR 53 (andata, auto) | Alternativa al Brennero per rotte da FR |
| **Autostrada Germania** | EUR 0 | Gratuita (nessun pedaggio auto) |
| **Autostrada Olanda** | EUR 0 | Gratuita |
| **Autostrada Belgio** | EUR 0 | Gratuita |

### Costo TOTALE Fly & Drive per Rotta (stima realistica)

| Rotta | Volo | Carburante | Pedaggi+Vignette | Sosta notte | TOTALE |
|-------|------|------------|------------------|-------------|--------|
| **Monaco -> Eboli/Salerno** | 70 | 144 | 88 | 60 | **EUR 362** |
| **Monaco -> Bari** | 70 | 162 | 93 | 60 | **EUR 385** |
| **Monaco -> Rende (CS)** | 70 | 166 | 95 | 60 | **EUR 391** |
| **Francoforte -> Napoli** | 60 | 183 | 88 | 80 | **EUR 411** |
| **Amsterdam -> Eboli** | 80 | 223 | 88 | 80 | **EUR 471** |
| **Amsterdam -> Bari** | 80 | 237 | 93 | 80 | **EUR 490** |
| **Bruxelles -> Napoli** | 55 | 207 | 88 | 80 | **EUR 430** |
| **Vienna -> Salerno** | 55 | 155 | 78 | 60 | **EUR 348** |
| **Parigi -> Napoli (via Frejus)** | 60 | 200 | 120 | 80 | **EUR 460** |
| **Stoccolma -> Napoli** | 100 | 330 | 100 | 160 | **EUR 690** |

**Nota:** Sosta notte = motel autostradale (EUR 50-80). Se si guida senza sosta (non raccomandato per >10h) si risparmia EUR 60-80.

### Pro/Contro Fly & Drive

| Pro | Contro |
|-----|--------|
| Costo piu' basso (EUR 350-500) | 1-2 giorni di tempo persona |
| Controllo diretto del veicolo | Fatica guida lunga (12-19h) |
| Verifica veicolo di persona prima del ritiro | Serve targa esportazione + assicurazione |
| Nessuna attesa (partenza immediata) | Rischio incidenti/danni durante trasferimento |
| Possibilita' di ispezionare dal vivo | Km extra sul veicolo (1.200-2.000 km) |

---

## Opzione 2: Bisarca Condivisa (Trasporto Professionale)

### Piattaforme Marketplace Principali

| Piattaforma | Modello | Copertura | Note |
|-------------|---------|-----------|------|
| **Macingo.com** | Asta/preventivi da trasportatori certificati | IT + EU | Principale in Italia, ottimo per DE->IT |
| **Clicktrans.it** | Asta — trasportatori competono sul prezzo | EU (forte PL/DE/IT) | Prezzi competitivi, molti trasportatori Est Europa |
| **Shiply.com** | Asta internazionale | UK + EU | Buono per NL/BE/FR->IT |
| **Spedingo.com** | Preventivi multipli | IT + EU | Alternativa a Macingo |
| **GO Trasporti** | Servizio diretto | IT + DE->IT | Trasporto dedicato, piu' costoso |

### Prezzi Reali Bisarca Condivisa (preventivi completati 2025-2026)

**Fonte:** Preventivi chiusi su Macingo, Clicktrans, dati aggregati da fonti multiple.

| Rotta | Distanza km | Prezzo bisarca condivisa | Tempi consegna |
|-------|------------|--------------------------|----------------|
| **Monaco -> Roma** | 1.050 | EUR 500-700 | 5-8 giorni |
| **Burgau (Baviera) -> Roma** | 1.004 | EUR 559 (prezzo reale chiuso) | 7 giorni |
| **Soverato (CS) -> Tubinga (DE)** | 1.658 | EUR 560 (prezzo reale chiuso) | 8 giorni |
| **Monaco -> Napoli** | 1.280 | EUR 600-850 | 7-10 giorni |
| **Monaco -> Salerno/Eboli** | 1.250 | EUR 600-800 | 7-10 giorni |
| **Monaco -> Bari** | 1.400 | EUR 650-900 | 7-12 giorni |
| **Monaco -> Cosenza** | 1.500 | EUR 700-950 | 8-12 giorni |
| **Francoforte -> Napoli** | 1.580 | EUR 700-1.000 | 7-12 giorni |
| **Amsterdam -> Napoli** | 1.930 | EUR 800-1.200 | 10-15 giorni |
| **Amsterdam -> Bari** | 2.050 | EUR 850-1.300 | 10-15 giorni |
| **Parigi -> Napoli** | 1.730 | EUR 750-1.100 | 8-12 giorni |
| **Stoccolma -> Napoli** | 2.830 | EUR 1.200-1.800 | 15-20 giorni |

**Costo medio al km (dati Clicktrans 2025):** EUR 0.40-0.55/km per tratte internazionali

### Prezzi Trasporto Dedicato (carrello/bisarca singola)

| Rotta | Prezzo dedicato | Tempi | Note |
|-------|----------------|-------|------|
| **Monaco -> Sud Italia** | EUR 1.200-1.800 | 3-5 giorni | Furgone con carrello singolo |
| **Francoforte -> Sud Italia** | EUR 1.400-2.000 | 3-5 giorni | |
| **Amsterdam -> Sud Italia** | EUR 1.600-2.500 | 4-6 giorni | |

**Regola pratica:** Il trasporto dedicato costa 2-2.5x la bisarca condivisa.

### Assicurazione Durante Trasporto

| Tipo | Copertura | Inclusa? |
|------|-----------|----------|
| Bisarca professionale | RC + danni durante carico/scarico | SI, inclusa nel prezzo |
| Trasportatore Macingo/Clicktrans | RC trasportatore (verificare polizza) | SI, ma controllare massimale |
| Fly & drive | RC targa esportazione | Solo RC, NO kasko |

### Pro/Contro Bisarca

| Pro | Contro |
|-----|--------|
| Zero fatica — l'auto arriva a destinazione | EUR 600-1.200 (2-3x fly & drive) |
| Zero km aggiuntivi sul veicolo | 7-15 giorni di attesa |
| Assicurazione professionale inclusa | Non si ispeziona il veicolo di persona |
| Il dealer non perde giornate lavorative | Possibili ritardi (meteo, carico pieno) |
| Ideale per auto premium >EUR 40k | Meno controllo sulla tempistica |

---

## Opzione 3: Servizi Door-to-Door Specializzati

### Servizi Esistenti

| Servizio | Cosa fa | Prezzo indicativo | Note |
|----------|---------|-------------------|------|
| **GO Trasporti** | Bisarca dedicata/condivisa DE->IT | EUR 800-1.500 | Servizio italiano, preventivo su misura |
| **Gerace Trasporti** | Bisarca Italia + EU, da EUR 120 (IT) | EUR 600-1.200 (EU->IT) | Forte su tratte nazionali |
| **SpediamoAuto.it** | Aggregatore preventivi | EUR 500-1.500 | Comparazione trasportatori |
| **Michael Auto Germania** | Import completo DE->IT (incluso trasporto) | Incluso nel servizio | Mandatario che importa auto dalla DE |
| **Trasportami.com** | Bisarca internazionale | EUR 600-1.500 | Focus Germania-Italia |

**Non esistono servizi "Amazon-style" con prezzo fisso e tracking.** Il mercato e' frammentato: si chiede preventivo su marketplace, si confrontano offerte, si sceglie.

---

## Tempistiche Realistiche

| Metodo | Tempo totale | Per chi ha fretta? | Per chi vuole risparmiare? |
|--------|--------------|--------------------|---------------------------|
| **Fly & drive** | 1-2 giorni | SI (la piu' veloce) | SI (EUR 350-500) |
| **Bisarca condivisa** | 7-15 giorni | NO | MEDIO (EUR 600-1.200) |
| **Trasporto dedicato** | 3-5 giorni | SI (ma costoso) | NO (EUR 1.200-2.500) |

**Per "il cliente ha fretta":** Fly & drive. Volo il giorno dopo, ritiro, guida, 2 giorni max l'auto e' dal dealer.

**Per il dealer standard:** Bisarca condivisa. 7-10 giorni, l'auto arriva, zero fatica. E' il metodo piu' usato dai piccoli importatori.

---

## Burocrazia e Costi Nascosti

### Targa Esportazione Tedesca (Ausfuhrkennzeichen)

| Voce | Dettaglio | Costo |
|------|-----------|-------|
| Rilascio targa esportazione | Targa rossa con data scadenza | EUR 30-50 (costo amministrativo) |
| Assicurazione RC inclusa | Obbligatoria, copre validita' targa | EUR 80-150 (15-45 giorni) |
| Validita' | 15-45 giorni (scelta al rilascio) | |
| **Totale targa + assicurazione** | | **EUR 120-200** |
| **Alternativa: servizio targhe** | Stocker, Europrofex, dealer stesso | EUR 149 (pacchetto targa+assicurazione) |

**Chi la richiede?** Il venditore tedesco (Autohaus/Handler) la include quasi sempre nel prezzo di vendita o la gestisce come servizio. Se non la include, costa EUR 120-200 extra.

**Validita' in Italia:** Le targhe tedesche di esportazione sono valide in tutta l'UE. Il veicolo puo' circolare in Italia con targa Zoll per tutta la durata della targa (15-45 giorni). Dopo, va nazionalizzato.

### Assicurazione Temporanea per Guida su Targa Estera

| Scenario | Cosa serve | Costo |
|----------|------------|-------|
| Targa esportazione tedesca (Ausfuhrkennzeichen) | RC GIA' INCLUSA nella targa | EUR 0 (inclusa) |
| Targa normale estera (non export) | Polizza del paese d'origine valida in UE | EUR 0 (carta verde) |
| Veicolo senza assicurazione | Polizza temporanea di frontiera UCI | EUR 120 (15gg) - EUR 245 (90gg) |

**Caso ARGOS tipico:** Il veicolo ha targa esportazione tedesca con RC inclusa. Nessun costo aggiuntivo assicurazione.

### Dogana e IVA (Intra-UE)

| Voce | Dettaglio |
|------|-----------|
| **Dogana** | ZERO — intra-UE, nessuna formalita' doganale |
| **IVA veicolo "fiscalmente usato"** | ZERO al momento dell'import (>6 mesi E >6.000 km) — regime margine |
| **IVA veicolo "fiscalmente nuovo"** | 22% su F24 (se <6 mesi O <6.000 km) |
| **Intrastat** | Solo per operatori IVA (il dealer) — dichiarazione trimestrale/mensile |

**Caso ARGOS tipico:** Veicoli usati 2018-2023 con >6.000 km. Regime IVA margine. Il dealer acquista con IVA esposta dal venditore tedesco (se B2B) oppure in regime margine. La gestione IVA e' del commercialista del dealer — ARGOS non interviene.

### Nazionalizzazione (Immatricolazione Italiana)

| Voce | Costo | Note |
|------|-------|------|
| Diritti Motorizzazione | EUR ~100 | |
| Iscrizione PRA | EUR ~150 | |
| Targa italiana | EUR ~40 | |
| IPT (Imposta Provinciale Trascrizione) | EUR 150-400 | Varia per kW e provincia |
| Agenzia pratiche auto | EUR 100-200 | Se il dealer non lo fa internamente |
| **TOTALE nazionalizzazione** | **EUR 350-700** | Dipende da kW e provincia |
| **Tempi** | 15-45 giorni | Media 20-30 giorni |

**Documenti necessari dalla Germania:**
- Zulassungsbescheinigung Teil I (libretto circolazione)
- Zulassungsbescheinigung Teil II (certificato proprieta')
- COC (Certificate of Conformity) — SE disponibile, semplifica enormemente
- Fattura di acquisto

**Il dealer lo sa gia' fare.** I concessionari che importano auto hanno agenzie di pratiche auto di riferimento. ARGOS NON deve occuparsi di nazionalizzazione — ma deve indicare nel dossier i documenti che il venditore DEVE fornire (soprattutto il COC).

---

## Tabella Riepilogativa: Costo TOTALE per Rotta e Metodo

### Rotta: Monaco (DE) -> Campania/Salerno (dealer tipo)

| Voce | Fly & Drive | Bisarca Condivisa |
|------|------------|-------------------|
| Trasporto/viaggio | EUR 274 (volo+gasolio+pedaggi+notte) | EUR 600-800 |
| Targa esportazione | EUR 0 (inclusa dal venditore) | EUR 0 (non serve, su bisarca) |
| Assicurazione extra | EUR 0 | EUR 0 (inclusa) |
| **TOTALE trasporto** | **EUR 274-362** | **EUR 600-800** |
| Nazionalizzazione (a parte) | EUR 350-700 | EUR 350-700 |

### Rotta: Amsterdam (NL) -> Puglia/Bari

| Voce | Fly & Drive | Bisarca Condivisa |
|------|------------|-------------------|
| Trasporto/viaggio | EUR 400-490 | EUR 850-1.300 |
| **TOTALE trasporto** | **EUR 400-490** | **EUR 850-1.300** |

### Rotta: Vienna (AT) -> Campania

| Voce | Fly & Drive | Bisarca Condivisa |
|------|------------|-------------------|
| Trasporto/viaggio | EUR 280-348 | EUR 500-700 |
| **TOTALE trasporto** | **EUR 280-348** | **EUR 500-700** |

---

## Cosa Deve Offrire ARGOS nel Dossier

### Raccomandazione: Informare, NON Gestire

ARGOS **NON** deve offrire trasporto come servizio per questi motivi:
1. **Responsabilita' legale** — se l'auto si danneggia durante trasporto coordinato da ARGOS, il dealer tiene ARGOS responsabile
2. **Margine zero** — rivendere il servizio di un trasportatore senza markup non ha senso, con markup il dealer lo scopre e perde fiducia
3. **Il dealer sa gia' fare** — i concessionari che importano hanno gia' i loro trasportatori di fiducia
4. **Focus ARGOS** — il valore e' nel trovare l'auto giusta al prezzo giusto, non nella logistica

### Cosa Includere nel Dossier PDF

```
TRASPORTO STIMATO
Rotta: Monaco di Baviera -> Salerno (~1.250 km)

Opzione 1 — Ritiro personale (fly & drive):    ~EUR 350
  Volo low-cost Napoli->Monaco:   EUR 60-90
  Carburante diesel (7L/100km):   EUR 145
  Pedaggi + vignetta AT:          EUR 88
  Sosta notturna:                 EUR 60
  Tempo: 1.5 giorni

Opzione 2 — Bisarca condivisa:                 ~EUR 700
  Piattaforme: macingo.com, clicktrans.it
  Tempo: 7-10 giorni lavorativi
  Assicurazione trasporto inclusa

Nota: costi di nazionalizzazione (EUR 350-700) a carico acquirente.
```

### Aggiornamenti al transport_estimator.py

Il file `tools/transport_estimator.py` esistente e' GIA' ben calibrato. Validazione:

| Parametro estimator | Valore attuale | Dato ricerca | Allineato? |
|---------------------|---------------|--------------|------------|
| COST_PER_KM bisarca | EUR 0.45/km | EUR 0.40-0.55/km (Clicktrans) | SI |
| COST_PER_KM drive | EUR 0.22/km | EUR 0.20-0.25/km (calcolato) | SI |
| Vignetta AT | EUR 11 | EUR 12.40 (2025-2026) | AGGIORNARE a 12.40 |
| Vignetta CH | EUR 42 | CHF 40 = EUR 42 | SI |
| Vignetta SI | EUR 16 | EUR 16 | SI |
| Flat rate DE | EUR 700 | EUR 600-850 reali | SI (nella media) |
| Flat rate NL | EUR 800 | EUR 800-1.200 reali | SI (lower bound) |
| Flat rate SE | EUR 1.200 | EUR 1.200-1.800 reali | SI (lower bound) |

**Unica correzione necessaria:** Vignetta Austria da EUR 11 a EUR 12.40.

---

## Common Pitfalls

### Pitfall 1: Km Extra sul Veicolo (Fly & Drive)
**What goes wrong:** Il fly & drive aggiunge 1.200-2.000 km al veicolo. Su un'auto venduta come "km bassi", questo puo' essere un problema commerciale.
**How to avoid:** Segnalare nel dossier che i km del fly & drive vanno aggiunti. Se il punto vendita del dealer e' "km certificati", raccomandare bisarca.

### Pitfall 2: Attesa Bisarca Condivisa
**What goes wrong:** La bisarca condivisa parte quando e' piena. Se non ci sono altre auto sulla rotta, l'attesa puo' essere 2-3 settimane.
**How to avoid:** Usare Macingo/Clicktrans con "data flessibile" per ottenere prezzi migliori. Se serve velocita', fly & drive.

### Pitfall 3: COC Mancante
**What goes wrong:** Senza Certificate of Conformity, la nazionalizzazione richiede omologazione individuale alla Motorizzazione (costo EUR 500-1.000, tempi 30-60 giorni).
**How to avoid:** ARGOS deve SEMPRE verificare che il venditore fornisca il COC. Se non disponibile, segnalarlo nel dossier come rischio.

### Pitfall 4: Targa Esportazione Scaduta
**What goes wrong:** La targa Zoll ha validita' 15-45 giorni. Se il fly & drive ritarda (guasto, imprevisto), la targa scade e il veicolo non puo' circolare.
**How to avoid:** Richiedere targa con validita' minima 30 giorni. Costo marginale in piu'.

### Pitfall 5: Rotta via Svizzera
**What goes wrong:** Google Maps suggerisce spesso la rotta via CH per DE->IT. La vignetta svizzera costa EUR 42 ed e' solo annuale — spreco per un passaggio.
**How to avoid:** Rotta via Austria (Brennero). Vignetta 10 giorni EUR 12.40. Molto piu' economica.

---

## Validazione transport_estimator.py vs Dati Reali

### Confronto Stime vs Preventivi Reali

| Rotta | Stima estimator (bisarca) | Prezzo reale marketplace | Delta |
|-------|--------------------------|--------------------------|-------|
| DE (Monaco) -> Eboli | EUR 562 (1250*0.45) | EUR 600-800 | -7% a -30% (sottostima) |
| DE (Francoforte) -> Napoli | EUR 711 (1580*0.45) | EUR 700-1.000 | OK |
| NL (Amsterdam) -> Eboli | EUR 855 (1900*0.45) | EUR 800-1.200 | OK |
| DE (Baviera) -> Roma | EUR 472 (1050*0.45) | EUR 559 (prezzo reale chiuso) | -15% (sottostima) |

**Conclusione:** L'estimator sottostima leggermente (5-15%) i costi bisarca. Suggerimento: aggiungere un markup "minimum fee" di EUR 350 (molti trasportatori hanno un minimo anche per tratte brevi).

---

## Integrazione nel Dossier Dealer

### Sezione da Aggiungere al PDF Generator

Il `pdf_generator_enterprise.py` dovrebbe includere una sezione "Stima Trasporto" con:

1. **Rotta calcolata automaticamente** da `transport_estimator.py`
2. **Due opzioni** (fly & drive e bisarca) con costi
3. **Link ai marketplace** (Macingo, Clicktrans)
4. **Nota sui documenti necessari** (COC, Teil I, Teil II)
5. **NON includere costi nazionalizzazione** — il dealer li conosce gia'

### Linguaggio per il Dealer

Seguendo le regole CLAUDE.md sul linguaggio dealer Sud Italia:

```
DIRE: "Per portarla giu' spende circa 350 euro guidandola,
       oppure 700 euro con bisarca che gliela consegna in 7-10 giorni"

NON DIRE: "Il costo logistico stimato per il trasferimento intra-UE
           del veicolo ammonta a EUR 350-700"
```

---

## Open Questions

1. **Trasportatori di fiducia dei dealer target?**
   - I dealer TIER0 (Stile Car, Car Plus, Sa.My. Auto) probabilmente hanno gia' trasportatori preferiti
   - Chiedere al primo dealer contattato: "Per il trasporto ha gia' un suo riferimento?"

2. **Il dealer preferisce fly & drive o bisarca?**
   - Dipende dal dealer: il NARCISO manda un dipendente, il RAGIONIERE vuole bisarca economica
   - Da validare con i primi contatti reali

3. **Dealer con partita IVA estera?**
   - Alcuni dealer piccoli NON hanno registrazione VIES per acquisto intra-UE
   - Verificare con il dealer se puo' acquistare direttamente o serve intermediario

---

## Sources

### Primary (HIGH confidence)
- Preventivi reali chiusi su marketplace (Macingo, Clicktrans) — EUR 559 Baviera->Roma, EUR 560 Calabria->Germania
- ASFINAG shop (vignetta Austria 2025-2026: EUR 12.40 per 10 giorni) — shop.asfinag.at
- Motor1 test consumi BMW X3 xDrive20d 2025: 7.0 L/100km autostrada
- ACI.gov.it — procedura nazionalizzazione veicolo estero
- Car4passion.com — guida trasporto auto Germania-Italia (bisarca EUR 500-1.500)

### Secondary (MEDIUM confidence)
- Ryanair.com/EasyJet — prezzi voli Napoli-Monaco/Francoforte (EUR 30-90 prenotando in anticipo)
- Clicktrans.it — costo medio al km EUR 0.40-0.55 per tratte internazionali
- Sicurauto.it — IVA import auto usata regime margine, assicurazione targa estera
- Zulassung-stocker.de — targa esportazione tedesca EUR 149 pacchetto

### Tertiary (LOW confidence)
- Prezzi diesel Germania 2025 (EUR 1.55-1.65/L) — dati aggregati, variabilita' alta
- Tempi bisarca condivisa 7-15 giorni — media indicativa, variabilita' alta per rotta

## Metadata

**Confidence breakdown:**
- Costi fly & drive: HIGH — calcolati da dati verificabili (consumo, pedaggi, voli)
- Costi bisarca: MEDIUM-HIGH — preventivi reali ma range ampio
- Burocrazia/nazionalizzazione: HIGH — fonti istituzionali (ACI, Motorizzazione)
- Transport estimator validation: HIGH — confronto diretto con preventivi reali

**Research date:** 2026-03-31
**Valid until:** 2026-06-30 (costi trasporto stabili, vignette cambiano a gennaio)
