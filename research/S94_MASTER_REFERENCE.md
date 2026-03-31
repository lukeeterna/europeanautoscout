# S94 MASTER REFERENCE — ARGOS AUTOMOTIVE
## Pivot Strategico: dal dealer con stock al dealer su commissione
**Data:** 2026-03-31 | **Sostituisce:** S73_MASTER_REFERENCE.md

---

## 0. IL PIVOT IN 30 SECONDI

Il target ARGOS NON e' piu' il concessionario con 15-30 auto sul piazzale.
Il target e' il **piccolo operatore che lavora su commissione**: il cliente gli chiede un'auto specifica, lui la cerca. Oggi cerca su Mobile.de con Google Translate, impiega 20-40 ore, rischia km scalati, e paga €1.700-2.500 di costi import. ARGOS gli fa tutto in 24h a €800-1.200, success-fee.

**Perche' il pivot:** i dealer con stock hanno gia' canali strutturati. Senza referenze, ARGOS non entra. Il dealer su commissione invece ha BISOGNO URGENTE di ARGOS — ha il cliente che aspetta ORA.

---

## 1. IL TARGET — CHI E', DOVE TROVARLO

### 1.1 Profilo tipo
```
Nome:           "Salonista" o "commerciante" (nessun termine unico)
ATECO:          45.11.01 (commercio) o 45.11.02 (intermediazione)
Eta':           35-55 anni
Sede:           Piazzale 200-500 mq, zona semi-periferica
Auto in stock:  3-10 (mix proprie + conto vendita)
Dipendenti:     0-2 (moglie/fratello/figlio)
Volume:         8-20 auto/mese
Margine:        €500-1.500/auto locale, €2.000-4.500/auto import EU
Import EU:      1-3 auto/mese, fatto a mano su Mobile.de
Clientela:      Tutta locale, raggio 20-50 km, 80% passaparola
```

### 1.2 Come riconoscerli online
| Segnale | Dove | Affidabilita' |
|---------|------|---------------|
| Pochi annunci (3-10) con rotazione alta | Subito/AS24 | ALTA |
| Annunci eterogenei (BMW+Fiat+Audi) | Portali | ALTA |
| Foto da cellulare, sfondo diverso per auto | Portali | MEDIA |
| "Su richiesta cerchiamo..." in descrizione | Sito/FB | ALTA |
| Pagina Facebook con foto consegne clienti | Facebook | ALTA |
| Google Maps con 5-20 recensioni, 4.5+ | GMaps | MEDIA |
| Indirizzo in zona residenziale | GMaps | ALTA |

### 1.3 Dove trovarli (in ordine di efficacia)
1. **Subito.it** — profili PRO con 3-10 annunci, shop su impresapiu.subito.it (AUTOMABILE)
2. **AutoScout24.it** — /concessionari/ per provincia, filtro per pochi annunci (AUTOMABILE)
3. **Google Maps** — "autosalone" + citta', scrappabile con Playwright (AUTOMABILE)
4. **Facebook** — pagine business locali, gruppi dealer (MANUALE)
5. **Agenzie pratiche auto** — conoscono TUTTI i commercianti della zona (REFERRAL)
6. **Passaparola** — il primo dealer convertito conosce 5-10 colleghi (POST-PRIMO-DEAL)

### 1.4 Numeri
| Dato | Valore | Fonte | Confidenza |
|------|--------|-------|------------|
| Imprese commercio auto Italia | 53.226 | Creditsafe 2024 | HIGH |
| Campania tra top 3 regioni | Confermato | Creditsafe | HIGH |
| Stima operatori commissione Sud | 2.500-4.000 | Cross-fonti | MEDIUM |
| Target fit ARGOS (premium, <55, provincia) | 600-950 | Extrapolazione | LOW |
| Trovabili via scraping nelle 8 province | 25-40 | Stima discovery | LOW |
| Passaggi proprieta' Italia 2024 | 5.400.000 (+7,4%) | UNRAE | HIGH |
| Import da Germania | 33-36% delle importate | carVertical | HIGH |

---

## 2. IL VALORE ARGOS — NUMERI CONCRETI

