# ARGOS — PRODUCTION HANDOFF COMPLETO — 2026-08-18

> Handoff canonico per continuare ARGOS da **repository code-certified** a **C10 iMac** e poi **C11 pilot S292**.
>
> Questo documento NON autorizza merge, `/resume`, outreach live o modifiche al canonico. Il codice certificato resta identificato dall'esatto `CODE_CERTIFIED_HEAD` sotto.

---

## 0. STATO IN UNA RIGA

**ARGOS è code-certified sul branch isolato, CI GREEN e review HIGH chiusa; NON è ancora LIVE perché manca esclusivamente il gate C10 sul runtime iMac reale, da eseguire senza outreach e con agent PAUSED.**

---

## 1. IDENTITÀ PROGETTO / SOURCE OF TRUTH

- Repository: `lukeeterna/europeanautoscout`
- Business SoT: `docs/ROADMAP.md`, S292
- Branch canonico/base: `s210/audit-master-plan`
- Base SHA certificata per questa serie: `b339bfac7f9985e37211c82d6c5868d7d10ba3cc`
- Branch di lavoro isolato: `sol/argos-canonicalization-20260817`
- **CODE_CERTIFIED_HEAD:** `bc6aed2470409854ae2aa9643f87cbe7443183ec`
- Draft PR: **#2 — ARGOS S292 — production canonicalization and single-writer runtime**
- PR state al freeze: OPEN, DRAFT, MERGEABLE, NON MERGED
- CI finale del code-certified head:
  - workflow: `ARGOS S292 Production Contract`
  - run number: **#48**
  - run id: **32162658656**
  - conclusion: **SUCCESS**
  - test suite: **65 tests, 65 PASS**

Clone MacBook storico/canonico di lavoro:

```text
/Users/macbook/Documents/europeanautoscout
```

Runtime iMac da certificare in C10:

```text
/Users/gianlucadistasi/Documents/app-antigravity-auto
```

**Non riaprire l'archeologia iMac già svolta. C10 deve verificare il runtime presente, non rifare audit generali.**

---

## 2. MODELLO BUSINESS CANONICO S292 — NON REINTERPRETARE

Flusso demand-side:

```text
MICRO-OPERATORE PLAUSIBILE
-> AZZURRA: CREDIBILITÀ
-> MANDATE / DEMAND DISCOVERY
-> DEALER COMMISSIONA
-> SOURCING
-> COVE / EVIDENCE / VEHICLE GRADE / ECONOMICS
-> PHOTO + DATA COMPLETENESS
-> DOSSIER
-> DEAL
-> ENABLEMENT + RETENTION
```

Regole chiuse:

1. ARGOS è facilitatore; non è il venditore/responsabile del veicolo.
2. Profilo dealer / Second Brain può aiutare tono e contesto, ma **non è domanda**.
3. Una classificazione linguistica `VEHICLE_REQUEST` **non è mandato**.
4. `MANDATE_CONFIRMED` richiede `DemandEvidence` tracciabile e commissione esplicita.
5. Prima dell'evidenza diretta, i campi business non provati restano `DA_VERIFICARE` / `n/d` / `NO-VERDICT`.
6. Niente prezzo Italia inventato via moltiplicatori `+12%/+15%`.
7. Niente default inventati Diesel/Benzina/Automatico/Grigio/proprietari/score/costi fissi.
8. Niente falsa referenza, mystery shopper, cliente fittizio o promessa di disponibilità/tempi non verificata.
9. Foto: il numero di immagini non equivale a copertura semantica delle viste.
10. Dossier dealer-ready solo con mandato, candidato coerente, evidence package e sidecar hash-bound.
11. WhatsApp ha un **solo writer**.
12. Nessun contatto live durante sviluppo/CI/C10.

---

## 3. COSA È STATO CHIUSO — UNITÀ / COMMIT CHIAVE

I commit sotto sono riferimenti di reasoning e implementazione. Non devono essere cherry-pickati singolarmente sul canonico: la PR #2 contiene l'integrazione completa.

### Demand / mandato

- `abc454f` — separazione evidenza verificabile vs commissione veicolo; sourcing autorizzato solo con gate S292.
- `b4d077b` — test contratto DemandEvidence.
- `048b876` — la conversazione non può auto-promuoversi a mandato.
- `3444cf5` — `demand_capture.py`: discovery vs istruzione esplicita di ricerca.
- `f98b723` — test demand capture.

### Orchestrazione / CoVe / seller

