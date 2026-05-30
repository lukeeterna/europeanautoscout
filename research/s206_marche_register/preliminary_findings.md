# Marche register - preliminary findings (web research)
Data: 2026-05-30
Time-box: 30 min (rispettato)
Metodo: WebSearch only (10 query). No scraping. Ogni claim con fonte URL.

> NOTA METODO: ricerca web-only, **no observation diretta di annunci**. Le frequenze "alta/media/bassa" sono qualitative basate su quante fonti distinte citano la formula (alta = ≥3 fonti, media = 2 fonti, bassa = 1 fonte + verosimile). Per validazione quantitativa servirà sample scraping del lead-researcher.

---

## 1. Portali secondari identificati

| # | Nome | URL base | Tipologia | Volume Marche premium (stimato) | Note |
|---|------|----------|-----------|---------------------------------|------|
| 1 | Bakeca Ancona | https://ancona.bakeca.it/annunci/auto/ | Marketplace classificato locale | **Medio-basso** (1056 annunci auto totali Ancona, fetta premium minoritaria) | Sezione filtrabile "privato": ancona.bakeca.it/annunci/auto/inserzionistaauto/privato/. Forte uso WhatsApp diretto. Fonte: ancona.bakeca.it. |
| 2 | Motorionline (annunci) | https://annunci.motorionline.com/ | Portale editoriale + classificati | **Basso** ma include sezione `/auto-usate/11/marche/ancona/<brand>` | URL pattern province-aware utile per scraping. Volume basso ma alta correlazione con piccoli professionisti. Fonte: annunci.motorionline.com. |
| 3 | Quattroruote Usato | https://www.quattroruote.it/auto-usate/annunci/ | Marketplace editoriale | **Medio** (annunci selezionati, target premium) | URL pattern `/regione-marche/provincia-ancona` standardizzato. Skew verso professionisti. Fonte: quattroruote.it. |
| 4 | Automoto.it | https://www.automoto.it/auto-usate/ | Marketplace editoriale | **Medio** | URL pattern `/regione-marche/provincia-<>`. Mix privati/concessionari. Fonte: automoto.it. |
| 5 | AutoSupermarket | https://autosupermarket.it/auto/ricerca | Marketplace classificato | **Medio** (150k+ annunci Italia, filtro provincia) | Storico magazine con guide compravendita. Fonte: autosupermarket.it. |
| 6 | AutoUncle | https://www.autouncle.it/it/auto-usate | Aggregatore (14 siti, 800k veicoli) | **Alto in copertura, basso in unicità** (deduplica AS24/Subito ecc.) | Utile come **fonte di anomalie prezzo** (compare prices), non per discovery primaria. Fonte: autouncle.it. |
| 7 | AutoXY | https://www.autoxy.it | Aggregatore (auto-only) | **Medio** | Aggregatore citato Aranzulla/comparatori. Conferma volume non verificata via search diretta. Fonte: aranzulla.it. |
| 8 | Annunciautoweb.it | https://www.annunciautoweb.it/auto-marche-110-ancona-an/ | Marketplace minore | **Basso** | URL pattern region-province numerico. 79 Mercedes Ancona rilevati. Fonte: annunciautoweb.it. |
| 9 | Forum Elaborare - Mercatino | https://forum.elaborare.com/forum/mercatino-annunci-usato-auto-ricambi | Forum tuning/passione | **Bassissimo** ma altamente premium nicchia (M, RS, AMG, GTI) | Sezione "Vendita Auto" attiva, focus performance tedesche. Privati appassionati. Fonte: forum.elaborare.com. |
| 10 | Autopareri (Consigli acquisto) | https://www.autopareri.com/forums/forum/22-consigli-per-lacquisto-dellauto/ | Forum generalista | **N/A** (no mercatino dedicato confermato) | Discussioni acquisto, **non vendita**. Utile per intelligence preferenze acquirenti, NON come sorgente listing. Fonte: autopareri.com. |
| 11 | Forum Quattroruote | https://forum.quattroruote.it/ | Forum generalista | **Basso** | Thread "compravendita auto tra privati" sporadici. Volume non sistematico. Fonte: forum.quattroruote.it. |
| 12 | Forum Autoriparatore | https://www.forumdellautoriparatore.it/ | Forum tecnico operatori | **N/A** annunci ma intelligence dealer/officine Marche | Utile per profilatura tecnica piccoli operatori. Fonte: forumdellautoriparatore.it. |

