# S165 — E2E Real Interactive con Luke come TEST_FOUNDER (gate Day 1 Stile Car)

## Contesto (autoportante — leggi anche se MEMORY.md non disponibile)

S164 chiuso **RETRACTED** (no green) 2026-05-12 ~19:00 su contestazione esplicita Luke:
> "ma che chiudi, nessuna operazione nel mondo reale, il contatto con founder deve avvenire realmente con risposta, tutto deve avvenire realmente. no green light"

I 4 step S164 erano simulazione automatica: response stringhe iniettate via test_e2e_full.py, contract creato via admin endpoint `POST /api/v1/contract/create` con dati hardcoded, sign via JSON-only POST (bypass form web), mark-paid finto. `wa_sent:true` daemon-accept non equivale a "Luke ha visto e reagito".

**Vincolo Luke `feedback_e2e_full_test_founder_before_day1.md`**: NESSUN Day 1 reale a dealer (Stile Car o altri) finché pipeline COMPLETA contatto → response → dossier → fattura → bonifico non è verificata end-to-end su TEST_FOUNDER `393314928901` con Luke fisicamente nei panni del dealer.

**Vincolo Luke `feedback_test_founder_means_real_interactive.md`** (nuovo S164): "E2E test_founder" = Luke umano riceve WA + risponde fisicamente + clicca sign URL + bonifico vero. NON unit test, NON admin API call dummy.

## Goal sessione

Luke vive 5 step da TEST_FOUNDER su 393314928901, ogni step triggerato dal flow naturale (non admin endpoint), ogni gate richiede conferma testuale Luke "ho ricevuto/risposto/firmato/pagato" (NON segnali daemon meccanici).

## Pre-conditions (verificare e CONFERMARE con Luke prima di partire)

1. Luke ha telefono TEST_FOUNDER 393314928901 accessibile per ricevere/leggere/rispondere WA.
2. Luke ha browser su telefono o desktop per aprire `https://argos-automotive.pages.dev/contract/<token>`.
3. Luke ha 30-60min disponibili in sessione continua (oppure split su 2-3 giorni naturali — dimmi quale modalità).
4. Conto Luca Ferretti accessibile per bonifico simbolico (€1 anche to-self).
5. Daemon WA online (`ssh imac "curl -s localhost:9191/status"` → `wa_status: connected`).

Se uno qualunque NO → STOP, scrivi handoff S166 con motivo blocco, non procedere.

## Step 0 — Cleanup S164 residuo (obbligatorio prima di Step 1)

Contract test S164 `6e243328f9d67896` è in stato `PAID` nel D1 produzione argos-contracts — inquina la pipeline contratti reali. Pulisci prima:

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/argos-proxy
CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN ../.env | cut -d= -f2) \
  npx wrangler d1 execute argos-contracts --remote \
  --command "UPDATE contracts SET status='TEST_CLEANED' WHERE id='6e243328f9d67896'"

# Verifica
CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN ../.env | cut -d= -f2) \
  npx wrangler d1 execute argos-contracts --remote \
  --command "SELECT id, status FROM contracts WHERE id='6e243328f9d67896'"
