# S73 — FEATURE MAP SISTEMA ARGOS COMPLETO
## Cosa abbiamo, cosa manca, in che ordine costruire
### 2026-03-21

---

## COSA ABBIAMO GIA'

| Componente | File | Stato |
|-----------|------|-------|
| Scraper 73 portali EU | `tools/scrapers/` | FUNZIONANTE |
| CoVe scoring bayesiano | `src/cove/cove_engine_v4.py` | FUNZIONANTE — NON TOCCARE |
| Fraud detection | `src/cove/fraud_flags.py` | FUNZIONANTE |
| Market Price Index | `src/cove/market_price_index.py` | FUNZIONANTE |
| ADAC Reference | `src/cove/adac_price_reference.py` | FUNZIONANTE |
| Pipeline E2E | `src/cove/scraper_cove_pipeline.py` | FUNZIONANTE |
| Batch Runner | `tools/batch_runner.py` | FUNZIONANTE |
| PDF Dossier | `tools/scripts/pdf_generator_enterprise.py` | FUNZIONANTE |
| Image Downloader + Watermark | `tools/scrapers/image_downloader.py` | FUNZIONANTE |
| Transport Estimator | `tools/transport_estimator.py` | FUNZIONANTE |
| Import Checklist | `tools/import_checklist.py` | FUNZIONANTE |
| Fee Calculator | `tools/fee_calculator.py` | FUNZIONANTE |
| WA Daemon | `wa-intelligence/wa-daemon.js` | ONLINE (9191) |
| Dashboard | `wa-intelligence/dashboard/app.py` | ONLINE (8080) |
| Dealer Scoring | `tools/dealer_scouting_playbook.py` | NUOVO S73 |
| Target Profiles + Regioni | `tools/dealer_target_profiles.py` | NUOVO S73 |

---

## COSA MANCA — PRIORITIZZATO

### P0 — Critico (prossime 2 sessioni)

| # | Feature | Descrizione | Perche' P0 |
|---|---------|-------------|------------|
| 1 | **Scheda dealer unificata SQLite** | Ogni dealer: titolare, stock, marchi, archetipo, WA, score, OBJ, stato pipeline (NEW→CONTACTED→REPLIED→INTERESTED→DEAL→CLOSED→LOST→DORMANT), log interazioni | Senza questo, i dealer sono sparsi in file MD. Non scala. |
| 2 | **Sequencer touchpoint automatico** | WA daemon esegue Day1→3→7→10→14→21→30 per ogni dealer. Se risponde → stop + notifica. Se no → next template archetipo | A mano su 20+ dealer = errori certi |
| 3 | **Vehicle-dealer matching** | CoVe trova BMW X3 +€9k margine → sistema identifica dealer in pipeline che trattano BMW → genera messaggio personalizzato | Core del business. HubSpot non sa cos'e' un BMW X3 |
| 4 | **Selezione template automatica** | archetipo + giorno + tipo target → template giusto senza intervento umano | 5 archetipi x 7 giorni x 5 target = 175 combinazioni |
| 5 | **Alert dealer INTERESTED** | Dealer che ha risposto con interesse → notifica immediata WA/Telegram al founder | Un dealer caldo che aspetta 48h si raffredda |

### P1 — Importante (sessioni 3-4)

| # | Feature | Descrizione |
|---|---------|-------------|
| 6 | **Stock change detection AS24** | Scraper periodico su profilo AS24 di ogni dealer in pipeline. +3 premium in 7gg = sta comprando = timing perfetto |
| 7 | **Weekly digest automatico** | Ogni lunedi WA al founder: nuovi dealer, risposte, silenzi >7gg, fee chiuse, top 3 opportunita' |
| 8 | **Dashboard kanban + metriche** | Vista pipeline per stadio + response rate + conversion rate stage-to-stage |
| 9 | **Delta DE→IT tracking** | MarketPriceIndex → trend settimanale per modello. Se delta si allarga → argomento piu' forte |
| 10 | **Referral tracking** | Campo parent_dealer_id. Sapere quale dealer ha portato quali altri |
| 11 | **A/B testing template** | 2 varianti Day1 per archetipo, traccia response rate |
| 12 | **Storico veicoli proposti** | Per dealer: quali VIN proposti, quando, esito. Mai riproporre lo stesso |

### P2 — Roadmap futura

| # | Feature | Descrizione |
|---|---------|-------------|
| 13 | Auto-enrichment dealer periodico (30gg) | Riscrape AS24 + Google Maps, aggiorna score |
| 14 | Alert "nuovo dealer in zona" | Scanner AS24 periodico, notifica se nuovo dealer >20 auto premium |
| 15 | Alert "riattivazione" | Dealer DORMANT >30gg → suggerisce veicolo nuovo per ricontatto |
| 16 | Content generation social | Post settimanale automatico con dati mercato |
| 17 | Stagionalita' alert | "Siamo in stagione alta — intensifica outreach" |
| 18 | Modello piu' richiesto per zona | Impara preferenze dealer per zona da storico |

---

## PERCHE' NON COMPRARE UN CRM

| Feature | CRM generico (HubSpot/Pipedrive) | ARGOS interno |
|---------|----------------------------------|---------------|
| Vehicle-dealer matching | NON ESISTE | Core business |
| Stock monitoring AS24 | NON ESISTE | Segnale acquisto |
| Delta DE→IT per modello | NON ESISTE | Argomento vendita |
| Archetipo comunicativo | NON ESISTE | Template selection |
| Sequenze WA native | Solo email | Canale primario Sud |
| OBJ handler integrato | NON ESISTE | Gestione obiezioni |
| CoVe + batch runner | NON ESISTE | Competitive advantage |

**Costruire interno in SQLite + dashboard gia' presente. Il vantaggio e' nell'integrazione.**