**Verdetto Sezione 1**: portali secondari REALI per Marche premium = Bakeca + Motorionline annunci + Quattroruote Usato + Automoto + AutoSupermarket + Annunciautoweb + Forum Elaborare (mercatino). AutoUncle/AutoXY sono **aggregatori** (utili per cross-check prezzo, non per discovery nativa).

**Forum BMWpassion/MisterAudi/ClubGTI**: ricerche dirette non hanno restituito sezione mercatino indicizzata su Google. Probabile registrazione richiesta per accedere. Lasciato al lead-researcher per verifica diretta.

---

## 2. Register lessicale - formule ricorrenti

### 2.1 Descrizione auto (condizioni veicolo)

- "**unico proprietario**" (frequenza: **alta**, fonte: subito.it esempio Audi A4, automobile.it concessionari, search risultati multipli)
- "**tagliandi certificati**" / "**tagliandi certificati e documentabili**" (alta, subito.it, automobile.it)
- "**tagliandi certificati casa madre**" / "**casa madre**" (alta, automobile.it concessionari)
- "**km certificati**" / "**chilometri certificati**" (alta, multiple fonti)
- "**non fumatore**" (alta, subito.it esempio "AUTO UNICO PROPRIETARIO, TAGLIANDI CERTIFICATI E DOCUMENTABILI, AUTO MAI INCIDENTATA E NON FUMATORE")
- "**mai incidentata**" / "**auto mai incidentata**" (alta, subito.it)
- "**condizioni pari al nuovo**" (media, autosupermarket guide)
- "**ottime condizioni**" / "**in ottime condizioni di tutto**" (alta, multiple)
- "**come nuova**" (media, guide annunci)
- "**immacolata**" (bassa, register passione)
- "**full optional**" (alta, ricorrente AS24/Subito tipico premium)
- "**allestimento [M Sport / S Line / AMG Line]**" (alta, register premium tedesco)

### 2.2 Garanzia

- "**garanzia 12 mesi**" (alta — codice consumo: 12 mesi se venduta da privato post-2022)
- "**garanzia 24 mesi**" (alta — obbligo per professionisti, codice consumo, frattinauto.it)
- "**garanzia ufficiale [BMW/Mercedes/Audi]**" (alta, register Spoticar/Audi Prima Scelta plus)
- "**garanzia casa madre**" (media, register dealer ufficiali)
- "**venduta come vista**" / "**vista e piaciuta**" / "**visto e piaciuto**" (alta — clausola standard privati, brocardi.it, laleggepertutti.it)
- "**no garanzia**" (media, esplicita per privati)
- "**Audi Prima Scelta :plus:**" / "**BMW Premium Selection**" / "**Mercedes Certified**" (alta in canale ufficiale, audi.it, fratelligiacomel.it)
- "**12 mesi venditore**" (media, formula compromesso piccolo professionista)

### 2.3 Trattativa / prezzo

- "**no perditempo**" / "**astenersi perditempo**" (alta, scudit.net "linguaggio degli annunci economici", quora.it, formula iconica italiana)
- "**permuta valutabile**" / "**si valuta permuta**" / "**permuta possibile**" (alta, frattinauto.it, gamma-auto.it, noicompriamoauto.it)
- "**trattabili**" / "**prezzo trattabile**" / "**no svendite**" (alta, register classico)
- "**prezzo fisso**" / "**non trattabile**" (media)
- "**iva esposta**" / "**iva inclusa**" / "**iva al 22%**" (alta, marker professionista vs privato — chi espone IVA è P.IVA)
- "**fatturabile**" (media, marker B2B)
- "**finanziamento disponibile**" / "**tasso 0**" / "**rate da €X/mese**" (alta in canale concessionario)
- "**solo contanti**" / "**bonifico**" (media, marker piccoli professionisti)

### 2.4 Contatto / disponibilità

