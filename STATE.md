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
_Rigenerato 2026-06-08T07:02:19Z · sessione `S243`_

| # | Anello | Stato | Tier | Check | Ultima sessione |
|---|--------|-------|------|-------|-----------------|
| 1 | invio Day1 WA | UNVERIFIED | full | — | — |
| 2 | classifier intent (AMBRA) | VERIFIED | smoke | `python3 tools/test_ambra_5scenarios.py` | S243 |
| 9A | approve -> send | VERIFIED | smoke | `python3 tools/tests/test_approve_reply_runtime.py` | S243 |
| 9B | reject -> abort | UNVERIFIED | full | — | — |
| 5-6-7 | dossier -> approve HITL -> invio PDF | UNVERIFIED | smoke | — | — |
| 8 | contract -> sign_url | BLOCKED | full | freeze: sign_url firmato dal dealer reale (HITL fisico Luke o terzo) — fatto esterno non raggiungibile in-sessione | — |
<!-- GENERATED:rings:end -->

Legenda: **VERIFIED** = check PASS in questa sessione · **STALE** = PASS ma in sessione
precedente (riesegui refresh) · **UNVERIFIED** = nessun check eseguibile in-sessione (o non
ancora scritto) · **FAIL** = check fallito = gap reale · **BLOCKED** = freeze su fatto esterno.

Pipeline core: `Scraper (28 portali) → CoVe Engine (scoring+fraud) → Opportunity Selection → Dealer Dossier`.

---

## 2. Task corrente (S243)

**Consolidamento substrato di stato** — sequenza verdetto Claude AI (`/tmp/s242_claude_ai_verdict.md`).
Substrato (rings.json + refresh.sh + render) costruito. Restano: guadagnare VERIFIED su 5/6/7
(step 4), gate A–C + .harness (step 6), redirect hook (step 7), archivio 7 doc (step 8), Gate E (step 9).

Dopo il consolidamento → anelli **5/6/7** (dossier → approve HITL → invio PDF al dealer).

---

## 3. Prossimi 3 step

1. **Step 4** — scrivere lo smoke check per 5/6/7, eseguirlo via refresh, chiudere i rossi con E2E
   su **TEST_FOUNDER 393314928901** (mai dealer reale prima).
2. **Step 6–7** — gate A–C + protezione `.harness/` + redirect auto-close hook (checkpoint git prima).
3. **Step 8** — archivio 7 doc legacy (backup verificato Rule 1d) + commit checkpoint reversibile.

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
