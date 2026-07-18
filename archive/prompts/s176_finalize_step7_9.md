# S176-finalize — Resume STEP 7-9 (signature + payment) + verify reply TEST_FOUNDER

**Precondizione**: S176 STEP 4-6 chiuso VERDE (vedi memory `s176_partial_step4_6_green_d32_sanitizer_blocker.md`). PDF dossier BMW X1 inviato `doc_1778941030143_bnstt` alle 16:17 CEST 2026-05-16. Letto da TEST_FOUNDER alle 17:29. Reply Luke "Va bene mi mandi il contratto" NON arrivata al daemon in S176 (zero INBOUND post-16:17 in DB messages + daemon log).

**Scope S176-finalize**: chiudere E2E reactive pipeline TEST_FOUNDER step 7-9 → primo deal end-to-end VERDE (contatto → dossier → contratto → pagamento simulato).

**Tempo stimato**: ~30-45min se reply Luke arrivata; +15min troubleshoot daemon se reply mancante.

## Fattuale pre-verified S176

- PDF: `dossiers/ARGOS_BMW_X1_2022_TEST_FOUNDER_20260516_120546.pdf` (937KB, 3 pagine) — su iMac
- WA send msg_id: `doc_1778941030143_bnstt` / wa_msg_id `true_141115562971357@lid_3EB0D5D49F3548AD2BAC66`
- daemon online, daily_sent 3/20 al close S176
- ARGOS_API_KEY: `<vedi wa-intelligence/.env>` (in `~/Documents/app-antigravity-auto/wa-intelligence/.env`)
- Cloudflare Worker `argos-proxy.gianlucanewtech.workers.dev` operativo (verified S164)
- Dashboard:8080 online (PM2 argos-dashboard uptime 112m+ al close S176)
- D-32 sanitizer regression NON blocca S176-finalize (TEST_FOUNDER è simulato D-11)

## Pre-flight Claude (~3min)

```bash
# 1. Daemon online + state
ssh imac "export PATH=\$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin; pm2 status | grep -E 'argos-wa-daemon|argos-cf-monitor|argos-dashboard'"

# 2. TEST_FOUNDER conversation state (atteso: DAY1_SENT o avanzato post-reply)
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, current_step, handoff_source FROM conversations WHERE dealer_id='TEST_FOUNDER';\""

# 3. Verifica fix S175.1 ancora attivo
ssh imac "grep -c -E 'vehicle_request_broker|_check_vehicle_hallucination|_check_broker_lexicon_ban|VEHICLE_REQUEST_BROKER_FALLBACK' ~/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py"
# Atteso: 7
```

## STEP 7 — Verify reply TEST_FOUNDER (~5-15min)

### Query DB messages (priorità 1)

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT datetime(created_at,'localtime'), direction, dealer_id, substr(body,1,120) FROM messages WHERE phone_number LIKE '%<TEST_FOUNDER_NUM>%' OR dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 8;\""
```

**Caso A — INBOUND da TEST_FOUNDER presente con "contratto/contract/firmo/firma/proseguo/va bene"**:
- Verifica `pending_replies` AMBRA classifier:
  ```bash
  ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT datetime(created_at,'localtime'), reply_label, substr(reply_text,1,150) FROM pending_replies WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 3;\""
  ```
- Atteso `reply_label` = `CONTRACT_REQUEST` o `LLM_MULTI` con menzione signature URL
- Se AMBRA ha auto-spedito URL signature → proseguo STEP 8
- Se AMBRA ha schedulato `pending_replies.approved=NULL` → Luke approva via dashboard:8080 (HITL D-07)

**Caso B — Nessun INBOUND TEST_FOUNDER post-16:17 S176**:
- Verifica daemon log:
  ```bash
  ssh imac "grep -E '16/05/2026 1[8-9]:|17/05/2026|Raw msg.from.*141115562971357|<TEST_FOUNDER_NUM>' /tmp/argos-wa-daemon-out.log | tail -20"
  ```
- Verifica TEST_FOUNDER profile WA da telefono Luke: lo screenshot della chat ARGOS Business (+39 328 1536308) mostra reply spedita o no?
- Possibili root cause:
  1. Luke non ha effettivamente inviato (apparente fail UX WA)
  2. Reply su thread WA sbagliato
  3. LID resolution failure daemon (pattern S171 dedup bug: `[bridge] inbound skip (unknown party ...)`)
  4. Test ha consumato sessione WA stale, serve re-pair
- Decisione: Luke re-invia reply ora → attendi 30s → re-query DB. Se ancora zero → debug lid resolution.

## STEP 8 — Sign + IBAN flow (~10-15min, fisico Luke)

Quando AMBRA invia URL signature in reply (es. `https://argos-automotive.pages.dev/sign?id=<token>`):