- `4646134` — `seller_contact.py` fail-closed su DemandEvidence; niente SMTP da listing nudo.
- `95a5578` — orchestratore demand-side canonico.
- `4bb6494` — copertura foto semantica condivisa.
- `51da858` — ARGOS Vehicle Grade evidence-safe, `NO-VERDICT` quando mancano evidenze.

### Second Brain / Azzurra

- `63c1dcd` + `69e51b0` — profilo dealer separato dall'autorità sulla domanda.
- `09817b3` — template-first S292; Day1 non vehicle-first; ACK della richiesta senza falsa disponibilità.
- `9c1887f` — outbound guard finale.
- `4db3a3b` — analyzer deterministico/template-first; LLM non è business authority.

### PDF / dossier / delivery

- `609a416` — sostituzione renderer legacy con PDF evidence-safe.
- `52b0b3d` — boundary dealer-delivery con sidecar atomico PDF metadata/SHA.
- `63fbf89dc750a408f87d42be5c17d703b03cfca2` — FIX HIGH: re-check candidato contro criteri commissionati al boundary finale.
- `bc6aed2470409854ae2aa9643f87cbe7443183ec` — test negativo dedicato del FIX HIGH + **CODE_CERTIFIED_HEAD**.

### Runtime / single writer / automazione

- `64a6320...` — post-send idempotente e compatibile con rollout.
- `e8bd7dd...` — scheduler queue-only iniziale.
- `face3771e5857ef9048b9ebc83af294625cf04b7` — Day1 credibility-safe nel scheduler.
- `ca7e10fd6c34fb7d83cdd8b5655f86f9b3c0643a` — PM2 allineato al runtime S292 via fail-closed entrypoint.
- `df0cdf34a90fedfc64e149397a05b83ef902db03` — `runtime_entrypoint.py`: first boot PAUSED, poi `exec()` del writer Node.
- `0c65ee1cbcecc7976ec2561eed87a528134b6deb` — smoke C10 read-only/no-outreach.

### CI

- `cbdc608...` — prima suite production completa.
- `00f941c...` — anti-drift reso semantico/AST, non grep ingenuo.
- `e222e5a...` — contratto sidecar↔daemon in CI.
- `0652dc7...` — PM2 first-boot fail-closed in CI.
- `3ee9a18...` — C10 smoke incluso nel gate.

---

## 4. FILE RUNTIME AUTORITATIVI E RESPONSABILITÀ

### Demand authority

`src/cove/demand_contract.py`

- `DemandEvidence`
- `require_sourcing_authorization`
- `require_listing_authorization`
- separa evidence, commissione e scorecard dimensions
- non inferisce domanda dal profilo

`wa-intelligence/demand_capture.py`

- interpreta messaggio inbound come discovery o commissione esplicita
- vehicle mention/interest da soli non autorizzano sourcing
- negazioni falliscono closed

`wa-intelligence/state_machine.py`

- `COLD -> CONTACTED -> ENGAGED -> DEMAND_DISCOVERY -> MANDATE_CONFIRMED -> CONVERTING`
- `VEHICLE_REQUEST` entra in discovery
- `record_verified_mandate()` è l'unico path che crea `MANDATE_CONFIRMED`
- handoff sintetici rimossi
- `outreach_authorized` è separato dal mandato

### Conversation / outbound

`wa-intelligence/templates.py`

- copy fisso evidence-safe
- factual slots mancanti => template vuoto/fail closed
- Day1 credibility-first
- vehicle proposal richiede facts/economics

`wa-intelligence/s292_outbound_policy.py`

- policy semantica finale
- blocca vehicle push prima del mandato
- blocca falsa referenza / disponibilità / tempi non provati
- riconosce e blocca vecchie righe synthetic/mystery shopper

`wa-intelligence/outbound_guard.py`

- verifica state machine + validator + S292 policy immediatamente prima del transport

`wa-intelligence/response-analyzer.py`

- analyzer deterministico/template-first
- stessa CLI consumata dal daemon
- salva intent/state/candidate reply
- bridge rows con `template_id` + `inbound_msg_id`
- commissione esplicita può creare DemandEvidence e mandato solo via gate S292

### Single writer

`wa-intelligence/wa-daemon.js`

Invariante certificato CI:

```text
ogni client.sendMessage(...) è dentro guardedSend(...)
```

Responsabilità:

