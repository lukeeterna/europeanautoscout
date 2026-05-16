# S176-finalize — Report ROSSO 6/9 (closure strutturale)

**Data**: 2026-05-16 ~18:00 CEST
**Verdict**: ROSSO 6/9 — STEP 7 blocker strutturale CONTRACT_REQUEST intent mancante
**Handoff**: `prompts/s177_contract_intent_implementation.md`

## Esecuzione step-by-step

### Pre-flight (VERDE 3/3)
- PM2: `argos-wa-daemon` online uptime 6h, `argos-dashboard` 7h, `argos-cf-monitor` 11d
- TEST_FOUNDER `conversations.current_step=DAY1_SENT`, `handoff_source=mystery_shopper`
- Fix S175.1 attivo: 7 occorrenze pattern `vehicle_request_broker|_check_vehicle_hallucination|_check_broker_lexicon_ban|VEHICLE_REQUEST_BROKER_FALLBACK` in `response-analyzer.py`

### STEP 7 — Verify reply TEST_FOUNDER (ROSSO)

**Sequence fattuale**:
1. 17:40 prima query DB → zero INBOUND post-16:17 PDF send
2. Tail daemon log 70s → silenzio assoluto
3. Luke ha inviato messaggio nel verso sbagliato (`3281536308 → 3314928901` invece di `3314928901 → 3281536308`) — pattern UX da documentare in prompt futuri
4. 17:52:47 dopo correzione direzione: INBOUND `"Va bene , mi mandi il contratto"` ingested OK, LID resolve OK, buffer flush OK, analyzer triggered (msg_id `msg_1778946767736_b0a4v`)
5. 17:53:08 AMBRA reply prodotta: `reply_e9be3ac6`, `reply_label=LLM_MULTI`, `approved=1`, `sent=0`

**Reply AMBRA (sbagliata)**:
```
"ciao, senti, non ho ancora trovato la bmw x1 del 2020 che cerchi, ma sto lavorando per te, ok?"
"sto verificando alcune opzioni, ti aggiornero entro 24-48h, va bene? Luca"
```

**Atteso**: classifier riconosce `CONTRACT_REQUEST` → handler genera contract token via `argos-proxy.gianlucanewtech.workers.dev` → AMBRA spedisce URL `https://argos-automotive.pages.dev/sign?id=<token>`.

**Azione di sicurezza**: `UPDATE pending_replies SET approved=0 WHERE id='reply_e9be3ac6'` — reply sbagliata bloccata, daemon non la spedirà.

## Root cause strutturale

`grep -in 'CONTRACT_REQUEST|contract_request|firmo|firma il contratto|proseguo|/sign|signature' wa-intelligence/response-analyzer.py` → **0 match operativi**. Unica occorrenza "firma" = prompt LLM `"Firma 'Luca' solo nell'ultimo"`.

Pipeline reactive end-to-end **MAI implementata oltre vehicle_request_broker**:
- S173 ha aggiunto AMBRA P3 prompt modules (vehicle_request_broker, identity_post_handoff)
- S175.1 ha aggiunto ResponseValidator (hallucination + lexicon ban)
- **Nessuno ha implementato intent CONTRACT_REQUEST + handler contract creation + state transition `DAY1_SENT → DOSSIER_SENT → CONTRACT_REQUESTED`**

Prompt S176-finalize assumeva componente esistente non verificato in codice. Pattern famiglia S159/S160 (planning su componente supposto). Vincolo #1 violato in fase pianificazione.

## Critica strutturale (vincolo #4)

1. **Assunzione errata**: prompt promette "AMBRA classifier riconosce CONTRACT_REQUEST auto-spedisce URL" — mai grep verificato
2. **Rompe già adesso**: primo dealer reale post-PDF accept = pipeline ferma a info-broker loop
3. **Pattern noto S159/S160**: planning su componente non verificato → false-positive
4. **Stato DB inconsistente**: `current_step` non avanza dopo PDF send (resta DAY1_SENT), analyzer non ha contesto "dossier inviato"

## Componenti DA implementare (S177)