# Atteso: status=TEST_CLEANED
```

Se wrangler fallisce per macOS 11 warning → workaround: query D1 via REST API Cloudflare diretta (curl con CLOUDFLARE_API_TOKEN).

## Step 1 — Day 1 reale a TEST_FOUNDER (con conferma umana)

1. Identifica veicolo reale BMW X3 (NO inventato): usa dossier S164 `dossiers/ARGOS_BMW_X3_2021_TEST_FOUNDER_20260512_184359.pdf` se ancora valido, oppure refresh:
   ```bash
   python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 40000 --dealer "TEST_FOUNDER"
   ```
2. Estrai dal JSON listing top 1 PROCEED: anno, km, prezzo, paese, anomalia prezzo (€ delta vs benchmark).
3. Componi Day 1 secondo regole `.claude/rules/communication.md` + `/outreach-day1`:
   - Max 5 righe
   - Veicolo reale numeri reali
   - Domanda chiusa monosillabica
   - Archetipo NARCISO (TEST_FOUNDER assegnato così nel DB)
   - MAI: "Germania", "import", "premium", "cerco auto", "estero" (regola CLAUDE.md)
4. Mostra messaggio a Luke per OK prima di inviare.
5. Invia via daemon (NON via test_e2e_full.py):
   ```bash
   WA_API_KEY=$(grep WA_API_KEY .env | cut -d= -f2)
   curl -X POST http://192.168.1.2:9191/send \
     -H "X-API-Key: $WA_API_KEY" -H "Content-Type: application/json" \
     -d '{"phone":"393314928901","message":"<DAY1_REALE>"}'
   ```
6. **Gate Step 1**: Luke conferma testualmente "ho ricevuto e letto su WA". NON `wa_sent:true`.

## Step 2 — Risposta REALE Luke + analyzer + reply schedulata

1. Luke risponde su WA come farebbe un dealer reale (libero su tono, contenuto, lunghezza). Non scriptato.
2. Verifica INBOUND nel DB iMac:
   ```bash
   ssh gianlucadistasi@192.168.1.2 "sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT timestamp_it, direction, substr(body,1,120), wa_msg_id FROM messages WHERE phone_number LIKE '%393314928901%' AND direction='INBOUND' ORDER BY created_at DESC LIMIT 1;\""
   ```
3. Verifica analyzer ha processato e schedulato reply (cerca log analyzer o nuovo OUTBOUND scheduled):
   ```bash
   ssh gianlucadistasi@192.168.1.2 "sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT timestamp_it, direction, substr(body,1,120) FROM messages WHERE phone_number LIKE '%393314928901%' ORDER BY created_at DESC LIMIT 5;\""
   ```
4. Luke conferma "ho ricevuto reply automatica e ha senso" (giudizio Luke su personalizzazione + variazione + non-spam).
5. **Gate Step 2**: 1 INBOUND vero + 1 OUTBOUND auto-generato + OK testuale Luke su qualità reply.

## Step 3 — Dossier delivery + contract proposal naturale

1. Continua conversazione finché analyzer rileva INTEREST conf>=0.85 (o forza il path con domande dealer su veicolo specifico).
2. Sistema invia dossier PDF via WA automaticamente (Day 3 path con foto HD + secondo veicolo, oppure dossier diretto se analyzer triggera).
3. Luke conferma su WA "ho ricevuto PDF, riesco ad aprirlo, immagini pulite, no watermark dealer DE" (gate visivo S163 + delivery).
4. Solo SE conversazione arriva naturalmente a INTEREST conf>=0.85: analyzer chiama `POST /api/v1/contract/create` con HOLD Telegram → tu approvi su TG → sign URL viene inviato a TEST_FOUNDER via WA.
5. **Gate Step 3**: Luke conferma "ho ricevuto sign URL su WA" + URL appare in conversazione DB iMac.

## Step 4 — Sign reale form web + send-iban + bonifico vero + mark-paid

1. Luke apre sign URL su browser (telefono o desktop), compila form:
   - signer_name reale
   - signature_font tra `[allura, great-vibes, pacifico, dancing-script, sacramento, tangerine, yellowtail, kaushan-script, satisfy, caveat]`
   - consent_fes checkbox = ON
   - submit
2. Verifica D1 contract status = `AWAITING_DELIVERY`:
   ```bash
   CLOUDFLARE_API_TOKEN=$(grep CLOUDFLARE_API_TOKEN .env | cut -d= -f2) \
     npx wrangler d1 execute argos-contracts --remote \
     --command "SELECT id, status, signer_name, signature_font, signed_at FROM contracts WHERE dealer_phone='+393314928901' ORDER BY created_at DESC LIMIT 1"
   ```
3. Per TEST_FOUNDER: salta consegna documenti auto fisica (non applicabile). Admin (tu) triggera send-iban:
   ```bash
   SECRET=$(grep ARGOS_ADMIN_SECRET .env | cut -d= -f2)
   CONTRACT_ID=<da query Step 4.2>
   curl -X POST https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/$CONTRACT_ID/send-iban \
     -H "Authorization: Bearer $SECRET" -H "Content-Type: application/json"
   ```
4. Luke conferma su WA "ho ricevuto IBAN" + Luke fa bonifico simbolico reale (€1 anche to-self su IBAN Luca Ferretti).
5. Quando bonifico arriva (1-2 giorni reali — o accelerato se Luke vuole con conferma manuale):
   ```bash
   curl -X POST https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/$CONTRACT_ID/mark-paid \
     -H "Authorization: Bearer $SECRET" -H "Content-Type: application/json" \
     -d '{"paid_amount_cents":100,"payment_bank":"<banca vera>","payment_reference":"<reference vero bonifico>"}'
   ```
   (paid_amount_cents=100 = €1; usa importo bonifico reale)
6. Luke conferma "ho ricevuto WA conferma pagamento".
7. **Gate Step 4**: D1 status=PAID + Luke conferma + reference bonifico vero registrato.

## Step 5 — Fattura TD17/18/19 (gap S164 BACKLOG)

Decisione Luke richiesta (vedi BACKLOG.md voce "fatturazione TD17/18/19"):

- **(a)** tool digitale ARGOS (Fatture in Cloud API o SDI XML generator) → costruzione dedicata S166+, NON in S165
- **(b)** processo manuale commercialista → trigger Telegram/email post mark-paid + Luke gira a commercialista

Per chiudere S165 verde su step 5: documenta scelta Luke + dimostra trigger funziona (es. notifica TG verso commercialista mock viene inviata post mark-paid).

Se Luke ancora indeciso → S165 chiude verde su step 1-4, step 5 rimane open con scelta entro S166. Day 1 Stile Car può procedere se step 1-4 verde + scelta (b) accettata da Luke come work-around manuale provvisorio.

## Closure criteria (TUTTI obbligatori per VERDE)

- ✅ Step 0: contract S164 dummy pulito (status=TEST_CLEANED in D1)
- ✅ Step 1: Day 1 reale inviato + Luke conferma lettura
- ✅ Step 2: ≥1 INBOUND Luke reale nel DB iMac + ≥1 OUTBOUND analyzer auto + OK Luke su qualità reply
- ✅ Step 3: dossier PDF aperto da Luke + Luke OK visivo no leak + sign URL ricevuto via WA
- ✅ Step 4: D1 contract PAID con signer_name reale Luke + bonifico reference reale + Luke conferma WA conferma pagamento
- ✅ Step 5: decisione Luke (a) o (b) documentata; se (b), trigger TG/email testato post mark-paid

**ARANCIONE/PARTIAL vietato** (vincolo 6 CLAUDE.md). Se non chiude verde → HANDOFF strutturato S166 con stato preciso (a che step bloccato, perché) + Day 1 Stile Car RESTA GATED.

## Vincoli sessione (hard rules)

- **NON** chiamare `POST /api/v1/contract/create` admin endpoint per bypassare flow analyzer → bypass = invalida step 3.
- **NON** dichiarare verde su `wa_sent:true` o HTTP 200 senza conferma testuale umana Luke.
- **NON** simulare risposte dealer — Luke risponde fisicamente come vuole.
- **NON** mockare bonifico — bonifico vero, anche €1.
- **NON** usare test_e2e_full.py come step E2E (= unit test, non E2E reale — lezione S164).
- **Verifica fattuale ogni claim**: "step N verde" → testo Luke + DB query corrispondente. Niente segnale meccanico standalone.
- **Context budget**: `/context` ogni 5-10 turni, sopra 60% chiudi ordinato.
- **Zero cost**: no nuove librerie, no servizi paid.
- **Pattern recognition**: se step blocca per dependency hell o infra issue (es. wrangler macOS 11 warning bloccante, daemon offline, D1 unreachable) → STOP, document gap, NON workaround sintetico.

## File chiave (read-only durante sessione, salvo BACKLOG)

- `wa-intelligence/response-analyzer.py` — daemon-side classifier + reply scheduler
- `wa-intelligence/wa-daemon.js` — daemon su iMac porta 9191
- `argos-proxy/src/routes/contract-create.ts` — flow naturale create (NON da chiamare manualmente)
- `argos-proxy/src/routes/contract-sign.ts` — form web sign endpoint
- `argos-proxy/src/routes/send-iban.ts` + `mark-paid.ts` — admin endpoint OK chiamare manualmente
- `landing/contract/sign.html` + `sign.js` — form Luke compila
- `tools/on_demand_runner.py` — scrape→CoVe→PDF con sanitizer S163 Vision Framework
- `BACKLOG.md` — gap fattura TD17/18/19 (step 5)
- `dossiers/ARGOS_BMW_X3_2021_TEST_FOUNDER_20260512_184359.pdf` — dossier S164 disponibile per Step 3 se ancora valido

## Memory da leggere prima di iniziare (priority order)

1. `feedback_test_founder_means_real_interactive.md` — definizione corretta "E2E real interactive"
2. `feedback_e2e_full_test_founder_before_day1.md` — vincolo hard Luke su Day 1
3. `s164_e2e_retracted_not_real.md` — lezione completa S164 retract + side effects
4. `feedback_no_live_without_test.md` — no Day 1 reale auto-eseguibile
5. `feedback_context_budget_gate.md` — chiusura ordinata sopra 50% context
6. `feedback_false_positive_lazy_import.md` — gate = invocazione reale, mai segnale lazy
7. `feedback_scope_creep_on_ambiguous_request.md` — AskUserQuestion su istruzione ambigua
8. `feedback_decision_support.md` — opzioni tecniche con raccomandazione singola motivata
9. `s163_closure_vision_framework.md` — stato sanitizer S163 (gate parallelo)

## Out-of-scope (defer)

- Send dealer reale Stile Car o altri: BLOCKED finché S165 non verde su step 1-4 + step 5 work-around accettato
- UAT visivo S163 sanitizer standalone (Luke su Finder `/tmp/argos_s163_e2e/`): gate parallelo indipendente
- Nuove feature, refactor, scope discovery
- Tool digitale fattura TD17/18/19: out-of-scope S165, defer S166 se Luke sceglie (a)
- Estensione test analyzer oltre i 5 step

## Apertura sessione attesa

L'agente next session dovrebbe iniziare con:

```
S165 — E2E Real Interactive con Luke come TEST_FOUNDER.

Pre-flight check:
1. ssh imac curl localhost:9191/status → wa_status connected? [verifico]
2. Luke disponibile 30-60min ora, o sessione split su giorni? [chiedo a Luke]
3. Telefono TEST_FOUNDER 393314928901 accessibile? [chiedo a Luke]
4. Conto Luca Ferretti accessibile per bonifico €1? [chiedo a Luke]

Se tutti OK → Step 0 cleanup contract S164 `6e243328f9d67896` + Step 1 compose Day 1.
Se uno NO → handoff S166 con motivo blocco.
```