- unico trasporto WhatsApp
- `/send` e `/send-doc` convergono in `guardedSend`
- bridge converge in `guardedSend`
- `/send-multi` e `/send-voice` = `410 LEGACY_TRANSPORT_RETIRED`
- API locale richiede `ARGOS_API_KEY`
- dossier metadata verificato prima del document send
- DB outbound persistito prima del post-send state transition
- business hours / global limit / dealer limit / runtime PAUSED controllati

`wa-intelligence/runtime_entrypoint.py`

- PM2 production entrypoint
- richiede DB esistente + API key
- primo boot: `agent_status=PAUSED`
- non sovrascrive un ACTIVE esplicitamente ottenuto in seguito
- nessun transport code
- `execv(node, wa-daemon.js)` => resta un solo writer

`wa-intelligence/post_send_update.py`

- idempotency table `argos_post_send_events`
- `BEGIN IMMEDIATE`
- stesso event/WA id non incrementa due volte outbound/state

### Zero-founder ordinary loop

`wa-intelligence/outreach_scheduler.py`

- **queue-only**, mai WhatsApp
- default runtime OFF: `ARGOS_AUTOMATION_ENABLED=0`
- richiede `outreach_authorized=1`
- Day1 / Day7 / Day12
- no follow-up se inbound successivo
- re-run outbound guard prima di accodare
- daemon rifà il guard prima del transport

### Photo / seller / economics / readiness

`src/cove/photo_coverage.py`

- distingue presenza immagine vs vista semantica verificata
- provenance necessaria

`src/cove/seller_contact.py`

- seller side-effect richiede mandato S292
- dry-run come path esplicito

`src/cove/deal_economics.py`

- costi/riferimenti devono essere espliciti e tracciabili
- dati incompleti => `NO-VERDICT`

`src/cove/argos_grade.py`

- grade A-E solo con evidenza minima
- sconosciuto => `NO-VERDICT`, non 0.5/default

`src/cove/dossier_standard.py`

- readiness separata dagli altri score
- mandatory: identity/price/km/photo semantic views/vehicle grade/economics/fraud/demand authorization
- seller contact inviato NON equivale a seller availability confirmed
- missing important => REVIEW, non dealer-ready

### Dealer-delivery artifact

`tools/scripts/pdf_generator_enterprise.py`

- renderer evidence-safe
- review mode separato da dealer-delivery
- nessun RAW fallback per foto
- niente default business inventati

`tools/scripts/argos_dealer_delivery.py`

Boundary production del dossier che può lasciare ARGOS:

1. valida DemandEvidence;
2. legge il candidato reale dal DB;
3. **ri-verifica candidato vs criteri commissionati**;
4. genera il PDF in `dealer_delivery=True` (readiness gate);
5. scrive `<pdf>.metadata.json` atomico;
6. sidecar contiene dealer/evidence/listing/file SHA-256;
7. daemon verifica sidecar + hash prima dell'invio documento.

### C10

`tools/scripts/argos_c10_smoke.py`

Read-only/no-outreach. È il gate locale da usare sull'iMac.

---

## 5. PROVE CI FINALI — EVIDENZA, NON ASSUNZIONE

Code-certified head:

```text
bc6aed2470409854ae2aa9643f87cbe7443183ec
```

Workflow:

```text
ARGOS S292 Production Contract
run #48
run id 32162658656
conclusion SUCCESS
```

Risultato suite:

```text
Ran 65 tests
OK
```

Gate aggiuntivi tutti PASS:

- production Python modules compile
- `node --check wa-intelligence/wa-daemon.js`
- `node --check wa-intelligence/ecosystem.config.js`
- C10 smoke CLI import/help
- `guardedSend` contiene tutti i `client.sendMessage`
- legacy multi/voice retired
- dealer-delivery sidecar ↔ daemon contract
- first-boot PAUSED ↔ PM2 entrypoint
- semantic anti-drift

Warning non bloccante nel post-cleanup del runner:

```text
fatal: No url found for submodule path 'tools/gsd' in .gitmodules
```

È avvenuto nel cleanup `actions/checkout` **dopo** i gate e il job è concluso `success`; non è un FAIL runtime né test. Non aprire una deviazione sul submodule durante C10.

---

## 6. REVIEW INDIPENDENTE — FINDING MATERIALI

### HIGH — CHIUSO

Problema trovato al boundary dealer-delivery:

- un mandato valido non necessariamente contiene `listing_id` fin dall'origine;
- `require_listing_authorization()` consente correttamente un mandato generico a criteri;
- senza un secondo match finale, un caller errato avrebbe potuto tentare il rilascio di un listing diverso dai criteri (esempio: mandato BMW X3, candidato Audi Q5).

