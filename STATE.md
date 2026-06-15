# STATE.md — ARGOS · unico source-of-truth di stato

> **Questo è l'UNICO file che risponde a "a che punto siamo + cosa faccio dopo".**
> La tabella anelli sotto è **GENERATA** da `state/refresh.sh` (non scrivibile a mano).
> "VERIFIED" = check passato in QUESTA sessione, non una frase digitata.
> Stato cross-sessione (memorie) → `~/.claude/projects/.../memory/MEMORY.md` (scopo diverso).
> Piano dettagliato → `PLAN.md` · Problemi parcheggiati → `BACKLOG.md`.
> Aggiornato: **S245 · 2026-06-08**

> **S263 · PROBE pool IT = ESITO C (inconclusivo sul mercato, conclusivo sullo scraper).**
> Report: `.claude/REPORT_S263.md`. Anello PDF CHIUSO in S262 (commit 9fb7824).
> Il muro NON è il mercato: lo scraper AS24.it via curl_cffi vede SOLO pagina-1 SSR (~19
> listing); il path Selenium-profondo esiste (`autoscout_scraper.py:1250`) ma è gated su
> zero-data → non scatta. A vs B INDECIDIBILE finché lo scraper non pagina oltre p.1.
> Segnale che sopravvive: config esatte (L0/L1) = 0 in tutte le 4 famiglie, solo L3 pesca 1-2
> → preview Esito misto (M340 = 0 ovunque). min_n NON ratificato (distribuzione corrotta dal muro).
> S264 proposto: de-gate fetch profondo IT (cambio poche righe, NO infra) → ri-eseguire probe.

---

## 1. Anelli E2E — mappa autoritativa (GENERATA, non editare a mano)

Rigenera con: `bash state/refresh.sh <SESSION_ID>` · sorgente: `state/rings.json`

<!-- GENERATED:rings:start -->
<!-- NON modificare a mano: rigenerato da `bash state/refresh.sh`. VERIFIED = check passato in QUESTA sessione. -->
_Rigenerato 2026-06-15T13:47:30Z · sessione `eb1e116f-05c9-45ba-aee8-e6d33c2d83e9`_

| # | Anello | Stato | Tier | Check | Ultima sessione |
|---|--------|-------|------|-------|-----------------|
| 1 | invio Day1 WA | UNVERIFIED | full | — | — |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke | `python3 tools/test_ambra_5scenarios.py` | eb1e116f-05c9-45ba-aee8-e6d33c2d83e9 |
| 9A | approve -> send | VERIFIED | smoke | `python3 tools/tests/test_approve_reply_runtime.py` | eb1e116f-05c9-45ba-aee8-e6d33c2d83e9 |
| 9B | reject -> abort | UNVERIFIED | full | — | — |
| 5 | generazione dossier PDF | VERIFIED | smoke | `python3 tools/tests/test_dossier_hitl_smoke.py` | eb1e116f-05c9-45ba-aee8-e6d33c2d83e9 |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED | full | — | — |
| 8 | contract -> sign_url | BLOCKED | full | freeze: sign_url firmato dal dealer reale (HITL fisico Luke o terzo) — fatto esterno non raggiungibile in-sessione | — |
<!-- GENERATED:rings:end -->

Legenda: **VERIFIED** = check PASS in questa sessione · **STALE** = PASS ma in sessione
precedente (riesegui refresh) · **UNVERIFIED** = nessun check eseguibile in-sessione (o non
ancora scritto) · **FAIL** = check fallito = gap reale · **BLOCKED** = freeze su fatto esterno.

Pipeline core: `Scraper (28 portali) → CoVe Engine (scoring+fraud) → Opportunity Selection → Dealer Dossier`.

---

## 2. Task corrente (S246)

