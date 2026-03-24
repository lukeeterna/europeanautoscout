# Requirements: ARGOS — Dal VIN Reale al Dossier Reale

**Defined:** 2026-03-24
**Core Value:** Il dealer riceve un dossier con dati che non trova da nessun'altra parte — verificati, reali, e pronti per la rivendita.

## v1 Requirements

### Validazione Tool

- [x] **TOOL-01**: Ogni tool gratuito (freevindecoder, car-recalls, KBA, DAT consumer, garanzia BMW/MB/Audi) e' stato testato con almeno 3 VIN reali PROCEED da DuckDB
- [x] **TOOL-02**: Per ogni tool esiste documentazione di cosa restituisce realmente vs cosa promette
- [x] **TOOL-03**: I tool che funzionano sono integrabili via scraping o API REST senza costi

### Data Infrastructure

- [ ] **DATA-01**: Schema DuckDB vehicle_listings con campi: listing_id, vin, make, model, year, mileage, price_eu, price_it_estimate, source, url, detail_url, scraped_at
- [ ] **DATA-02**: Schema DuckDB vehicle_images con campi: listing_id, image_url, image_type, downloaded, local_path
- [ ] **DATA-03**: Detail Enricher V2 popola vehicle_listings con dati da detail page per listing PROCEED

### Grading & Verification

- [x] **GRADE-01**: Sistema ARGOS GRADE A-E implementato con pesi: 35% CoVe confidence, 20% fraud flags, 15% completezza dati, 15% foto, 10% recall, 5% storico km
- [x] **GRADE-02**: Recall check automatico via car-recalls.eu o KBA per ogni veicolo PROCEED
- [x] **GRADE-03**: VIN decode via freevindecoder.eu integrato nel dossier (specs, emissioni, anno)
- [x] **GRADE-04**: Verifica garanzia costruttore residua via sito brand (BMW/MB/Audi) con VIN

### Dossier PDF

- [ ] **PDF-01**: PDF Enterprise V2 include foto reali HD scaricate dal listing (non placeholder)
- [ ] **PDF-02**: PDF mostra ARGOS GRADE (A-E) prominente in copertina
- [ ] **PDF-03**: PDF include sezione "7 Criteri ARGOS Premium Verified" con solo dati verificati reali
- [ ] **PDF-04**: PDF include analisi finanziaria completa (prezzo EU, costo chiavi in mano, margine netto dealer)
- [ ] **PDF-05**: PDF ha watermark dealer-specific e zero riferimenti a fonti

### Primo Outreach

- [ ] **OUT-01**: Dossier BMW X3 xDrive20d 2022 generato per Stile Car con tutti i dati reali verificati
- [ ] **OUT-02**: Messaggio Day 1 per Domenico (NARCISO) con riferimento al dossier, max 5 righe, domanda chiusa
- [ ] **OUT-03**: WA daemon operativo e messaggio inviato con successo
- [ ] **OUT-04**: CRM aggiornato con stato dealer e timestamp invio

## v2 Requirements

### Intelligence Avanzata

- **INTEL-01**: TCO calculator IT (bollo + RC + manutenzione + carburante) nel dossier
- **INTEL-02**: Time-to-sell estimate per zona/modello
- **INTEL-03**: Storico prezzi 12 mesi trend per modello
- **INTEL-04**: Alert stock personalizzato per dealer (filtro su 73 portali)
- **INTEL-05**: Scheda rivendita per cliente finale (secondo template PDF)

### Scale

- **SCALE-01**: Outreach Car Plus (RAGIONIERE) e Sa.My. Auto (TECNICO)
- **SCALE-02**: Batch processing multi-veicolo per dealer
- **SCALE-03**: DEKRA accordo volume post 3-5 deal

## Out of Scope

| Feature | Reason |
|---------|--------|
| SilverDAT/Schwacke API | Viola guardrail zero costi (€1.400/anno) |
| DEKRA ispezione fisica | Serve dopo 3-5 deal, non prima |
| Facebook pagina | Non bloccante per primo deal |
| Perito auto Camera di Commercio | Fase 3+, dopo track record |
| Audio motore ACV-style | Richiede hardware proprietario |
| 360° foto Carvana-style | Richiede presenza fisica al veicolo |
| Paint meter / OBD scan | Richiede ispezione fisica |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOOL-01 | Phase 1 | Complete |
| TOOL-02 | Phase 1 | Complete |
| TOOL-03 | Phase 1 | Complete |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| GRADE-01 | Phase 3 | Complete |
| GRADE-02 | Phase 3 | Complete |
| GRADE-03 | Phase 3 | Complete |
| GRADE-04 | Phase 3 | Complete |
| PDF-01 | Phase 3 | Pending |
| PDF-02 | Phase 3 | Pending |
| PDF-03 | Phase 3 | Pending |
| PDF-04 | Phase 3 | Pending |
| PDF-05 | Phase 3 | Pending |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| OUT-03 | Phase 4 | Pending |
| OUT-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after initial definition*