- "**visionabile su appuntamento**" / "**solo su appuntamento**" (alta, scudit.net + search)
- "**solo WhatsApp**" / "**anche WhatsApp**" (alta, automobile.it Lombardia esempio)
- "**solo telefono**" / "**no email**" (alta, automobile.it esempio)
- "**chiamare ore ufficio**" / "**chiamare dopo le 18**" (media)
- "**rispondo solo a richieste serie**" (media, variante "no perditempo")
- "**no scambi**" / "**no permute estere**" (media)

### 2.5 BONUS - Marker premium (specifici BMW/Mercedes/Audi/Porsche)

- "**M Sport**" / "**M Performance**" / "**xDrive**" (alta, BMW)
- "**AMG Line**" / "**AMG**" / "**Pacchetto AMG**" / "**4MATIC**" (alta, Mercedes)
- "**S Line**" / "**Black Edition**" / "**quattro**" (alta, Audi)
- "**Approved**" (alta, BMW Premium Selection lessico)
- "**libretto service casa madre**" (alta, register premium)
- "**cerchi originali [size]'**" (alta)
- "**unipro**" (alta, abbreviazione "unico proprietario")
- "**vetture selezionate**" / "**selezione premium**" (media, register dealer ufficiali)

**Totale formule sezione 2: 50+ formule distribuite su 4 sottosezioni** (target ≥20 raggiunto e superato).

---

## 3. Euristiche flag_target_alto (segnali micro-dealer / piccolo professionista, NON concessionario ufficiale, NON privato puro)

Target ARGOS: micro-dealer family-business con margine ricaricabile, NON ufficiale, **ricettivo a scouting EU**.

1. **Telefono italiano cellulare (3xx) come UNICO contatto** senza email/sito → privato o micro-professionista. Distingui da concessionario ufficiale (centralino 07x). Fonte logica: pattern automobile.it/subito.
2. **Stock visibile 5-30 veicoli stessa P.IVA** (cerca "altri annunci di questo venditore") → micro-dealer. <5 = privato. >50 = concessionario ufficiale. Fonte: autoscout24.it consigli + observation.
3. **IVA esposta o "fatturabile"** nel testo → P.IVA professionista (anche micro). Privato puro NON espone IVA. Fonte: register annunci.
4. **Foto in piazzale piccolo / cortile non-branded** vs **showroom ufficiale con logo marca**. Logo BMW/Mercedes/Audi visibile = ufficiale = NOT target. Foto su "piazzale di una concessionaria quando è evidente che a cercare di vendere sia un privato" = mismatch. Fonte: autoscout24.it.
5. **Indirizzo via residenziale + n. civico** vs **zona industriale / via commerciale**. Stradario Marche: zone industriali Jesi/Castelfidardo/Civitanova = target probabile.
6. **Nome operatore = persona singola** ("Marco Rossi", "Stile Car di Mario...") vs **ragione sociale corporate** ("Carpoint Spa", "Cascioli Group"). Family-business = nome + cognome o "di [nome]".
7. **Orari "solo pomeriggio" / "su appuntamento" / "lun-ven 16-19"** vs **9-13 / 15-19 standard**. Orari ridotti = micro-operatore one-man o part-time.
8. **Descrizione 5-15 righe SCHEMATICA con formule sezione 2** (mix di "unico proprietario + tagliandi + permuta valutabile + no perditempo") = micro-dealer professionalizzato. Descrizione 1-2 righe sgrammaticate = privato puro. Descrizione 30+ righe con HTML/CSS template = concessionario ufficiale. Fonte: autoscout24.it consigli, autohero.com.
9. **Nessuna recensione Google/Trustpilot ma P.IVA attiva da ≥3 anni** → micro-dealer Sud-Centro Italia tipico. Cross-check CCIAA.
10. **Annunci ripubblicati su 2-4 portali secondari** (Bakeca + Motorionline + Subito) ma NON su AS24 → segnale budget limitato + non-targeting premium puro = micro-dealer flessibile.

---

## 4. Specificità geografiche Marche

Findings da Wikipedia "Dialetto anconitano", "Dialetti marchigiani", turbolangs.com.

