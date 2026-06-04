# S237 — Ripartenza

## ✅ S237 — ESITO (2026-06-04): "🔄 Rigenera" IMPLEMENTATO + DEPLOYATO (code-verified, daemon-safe) → resta SOLO il GATE FISICO human-gated

### FATTO (delega ai-engineer impl + devops-automator deploy)
- **`cmd_genera(reply_id)` implementato** in `wa-intelligence/telegram-handler.py:407-549` (Python 3.9 compat — niente PEP 604, `py_compile` OK locale+remoto). Spec 7-punti rispettato:
  1. Legge `pending_replies` (rifiuta se `sent==1`). 2. Re-recupera inbound da `messages` (`direction='INBOUND' ORDER BY timestamp_it DESC LIMIT 1`, cols verificate vs response-analyzer.py:1152) + archetipo da `conversations.persona_type`. 3. Ricostruisce system prompt via `build_system_prompt(archetype=...)` (riuso importlib `spec_from_file_location` su response-analyzer.py; fallback inline 3 righe se import fallisce) + inietta `<regen_instruction>` "precedente RIFIUTATA → versione diversa/più forte, NON ripetere". 4. Chiama `gemini-2.5-flash` via `urllib` (zero nuove dep), `maxOutputTokens=512 temp=0.85`. 5. **Floor guard**: 429→"quota esaurita", 404→"modello non trovato", altro HTTP/timeout/vuoto → messaggio operatore + **riga DB INVARIATA** (no fallback spacciato per premium). 6. Successo: `UPDATE reply_text=?, approved=NULL, sent=0` + re-notifica con keyboard COMPLETA. 7. JSONL append-only `wa-intelligence/regenerate_log.jsonl` (`{ts,reply_id,archetype,reason:'operator_rejected_no_reason',model_used,original}`).
- **3° bottone** `🔄 Rigenera`→`genera:<id>` aggiunto in `make_inline_keyboard` (riga 155/165, guard 64-byte) + branch `elif action=='genera'` nel callback handler (riga ~989).
- **HITL guard #9 NON toccato** (cmd_approva/cmd_rifiuta intatti). VERIFIED #9 invariato.
- **DEPLOY (devops-automator, daemon-safe):** telegram-handler.py → release `releases/20260527_083951/wa-intelligence/` + ROOT (md5 `81c48ab8b3d9461a35dc44988fa942ce` identico su entrambi+locale), backup `.bak-pre-s237` su entrambi i path. Remote py_compile OK (3.9). **Restart SOLO `argos-tg-bot`** (online, no crash-loop, no traceback). **`argos-wa-daemon` restart_time 50→50 INVARIATO + connected** (window-integrity OK, non-VOID).

### NEXT (S238) — UNICO lavoro residuo = GATE FISICO human-gated (R1: MAI auto-VERIFIED). PACKET pronto:
```
PRE (CC, read-only devops): pm2 jlist → restart_time argos-wa-daemon (atteso 50) · tail /tmp/argos-tg-bot-out.log
SEED (Luke ~1min): WA dalla SIM TEST_FOUNDER 393314928901 → ARGOS Business 3281536308 → annota reply_id dalla notifica TG (deve mostrare 3 bottoni: ✅ 🚫 🔄)
ESEGUI: tap 🔄 Rigenera
  PASS = arriva nel bot una NUOVA reply (testo diverso dal precedente) con keyboard COMPLETA (✅/🚫/🔄)
         + riga in wa-intelligence/regenerate_log.jsonl (model_used=gemini-2.5-flash)
         + DB pending_replies: reply_text cambiato, approved=NULL, sent=0
  FAIL-soft atteso se quota Gemini esaurita = msg "⚠️ Rigenera premium non disponibile (quota Gemini esaurita)" + riga DB INVARIATA (questo è CORRETTO, non un bug — è il floor guard)
POI (chiude il ciclo): tap ✅ Accetta sulla reply rigenerata → arriva sulla SIM
NB iMac clock +2h · log tg-bot /tmp/argos-tg-bot-out.log · rollback = cp telegram-handler.py.bak-pre-s237 su ENTRAMBI i path + pm2 restart argos-tg-bot
```
- **Pre-req runtime da verificare nel gate**: `GOOGLE_AI_API_KEY` deve essere nell'env di `argos-tg-bot` su iMac (se manca → cmd_genera ritorna "GOOGLE_AI_API_KEY mancante" senza chiamare). Se il gate mostra quel messaggio → aggiungere la chiave all'env PM2 del tg-bot e restart.

### S237b FIX (2026-06-04, gate-discovered): notifica PUSH mostrava solo 2 bottoni — il 3° 🔄 va aggiunto in response-analyzer.py (che costruisce la SUA keyboard, NON usa make_inline_keyboard). FATTO: response-analyzer.py:1889-1902 (send_telegram_notification) + 1969-1981 (send_telegram_hold) ora emettono [[Accetta,Rifiuta],[Rigenera]] con guard 64b. Deploy ROOT+release (md5 10620c26), NO restart (daemon respawna per-inbound). reply_d752cfb5 seedato PRE-fix NON ha il bottone — serve SEED NUOVO dalla SIM per la notifica a 3 bottoni.

### Vincoli S238: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · `restart_time argos-wa-daemon`=50 · iMac clock +2h.

---

# S236 — Ripartenza

## ✅ S236 — ESITO (2026-06-03): GROUND-TRUTH MODEL-ID CHIUSO (`gemini-2.5-flash`) · IMPLEMENTAZIONE INTERROTTA (agent crash) → spec completo per S237

