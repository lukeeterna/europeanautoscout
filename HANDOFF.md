# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S125 — 2026-04-15

---

## S125 COMPLETATA — DEEP RESEARCH DEALER TUTTA ITALIA + ALLINEAMENTO STRATEGICO

### Cosa è stato fatto

1. **3 research parallele completate** (agent-research, ~10 min):
   - Research A: Self-perception dealer TUTTA Italia (Nord/Centro/Sud) — confidenza 6.5/10
   - Research B: Come dealer italiano parla ai clienti premium oggi — canali, gap, confronto UK/DE
   - Research C: Gap di mercato — territorio vuoto al 90%, nessun competitor su formazione premium per indipendenti

2. **Sintesi presentata al founder** — mappa per macroarea, 5 gap documentati, 3 opzioni costruttive

3. **Allineamento strategico raggiunto** — decisioni founder:
   - Opzione **C** (area formazione) come direzione principale
   - Frame **per macroaree** — ma serve più segmentazione → altra research necessaria
   - Sequenza: **materiali prima, poi come leva nel Day 1** (non go-live subito)

4. **Proposta CTO accettata**: parallelizzare, non serializzare. Stile Car come MVP pilota (Sud già researched), research Nord/Centro in parallelo.

### Correzioni critiche confermate in S125

- Self-perception dealer: NON "già nel premium", ma "seri e affidabili con auto buone" — in tutta Italia
- "Premium" = categoria veicolo (BMW/Mercedes), MAI identità del dealer — in tutta Italia
- Frame per area: Nord → "processo più efficiente" | Sud → "auto che i tuoi clienti cercano, più veloce"
- Domanda latente: i dealer non cercano "formazione premium" — va creata la categoria mentale

### Stato pipeline (invariato da S123)

| Nome | dealer_id | Step | Note |
|------|-----------|------|------|
| Enzo Car | TIER1_FG_002 | CLOSED_NO | CHIUSO — NEGATIVE |
| Stile Car | TIER0_FG_001 | PENDING | Day 1 pronto — MVP materiale formativo da costruire |
| Sa.My. Auto | TIER0_CS_001 | PENDING | In attesa materiali + go-live founder |
| Car Plus | TIER0_AV_001 | PENDING | In attesa materiali + go-live founder |

---

---

## S123 COMPLETATA — PIPELINE TEST + FIDELIZZAZIONE IMPLEMENTATA

### Cosa è stato fatto
1. **Pipeline test live su TEST_FOUNDER (393314928901)** — PASS
   - dry_run PASS → invio reale `msg_id: out_1776266941757_bxnw3` → loggato in DB
   - Template Day 1 Stile Car inviato correttamente via WA daemon 9191
2. **Fidelizzazione: DB migration** — 6 colonne aggiunte su iMac DB:
   `is_active_partner, partner_since, total_transactions, total_revenue_dealer, last_analytics_sent, trusted_partner_sent`
3. **3 script fidelizzazione** in `tools/fidelizzazione/`:
   - `promote_partner.py` — promuove dealer a partner dopo transazione (update DB)
   - `analytics_dossier.py` — PDF "quanto hai guadagnato con ARGOS" (trimestrale, dopo 2-3 tx)
   - `trusted_partner_letter.py` — lettera fisica firmata Luca (dopo 1ª tx)
4. **Test fidelizzazione E2E**: promote → preview → PDF generato → rollback ✅

### Flusso fidelizzazione operativo
```
1ª conversione completata:
  → python3 tools/fidelizzazione/promote_partner.py --dealer <id> --transactions 1 --revenue <€>
  → python3 tools/fidelizzazione/trusted_partner_letter.py --dealer <id> --mark-sent
  → Stampa PDF + spedisci (€5 spedizione)

Dopo 2-3 transazioni (trimestrale):
  → python3 tools/fidelizzazione/analytics_dossier.py --dealer <id> --output /tmp/ --mark-sent
  → Invia PDF via WA

Verifica partner attivi:
  → ssh iMac "python3 tools/fidelizzazione/promote_partner.py --list"
```

---

## S122 COMPLETATA — PHASE 4 WAVE 1 + TEMPLATE DAY 1

### Stato corrente
**Phase 4 Wave 1 DONE** — DB pulito, WA green, E2E 3/3 PASS, 3 template Day 1 pronti.

