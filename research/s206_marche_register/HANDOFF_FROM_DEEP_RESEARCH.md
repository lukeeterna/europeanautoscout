# Handoff deep-research → lead-researcher
Data: 2026-05-30
Fonte: research/s206_marche_register/preliminary_findings.md (web-research 30 min, 10 WebSearch, 0 WebFetch)

> **Lead-researcher**: leggi questo file PRIMA di chiudere lo scope. Contiene portali aggiuntivi, keyword di filtro CoVe-like, blacklist concessionari ufficiali, e euristiche flag_target_alto da iniettare nei tuoi output. Non duplichi lavoro: integri.

---

## 1. Portali da AGGIUNGERE allo scope scraping nativo (oltre AS24/Subito/Automobile.it)

Priorità ordinata. Pattern URL province-aware verificato via search.

1. **Quattroruote Usato** — `quattroruote.it/auto-usate/annunci/marca-{brand}/modello-{model}/regione-marche/provincia-{prov}` — premium-skewed, sezione targata province AN/MC/PU/AP/FM.
2. **Automoto.it** — `automoto.it/auto-usate/{brand}/regione-marche/provincia-{prov}` — mix professionisti/privati.
3. **Bakeca Ancona/Marche** — `ancona.bakeca.it/annunci/auto/inserzionistaauto/privato/` + `bakeca.it/annunci/auto/luogo/marche/inserzionistaauto/privato/` — filtro `privato` nativo, alto rapporto micro-dealer.
4. **Motorionline annunci** — `annunci.motorionline.com/auto-usate/11/marche/{prov}/{brand}` — codice regione 11 = Marche.
5. **AutoSupermarket** — `autosupermarket.it/auto/ricerca?regione=marche&provincia={prov}&marca={brand}` — volume nazionale, copertura provincia.
6. **Annunciautoweb.it** — `annunciautoweb.it/auto-marche-110-ancona-an/{brand}-{code}` — minore, fallback long-tail.

**Non target Discovery primaria (solo cross-check prezzo)**: AutoUncle (aggregatore 14 fonti, 800k veicoli) — utile come oracolo anomalie prezzo per CoVe, NON come sorgente listing.

**Da verificare in autonomia se hai tempo**: BMWpassion / MisterAudi / ClubGTI mercatini — probabile registrazione richiesta, no preview Google.

---

## 2. Keyword per `flag_target_alto` (da cercare nelle description estratte)

### Positive (aumenta score micro-dealer professionista target)
- `iva esposta`, `iva inclusa`, `fatturabile`, `iva al 22%` → P.IVA attiva
- `permuta valutabile`, `si valuta permuta` → apertura trattativa
- `tagliandi certificati`, `casa madre`, `libretto service`
- `unipro`, `unico proprietario`, `non fumatore`, `mai incidentata`
- `M Sport`, `AMG Line`, `S Line`, `xDrive`, `quattro`, `4MATIC` → marker premium autentico

### Negative (riduce score: concessionario ufficiale, NON target ARGOS)
- `BMW Premium Selection`, `Approved`, `Audi Prima Scelta`, `Mercedes Certified`
- `finanziamento tasso 0`, `rate da €X/mese`, `leasing aziendale`
- Ragione sociale `SpA`, `Group`, `Gruppo`

### Neutral (ambigui)
- `no perditempo`, `solo WhatsApp`, `visionabile su appuntamento`, `vista e piaciuta`

---

## 3. Blacklist concessionari ufficiali Marche (escludi prospect_list.csv)

Inserire `flag_target_alto=NO` + nota `BLACKLIST_UFFICIALE`:

- **Carpoint** (BMW — Pesaro/Rimini/Ancona) — bmwauto.it
- **Cascioli Group** (multi-brand — MC/FM/AP/AQ/TE) — cascioligroup.it
- **Delta Motors** (Mercedes/Hyundai — AN/MC/PU/RN) — delta-motors.it
- **Domina** (Audi — AN/JE/PSE) — dominaspa.it
- **Luxcar** (Mercedes — PU/RN) — mercedesluxcar.it
- **Fratelli Giacomel** (citato come Audi ufficiale)

---

## 4. Euristiche flag_target_alto da popolare nel CSV

Algoritmo di assegnazione `flag_target_alto = SI` se ≥3 condizioni vere:

1. Telefono cellulare 3xx come unico contatto (no centralino 07x)
2. Stock visibile 5-30 veicoli stessa entità (raggruppa per `seller_phone` o `seller_id`)
3. IVA esposta o "fatturabile" nel testo
4. Nome operatore = persona singola (no SpA/Group/Gruppo)
5. Indirizzo via residenziale + numero civico
6. Foto piazzale piccolo / cortile non-branded (no logo BMW/Mercedes/Audi)
7. Descrizione 5-15 righe schematica con mix di keyword Positive sezione 2
8. NON in blacklist sezione 3

Se ≥6 condizioni vere → `flag_target_alto = SI_PRIORITARIO` (campione gold per Luke).

---

## 5. Specificità register marchigiano (per `corpus_register.md` sezione 4 opzionale)

- Register commerciale Ancona ≈ italiano standard con sfumatura toscano-aulica. NO dialetto stretto.
- Antifrasi "un bel po'" = molto (litote tipica).
- Saluti convenzionali ("Buongiorno") possono sembrare fuori-register. Apertura diretta sul veicolo è culturalmente coerente (rinforza `.claude/rules/communication.md`).
- Marker autenticità: "gustà" / "dà gusto" = piacere intensamente (se compare in risposta dealer).
- "Lei" vs "tu": NON verificato. Default "Lei" coerente con persona Luca Ferretti.

---

## 6. Output deliverable suggerito al lead-researcher

Aggiungere a `EXECUTION_REPORT.md` una sezione:

```markdown
## Integrazione findings deep-research preliminary_findings.md
- Portali aggiunti: [lista effettivamente scrapata]
- Portali skip: [lista con motivazione: ban/captcha/dataset insufficiente]
- Blacklist applicata: [N concessionari ufficiali esclusi su N totali in blacklist]
- Keyword Positive trigger count: [top-10 keyword più frequenti corpus]
- Keyword Negative trigger count: [keyword ufficiali viste = candidati escludibili]
```

---

## Vincoli ricordati
- Time-box totale lead-researcher: 3h. Se a 2.5h sotto gate → scope-cut AN+PU dichiarato.
- No push su master. Branch `s206/marche-register`.
- Nessun contatto operatori (Luke chiama a mano).
- Idempotenza CSV (re-run no duplica).