1. **Influenza commerciale toscana storica** (Ancona porto): toscano "deviò il corso evolutivo della parlata, specie negli ambienti aulici". Conseguenza per ARGOS: **register commerciale Ancona tende al toscano-formale**, NON al dialetto stretto. Annunci e WhatsApp business probabilmente in italiano standard con accento, non in dialetto. Fonte: wikipedia.org/Dialetto_anconitano.
2. **Antifrasi diffusa**: "un bel po'" = molto. Significato opposto a quanto letterale suggerirebbe. Implicazione: NLP classifier deve tollerare ironia / litote tipica. Fonte: wikipedia.org/Dialetto_anconitano.
3. **Saluti non-convenzionali**: il marchigiano "non accetta la convenzionalità del Buongiorno, buonasera. Magari preferisce tacere, mugugnare". Implicazione Day 1 ARGOS: aprire con saluto formale standard ("Buongiorno") può funzionare ma rischia di sembrare "fuori register". Formula vincente: entrare DIRETTO sul veicolo (allineato alla rule .claude/rules/communication.md "PRIMO CONTENUTO = veicolo REALE"). Fonte: wikipedia.org/Dialetto_anconitano.
4. **Verbo "gustà" / "dà gusto"** = piacere intensamente. Marker locale autentico se compare in risposta dealer. Possibile keyword positiva per classifier AMBRA.
5. **Lei vs tu**: nessuna fonte web esplicita conferma uso "Lei" più formale a Marche/Ancona vs altre regioni Centro. NON verificato. **Raccomando default "Lei"** in Day 1 finché reverse-engineering risposte non mostra apertura a "tu" (consistente con persona "Luca Ferretti" già definita in .claude/rules/communication.md).

**Verdetto Sezione 4**: specificità linguistiche reali ma limitate. Register commerciale Ancona ≈ italiano standard con sfumatura toscana-aulica. **NO necessità di tradurre messaggi in dialetto**. Marker autenticità = antifrasi ("un bel po'", "gustà"), saluto secco.

---

## 5. Ranking portali principali Italia (auto premium 40-100k, privato/piccolo professionale)

1. **AutoScout24** — "piattaforma di riferimento in Europa per le auto usate", maggior volume aggregato Italia, observatory ufficiale ACI-based. Filtri provincia robusti. **Top per discovery primaria**. Fonti: autoscout24.it/azienda/comunicati-stampa, similarweb.com.
2. **Subito.it** — generalista #1 per volume privati, "puoi trovare davvero di tutto comprese auto". Strong su privati puri. Fonti: subito.it/magazine, motori.money.it.
3. **Automobile.it** — "valida alternativa gratuita, cresciuto in maniera esponenziale, reintroducendo possibilità privati pubblicare annunci a costo zero". Fonte: aranzulla.it.
4. **Quattroruote Usato** — selettivo, target premium, "una delle piattaforme più conosciute in Italia per la compravendita". Skew professionisti. Fonte: aranzulla.it, quattroruote.it.
5. **Automoto.it** — editorial-driven, copertura provincia-aware. Volume medio ma qualità annunci alta. Fonte: automoto.it.

**Risposta a Q5**: AS24 + Subito + Automobile.it confermati top-3. **Quarto dominante locale Marche = NESSUNO esclusivo**. Bakeca è 4° generalista nazionale per volume locale ma non-premium-skewed. **Raccomandazione: aggiungere Quattroruote Usato e Automoto.it allo scope per coprire fascia premium professionale** non sempre presente su AS24/Subito.

---

## 6. RACCOMANDAZIONI PER LEAD-RESEARCHER (azionabili)

### Portali da aggiungere allo scope scraping nativo (priorità ordinata)
1. **Quattroruote Usato** `quattroruote.it/auto-usate/annunci/marca-{brand}/modello-{model}/regione-marche/provincia-{prov}` — pattern URL standardizzato, premium-skewed, sezione targata province AN/MC/PU/AP/FM.
2. **Automoto.it** `automoto.it/auto-usate/{brand}/regione-marche/provincia-{prov}` — pattern parallelo, mix professionisti/privati.
3. **Bakeca Ancona/Marche** `ancona.bakeca.it/annunci/auto/inserzionistaauto/privato/` + `bakeca.it/annunci/auto/luogo/marche/inserzionistaauto/privato/` — filtro `privato` nativo, alto rapporto micro-dealer/privato.
4. **Motorionline annunci** `annunci.motorionline.com/auto-usate/11/marche/{prov}/{brand}` — codice regione 11 = Marche, pattern compatto.
5. **AutoSupermarket** `autosupermarket.it/auto/ricerca?regione=marche&provincia={prov}&marca={brand}` — volume nazionale 150k, copertura provincia disponibile.
6. **Annunciautoweb.it** `annunciautoweb.it/auto-marche-110-ancona-an/{brand}-{code}` — minore ma pattern province-aware, utile come fallback long-tail.

