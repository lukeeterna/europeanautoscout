# S151 — E2E COMPLETO SIMULATO su TEST_FOUNDER (pre-Day 1 reale)

**Sessione**: S151 (clean context start)
**Data**: 2026-05-01 → continua da S149c chiuso a 78% context
**Scope**: prima del Day 1 reale Stile Car, simulare TUTTA la pipeline E2E con TEST_FOUNDER (393314928901): cold contact → richiesta modello → dossier → contratto firmato → pagamento Stripe.
**Vincolo CTO**: Day 1 reale NON parte finché tutti 5 step E2E sono verdi su TEST_FOUNDER.
**Decisione**: martedì 5/5 → NUOVO SLITTAMENTO. Target Day 1 reale: solo dopo S151+S152 (E2E sim + fix gap).

---

## ⛔ STATO PRECEDENTE (S149c chiuso)

- ✅ Daemon WA outbound + ack 1/2/3 + multi-msg split
- ✅ Templates.py iMac fixato
- ✅ Image sanitizer iMac validato
- ✅ LLM cascade (Groq fallback operativo)
- ✅ Scrape live BMW X3 (10 PROCEED/17)
- 🟡 Reply LLM Day N+ qualità sotto-Cormorant (P1)
- ❌ Stripe pipeline INESISTENTE (zero ref nel codebase, verificato S149)
- ❌ Contratto + firma INESISTENTI (mai progettati)
- ❌ Landing → Stripe checkout INESISTENTE
- ❌ Dossier-on-demand request handler (dealer dice "mandami scheda" → trigger PDF) UNTESTED end-to-end

S149c verdetto era "🟢 GO Day 1 martedì" sul presupposto che Day 1 = solo testo. Luke ha esteso lo scope: vuole **TUTTA** la pipeline simulata su TEST prima di rischiare un dealer reale.

**S149c verdetto AGGIORNATO**: 🟡 GO solo dopo S151 E2E sim verde su tutti 5 step.

---

## 0. Letture obbligatorie (15 min)

1. `.planning/E2E-AUDIT-S149.md` (verdetto + P1 + lista cosa funziona/no)
2. `~/.claude/projects/.../memory/MEMORY.md` entry "2026-05-01 12:50 — S149c"
3. `HANDOFF.md` sezione S151 NEW (sotto sezione S149c)
4. `.claude/rules/communication.md` + `.claude/rules/security.md` + `.claude/rules/cove.md`
5. **NEW**: leggere il progetto **Fluxion** (Luke ti dirà il path — probabile `~/Documents/fluxion-*` o simile) per copiare il flow Stripe + landing checkout + webhook handler

---

## 1. I 5 STEP E2E SIM (target tutti verdi prima di Day 1 reale)

### Step 1 — Cold contact persona-prima
- Invio Day 1 reale a TEST_FOUNDER (testo `DAY1_STILE_CAR.md` adapted con dealer name = "TEST")
- Verifica: payload integro, ack 1/2/3, conferma visiva Luke su telefono
- **Vincolo persona**: Luke deve rispondere COME UN DEALER reale (non "ok funziona") — interpretare Stile Car, archetype RELAZIONALE
- **Pass criteria**: Luca risulta persona credibile (no "lei chi è" sospetto, ma curiosità naturale)
- **Già tested S149b/c parzialmente** (smoke test) — ripetere completo e cronometrato

### Step 2 — Richiesta modello dal dealer (inbound vehicle_request)
- TEST_FOUNDER risponde con richiesta veicolo specifica (es. "mi serve una BMW X3 2022 sotto 35k, automatica")
- Daemon riceve → analyzer classify VEHICLE_REQUEST → estrae parametri (marca, modello, anno, prezzo, optional)
- Trigger automatico scrape on-demand? O Luke approva via Telegram → trigger manuale?
- **Da decidere in S151 step 0**: auto-trigger vs manual-approve flow
- **Pass criteria**: parametri estratti correttamente, trigger pipeline corretta

### Step 3 — Dossier creato + inviato
- Pipeline: scrape AS24 → CoVe scoring → top candidate → image sanitizer → PDF generator → send WA PDF
- Bug noto: PDF generator locale (MacBook) rotto senza PaddleOCR — **fix S151 OPPURE forzare esecuzione su iMac via SSH**
- **Pass criteria**:
  - PDF size > 200KB (con immagini sanitizzate)
  - 6 pagine (cover + specs + 4 immagini + closing)
  - Sanitizer: zero EXIF, banner stripped, dealer name watermark applicato
  - Send via daemon → ack=2 + LETTO
  - Conferma visiva Luke: "il PDF si apre e ha senso"