### Cosa è VERIFICATO A RUNTIME (fatti chiusi da chiamate live, NON da memoria/Deep Research)
- **Premium del rigenera = `gemini-2.5-flash`** su Google API diretta (`generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GOOGLE_AI_API_KEY`). Test `generateContent` REALE → risposta OK, `modelVersion: gemini-2.5-flash`. Quota SEPARATA dalle 50/giorno OpenRouter. Upgrade genuino sul liv.1 cascade `gemini-2.0-flash` (`src/llm_cascade.py:158`).
- **`gemini-2.5-pro` ESCLUSO** — test REALE → `429 RESOURCE_EXHAUSTED` su free key. Listato in ListModels ma NON usabile free. Fatto, non speculazione.
- **Deep Research VALUTATO e SCARTATO (motivazione fattuale, NON ritornarci in S237)**: output Gemini Deep Research arrivato a fine S236, raccomanda **Llama 4 Maverick** per qualità copy B2B IT (tesi: 12 lingue core ottimizzate vs 119 di Qwen). **Scartato** perché NON eseguibile a costo zero su ARGOS, verificato live: `meta-llama/llama-4-maverick` su OpenRouter esiste SOLO a pagamento (`pricing.prompt=0.00000015` = $0.15/M), **nessun tier `:free`**; locale impossibile (MoE 400B, no GPU su Big Sur/iMac 2012). La tesi qualità-IT è proxy debole (il DR stesso ammette: nessun benchmark copywriting-IT esiste; fonti non ufficiali "ClickRank"/"India Today"). → `gemini-2.5-flash` confermato (free reale + reasoning + quota separata + `_call_gemini` pronto).
- **OpenRouter live**: nessun `deepseek:free` vivo (candidato S233-1 MORTO, volatilità confermata). 21 `:free` totali; `pricing.prompt` è **stringa `'0'`** sul live (la claim S235 #3 "è float" era ERRATA) — irrilevante perché premium = Gemini.
- **Quota free 2.5-flash**: `ai.google.dev/rate-limits` NON espone più i numeri free (spostati su dashboard AI Studio auth). NON binding: il rigenera è human-triggered a bassa frequenza; l'esaurimento (429) è coperto dal floor guard. `[UNVERIFIED-NUMERO]` quota esatta — non serve per procedere.

### Scoperta architetturale (input per l'implementazione)
`pending_replies` (INSERT `response-analyzer.py:1503`) salva SOLO `(id, dealer_id, dealer_name, reply_text, reply_label, approved, sent)` — **NON** archetype né inbound originale. → `cmd_genera` DEVE ri-recuperare inbound+archetype dal DB (`messages`/`conversations`) e ricostruire il prompt via `build_system_prompt` (`response-analyzer.py:448`). Questo è il pezzo da delegare a backend.

### Stato IMPLEMENTAZIONE (delega ai-engineer CRASHATA mid-work, API error dopo 14 tool-use)
Sul disco c'è SOLO scaffolding (additivo, compila, ripulito da CC della doppia-assegnazione lasciata a metà): `telegram-handler.py:51-62` = costanti `GOOGLE_AI_API_KEY`, `REGEN_GEMINI_URL`, `REGEN_GEMINI_MODEL='gemini-2.5-flash'`, `REGEN_LOG_PATH`. **NULLA d'altro**: niente `cmd_genera`, niente 3° bottone, niente branch callback `genera`, niente JSONL, niente caller. **VERIFIED #9 invariato (no impatto). NON deployato.**

### NEXT (S237) — implementare con spec COMPLETO qui sotto (delega ai-engineer/backend-architect, edit-only no deploy), POI deploy 2 path + gate fisico
SPEC `cmd_genera(reply_id)` (Python **3.9** compat su path tg-bot — VIETATO `str|None` PEP 604, usa `Optional`; solo `requests`):
1. Legge riga `pending_replies` (dealer_id, dealer_name, reply_text orig, reply_label).
2. Re-recupera inbound dealer + archetype dal DB (`messages`/`conversations` in `dealer_network.sqlite`; archetype via classifier/`build_system_prompt`). Ricostruisce system+user prompt; inietta "reply precedente respinta dall'operatore → produci versione più forte/diversa, NON identica".
3. Chiama premium `gemini-2.5-flash` (riusa pattern `src/llm_cascade.py:_call_gemini` riga 202, requests-only).
4. **Floor guard**: premium fallisce (429/404/timeout) → NON spacciare fallback debole per premium; avvisa operatore "rigenera premium non disponibile (motivo)" + LASCIA reply invariata. 404 esplicito.
5. Successo: `UPDATE pending_replies SET reply_text=<nuova>, approved=NULL, sent=0 WHERE id=?` + ri-notifica con keyboard COMPLETA (✅/🚫/🔄).
6. **JSONL append-only** `wa-intelligence/regenerate_log.jsonl` (path già in `REGEN_LOG_PATH`): `{"ts":iso8601,"reply_id":...,"archetype":...,"reason":"operator_rejected_no_reason","model_used":"gemini-2.5-flash","original":<reply precedente>}`. (Cattura testuale del `reason` via force_reply = enhancement futuro, NON ora.)
7. Aggiungere 3° bottone `genera:<id>` in `make_inline_keyboard` (`telegram-handler.py:143`) + branch `action=='genera'` nel callback handler (`telegram-handler.py:826-834`) che chiama `cmd_genera`.
- **Deploy ENTRAMBI i path (path-split S233)**: `telegram-handler.py` → release path `releases/.../wa-intelligence/` (tg-bot gira da lì); se tocchi `response-analyzer.py` → anche ROOT `~/Documents/app-antigravity-auto/wa-intelligence/` (daemon spawna da ROOT). Restart SOLO `argos-tg-bot`, NON `argos-wa-daemon` (baseline `restart_time=50`).
- **Gate fisico TEST_FOUNDER 393314928901** (human-gated, MAI auto-VERIFIED): SEED da SIM → notifica con 🔄 → tap Rigenera → nuova reply premium arriva nel bot con keyboard → approva → arriva sulla SIM. iMac clock +2h · log tg-bot `/tmp/argos-tg-bot-out.log`.

### Vincoli S237: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · `restart_time argos-wa-daemon`=50 · iMac clock +2h · deploy 2 path.

---

# S226 — Ripartenza (riscritto a mano da CC, supersede stub auto-gen + handoff S225)

**Branch**: `s210/audit-master-plan` · **Generato**: 2026-06-02 · **Last commit**: `f63a1ee` (locale, NON deployato)
Questo file riscrive lo stub auto-generato. Fonte ricca precedente: `.claude/NEXT_SESSION_PROMPT.manual.md` (S225) — qui consolidata e corretta con la governance decisa il 2026-06-02.

---

## ✅ S235 — ESITO (2026-06-03): DESIGN "🔄 Rigenera" VALIDATO DATA-DRIVEN → premium = Gemini su API Google (NON OpenRouter). Implementazione = S236.

### Cosa è stato fatto (no codice, solo validazione)
Output Claude AI sul design rigenera ricevuto + fact-check delegato (`research-fact-checker`, 2+ fonti) sui 6 claim OpenRouter + lettura `src/llm_cascade.py`. Nessuna modifica codice (chiusura @ budget 55%).

### Matrix validazione 6 claim OpenRouter (fonti ufficiali, giugno 2026)
1. Rate-limit free 50/giorno · 20/min · 1000/giorno con ≥$10 → **CONFIRMED**
2. Richieste fallite contano verso quota → **UNVERIFIABLE** (1 sola fonte Zendesk) — testare con 1 call
3. `pricing.prompt == "0"` indica free → **DISPUTED**: `expiration_date` ESISTE, ma `pricing.prompt` è **float non stringa** → `=="0"` sempre False (bug nel codice Claude AI). Fix: `float(price)==0.0`
4. array `models` = fallback nativo → **CONFIRMED** ma **bug noto**: un 404 FERMA la chain invece di proseguire (proprio il caso `:free` deprecato)
5. response `model` = modello reale usato → **CONFIRMED**
6. modello deprecato → 404 "no endpoints found" → **CONFIRMED** (stesso 404 per feature-incompat → parsare body)

### Finding decisivo da `src/llm_cascade.py` (verificato a codice)
- **Gemini gira su API Google DIRETTA** (`generativelanguage.googleapis.com`): liv.1 `gemini-2.0-flash` (250/giorno), liv.4 `gemini-2.0-flash-lite` (1000/giorno), via `GOOGLE_AI_API_KEY`. **Quota SEPARATA dalle 50/giorno OpenRouter** (liv.3 = `meta-llama/llama-3.3-70b-instruct:free` hardcoded riga 172).
- **Bug stale scoperto**: docstring riga 9 dichiara OpenRouter free "1000 req/day" → REALTÀ 50/giorno (sovrastima 20×). Non è blocker rigenera ma è un debito-doc.
- `_call_gemini()` (riga 202) esiste, `requests`-only, no SDK → aggiungere provider premium Gemini = riuso path testato.

### RACCOMANDAZIONE CTO (single, data-grounded) per S236
**Premium del rigenera = modello reasoning Gemini su API Google diretta, NON un `:free` OpenRouter.** Perché: (1) quota Google separata → no collisione con 50/giorno OpenRouter; (2) infra `_call_gemini` già pronta; (3) cancella i 3 bug verificati OpenRouter (float `=="0"`, 404-ferma-chain, deprecation) + tutta la sezione (b) volatilità del design Claude AI diventa inutile.
- **TENGO di Claude AI**: tesi "il prompt è la leva ~70%, modello ~30%" (combacia con regola business `communication.md`: conversione da competenza-mercato non persuasione) + re-prompt che inietta motivo-rifiuto+persona+dati reali + log JSONL append-only `{ts,reply_id,archetype,reason,model_used,original}`.
- **SCARTO**: `refresh_free_catalog()`, `PREMIUM_PREFERENCE` editoriale, discovery OpenRouter.
- **Floor guard** (se premium non disponibile → NON spacciare cascade per premium) = da tenere.

### GATE IMPLEMENTAZIONE S236 — l'UNICO dato non verificato
**Quale modello Gemini reasoning è free su API Google a giugno 2026 + quota** (cascade usa `gemini-2.0-flash`; verificare se `gemini-2.5-pro`/`flash` free più forte esiste). METODO (Luke S235): i FATTI-API si chiudono interrogando endpoint LIVE, NON Deep Research: (1) `GET generativelanguage.googleapis.com/v1beta/models?key=` → id Gemini reali; (2) `GET openrouter.ai/api/v1/models` → id `:free` vivi + `expiration_date`; (3) quote free Gemini = WebFetch doc `ai.google.dev/rate-limits` (non in ListModels). Deep Research SOLO per ranking-qualità copy B2B italiano tra i candidati risultati vivi (no endpoint per "quale è più bravo"). Verificato questo → implementare (`ai-engineer`/`backend-architect`), deploy **ENTRAMBI i path** (tg-bot release + daemon ROOT, path-split S233), gate fisico TEST_FOUNDER.

### Vincoli S236: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · baseline `restart_time argos-wa-daemon=50` · iMac clock +2h · path log tg-bot `/tmp/argos-tg-bot-out.log` · deploy SEMPRE su 2 path.

---

## ✅ S234 — ESITO (2026-06-03): GATE #9-B SCENARIO B = PASS RUNTIME → anello #9 VERIFIED 3/9 (Luke soddisfatto)

### ✅ FATTO (runtime-verified, R1):
1. **VERIFICA BOTTONI = PASS (punto 1 S234).** La notifica TG mostra i bottoni inline **✅Accetta / 🚫Rifiuta** (non più testo `/rifiuta`). Prova: screenshot Luke ore 16:39 (clock sessione) — bottoni renderizzati + ack bot `🚫 Reply reply_ec6bdb52 rifiutata. Nessun messaggio inviato` + DB `reply_ec6bdb52 approved=0,sent=0`. **Il fix path-split ROOT (S233) è confermato a runtime.**
2. **Real-case reject VERIFIED.** Tap diretto 🚫Rifiuta (senza accetta) → `cmd_rifiuta` porta `approved` NULL→0, `sent=0`, nessun msg, ack consegnato. Path rifiuta sano a runtime.

### ✅ GATE #9-B ABORT-RACE = PASS RUNTIME → anello #9 VERIFIED 3/9
Sequenza completa provata su `reply_8c0934fb` (log `/tmp/argos-tg-bot-out.log` + `/tmp/argos-tg-send.log`):
- ✅ `approva:reply_8c0934fb` + **`sleep 415s`** (18:46:11 iMac/+2h)
- 🚫 `rifiuta:reply_8c0934fb` 2s dopo, **DURANTE lo sleep** (18:46:13)
- guard a fine sleep: **`[ABORT] Reply reply_8c0934fb non piu approvata (rifiutata durante sleep) — invio annullato`**
- DB `approved=0, sent=0` · `argos-wa-daemon` online `restart_time=50` invariato (non-VOID, window-integrity OK) · Luke conferma NESSUN msg sulla SIM + **"soddisfatto"**.
- Prova indipendente = `[ABORT]` (NON dipende da `sent` TAINTED). **#9 chiuso VERIFIED 3/9** (era 2/9 da ~130 sessioni).
- **PATH LOG TG-BOT corretto = `/tmp/argos-tg-bot-out.log`** (NON `~/.pm2/logs/` — memorizzare per debug futuri). iMac clock **+2h**.
- `reply_dd01fa73` (16:54) stessa sequenza corretta, `[ABORT]` atteso ~17:03 (sleep 523s ancora in corso a fine sessione) — ridondante, non serve verificarla.

### NEXT (S235) — implementare tasto "🔄 Rigenera" (BACKLOG S233-1, sbloccato perché #9 è verde). ORDINE: (1) portare il PROMPT CLAUDE AI qui sotto a Claude.ai per second-opinion design, (2) incrociare con autocritica CC, (3) implementare con `ai-engineer`/`backend-architect`, (4) deploy ENTRAMBI i path (tg-bot release + daemon ROOT), (5) gate fisico TEST_FOUNDER.

### 📋 PROMPT CLAUDE AI — design tasto "🔄 Rigenera" (incolla a Claude.ai web, S235 STEP 0):
```
Sei un architetto software. ARGOS è un sistema Python di outreach B2B auto. Un bot Telegram
notifica all'operatore umano (HITL) le reply generate da LLM; l'operatore le approva/rifiuta con
bottoni inline (✅Accetta / 🚫Rifiuta, appena verificati a runtime). Le reply sono generate da
`src/llm_cascade.py`: cascade 5 livelli che prova provider in ordine FISSO hardcoded per
DISPONIBILITÀ, non qualità: Gemini Flash → Groq llama-3.3-70b → OpenRouter llama-3.3-70b:free →
Gemini Lite → Ollama qwen2.5:3b. La cascade DEGRADA (ogni livello ≤ del precedente, l'ultimo è il
più debole). Circuit breaker per provider (3 fail/5min → OPEN 10min → skip). Tutti FREE-tier.

OBIETTIVO: aggiungere un 3° bottone inline "🔄 Rigenera" che, quando l'operatore NON è soddisfatto
di una reply, la rigeneri con un modello PIÙ FORTE (non uguale/peggiore come darebbe la cascade).

VINCOLI HARD: zero-cost assoluto (solo free-tier o già pagato, €0 capex); macOS 11 Big Sur +
Python 3.13 (iMac) / 3.9 (path tg-bot, no PEP 604 `str|None`); solo libreria `requests`, no SDK AI;
catalogo OpenRouter free-tier VOLATILE (modelli `:free` appaiono/spariscono, rate-limit cambiano —
verificato giugno 2026), quindi NO model-id hardcodato fragile; mantenere cascade + circuit breaker.

VOGLIO UNA RACCOMANDAZIONE SINGOLA MOTIVATA (no liste A/B/C) su:
Q1 — con quale meccanismo il "rigenera" sceglie un modello PIÙ COMPETENTE? Oggi nessuno: serve un
     "provider premium" dedicato invocato SOLO dal callback `genera:<id>`. Come definire "più forte"
     in modo robusto e zero-cost? (NB: il collo di bottiglia di una reply dealer-grade potrebbe
     essere il PROMPT/contesto-persona, non la potenza del modello — valuta questa ipotesi).
Q2 — come gestire PROATTIVAMENTE la volatilità free-tier OpenRouter? Oggi ARGOS ha solo il
     circuit-breaker reattivo, nessun refresh catalogo (se un `:free` sparisce, resta skippato finché
     qualcuno tocca il codice). Valuta discovery periodico `GET /api/v1/models`, healthcheck, catena
     premium con fallback.
Extra — il rigenera dovrebbe loggare il MOTIVO del rifiuto (segnale per migliorare il prompt, non
     solo cambiare modello)?

OUTPUT: (a) come selezionare il modello premium; (b) come gestire la volatilità; (c) pseudo-codice del
provider premium + handler callback `genera:<id>`; (d) autocritica 4 punti (assunzioni nascoste, cosa
rompe a 30/60/90gg, pattern errori noti su sistemi simili, dove sovradimensioni).
```
**Findings CC già verificati su `src/llm_cascade.py` (input per il giudizio):** cascade DEGRADA non escala · model-id OpenRouter hardcoded riga 172 · volatilità gestita SOLO da circuit-breaker reattivo (righe 64-141) · `routing.yaml`/`routing-refresh` sono VOS, NON ARGOS (non riusabili).

### 🆕 BACKLOG S233-1 aggiornato (tasto "🔄 Rigenera") — chiarito su codice reale (`src/llm_cascade.py`):
- **La cascade ARGOS NON escala verso l'alto, DEGRADA verso il basso.** Lista fissa hardcoded 5 provider per *disponibilità non qualità*: Gemini Flash → Groq llama-3.3-70b → OpenRouter free llama-3.3-70b:free → Gemini Lite → Ollama qwen2.5:3b (il più debole, ultimo). Riusare la cascade per "rigenera migliore" darebbe modello uguale/peggiore.
- **Volatilità free-tier OpenRouter NON gestita proattivamente.** Model-id hardcoded (`llm_cascade.py:172`). Solo circuit-breaker reattivo (3 fail/5min → OPEN 10min → skip). NESSUN auto-discovery catalogo. **CORREZIONE:** `routing.yaml`+`routing-refresh` sono meccanismi **VOS, NON ARGOS** (claim mio S234 ritirato, era unverified).
- **Design rigenera (post #9-B):** provider "premium" DEDICATO in cima invocato solo da callback `genera:<id>` (candidato zero-cost forte = DeepSeek V3 free, id esatto da verificare al momento = volatile) + fallback su cascade normale se 404/rate-limit + log del motivo-rifiuto. NON hardcodare l'id senza un check catalogo.

### Vincoli S235: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · baseline `restart_time argos-wa-daemon=50` · iMac clock +2h da tenere a mente sui log.

---

## ⏸ S233 — ESITO (2026-06-03, chiusura @ budget 60%): DEPLOY FIXATO SUL PATH GIUSTO (path-split ROOT scoperto) — GATE #9-B NON ESEGUITO, ORA SBLOCCATO
**Due finding strutturali risolti, gate B non ancora eseguito. VERIFIED resta 2/9.**

### FATTO (runtime-verified, R1):
1. **Fix compat Python 3.9 (commit `0132f92`).** Assunto handoff S233 "tg-bot gira su 3.13" SMENTITO a runtime: `argos-tg-bot` gira con `--interpreter python3` → **Python 3.9** (CommandLineTools, doc linea 23 telegram-handler.py). La syntax `str | None` (PEP 604, 3.10+) di S232 crashava all'import = **crash loop osservato**. Fix: rimossa annotation di ritorno cosmetica su `make_inline_keyboard` (telegram-handler.py:143). Deploy release `20260527_083951` verificato: tg-bot online STABILE (uptime cresce, no crash loop), no traceback, `argos-wa-daemon` ↺=50 invariato + connected.
2. **PATH-SPLIT CODICE scoperto (stessa classe di C-DB-SPLIT S226/S228, ora su file .py).** La notifica reply NON mostrava i bottoni anche DOPO deploy. Root cause: `wa-daemon.js:40` `ANALYZER_SCRIPT = path.join(__dirname,'response-analyzer.py')` + cwd daemon (PID 78295) = **`~/Documents/app-antigravity-auto/wa-intelligence/` (ROOT)**, NON il release path dove avevo deployato. Il daemon spawna la copia ROOT (per-inbound, no restart). **Fix:** `response-analyzer.py` copiato su ROOT (`md5 1a0243ec` match, backup `.bak-pre-s233` 114700B verificato). I bottoni inline ESISTONO già nel codice (response-analyzer.py:1889-1908, `send_telegram_notification`) → ora sul path giusto.
   - **DISALLINEAMENTO PATH da sapere:** `argos-tg-bot` gira dal **release path** `releases/20260527_083951/wa-intelligence/` (callback_query handler lì = OK). `argos-wa-daemon` gira da **ROOT** e spawna response-analyzer da ROOT. Due root diverse → un deploy completo deve toccare ENTRAMBI i path per i file rilevanti.

### `UNVERIFIED-RUNTIME` (NON ho potuto verificare a runtime — budget):
- I bottoni NON sono ancora stati VISTI da Luke su una notifica reale (il fix ROOT è arrivato dopo l'ultima notifica delle 16:23, che era ancora la copia vecchia). **Prossimo inbound dovrebbe renderli.**
- Gate #9 Scenario B NON eseguito.

### NEXT (S234) — verifica bottoni + GATE #9-B (apertura ~15 min):
1. **VERIFICA BOTTONI (30s):** Luke manda WA dalla SIM `393314928901` → ARGOS Business `3281536308` → la notifica TG deve ora mostrare **✅ Accetta / 🚫 Rifiuta** (bottoni, non testo `/rifiuta`). Se SÌ → fix path confermato runtime.
2. **GATE #9-B v3 (ack-gate + bottoni):** SEED → reply_id (DB ROOT: `approved=NULL,sent=0`) → tap **✅ Accetta** (bot: "approvata, invio tra ~Nmin") → SUBITO tap **🚫 Rifiuta** → ATTENDI ack bot `🚫 Reply rifiutata` → attendi fine sleep (~12min). **PASS B = NESSUN msg sulla SIM + log `[ABORT]` + `approved=0` + `sent=0` + `restart_time argos-wa-daemon`=50 invariato** → **#9 VERIFIED 3/9** + Luke "soddisfatto". Verità = msg fisico sulla SIM (`sent` TAINTED). Vietato re-validare staticamente (#1b).

### 🆕 BACKLOG S233-1 (richiesta founder, NUOVO SCOPE — non implementato): terzo bottone "🔄 Genera nuova reply"
Luke: vuole un terzo bottone inline che **rigeneri la reply usando un altro LLM** (potenzialmente migliore) invece di solo accetta/rifiuta. Richiede: nuovo `callback_data` `genera:<id>` + handler in telegram-handler.py run_daemon che ri-invoca la generazione reply (response-analyzer / cascade LLM) e ri-notifica. Scope > gate B → valutare dopo che #9-B è VERIFIED.

### Vincoli S234: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · baseline `restart_time argos-wa-daemon=50` · rollback response-analyzer ROOT = `cp response-analyzer.py.bak-pre-s233 response-analyzer.py` (no restart).

---

## ⏸ S232 — ESITO (2026-06-03, chiusura ordinata @ budget 60%): BOTTONI INLINE IMPLEMENTATI (code-verified) — DEPLOY + GATE #9-B NON ESEGUITI
**Deliverable 1 (bottoni inline accetta/rifiuta) = IMPLEMENTATO nel repo, `UNVERIFIED-RUNTIME`** (delega rapid-prototyper + verifica CC sui path critici). NON deployato su iMac, NON runtime-testato.
- **File modificati (repo, NON deployati):** `wa-intelligence/telegram-handler.py` + `wa-intelligence/response-analyzer.py`. `python3 -m py_compile` OK su entrambi.
- **Cosa fa:**
  - `telegram-handler.py:143` nuovo helper `make_inline_keyboard(reply_id)` → JSON `{inline_keyboard:[[✅ Accetta `approva:<id>`, 🚫 Rifiuta `rifiuta:<id>`]]}` (guard 64-byte callback_data). `send()` (riga 132) esteso con param `reply_markup`.
  - `telegram-handler.py:805` polling `allowed_updates` ora `json.dumps(['message','callback_query'])`. `run_daemon` (812-834) nuovo branch `callback_query`: auth chat_id identica al path testo → `answerCallbackQuery` (toglie spinner) → split `data` su `:` → chiama **cmd_approva/cmd_rifiuta esistenti** (no logica duplicata, riusa guard #9) → `send(reply)` conferma. Offset avanza per OGNI update. Branch `message` legacy INTATTO.
  - `response-analyzer.py:1889` (`send_telegram_notification`, notifica PUSH del gate) + `:1946` (`send_telegram_hold` multi-candidato) → `reply_markup` aggiunto al payload sendMessage, mantenuto in ENTRAMBI i tentativi Markdown/plain. Path PENDING (best_id) eredita i bottoni via `send_telegram_notification`.
  - `cmd_pending` NON modificato (keyboard è message-level; i bottoni live arrivano sulle notifiche PUSH = quelle del gate). Scelta a basso rischio.
- **Guard #9 NON toccato** (re-check approved post-sleep `telegram-handler.py:256-264` intatto). `argos-wa-daemon` NON toccato.
- **Verità #9 invariata: VERIFIED resta 2/9** (#1b: code-verified ≠ chiusura).

### NEXT (S233) — 2 cose in sequenza, gate-packet già armato:
1. **DEPLOY (delega devops-automator, rsync atomico):** copia i 2 file → `releases/20260527_083951/wa-intelligence/` con backup `.bak-pre-s232`. **Restart SOLO `argos-tg-bot`. NON toccare `argos-wa-daemon`** (deve restare `connected`, baseline `restart_time=50`). Verifica runtime: tg-bot online + daemon connected. NB: i 2 file girano sotto Python 3.13 su iMac (`str | None` annotation OK, confermato S197).
2. **GATE #9 Scenario B v3 ARMATO (ack-gate + bottoni):** SEED da SIM TEST_FOUNDER `393314928901` → reply_id (verifica DB `approved=NULL,sent=0`) → **tap ✅ Accetta** (bot risponde "✅ approvata — invio tra ~Nmin") → **SUBITO tap 🚫 Rifiuta** → **ATTENDI ack bot "🚫 Reply rifiutata"** (prova revoca eseguita; il tap garantisce consegna col reply_id esatto = fix root-cause harness S231) → attendi fine sleep (max ~12min). **PASS B = NESSUN msg sulla SIM + log `[ABORT]` + `approved=0` + `sent=0` + `restart_time argos-wa-daemon`=50 invariato** (se ≠ → VOID, retry). PASS → **#9 VERIFIED 3/9** + Luke "soddisfatto". Verità = msg fisico sulla SIM (`sent` TAINTED). Vietato re-validare staticamente (#1b).

**Vincoli S233:** TEST_FOUNDER prima di dealer reali · domenica OFF Luke · `image_sanitizer`/landing CONGELATI · baseline `restart_time argos-wa-daemon=50`.

---

## ⏹ S231 — ESITO (2026-06-03): GATE #9 SCENARIO B **INCONCLUSIVE** (non FAIL guard) → re-run armato + nuova richiesta Luke (bottoni inline)
**Gate fisico eseguito con Luke** su SIM TEST_FOUNDER `393314928901`, `reply_b785f97b`. Window-integrity OK (`restart_time argos-wa-daemon=50` PRE/POST → **NON-VOID, test valido**).
- **Esito:** Scenario B **NON passato MA NON è un FAIL del guard** — il guard non è mai stato esercitato.
- **Dati (delega devops-automator, read-only):** log tg-bot `13:09:16 Comando ricevuto: /approva reply_b785f97b` + `Approvata ... sleep 229s`; **NESSUNA riga `Comando ricevuto: /rifiuta`** in 120 righe. Log send: `[SENT] ... /send-multi ref=[3× multi_*]`, NO `[ABORT]`. DB ROOT: `reply_b785f97b | approved=1 | sent=1`, daily_sent 0→3. Luke conferma: 3 msg ARRIVATI sulla SIM; il bot mostrò `📤 Multi-msg INVIATO` (conferma invio daemon, NON `🚫 Reply rifiutata`).
- **Diagnosi:** `/rifiuta` non è mai arrivato a `cmd_rifiuta` → `approved` mai 0 → guard post-sleep ha riletto `approved=1` e ha (correttamente per la sua logica) inviato.
- **Guard sano (code-verified, NON prova di chiusura #1b):** `cmd_approva` lancia sleep in `subprocess.Popen` non-bloccante + re-check `approved` post-sleep (`telegram-handler.py:256-264` → `[ABORT]`); `cmd_rifiuta:369-372` = `UPDATE ... SET approved=0 WHERE id=? AND sent=0` (corretto); `run_daemon:782-806` polling NON bloccato dal subprocess → bot POTEVA ricevere /rifiuta.
- **Root cause /rifiuta sparito: NON determinata [UNVERIFIED]** (non inviato / consegna Telegram persa).
- **Fix harness (procedura): ack-gate** — al re-run, dopo `/rifiuta` ATTENDERE risposta bot `🚫 Reply rifiutata` (prova che revoca eseguita) PRIMA di committere all'attesa sleep; se entro ~20s niente ack → rimandare /rifiuta. Self-correcting a prescindere dalla root cause.

**#9 RESTA: Scenario A VERIFIED (S230) · Scenario B PENDING-GATE re-run armato. VERIFIED resta 2/9** (onestà R1, no re-validazione statica #1b).

### 🆕 RICHIESTA FOUNDER S231 (scope prossima sessione, NON implementata — context budget): bottoni INLINE `/accetta`-`/rifiuta` su TUTTI i msg generati
Luke: *"bisogna inserire /accetta /rifiuta per tutti i messaggi generati come abbiamo definito"*. Oggi la notifica TG mostra `/approva {id} | /rifiuta {id}` come **testo** (`telegram-handler.py:557`) → richiede typing manuale = fragilità che ha rotto il gate B. **Fix proposto:** inline keyboard (Telegram `reply_markup` + `callback_query`, `allowed_updates` da estendere a `callback_query` nel polling riga 788) su ogni notifica reply generata → tap garantisce consegna con `reply_id` esatto, niente typing. **Risolve sia la richiesta founder sia la root-cause harness del gate B.** Valutare in apertura S232 come PRE del re-run (un solo lavoro che chiude due cose).

### GATE PACKET #9 — Scenario B v3 (ARMATO con ack-gate) — pronto per S232
```
PRE (CC): baseline iMac read-only (devops): wa_status=connected · restart_time argos-wa-daemon (era 50) · ultima riga /tmp/argos-tg-send.log
SEED (Luke): WA da SIM 393314928901 → reply_id (verifica DB: approved=NULL, sent=0)
ESEGUI: /approva <id> → bot risponde "✅ approvata — invio tra ~Nmin" (annota N)
        SUBITO /rifiuta <id> → **ATTENDI bot "🚫 Reply rifiutata"** (ack-gate). Se entro ~20s niente → rimanda /rifiuta.
        Solo a ack ricevuto → attendi fine sleep (max ~12min)
PASS B = NESSUN msg sulla SIM + log [ABORT] + approved=0 + sent=0 + restart_time invariato (se ≠ → VOID, retry)
CHIUSURA: Luke "soddisfatto" → #9 VERIFIED 3/9.
```
**Backlog confermato S224-1:** `reply_d18d7dc6` resta `approved=1,sent=0` — reconcile path TG. (NB `reply_b785f97b` sent=1 = invio reale a TEST_FOUNDER, legittimo, non backlog.)

---

## ✅ S230 — ESITO (2026-06-02): GATE #9 SCENARIO A VERIFIED RUNTIME (multi-msg) → resta SOLO Scenario B
**Gate fisico eseguito con Luke, DUE cicli.** SEED reali dalla SIM TEST_FOUNDER `393314928901`.
- **Ciclo 1 (`reply_eff8cfb3`):** `/approva` → msg ARRIVATO sulla SIM + log `[SENT] ... via daemon msg_id=out_1780428918468_qel9v` + `sent=1` + `daily_sent` 0→1 + `restart_time=50` invariato. **MA payload = envelope JSON grezzo** `{"messages":[...]}` (NUOVO bug C-WA-SEND-MULTIMSG). Trasporto OK, formato rotto.
- **Root cause C-WA-SEND-MULTIMSG:** `telegram-handler.py:266` inviava `reply_text` (envelope AMBRA multi-msg) come singolo `message` a `/send`. Il branch mono/multi canonico esisteva solo in `response-analyzer.py:1677-1693`, non nel path `/approva`.
- **FIX S230 (delega devops-automator, code+diff verificato da CC):** send_script di `telegram-handler.py` (righe 265-303) ora fa `json.loads(reply_text)` → se `messages[]` non vuoto POST a **`/send-multi`** (`{phone, messages}`, NO force), altrimenti `/send` testo+force. URL derivato da `daemon_url.rsplit('/',1)[0]+'/send-multi'`. **Guard #9 re-check `approved` post-sleep (righe 256-264) INTATTO.** `[SENT]` ora stampa `ref=<msg_ids>`. py_compile OK. Deploy iMac release `20260527_083951` (backup `.bak-pre-s230`, md5 match `b08ef3e6...`), restart SOLO `argos-tg-bot`, daemon non toccato (`connected`).
- **Contratto `/send-multi` (wa-daemon.js:1332) chiuso:** risposta successo `{status:'sent', msg_ids:[...], count, daily_sent}`; **non** accetta `force`; bypassa business-hours per TEST_FOUNDER via `isAllowedToSend` (`wa-daemon.js:799-804`) → gate eseguibile fuori orario per la SIM. NB: dealer REALI fuori 09-18 → 403, da fare in orario.
- **Ciclo 2 (`reply_26e8c243`) POST-FIX:** `/approva` → sulla SIM **2 messaggi separati, italiano leggibile stile AMBRA** (Luke confermato) + log `[SENT] ... /send-multi ref=[2× multi_*]` + `approved=1,sent=1` + `daily_sent` 1→3 + `restart_time=50` invariato (non-VOID).

**#9 RICLASSIFICATO:** **Scenario A (invio consentito) = VERIFIED RUNTIME** end-to-end (consegna corretta multi-msg via single-writer). **Scenario B (revoca durante sleep → `[ABORT]` + nessun msg) NON ancora runtime-testato** — code-verified, condivide il re-check provato in A. **VERIFIED resta 2/9 finché B non passa** (gate #9 = A+B per chiusura piena, contratto packet v2). NON è 3/9 con la sola A: onestà R1.

**NEXT (S231) — chiudere #9 con Scenario B (apertura ~10 min, delega devops per monitor):** SEED nuovo dalla SIM → `reply_idB` → `/approva reply_idB` poi **subito (<60s) `/rifiuta reply_idB`** → attendi fine sleep (max ~12 min) → PASS B = NESSUN msg sulla SIM + log `[ABORT]` + `approved=0` + `sent=0` + `restart_time` invariato. Se PASS → **#9 VERIFIED 3/9**. PRE già pronto (fix LIVE su iMac). Vietato re-validare staticamente (#1b).
**Backlog confermato S224-1:** `reply_d18d7dc6` resta `approved=1,sent=0` (fallimento PRE-fix S228, non si auto-risolve) — reconcile path TG.

---

## ⏹ S229 — ESITO (2026-06-02): C-WA-SEND-SPLIT FIXATO + DEPLOYATO → #9 ora BLOCKED-ON Luke fisico
**Fix applicato (delega devops-automator, code-verified):** il path `/approva` non spawna più `send_message.js` standalone (auth dir inesistente). Ora `cmd_approva` invia via **daemon connesso** POST `http://127.0.0.1:9191/send` + `X-API-Key` (single-writer S173). Edit chirurgico in `telegram-handler.py`:
- `task` dict (righe 237-246): `wa_id`/`wa_sender`/`client_id` → `phone`+`daemon_url`+`api_key`+`force`.
- `send_script` (righe 252-289): **guard HITL re-check `approved` post-sleep INTATTO** (anello #9 verificato); sostituito SOLO il blocco invio `node` con POST urllib; `[ABORT]/[ERROR]/[SENT]` preservati; `UPDATE sent=1` preservato. `py_compile` OK.
- **3 decisioni design:** (1) NON passo `dealer_id`/`template_id` → evito `runOutboundGuard` S106 (bloccherebbe la reply) + bump `current_step`; reply va come send "manual", tracking autoritativo = `pending_replies.sent=1`; (2) `force=true` (Luke approva esplicitamente, annulla precheck24h duplicato daemon); (3) business-hours gate introdotto da `/send` ma TEST_FOUNDER 393314928901 lo bypassa (`wa-daemon.js:799-805`).

**Deploy iMac (devops-automator):** file → `releases/20260527_083951/wa-intelligence/telegram-handler.py` (backup `.bak-pre-s229`). Restart SOLO `argos-tg-bot` (PID 91112 online); `argos-wa-daemon` NON toccato, `wa_status: connected`. **Preconditions verificate:** `ARGOS_API_KEY` presente su tg-bot (no 401), `TEST_FOUNDER_PHONE=393314928901` presente sul daemon (no business-hours block).

**#9 RICLASSIFICATO:** resta **PENDING-GATE**, ora **BLOCKED-ON Luke fisico** (NON più fix codice — C-WA-SEND-SPLIT chiuso code+deploy). **VERIFIED resta 2/9** → sale a 3/9 SOLO a gate fisico passato. La fix è ora RAGGIUNGIBILE (deployata) — vietato re-validarla staticamente (vincolo #1b).

**GATE PACKET #9 v2 — pronto per Luke (esegui il blocco "GATE PACKET #9 — v2" più sotto):** SEED dalla SIM 393314928901 → `/approva <reply_id>` → atteso log iMac `/tmp/argos-tg-send.log`: `[SENT] Reply <id> inviata via daemon msg_id=<id>` + msg ARRIVA sulla SIM (Scenario A). Scenario B: `/approva` poi subito `/rifiuta` → `[ABORT]` + nessun msg + `approved=0`.

---

## ⏹ S228 — ESITO (2026-06-02): GATE #9 ESEGUITO → guard OK, E2E send BLOCCATO da split sessione WA (NUOVO: C-WA-SEND-SPLIT)
**Gate fisico eseguito con Luke.** SEED reale dalla SIM TEST_FOUNDER `393314928901` → `reply_d18d7dc6` (`approved=NULL` PRE = P1 runtime confermato). Luke `/approva reply_d18d7dc6` da TG (niente precheck-block).
- **Guard HITL CORRETTO:** `approved=NULL→1`, tentato invio post-sleep, invio fallito (`node sender rc=1`), `sent` **giustamente NON marcato** (`sent=0` onesto, niente latent bug su questo path/evento).
- **Window-integrity OK (non-VOID):** `uptime_sec` PRE=2719 → POST=4370, nessun restart daemon nei ~12 min.
- **❌ NUOVO BLOCKER — C-WA-SEND-SPLIT:** log daemon `/tmp/argos-tg-send.log` → `❌ Sessione non trovata: ~/.wwebjs_auth/session-argos-business`. Il path `/approva` NON invia via daemon connesso: spawna standalone `~/Documents/app-antigravity-auto/wa-sender/send_message.js` (CLIENT_ID `argos-business`, `telegram-handler.py:45-47`) che cerca auth in `~/.wwebjs_auth/session-argos-business` (INESISTENTE). Daemon connesso usa auth dir diversa (`wa-intelligence/.wwebjs_auth`). Due client whatsapp-web.js → uno solo autenticato → invio path-TG fallisce SEMPRE.
- **NO business-hours gate** sul send path (`cmd_approva` non controlla orario — verificato): il fallimento è solo la sessione mancante, non l'orario.

**#9 RICLASSIFICATO:** resta **PENDING-GATE**, ora **BLOCKED-ON fix codice C-WA-SEND-SPLIT** (NON più Luke fisico: il SEED fisico è stato dato e ha funzionato). **VERIFIED resta 2/9.**

**NEXT (S229) — fix C-WA-SEND-SPLIT (delega devops-automator, time-boxed):** instradare l'invio del path Telegram attraverso il **daemon connesso** (single-writer già autenticato, principio bridge S173) invece di spawnare `send_message.js` standalone. Aggancia backlog "migrare path legacy TG al bridge canonico". Opzioni da valutare in apertura: (a) POST al daemon `:9191/send` con X-API-Key; (b) far puntare `send_message.js` alla stessa auth dir del daemon — SCARTATA a priori se i due client girano simultaneamente (LocalAuth lock whatsapp-web.js). Dopo il fix: ri-eseguire GATE PACKET #9 v2 (SEED già provato raggiungibile) → Scenario A msg ARRIVA sulla SIM + `[SENT]` → #9 VERIFIED 3/9. Scenario B (rifiuta durante sleep → `[ABORT]`) resta da provare.

**Scenario B NON eseguito** (bloccato a monte dal send split): da fare in S229 dopo il fix.

---

## ⏹ S227 — ESITO (2026-06-02): FONDAMENTA C-DB-SPLIT-001/C-DB-ENV-001 CHIUSA VERDE
**FATTO (runtime-verified via devops-automator, R1):** stack iMac ora gira sul DB CANONICO ROOT.
- **Root cause vera ≠ diagnosi S226.** Non era `dump.pm2` (già=ROOT). Era: `wa-intelligence/ecosystem.config.js` calcola `ARGOS_DB_PATH=path.join(BASE,'dealer_network.sqlite')` con BASE=`dirname(__dirname)` → dentro una release punta al DB della release; e **`deploy/sync.sh` linkava `.env` ma NON il DB** (rsync esclude `*.sqlite`) → ogni release nasceva senza DB e SQLite ne auto-creava uno VUOTO → split.
- **Fix permanente (repo):** `deploy/sync.sh` step [4/6] ora linka il DB canonico nella release (`ln -sfn $REMOTE_BASE/dealer_network.sqlite $RELEASE_DIR/dealer_network.sqlite`, pattern Capistrano linked-file). Previene la ricaduta.
- **Fix one-time (iMac):** `releases/20260527_083951/dealer_network.sqlite` (vuoto) → backup `.empty-bak-20260602_193153` + symlink `→ ../../dealer_network.sqlite` (ROOT). I 4 processi condividono quella stringa env → un solo symlink li redirige tutti su ROOT. Restart 4 proc + `pm2 save`.
- **Verifica runtime:** wa_status `connected` PRE/POST (sessione WA INTATTA), lsof daemon→ROOT, stack legge `pending_replies=21` + TEST_FOUNDER `DOSSIER_SENT`.
- **Step 5 "WA session fuori da releases" GIÀ soddisfatto:** auth a `wa-intelligence/.wwebjs_auth` (livello BASE).
- **Rollback manuale (se servisse):** `ssh imac 'cd ~/Documents/app-antigravity-auto/releases/20260527_083951 && pm2 stop argos-wa-daemon argos-tg-bot argos-cf-monitor argos-dashboard && rm dealer_network.sqlite && mv dealer_network.sqlite.empty-bak-20260602_193153 dealer_network.sqlite && pm2 start argos-wa-daemon argos-tg-bot argos-cf-monitor argos-dashboard'`

**#9 RICLASSIFICATO:** non più `BLOCKED-ON C-DB-ENV-001` (risolto). Ora **BLOCKED-ON Luke fisico** (SEED inbound dalla SIM TEST_FOUNDER). VERIFIED resta 2/9 → sale a 3/9 al gate fisico.

**NEXT (S228):** eseguire GATE PACKET #9 v2 (sotto, invariato) con Luke. PRE già fatto (deploy f63a1ee LIVE + stack su ROOT). Serve solo: Luke manda WA dalla SIM → reply_id → Scenario A/B. Verità di PASS = msg fisico sulla SIM (sent è TAINTED). Chiusura: #9→VERIFIED 3/9 o handoff.

---

## ▶ APERTURA (storico S227 — fondamenta ora CHIUSA, vedi ESITO sopra)
Sei CC che apre S227 su ARGOS. Internalizza R1–R4 + budget-rule (più sotto) e applicali. Stato: P0 deploy `f63a1ee` GIÀ LIVE su iMac; anello #9 = PENDING-GATE **BLOCKED-ON C-DB-ENV-001** (NON Luke fisico). VERIFIED 2/9. Il gate #9 è irraggiungibile finché lo stack gira sul DB sbagliato.
**Questa sessione fa UNA cosa: la fondamenta C-DB-ENV-001/C-DB-SPLIT-001 (R3, time-boxed 1 sessione), poi se avanza budget rieseguи il GATE PACKET #9 v2.** Delega a `devops-automator`. Esegui i 5 step del blocco "NEXT (S227)" qui sotto, in ordine, fermandoti se uno non passa. NON flippare l'env senza riconciliare i dati (R4 — è ciò che ha bloccato S226). Verità #9 = msg fisico sulla SIM (sent TAINTED). Chiusura: #9→VERIFIED 3/9 o handoff PENDING-GATE; mai chiusura silenziosa al budget.

---

## ⏹ S226 — ESITO (2026-06-02, chiusura ordinata al 59% budget)

**FATTO (runtime-verified, R1):**
- **P0 deploy `f63a1ee` su iMac = LIVE.** md5 locale==iMac sui 2 file in entrambi i path (root daemon + release tg-bot), healthcheck `:9191` HTTP 200, `wa_status: connected`. Backup `.bak-pre-f63a1ee` su 4 file → rollback 10s.
- **C-WA-RESTART window-integrity = PRONTO.** Campo PRE/POST = `pm2_env.restart_time` (valore 50 su `argos-wa-daemon`). Meccanismo gate disponibile.

**ROOT-CAUSE SCOPERTA (vero deliverable S226):** il gate #9 NON era raggiungibile, e NON per "Luke fisico". Inbound reale TEST_FOUNDER `393314928901` → daemon lo SCARTA "non in pipeline" (`wa-daemon.js:577-588` `lookupDealer` SELECT su `conversations`). Causa: **tutti e 4 i processi PM2 girano sul DB RELEASE sbagliato** (`releases/20260527_083951/dealer_network.sqlite`, 28KB, schema base 15 col, 0 `pending_replies`), via `ARGOS_DB_PATH` settato in **`~/.pm2/dump.pm2`** (NON in `sync.sh`). Il DB ROOT autoritativo (`~/Documents/app-antigravity-auto/dealer_network.sqlite`, 389KB, schema 30 col post-S201/S202, riga TEST_FOUNDER `current_step=DOSSIER_SENT opt_out=0`) è scavalcato. → **C-DB-ENV-001 + C-DB-SPLIT-001 VIVI = root cause strutturale di C-E2E-ZERO.**

**PERCHÉ NON HO FLIPPATO L'ENV (R4, challenge Luke corretto):** né ROOT né RELEASE è "il buono" pulito.
- ROOT: schema mantenuto + TEST_FOUNDER, MA dati congelati al 2026-05-16 (`conversations` max `state_updated_at`=16/05, 7 righe).
- RELEASE: DB runtime live, MA schema base (manca col `state_updated_at` ⇒ ALTER S201/S202 mai applicati) + quasi vuoto.
Env-flip secco = abbandona scritture RELEASE + schemi disallineati = violazione R4 (stato su dato non riconciliato). Serve sessione-fondamenta, non coda a 59%.

**#9 RICLASSIFICATO:** PENDING-GATE, `BLOCKED-ON: C-DB-ENV-001` (non più "Luke fisico"). **VERIFIED resta 2/9.** `UNVERIFIED-RUNTIME`: inbound→pending_reply · `/approva` runtime · Scenari A/B (tutti bloccati a monte dal DB sbagliato — non testabili finché lo stack gira su RELEASE).

**NEXT (S227) — fondamenta C-DB-ENV-001/C-DB-SPLIT-001, TIME-BOXED 1 sessione (delega devops-automator):**
1. DB canonico = **ROOT** (contratto riga 92 + default codice `telegram-handler.py:42` + schema mantenuto).
2. Riconciliare: verificare se RELEASE ha inbound/conversations post-16/05 da salvare → migrare su ROOT. Confermare schema ROOT completo per daemon Node (better-sqlite3 SELECT *).
3. Correggere `ARGOS_DB_PATH` dei 4 processi in `~/.pm2/dump.pm2` → ROOT · `pm2 save` · restart · verificare `pm2 jlist` DB=ROOT su tutti e 4.
4. Confermare `deploy/sync.sh` non re-introduca lo split (non setta ARGOS_DB_PATH — verificato; controllare che non copi un DB dentro release/).
5. SOLO DOPO: rieseguire GATE PACKET #9 v2 (invariato, sotto) → #9 VERIFIED 3/9. Setup WA session in `wa-intelligence/../wa-sender` + `.wwebjs_auth` (NON sotto releases → restart non perde QR).

---

## ▶ PROMPT DI APERTURA S226 — incolla/leggi questo, poi ESEGUI (non descrivere)

Sei CC che apre S226 su ARGOS. **Internalizza il contratto operativo R1–R4 + budget-rule (sotto) e applicalo**, non riassumerlo. Questa sessione fa **UNA cosa** sul percorso canonico `scrape→CoVe→PDF→WA→reply→sign→paid`; finché **C-E2E-ZERO è OPEN, VIETATO aprire file/feature fuori dal percorso** (R2).

Lo stato: anello #9 (HITL guard, commit `f63a1ee`) è **PENDING-GATE non DONE** — code-verified, MAI eseguito a runtime; il fix è su MacBook, **iMac gira la versione vecchia**. VERIFIED 2/9.

**Formato gate (vincolo #1b):** #9 → `TERMINAL_FACT = "msg fisicamente arrivato (o NON arrivato) sulla SIM TEST_FOUNDER nello scenario corretto"` · `BLOCKED-ON = Luke fisico sul gate`. È irraggiungibile-in-sessione → **NON ri-validarlo staticamente** (py_compile/simulazione = vietato come prova di chiusura). L'unico lavoro lecito = **renderlo raggiungibile** (P0 deploy + P1 runtime + packet pronto) o escalare. Stessa firma di C-SAN-001/C-E2E-ZERO che si avvitavano: non ricaderci.

**Esegui in quest'ordine, una cosa alla volta, fermandoti se un gate non passa:**
1. **C-WA-RESTART-001, time-boxed 1 sessione** (delega `devops-automator`). Criterio misurabile: "stabile" = 0 restart non-pianificati in 6h. Se la root-cause non emerge nel time-box → **fallback = window-integrity check** (leggi `restart_time` da `pm2 jlist` PRE/POST finestra test; se cambia → VOID+retry). NON inseguire la root-cause a oltranza (anti S159/S166).
2. **P0 — deploy `f63a1ee` su iMac** (`devops-automator`, rsync atomico + healthcheck). Senza, testi il bug non la fix.
3. **P1 — verifica runtime su iMac**: quale DB ospita `pending_replies` · un inbound da TEST_FOUNDER genera davvero riga `approved=NULL` · `/approva` accettato come testo. (R1: esecuzione reale, non py_compile.)
4. **Consegna il GATE PACKET v2 a Luke** (sotto) ed esegui il gate fisico su TEST_FOUNDER 393314928901.

**Verità di PASS (R4): `sent` è TAINTED** → la verità primaria dello Scenario A è "msg fisicamente arrivato sulla SIM" + log `[SENT]`; `sent=1` è solo conferma attesa. Divergenza (msg arrivato ma sent=0) = **finding** (latent bug storico vivo, aggancia S224-1), NON fail del guard.

**Condizione di chiusura S226 (budget-rule):** o #9 → **VERIFIED 3/9** (gate fisico passato + Luke "soddisfatto"), o handoff `PENDING-GATE` con packet già pronto + tag `UNVERIFIED-RUNTIME` su ciò che non hai provato a runtime. **Mai chiusura silenziosa al budget come `f63a1ee`.** Aggiorna QUESTO file (`.manual.md`, il hook auto-close NON lo clobbera) a fine sessione.

---

## DIAGNOSI (condivisa, ancorata ai dati) — il meta-bug è la CONDIZIONE DI CHIUSURA
~130 sessioni (S94→S225), superficie enorme, **E2E integrato = 0**, **VERIFIED 2/9** anelli, e un campo
di stato auto-riportato (`sent` sul path Telegram) si è rivelato **falso**. Pattern reale: ottimismo in
build-mode → audit reattivo che bonifica. La bonifica è ottima ma è governance, non prevenzione.
Tre problemi: (1) costruisce componenti, non chiude la catena; (2) chiude al limite di budget non di
verifica (es. `f63a1ee`: fix di un path verificato-rotto, committato senza ri-review per "chiusura budget");
(3) verifica lo strato sbagliato (py_compile/simulazione, non runtime) → il bug quoting `cmd_approva`
ha tenuto `UPDATE sent=1` MAI eseguita per tempo ignoto, runtime silenziosamente rotto.

## 5 REGOLE OPERATIVE (estensione, NON sostituzione dei meccanismi che già funzionano)
Tieni: evidence path:riga su ogni claim · separazione code-verified vs E2E reale · scope-fence per sessione · self-audit con de-idratazione overclaim.

- **R1 — Chiusura a due binari.**
  • *Runtime-verificabile* (lo provi da solo): DONE solo dopo **esecuzione reale del path** (output reale, non "compila"/simulazione).
  • *Human-gated* (HITL / E2E founder / dealer reale): **MAI VERIFIED**. Commit `PENDING-GATE` + produci **GATE PACKET** pronto (comando esatto, scenario A/B, durata, cosa osservare, criterio pass) così Luke chiude in <10 min. La latenza del gate umano è il vero collo di C-E2E-ZERO: riducila preparando il packet, non aspettando.
- **R2 — Catena prima della superficie.** Percorso canonico unico: `scrape → CoVe → PDF → WA → reply → sign → paid`. Finché C-E2E-ZERO è OPEN: VIETATO aprire file/feature fuori dal percorso. Ogni sessione muove UN anello verso VERIFIED o consolida una fondamenta che lo blocca (R3). Niente espansione laterale (anti S159/S166).
- **R3 — Fondamenta = prerequisito, non feature.** Prima dell'E2E reale: (a) DB autoritativo unico (C-DB-SPLIT-001 + C-DB-ENV-001); (b) daemon stabile (C-WA-RESTART-001). **Time-box obbligatorio** (vedi sotto) o R3 diventa il buco-senza-fondo che vuole prevenire.
- **R4 — Niente stato su dato non riconciliato.** Dopo un bug che corrompe un campo, quel campo è **TAINTED** finché non riconcili. Concreto: `sent` su path TG inaffidabile → NON usarlo come verità. Reconcile = backlog **S224-1**.
- **Budget-rule (il meta-bug).** Se il context finisce PRIMA della verifica runtime R1: NON committare come DONE. Commit su branch + tag `UNVERIFIED-RUNTIME` + handoff dichiara "manca verifica runtime: <cosa>". Mai più una chiusura silenziosa al budget come `f63a1ee`.

## STATO ANELLO #9 (HITL guard) — riclassificato R1
**PENDING-GATE, non DONE.** `f63a1ee` è *code-verified only* (py_compile + simulazione). **VERIFIED resta 2/9** (#1, #6). Sale a 3/9 solo a gate fisico passato. Il fix è su MacBook; **l'iMac gira la versione vecchia** → senza deploy (P0) testi il bug, non la fix.

Comando reale (`wa-intelligence/telegram-handler.py:10-12,171-347`): `/approva <reply_id>`, `/rifiuta <reply_id>`.
Sleep anti-ban **random 90–720s** (`SLEEP_MIN,SLEEP_MAX = 90,720`, riga 52 — NON 90s fisso). Segnale indipendente da `sent`: log `[SENT]`/`[ERROR] rc=`/`[ABORT]` dal send_script (righe 262-277).

## GATE PACKET #9 — v2 (corretto: sent TAINTED + window-integrity)
```
PRE (CC): P0 deploy f63a1ee su iMac (rsync atomico + healthcheck — via devops-automator)
          P1 verifica runtime su iMac: DB di pending_replies · inbound TEST_FOUNDER genera
             riga approved=NULL · /approva accettato come testo (non solo inline button)

SEED (Luke ~1min): WA da SIM TEST_FOUNDER 393314928901 → numero ARGOS Business → annota reply_id da notifica TG

SCENARIO A — invio consentito:
  pm2 jlist → annota restart_time PRE
  /approva <reply_id> · attendi 90–720s
  PASS A (verità primaria) = msg ARRIVATO sulla SIM (osservazione Luke) + log [SENT]
  CONFERMA attesa (tertiaria, TAINTED, non decide) = sent=1
  DIVERGENZA (msg arrivato MA sent=0) = NON FAIL del guard → prova viva del latent bug storico → FINDING, aggancia S224-1
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry

SCENARIO B — revoca durante sleep (nuovo reply_id2):
  pm2 jlist → restart_time PRE
  /approva <reply_id2> · SUBITO (<60s) /rifiuta <reply_id2>
  PASS B = NESSUN msg sulla SIM + log [ABORT] + sent=0 + approved=0
  pm2 jlist → restart_time POST; se ≠ PRE → VOID, retry (NON interpretare "no msg" come PASS)

EVIDENCE: osservazione fisica Luke (A+B) | log daemon [SENT]/[ABORT]/[ERROR] |
          SELECT id,approved,sent FROM pending_replies WHERE id IN (r1,r2) | restart_time PRE/POST
CHIUSURA: Luke "soddisfatto" → #9 DONE, VERIFIED 3/9.
```
Nota window-integrity: il gate **non** richiede C-WA-RESTART chiuso, richiede di SAPERE se il daemon è ripartito nei ~12 min del test. Il check `restart_time` PRE/POST (`pm2 jlist` → confermare nome campo sulla versione iMac) rende lo Scenario B interpretabile senza prima stabilizzare del tutto il daemon.

## ORDINE ESECUZIONE S226 (una cosa alla volta, sul percorso canonico)
1. **C-WA-RESTART-001 — time-boxed**: "daemon stabile" = 0 restart non-pianificati in finestra 6h (criterio misurabile, NON "root-cause trovata"). Root-cause time-box = 1 sessione; se non emerge → fallback = window-integrity check nel packet (sufficiente a rendere B interpretabile). Foundation completa resta task R3, **fuori dal critical-path del gate**.
2. **P0 deploy `f63a1ee`** su iMac (devops-automator). NB: codice solo su MacBook ora.
3. **P1 verifica runtime** su iMac (i 3 punti del PRE).
4. **Consegna GATE PACKET v2 a Luke** ed esegui il gate.

## VINCOLI / NON TOCCARE
- TEST_FOUNDER 393314928901 prima di qualsiasi dealer reale. **Domenica = OFF Luke** (no scadenze domenicali).
- `image_sanitizer.py` + scope partner-unico (landing/Gemini/trasporto) **CONGELATO**. No deploy landing/PDF.
- Day 1 Stile Car blocker invarianti: C-SAN-001, **C-E2E-ZERO**, C-COMM-INTEL-001, C-GATE-FONTE-001.
- Fondi di verità: `PLAN.md` (carte C-DB-SPLIT:178, C-WA-RESTART:179, C-E2E-ZERO:182). DB iMac autoritativo = `~/Documents/app-antigravity-auto/dealer_network.sqlite`.

## BACKLOG (non scope S226 salvo R4)
- **[S224-1]** Reconcile path TG: quante righe `pending_replies` con `approved=1 AND sent=0` ma msg realmente inviato (dati `sent` storici inaffidabili). Prerequisito R4 per fidarsi di metriche di invio su path TG.
- Migrare path legacy multi-msg + Telegram al **bridge canonico** (single-writer S173) → elimina la classe di bug.
- Verifica anelli #2..#5, #7, #8 per salire VERIFIED oltre 3/9.