### 2.1 Costo fai-da-te per il dealer (1 auto import)
| Voce | Costo | Tempo |
|------|-------|-------|
| Ricerca su Mobile.de/AS24 | - | 2-6 ore |
| Contatto venditore DE | - | 1-3 giorni |
| Verifica documenti | - | 2-4 ore |
| COC (Certificate of Conformity) | €149-300 | - |
| Trasporto (bisarca condivisa) | €600-1.200 | 7-15 giorni |
| IPT (Sud Italia, BMW X3) | ~€593 | - |
| Pratiche auto + revisione | €200-400 | 3-4 settimane |
| **TOTALE** | **€1.200-2.500** | **20-40 ore + 30-60 giorni** |

### 2.2 Delta prezzo EU→IT (verificato marzo 2026)
| Modello | Prezzo DE | Prezzo IT | Delta lordo |
|---------|-----------|-----------|-------------|
| BMW X3 xDrive20d 2022 45k km | €28.500 | €36.000 | €7.500 |
| Mercedes GLC 220d 2022 35k km | €34.400 | €42.000 | €7.600 |
| Audi Q5 40 TDI 2022 50k km | €26.000 | €33.000 | €7.000 |
| Porsche Macan 2021 40k km | €42.000 | €48.000 | €6.000 |

### 2.3 Margine netto dealer con ARGOS
```
Delta lordo medio:                    €6.500-7.500
- Costi import (COC+IPT+pratiche):    -€1.200-1.500 (ARGOS gestisce)
- Trasporto:                          -€600-1.200 (dealer gestisce)
- Fee ARGOS:                          -€800-1.200 (success-fee)
= MARGINE NETTO DEALER:              €3.000-4.500 per auto

vs margine auto usata locale:         €350/pezzo
Differenza:                           +900% (10x)
Tempo dealer con ARGOS:               0 ore (manda 1 WA)
```

### 2.4 Rischio frode (perche' la verifica CoVe vale)
| Dato | Valore | Fonte |
|------|--------|-------|
| Auto in Italia con km manomessi | 4.000.000 (11%) | carVertical 2025 |
| Auto importate con km falsificati | 7% (vs 3% locali) | carVertical |
| Riduzione media km | 69.800 km | carVertical |
| Danni nascosti (veicoli controllati) | 12,6% | carVertical |
| Valore medio danni nascosti | €7.100 | carVertical |
| Costo frode in Europa/anno | €9 miliardi | carVertical |

---

## 3. IL MODELLO DI BUSINESS — IBRIDO

### 3.1 Flusso operativo
```
FASE 0 — ATTIVAZIONE (proattiva, ARGOS inizia)
  Primo messaggio WA: veicolo REALE con numeri REALI dal suo segmento
  Scopo: dimostrare competenza, aprire la relazione

FASE 1 — TRANSIZIONE A ON-DEMAND (Day 3-7)
  "Ha un cliente che cerca una tedesca? Mi mandi marca/modello/budget."
  Il dealer invia richiesta via WA

FASE 2 — SHORTLIST (24h)
  ARGOS cerca su 73 portali EU → CoVe scoring → top 3 opzioni
  Formato WA: 3 opzioni con foto, prezzo, margine, score

FASE 3 — DOSSIER COMPLETO (48-72h)
  Dealer sceglie 1 → ARGOS prepara PDF enterprise
  Dealer presenta al cliente finale

FASE 4 — ACQUISTO + IMPORT (10-15 giorni)
  Dealer conferma → ARGOS gestisce acquisto + documenti
  Fee €800-1.200 alla consegna
```

### 3.2 Fee structure
| Fase | Fee | Quando |
|------|-----|--------|
| Primo dossier | €0 (gratuito) | Dimostra valore, zero rischio |
| Prime 3 transazioni | €800-1.200 success-fee | Paga solo a consegna |
| Partner (dopo 3+) | €500/mese per 3 ricerche | Dealer risparmia, ARGOS prevedibilita' |
| Premium | €800/mese illimitato | Dealer alto volume |

### 3.3 SLA
| Livello | Tempo | Output |
|---------|-------|--------|
| ACK | 2-4 ore | "Ricevuto, sto cercando" |
| Shortlist | 24 ore | 3 opzioni con prezzo/margine/foto |
| Dossier completo | 48-72 ore | PDF enterprise |
| Urgente ("cliente in showroom") | 4-6 ore | 2 opzioni rapide |

