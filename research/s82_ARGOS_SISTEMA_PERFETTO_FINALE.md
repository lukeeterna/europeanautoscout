# ARGOS SISTEMA PERFETTO — BLUEPRINT FINALE
## Sintesi da 6 ricerche globali | S82 — 2026-03-24

---

## VISION IN UNA FRASE

Il dealer riceve un pacchetto che non esiste in Italia:
veicolo trovato su 73 portali in 15 lingue, verificato su 7 criteri documentali,
con foto HD, margine netto calcolato, recall controllati, km certificati multi-fonte,
scheda pronta per la rivendita al cliente finale, garanzia attivabile.
Paga solo a consegna. Nessuno offre questo.

---

## PARTE 1 — IL DOSSIER ARGOS (cosa riceve il dealer)

### Pagina 1: COPERTINA
```
Logo ARGOS + Badge "ARGOS PREMIUM VERIFIED"
BMW X3 xDrive20d 2022 — 42.600 km
Scheda Riservata per [Dealer] — [Citta]
ARGOS GRADE: A (scala A-E, basata su NAAA/USS)
Confidence Score: 87/100
```

### Pagina 2: HERO + NUMERI CHIAVE
```
3-4 foto HD reali del veicolo (scaricate, watermarked)
Prezzo EU: €30.951 | Mercato IT: €37.810 | Margine netto dealer: €4.300
Costo totale chiavi in mano: €33.510 (tutto incluso)
Tempistica: 12 gg lavorativi
```

### Pagina 3: VERIFICA 7 CRITERI "ARGOS PREMIUM VERIFIED"
```
[V] Km verificati multi-fonte          — CoVe + NAP/Car-Pass se NL/BE
[V] Zero flag frode rilevati           — CoVe fraud_flags CLEAN
[V] Revisione tecnica attiva           — HU valida fino a [data] (da annuncio DE)
[V] Affidabilita modello               — ADAC/TUV: anomalie 4% (classe ottima)
[V] Delta mercato documentato          — 22 annunci comparati su 28 portali
[V] Proprietari dichiarati: 1          — da annuncio originale
[V] Foto HD originali verificate       — 6 foto, angoli standard
```

### Pagina 4: ANALISI FINANZIARIA COMPLETA
```
Prezzo acquisto EU           EUR 30.951    Franco EU (IVA esclusa)
Trasporto bisarca            EUR 1.200     Norvegia → Sud Italia, ~3.200 km
Immatricolazione IT          EUR 430       IPT + Motorizzazione + targhe
Costo totale chiavi in mano  EUR 32.581
────────────────────────────────────────
Prezzo mercato Italia        EUR 37.810    Media 22 annunci IT
Margine lordo                EUR 5.229
Fee ARGOS                    EUR 900       Solo a deal chiuso
MARGINE NETTO DEALER         EUR 4.329     Guadagno reale per lei
────────────────────────────────────────
Rotazione stimata zona       45-60 gg      Basata su dati AS24 provincia
```

### Pagina 5: INTELLIGENCE VEICOLO
```
Recall check                 Nessun richiamo pendente (KBA + Safety Gate EU)
VIN decode                   Specifiche tecniche confermate (freevindecoder.eu)
Garanzia costruttore         BMW — attiva fino a [data] (verificabile su my.bmw.com)
Classe emissioni             Euro 6d (conforme Italia)
Superbollo                   Non applicabile (< 185 kW)
Bollo annuale stimato        EUR 284
```

### Pagina 6: DETTAGLI TECNICI + ALLESTIMENTO
```
Motore: 2.0 diesel 190 CV | Cambio: Automatico 8 marce | Trazione: xDrive
Colore: [da detail page] | Interni: [da detail page]

Allestimento di fabbrica (da VIN decode):
- LED Matrix | Head-Up Display | Navi Professional
- Pelle Vernasca | Sedili riscaldati | Park Assist Plus
- Harman Kardon | Driving Assistant Plus | Panoramico
```