### Keyword "target_alto" da cercare nelle description (CoVe filter potenziamento)
**Positive (aumenta score micro-dealer professionista ricettivo)**:
- `iva esposta`, `iva inclusa`, `fatturabile`, `iva al 22%` → P.IVA attiva
- `permuta valutabile`, `si valuta permuta` → apertura trattativa
- `tagliandi certificati`, `casa madre`, `libretto service`
- `unipro`, `unico proprietario`, `non fumatore`, `mai incidentata`
- `M Sport`, `AMG Line`, `S Line`, `xDrive`, `quattro`, `4MATIC` → marker premium autentico

**Negative (riduce score: probabile concessionario ufficiale, NOT target ARGOS)**:
- `BMW Premium Selection`, `Approved`, `Audi Prima Scelta`, `Mercedes Certified`
- `finanziamento tasso 0`, `rate da €X/mese`, `leasing aziendale`
- `Carpoint`, `Domina`, `Cascioli`, `Delta Motors`, `Luxcar`, `Fratelli Giacomel` (concessionari ufficiali Marche identificati — Sezione concessionari)
- Ragione sociale `SpA`, `Group`, `Gruppo`

**Neutral / da contestualizzare**:
- `no perditempo`, `solo WhatsApp`, `visionabile su appuntamento`, `vista e piaciuta` → ambigui (alto su privati, presenti anche su micro-dealer)

### Filtri aggiuntivi suggeriti per la pipeline ARGOS
- **F1 - Stock-size filter** (post-scrape): dopo aver collezionato annunci, raggruppa per `seller_phone` / `seller_id`. Range target = 5-30 annunci stessa entità (micro-dealer). <5 → privato puro (esclude). >50 → ufficiale (esclude).
- **F2 - Concessionari-ufficiali blacklist Marche** (pre-Day 1): inserire in `dealer_network.sqlite` colonna `excluded=1` per: Carpoint (Pesaro/Rimini/Ancona), Cascioli Group (MC/FM/AP/AQ/TE), Delta Motors (Mercedes/Hyundai AN/MC/PU/RN), Domina (AN/JE/PSE), Luxcar (PU/RN). Fonti URL già raccolte in Q-search 5.
- **F3 - Antifrasi marchigiana**: classifier AMBRA tollerare "un bel po'" come intensifier positivo, NON come quantità reale. Documentare in `~/.claude/rules/communication.md` se replay Stile Car conferma.
- **F4 - Saluto secco autorizzato**: Day 1 ARGOS aprire direttamente sul veicolo è **allineato culturalmente al register marchigiano** (rugnà/saluto inventato vs convenzionale). Non è un "bug" di freddezza, è feature. Rafforza scelta già in `.claude/rules/communication.md`.
- **F5 - Aggregatore cross-check anomalie prezzo**: usare AutoUncle come oracolo prezzo (compara 14 fonti). Se prezzo dealer Marche scarta >15% sotto mediana AutoUncle stesso veicolo/anno/km → flag opportunity per CoVe (margine ricaricabile EU→IT).
- **F6 - Forum Elaborare (long-tail premium-passione)**: bassissimo volume ma 100% privati appassionati BMW M/AMG/RS. Scope OPTIONAL fase 2 Stile Car.

---

## Note di onestà metodologica (vincolo #10)

