# ARGOS — Architettura di sistema end-to-end
### sourcing → verifica → profilazione → outreach → vendita
**Versione:** 1.0 · **Data:** 2026-06-20 · **Ruolo doc:** blueprint da architetto (CC esegue per fasi)

> Questo documento progetta il **100% del sistema richiesto**. La sezione 5 (ordine di
> build) NON taglia nulla dal design: definisce solo la **sequenza di costruzione per
> dipendenza**. È la parte da architetto — alcuni pezzi non funzionano senza altri, e
> costruirli nell'ordine sbagliato è il modo in cui un progetto si impantana.
>
> **Fonte di verità resta il disco.** Questo è un blueprint, non uno stato. Ogni "esiste
> già" va verificato da CC contro git prima di costruirci sopra.

---

## 0. Scopo e confini

**Cosa fa il sistema.** Arbitraggio B2B di auto usate EU→IT. Trova auto premium sottoprezzo
sui canali europei → le verifica allo *standard ARGOS* → le abbina a micro-dealer italiani
**profilati** → li contatta con Azzurra (assistente automatica dichiarata di Luca Ferretti)
proponendo un **margine credibile** → success-fee sulla transazione.

**Confine GDPR (requisito di design, non morale).** La profilazione (S4) ingerisce **solo
dati commerciali pubblici**: cosa stocca il dealer, prezzi, anzianità annunci, brand, gap a
listino. **Mai dati personali**, mai OSINT su persone fisiche. Motivo tecnico: così la
profilazione resta dentro l'envelope "rischio accettato" già deciso sul canale cold-WA, e
**fuori dall'Art. 9 / dal balancing test pesante** che un profiling di individui aprirebbe.
Un dealer è un'attività commerciale: il suo inventario pubblico su AutoScout24 è dato
commerciale, non personale. Questo confine è cablato nel collector S4.

---

## 1. Vista d'insieme — i 7 sottosistemi

```
 [S1 SUPPLY]                          [S4 DEALER PROFILING]
  raccolta canali EU                   intelligence pre-outreach
  → pool veicoli grezzi                → profilo commerciale dealer
        │                                       │
        ▼                                       │
 [S2 VERIFICATION]                              │
  standard ARGOS + gap-filling agent            │
  → veicolo CERTIFICATO                         │
        │                                       │
        ▼                                       ▼
 [S3 PRICING] ──────────────────────► [S6 MATCHING]
  dossier onesto                       dealer × supply
  (Gate D = base fidata)               → "quale auto a quale dealer"
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                 [S5 AZZURRA]
                  sector wiki + outreach + conversazione + sequencer
                  → Day-1 personalizzato → trattativa
                        │
                        ▼
                 [S7 CONTROL PLANE]   (VOS · Gate-E · state machine · scheduler)
                  attraversa tutti i sottosistemi
```