### Pagina 7: SCHEDA RIVENDITA PER IL CLIENTE FINALE (BONUS)
```
Scheda in italiano, pronta da stampare, con:
- Foto HD dell'auto
- Dati tecnici essenziali
- "Km certificati" + "Verificata ARGOS"
- QR code → scheda digitale completa
- Garanzia costruttore residua
- TCO stimato: €7.500/anno vs €11.000 auto nuova

Il dealer la da al SUO cliente senza fare nulla.
```

### Pagina 8: FOOTER + PROSSIMI PASSI
```
"Conferma interesse? Blocchiamo il veicolo in 24h."
"Trasporto 10-14 giorni, pratiche incluse."
"Paga SOLO a veicolo consegnato e immatricolato."

ARGOS Automotive | Luca Ferretti
ferretti.argosautomotive@gmail.com
Documento riservato per [Dealer]
```

---

## PARTE 2 — FEATURE COMPLETE LIST (ordinate per sprint)

### SPRINT 0 — GIA IMPLEMENTABILI (infrastruttura esiste)

| # | Feature | Come | Costo |
|---|---------|------|-------|
| 1 | Alert stock personalizzato | Scraper 73 portali + filtro per profilo dealer + WA notification | €0 |
| 2 | Delta prezzo IT nel dossier | AS24.it valutazione gratis + CoVe market index | €0 |
| 3 | Scheda rivendita per cliente finale | Secondo template PDF generator | €0 |
| 4 | Fee calculator all-in (numero unico) | fee_calculator.py + transport_estimator.py esistono | €0 |
| 5 | Confronto fai-da-te vs ARGOS | Documento statico, aggiornabile | €0 |
| 6 | Esclusiva 48h per dealer partner | Logica nel CRM, timer | €0 |
| 7 | SLA risposta 24h comunicato | Copy nel messaggio + landing | €0 |
| 8 | Briefing vocale WA 60 sec | edge-tts (Diego Neural IT) + wa-daemon | €0 |

### SPRINT 1 — SVILUPPO 2-3 SETTIMANE

| # | Feature | Come | Costo |
|---|---------|------|-------|
| 9 | Schema DB completo (vehicle_listings + images) | DuckDB, nuove tabelle | €0 |
| 10 | Detail enricher V2 (VIN, equipment, description) | Scraping detail page PROCEED | €0 |
| 11 | Image downloader + cache + watermark | CDN upgrade rules + download + watermark | €0 |
| 12 | Recall check automatico | Scrape KBA + car-recalls.eu + NHTSA (recall globali) | €0 |
| 13 | VIN decode (specs + emissioni) | freevindecoder.eu (illimitato) | €0 |
| 14 | Odometro multi-source | RDW API (NL gratis), Car-Pass (BE, venditore obbligato) | €0 |
| 15 | DAT consumer sanity check | dat.de/gebrauchtfahrzeugwerte (gratis) | €0 |
| 16 | Garanzia costruttore check | my.bmw.com / myaudi.it / mercedes-benz.it con VIN | €0 |
| 17 | ARGOS GRADE (A-E) | Basato su NAAA (PDF pubblico gratis) + CoVe scores | €0 |
| 18 | Filtro dealer-ready (margine >= EUR 3.000) | Logica in pipeline | €0 |

### SPRINT 2 — MESE 2

| # | Feature | Come | Costo |
|---|---------|------|-------|
| 19 | Foto sottoscocca come standard | Checklist fotografica al venditore DE | €0 |
| 20 | Foto HD organizzate per rivendita | Google Drive condiviso per dealer | €0 |
| 21 | Report mensile zona dealer | Scraper data + analisi rotazione per provincia | €0 |
| 22 | Modelli alta rotazione per zona | AS24.it + dati venduto per provincia | €0 |
| 23 | Storico prezzi 12 mesi trend | Market Price Index storico | €0 |
| 24 | TCO calculator IT | Bollo ACI + assicurazione media + manutenzione + carburante | €0 |
| 25 | QR code nel dossier | Genera QR → scheda digitale veicolo | €0 |
| 26 | AutoBild TUV-Report integrato | Affidabilita modello da 38M revisioni (gratuito) | €0 |
| 27 | Ravin AI scan richiesta al venditore | App consumer gratuita, scan smartphone | €0 |
| 28 | 4 prezzi per contesto (KBB model) | Wholesale / Trade-In / Retail / Premium Retail | €0 |