1. **Classifier intent CONTRACT_REQUEST** in `response-analyzer.py`:
   - Pattern regex: `r'\b(mi mandi|mandami|inviami|mandate?mi).{0,30}(contratto|contract|firma|signature|sign)\b'` + variants ("va bene proseguo", "ok firmo", "facciamo il contratto", "procediamo")
   - Priorità routing: BEFORE LLM_MULTI fallback, AFTER VEHICLE_REQUEST
   - Solo se `conversations.current_step IN ('DOSSIER_SENT','DAY3_SENT')` (gating per evitare false-positive su Day 1)

2. **Handler CONTRACT_REQUEST**:
   - Call Cloudflare Worker `POST /api/v1/contract/create` con `{dealer_id, vehicle_ref, fee=800}`
   - Worker ritorna `{contract_id, sign_url}`
   - AMBRA reply template: `"perfetto. firmiamo qui: {sign_url}\\nappena firmato le mando IBAN per il bonifico. Luca"`
   - Insert `pending_replies` con `reply_label=CONTRACT_REQUEST` + `approved=NULL` (HITL D-07)

3. **State transition**:
   - PDF send via `/send-doc` → trigger `UPDATE conversations SET current_step='DOSSIER_SENT', state_updated_at=now`
   - CONTRACT_REQUEST handler success → `UPDATE conversations SET current_step='CONTRACT_REQUESTED'`
   - Aggiunge contesto a successivi LLM call

4. **Test E2E**:
   - Replay TEST_FOUNDER: reset `current_step='DOSSIER_SENT'`, mantieni inbound 17:52:47, force re-analyze → verify reply_label=CONTRACT_REQUEST + URL signature
   - STEP 8 sign + STEP 9 mark-paid già operativi via dashboard:8080 (verified S164)

## Decisione priorità S177 vs S176-bis sanitizer

**S177 (contract intent) PRIMA di S176-bis (sanitizer)**:

| Asse | S177 | S176-bis |
|---|---|---|
| Blocca | Primo deal reale end-to-end (chiunque accetti dossier) | Day 1 dealer reale "fresh" con foto autopanned |
| Sequenza valore | Contract = PUNTO conversione revenue | Sanitizer = qualità asset pre-conversione |
| Costo dev | ~2-3h (regex + handler + worker call + test) | ~1h (LaMa→Pillow rectangle refactor D-32) |
| Dipendenza | TEST_FOUNDER inbound già pronto (17:52:47), replay rapido | Independent |

S177 sblocca catena valore completa (D-21 workflow info-broker → communication-broker-garante). S176-bis blocca scaling Day 1, ma se contract non funziona allora il dossier perfetto è inutile.

**Ordine**: S177 → S176-bis → Day 1 reale (Stile Car).

## Findings collaterali (BACKLOG)

1. **Inversione direzione test reactive UX** — chiarire in tutti prompt futuri: TEST_FOUNDER reactive = SIM `3314928901` → SIM `3281536308`, MAI viceversa (auto-eco filtrato dal daemon)
2. **PDF send non aggiorna `current_step`** — root cause classifier degeneration su LLM_MULTI (mancano contesto fase)
3. **D-32 sanitizer regression** — invariato, resta blocker Day 1 dealer reale
4. **D-31 dossier 12 sezioni** — invariato, deferred S178+

## Stato safe sessione

- `reply_e9be3ac6` BLOCKED (`approved=0, sent=0`) — daemon non spedirà nulla a TEST_FOUNDER
- INBOUND `Va bene , mi mandi il contratto` (msg_id `msg_1778946767736_b0a4v`) preservato in DB — replay S177 partirà da qui
- Daemon online, conversation state intatta, no side effects DB

## Verdict finale

**STEP 4-6 S176 VERDE** (pipeline + PDF + send-doc) + **STEP 7 S176-finalize ROSSO** (intent mancante) + **STEP 8-9 NON ESEGUITI** (gated da STEP 7).

Score finale E2E reactive: **6/9 confermato VERDE, 3/9 BLOCKED su S177**.