**Prossima azione immediata**: founder approva template → `/gsd:execute-phase 4` Wave 2.

### Dealer pipeline
| Nome | dealer_id | Step | Note |
|------|-----------|------|------|
| Enzo Car | TIER1_FG_002 | CLOSED_NO | CHIUSO — NEGATIVE |
| Stile Car | TIER0_FG_001 | PENDING | Day 1 pronto (NARCISO) |
| Sa.My. Auto | TIER0_CS_001 | PENDING | Day 1 pronto (RELAZIONALE) |
| Car Plus | TIER0_AV_001 | PENDING | Day 1 pronto (RAGIONIERE) |
| Autoline | TIER1_AV_002 | PENDING/COLD | In attesa autorizzazione |
| GP Cars | TIER1_TA_001 | PENDING/COLD | In attesa autorizzazione |

### Artifacts pronti
- `tools/outreach/dealer_profiles_validated.json` — profili validati
- `tools/outreach/day1_templates/` — 3 template Day 1 personalizzati
- Commits: 4a92e62 (04-02) + fe8e88e (04-03)

### Gate Wave 2
- [ ] **Founder approva i 3 template Day 1** (testi in `tools/outreach/day1_templates/`)
- [ ] `/gsd:execute-phase 4` → esegue 04-01 (Stile Car singolo) + 04-04 (multi-dealer)

---

## S123 COMPLETATA — SCHEDULER FIX + DASHBOARD KPI + FIDELIZZAZIONE

### Commit: f21e0e9 + c6c16d1

### Fix critici eseguiti

**1. Scheduler (era completamente rotto)**
- Bug: LaunchAgent puntava a `dealer_network.duckdb` → `ERROR: file is not a database` ogni 5 min
- Bug: `SEQUENCE_MAP` usava `WA_DAY1_SENT` — DB ha `DAY1_SENT` → zero match
- Bug: `ARGOS_TELEGRAM_TOKEN` assente nel plist → alert Telegram mai inviati
- Fix: plist corretto + SEQUENCE_MAP allineato a wa-daemon.js + token iniettato
- **Verificato**: scheduler trova 6 dealer, calcola TEST_FOUNDER Day3 scadenza Sab 18/04 15:29

**2. Dashboard KPI (erano 4 numeri inutili)**
- Aggiunti: WA status live, response rate, sent today, daily_remaining, scadenze 24h, pending urgenti
- Banner alert scadenze imminenti (auto-refresh 30s via HTMX)
- File: `wa-intelligence/dashboard/db.py` + `app.py` + `_kpi_cards.html`

**3. Fidelizzazione implementata**
- DB migration iMac: 6 colonne (is_active_partner, partner_since, total_transactions, total_revenue_dealer, last_analytics_sent, trusted_partner_sent)
- `tools/fidelizzazione/promote_partner.py` — promuove dealer dopo transazione
- `tools/fidelizzazione/trusted_partner_letter.py` — PDF lettera fisica (~€5 spedizione)
- `tools/fidelizzazione/analytics_dossier.py` — PDF trimestrale "quanto hai guadagnato"

**4. Pipeline test**
- Day 1 inviato a TEST_FOUNDER (393314928901) — confermato ricevuto dal founder

### Gap production-ready rimanenti (prossima sessione)
| # | Gap | Priorità |
|---|-----|----------|
| 1 | **Pending reply E2E** — verificare che alert Telegram + approvazione dashboard funzioni end-to-end | ALTA |
| 2 | **Scraper scheduling** — automatizzare on_demand_runner su cron/LaunchAgent | MEDIA |
| 3 | **Wave 2 go-live** — in attesa approvazione template founder | BLOCCANTE |
| 4 | **Landing area formazione** — research in `s99_formazione_integrata_operazione.md`, da implementare | BASSA |

### Research già fatta (NON rifare)
- `research/s99_PIANO_OPERATIVO_COMPLETO.md` — piano 24 mesi
- `research/s99_DATI_CERTI_segmentazione_province.md` — volumi per regione/provincia
- `research/s99_formazione_integrata_operazione.md` — modello "learn by earning"

---

## S120 COMPLETATA — COVE E2E FIX + RESEARCH AUTOSALON SU COMMISSIONE