### SPRINT 3 — MESE 3+

| # | Feature | Come | Costo |
|---|---------|------|-------|
| 29 | Gestione documentale chiavi in mano | COC (EuroCOC), traduzione, F24, coordinamento STA | €80-200 incluso in fee |
| 30 | Trasporto coordinato zero gestione | Rete bisarcari, conferma 24h prima | Incluso in fee |
| 31 | Garanzia convenzionale attivabile | Partnership ConformGest/AutoProtetta | €150-400 (dealer paga) |
| 32 | DEKRA ispezione (post 3-5 deal) | Accordo volume usedcar@dekra.it | €60-80/veicolo |
| 33 | Officina autorizzata report pre-acquisto | BMW/MB/Audi workshop nel CAP venditore | €50-80/veicolo premium |
| 34 | Perito auto indipendente | Iscrizione Camera di Commercio | €200-500 una tantum |

---

## PARTE 3 — STRUMENTI GRATUITI INTEGRABILI

### VIN & Specs
| Strumento | URL | Gratis | Cosa da |
|-----------|-----|--------|---------|
| freevindecoder.eu | freevindecoder.eu | SI, illimitato | Make, model, anno, motore, emissioni EU |
| vindecoder.eu | vindecoder.eu | 20 VIN gratis | 50+ campi strutturati |
| CARFAX EU free decoder | carfax.eu/free-vin-decoder | SI parziale | Make/model + storico import 20 paesi |

### Recall
| Strumento | URL | Gratis | Cosa da |
|-----------|-----|--------|---------|
| car-recalls.eu | car-recalls.eu | SI | Aggregato Safety Gate EU + KBA, scrapabile |
| KBA ufficiale | kba-online.de/rrdb/buerger | SI | Recall tedeschi dal 2004 |
| NHTSA API | api.nhtsa.gov | SI, no auth | Recall USA (BMW/MB/Audi globali) |
| Safety Gate EU | ec.europa.eu/safety-gate-alerts | SI | Dataset Excel scaricabile settimanalmente |

### Storico KM
| Strumento | URL | Gratis | Cosa da |
|-----------|-----|--------|---------|
| RDW open data NL | opendata.rdw.nl | SI, API REST | Km, revisioni APK, emissioni (veicoli NL) |
| Car-Pass BE | car-pass.be | Venditore obbligato | Km certificati per legge (veicoli BE) |
| MOT History UK | gov.uk/check-mot-history | SI | Revisioni con km (veicoli UK) |

### Pricing
| Strumento | URL | Gratis | Cosa da |
|-----------|-----|--------|---------|
| AS24 IT valutazione | autoscout24.it/valutazione-auto | SI | Prezzo medio + range IT, PDF scaricabile |
| automobile.it | automobile.it/valutazione-auto | SI | Quotazioni Eurotax come wrapper |
| DAT consumer | dat.de/gebrauchtfahrzeugwerte | SI | Valore orientativo DE (sanity check) |

### Garanzia costruttore
| Brand | URL | Gratis | Cosa verifica |
|-------|-----|--------|---------------|
| BMW | my.bmw.com | SI, con VIN | Garanzia residua, pacchetti service |
| Mercedes | mercedes-benz.it/warranties | SI, con VIN | Garanzia residua |
| Audi | myaudi.it | SI, con VIN | Garanzia residua |

### Documenti Import
| Strumento | URL | Gratis |
|-----------|-----|--------|
| ACI modulistica | aci.gov.it | SI |
| Calcolatore IPT | aci.gov.it/calcolo-ipt | SI |
| Calcolatore Bollo/Superbollo | aci.gov.it o calcolosuperbollo.it | SI |

---

## PARTE 4 — GRADING SYSTEM "ARGOS GRADE"

### Scala A-E (ispirata a NAAA + USS + BCA)