### Step 4 — Accettazione + contratto firma 10-scelte
**Componente NUOVO da progettare**:
- Dealer dice "ok mi piace, procediamo" → analyzer classify INTEREST/POSITIVE
- Trigger: invio link landing personalizzato `argos-automotive.pages.dev/contract/<token>`
- Landing page contratto:
  - Recap veicolo (modello, prezzo, fee, totale)
  - Form: dealer digita NOME e COGNOME
  - **Selettore firma**: sistema genera 10 varianti di firma stilizzate (font script diversi: Allura, Great Vibes, Pacifico, Dancing Script, Sacramento, etc.) basate sul nome digitato → dealer sceglie la più simile alla sua
  - Click → firma renderizzata su PDF contratto + timestamp + IP + hash
  - PDF contratto firmato salvato + email + WhatsApp notification
- **Stack proposto** (verificare con Fluxion):
  - Cloudflare Pages (frontend)
  - Cloudflare Workers (signature endpoint, hash, store)
  - R2 / D1 (storage contratto firmato)
  - Library JS firma: `@signature_pad/core` o canvas custom con Google Fonts
- **Pass criteria**: TEST_FOUNDER apre link → sceglie firma → contratto PDF generato → notification arriva su WA Luca + email Luke

### Step 5 — Workflow pagamento Stripe
**Componente NUOVO da progettare** (riferimento: progetto Fluxion):
- Post-firma → trigger checkout Stripe
- Modello pagamento ARGOS:
  - Success-fee: NESSUN upfront, fee €800 al momento consegna veicolo
  - Quindi pagamento NON è "upfront purchase" ma "delayed billing on event"
  - Stripe Setup Intent + payment_method saved → charge alla consegna
  - OPPURE Stripe Subscription / Invoice manuale post-consegna
- **Da decidere S151 step 0**: modello Stripe corretto per success-fee (Setup Intent vs Manual Invoice vs Hold/Capture)
- Webhook handler: `payment_intent.succeeded` → marca dealer paid → genera fattura TD24 (electronic invoice)
- Fattura: chi emette? Persona Luca Ferretti = alias commerciale di Gianluca Di Stasi → P.IVA assente attualmente. **Blocker fiscale**: prima fattura richiede struttura legale (P.IVA o forma forfettaria intestata a Gianluca)
- **Pass criteria simulato**: TEST_FOUNDER inserisce carta test Stripe (4242...) → checkout success → webhook fired → DB marca paid → notification fired
- **NON simulato (richiede legal)**: emissione fattura reale con P.IVA

---

## 2. Pre-flight S151 (15 min)

```bash
# 1. iMac up + daemon
ssh -o ConnectTimeout=5 gianlucadistasi@192.168.1.2 "uptime && curl -s localhost:9191/status | grep -E 'wa_status|daily'"

# 2. Backup pre-S151
bash deploy/sync.sh  # se esiste, altrimenti git status pulito

# 3. Stato TEST_FOUNDER pulito
ssh gianlucadistasi@192.168.1.2 'sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite "SELECT current_step, conversation_state, outbound_count FROM conversations WHERE dealer_id=\"TEST_FOUNDER\";"'
# Reset suggested: UPDATE conversations SET current_step='PENDING', conversation_state='COLD', outbound_count=0 WHERE dealer_id='TEST_FOUNDER'
# Confermare con Luke prima di reset

# 4. Daily quota WA
# >= 10 sends disponibili (E2E full consumera 8-10 messaggi)

# 5. Path Fluxion
# Luke fornira il path. Esempio:
# ls -la ~/Documents/Fluxion* 2>&1 || ls -la ~/Documents/fluxion* 2>&1
```

---

## 3. Sequenza S151 (stimata 4-6h, distribuita su S151+S152)

### Phase A — Planning completo (S151, ~2h)
1. Leggere Fluxion (path da Luke) → estrarre flow Stripe + Cloudflare Workers + landing
2. Mappare gap: cosa Fluxion ha che ARGOS non ha
3. Decisione modello pagamento (Setup Intent vs Manual Invoice vs Subscription)
4. Decisione legale: P.IVA Gianluca o blocker?
5. Decisione library firma 10-scelte (Google Fonts script + canvas render)
6. Scrivere `.planning/E2E-SIM-PLAN.md` con:
   - Architettura componenti nuovi (contract page, signature endpoint, payment flow)
   - Lista TODO atomica per ogni step (1-5)
   - Test plan per ogni step (cosa verificare su TEST_FOUNDER)
   - Stima tempo per step
7. Approvazione Luke su plan prima di Phase B

### Phase B — Build componenti nuovi (S152+, ~3-4h)
1. Step 4 contract page: scaffold Cloudflare Pages + Workers
2. Step 4 signature 10-choice picker (Google Fonts + canvas)
3. Step 4 backend: contract generator PDF + storage R2/D1
4. Step 5 Stripe Setup Intent flow
5. Step 5 webhook handler + DB integration
6. Trigger flow: analyzer INTEREST → send contract link

