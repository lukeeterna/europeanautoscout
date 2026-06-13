# Backlog — problemi trovati ma non nel sprint corrente

<!-- Aggiungi qui durante lo sprint. Non risolvere ora. -->

## S273 2026-06-13 — #S273-ASTE [ICEBOX — canale SOURCING #2, NON PLAN item]

### 🧊 Aste giudiziarie IT come canale ACQUISTO — parcheggiato (esito FASE 0: NON-FATTIBILE-ORA senza autorizzazione)

**TRIGGER DI RIEVOCO (entrambi, verificati non assunti)**: (a) primo dossier DE→IT reale
CHIUSO con un dealer vero (primo CLOSED_WON); (b) baseline AS24 consolidata (pool geo==IT,
experiment EU-wide OFF). Finché (a)&(b) non sono veri questo NON parte. È il secondo canale,
non apre il primo. Prossimo lavoro reale = ADD-1 / prezzo_de reale / primo dealer — NON questo.

**ESITO FASE 0 (research S273, provato — non assunto)**:
- I veicoli vivono SOLO nel circuito IVG (`astagiudiziaria.com/inserzioni/autoveicoli-e-cicli`
  + singoli IVG `/ricerca/mobili`). NON sul PVP-immobili.
- `astagiudiziaria.com/robots.txt` (verificato): `Disallow: /` + `Disallow: /json/*` +
  `Disallow: /stampa-pdf/*`, Allow solo Googlebot/social/GPTBot. → l'endpoint JSON strutturato
  ESISTE ma è esplicitamente off-limits. Scrape del canale-veicoli = robots-vietato.
- PVP non ha read-API: i 3 parser OSS noti usano tutti Playwright/browser-scrape, e sono tutti
  immobiliari/generici (nessuno copre veicoli). Vedi reference sotto.
- GDPR/Garante: "disponibilità pubblica ≠ legittimità scraping" (avvisi contengono dati personali).
- **Conclusione**: nessun metodo automatizzato ToS-compliant oggi sul canale-veicoli. Vie pulite =
  solo autorizzative: MyAsta (alert email ANVG, manuale) o accesso autorizzato/partnership ANVG/IVG.
  API commerciali (gestionale-aste/miglioriaste) solo SE coprono veicoli E ToS-riuso ok (entrambe
  immobili-centriche, key "test" da verificare). Scrape robots-vietato = STOP, decisione Luke col
  rischio legale/reputazionale in chiaro, MAI CC in autonomia.