### 3.4 Competitor
| Competitor | Modello | Fee | Target | Gap vs ARGOS |
|-----------|---------|-----|--------|-------------|
| Bolidem | Cliente porta link | €1.597 upfront | B2C privati | Zero proattivita', B2C, upfront |
| Autotedesche.it | Cliente porta link | ~€300-600 | B2C privati | Fatturato €3,28M/2 dip. ma B2C |
| Importami.com | Cliente identifica | 4% min €750+IVA | B2C luxury | Upfront, B2C |
| AUTO1 | Marketplace self-service | Inclusa | B2B ma 10 anni + 62 filiali | Compra DAL dealer, non PER il dealer |
| "Collega con contatto in DE" | Informale | Variabile | B2B informale | Zero verifica, zero documenti |
| **ARGOS** | **Concierge on-demand** | **€800-1.200 success** | **B2B dealer Sud** | **Unico B2B success-fee + verifica** |

**Nessuna piattaforma B2B offre servizio concierge on-demand per dealer piccoli. Il gap e' completamente vuoto.**

---

## 4. COMUNICAZIONE — COME PARLARE AL TARGET

### 4.1 Linguaggio
```
USARE: "macchina/auto", "tedesca", "margine", "ci guadagna €X", "km certificati",
       "pezzo buono", "ci sta", "quanto ci vuole?", "i documenti li faccio io"
MAI:   "veicolo EU", "ROI", "pipeline", "piattaforma", "algoritmo", "scouting",
       "reimportazione", CoVe, RAG, Claude, AI, embedding
Numeri: SEMPRE in EUR netti, MAI percentuali
Golden: €2-3k "ci sta" | €4-6k "ottimo" | >€6k "non ci credo finche' non vedo"
```

### 4.2 Canali (ranking)
1. **WhatsApp** — primario per TUTTO (98% open, 40-60% response)
2. **Telefono** — Day 10+, "da persona seria"
3. **Di persona** — gold standard, necessario per primo deal senza referral
4. **Email** — solo per documenti formali, dopo accordo

### 4.3 Timing migliore
- **SI:** Martedi/Mercoledi 8:30-9:00 | Sabato 8:30-10:00 | 14:00-15:30
- **NO:** Lunedi mattina | 10:00-12:00 | Venerdi PM | Dopo le 19

### 4.4 Primo messaggio (l'UNICO modello che funziona)
```
Buongiorno [nome], sono Luca — cerco auto dalla Germania per concessionari del Sud.
Ho trovato una [marca modello anno km] a [citta' DE] a €[prezzo].
Margine stimato €[cifra netta] al netto di tutto.
Km certificati, documenti pronti, consegna [N] giorni a [citta' dealer].
Ha interesse? Le mando le foto.
```

**Regole:** Max 5 righe | 1 domanda chiusa | Zero link/allegati Day 1 | Zero fee | Zero presentazione lunga | Personalizzato sul SUO segmento

### 4.5 Sequenza touchpoint (aggiornata per on-demand)
```
Day 1:  Veicolo concreto dal SUO segmento + domanda chiusa (WA testo)
Day 3:  Secondo veicolo + bridge on-demand: "ha clienti che cercano tedesche?"
Day 7:  PDF allegato + FOMO lieve OPPURE bridge on-demand esplicito
Day 10: Vocale 20 sec personalizzato (WA voice)
Day 14: Case study / referral se disponibile
Day 21: Break-up gentile
Day 30: Telefonata o visita fisica (obbligatoria per Calabria/Sicilia)
```

