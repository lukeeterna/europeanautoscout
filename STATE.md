# STATE.md — ARGOS · unico source-of-truth di stato

> **Questo è l'UNICO file che risponde a "a che punto siamo + cosa faccio dopo".**
> La tabella anelli sotto è **GENERATA** da `state/refresh.sh` (non scrivibile a mano).
> "VERIFIED" = check passato in QUESTA sessione, non una frase digitata.
> Stato cross-sessione (memorie) → `~/.claude/projects/.../memory/MEMORY.md` (scopo diverso).
> Piano dettagliato → `PLAN.md` · Problemi parcheggiati → `BACKLOG.md`.
> Aggiornato: **S243 · 2026-06-08**

---

## 1. Anelli E2E — mappa autoritativa (GENERATA, non editare a mano)

Rigenera con: `bash state/refresh.sh <SESSION_ID>` · sorgente: `state/rings.json`

<!-- GENERATED:rings:start -->
<!-- NON modificare a mano: rigenerato da `bash state/refresh.sh`. VERIFIED = check passato in QUESTA sessione. -->
_Rigenerato 2026-06-08T07:32:27Z · sessione `S244`_

| # | Anello | Stato | Tier | Check | Ultima sessione |
|---|--------|-------|------|-------|-----------------|
| 1 | invio Day1 WA | UNVERIFIED | full | — | — |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke | `python3 tools/test_ambra_5scenarios.py` | S244 |
| 9A | approve -> send | VERIFIED | smoke | `python3 tools/tests/test_approve_reply_runtime.py` | S244 |
| 9B | reject -> abort | UNVERIFIED | full | — | — |
| 5 | generazione dossier PDF | VERIFIED | smoke | `python3 tools/tests/test_dossier_hitl_smoke.py` | S244 |
| 6-7 | approve HITL dossier -> invio PDF al dealer | UNVERIFIED | full | — | — |
| 8 | contract -> sign_url | BLOCKED | full | freeze: sign_url firmato dal dealer reale (HITL fisico Luke o terzo) — fatto esterno non raggiungibile in-sessione | — |
<!-- GENERATED:rings:end -->

Legenda: **VERIFIED** = check PASS in questa sessione · **STALE** = PASS ma in sessione
precedente (riesegui refresh) · **UNVERIFIED** = nessun check eseguibile in-sessione (o non
ancora scritto) · **FAIL** = check fallito = gap reale · **BLOCKED** = freeze su fatto esterno.

Pipeline core: `Scraper (28 portali) → CoVe Engine (scoring+fraud) → Opportunity Selection → Dealer Dossier`.

---

## 2. Task corrente (S244)

**Consolidamento substrato di stato** — sequenza verdetto Claude AI (`state/s242_claude_ai_verdict.md`).
Step 4 CHIUSO: smoke `tools/tests/test_dossier_hitl_smoke.py` scritto + eseguito (1/1 PASS).
Ring `5-6-7` SPLITTATO onestamente in **5** (PDF gen, smoke VERIFIED — `generate_dossier_from_data`
produce PDF reale su disco) e **6-7** (gate HITL + invio PDF WA, tier full → E2E iMac/TEST_FOUNDER).
Anello 6 (gate HITL `app.py`) è fastapi-coupled: gira solo su iMac/CI; su MacBook = SKIP non-gating.

Restano (verdetto Claude AI): step 6 (gate A–C + `.harness/`), step 7 (redirect auto-close hook),
step 8 (archivio doc legacy), step 9 (Gate E azioni high-stakes).

---

## 3. Prossimi 3 step

1. **Step 6** — Gate A–C + `.harness/`: PreToolUse hook che (a) rifiuta scrittura manuale dentro
   `<!-- GENERATED:rings -->`, (b) rifiuta token VERIFIED in file stato per anello non-PASS,
   (c) rifiuta edit a file-hook. SessionStart hook esegue `refresh.sh` prima di CC. Checkpoint git prima.
2. **Step 7** — redirect `~/.claude/hooks/global_session_end.sh` → breadcrumb = pointer a STATE.md,
   ZERO ri-asserzione status. NON disattivarlo (memoria `feedback_keep_autoclose_hook_context_control`).
3. **Step 8** — archivio `prompts/` (58) + `HANDOFF*` + `.claude/NEXT_SESSION_PROMPT` (backup verificato
   Rule 1d) → 1 riga pointer in STATE.md → commit checkpoint reversibile.

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

> **STATO REALE (S243)**: archivio NON ancora creato (step 8 pendente). Handoff/prompt legacy
> ancora in `prompts/` (58 file), `HANDOFF*.md`, `.claude/NEXT_SESSION_PROMPT.md`.
> Auto-close hook `~/.claude/hooks/global_session_end.sh` **ATTIVO** (NON disattivato): da
> reindirizzare a breadcrumb-pointer (step 7), non spegnere.