**Lettura del grafo:** due ingressi indipendenti — **S1** (l'offerta: auto trovate in EU) e
**S4** (la domanda: dealer profilati). Si incontrano in **S6** (matching). Il dossier credibile
(**S3**) e la voce esperta (**S5**) sono ciò che trasforma un match in una vendita. **S7** è
il control-plane che già esiste.

---

## 2. Sottosistema per sottosistema

### S1 — SUPPLY / Acquisizione canali EU
**Cosa fa.** Trova auto candidate sui canali europei, normalizzate in uno `Vehicle` comune.

**Componenti.**
- **Channel Registry** (`config/channels.yaml`) — ogni canale con: `country`, `type`
  (`dealer_marketplace | private_listing | wholesale_auction | aggregator`), `url`,
  `anti_bot_level` (low/med/high), `poll_cadence`, `status`
  (`LIVE | DA_VERIFICARE | MANUAL_ASSIST`), `method` (`scraper | api | aggregator`).
- **Collectors** — un collector per canale/aggregatore. Output → schema `Vehicle` normalizzato.
- **Freshness Scheduler** — poll per cadenza, dedup (`hash(VIN|prezzo|km)`), flag "nuovo dall'ultimo run" per non riprocessare lo stock vecchio.

**Esiste già.** Scraper AutoScout24 (geo==IT corretto su `location.countryCode`, experiment-OFF, pool p25-p75). Copre già supply pan-EU dei marketplace dealer.

**⚠ Decisione da architetto — BUILD vs BUY (nodo aperto, scelta economica = tua).**
Su hardware 2012 + solo founder + ~€240/mese, mantenere **28 scraper anti-bot freschi per
sempre non regge**: AS24, mobile.de, leboncoin montano Cloudflare/DataDome, cambiano DOM,
bannano IP. Esistono aggregatori commerciali (AutoUncle, AutoSourcer, Carapis API) che già
scansionano 28 paesi ogni 5-15 min. La scelta sana è **ibrida**: scraper proprietari sui 2-3
canali **core** (dove serve profondità e controllo — AS24 + mobile.de), **API aggregatore**
sui canali di coda. Non lo decido io perché è una scelta di costo, non tecnica: la metto come
nodo esplicito da chiudere in Fase 5.

### S2 — VERIFICATION / Standard ARGOS + gap-filling agent
**Cosa fa.** Stabilisce se un'auto è reale, sana, completa e **presentabile**.

**Componenti.**
- **CoVe engine** (esiste, v4 Factored+Bayesian) — punteggio qualità.
- **VIN decode** (Vincario, configurato) — decodifica + check frodi.
- **ARGOS Standard** (`config/argos_standard.yaml`, spec versionata) — i campi **obbligatori**
  perché un veicolo sia presentabile: VIN, km verificati (revisione/TÜV), storico tagliandi,
  stato danni, n° proprietari, foto HD, prezzo aggiornato. Una checklist falsificabile.
- **Gap-Filling Agent** ("l'agent che parla"). Input: record incompleto + lista campi mancanti.
  Genera domande **mirate** alla fonte (dealer/venditore EU) per completare il record
  (es. "VIN completo? Tagliandi in concessionaria? Foto del vano motore?"). Output: messaggio
  di richiesta → parsing risposta → record completato **oppure** marcato `NON_COMPLETABILE`.
  Stessa disciplina di Azzurra: niente claim inventate, disclosure automatica.

**Manca.** La checklist `argos_standard.yaml` come spec versionata + il gap-filling agent.

### S3 — PRICING / Dossier onesto
**Cosa fa.** Il numero **credibile** (banda + margine) oppure l'onesto "comparabili insufficienti".

**Esiste già + indurito.** G1 (thin-pool → dossier degradato, **mai banda finta**), bande
p25-p75 (non punto), margine come intervallo, NO-VERDICT, break-even derivato.

**🔴 Blocco aperto = Gate [D].** Base-mercato IT **fidata**: scrape esaustiva `DEEP_PAGES≥80`
fino a pagina vuota, experiment-OFF, geo==IT, + ADD-1 (la config-esatta è davvero thin o era
artefatto del cap?). **Senza [D], il margine non è credibile davanti a un dealer reale.** È il
gate-3 a un dealer reale.

### S4 — DEALER PROFILING  ⟵ *il layer che manca, causa dell'"outreach alla cieca"*
**Cosa fa.** Intelligence commerciale sul dealer **prima** di contattarlo. È il fattore che i
dati indicano come il maggior moltiplicatore di conversione (personalizzazione oltre il nome
≈ +340% reply rate; sotto il 3% di reply il problema è rilevanza, non volume).

**Componenti.**
- **Dealer Registry** (`data/dealers.db`) — anagrafica target: nome, URL pagina-dealer AS24,
  sito, brand trattati, fascia prezzo, n° annunci attivi, anzianità media listing, snapshot
  inventario.
- **Profiling Collector** — scrapa l'impronta **commerciale pubblica** del dealer: la sua
  **pagina-dealer AS24** (= il suo inventario reale), il sito, la pagina FB business.
  **Solo dati commerciali** (confine §0).
- **Gap Analysis** — cosa il dealer **non** stocca che ARGOS può procurare (es. "tratta
  BMW/Audi, zero diesel premium 2020+ → ARGOS ne ha 3 dalla Germania a margine X").
- **Personalization Payload** — il pacchetto che alimenta Azzurra: `nome`, `brand_focus`,
  `gap`, `match_disponibili`, `provenienza` (come l'ho trovato).

**Manca interamente.** Ma **riusa la tecnologia scraper di S1** — è scraping di pagine AS24,
problema già risolto. Per questo è la fase più economica ad alta leva.

### S5 — AZZURRA / Sector wiki + outreach + conversazione
**Cosa fa.** Parla col dealer come una **che capisce il mestiere**; apre, gestisce le risposte,
porta alla trattativa.

**Componenti.**
- **Sector Wiki** (`kb/azzurra/`) — la KB di dominio che rende Azzurra esperta: come ragiona un
  dealer dell'usato, margini tipici del premium, gergo, **obiezioni classiche + risposte**,
  l'iter di vendita, fiscalità (reverse charge intra-UE, immatricolazione IT, IPT), rischi del
  mestiere (km clonati, sinistri occultati, garanzia costruttore cross-border). **È la wiki che
  chiedi da mesi.** Strutturata in moduli interrogabili, non un blob.
- **Day-1 Generator** (esiste, G2, offline, firma Azzurra) — ora **personalizza** SE alimentato
  dal payload S4.
- **Conversation Engine** (AMBRA classifier esiste) — gestione risposte, disclosure runtime
  ("sono automatica" se interrogata), routing intent.
- **Multi-touch Sequencer** — i follow-up (i dati: 8-12 touchpoint per chiudere un meeting a
  freddo; il singolo messaggio ha probabilità bassa per costruzione), cadenza, opt-out, stop-rules.

**Manca.** La sector wiki + il sequencer multi-touch. Day-1 e classifier esistono in seed.

### S6 — MATCHING / domanda × offerta
**Cosa fa.** Abbina il profilo-dealer (cosa gli serve) al pool-supply verificato (cosa ARGOS ha).

**Componenti.** Motore di match: `brand × fascia_prezzo × gap_dealer` contro veicoli
`CERTIFICATO` disponibili → "questa auto, a questo dealer, con questo margine". Alimenta sia S4
(gap→match) sia S5 (cosa pitchare). Scoring di rilevanza per ordinare i pitch.

**Manca.** Dipende da S1 (pool supply) + S4 (profili) già esistenti.

### S7 — CONTROL PLANE  *(esiste)*
VOS (RESEARCH→PLAN→EXECUTE→MEASURE), Gate-E (chokepoint azioni irreversibili), state machine
anelli E2E, freshness scheduler, single-writer per branch, tag `MANDATO:`. Attraversa tutto.

---

## 3. Registro canali EU (grounded)

**Pan-EU dealer (dove sta il target BMW/Mercedes/Audi 2018-2023):**

| Canale | Paesi | Tipo | Stato / anti-bot |
|---|---|---|---|
| **AutoScout24** | TUTTI (DE/NL/BE/AT/FR/IT…) | dealer + private | **LIVE (già scrapato)** · medio |
| **mobile.de** | DE #1 | dealer + private | DA_VERIFICARE · alto (DataDome) |

**Per-paese (private + dealer) — fonte di supply di coda:**

| Paese | Canali principali |
|---|---|
| DE | Kleinanzeigen · mobile.de · AS24.de |
| FR | leboncoin (#1, ~33M traffico) · LaCentrale · ParuVendu · AS24.fr |
| NL | Marktplaats (#1) · Gaspedaal (aggregatore) · AutoTrack |
| BE | 2dehands / 2ememain · AS24.be |
| AT | willhaben (#1) · AS24.at |
| SE | Blocket (#1) · Bilweb |
| CZ | Sauto.cz · TipCars |
| ES | coches.net · Milanuncios · Wallapop · Autocasion |
| PT | StandVirtual (OLX) · Custo Justo |
| DK | DBA.dk · Bilbasen |
| NO / FI / IE / PL | Finn.no · Nettiauto · DoneDeal · Otomoto |

**Wholesale / dealer-to-dealer auction (lato COSTO — qui sta il margine vero):**
AUTO1 / CarOnSale · BCA Europe · AUTOproff/Autorola · Autobid.de · OPENLANE (ex-ADESA) · CarNext.
*(Già seed in ARGOS [C]. Modellati come canale d'acquisto, MAI come comparabile di mercato.)*

**Aggregatori pan-EU (per il nodo build-vs-buy di S1):** AutoUncle · Gaspedaal · AutoSourcer · Carapis (API).

---

## 4. Schema dati comune (i contratti tra sottosistemi)

```yaml
Vehicle:            # output S1, input S2/S3/S6
  vin: str | null
  source_channel: str          # es. "autoscout24.de"
  source_url: str
  make, model, year, km: ...
  price_eu: float              # IVA esclusa (reverse charge intra-UE)
  fuel, gearbox, owners: ...
  photos: [url]
  raw_fields: {...}            # tutto il grezzo per il gap-filling
  first_seen, last_seen: date  # per freshness/dedup

ArgosStandard:      # spec S2 (versionata)
  required: [vin, km_verified, service_history, damage_status, owners, photos_hd, price_fresh]
  status: COMPLETO | DEGRADATO | NON_COMPLETABILE

Dealer:             # registry S4
  id, name: str
  as24_dealer_url: str         # = il suo inventario pubblico
  site, fb_business: str | null
  brands: [str]
  price_band: [min, max]
  active_listings: int
  avg_listing_age_days: float
  inventory_snapshot: [Vehicle-lite]

DealerProfile:      # output S4, input S5/S6
  dealer_id: str
  brand_focus: [str]
  gaps: [str]                  # cosa NON stocca e ARGOS può procurare
  matched_vehicles: [vehicle_id]
  provenance: str              # "trovato su AS24, dealer pagina X"
  personalization_payload: {...}   # alimenta il Day-1

Match:              # output S6
  dealer_id, vehicle_id: str
  margin_band: [min, max] | NO_VERDICT
  relevance_score: float
  rationale: str
```

---

## 5. Percorso critico — ordine di build (per dipendenza)

**Principio.** Costruire il **loop che può chiudere UN affare**, validarlo, **poi** la breadth.
Costruire breadth prima = il rischio #1 documentato (macchina infinitamente rifinita che non
spedisce). Questo NON è una preferenza: è dipendenza.

**Fatti di dipendenza che fissano l'ordine:**
1. **AS24 (già scrapato) copre già la supply premium pan-EU** (DE/NL/BE/AT su un solo canale).
   Per trovare **UNA** buona BMW per **UN** dealer **non servono** leboncoin + willhaben + 28
   scraper. → La breadth canali (S1 esteso) è **scala**, non validazione.
2. Il moltiplicatore di conversione (dati) è **S4 profiling** (+340%), ed è anche il **più
   economico** (riusa lo scraper AS24). → Prima leva da tirare.
3. Quando un dealer dice "ok fammi vedere" serve **S3/Gate[D]** (numero credibile). Oggi il
   dossier è degradato. → Secondo gate.
4. La **sector wiki S5** serve quando **rispondono** (per non sembrare bot). → Prima della scala,
   non prima del primo reply.

| Fase | Cosa si costruisce | Perché qui | Riusa |
|---|---|---|---|
| **1** | **S4 Dealer Profiling** | layer mancante, leva massima, costo minimo; risolve "alla cieca" | scraper AS24 |
| **2** | **S3 Gate [D]** base-mercato fidata | il numero credibile per quando rispondono; F1+F2 = prodotto reale | scraper AS24 |
| **3** | **S5 Sector Wiki** | Azzurra esperta prima di scalare le conversazioni | KB infra esistente |
| **4** | **S6 Matching** | domanda × offerta, una volta che profili+supply esistono | S1+S4 |
| **5** | **S1 breadth (28 canali) + S2 gap-filling agent** | breadth e profondità, costruiti quando il loop converte; qui il nodo build-vs-buy | aggregatori/API |

> **Sulla Fase 5 (i 28 scraper che vuoi):** è in fondo **non perché conta meno**, ma perché AS24
> ti dà **già** supply per validare, e costruire 28 scraper anti-bot **prima** che UN dealer
> voglia UN'auto è costruire offerta per domanda non ancora validata. Il giorno che il loop
> converte, la breadth diventa la priorità #1 e si apre con i dati in mano (e con la scelta
> build-vs-buy informata dal costo reale di manutenzione visto in Fase 1).

---

## 6. Fase 1 — specifica del primo work item (S4 Dealer Profiling MVP)

**Obiettivo:** da "Day-1 generico alla cieca" a "Day-1 con un dato vero e verificato sul dealer".

**Done-condition (falsificabile, sul render reale):**
1. `data/dealers.db` con ≥1 dealer reale profilato da scrape AS24 (pagina-dealer pubblica).
2. `DealerProfile` popolato: `brand_focus`, `active_listings`, `avg_listing_age`, **almeno 1
   `gap`** derivato dal suo inventario reale.
3. Day-1 generato che **inserisce un dato specifico del profilo** (non l'inferenza generica
   "lavora con BMW e Mercedes, giusto?" ma un fatto: es. "ho visto che ha N annunci, forte su
   X, ma vedo poco Y").
4. Confine GDPR rispettato: il collector estrae **solo** dati commerciali, **zero** campi
   personali. Verificabile leggendo cosa salva nel DB.
5. `grep` superlativi sul Day-1 = 0; firma Azzurra + opt-out + provenienza presenti.

**Vincoli:** riusa lo scraper AS24 esistente (non riscrivere); single-writer; nessun invio
(solo generazione + profilo); il test gira su un dealer reale **come fonte dati pubblica di
profilazione**, l'eventuale invio resta a TEST_FOUNDER e dietro Gate-E.

---

*Fine documento. La sezione 6 è il prossimo lavoro per CC. Le sezioni 2-5 sono il blueprint
completo da cui derivare i work item successivi, una fase alla volta, con la disciplina solita
(verifica contro git, MANDATO tag, done-condition esterna).*