### 4.6 Obiezioni
| Obiezione | Risposta |
|-----------|----------|
| "Lo faccio gia' da solo" | "Non le chiedo di smettere. Le risparmio 30 ore per auto. E i km li verifico io prima." |
| "Troppo caro" | "La ricerca le costa 20-40 ore + €1.700 di burocrazia. La mia fee e' €800 tutto incluso." |
| "Non mi fido" | "Primo dossier gratuito. Se non le piace, zero impegno." |
| "Chi ti ha mandato?" | [Specificita' chirurgica sul SUO stock] "Ho visto che tratta BMW/Audi. Ho 3 opportunita' dalla Germania che potrebbe rivendere domani." |
| "Mai sentito ARGOS" | "Sono Luca Ferretti, lavoro con concessionari del Sud. Le faccio vedere cosa trovo per lei, a costo zero. Poi decide." |

---

## 5. FIDUCIA — COME COSTRUIRLA DA ZERO

### 5.1 Il percorso obbligatorio (Sud Italia)
```
STEP 1: "Chi sei?"           → Persona reale (Luca Ferretti), trovabile su Google
STEP 2: "Chi ti ha mandato?" → Specificita' chirurgica sullo stock (surrogato del referral)
STEP 3: "Cosa hai fatto?"    → Track record (anche 1 solo deal completato)
STEP 4: "Cosa mi offri?"     → Solo DOPO i primi 3

SE SALTI UNO STEP, RICOMINCIA DA CAPO.
```

### 5.2 Credibilita' minima richiesta
- Google Business Profile con 5+ recensioni (il dealer cerca su Google)
- Sito web credibile (non bello, CREDIBILE)
- Persona reale con nome e volto trovabile
- 1 video testimonial vale piu' di 100 messaggi

### 5.3 Il primo dealer
- Vale 3-5 dealer via referral in 6-12 mesi (lead da referral convertono +70%)
- Trattarlo come INVESTIMENTO, non come cliente
- Primo dossier GRATUITO, servizio impeccabile
- Chiedere referral 2-3 settimane DOPO prima consegna riuscita
- Dove parlano tra loro: bar, distributore, fiere, gruppi WA

### 5.4 Differenze regionali
| Regione | Caratteristica | Approccio |
|---------|---------------|-----------|
| Campania | Relazionale, serve "conoscente" | Nome specifico in zona |
| Puglia | Pragmatica, numeri contano | Numeri chiari nel primo messaggio |
| Calabria | Sud profondo, fisicita' quasi obbligatoria | Visita fisica prevista |
| Sicilia | Relazioni lungo termine, cambio fornitore raro | Pazienza estrema, 6-12 mesi |

---

## 6. TRASPORTO — COSA DIRE AL DEALER

### 6.1 Opzioni (ARGOS informa, NON gestisce)
| Opzione | Costo | Tempo | Per chi |
|---------|-------|-------|---------|
| Fly & drive (volo+guida) | €350-500 | 1-2 giorni | Dealer che vuole risparmiare |
| Bisarca condivisa | €600-1.200 | 7-15 giorni | Standard |
| Trasporto dedicato | €1.000-1.500 | 3-5 giorni | "Il cliente ha fretta" |

### 6.2 Rotte principali
| Rotta | Fly & drive | Bisarca |
|-------|------------|---------|
| Monaco → Napoli | ~€362 | €600-800 |
| Francoforte → Bari | ~€420 | €650-850 |
| Amsterdam → Catanzaro | ~€480 | €800-1.100 |

### 6.3 Documento critico: COC
Il COC (Certificate of Conformity) e' il documento che fa la differenza tra immatricolazione facile (2 settimane) e incubo burocratico (2 mesi). ARGOS DEVE verificarlo PRIMA e segnalarlo nel dossier.

---

## 7. AUTOMAZIONE — COSA ESISTE, COSA SERVE

### 7.1 Infrastruttura operativa (gia' al 70%)
| Componente | Stato | Path |
|-----------|-------|------|
| WA daemon | OPERATIVO | wa-intelligence/wa-daemon.js |
| Response analyzer (LLM) | OPERATIVO | wa-intelligence/response-analyzer.py |
| Outreach scheduler | OPERATIVO (bug: non check risposta) | tools/outreach_scheduler.py |
| Dealer CRM | OPERATIVO | tools/dealer_crm.py |
| Pipeline CoVe | OPERATIVO (cron 4h) | src/cove/pipeline_orchestrator.py |
| Scraper 28 portali | OPERATIVO | tools/scrapers/ |
| PDF generator | OPERATIVO | tools/scripts/pdf_generator_enterprise.py |
| Image sanitizer | OPERATIVO | src/cove/image_sanitizer.py |

### 7.2 Moduli nuovi necessari
| Modulo | Scopo | Priorita' |
|--------|-------|-----------|
| dealer_discovery/ | Scraper Subito+AS24+GMaps per trovare target | ALTA |
| message_generator.py | Genera Day 1 personalizzato da profilo dealer | ALTA |
| request_parser.py | Parsea richiesta on-demand da WA (regex+LLM) | MEDIA |
| vehicle_matcher.py | Matcha opportunita' CoVe con profilo dealer | MEDIA |
| voice_generator.py | Vocale Day 10 con edge-tts (gratis) | BASSA |

### 7.3 Bug critici da fixare
1. **outreach_scheduler.py** — NON controlla se dealer ha risposto prima di avanzare sequenza
2. **seller_name extraction** — rotta su pagina dettaglio AS24

### 7.4 Compliance
- GDPR B2B: contatto personalizzato, uno alla volta, da numero pubblico, opt-out immediato
- Max 5 nuovi dealer/giorno
- whatsapp-web.js OK per 10-50 msg/day (NO migrazione a WA Business API — viola zero costi)

---

## 8. AZIONI IMMEDIATE

### Priorita' 1: Valutare TIER0 attuali
I 3 dealer contattati (Stile Car, Car Plus, Sa.My. Auto) sono dealer con stock, NON su commissione.
Verificare se hanno anche componente commissione. Se no, il Day 7 va ripensato con bridge on-demand.

### Priorita' 2: Dealer discovery
Costruire scraper Subito.it + Google Maps per identificare il target GIUSTO nelle province:
Foggia, Caserta, Cosenza, Lecce, Taranto, Salerno, Catanzaro, Avellino.

### Priorita' 3: Nuova comunicazione
Riscrivere messaggi Day 1/3/7 per il dealer su commissione.
Il Day 7 ai TIER0 introduce il bridge: "Ha un cliente che cerca una tedesca? Mi mandi marca/modello/budget."

### Priorita' 4: Fix bug critico
outreach_scheduler deve verificare se il dealer ha risposto prima di mandare il messaggio successivo.

---

## 9. PATH CRITICI (aggiornati)
```
MASTER REF:     research/S94_MASTER_REFERENCE.md           ← QUESTO FILE
PIPELINE:       src/cove/pipeline_orchestrator.py           ← Autonoma, cron 4h
SCRAPER:        src/cove/scraper_cove_pipeline.py           ← Scrape→CoVe→DuckDB
SANITIZER:      src/cove/image_sanitizer.py                 ← V15 YOLO+LaMa
ENRICHER:       src/cove/detail_enricher_v2.py              ← Prezzo/anno/km/VIN/foto
PDF:            tools/scripts/pdf_generator_enterprise.py    ← Galleria+grade+prezzi
OUTREACH:       tools/outreach_scheduler.py                  ← Sequenza Day 1-30
CRM:            tools/dealer_crm.py                          ← SQLite dealer network
WA DAEMON:      wa-intelligence/wa-daemon.js                 ← Sessione WA + invio
RESPONSE:       wa-intelligence/response-analyzer.py         ← LLM classification
PRICE INDEX:    src/cove/data/market_price_index.json        ← 4 modelli, 1296 punti
CoVe:           src/cove/cove_engine_v4.py                   ← NON MODIFICARE

RESEARCH S94:
  research/s94_dealer_su_commissione_sud_italia.md
  research/s94_dealer_commissione_pain_points_comunicazione.md
  research/s94_value_proposition_on_demand.md
  .planning/phases/08-trasporto.../08-RESEARCH.md
  .planning/phases/09-fiducia.../09-RESEARCH.md
  .planning/phases/10-dealer-discovery.../10-RESEARCH.md
  .planning/phases/11-automazione.../11-RESEARCH.md
  .planning/phases/10-deep-research.../10-RESEARCH.md
```

---

*Questo documento e' il riferimento operativo per tutte le decisioni ARGOS da S94 in poi.
Ogni messaggio, ogni dossier, ogni scelta deve rispondere alla domanda:
"Questo crea valore per un piccolo dealer che ha un cliente che aspetta ORA?"*