```
GRADE A — ECCELLENTE (Confidence >= 0.85, zero flag)
  Km/anno nella media, prezzo competitivo, fraud CLEAN,
  documentazione completa, foto HD disponibili,
  revisione tecnica attiva, zero recall pendenti.

GRADE B — BUONO (Confidence >= 0.75, zero flag critici)
  Km leggermente sopra media OPPURE 1 dato mancante
  (es. colore non confermato), resto tutto verificato.

GRADE C — ACCETTABILE (Confidence >= 0.65, warning minori)
  Km elevati OPPURE prezzo borderline OPPURE
  documentazione parziale. Richiede attenzione.

GRADE D — ATTENZIONE (Confidence >= 0.55, warning)
  VIN_CHECK necessario OPPURE anomalia km/prezzo
  OPPURE fraud flag WARNING. Da valutare caso per caso.

GRADE E — NON RACCOMANDATO (Confidence < 0.55)
  Non proposto al dealer. Solo per tracking interno.
```

### Componenti del grade (peso)
```
35% — CoVe confidence score (bayesiano)
20% — Fraud flags (CLEAN/WARNING/SUSPICIOUS)
15% — Completezza dati (quanti campi verificati su 7)
15% — Qualita foto (N. foto, angoli coperti)
10% — Recall status (pulito/pendente)
 5% — Storico km verificabile (NAP/Car-Pass/RDW)
```

### Primo in Italia
Nessun operatore italiano ha un grading system per usato.
ARGOS diventa il riferimento. Ogni dossier apre con il GRADE.

---

## PARTE 5 — DEKRA & DAT: PIANO OPERATIVO

### FASE 1 — Oggi (€0)
```
"ARGOS Pre-Purchase Inspection" — stessi 100 punti di DEKRA, brand nostro
- Checklist fotografica 50 punti inviata al venditore DE
- OBD readout richiesto (dealer DE lo fanno volentieri)
- VIN decode completo (freevindecoder.eu)
- Recall check (KBA + Safety Gate EU)
- Km verification (RDW per NL, Car-Pass per BE)
- DAT consumer valuation come sanity check
```

### FASE 2 — Dopo 3-5 deal (€50-80/veicolo premium)
```
Per veicoli > EUR 25.000:
- Officina autorizzata BMW/MB/Audi nel CAP del venditore DE
- Report pre-acquisto con timbro officina autorizzata
- "Verificato da officina autorizzata BMW Monaco" nel dossier
- Pesa quanto DEKRA per il dealer IT
```

### FASE 3 — Dopo 10+ deal (€60-80/veicolo)
```
Contattare usedcar@dekra.it per accordo volume
- Standard: EUR 120,78/ispezione
- Volume (stima): EUR 60-80/ispezione
- Sigillo DEKRA fisico sull'annuncio = credibilita massima
- Usare SOLO per deal > EUR 40.000 dove il ROI lo giustifica
```

### FASE 4 — Lungo termine
```
Iscrizione Camera di Commercio come perito auto
- EUR 200-500 una tantum
- Titolo usabile nelle comunicazioni
- "Perito Auto — Camera di Commercio di [provincia]"
```

---

## PARTE 6 — AUDIT AFFIDABILITA DELLA RICERCA

### Dati VERIFICATI (fonti primarie consultate)
```
[V] NAAA grading scale — PDF pubblico scaricabile da naaa.com
[V] RDW open data NL — API REST pubblica, documentazione verificata
[V] Car-Pass BE — legge belga, obbligo del venditore
[V] freevindecoder.eu — testato, nessun limite
[V] car-recalls.eu — sito attivo, dati aggiornati
[V] KBA recall database — sito governativo DE attivo
[V] Safety Gate EU — dataset Excel scaricabile
[V] NHTSA API — documentazione pubblica, no auth
[V] AS24 IT valutazione — tool pubblico funzionante
[V] automobile.it valutazione — wrapper Eurotax funzionante
[V] DAT consumer — tool pubblico su dat.de
[V] ACI calcolatori — tools pubblici funzionanti
[V] DEKRA prezzi — listino pubblico su dekrate.dekra.it
[V] Garanzia BMW/MB/Audi — verificabile con VIN su siti ufficiali
```