1. Luke apre link dal telefono TEST_FOUNDER
2. Compila form:
   - Nome dealer/founder: `Test Concessionaria Founder`
   - Codice fiscale/P.IVA: test data placeholder
   - Firma touch
   - Submit
3. Backend Cloudflare Worker `argos-proxy.gianlucanewtech.workers.dev`:
   - Registra contract row in DB iMac
   - Trigger `/send-iban` → AMBRA invia IBAN via WA

Verifica:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, dealer_id, status, datetime(created_at,'localtime') FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 2;\""
```

Atteso: nuovo contract row con `status` evoluto `DRAFT → AWAITING_DELIVERY → IBAN_SENT`.

## STEP 9 — Mark-paid + delivery flow (~5min, fisico Luke)

Su dashboard `http://192.168.1.2:8080`:
1. Apre contract TEST_FOUNDER
2. Click **Mark as PAID**
3. Inserisce: `paid_amount=800`, `ref="S176-FINALIZE-TEST-FOUNDER-001"`
4. Submit → AMBRA invia conferma payment + ETA delivery

Verifica DB:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT id, status, paid_amount, datetime(paid_at,'localtime'), ref FROM contracts WHERE dealer_id='TEST_FOUNDER' ORDER BY rowid DESC LIMIT 1;\""
```

Atteso: `status=PAID, paid_amount=800.0, paid_at=<now>`.

## Verdict S176-finalize

- **VERDE 9/9** (STEP 7-9 tutti pass) → S175.0 + S176 E2E reactive UFFICIALMENTE chiuso. Trigger immediato: **S176-bis sanitizer refactor D-32** (BLOCKER Day 1 reale). Path A LUCKY CARS mystery shopper still gated da S176-bis.
- **GIALLO 7-8/9** → 1-2 step ROSSO → patch mirato in S176-finalize-bis + retry singolo step
- **ROSSO ≤6/9** → blocker hard, handoff strategic + root cause analysis (probabile bug daemon LID resolution o reply detection)

## Output attesi sessione S176-finalize

1. `data/s176_finalize_report.md` — esecuzione step 7-9 + verdict 9/9
2. Contract TEST_FOUNDER in DB con `status=PAID`
3. Memory entry close S176 9/9 verde
4. Conditional handoff: **S176-bis sanitizer refactor D-32** (prompt scaffold pronto in `prompts/s176_bis_sanitizer_refactor.md` — da creare)

## Context budget S176-finalize

Pre-flight 5% + STEP 7 verify reply 10% + STEP 8-9 verify DB 15% + report 10% = ~40%. Headroom S176-bis sanitizer refactor (~30 righe) **disponibile se 9/9 closure** rapida.

## Decisioni applicate

- **D-07** HITL strutturale primi 20 dealer reali
- **D-11** Test pipeline 5-step su TEST_FOUNDER prima dealer reale
- **D-15** Founder HITL 100% primi 1-3 deal
- **D-16** Dossier ampliamento + carVertical on-demand
- **D-18** Dossier 12 sezioni core (gap → D-31 S177)
- **D-21** Workflow info-broker → communication-broker-garante eBay-style
- **D-25** Image-shield Pillow-only stack (violazione attiva → D-32 fix)
- **D-30** Workflow contatto venditore EU foto extra (BACKLOG conditional)
- **D-31** Dossier ampliamento gap-analysis-first (DEFERRED S177)
- **D-32** Sanitizer refactor LaMa→Pillow rectangle (BLOCKER Day 1 S176-bis)
- **D-OPEN-Q2** P.IVA timing — pagamento cash a consegna €800-1.200
- **D-OPEN-Q5** Pricing range €800-1.200 in conversation, NON landing

## Findings collaterali da NON aprire in S176-finalize (BACKLOG)

1. **iMac branch divergence** (`main` HEAD `fd35965e` history-rewrite vs `origin/master`)
2. **Estrattore VEHICLE_REQUEST `modello=None`** — parsing "BMW x1" non riconosce X1 come modello (LLM compensa)
3. **`pending_replies.scheduled_at` NULL** — scheduler funziona via altra logica, documentare
4. **PDF 3 pagine vs D-18 12 sezioni** — DEFERRED S177 via D-31
5. **Sanitizer LaMa regression** — BLOCKER S176-bis via D-32 (non blocker per finalize 9/9, è blocker per Day 1 reale dopo)

Sprint scope-lock S176-finalize = STEP 7-9 closure only.