Fix:

```text
tools/scripts/argos_dealer_delivery.py
commit 63fbf89dc750a408f87d42be5c17d703b03cfca2
```

Test negativo:

```text
test_wrong_vehicle_cannot_use_valid_mandate
```

Il test è PASS nel run #48.

### Altri boundary rivisti

- `post_send_update.py`: transazione/idempotenza coerenti; nessun HIGH/MED aperto.
- `runtime_entrypoint.py`: nessun transport; first boot PAUSED; nessun HIGH/MED aperto.
- `state_machine.py`: mandato solo da DemandEvidence verificata; nessun HIGH/MED aperto.
- `dossier_standard.py`: evidence-safe / no economics invention; nessun HIGH/MED aperto.
- `outreach_scheduler.py`: queue-only + outreach_authorized + final guard; nessun HIGH aperto.

---

## 7. DEBITO NON BLOCCANTE — NON TOCCARE PRIMA DI C10

### Buffered inbound `processed=0`

Il daemon aggrega più messaggi inbound e passa all'analyzer un evidence-id composto (`id1+id2+...`). La business evidence resta tracciabile, ma l'helper dell'analyzer può aggiornare come `processed` solo il compound id invece delle singole righe.

Effetto attuale:

- non crea secondo writer;
- non crea automaticamente un nuovo transport;
- non bypassa DemandEvidence/guard;
- non è un blocker C10.

Backlog post-C10: normalizzare l'update sulle singole righe del batch con test dedicato, in commit separato.

---

## 8. C10 — OBIETTIVO

Provare sul runtime iMac reale, **senza inviare niente**, che:

1. il tree è esattamente quello code-certified;
2. worktree è clean;
3. Python 3.13 / Node / PM2 sono presenti;
4. `.env`, primary DB, bridge DB sono presenti;
5. API key è configurata;
6. LocalAuth WA esistente viene riusato;
7. automazione è disabilitata;
8. nessun dealer è già `outreach_authorized=1` durante certificazione;
9. nessuna riga bridge già approved/pending può partire;
10. runtime non è ACTIVE;
11. PM2 avvia daemon + scheduler corretti;
12. `/health` risponde `runtime=argos-s292-single-writer` e `agent_status=PAUSED`;
13. nessun `/resume` viene chiamato.

**C10 non include pilot dealer.** Il pilot è C11.

---

## 9. C10 — PROCEDURA ESATTA iMac

### 9.1 Presupposto

La directory in cui si eseguono i comandi deve contenere esattamente:

```text
CODE_CERTIFIED_HEAD=bc6aed2470409854ae2aa9643f87cbe7443183ec
```

Non usare il commit documentale che aggiunge questo handoff come sostituto del code-certified head se il runtime non lo contiene.

### 9.2 PREDEPLOY — READ ONLY

Dalla root runtime revisionata:

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode predeploy \
  --repo-root "$PWD" \
  --expected-head "bc6aed2470409854ae2aa9643f87cbe7443183ec" \
  --pretty
```

**STOP immediato se exit != 0 o `"ok": false`.**

Non usare durante certificazione:

```text
--allow-authorized-dealers
--allow-pending-bridge
```

Se servono per far passare C10, C10 non è realmente safe: investigare il dato reale.

### 9.3 START/RELOAD PM2 — RUNTIME RESTA PAUSED

Solo se PREDEPLOY GREEN:

```bash
cd wa-intelligence
pm2 startOrReload ecosystem.config.js --update-env
pm2 save
cd ..
```

`runtime_entrypoint.py` deve preservare/creare:

```text
agent_status=PAUSED
```

### 9.4 POSTDEPLOY — NO OUTREACH

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode postdeploy \
  --repo-root "$PWD" \
  --expected-head "bc6aed2470409854ae2aa9643f87cbe7443183ec" \
  --pretty
```

Atteso:

```text
ok=true
pm2 argos-wa-daemon online
pm2 argos-outreach-scheduler online
local /health reachable
runtime=argos-s292-single-writer
agent_status=PAUSED
bridge_enabled=true
```

Se la sessione WA deve risultare già autenticata, dopo il primo POSTDEPLOY GREEN:

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode postdeploy \
  --repo-root "$PWD" \
  --expected-head "bc6aed2470409854ae2aa9643f87cbe7443183ec" \
  --require-connected \
  --pretty