### Dati DA VERIFICARE SUL CAMPO
```
[?] vindecoder.eu — 20 VIN gratuiti dichiarati, da testare se effettivi
[?] CARFAX EU free decoder — da testare cosa restituisce realmente
[?] Ravin AI consumer app — da testare qualita output
[?] DAT consumer output — da testare con VIN reale
[?] Officina autorizzata DE — da verificare costo reale report pre-acquisto
[?] DEKRA accordo volume — prezzo €60-80 e una STIMA, da negoziare
[?] ConformGest/AutoProtetta — costi partnership B2B da verificare
[?] NAP NL — costo check singolo da verificare (RDW e l'alternativa gratis)
[?] MOT UK — da verificare se funziona per auto poi esportate
```

### Dati ASSUNTI (non verificati, basati su fonti secondarie)
```
[!] Rotazione 45-60 gg per provincia — stima basata su media nazionale 59gg
[!] TCO €7.500/anno — stima aggregata, varia per regione e uso
[!] Trasporto NO→IT €1.200 — stima da transport_estimator, da quotare reale
[!] Margine netto dealer — dipende dal prezzo finale di vendita reale
[!] Transaction price vs listing price — delta sconosciuto per mercato IT
[!] TUV-Report anomalie per modello — dati 2025, da verificare aggiornamento 2026
```

### Come migliorare l'affidabilita
```
1. TEST REALI — prendere 5 VIN di veicoli PROCEED e passarli attraverso
   OGNI strumento gratuito. Documentare cosa restituisce realmente.

2. PREZZO VENDITA REALE — dopo i primi deal, confrontare il prezzo
   a cui il dealer rivende vs la nostra stima mercato IT.
   Questo calibra il CoVe con actual_outcome (oggi 230 row hanno NULL).

3. CROSS-VALIDATION — per ogni veicolo, confrontare:
   - Nostro market_price vs DAT consumer vs AS24 valutazione
   Se divergono > 15%, investigare quale fonte e piu accurata.

4. FEEDBACK DEALER — chiedere al dealer dopo la consegna:
   "Il veicolo corrispondeva alla scheda?" SI/NO + note
   Questo alimenta il loop di calibrazione.

5. STORICO — dopo 20+ deal, calcolare:
   - % veicoli dove il margine reale era entro ±20% della stima
   - % veicoli con sorprese (danni, km falsi, recall scoperti dopo)
   - Accuracy rate del grading ARGOS

6. LISTING FRESHNESS — verificare che i veicoli proposti siano
   ancora disponibili. Un dossier per un'auto gia venduta = danno reputazionale.
   Implementare check freshness < 48h prima dell'invio.
```

---

## PARTE 7 — ORDINE DI COSTRUZIONE

```
S83: Schema DB (vehicle_listings + vehicle_images) + scraper salva URL e immagini
S84: Detail Enricher V2 (VIN decode, equipment, foto HD, description)
S85: ARGOS GRADE + Recall check + Garanzia check + filtro dealer-ready
S86: PDF Enterprise V2 (foto reali, grading, 7 criteri, scheda rivendita)
S87: Alert stock personalizzato + esclusiva 48h + briefing vocale
S88: TCO calculator + storico prezzi + report mensile zona
S89: DEKRA/officina autorizzata pilot (primi deal reali)
S90: Calibrazione con actual_outcome dei primi deal
```

---

## CONCLUSIONE

Il sistema perfetto non e un sistema che fa tutto.
E un sistema dove OGNI dato nel dossier e:
1. REALE (viene da una fonte verificabile)
2. UTILE (il dealer ci prende una decisione)
3. UNICO (non lo trova da nessun'altra parte)
4. GRATUITO (costa zero ad ARGOS)

Se anche UNO dei dati nel dossier e inventato, stimato senza base,
o disponibile su AutoScout24 con un click — non vale la pena metterlo.

Il dealer deve aprire il dossier e dire:
"Questa roba non la trovo da nessun'altra parte."