**MODELLO DI PRODOTTO (vale a prescindere dall'accesso, da preservare se si riapre)**:
- Asta = canale ACQUISTO (come la Germania), MAI un comparabile. Entra nel verdetto-margine come
  prezzo-acquisto alternativo; NON entra MAI in `get_it_distribution` (il pool-comp resta AS24
  geo==IT puro — mischiarla = banda artificialmente bassa = falso-REJECT).
- Tre prezzi distinti, mai collassati: prezzo_base (perizia, è un'ESCA — errore speculare all'X1) |
  prezzo_minimo | prezzo_aggiudicazione (reale, noto solo a vendita conclusa). Il margine si calcola
  sull'AGGIUDICAZIONE stimata. Se non prevedibile → il verdetto DICHIARA il range + incertezza,
  non finge un punto.
- Vantaggio strutturale vs DE: auto già in IT, già immatricolata IT → ZERO trasporto (-750) +
  ZERO re-immatricolazione (-1.165).
- Rischi-canale DA DICHIARARE nel dossier: rilanci imprevedibili; "visto e piaciuto" no garanzia;
  stato reale incerto; tempi/burocrazia; cauzione; rischio non-aggiudicazione.
- Riuso motore esistente (NON nuovo): `evaluate_margin` (tools/margin_gate.py:54) + `_band_verdict`
  (pdf_generator_enterprise.py:228). chiavi_in_mano_asta = aggiudicazione_stimata + cauzione/oneri
  (no trasporto, no re-immatr.); spread = banda_AS24_geo_IT − chiavi_in_mano_asta.
- Gate pre-produzione: test che un record fonte=asta NON entri MAI in `get_it_distribution`; test
  render (pypdf) che il dossier dichiari fonte + base≠aggiudicazione + frizione-IT-azzerata + rischi
  + etichetta non dica "dealer"/"mercato".

**REFERENCE FASE 0 (parser PVP OSS, immobiliari — riuso del "come", non del "cosa")**:
- `lumontech/aste-giudiziarie` (2026-06-07, Flask+Playwright+dashboard) — mattone base più fresco
- `webextdev/pvp-scraper` (2026-05) — annunci immobiliari PVP
- `sdelliq/PVP_WebScraping` (2024) — scrape generico PVP
- BDAG: accesso = identità digitale UMANA (SPID/CIE/CNS/ADN) via SAML/IAMG, nessuna API M2M →
  presunzione forte solo-istituzionale → da scartare.

**Owner**: chi riapre dopo (a)&(b). **Gating**: NON parte prima del primo CLOSED_WON.

## S257 2026-06-09 — #S257-1 [CRITICAL PATH — non backlog opzionale, founder verdict]

### 🔴 Mediana mercato IT è TRIM-BLIND → il verdetto del gate margine non è ancora affidabile

**NON declassare a "precisione".** La mediana IT (`tools/it_market_price.py:get_it_distribution`)
e' l'**input portante** di ogni decisione del gate. Oggi esce IDENTICA per ogni anno
(€41.200, n=19) perche' lo scrape `scrape_model(year±1)` non discrimina anno ne' allestimento.
Logica perfetta su input grezzo = risposta sbagliata detta con sicurezza.

**Perche' e' il rischio peggiore per ARGOS (falso-PASS):**
- Il bug €167 (S254) aveva DUE cause: (a) fee flat €900 — UCCISA davvero (S257); (b) prezzo IT
  finto ×1.15 — cambiato il *meccanismo* (scrape reale) ma NON l'*affidabilita'* (resta trim-blind).
- ×1.15 SOTTOstimava → falso-REJECT (perdi un affare). Mediana pooled alta SOVRAstima →
  **falso-PASS** (mandi al dealer un affare che non c'e'). Per ARGOS il falso-PASS e' peggiore.
- Esempio dal DoD #2: DE €29.980 → IT €41.200 = gap 27% (oltre la forbice import 10-30%).
  Non distinguibile oggi tra (a) vero affare d'oro (auto carica sottoprezzata DE) e
  (b) artefatto (auto DE base vs pool IT inquinato da M-Sport/M340i nella stessa mediana).
  Un verdetto che non distingui da un artefatto NON e' un verdetto.

**Regola per chi ci mette mano (anti-trappola):**
- Filtra spec-aware (trim + anno + km), NON solo year±1.
- Riporta SEMPRE N. Stringere il filtro fa crollare N: mediana su n=4 e' fragile quanto
  trim-blind su n=19. NON scambiare cecita' sul trim per cecita' sul campione.
- Sotto soglia minima di comparabili → emetti **"bassa confidenza / no verdetto"**,
  MAI un numero detto con sicurezza.
- Delta optional DE↔IT in €: se non hai listino reale per trim → `[unverified]`, non inventare.

**Gating**: blocca la dichiarazione "anello 6-7 verde col gate". Il gate e' solido in
isolamento ma il suo input no.

## S257 2026-06-09 — #S257-2 [HIGH — coesistenza assi non dimostrata]

### 🟠 Gate margine verificato in ISOLAMENTO, non co-esercitato con CoVe nel runner reale

Il DoD #2 ha chiamato il vero `on_demand_runner.generate_dossier` MA con un driver che
salta lo scoring CoVe a monte. I due assi (CoVe = bonta' dell'AUTO, margine = bonta'
dell'AFFARE) dovevano coesistere: quella coesistenza nella pipeline reale
(scrape → CoVe → Step 2c → PDF) NON e' dimostrata end-to-end.

**Done-condition**: un run completo del runner (con CoVe attivo) che produce un PDF
con verdetto margine reale su un PASS. Solo allora l'anello 6-7 e' "verde col gate".

**Prova DoD #2 (versionata)**: `evidence/dod/S257_DoD2_PASS_BMW_Serie3_2021.pdf`
(+ `evidence/dod/S257_DoD2_run.log`). NB: `dossiers/` e' gitignored — la prova vive in `evidence/`.

## S229 2026-06-02 — BACKLOG #S229-1 [MED, UX, richiesta Luke]

### 🟡 Bottoni inline tappabili /approva /rifiuta sotto la reply auto-generata su Telegram

**Cosa vuole Luke**: quando arriva una risposta auto-generata (pending_reply), su TG mostrare il testo proposto + due bottoni cliccabili (`✅ Approva` / `🚫 Rifiuta`) invece di dover digitare `/approva <id>` a mano.

**Spec implementazione** (2 file):
1. **Dove parte l'alert pending_reply** (`wa-intelligence/response-analyzer.py` — la funzione che fa `sendTelegramAlert`/POST sendMessage con la reply proposta): aggiungere `reply_markup` = `inline_keyboard` con due bottoni `callback_data` = `approva:<reply_id>` e `rifiuta:<reply_id>`. (Telegram `sendMessage` accetta `reply_markup` JSON.)
2. **`telegram-handler.py` polling loop** (`run_daemon`, riga 759): cambiare `allowed_updates` da `'message'` a `'message,callback_query'`; nel loop, se `upd` ha `callback_query` → estrarre `callback_data`, splittare `azione:reply_id`, chiamare `cmd_approva(reply_id)` / `cmd_rifiuta(reply_id)`, poi `answerCallbackQuery` (obbligatorio per togliere lo spinner) + `send()` del risultato. Auth: verificare `callback_query.from.id == TELEGRAM_CHAT_ID`.

**Verifica fattuale pre-impl**: confermare formato `reply_markup` su doc Telegram Bot API (`inline_keyboard` array di array) + che `answerCallbackQuery` richieda `callback_query_id`.
**Gating**: non blocca gate #9 (Luke può già digitare `/approva <id>`). UX, non operativo.
**Owner**: ai-engineer o backend-architect.

## S196 2026-05-26 — BACKLOG #S196-1 [MED, observability]

### 🟡 audit BRIDGE_INSERTED può perdersi silent

**Scope**: `wa-intelligence/dashboard/db.py:approve_reply`. Dopo che `bridge_outbound` è già committato + connection chiusa, un `_audit('BRIDGE_INSERTED')` + `con.commit()` su dealer_network.sqlite può fallire (es. disk full, lock contention). Il `finally` chiude `con` con rollback implicito → audit perso. Il chiamante riceve comunque `{approved: True, bridge_queued: True, error: None}` (corretto operativamente: bridge in coda) ma audit trail incompleto.

**Fix proposto**: try/except locale attorno a `_audit` + commit, log.error se fallisce, ritorno positivo invariato.

**Gating**: post-Day1 Stile Car. Audit è monitoring, non operativo.
**Owner**: backend-architect.
**Reference**: S196 code-review MED-2 (accepted by reviewer as non-blocking).

## S196 2026-05-26 — BACKLOG #S196-2 [LOW, code-hygiene]

### 🟢 import sqlite3 ridondante in approve_reply

**Scope**: `wa-intelligence/dashboard/db.py:approve_reply` fa `import sqlite3 as _sqlite3` localmente, ma `sqlite3` è già importato a module-level. Refactor cosmetico: usare `sqlite3` direttamente.

**Owner**: chi tocca prossimo db.py.
**Reference**: S196 code-review note strutturale.

## S191 2026-05-26 — BACKLOG #S191-1 [LOW, perf]

### 🟢 image_sanitizer doppia lettura immagine (`_get_image_height`)

**Scope**: `src/cove/image_sanitizer.py:_get_image_height()` (riga ~362) riapre il file immagine con `Image.open()` immediatamente dopo che `vision_fn` lo ha già aperto/processato. Doppia lettura disco ~20-40ms per immagine. Su 6 immagini/dossier = ~120-240ms overhead per dossier.

**Fix proposto**: estendere signature `_detect_text_regions` con `img_h: Optional[int] = None`, passare valore già calcolato in `sanitize_image` (variabile `h` disponibile).

**Side effect bonus**: se file temporaneo viene cancellato tra apertura vision e apertura `_get_image_height` (race), oggi `img_h=0` silently disabilita check POSIZIONE_RIFLESSO. Fix elimina anche la race.

**Gating**: pre-scaling >5 dossier/giorno.
**Owner**: backend-architect.
**Reference**: S191 code-review issue MED-3.

## S191 2026-05-26 — BACKLOG #S191-2 [LOW, edge-case]

### 🟢 _is_plate_format Unicode omoglifi

**Scope**: `src/cove/image_sanitizer.py:_is_plate_format()` accetta Cyrillic 'А' come `isalpha()=True` → falso positivo plate detection. Fix banale: `compact = compact.upper()` dopo `re.sub` per garantire ASCII-only via `_PLATE_COMPACT_RE` con `re.IGNORECASE`.

**Probabilità**: irrilevante su immagini auto EU reali. Hardening cosmetico.
**Owner**: chi tocca prossimamente sanitizer.
**Reference**: S191 code-review issue LOW-1.

## S191 2026-05-26 — BACKLOG #S191-3 [LOW, path-safety]

### 🟢 pdf_generator output_dir abspath

**Scope**: `tools/scripts/pdf_generator_enterprise.py:1179` — `sanitized_dir = os.path.join(output_dir, "_sanitized", safe_listing_id)` senza `os.path.abspath(output_dir)`. Se caller passa path relativo e cwd cambia tra `os.makedirs` e write subprocess, path inconsistente.

**Fix**: `sanitized_dir = os.path.join(os.path.abspath(output_dir), "_sanitized", safe_listing_id)`.

**Probabilità**: caller produzione passa abs path. Defense-in-depth.
**Owner**: chi tocca prossimamente pdf_generator.
**Reference**: S191 code-review issue LOW-2.

## S183-bis 2026-05-21 — BACKLOG #S183b-1 [MEDIUM, scaling-gated]

### 🟡 Test golden auto_features check — refactor sanitize_image API per geometry metadata

**Scope**: `src/cove/image_sanitizer.py:sanitize_image()` ritorna optional tuple `(path, crop_metadata)` invece di solo `path: str`, dove `crop_metadata = {'top': int, 'bottom': int, 'original_size': (w, h)}`. Test `tests/test_sanitizer_golden.py` usa metadata per applicare auto_features zone su region POST-crop, eliminando il resize-back stretching che genera false positive 60-83% over-mask.

**Root cause loggata** (S183 baseline 2026-05-21): `sanitize_image` fa banner crop top 18-23% + bottom 80-87% → `sanitized.size != original.size`. Test `test_sanitizer_golden.py` linee 95-96 fa `sanitized.resize(original.size, LANCZOS)` per normalizzare diff, ma stretching shifta pixel y → bbox auto_features in coordinate original NON corrisponde più a stesso contenuto in sanitized → 10/10 FAIL falso positivo.

**Workaround attuale S183-bis Path 2**: flag `AUTO_FEATURES_CHECK_ENABLED = False` in `tests/test_sanitizer_golden.py:42`. Gate qualità over-mask delegato a UAT visual Luke (max 5 dossier/settimana realistici).

**Acceptance criteria (Definition of Done)**:
1. `sanitize_image` ritorna tuple backward-compat: caller esistenti possono fare `path = sanitize_image(...)` se non interessa metadata (default None secondo elemento via wrapper o conversion `__index__`).
2. Test `test_sanitizer_golden.py` rimuove resize-back, usa `crop_metadata` per shiftare bbox coordinate.
3. `AUTO_FEATURES_CHECK_ENABLED = True` ripristinato.
4. Run `~/.argos-sanitizer-venv/bin/python -m pytest tests/test_sanitizer_golden.py -v` → 10/10 PASS.
5. Smoke regression `tools/scripts/sanitize_all_images.py` su 1 dossier completo → zero rotture caller esistenti.
6. Rollback plan: revert tuple → string + revert `AUTO_FEATURES_CHECK_ENABLED = False`.

**ETA target**: pre-scaling oltre 5 dossier/settimana (post Day 1 Stile Car verde + 1-2 dealer aggiuntivi).
**Owner**: backend-architect agent S184+ (dopo Day 1 close).
**Gating**: scaling produzione dossier (NON Day 1 reale che usa UAT visual Luke).
**Reference**: `prompts/s183b_overmask_diagnosis_then_b_c_d.md` Path 1, autocritica CTO sezione diagnosi.

## S173b 2026-05-20 — BACKLOG #S172-1 [HIGH, GATING Day 1 dealer Aprile]

### 🔴 bridge_outbound multi-msg + media schema extension

**Scope**: estendere `bridge_outbound` per supportare:
- N>1 messaggi consecutivi (AMBRA reply multi-bubble)
- MessageMedia (Day7 voice .mp3, future immagini PDF)

**Schema delta**:
```sql
ALTER TABLE bridge_outbound ADD COLUMN media_path TEXT;
ALTER TABLE bridge_outbound ADD COLUMN media_type TEXT; -- 'audio/ogg', 'image/jpeg', etc.
ALTER TABLE bridge_outbound ADD COLUMN msg_sequence INTEGER DEFAULT 0; -- 0..N per ordering
```

**Acceptance criteria (Definition of Done)**:
1. Schema migrato + backward compat (NULL = single msg, no media)
2. `pollBridgeOutbound` gestisce msg_sequence ORDER BY per consecutive sends
3. Day7 voice migra a bridge (no più callsite diretto)
4. `auto_approve_and_send` multi-msg migra a bridge (no più Popen)
5. Test E2E: AMBRA reply 3 bubble → 3 WA messages distinte recapitati TEST_FOUNDER 393314928901
6. Rollback plan documentato (DROP COLUMN media_path/media_type/msg_sequence + revert wa_bridge.py)

**ETA target**: 2026-04-25 (5 working days da S173b close)
**Owner**: implementer agent S174
**Gating**: Day 1 dealer reale Aprile bloccato fino merge
**Prompt resume**: `prompts/s174_bridge_multimsg_extension.md`

## S178 2026-05-16 — Findings collaterali

### 🟡 BUG-5 — Sign page mostra "token non valido" post-submit successful
Luke firma OK (contract `52bc66c9feb4771d` → AWAITING_DELIVERY confermato), MA UI sign page mostra "token del contratto non valido". Cosmetic error (firma processata server-side), probabilmente sign.js dopo POST submit ricarica DTO o cleanup token state. Audit `landing/contract/sign.js` flow post-submit (state-signed render vs token revalidate). Non bloccante ma confonde dealer reale.

### 🟢 mark-paid `wa_sent:false email_sent:false`
Endpoint admin mark-paid ritorna OK con `wa_sent:false, email_sent:false`. Da capire se atteso (admin endpoint = no notify automatic) o gap pipeline (dealer non riceve conferma pagamento). Verifica `argos-worker.js` mark-paid handler — se notify mancante, dealer reale non ha receipt conferma → trust issue.

### ✅ BUG-4 — Cloudflare Pages NON ha auto-deploy GitHub (RISOLTO via wrangler CLI)
Root cause confermata: project `argos-automotive` ha Git Provider `No` (zero integration GitHub). Inoltre `production_branch=main` (NON `master`) → deploy CLI con `--branch=master` finiva in **Preview**, mai promosso. Fix workflow: `cd landing && CLOUDFLARE_ACCOUNT_ID=22ddff3a4ef544511523a841b3dcadf8 npx wrangler pages deploy . --project-name=argos-automotive --branch=main --commit-dirty=true`. Token in `.env` repo. Da automatizzare via `.github/workflows/cd-pages.yml` (cloudflare/pages-action) — defer S180+.

### 🟡 _redirects splat rewrite 200 NON funziona su CF Pages
Regola `/contract/* /contract/index.html 200` testata: produce HTTP 200 ma serve landing root, non file destination. Anche `/contract/:token /contract/?token=:token 302` ha `:token` letterale (non sostituito) + cattura `sign.js`. Soluzione adottata S178: Pages Function `landing/functions/contract/[token].js` con `next()` pass-through per asset estensione. Documentare in runbook deploy: preferire Functions per dynamic routing vs _redirects splat.

## S177c 2026-05-16 — Findings collaterali (HIGH)

### 🟡 SSH .env sourcing pattern
`ssh imac "source .env && cmd"` NON esporta KEY=val come env var (default bash limita a var locale). Pattern corretto: `set -a; source .env; set +a; cmd`. Documentato in S177c memory. Aggiornare reference `wiki/projects/ARGOS/runbooks/ssh-imac.md` se esiste, o aggiungere snippet in CLAUDE.md.

### 🟡 .env iMac linea 12 quote
`GMAIL_FERRETTI_APP_PASSWORD=jzge syej rqex zkrw` senza quote → spazi rompono source → tutte le var sotto linea 12 (incluso `ARGOS_ADMIN_SECRET`) non esportate. Fixed S177c con sed quote. Audit altri .env del progetto per pattern simile.

## S176-finalize 2026-05-16 — Findings collaterali (priorità ordinata)

### 🔴 PRIORITÀ 1 — S177 contract intent (BLOCKER primo deal E2E)
Classifier AMBRA non gestisce intent CONTRACT_REQUEST. Pipeline reactive si ferma a info-broker loop dopo dossier accept. Resume: `prompts/s177_contract_intent_implementation.md`. **PRIMA di S178 sanitizer**.

### 🟠 PRIORITÀ 2 — S178 sanitizer refactor D-32 (BLOCKER Day 1 reale)
LaMa→Pillow rectangle solid (D-25 violazione). Targa scomparsa + paraurti deformato in regression test S176. Senza fix = primo dealer reale vede foto distorte = trust kill. **Dopo S177 verde**.

### 🟡 PRIORITÀ 3 — UX direzione TEST_FOUNDER reactive
In tutti prompt futuri esplicitare: TEST_FOUNDER reactive = SIM `3314928901` → SIM `3281536308`. Direzione invertita = daemon filtra come auto-eco. S176-finalize ha perso 15min su questo.

### ✅ PRIORITÀ 4 — `current_step` non si aggiorna dopo PDF send (RISOLTO S177a 2026-05-16)
Daemon `wa-daemon.js` `/send-doc` patch in-place iMac: post-send UPDATE `conversations.current_step='DOSSIER_SENT'` se era `DAY1_SENT`/`DAY3_SENT`. Backup `wa-daemon.js.s177a_bak`. Restart pulito 18:11. Smoke test fisico differito S177b primo `/send-doc` reale.

### 🔴 PRIORITÀ 4-bis NUOVA — HITL LLM_MULTI bypass strutturale (D-07 violation)
`pending_replies.reply_e9be3ac6` ha `approved=0` MA `sent=1` con 2 OUTBOUND messaggi delivered TEST_FOUNDER 17:57:44/48 (reply hallucinata mai approvata). Schema NON ha `approved_ts` né `sent_at` (solo `approved`, `sent`). `wa-daemon.js pollBridgeOutbound` legge da `bridge_outbound` (table diversa) con `approved_ts IS NOT NULL` — quindi reply LLM_MULTI NON viene da quella pipeline. Sospetti path auto-send: (a) `telegram-handler.py:171` esegue UPDATE sent=1 post Telegram approve, (b) embedded subprocess in response-analyzer.py:1684 `c.execute('UPDATE pending_replies SET sent=1 WHERE id=?', [task['reply_id']])`. Per dealer reale = un dealer riceve hallucination senza HITL gate. **FIX URGENTE pre-Day 1 reale Stile Car**. Audit completo path subprocess in S177b o S177-bis-hitl.

### 🟠 PRIORITÀ 4-ter NUOVA — Worker `/api/v1/contract/create` 401 INVALID_TOKEN
Endpoint Cloudflare `https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create` rifiuta `X-API-Key: $ARGOS_API_KEY` (token presente in `.env` iMac). Test S164 aveva creato contract via questo path → o token ruotato o auth method cambiato. Verifica `wrangler.toml` Worker env binding + path autenticazione (Bearer?). Necessario per S177b classifier handler che chiama questo endpoint.

### ⚪ PRIORITÀ 5 — D-31 dossier 12 sezioni
PDF S176 = 3 pagine vs D-18 12 sezioni. Gap analysis deferred S179+.

### ⚪ PRIORITÀ 6 — iMac branch divergence
`main` HEAD `fd35965e` history-rewrite vs `origin/master`. Risolvere prima di prossimo deploy esteso.



## S174 — Classifier substring bug (false-positive `passat` in `passato`)

`wa-intelligence/response-analyzer.py` line 1136 — keyword list VEHICLE_REQUEST contiene `passat` come exact match ma classifier usa substring scan (line 1306 area `keyword_mixed_intent`). Messaggio "il cliente che è passato da me" → matcha `passat` → routato VEHICLE_REQUEST → template VEHICLE_PROPOSAL servito → LLM bypassed.

Impatto: dealer Layer 3 post-handoff che racconta storia cliente (vocabolario naturale "passato/è venuto/è stato qui") finiscono in template invece di LLM identity_post_handoff. Risposta scriptata BMW/Mercedes/Audi.

Fix candidato: word boundary regex `\bpassat\b` invece di substring, OR sostituire `passat` con `vw passat`/`volkswagen passat` per disambiguare. Stessa famiglia tutti gli "exact" keyword di VEHICLE_REQUEST con frammenti corti (`golf`, `t-roc`).

Defer: non blocca S175 mystery shopper (test parlerà di auto specifiche, non storie cliente). Da affrontare post primo deal.

## ✅ FIXED S171 — wa-daemon duplicate sends + retry loop su permanent error

**Risolto 2026-05-15**: `wa-intelligence/wa-daemon.js` `pollBridgeOutbound()` patch atomica.

**Root cause (cumulativa)**:
- (Bug A) Error path linea 305 aggiornava `sent_status` ma NON `sent_ts` → row con errore permanente (es. Auto Carfora "No LID for user") re-pollato ogni 30s → 41+ retry confermati nei log iMac 21:05-21:25.
- (Bug B) Poll-then-send-then-update senza lock atomico: `setInterval` può lanciare poll #2 mentre await `sendMessage` di poll #1 ancora in flight → race window duplicate.

**Fix applicato**:
1. Schema migration additive (`processing_ts INTEGER`, `attempt_count INTEGER DEFAULT 0`) idempotente a startup
2. Atomic claim pre-send: UPDATE `processing_ts=now, attempt_count++` WHERE `sent_ts IS NULL AND (processing_ts IS NULL OR processing_ts < now-RECLAIM)` → se `changes===0` skip (concurrent poll)
3. Poll query filtra stale processing + cap attempt_count<3
4. Error path classifica permanent (regex `/No LID|invalid|forbidden|not.found/i`) vs transient → permanent o cap-3 → set `sent_ts=now` terminal (escape loop)
5. Stale reclaim window = max(120s, poll_interval*4)

**Cleanup eseguito**:
- Backup DB e source su iMac (`*.bak_s171`)
- id=5 Auto Carfora marcato `sent_ts=now, sent_status='error_permanent_S171: No LID for user (frozen)'` per fermare retry loop attivo
- better-sqlite3 rebuilt per node 22 (era contro node 20, pm2 --update-env aveva switchato versione)

**Verifica fix**:
- Daemon ONLINE post-restart, schema migration confermata via `.schema bridge_outbound`
- Smoke 3/3 single-send su TEST_FOUNDER → **pending Luke fisico** (vincolo `feedback_test_founder_means_real_interactive.md`)

## fatturazione TD17/18/19: nessun tool emissione (S164 gap critico)

**Trovato S164 2026-05-12**: grep `TD17|TD18|TD19|reverse_charge|fattura|invoice` in tutto codebase → solo menzioni marketing copy (`tools/fee_calculator.py`, `tools/import_checklist.py`, dataset training) e KB session test (`mario_kb_test_session40.py`). **Nessun tool che emette XML SDI / PDF fattura su transazione reale**. `argos-proxy/src/routes/` ha `mark-paid.ts` ma è notifica WA conferma pagamento, NON emissione fattura.

**Implicazione vincolo Luke (`feedback_e2e_full_test_founder_before_day1.md` step 4 "Pagamento: fattura emessa TD17/18/19 corretto")**: step 4 E2E pipeline non chiudibile finché non esiste tool fattura O processo manuale documentato (commercialista che riceve trigger post `mark-paid` e emette fattura entro 15gg per reverse charge intracomunitario).

**Decisione richiesta a Luke**: (a) tool fattura va costruito dentro ARGOS (Fatture in Cloud API / fattura PA XML SDI generator) E2E digitale, oppure (b) processo manuale via commercialista (`mark-paid` worker invia notifica TG + email a commercialista con dati transazione → fattura emessa offline) → gap step 4 risolto a livello processo, non a livello tool.

**File coinvolti se opzione (a)**: nuovo `argos-proxy/src/routes/invoice-emit.ts` o `tools/invoice_generator.py`. Se (b): solo nuovo handler in `mark-paid.ts` o telegram alert dedicato.

## scraper(autoscout24): filtrare slide marketing PRIMA del DB insert (S163.1 follow-up)

Filtra slide marketing AS24 (Premium Selection, Garantie, Wartungsfreiheit, Inzahlungnahme, Finanzierung) PRIMA del DB insert in `vehicle_images`. Fix economico upstream; sanitizer S163.1 è safety net non solution.

**Pattern detect**:
- `image_url` contiene marketing-asset path (es. `/promo/`, `/banner/`, hash AS24 noti per slide stock)
- OR primo OCR Vision restituisce >5 region testo tedesco senza targa/badge BMW
- OR aspect ratio + dominant color → slide bianca con solo overlay testuale

**Razionale**: oggi S163.1 guard salta JPEG <20% size originale post-sanitize, ma è reattivo (richiede full pipeline run + inpaint + ricompress per scartare). Filtro upstream a scraping time = zero cost downstream + DB pulito (no rows da skippare).

**File coinvolti**: `tools/scrapers/autoscout_scraper.py`, `vehicle_images` table.

## Gap strutturali (da S130)
- `days_on_market` non recuperabile dai search results — richiede click su detail page
- `vehicle_listings.matched_dealer` = NULL — le due tabelle non sono collegate
- PDF E2E con dati CoVe reali mai completato (immagini sanitizzate OK, dati reali no)

## Architettura avanzata (Phase 3 — dopo 30 messaggi reali)
- L5 LLM-as-judge validator
- `mv_market_insights` view materializzata su CoVe
- Geographic routing Nord/Centro/Sud
- `insight_delta` schema
- SEQ-NOEXIT-BEFORE-DAY21 rule
- Batch generation + digest Telegram 08:00
- `persona_evolution_log`
- GATE-ICP-001 con soglie calibrate empiricamente
- Confidence-gated blending archetipi (0.65-0.85 → top-2 blend)

## CF Workers → LAN daemon unreachable (rilevato S154-ter, PIVOT S155 → Tailscale Funnel, ✅ FIXED S155-tris)
**Status**: ✅ FIXED in S155-tris via `tailscaled` open-source standalone + Tailscale Funnel su iMac. Worker secret `WA_DAEMON_URL` aggiornato a `https://imac-di-gianluca.tail62c468.ts.net`. Smoke E2E TEST_FOUNDER 8/8 verde con `wa_sent:true` confermato (2 WhatsApp delivered, log + visual Luke).

- **Sintomo**: `send-iban` + `mark-paid` ritornano `wa_sent: false`. Worker tail mostra:
  ```
  (error) WA daemon HTTP 403: error code: 1003
  (warn) send-iban WA failed: HTTP 403
  ```
- **Root cause**: `WA_DAEMON_URL=http://192.168.1.2:9191` è IP RFC1918 privato. Cloudflare Workers fetch da edge non può raggiungere LAN. CF gateway risponde con error code 1003 ("Direct IP Access Not Allowed").
- **Già documentato** in `argos-proxy/src/lib/wa-daemon.ts:8-11` come known limitation pre-prod.
- **Decisione S155 PIVOT (€0 + zero domain)**: scartata Opzione A (CF Tunnel) perché Luke non possiede dominio e CF account ha 0 zone DNS (verificato `GET /zones` → `result:[]`). Scartato anche acquisto domain CF Registrar (~€9/anno → viola ZERO COSTI). **Pivot a Tailscale Funnel**: URL stabile `<machine>.<tailnet>.ts.net`, TLS auto, free tier 3 nodes, no domain ownership.
- **Status S155 PARTIAL (2026-05-04 13:30)**:
  - ✅ Tailscale 1.96.5 già installato iMac
  - ✅ Login completato (account `ferretti.argosautomotive@gmail.com`, tailnet `tail62c468.ts.net`)
  - ✅ ACL nodeAttrs `funnel` aggiunto via API (commit token in `.env`)
  - ✅ HTTPS Certs abilitati via API `PATCH /tailnet/-/settings httpsEnabled:true`
  - ✅ Cert Let's Encrypt provisioned (`tailscale cert imac-di-gianluca.tail62c468.ts.net`)
  - 🐛 `tailscale funnel --bg 9191` set OK ma `funnel status` legge `{}` empty in session SSH successive — bug stato sandbox/socket macOS App (vedi sezione sotto)
  - 🟡 Smoke E2E + Worker secret update **deferred S155-bis** (post-reboot Tailscale.app o forced GUI restart)
- **Resume path S155-bis**: `prompts/s155b_funnel_smoke.md`. Token API Tailscale 90 giorni in `.env` come `TAILSCALE_API_TOKEN`.

## Tailscale Funnel `--bg` set ma `status` empty su macOS App (rilevato S155 PARTIAL, CONFERMATO IRRECUPERABILE S155-bis, ✅ WORKAROUND DEPLOYED S155-tris)
**Status**: ✅ WORKAROUND DEPLOYED in S155-tris via switch a `tailscaled` open-source standalone (Homebrew build + launchd). Bug GUI App **non risolto upstream** (struttura macOS Tailscale.app 1.96.x network extension), ma **completamente bypassato** in produzione. Funnel persiste, DNS pubblico risolve, curl HTTP 200 confermato.

**Setup canonical S155-tris**:
- `brew install tailscale` → `/usr/local/bin/{tailscale,tailscaled}` (compile from source con go 1.26.2 dependency, ~10min totali)
- launchd plist `/Library/LaunchDaemons/com.tailscale.tailscaled.plist` (KeepAlive + RunAtLoad, sopravvive reboot)
- Socket dedicato `/var/run/tailscale/tailscaled.sock` (separato da GUI App, no interferenze)
- State `/var/lib/tailscale/tailscaled.state`
- CLI invocation: `sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock <cmd>`
- Runbook completo: `docs/ops/tailscaled-runbook.md`


- **Sintomo**: `tailscale funnel --bg 9191` ritorna "Funnel started and running in the background" + URL. Ma `tailscale funnel status` → `No serve config`. JSON: `{}`. DNS pubblico NXDOMAIN. Cert provisioned ma DNS record AAAA non pubblicato presso control plane.
- **Root cause confermato S155-bis**: bug strutturale Tailscale.app GUI macOS network extension 1.96.x. Network extension daemon non persiste serve/funnel config dal CLI socket bridge. Tailscale 1.96.5 = ultima versione disponibile su macOS Monterey 12.7.4 ([1.98+ richiede Ventura 13+](https://tailscale.com/docs/install/mac)). Update GUI App NON è opzione.
- **Mitigation tentativi falliti S155-bis** (5 retry consecutive identici):
  - ✅ Quit + Relaunch Tailscale.app GUI (eseguito Luke)
  - ✅ Verifica "Allow Incoming Connections" abilitato (no fix da [tailscale#11049](https://github.com/tailscale/tailscale/issues/11049))
  - ✅ Re-auth via API auth-key fresh
  - ✅ Cleanup naming via API DELETE/POST `/name` (rimosso suffix `-1`)
  - ✅ Re-emit cert idempotent
  - ✅ Reset + retry funnel + serve separato
  - ✅ Verifica ACL `nodeAttrs autogroup:member → funnel` propagato
  - ✅ Verifica `httpsEnabled: true` settings
  - Tutti success message ma status sempre `{}` empty + DNS NXDOMAIN + curl HTTP 000
- **Mitigation S155-tris (decisione CTO Opzione A)**: switch a `tailscaled` open-source standalone via launchd plist `/Library/LaunchDaemons/com.tailscale.tailscaled.plist`. Bypass GUI App network extension. Riusa cert+ACL+API token già configurati. Reversibile. Plan completo: `prompts/s155c_tailscaled_standalone.md` (10 phase, ~60-90min autonomo).
- **Plan B se anche standalone fallisce**: switch architettura cloudflared tunnel.
- Priorità: **alta** — blocca smoke E2E end-to-end + Day 1 reale.

## PM2 daemon non resurrect post-reboot iMac (rilevato S155-bis, ✅ FIXED S156)
**Status**: ✅ FIXED in S156 via `pm2 startup launchd` + workaround manuale spostamento plist da `~/Library/LaunchAgents/` a `/Library/LaunchDaemons/`. Reboot test verde alle 18:48: PM2 + argos-wa-daemon + argos-cf-monitor + funnel external auto-restart in <1min senza intervento utente.

- **Sintomo (storico)**: SessionStart hook segnala `WA Daemon: UNREACHABLE`. PM2 daemon era morto, dump.pm2 esistente. `pm2 resurrect` con PATH fix ripristina entrambi processi.
- **Root cause**: PM2 startup script non installato. Reboot iMac ferma daemon e non si ricarica.
- **Fix S156**:
  1. `sudo env PATH=$PATH:/usr/local/bin /Users/gianlucadistasi/.npm-global/lib/node_modules/pm2/bin/pm2 startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi` → genera plist (Label `com.PM2`)
  2. **Workaround pm2 bug**: pm2 mette plist in `~/Library/LaunchAgents/` (user-level) invece di `/Library/LaunchDaemons/` (system-level). Su iMac headless senza auto-login GUI, LaunchAgent NON parte al boot. Soluzione: `sudo mv` a `/Library/LaunchDaemons/` + `sudo chown root:wheel + chmod 644` + `sudo launchctl bootstrap system /Library/LaunchDaemons/pm2.gianlucadistasi.plist`
  3. Cleanup vecchio `~/Library/LaunchAgents/com.argos.pm2.plist` (path `/usr/local/bin/pm2` inesistente, exit 78 storico) → rinominato `.S156-DISABLED`
  4. `pm2 save` → snapshot `~/.pm2/dump.pm2` per resurrect
- **Reboot test S156 (18:46:55 → 18:48:39)**: ping back 16s, SSH back 60s, cascade auto-restart verde in 110s totali — nessun intervento manuale richiesto. argos-wa-daemon + argos-cf-monitor uptime 53s post-reboot, WA daemon connected, funnel external HTTP 200.
- Runbook: `docs/ops/tailscaled-runbook.md` sezione "PM2 startup persistenza".

## Phone format mismatch contract-create ↔ wa-daemon.ts (rilevato S154-bis, FIXED S154-ter)
**Status**: ✅ FIXED in commit `ab938c4` `fix(s154c): normalize phone in wa-daemon.ts`. Sezione mantenuta come reference storica.


- `argos-proxy/src/routes/contract-create.ts:46` regex `^(\+39)?3\d{8,10}$` accetta:
  - `+393314928901` ✅ (`+39` + `3` + 9 digits)
  - `3314928901` ✅ (10 digit national)
  - `393314928901` ❌ (11 digits dopo prima `3` → fuori range {8,10})
- `argos-proxy/src/lib/wa-daemon.ts:27` regex `^\d{11,13}$` accetta:
  - `393314928901` ✅ (12 digits puri)
  - `+393314928901` ❌ (presenza `+` invalida)
  - `3314928901` ❌ (10 digits)
- **Intersezione vuota per TEST_FOUNDER 393314928901 (formato WA standard country+national)**
- Side effect: in send-iban / mark-paid Worker valida prima di chiamare daemon → `wa_sent: false`. Status DB transition OK (best-effort), ma dealer non riceve IBAN_SEND/PAYMENT_RECEIVED su WA.
- **Fix proposto** (3 LOC, send-iban + mark-paid + wa-daemon.ts):
  - In `wa-daemon.ts`: normalizzare con `phone.replace(/\D/g, '')` PRIMA del regex check, passare valore pulito a fetch.
  - Daemon iMac già fa stripping interno (`phone.replace(/[^0-9]/g, '')`), quindi consistente.
- Alternativa (più invasiva): contract-create normalizza phone in formato canonical (393...) prima di INSERT.
- Priorità: **alta** — blocca smoke E2E S154-bis (WA delivery KO), blocca Day 1 reale fino a fix.

## Rate-limit middleware soft-limit per CF isolate spread (rilevato S154-bis)
- `argos-proxy/src/middleware/rate-limit.ts` usa `Map` module-level → buckets per-isolate, non globali.
- Smoke test S154-bis evidenza:
  - 35 GET sequenziali (non sleep) tra le richieste → 35x 200, **0x 429** (CF distribuisce su isolate diversi, ognuno bucket fresh).
  - 100 GET parallel via `xargs -P 50` → **42x 429**, 58x 200 (sotto burst, isolate riusati).
- **Diagnosi**: il middleware funziona come "circuit breaker per single isolate" ma NON come "rate-limit globale per IP". Per ARGOS scale (~100 req/giorno) accettabile come anti-flood layer, NON come hard cap.
- **Fix opzionale** (per quando supera 1k req/min): migrare a Durable Objects o KV con atomic INCR (commento già presente in middleware:8).
- Priorità: **bassa** — soft limit sufficiente, but documentare in PR description e ops runbook.

## Drift architetturale deploy iMac (rilevato S153)
- **Directory `~/Documents/app-antigravity-auto/wa-intelligence/` (legacy) NON è symlink** ma directory standalone con codice obsoleto (mtime drift di ore/giorni vs `current/wa-intelligence/`)
- `deploy/sync.sh` aggiorna SOLO `current/` (symlink to fresh release), NON aggiorna legacy
- PM2 apps (wa-daemon, tg-bot, cf-monitor) sono registrati col path legacy → girano su codice OBSOLETO ad ogni deploy
- Workaround attuale (S153): post-deploy `cp current/wa-intelligence/*.{js,py} wa-intelligence/` per file modificati
- **Fix proposto**: o (a) trasformare legacy in symlink a current/wa-intelligence (richiede pm2 stop/start tutti), o (b) deploy/sync.sh aggiunge step "rsync current → legacy" (più sicuro, no PM2 disruption)
- Priorità: media — bug latente, non critico ma causa silent staleness deployment

## Drift secrets local↔iMac (rilevato S153)
- Root `.env` aveva `TELEGRAM_BOT_TOKEN` revocato (401) mentre iMac `wa-intelligence/.env` aveva token valido
- Nessun fail visibile finché qualcuno usa root .env per script ad-hoc
- **Fix proposto**: definire single source of truth (iMac canonical), root `.env` rigenerato post-deploy via `scp iMac:.../wa-intelligence/.env .env.from-imac` per script local

## Security cleanup .env (post-S153)
- **Rimuovere password Gmail/LinkedIn plain text** dopo switch a App Password IMAP per CF Alert Monitor
  - `GMAIL_PWD=...` e `ARGOS_GMAIL_PWD=...` sostituibili da `GMAIL_FERRETTI_APP_PASSWORD` per IMAP
  - Audit script che leggono `GMAIL_PWD` (grep ricorsivo `wa-intelligence/`, `tools/`) prima di rimuovere
  - Mantenere solo se ancora usata da SMTP/login web automation (in tal caso: switchare anche quelli a App Password)
- **`LINKEDIN_PWD` = stessa password `GMAIL_PWD`**: single-point-of-failure. Cambiare LinkedIn con password dedicata + salvare separatamente. Trapela `.env` → perdi entrambi.
- **Rotazione password Gmail post-S153**: la password attuale è già stata in plain text in `.env` da Sx (commit history può averla esposta se per errore committata). Verificare `git log -p -- .env` non sia mai stata pushata. Se sì → rotation immediata + revoca app password.
- **`VOIP_PASSWORD`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_AI_API_KEY`, `CLOUDFLARE_API_TOKEN`**: già in plain text — accettabile per ora (sono token revocabili, non password account), ma considerare migrazione a Cloudflare Workers Secrets / macOS Keychain CLI per ridurre file plain text.
- **Backup codes Google**: salvati in [TODO Luke conferma: Apple Note bloccata / cassaforte fisica / password manager]. NON in `.env`, NON in MEMORY.md, NON in repo.

## Miglioramenti scraper
- Scraping periodico AutoScout24.it → `dealer_inventory_snapshots` in DuckDB
- Signal: aged inventory (>90 giorni senza variazioni) come trigger primario
- `days_on_market` via detail page click (richiede Playwright o delay aggiuntivo)
- `mobile_de`: MobileDeScraper non implementa `parse_search_results` (abstract method) — on_demand_runner skips silenziosamente
- `seller_name` ancora NULL per listing DE/NL già esistenti — solo nuovi insert la salvano (fix S131)
- `vehicle_listings.seller_city` non estratta (disponibile in `item.location` su AS24.it)

## Scraper "ROTTI" BMW Serie 3/5 + Mercedes GLC/C/E/GLE (CLAUDE.md, ✅ VERIFICATO FALSE-POSITIVE S157)
**Status**: ✅ NON ROTTI — claim CLAUDE.md obsoleto. Verificato S157 (2026-05-05): tutti 6 modelli producono 19-20 listing/run su autoscout24.de con `price_eur`, `km`, `seller_name` tutti popolati. Slug `-(alle)` ritorna HTTP 200. Pipeline E2E BMW Serie 3 → CoVe → PDF in 41s, 2 PROCEED su 16. CLAUDE.md aggiornato a "E2E FUNZIONANTE".

## PDF dossier size 5KB sospetto (rilevato S157, ✅ FIXED S158)
**Status**: ✅ FIXED S158 (2026-05-05). Root cause: `_download_image_to_temp` in `pdf_generator_enterprise.py` non upgradava URL thumbnail AutoScout24 (`/250x188.webp`) a full-res (`/2560x1920.webp`); il filtro `> 30000` byte poi escludeva tutte le immagini 9-22KB. Fix: aggiunto `_upgrade_thumbnail_url()` (replica `image_downloader.PORTAL_IMAGE_UPGRADES`) prima del download. Verifica: BMW Serie 3 PDF 5,289 → **4,161,219 bytes** (4.1MB), Mercedes GLC PDF **4,761,092 bytes** (4.7MB), 6 image XObjects + 6 DCTDecode JPG embedded confermati via raw PDF inspection. Diagnosi completa in `.planning/S158-PDF-DIAGNOSIS.md`.

## Image Sanitizer (PaddleOCR) NON OPERATIVO — leak foto dealer originario (rilevato S158, defer)
**Status**: 🟢 STACK-FIXED S160 (2026-05-11) — combo `opencv-python==4.7.0.72 + numpy<2 + paddleocr 3.5` operativa in `~/.argos-sanitizer-venv/`. `_find_sanitizer_python()` timeout 30s. **Smoke E2E + visual inspection deferred S161** (`prompts/s161_sanitizer_smoke.md`). Day 1 reale Stile Car bloccato fino S161 verde. Dettagli: `.planning/s160_path_c_working_combo.md`.

**Sintomo**: Il PDF generato S158 contiene foto full-res direttamente dal CDN AutoScout24 con watermark/branding del dealer tedesco originario visibili (targhe, numeri telefono, loghi concessionario). Violazione zero-source policy ARGOS — un dealer Sud Italia capisce subito da quale portale arriva l'opportunità.

**Root cause** (nel codice già prima S158):
- `_find_sanitizer_python()` cerca Python con PaddleOCR su `/usr/local/bin/python3.12`, `/usr/bin/python3`, `/usr/local/bin/python3.11` — nessuno lo ha installato sul MacBook
- Quando non trovato, `_sanitize_photo()` (line 1531-1538) ritorna `image_path` (l'immagine RAW originale) senza modifiche
- Il log stampa `[SANITIZER] 6/6 photos sanitized` ma il count include anche le immagini RAW non realmente sanitized → **messaggio fuorviante**

**Pre-esistente**: il bug era già presente in S157 e prima — non visibile perché le immagini non venivano embeddate (Bug S158 sopra). Ora che le full-res vengono embedded correttamente, il problema sanitizer è esposto.

**Cosa fare (defer S158-bis o S159+)**:
1. Setup PaddleOCR: `python3.12 -m pip install paddleocr` o creare venv `~/.argos-sanitizer-venv/`
2. Verificare path candidates in `_find_sanitizer_python()` includano il venv dedicato
3. Smoke re-run: log deve mostrare `[SANITIZER] Using /path (has PaddleOCR)` invece di "No Python with PaddleOCR found"
4. Visual inspection PDF post-fix: targhe blur + watermark dealer originale rimossi
5. **Bonus fix log**: `_sanitize_photo()` deve distinguere "RAW (passthrough)" da "sanitized"; messaggio finale deve riportare numeri reali (es. `0/6 sanitized (PaddleOCR missing) — photos RAW`)

**Implicazione operativa Day 1**: NON inviare PDF S158 a dealer reali finché sanitizer non operativo. PDF dealer-grade in size, ma leak operativo non risolto.
