# S94 — Comunicazione Dealer: Gap Analysis + Fix

## CONTESTO
S93 ha validato la pipeline E2E (scrape→score→enrich→sanitize→PDF) e reso il sistema autonomo via cron su iMac. Ma durante lo stress test sono emersi GAP critici nella qualita' del prodotto che il dealer riceve.

## GAP RILEVATI (da fixare in ordine di priorita')

### 1. IMMAGINI — QUALITA' DOSSIER
**Problemi trovati durante stress test 5 PDF:**
- [ ] **Branding dealer fisico NON rimosso** — tappetini/sedili con logo dealer (es. "AuRa" corsivo su seduta) passano il sanitizer perche' EasyOCR non rileva testo cursivo a bassa confidenza
- [ ] **Foto non-auto nella galleria** — piazzale dealer, edificio, persone/venditori finiscono nella galleria (pagina 3/3). Fix parziale: cap a 15 foto + sky detection per immagini >12. Da verificare e rendere piu' robusto
- [ ] **Seller name extraction rotta** — `extract_specs_from_html()` estrae seller da `__NEXT_DATA__.listings[0].seller.companyName` ma su pagina DETTAGLIO la struttura e' diversa → seller_name sempre NULL
- [ ] **OCR soglia 0.10 potrebbe dare falsi positivi** — abbassata da 0.15 per catturare corsivo, ma potrebbe mascherare testo auto legittimo. Serve test su campione largo

### 2. PDF — CONTENUTO E LAYOUT
- [ ] **Tutti Grade B** — il grading sembra non differenziare (0.78-0.84). Verificare la formula del grade e se e' calibrata correttamente
- [ ] **Margine netto basso/negativo** — molti listing PARKED per gate3_fail (margine <€2500). Il moltiplicatore EU→IT 1.10 e' conservativo. Verificare con dati reali di rivendita
- [ ] **"Riservato per BD Auto"** — il watermark dealer funziona ma il dealer_matcher non ha abbastanza dealer nel DB per distribuzione reale

### 3. COMUNICAZIONE DEALER — ZERO RISPOSTE
**Stato TIER0 (contattati 27/03, Day 3 inviato 30/03):**
- Stile Car (Domenico, NARCISO) — LETTO, zero risposta
- Car Plus (Luca, RAGIONIERE) — LETTO, zero risposta
- Sa.My. Auto (Antonio, TECNICO) — LETTO, zero risposta

**Analisi:**
- Day 1 + Day 3 inviati ma senza PDF allegato (i PDF non erano pronti)
- I messaggi Day 3 sono in `dossiers/messaggi_day3_pronti.md` — verificare se inviati
- Il Day 7 scade il 3 aprile — serve strategia FOMO/exit
- TIER1 (6 dealer) non ancora contattati

**Azioni comunicazione:**
- [ ] Verificare stato reale invii WA (Day 1 + Day 3) per tutti e 3
- [ ] Preparare Day 7 con PDF allegato (ora disponibile!)
- [ ] Decidere se contattare TIER1 con il nuovo sistema PDF
- [ ] Valutare se il messaggio Day 1 era troppo generico / necessita revisione

### 4. OUTREACH SCHEDULER — BUG FIXATO
- [x] Bug re-invio: scheduler mandava la stessa notifica TG ogni giorno senza avanzare la sequenza
- [x] Fix: ora avanza `next_action_type` + `next_action_at` dopo ogni notifica
- [ ] Verificare che il fix funziona correttamente nei prossimi giorni

### 5. PIPELINE AUTONOMA — VERIFICATA MA CON LIMITI
- [x] Cron attivo su iMac: scrape 5am, pipeline ogni 4h, outreach 8-20 lun-sab
- [x] Stale cleanup automatico (>5 giorni → REJECTED)
- [x] Dealer round-robin funzionante
- [ ] **YOLO su CPU troppo lento**: ~5 min per PDF con 19 foto → max 12 PDF per cron cycle (4h)
- [ ] **55 SCORED vecchi ancora nel DB** — stale ma non cleanup perche' su MacBook (diverso DB da iMac)

## PRIORITA' S94

1. **Verificare invii WA reali** — cosa hanno ricevuto i 3 TIER0?
2. **Day 7 strategia** — con PDF allegato stavolta
3. **Fix seller_name extraction** dalla pagina dettaglio AS24
4. **Test sanitizer su 20 immagini** — verificare che il filtro non-auto e OCR 0.10 funzionano
5. **TIER1 outreach** — iniziare con i nuovi PDF

## FILE MODIFICATI IN S93
```
src/cove/detail_enricher_v2.py      — image dedup fix, seller_name extraction, cap 15 imgs
src/cove/image_sanitizer.py         — OCR 0.10, seller blocklist, non-car filter, sanitizer dedup fix
src/cove/pipeline_orchestrator.py   — rate limit 60, stale cleanup, margin 1.10, --max-score flag
src/cove/dealer_matcher.py          — round-robin tiebreaker
tools/scripts/pdf_generator_enterprise.py — filename collision fix (listing_id suffix)
tools/outreach_scheduler.py         — bug re-invio fixato (avanza sequenza)
scripts/daily_scrape.sh             — NUOVO: cron scrape 4 modelli
scripts/run_pipeline.sh             — NUOVO: cron pipeline runner
```