### Phase C — E2E sim completo (S153, ~1-2h)
1. Reset TEST_FOUNDER state
2. Run step 1: Day 1 → TEST_FOUNDER risponde come Stile Car RELAZIONALE
3. Run step 2: TEST_FOUNDER richiede BMW X3 → analyzer extract → trigger scrape
4. Run step 3: dossier generato + sent
5. Run step 4: TEST_FOUNDER apre contract link → firma 10-scelte → PDF generato
6. Run step 5: TEST_FOUNDER inserisce carta test Stripe → webhook → DB paid
7. Time-cronometrato + bug log
8. Decisione finale: GO Day 1 reale Stile Car o ulteriore iterazione

---

## 4. Vincoli S151 (ereditati S149c + nuovi)

- ✋ Day 1 reale Stile Car NON PARTE finché 5 step E2E sim non sono verdi su TEST_FOUNDER
- ✋ Stripe NON in produzione finché P.IVA situazione legale risolta (test mode keys ok)
- ✋ Contract page NON pubblicato in production finché firma flow validato
- ✋ Zero modifiche al daemon WA (S149 fix solido)
- ✋ Zero esperimenti di sicurezza con dati reali (no PII Luke nei log condivisi)
- ✋ Se context >75% in S151 e Phase A non finita → **STOP, S151b clean restart**
- ✋ Documentare TUTTO in `.planning/E2E-SIM-PLAN.md`

---

## 5. Scope creep da rifiutare in S151

- Refactoring del codebase ARGOS esistente
- Fix del PDF generator locale MacBook (workaround: forzare iMac via SSH è ok)
- Fix Gemini MAX_TOKENS (cascade Groq tiene)
- Riscrittura system prompt analyzer (S150+)
- Migration database
- Aggiunta nuovi scrapers
- Marketing / landing copywriting
- Persona LinkedIn updates

S151 è SOLO planning E2E sim. Build = S152+.

---

## 6. Reference rapidi

- iMac IP: `192.168.1.2`
- Daemon: `localhost:9191`
- TEST_FOUNDER: `393314928901`
- Stile Car (NO touch): `393334254654`
- DB iMac: `/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`
- Repo: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
- Landing prod: `https://argos-automotive.pages.dev`
- WA daemon: `wa-intelligence/wa-daemon.js`
- Analyzer: `wa-intelligence/response-analyzer.py`
- Audit S149: `.planning/E2E-AUDIT-S149.md`

---

## 7. Domande aperte per Luke (rispondere a inizio S151)

1. **Path Fluxion**: dove sta il progetto da cui copiare flow Stripe + Cloudflare?
2. **Stato P.IVA Luca/Gianluca**: forfettario aperto? deroga "sistemiamo dopo"?
3. **Stripe account**: già esiste? key test/prod? (no commit di key — verifica `.env`)
4. **Cloudflare account**: già attivo per `argos-automotive.pages.dev` (Wrangler ok)? Workers/R2/D1 quote?
5. **Contract template**: esiste un PDF reference (anche da settore auto) o va disegnato da zero?
6. **Firma 10-scelte**: Google Fonts script (open source, gratis) ok? Library `signature_pad` ok?
7. **Reset TEST_FOUNDER**: confermi reset state machine prima di S151 step 1?

---

## 8. Target di fine S151

✅ `.planning/E2E-SIM-PLAN.md` completo (architettura + TODO + test + tempi)
✅ Decisioni prese (modello Stripe, library firma, P.IVA position)
✅ Lista gap Fluxion → ARGOS chiarita
✅ Approvazione Luke su plan
✅ Prompt S152 build pronto

**NON in S151**: code, deploy, test E2E reale. Solo plan.

---

## 9. Decisione CTO ereditata da S149c

S149c era 🟢 GO Day 1 martedì 5/5 sul presupposto "Day 1 = solo testo, P1 off-path".
**Luke ha esteso lo scope**: vuole TUTTO il flow validato prima di rischio dealer reale.

**S151 verdetto provvisorio**: Day 1 reale rinviato di 1-2 settimane (S151+S152+S153). Slittamento ~7-14gg.

**Rischio asimmetrico riconfermato**: bruciare primo dealer Sud = perdita 3-5 dealer via referral. Se Stile Car risponde "ok procediamo, mandami fattura" e ARGOS non ha contract+payment funzionante → autogol totale. Slittare > rischio.

**Trade-off accettato**:
- Slittamento +7-14gg
- Riduzione rischio failure full pipeline ~95%
- Possibile scoperta blocker legali (P.IVA) → ulteriore slittamento ma con visibilità

**Stripe NON M3 separata**: ridotta in S151 dentro lo scope perché Luke vuole flow completo.
