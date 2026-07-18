# S176 — Resume S175.0 STEP 4-9 (on-demand runner BMW X1 + signature + payment)

**Precondizione**: S175.1b chiuso VERDE 4/4 (vedi `data/s175_1b_replay_report.md`). AMBRA role-binding info-broker fixato live su TEST_FOUNDER, fix S175.1 attivo. Reply 11:48 compliant. Resume S175.0 step 4-9 sbloccato.

**Scope S176**: completare E2E reactive pipeline su TEST_FOUNDER step 4-9 di `prompts/s175_0_e2e_reactive_test_founder.md`. Goal = primo deal chiuso end-to-end (contatto → dossier → contratto → pagamento finto) su TEST_FOUNDER. Sblocca Path A LUCKY CARS mystery shopper reale post-9/9 VERDE.

**Tempo stimato**: ~45-90min (lookup CoVe 5-15min + Luke phone interactions + contract flow). Budget context ~50% finale.

## Pre-flight Claude (~3min)

```bash
# 1. Daemon ancora online + fix S175.1 still active
ssh imac "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin; pm2 status | grep -E 'argos-wa-daemon|argos-cf-monitor|argos-dashboard'"

# 2. Fix S175.1 markers ancora su disk
ssh imac "grep -c -E 'vehicle_request_broker|_check_vehicle_hallucination|_check_broker_lexicon_ban|VEHICLE_REQUEST_BROKER_FALLBACK' ~/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py"
# Atteso: 7

# 3. TEST_FOUNDER state
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, current_step, handoff_source FROM conversations WHERE dealer_id='TEST_FOUNDER';\""
```

Se daemon offline o markers !=7 → restart + re-checkout (vedi S175.1b pre-flight pattern).

## STEP 4 — Lancio pipeline on-demand reale (~10min)

Luke lancia manualmente (D-15 founder HITL 100% primi 1-3 dealer):

```bash
ssh imac "cd ~/Documents/app-antigravity-auto && python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 18000 --dealer TEST_FOUNDER 2>&1 | tail -60"
```

Output atteso:
- Scrape ~20 listing BMW X1
- CoVe scoring filtra → 1-3 PROCEED candidates
- PDF dossier generato `dossiers/ARGOS_BMW_X1_*.pdf`
- (Opzionale) auto-invio Luca Ferretti dossier via WA

Se pipeline ROSSO (scraper down, CoVe error, PDF empty) → diagnose + fix come gate per S176.

## STEP 5 — Founder check PDF (~3min Luke)

Luke apre PDF + verifica:
- Watermark "Luca Ferretti" presente
- 12 sezioni dossier complete (D-18)
- Foto sanitized (no DAT/portal source)
- VIN check presente
- Margine stimato leggibile

Se PDF MAL → BACKLOG + fix step S176-bis.

## STEP 6 — Send dossier via WA (~5min)

Luke lato Claude:
```bash
# Verifica file PDF
ssh imac "ls -la /Users/gianlucadistasi/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_X1_*$(date +%Y%m%d)*.pdf"

# Send via WA (oppure usa dashboard:8080)
ssh imac "curl -X POST http://localhost:9191/send -H 'Content-Type: application/json' -H 'X-API-Key: ...' -d '{\"to\":\"39<TEST_FOUNDER_NUM>\",\"message\":\"<msg + filepath>\"}'"
```

Verifica delivery DB messages.

## STEP 7 — Reactive sign request (~5min Luke)

Da TEST_FOUNDER (+39 331 4928901) → Argos WA Business:

> Va bene, mi mandi il contratto

Atteso: AMBRA classifica `CONTRACT_REQUEST` → genera URL signature form → reply con link `https://argos-automotive.pages.dev/sign?id=<token>`.

Verifica reply via DB messages + analyzer log.

## STEP 8 — Sign + IBAN flow (~10min Luke)

Luke apre link signature dal telefono, compila form:
- Nome dealer/founder
- Codice fiscale/P.IVA (test data)
- Firma (touch)
- Submit

Backend Cloudflare Worker (`argos-proxy.gianlucanewtech.workers.dev`) registra contract → trigger `/send-iban` → AMBRA invia IBAN su WA.

```bash
# Verifica contract creato + IBAN sent
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, dealer_id, status, datetime(created_at) FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 2;\""
```

## STEP 9 — Mark-paid + delivery flow (~5min Luke)

Luke su dashboard:8080 / admin:
- Apre contract TEST_FOUNDER
- Mark as PAID (paid_amount fittizio €800, ref "S176-TEST-FOUNDER-001")
- Verifica AMBRA invia conferma payment + ETA delivery

Verifica DB:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, status, paid_amount, datetime(paid_at) FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;\""
```

## Verdict S176

- **VERDE 9/9 (STEP 4-9 tutti pass)** → S175.0 E2E reactive UFFICIALMENTE chiuso. Path A LUCKY CARS mystery shopper sbloccato (`prompts/s175_mystery_shopper_pilot.md`). Day 1 dealer reale ancora gated da founder discretion (D-07 HITL primi 20 + D-15 first 1-3).
- **GIALLO 7-8/9** → 1-2 step ROSSO → patch mirato in S176.x + retry singolo step
- **ROSSO ≤6/9** → blocker hard, handoff strategic con root cause analysis

## Output attesi sessione S176

1. `data/s176_e2e_resume_report.md` — esecuzione step 4-9 + verdict
2. PDF dossier BMW X1 in `dossiers/`
3. Contract TEST_FOUNDER in DB con status PAID
4. Conditional handoff: S175 chiuso 9/9 verde OR S176.x patch prompt

## Context budget S176

Pre-flight 5% + STEP 4 pipeline 15% + STEP 5-9 verify 25% + report 10% = ~55%. Watch >50% per closure pulita.

## Findings collaterali da non risolvere in S176 (BACKLOG)

1. **iMac branch divergence** (`main` HEAD `fd35965e` history-rewrite vs `origin/master`) — workaround attuale: checkout puntuale file da `origin/master`. Da sessione dedicata: decidere reset hard vs branch switch (richiede Luke approval per destructive op).
2. **Estrattore VEHICLE_REQUEST `modello=None`** — parsing "BMW x1" non riconosce X1 come modello. LLM compensa via context raw, non-bloccante.
3. **`pending_replies.scheduled_at` NULL** — scheduler funziona via altra logica. Documentare comportamento attuale.

Da NON aprire in S176 — sprint resta scope-locked su S175.0 step 4-9.

## Decisioni applicate

- **D-07** HITL strutturale primi 20 dealer
- **D-11** Test pipeline 5-step su TEST_FOUNDER prima dealer reale
- **D-15** Founder HITL 100% primi 1-3 dealer
- **D-16** Dossier ampliamento + carVertical on-demand
- **D-18** Dossier 12 sezioni core
- **D-OPEN-Q2** P.IVA timing — pagamento cash a consegna €800-1.200, no P.IVA
- **D-OPEN-Q5** Pricing range €800-1.200 in conversation, NON landing

## Fattuale pre-verified

- Fix S175.1 attivo su iMac (checkout S175.1b)
- TEST_FOUNDER state post-S175.1b reply: `HANDOFF_LAYER3` con 2 OUTBOUND recenti
- Daemon online uptime ~post-11:38 restart
- DB schema S173 colonne presenti
- Cloudflare Worker `argos-proxy.gianlucanewtech.workers.dev` operativo (verified S164)
- Dashboard:8080 online (uptime 86m+ pre-S175.1b)
