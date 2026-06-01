# S82 — Strumenti Gratuiti per Dati Veicoli EU
**Data**: 2026-03-24
**Obiettivo**: Censimento verificato di tutti gli strumenti gratuiti per ottenere dati su veicoli usati in Europa
**Metodo**: Web research live con verifica incrociata su pricing e funzionalita' reali

---

## SOMMARIO EXECUTIVE

| Categoria | Strumenti trovati | Davvero gratuiti | Usabili ARGOS |
|-----------|------------------|-----------------|---------------|
| VIN Decoder | 6 | 4 (con limiti) | 3 |
| Recall Check | 4 | 3 | 3 |
| Storico km / Frodi | 4 | 0-1 parziale | 1 parziale |
| Valutazione / Pricing | 4 | 2 parziali | 2 |
| Documenti importazione | 4 | 4 | 4 |
| Garanzia | 3 programmi | N/A | STRATEGICO |
| Emissioni / Tasse | 3 | 3 | 3 |

**VERDETTO GENERALE**: Gli strumenti davvero gratuiti coprono bene VIN decode, recall e tasse. Il gap critico rimane lo storico km (Car-Pass e NAP sono a pagamento) e la valutazione (Eurotax/DAT/Schwacke sono enterprise). Per ARGOS il valore e' nell'aggregazione dei nostri 22 scraper EU per i prezzi, non negli strumenti di terze parti.

---

## 1. VIN DECODER GRATUITI

### 1.1 vindecoder.eu (= Vincario sotto)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://vindecoder.eu |
| **Gratis?** | SI — 20 VIN decode di prova senza carta |
| **Dati restituiti** | Make, model, anno, body style, motore, trasmissione, carburante, emissioni, specifiche tecniche complete (50+ campi) |
| **Coverage** | EU + USA + internazionale |
| **Limite free** | 20 lookup totali (non rinnovabili) |
| **API?** | SI — stessi 20 lookup gratis, poi $50 per 200 ($0.25/VIN) |
| **Prezzi API** | 200 VIN=$50, 1.000 VIN=$200 |
| **Formato** | REST JSON |
| **ARGOS use** | Test VIN di veicoli sospetti — 20 gratis sufficienti per fase iniziale |

**Nota**: E' lo stesso backend di Vincario (gia' integrato in CoVe). I 3 report gratuiti Vincario e i 20 decode vindecoder.eu sono pool SEPARATI — si possono usare entrambi.

---

### 1.2 freevindecoder.eu

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.freevindecoder.eu |
| **Gratis?** | SI — completamente gratuito, no registrazione |
| **Dati restituiti** | Marca, modello, anno, tipo body, motorizzazione, data prima immatricolazione, tipo veicolo |
| **Coverage** | EU + internazionale |
| **Limite free** | Nessun limite dichiarato (no API key) |
| **API?** | NO — solo interfaccia web |
| **ARGOS use** | Verifica rapida manuale di un VIN sospetto. Zero costo, zero API |

---

### 1.3 CARFAX Europe — Free VIN Decoder

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.carfax.eu/free-vin-decoder |
| **Gratis?** | SI parziale — decoder base gratis, report completo a pagamento |
| **Dati gratuiti** | Make, model, anno, storico import da 20 paesi EU o Nord America |
| **Dati a pagamento** | Incidenti, storico revisioni, odometro, cambio proprieta' |
| **Coverage** | 20 paesi EU + USA |
| **ARGOS use** | UTILE: "import history from 20 EU countries" — capisce se l'auto e' passata per piu' paesi (segnale frode potenziale) |

---

### 1.4 vindecoderz.com

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.vindecoderz.com |
| **Gratis?** | PARZIALE — alcune info base gratis, report dettagliati a pagamento |
| **Dati gratuiti** | Specifiche tecniche base (make, model, anno, body) |
| **API** | SI — pay-per-query, no free tier dichiarato |
| **ARGOS use** | BASSO — preferire vindecoder.eu o freevindecoder.eu che danno piu' dati gratis |

---

### 1.5 NHTSA vPIC (USA — no utilita' diretta per EU)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://vpic.nhtsa.dot.gov/api/ |
| **Gratis?** | SI — 100% gratis, no registrazione, no limiti |
| **Dati** | VIN decode completo per veicoli USA-spec |
| **Coverage** | SOLO USA |
| **ARGOS use** | NULLO per il nostro segmento (BMW/MB/Audi EU-spec) |

