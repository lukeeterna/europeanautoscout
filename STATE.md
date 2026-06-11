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
_Rigenerato 2026-06-11T16:29:37Z · sessione `auto-20260611T182936Z`_

| # | Anello | Stato | Tier | Check | Ultima sessione |
|---|--------|-------|------|-------|-----------------|
| 1 | invio Day1 WA | UNVERIFIED | full | — | — |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke | `python3 tools/test_ambra_5scenarios.py` | auto-20260611T182936Z |
| 9A | approve -> send | VERIFIED | smoke | `python3 tools/tests/test_approve_reply_runtime.py` | auto-20260611T182936Z |
| 9B | reject -> abort | UNVERIFIED | full | — | — |
| 5 | generazione dossier PDF | VERIFIED | smoke | `python3 tools/tests/test_dossier_hitl_smoke.py` | auto-20260611T182936Z |
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

## 3. Prossimi step (S248)

1. **Gate E refinement — PROSSIMO work-item gated, NON "BACKLOG un giorno"** (verdetto Claude AI S247).
   Far scattare il gate SOLO sugli operandi reali (numero destinatario, path-file effettivi, edit reale
   del file-hook), MAI sul testo del commit message — il match sulla prosa è un errore di categoria
   (FP illimitati, zero veri-positivi extra). + restringere `*.db` al path del DB source-of-truth.
   + `ARGOS_HARNESS_UNLOCK=1` come escape manutenzione di gate_e + `gate_e.py` in PROTECTED_FILES di
   state_guard. Disciplina: edit → selftest+E2E → land (verify-then-land). Trigger: FP sostenuto sposta
   il decadimento da auto-disciplina-AI a vigilanza-umana = stesso failure-mode che l'apparato impedisce.
2. **COVERAGE-CHECK (production-blocking per classe `outreach_real`, verdetto Claude AI S247)**: l'E2E
   ha verificato il blocco sul path-SHELL. PRIMA di alzare la soglia autonomia-invio (oggi già bloccata
   da regola ≥10 CLOSED_WON), CONFERMARE che Gate E intercetti il path-tool REALE con cui AMBRA invia in
   produzione. Se AMBRA manda via tool MCP/Python che bypassa il matcher-shell → breaker DECORATIVO sulla
   sua classe più critica = difetto strutturale (flip a REJECT). Non urgente oggi (autonomia già gated).
3. **6-7 E2E** — gate HITL su iMac (fastapi presente) + invio PDF su TEST_FOUNDER 393314928901
   (mai dealer reale). Anello 6 fastapi-coupled: smoke-abile solo iMac/CI. È la prima azione che
   innesca **Gate E** (classe `outreach_real`): l'invio verrà BLOCCATO + packet, si procede solo dopo
   verdetto esterno + `approve <slug>`. NB: fare DOPO il coverage-check (item 2).

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