### Cosa è successo

**1. CoVe E2E: PASS 3/3 (era FAIL 2/3)**
- Root cause: test non passava `market_price_ref` → engine cadeva in euristica σ=0.40 → confidence collapse
- Fix: mock `AsyncMock` su `engine.market_verifier.verify` + `market_price_ref` nei ground truth cases
- File: `/Users/gianlucadistasi/Documents/app-antigravity-auto/python/tests/test_e2e_integration_v3.py`
- `cove_engine_v4.py` NON modificato (regola invariata)

**2. DB dealer reset**
- Stile Car, Sa.My. Auto, Car Plus avevano `DAY1_SENT` come artefatti seeding
- Resettati a `PENDING/COLD/outbound_count=0` in `app-antigravity-auto/dealer_network.sqlite`
- Nessun messaggio mai inviato a questi 3 dealer

**3. Path reale infra (scoperto)**
- Daemon e DB messaggi sono in `app-antigravity-auto/` (NON enterprise repo)
- `dealer_network.sqlite` enterprise ha solo market data (NO messages/conversations)
- DB corretto: `sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`

**4. Research "autosalon su commissione" completata**
- ~5.800 IT / ~2.100 Sud+Isole — contratto estimatorio, commissione 4-7%, NON possiedono stock
- Pain point: OFFERTA (trovare veicoli che il cliente vuole in <90gg), non acquisto
- Pitch adattato: "trovo BMW/Mercedes EU che il tuo cliente vuole in <30gg. Zero anticipo."
- Gap competitivo confermato: zero operatori con outreach B2B proattivo su questo segmento

**5. Strategia fidelizzazione: verdetto**
- "Area formazione" = Fase 3 (5+ dealer). Oggi è distrazione
- Top-3 mechanic zero costo: (1) priority_access flag DB, (2) dossier analytics trimestrale, (3) lettera Trusted Partner

**6. Image sanitizer: PASS**
- Pipeline 5 stadi funzionante, 16s/immagine, output corretto

---

## STATO SISTEMA (post S120 — 2026-04-15 ore ~11:00)

### Infra iMac
- PM2: `argos-wa-daemon` online, `argos-dashboard` online
- WA: **connected**, porta 9191, daily remaining: **10/10**
- block_rate: 0.000

### DB stato dealer reali
| Nome | dealer_id | Step | inbound | Note |
|------|-----------|------|---------|------|
| Enzo Car | TIER1_FG_002 | CLOSED_NO | 1 ("Nulla") | CHIUSO |
| Stile Car | TIER0_FG_001 | PENDING | 0 | Pronto per Day 1 |
| Sa.My. Auto | TIER0_CS_001 | PENDING | 0 | Pronto per Day 1 |
| Car Plus | TIER0_AV_001 | PENDING | 0 | Pronto per Day 1 |
| Autoline | TIER1_AV_002 | PENDING/COLD | 0 | Candidato go-live |
| GP Cars | TIER1_TA_001 | PENDING/COLD | 0 | Candidato go-live |

---

## PROSSIMA SESSIONE — S121

**Obiettivo principale**: validare research su autosalon su commissione + pianificazione E2E production-ready.

**Agenda S121**:
1. **Validazione dati research**: verificare numeri iCRIBIS/UNRAE con dati reali (AutoScout24 profili, Google Maps, stock effettivo dealer target)
2. **Adattare pitch**: riscrivere template Day 1 per autosalon su commissione (contratto estimatorio, rotazione 90gg, zero rischio capitale)
3. **Pianificazione E2E production-ready**: definire gate di qualità da CoVe score → dossier → outreach → risposta → transazione
4. **Go-live con founder authorization**: Day 1 a Stile Car, Sa.My. Auto, Car Plus (e Autoline/GP Cars se autorizzati)
5. **Test Day 1 su TEST_FOUNDER** prima di qualsiasi invio reale

**Gate bloccanti per go-live**:
- [ ] Pitch template validato per autosalon su commissione
- [ ] Test E2E WA (Day 1 → risposta → auto-reply) su TEST_FOUNDER: PASS
- [ ] Founder autorizza esplicitamente i dealer target

**Prompt**: `prompts/s121_validazione_research_production_ready.md`