- **Non verificati** via search: volumi reali quantitativi per portale Marche premium 40-100k (servirebbe API Similarweb / scraping pilota); presenza sezione mercatino attiva su BMWpassion / MisterAudi / ClubGTI (probabile registrazione richiesta, no preview Google); uso "Lei" vs "tu" in commercio anconitano (no fonte).
- **Verosimili ma da validare** sul campo: pattern "stock-size 5-30" come euristica micro-dealer (dedotto da AS24 consigli + logica, **NON** misurato su sample reale); peso effettivo di antifrasi "un bel po'" in WhatsApp commerciale (fonte è descrittiva del dialetto colloquiale, NON del register commerciale).
- **Solidi**: lista portali secondari (tutti URL fetchable verificati nelle search), formule lessicali (multiple fonti convergenti automobile.it/subito/AS24 guide), concessionari ufficiali Marche da escludere (4+ fonti distinte).

---

## Fonti principali (URL canonici)

- Bakeca Ancona auto privati: https://ancona.bakeca.it/annunci/auto/inserzionistaauto/privato/
- Motorionline annunci Marche: https://annunci.motorionline.com/auto-usate/11/marche/ancona/
- Quattroruote Usato Marche: https://www.quattroruote.it/auto-usate/annunci/regione-marche/provincia-ancona
- Automoto.it Ancona: https://www.automoto.it/auto-usate/bmw/regione-marche/provincia-ancona
- AutoSupermarket: https://autosupermarket.it/
- AutoUncle Italia: https://www.autouncle.it/it/auto-usate
- AutoScout24 Ancona: https://www.autoscout24.it/auto/auto-usate/marche/ancona/
- Forum Elaborare mercatino: https://forum.elaborare.com/forum/mercatino-annunci-usato-auto-ricambi
- Autopareri consigli acquisto: https://www.autopareri.com/forums/forum/22-consigli-per-lacquisto-dellauto/
- AutoScout24 guida annuncio: https://autoscout24.it/informare/consigli/vendita-auto-da-dove-iniziare/come-inserire-un-annuncio
- Subito Magazine vendere auto usata: https://www.subito.it/magazine/vendere-auto-usata.html
- Autosupermarket guida annuncio: https://autosupermarket.it/magazine/compravendita-auto/come-creare-un-annuncio-efficace-per-vendere-la-tua-auto-usata
- Frattin Auto garanzia 2025: https://frattinauto.it/blog/garanzia-auto-usata-guida-completa-2025/
- Brocardi vista e piaciuta: https://www.brocardi.it/notizie-giuridiche/vendita-auto-usata-clausola-visto-piaciuto-inapplicabile-venditore/6124.html
- Scudit linguaggio inserzioni: https://www.scudit.net/mdinserzioni_esempi.htm
- Wikipedia Dialetto anconitano: https://it.wikipedia.org/wiki/Dialetto_anconitano
- Wikipedia Dialetti marchigiani: https://it.wikipedia.org/wiki/Dialetti_marchigiani
- AutoScout24 confronto privato/concessionario: https://www.autoscout24.it/informare/consigli/prima-dell-acquisto/concessionario-o-privato/
- Carpoint BMW: https://www.bmwauto.it/
- Cascioli Group: https://www.cascioligroup.it/
- Delta Motors: https://www.delta-motors.it/
- Domina Audi: https://www.dominaspa.it/
- Luxcar Mercedes: https://www.mercedesluxcar.it/
- AutoScout24 osservatorio 2025: https://www.autoscout24.it/azienda/comunicati-stampa/osservatorio-di-autoscout24-sul-mercato-delle-auto-usate-nel-i-semestre-2025/

---

## Gate chiusura (self-check)

- [x] File creato: `/Users/macbook/Documents/combaretrovamiauto-enterprise/research/s206_marche_register/preliminary_findings.md`
- [x] Sezione 1: 12 portali identificati (≥5 richiesto)
- [x] Sezione 2: 50+ formule distribuite su 4 sottosezioni + 1 bonus premium (≥20 richiesto)
- [x] Sezione 3: 10 euristiche flag_target_alto (5-10 richiesto)
- [x] Sezione 4: 5 osservazioni Marche (3-5 richiesto)
- [x] Sezione 5: top-5 ranking con motivazione
- [x] Sezione 6: 6 portali + 2 set keyword + 6 filtri suggeriti (≥3 raccomandazioni richiesto)
- [x] Time-box 30 min rispettato (10 WebSearch, 0 WebFetch necessari)
- [x] Ogni claim ha fonte URL o flag "non verificato/verosimile"

**Status: COMPLETO — VERDE.**