---

### 1.6 coceurope.eu VIN Decoder

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://coceurope.eu/vin-decoder-vehicle/ |
| **Gratis?** | SI — strumento accessorio al loro servizio CoC |
| **Dati** | Specifiche EU del veicolo da VIN, utile per verificare conformita' |
| **ARGOS use** | INTERESSANTE: lo stesso provider che vende i CoC — il VIN decoder e' gratuito e puo' pre-verificare compatibilita' |

---

## 2. RECALL CHECK GRATUITI

### 2.1 Safety Gate EU / RAPEX

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://ec.europa.eu/safety-gate-alerts/ |
| **Gratis?** | SI — completamente gratuito, istituzionale EU |
| **Dati** | Tutti i richiami di sicurezza EU per prodotti non alimentari, inclusi veicoli |
| **Aggiornamento** | Settimanale |
| **Dataset** | Disponibile anche come file Excel scaricabili |
| **API?** | NO API ufficiale — ma dataset Excel settimanale scaricabile e ingestibile |
| **ARGOS use** | Scaricare dataset settimanale + query per make/model. Costo: €0 |

**Come usarlo per ARGOS**:
```python
import pandas as pd
# Scarica dataset settimanale EU Safety Gate
url = "https://ec.europa.eu/safety-gate-alerts/screen/webReport"
# Oppure dataset open: https://data.europa.eu/data/datasets/...
df = pd.read_excel("rapex_weekly.xlsx")
recalls = df[df['brand'].str.contains('BMW|Mercedes|Audi', case=False)]
```

---

### 2.2 car-recalls.eu

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://car-recalls.eu/ |
| **Gratis?** | SI — accesso libero, no registrazione |
| **Dati** | Aggregato Safety Gate EU + KBA Germania + USA NHTSA, ricercabile per marca/modello |
| **Aggiornamento** | Settimanale (~10 nuovi record/settimana) |
| **API?** | NO — solo interfaccia web, ma scrapabile facilmente |
| **ARGOS use** | CONSIGLIATO come interfaccia web per check manuale. Scrapabile per alert automatici |

---

### 2.3 KBA Kraftfahrt-Bundesamt (Germania)

| Campo | Dettaglio |
|-------|-----------|
| **URL ufficiale** | https://www.kba.de/EN/Themen_en/Marktueberwachung_en/Rueckrufe_en/ |
| **URL ricerca** | https://www.kba-online.de/rrdb/buerger/ |
| **Gratis?** | SI — database pubblico gratuito |
| **Dati** | Richiami auto Germania da 2004 a oggi, ricercabile per marca/modello/periodo |
| **API?** | NO API ufficiale — interfaccia web, scrapabile |
| **Coverage** | Veicoli immatricolati in Germania (la maggior parte del nostro stock) |
| **ARGOS use** | FONDAMENTALE: la maggior parte dei nostri veicoli vengono da DE — KBA e' la fonte primaria per recall |

---

### 2.4 NHTSA Recalls API (USA — limitata utilita')

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://api.nhtsa.gov/recalls/recallsByVehicle |
| **Gratis?** | SI — API pubblica no auth |
| **Endpoint** | `GET /recalls/recallsByVehicle?make=BMW&model=X3&modelYear=2022` |
| **Dati** | Recall USA per make/model/anno |
| **ARGOS use** | BASSO — ricordare che recall USA non equivalgono a recall EU, ma BMW/MB/Audi spesso emettono recall globali simultanei. Da usare come segnale aggiuntivo, non primario |

---

## 3. STORICO KM / VERIFICA FRODI

### 3.1 Car-Pass (Belgio)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.car-pass.be/en |
| **Gratis?** | NO — costo €7,30 per certificato |
| **Dati** | Storico km completo per veicoli immatricolati in Belgio, registrato da officine/revisioni |
| **Coverage** | SOLO veicoli belgi (immatricolati BE) |
| **Come funziona** | Obbligatorio per legge in BE allegarlo alla vendita. Chi vende BE→IT deve fornirlo. |
| **ARGOS use** | RICHIEDERLO SEMPRE quando acquisto veicolo belga. Il venditore e' obbligato per legge a fornirlo. Costo per ARGOS: €0 (paga il venditore) |