```

### 9.5 VIETATO IN C10

NON eseguire:

```text
POST /resume
ARGOS_AUTOMATION_ENABLED=1
outreach_authorized=1 su dealer reali
/send
/send-doc
pilot live
merge PR #2
```

---

## 10. SE C10 FALLISCE — FAIL CLOSED

Non correggere “a tentativi” sul runtime live.

Per ogni FAIL riportare:

```text
CHECK_NAME
DETAIL
exit code
HEAD
pm2 jlist rilevante
/health se disponibile
```

Classificazione:

- HEAD/worktree mismatch -> STOP, nessun deploy.
- DB/bridge/sessione mancanti -> STOP, risolvere path/config, non creare dati finti.
- API key mancante -> STOP.
- automation enabled -> STOP e riportare origine env.
- authorized dealers > 0 -> STOP e identificare i record; non usare override in certificazione.
- approved pending bridge > 0 -> STOP e identificare le righe; non inviarle.
- runtime ACTIVE -> STOP e riportare perché; non iniziare pilot.
- PM2 process offline -> leggere log, correggere su branch separato se è codice.
- `/health` non S292/PAUSED -> STOP.

---

## 11. C11 — SOLO DOPO C10 GREEN

C11 è il pilot live S292. Non partire automaticamente alla chiusura di C10.

Ordine consigliato:

1. Registrare nel repo/evidence report l'esito C10 completo.
2. Review del report C10.
3. Merge/release solo con gate esplicito.
4. Selezionare un micro-operatore del pilot autorizzato.
5. Impostare `outreach_authorized=1` soltanto sui record del pilot e con provenienza documentata.
6. Lasciare `ARGOS_AUTOMATION_ENABLED=0` per il primo smoke del transport controllato.
7. Attivare `/resume` solo quando si intende realmente consentire il writer.
8. Per il loop ordinario zero-founder, impostare `ARGOS_AUTOMATION_ENABLED=1` soltanto dopo il primo invio/pilot controllato e verifica audit/bridge/state.
9. Monitorare delivery/error/rate/state; qualsiasi anomalia -> PAUSED.

C11 deve misurare almeno:

- messaggio Day1 effettivamente conforme al template S292;
- inbound persistito una volta;
- discovery non mandato;
- commissione esplicita -> DemandEvidence -> MANDATE_CONFIRMED;
- sourcing solo dopo mandato;
- candidate match prima CoVe e prima dealer-delivery;
- seller contact evidence-gated;
- dossier review/dealer-ready corretti;
- sidecar/hash accettato dal daemon;
- post-send state idempotente;
- zero bypass del writer.

---

## 12. PR #2 — REGOLA DI MERGE

La PR deve restare DRAFT finché C10 non è GREEN.

Stato al freeze code-certified:

```text
PR #2
OPEN
DRAFT
MERGEABLE
base: s210/audit-master-plan @ b339bfac7f9985e37211c82d6c5868d7d10ba3cc
code head: bc6aed2470409854ae2aa9643f87cbe7443183ec
```

Non confondere:

- code-certified head;
- merge ref temporaneo GitHub Actions;
- eventuale commit documentale che contiene questo handoff.

---

## 13. DO NOT — PROSSIMA SESSIONE

Non fare:

- nuova architettura parallela;
- re-audit generale iMac;
- vehicle-first dealer matcher come parent;
- profilo dealer -> demand inference;
- prompt LLM -> mandate;
- `client.sendMessage` fuori `guardedSend`;
- ripristino `/send-multi` o `/send-voice`;
- RAW image fallback;
- costi/mercato/default inventati;
- falsa referenza / mystery shopper;
- human visual approval come ordinary success path sanitizer;
- `ARGOS_AUTOMATION_ENABLED=1` prima del gate;
- `/resume` durante C10;
- contatti dealer per “testare” C10;
- merge prima del C10 locale;
- modifiche a FLUXION.

Non riaprire automaticamente:

- vecchi commit mandatari;
- freeze iMac storico;
- submodule `tools/gsd` warning cleanup CI;
- archaeology del daemon legacy già ritirato.

---

## 14. PROMPT DI CONTINUAZIONE — NUOVA SESSIONE SOL

Copia integralmente questo prompt nella nuova sessione:

```text
RIPRENDI ARGOS / europeanautoscout ESATTAMENTE DAL GATE C10.

Leggi integralmente come fonte primaria:
  docs/handoff/ARGOS_PRODUCTION_HANDOFF_2026-08-18.md

Repo:
  lukeeterna/europeanautoscout

