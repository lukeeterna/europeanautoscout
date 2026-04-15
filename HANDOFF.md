# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S120 — 2026-04-15

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