---

### 3.2 NAP / RDW (Olanda)

| Campo | Dettaglio |
|-------|-----------|
| **URL NAP** | https://www.napcheck.com/ |
| **URL RDW open data** | https://opendata.rdw.nl/ |
| **NAP gratis?** | NO — certificato NAP a pagamento (piccola fee) |
| **RDW open data gratis?** | SI — API completamente gratuita, no API key |
| **Dati RDW** | Marca, modello, anno imm., potenza, carburante, emissioni, colore, peso, massa, tipo carrozzeria, data prima immatricolazione NL, storico revisioni APK (analogo revisione IT) |
| **Endpoint RDW** | `https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken=AB123CD` |
| **Formato** | JSON, CSV, XML |
| **ARGOS use** | FONDAMENTALE per veicoli olandesi: RDW open data e' gratuito, restituisce dati completi incluse date revisione APK (indicano uso reale del veicolo). Aggiungere al CoVe enrichment pipeline per veicoli NL |

**Integrazione Python RDW**:
```python
import requests

def get_rdw_data(license_plate: str) -> dict:
    """Dati gratuiti RDW per veicoli NL. No API key richiesta."""
    plate = license_plate.replace("-", "").upper()
    url = f"https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken={plate}"
    resp = requests.get(url, timeout=10)
    return resp.json()[0] if resp.ok and resp.json() else {}
```

---

### 3.3 Carvertical (NON gratuito — per riferimento)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.carvertical.com |
| **Costo** | ~€20-30 per report completo |
| **Dati** | 1.000+ fonti, 45 paesi, odometro, incidenti, furto, aste, danni alluvione |
| **ARGOS use** | Solo per veicoli ad alto rischio frode (km molto bassi, prezzo molto basso, multipli proprietari). NON per ogni veicolo — troppo costoso a volume |

---

## 4. VALUTAZIONE / PRICING

### 4.1 AutoScout24 Valutazione (IT)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.autoscout24.it/valutazione-auto/ |
| **Gratis?** | SI — completamente gratuito, no registrazione |
| **Dati** | Prezzo medio, range min-max, basato su 10M+ annunci AS24 attuali |
| **Input richiesto** | Marca, modello, anno, carburante, potenza, cambio, km |
| **Output** | Prezzo medio offerta + range + PDF scaricabile |
| **Limite** | Prezzi IT (listing), non wholesale. Soggetti a stagionalita' |
| **ARGOS use** | UTILE come benchmark IT velocity per il dossier dealer. Citabile come "quotazione AutoScout24 aggiornata" |

---

### 4.2 automobile.it Valutazione

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.automobile.it/valutazione-auto |
| **Gratis?** | SI — gratuito |
| **Dati** | Basato su quotazioni Eurotax aggiornate. Restituisce stima prezzo usato IT |
| **ARGOS use** | INTERESSANTE: utilizza Eurotax come base ma espone il dato gratis. Usare per cross-check prezzo IT accanto a AS24 |

---

### 4.3 Eurotax (accesso diretto)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.motornet.it/ |
| **Gratis?** | PARZIALE — €3 per quotazione standard, €4 personalizzata su Motornet.it |
| **Dati** | Quotazione ufficiale Eurotax (listino blu = compra da privato, listino giallo = vende a privato) |
| **Aggiornamento** | Ogni 2 mesi circa |
| **ARGOS use** | €3 per verifica puntuale quando serve quotazione "ufficiale" da mettere nel dossier dealer |

**NOTA IMPORTANTE**: automobile.it espone le quotazioni Eurotax GRATIS come wrapper. Preferire quello prima di pagare €3 su Motornet.

---

### 4.4 DAT / SilverDAT (NON gratuito)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.dat.de |
| **Costo** | €274+/mese per accesso professional |
| **Dati** | Valutazioni wholesale tedesche, prezzi di vendita reali (non listing) |
| **ARGOS use** | NON usare — troppo costoso. Alternativa: i nostri scraper su Mobile.de + AS24.de |

---