**Consolidamento substrato di stato** — sequenza verdetto Claude AI (`state/s242_claude_ai_verdict.md`).
**Step 7 CHIUSO (commit d8f8018)**: auto-close hook `~/.claude/hooks/global_session_end.sh`
REINDIRIZZATO — su repo con STATE.md genera breadcrumb zero-status (pointer a STATE.md), non più
prosa di stato (doc #8). Auto-commit safety-net invariato; ramo legacy preservato per repo senza
STATE.md (FLUXION/Guardian). Backup Rule 1d `global_session_end.sh.bak-S246-*`. Done-condition
verificata: dry-run su repo ARGOS produce breadcrumb.
**Step 8 CHIUSO (commit d8f8018)**: `git mv` 58 prompt + 2 HANDOFF → `archive/` (history preservata,
reversibile, revert testato). STATE.md sez.7 = pointer archivio.
**(S245) Step 6 CHIUSO (commit d97d353)**: `.harness/state_guard.py` Gate A–D attivo, 11 test PASS.
**Step 9 CHIUSO (S247)**: `.harness/gate_e.py` = PreToolUse hook (matcher `Bash|Write|Edit|MultiEdit`,
registrato in `.claude/settings.json`). CLASSE azioni high-stakes: `outreach_real` (WA a numero ≠
TEST_FOUNDER), `archive_doc` (git mv/rm → archive/), `overwrite_sot` (CLAUDE.md/MEMORY.md/DECISIONS.md/
PLAN.md/*.db via Write/Edit/Bash-lossy — chiude il gap Bash di state_guard, es. `sed -i STATE.md`),
`disable_hook` (settings.json/hook globali/file-harness). Meccanica: BLOCCA → scrive
`pending_review/<slug>.md` (packet precompilato) → CC fermo finché Luke non incolla verdetto esterno +
`! python3 .harness/gate_e.py approve <slug>` (token one-shot consumato all'uso; CC non può auto-approvare).
Done-condition VERIFICATA E2E: deny+packet, retry deny, approve→allow, consumo→deny, self-approve→deny.
selftest 9/9 PASS. Hook ATTIVO LIVE (CC rilegge settings.json a caldo): ha bloccato il proprio
commit di install = prova in produzione. Verdetto esterno Claude AI S247: APPROVE (atterra verificato,
refinement dopo con stessa disciplina verify-then-land).

Resta (verdetto Claude AI): 6-7 E2E (gate HITL iMac + invio PDF TEST_FOUNDER 393314928901). È la prima
azione che innescherà Gate E (classe `outreach_real`).

---

## 3. Prossimi step (S249 · coverage-check ESEGUITO)

> **PRIORITÀ S250 (specchio strategico, second-opinion S249 + decisione Luke).**
> Arco S245→S273 = motore + control-plane induriti, ma **ZERO dealer contattati**. Il vincolo
> legante NON è tecnico: è il GATE LEGALE/PERSONA (sotto), archiviato BLOCKED-ON-LUKE di sessione
> in sessione. Motore pronto per un primo dossier, control-plane pronto per invio human-initiated.
> **#1 = chiudere il gate legale/persona (azione LUKE)**, non altra hardening. Poi 6-7 E2E.
> **VINCOLO LUKE (duro): "il metodo WA non si tocca"** — canale, sequenza human-first, persona
> Luca Ferretti sono DECISI. Il gate legale NON è "sostituire WA": è il parere legale sulla base
> giuridica del primo contatto + la decisione su persona/trasparenza ATTORNO al metodo.
>
> **ADD-1 tripwire `/send` — adottare lo SPIRITO, NON la lettera.** "Require `approved_ts` su /send"
> come hard-assert ROMPE il Day-1 human-initiated: gli script Day-1 fanno POST /send diretto, NON
> hanno approved_ts (autorizzazione = invocazione umana + precheck24h). Versione sicura = **log-loud
> NON-bloccante** che marca `direct-/send senza approved_ts` distinto da `bridge-approvato`
> nell'audit (1 riga di log; l'alert TG per-invio già esiste, wa-daemon.js:1318). Hard-assert +
> riprogetto 2-path = fase hardening completa, gated su autonomia. NON ora.

1. **Gate E refinement — CHIUSO** (verificato S249, selftest 33/33 PASS). Raffinamento S248 nel codice:
   `lossy_operands` su operandi reali, `strip_git_invocations` (no FP su commit-message), `*.db`
   ristretto ai 3 DB SoT. I FP su prosa commit → allow sono coperti dai casi selftest.
2. **COVERAGE-CHECK — ESEGUITO S249. Esito: Gate E copre la sua mansione, MA non è il breaker di
   produzione.** Due threat-model:
   - **CC-sbadataggine (CC invia in-sessione)** = mansione dichiarata di Gate E → **COPERTO**. Signatures
     (`:9191/send`, `tools/outreach/`, `send_message.js`, `/send-doc`, `/send-multi`, `sendMessage(`) +
     discriminazione telefono. I 4 script Day-1 reali cadono sotto le signatures.
   - **Runtime daemon (AMBRA in produzione)** = Gate E **strutturalmente assente, by design**
     (docstring gate_e.py righe 33-34: path non-shell fuori da classify_bash). Gate E è PreToolUse di CC,
     non vede il processo Node in esecuzione.
   - **BUCO REALE localizzato**: i 4 script Day-1 chiamano `/send` (wa-daemon.js:1269) che **NON ha il
     gate `approved_ts`** — solo il poller bridge (342) ce l'ha. La garanzia HITL vive nel CALLER, non
     nell'endpoint. Oggi caller=CC/Luke → coperto. Un processo non-CC (scheduler/PM2/cron) su `/send`
     bypassa ENTRAMBI (Gate E è CC-only + `/send` salta il bridge) → invio reale non sorvegliato.
   - **AZIONE gated PRIMA di alzare autonomia-invio (oggi già bloccata da ≥10 CLOSED_WON)**: far
     rispettare `approved_ts` a `/send` stesso, o instradare ogni invio reale dentro il bridge
     (single-writer vero). NON blocca 6-7 (TEST_FOUNDER + CC-initiated).
3. **6-7 E2E** — gate HITL su iMac (fastapi presente) + invio PDF su TEST_FOUNDER 393314928901
   (mai dealer reale). Anello 6 fastapi-coupled: smoke-abile solo iMac/CI. Prima azione che innesca
   **Gate E** (classe `outreach_real`): invio BLOCCATO + packet, si procede solo dopo verdetto esterno +
   `approve <slug>`. Coverage-check (item 2) ESEGUITO → sbloccato.

### GATE LEGALE/TRASPARENZA (sopra Gate E — BLOCKED-ON-LUKE, blocca invio a dealer REALE, NON la E2E test)
Nessun invio a un dealer **reale** (anelli #1, 6-7 verso numero ≠ TEST_FOUNDER) finché Luke (autorità su
irreversibile + verifica con professionista legale — CC non è un legale) non chiude:
 (a) **liceità canale primo contatto**: WA outbound a freddo in IT = alto rischio GDPR (regola-base =
     consenso; legittimo interesse marketing va usato con parsimonia + balancing test documentato —
     Garante/Federprivacy 2026 verificato S249). Lecito come follow-up di lead inbound / rapporto
     preesistente / richiesta esplicita. NON "illegale a prescindere", ma NON assumibile come lecito.
 (b) **trasparenza AMBRA**: l'agente NON deve negare di essere automatico se interrogato (rimuovere
     eventuale istruzione KB "nega di essere un bot"). Trasparenza, oltre che consenso.
La E2E contro TEST_FOUNDER 393314928901 procede comunque (non è un dealer).

---

## 4. Vincoli sempre attivi

- **TEST_FOUNDER 393314928901** prima di QUALSIASI dealer reale. Max 1 Day1/numero.
- `image_sanitizer` (D-32) e **landing CONGELATI** finché anelli E2E non risalgono.
- Clock skew iMac: DB `created_at` ~−2h vs log wa-daemon (non è un bug).
- Deploy 2-path. Per OGNI path iMac consultare memoria `reference_imac_deploy_paths.md`.
- DB canonico `pending_replies` = `~/Documents/app-antigravity-auto/dealer_network.sqlite` (ROOT, via symlink shared).
- Token Telegram in `current/wa-intelligence/.env` var `ARGOS_TELEGRAM_TOKEN` (MAI stampare).
- `argos.py` NON esiste (CLAUDE.md `python3 argos.py test` è stale). Test reali: `tools/test_*.py`, `tools/tests/`.

---

## 5. File critici (punto di partenza, NON ricostruire a memoria)

- CoVe Engine: `src/cove/cove_engine_v4.py` (NON modificare — solo leggere/invocare)
- Scrapers: `tools/scrapers/` · On-demand: `tools/on_demand_runner.py`
- PDF dossier: `tools/scripts/pdf_generator_enterprise.py`
- Response analyzer (AMBRA): `wa-intelligence/response-analyzer.py`
- WA daemon: `wa-intelligence/wa-daemon.js` · Dashboard: `wa-intelligence/dashboard/app.py`
- Bridge HITL Telegram: invio via daemon (bridge S173).
- Substrato stato: `state/rings.json` (sorgente) · `state/refresh.sh` (generatore).

---

## 6. Note di stato pulito (da S241)

- `reply_94678456`: `approved=0, sent=0` = reject completato, SAFE.
- `reply_f4a419e8`: `approved=NULL` = HOLD mai consumato, SAFE.
- Bot tg SANO (getMe ok, /help processato; `409` = vivo, non token-revocato). Residuo ~1% `read timeout` = rumore rete iMac 2012, impatto reale zero (Telegram ri-consegna). NON applicare patch timeout speculative (refutate S240).
- **Lezione delega (REGOLA #0)**: agent-ops in S240 allucinò `409→token revocato`. Verificare SEMPRE il fatto terminale (getMe/probe/log reale) prima di accettare il verdetto di un subagent.

---

## 7. Archivio storico

> Doc legacy di stato (58 prompt + 2 HANDOFF) archiviati in **`archive/`** (S246, `git mv` →
> history preservata, ripristinabile con `git revert` o `git mv` inverso). NON sono più
> source-of-truth: lo stato vive solo qui in STATE.md + `state/rings.json`.
> Auto-close hook `~/.claude/hooks/global_session_end.sh` **ATTIVO + REINDIRIZZATO** (S246 step 7):
> su repo con STATE.md genera breadcrumb zero-status (pointer a STATE.md), NON più prosa di stato.
> Auto-commit safety-net invariato. Backup pre-modifica: `global_session_end.sh.bak-S246-*`.
> Gate A–C (`.harness/state_guard.py`) **ATTIVO** (commit d97d353): per modificare guard/generatori
> o il blocco GENERATED serve `ARGOS_HARNESS_UNLOCK=1`.