Business SoT:
  docs/ROADMAP.md — S292 demand-side.

Branch di lavoro certificato:
  sol/argos-canonicalization-20260817

Base canonica:
  s210/audit-master-plan
  BASE_SHA=b339bfac7f9985e37211c82d6c5868d7d10ba3cc

CODICE CERTIFICATO — NON RIDIAGNOSTICARE / NON RISCRIVERE:
  CODE_CERTIFIED_HEAD=bc6aed2470409854ae2aa9643f87cbe7443183ec
  PR #2 draft, open, mergeable
  CI ARGOS S292 Production Contract run #48 / id 32162658656 = SUCCESS
  65/65 test PASS
  single-writer PASS
  sidecar↔daemon PASS
  first-boot PAUSED PASS
  semantic anti-drift PASS

Obiettivo unico della sessione:
  portare C10 iMac a GREEN senza outreach reale; poi preparare il gate C11.

NON rifare:
  DemandEvidence, demand_capture, state machine S292, templates, outbound_guard,
  response-analyzer, single-writer wa-daemon, scheduler queue-only,
  post_send idempotente, photo coverage, Second Brain boundary,
  ARGOS Grade, PDF renderer, dealer-delivery sidecar, CI.

Finding HIGH già trovato e CHIUSO:
  dealer-delivery ri-verifica il candidato contro i criteri commissionati;
  test_wrong_vehicle_cannot_use_valid_mandate è PASS nel run #48.

C10 deve usare:
  tools/scripts/argos_c10_smoke.py

Sull'iMac, dalla root esatta del runtime revisionato, prima esegui SOLO:

/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode predeploy \
  --repo-root "$PWD" \
  --expected-head "bc6aed2470409854ae2aa9643f87cbe7443183ec" \
  --pretty

Se PREDEPLOY non è completamente GREEN: STOP MUTATION e analizza soltanto i check rossi.
NON usare --allow-authorized-dealers o --allow-pending-bridge per farlo passare.

Se PREDEPLOY è GREEN:

cd wa-intelligence
pm2 startOrReload ecosystem.config.js --update-env
pm2 save
cd ..

Poi:

/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode postdeploy \
  --repo-root "$PWD" \
  --expected-head "bc6aed2470409854ae2aa9643f87cbe7443183ec" \
  --pretty

Durante C10:
  ARGOS_AUTOMATION_ENABLED deve restare 0.
  agent_status deve restare PAUSED.
  NON chiamare /resume.
  NON autorizzare dealer.
  NON inviare WhatsApp/documenti.
  NON mergeare PR #2.

Se POSTDEPLOY è GREEN, opzionalmente verifica la sessione WA con --require-connected,
sempre PAUSED e senza invii.

Dopo C10 GREEN:
  aggiorna evidence/report C10, fai review del risultato e prepara C11 pilot S292.
  Non partire live senza gate esplicito.

Debito non bloccante noto:
  nei batch inbound le singole righe possono restare processed=0; non crea transport;
  correggerlo solo dopo C10 e in commit separato.

Non cambiare progetto. Non toccare FLUXION.
```

---

## 15. DEFINITION OF DONE PRODUCTION

ARGOS può essere dichiarato **LIVE production** soltanto quando sono vere TUTTE:

- [x] S292 demand contract implementato
- [x] state machine non promuove classifier a mandato
- [x] demand-side orchestrator
- [x] evidence-only economics
- [x] semantic photo coverage
- [x] seller contact mandate-gated
- [x] Vehicle Grade evidence-safe
- [x] dossier readiness evidence-safe
- [x] PDF truthfulness
- [x] dealer-delivery sidecar/hash
- [x] candidate-vs-mandate re-check finale
- [x] Second Brain non authoritative sulla domanda
- [x] Azzurra template-first
- [x] single WhatsApp writer
- [x] queue-only scheduler
- [x] first boot PAUSED
- [x] post-send idempotente
- [x] CI production contract GREEN
- [x] 65/65 offline tests PASS
- [x] independent boundary review senza HIGH/MED aperti
- [ ] **C10 PREDEPLOY iMac GREEN**
- [ ] **C10 POSTDEPLOY iMac GREEN**
- [ ] C10 connected check se richiesto
- [ ] merge/release controllato
- [ ] C11 live S292 pilot GREEN

Fino alla chiusura degli ultimi punti, stato corretto:

```text
REPO-PRODUCTION-READY / CODE-CERTIFIED
C10 iMac PENDING
NOT LIVE
```