### 4.5 ADAC — dati pubblici

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://www.adac.de |
| **Gratis?** | Dati statistici pubblici SI, valutazione singolo veicolo NO (riservata soci) |
| **Dati pubblici** | Costi operativi per modello (consumo, manutenzione, deprezzamento medio), test affidabilita', prezzi medi di categoria |
| **ARGOS use** | Usare i dati pubblici ADAC per arricchire CoVe con costi operativi attesi (gia' integrato in adac_price_reference.py) |

---

## 5. DOCUMENTI IMPORTAZIONE

### 5.1 Modulistica Motorizzazione Civile (gratuita)

| Documento | Dove trovarlo | Costo |
|-----------|--------------|-------|
| Modello NP2C | ACI Gov — aci.gov.it | Gratuito |
| Modello NP2D | ACI Gov o uffici STA | Gratuito |
| Modello TT2119 | Motorizzazione Civile | Gratuito |
| Dichiarazione conformita' UE | Costruttore o CoC provider | Gratuito (CoC a pagamento) |

**URL ACI nazionalizzazione**: https://aci.gov.it/pratica-auto/nazionalizzazione-iscrizione-di-veicolo-usato-proveniente-dallestero/

---

### 5.2 ACI — Calcolatore IPT

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://aci.gov.it/pratica-auto/calcolo-ipt-percentuali-di-maggiorazione/ |
| **Gratis?** | SI |
| **Dati** | IPT per provincia: base €151 (<53kW) poi €3,51-4,56/kW aggiuntivo. Province possono aumentare fino al +30% |
| **ARGOS use** | Inserire nel dossier la stima IPT per la provincia del dealer (es. Foggia, Cosenza, Avellino) per dimostrare controllo totale dei costi import |

**Calcolatori alternativi gratuiti**: pratico.it, socalsolver.com

---

### 5.3 ACI — Calcolatore Bollo e Superbollo

| Campo | Dettaglio |
|-------|-----------|
| **URL ufficiale** | https://aci.gov.it/servizio/calcola-online-il-bollo-ed-il-superbollo/ |
| **URL alternativo** | https://www.calcolosuperbollo.it/ o https://superbollo.altervista.org/ |
| **Gratis?** | SI — tutti gratuiti |
| **Input** | Classe ambientale EURO, potenza kW, anno immatricolazione, regione, alimentazione |
| **Output** | Importo bollo + superbollo + genera F24 ELIDE precompilato |
| **ARGOS use** | Inserire nel dossier: "superbollo annuale previsto: €X" per auto >185kW. Dimostra al dealer che ha calcolato anche il costo post-acquisto |

---

### 5.4 IVA Intra-EU — Regime corretto

| Scenario | Regime | Costo IVA |
|----------|--------|-----------|
| Dealer IT acquista da dealer DE (B2B, partita IVA) | Reverse charge — art. 38/DL 331/93 | 0 in Germania, autofattura IT |
| Dealer IT acquista da privato DE | Regime del margine | IVA sul margine del venditore |
| Acquisto veicolo nuovo intra-UE | F24 immatricolazione | 22% IT da versare prima di immatricolare |

**Fonte ufficiale**: https://europa.eu/youreurope/citizens/vehicles/cars/vat-buying-selling-cars/index_it.htm (gratuita, istituzionale)

**Calcolatore doganale**: https://www.alpimelissa.com/consulenza-doganale/calcolare-i-costi-di-importazione/ (gratuito per stima)

---

## 6. GARANZIA — GUIDA STRATEGICA

### 6.1 Garanzia Legale UE (2 anni — Direttiva 2019/771)

| Campo | Dettaglio |
|-------|-----------|
| **Base legale** | Direttiva UE 2019/771, recepita IT con D.Lgs 170/2021 |
| **Durata** | 2 anni (auto nuove) / minimo 1 anno per usate (ma il venditore puo' contrattare fino a 2 anni) |
| **Chi la deve al dealer IT** | Il VENDITORE EU (dealer DE) e' obbligato verso un consumatore finale. Ma ARGOS acquista B2B → la garanzia legale consumer NON si applica automaticamente B2B |
| **Come usarla per il dealer IT** | Il dealer IT che rivende al privato garantisce 2 anni (minimo 1 anno per usate). Non e' la garanzia del venditore DE, e' l'obbligo del dealer IT verso il suo cliente finale |

**IMPLICAZIONE ARGOS**: La garanzia legale UE non e' un vantaggio diretto per ARGOS nel B2B. Il vantaggio reale e' la garanzia costruttore.

---

### 6.2 Garanzia Costruttore EU — Cross-Border VALIDA

| Brand | Programma | Durata | Cross-border EU? | Note |
|-------|-----------|--------|-----------------|------|
| **BMW** | BMW Approved Used / Premium Selection | 24 mesi | SI — tutta Europa continentale | Riparabile in qualsiasi BMW Center EU |
| **Mercedes-Benz** | Mercedes-Benz Certified | 12-48 mesi (varia) | SI — tutti stati UE + IS/LI/NO/CH | Mobilo roadside assistance EU inclusa |
| **Audi** | Audi Prima Scelta Plus | fino a 4 anni | SI — EU | Valida <96 mesi eta', <150.000km |
| **Porsche** | Porsche Approved | 24 mesi | SI — EU | |

**REGOLA CRITICA**: La garanzia costruttore (BMW/MB/Audi Certified) e' VALIDA in tutta EU solo se il veicolo e' entrato nel programma certified. Auto comprata da dealer tedesco non-certified NON ha questa garanzia — ha solo quella legale.

**COME USARLO NEL PITCH A DEALER**:
```
"La X3 che le propongo viene da dealer autorizzato BMW Premium Selection.
Garanzia costruttore ancora attiva fino a [data], valida in tutta Europa,
riparabile dal BMW Center piu' vicino a lei. Il suo cliente finale compra
tranquillo."
```

---

### 6.3 Come verificare garanzia residua GRATIS

| Metodo | Come | Costo |
|--------|------|-------|
| BMW Online Check | my.bmw.com/it → "Verifica garanzia" con VIN | Gratuito |
| Mercedes-Benz | mercedes-benz.it/warranties → inserisci VIN | Gratuito |
| Audi | myaudi.it → VIN lookup | Gratuito |
| Dealer autorizzato | Telefonata con VIN → risposta immediata | Gratuito |

---

## 7. EMISSIONI E TASSE

### 7.1 Calcolatore Superbollo (ACI — ufficiale)

| Campo | Dettaglio |
|-------|-----------|
| **URL** | https://aci.gov.it/servizio/calcola-online-il-bollo-ed-il-superbollo/ |
| **Gratis?** | SI |
| **Soglia superbollo** | >185kW (252CV): +€20/kW aggiuntivo |
| **Esenzioni** | Dopo 5 anni dal 1° imm. paghi il 60%, dopo 10 anni 30%, dopo 20 anni esente |
| **Genera F24** | SI — precompilato |

---

### 7.2 Classe Emissioni da VIN / Targa

| Metodo | URL | Costo | Note |
|--------|-----|-------|------|
| ACI bollo (da targa IT) | aci.gov.it | Gratis | Solo auto gia' immatricolate IT |
| Motorizzazione (da libretto) | Dato fisico sul libretto DE | Gratis | Euro 5/6 scritto su libretto tedesco |
| freevindecoder.eu | freevindecoder.eu | Gratis | Restituisce norma emissioni da VIN |
| vindecoder.eu (20 free) | vindecoder.eu | Gratis (20 VIN) | Campo emission_standard nel JSON |

**Per auto da immatricolare IT**: la classe emissioni (Euro 5/6) e' nel libretto tedesco (Zulassungsbescheinigung Teil I) al campo "P.3" (Euro standard) e "V.9" (CO2 g/km). Gratis, nessuno strumento richiesto.

---

### 7.3 Esenzioni Regionali Bollo

| Regione | Esenzione | Note |
|---------|-----------|------|
| Campania | Esenzione per veicoli ibridi/elettrici | 3 anni |
| Puglia | Idem | Varia per anno |
| Calabria | Riduzione per veicoli Euro 6 nuovi | Verifica annuale |

**Come verificare per ogni regione**: ACI → "Agevolazioni IPT" → filtro per regione. Gratuito.

---

## 8. MAPPA UTILIZZO ARGOS — WORKFLOW INTEGRATO

```
VEICOLO TROVATO DA SCRAPER
         │
         ├─ VIN decode: freevindecoder.eu (gratis, no limiti)
         │   Dati: anno esatto, motorizzazione, emissioni
         │
         ├─ Recall check: car-recalls.eu (gratis, scrapabile)
         │   + KBA database se veicolo tedesco
         │
         ├─ Verifica garanzia costruttore: sito brand con VIN (gratis)
         │   → inserire data scadenza nel CoVe score
         │
         ├─ Pricing benchmark IT: AS24 valutazione (gratis)
         │   + automobile.it/Eurotax (gratis)
         │
         ├─ Se veicolo NL: RDW open data (gratis, API JSON)
         │   → km storia APK, date revisione
         │
         ├─ Se veicolo BE: richiedere Car-Pass al venditore (obbligatorio per legge)
         │
         ├─ Calcolo costi dealer: ACI IPT + Bollo/Superbollo (gratis)
         │
         └─ PDF dossier: tutti i dati sopra aggregati dal CoVe
```

---

## 9. STRUMENTI DA AGGIUNGERE AL COVE ENRICHMENT PIPELINE

| Strumento | Endpoint | Priorita' | Effort |
|-----------|----------|-----------|--------|
| freevindecoder.eu | Web scrape | P1 | 2h |
| car-recalls.eu | Web scrape (settimanale) | P1 | 3h |
| KBA recall DB | Web scrape | P1 | 2h |
| RDW open data (NL) | API REST gratis | P0 | 1h |
| AS24 valutazione | Web scrape | P2 | 3h |
| Safety Gate EU Excel | Download settimanale | P2 | 2h |

**Total effort stimato**: 13h per enrichment pipeline completa con zero costi aggiuntivi.

---

## FONTI

- [vindecoder.eu/api](https://vindecoder.eu/api/) — Pricing e dati API
- [vindecoder.eu/pricing/api](https://vindecoder.eu/pricing/api) — Piani tariffari
- [freevindecoder.eu](https://www.freevindecoder.eu/) — Free VIN decoder EU
- [carfax.eu/free-vin-decoder](https://www.carfax.eu/free-vin-decoder) — CARFAX free decoder
- [ec.europa.eu/safety-gate-alerts](https://ec.europa.eu/safety-gate-alerts/) — RAPEX/Safety Gate EU ufficiale
- [car-recalls.eu](https://car-recalls.eu/) — Aggregatore recall EU+KBA
- [kba.de/EN/Themen_en/Marktueberwachung_en/Rueckrufe_en/](https://www.kba.de/EN/Themen_en/Marktueberwachung_en/Rueckrufe_en/rueckrufe_node_en.html) — KBA ufficiale
- [kba-online.de/rrdb/buerger/](https://www.kba-online.de/rrdb/buerger/) — KBA recall search pubblico
- [car-pass.be/en](https://www.car-pass.be/en) — Car-Pass Belgio
- [napcheck.com](https://www.napcheck.com/) — NAP check NL (a pagamento)
- [opendata.rdw.nl](https://opendata.rdw.nl/) — RDW open data NL (gratuito)
- [autoscout24.it/valutazione-auto](https://www.autoscout24.it/valutazione-auto/) — Valutazione AS24 gratuita
- [automobile.it/valutazione-auto](https://www.automobile.it/valutazione-auto) — Valutazione Eurotax gratuita
- [motornet.it](https://www.motornet.it/) — Eurotax a pagamento (€3)
- [aci.gov.it — IPT](https://aci.gov.it/pratica-auto/calcolo-ipt-percentuali-di-maggiorazione/) — Calcolatore IPT gratuito
- [aci.gov.it — Bollo/Superbollo](https://aci.gov.it/servizio/calcola-online-il-bollo-ed-il-superbollo/) — Calcolatore ufficiale
- [calcolosuperbollo.it](https://www.calcolosuperbollo.it/) — Calcolatore alternativo con F24
- [aci.gov.it — Nazionalizzazione](https://aci.gov.it/pratica-auto/nazionalizzazione-iscrizione-di-veicolo-usato-proveniente-dallestero/) — Modulistica import
- [euroconsumatori.org — garanzia EU import](https://www.euroconsumatori.org/it/garanzia_ue_auto_importate) — Guida garanzia UE
- [mercedes-benz-certified.it](https://mercedes-benz-certified.it/auto-usate-servizi/) — Mercedes Certified EU
- [api.nhtsa.gov](https://api.nhtsa.gov/recalls/recallsByVehicle) — NHTSA recall API gratuita
- [europa.eu — IVA veicoli](https://europa.eu/youreurope/citizens/vehicles/cars/vat-buying-selling-cars/index_it.htm) — Regime IVA ufficiale EU
