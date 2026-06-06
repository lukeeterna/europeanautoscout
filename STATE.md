# STATE.md — ARGOS · unico source-of-truth di stato

> **Questo è l'UNICO file che risponde a "a che punto siamo + cosa faccio dopo".**
> Non creare HANDOFF/NEXT_SESSION/prompt paralleli: aggiorna QUESTO file a fine sessione.
> Stato cross-sessione (memorie) → `~/.claude/projects/.../memory/MEMORY.md` (scopo diverso).
> Piano dettagliato → `PLAN.md` · Problemi parcheggiati → `BACKLOG.md` (NON duplicare lo stato lì).
> Aggiornato: **S242 · 2026-06-06**

---

## 1. Anelli E2E — mappa autoritativa

| #   | Anello                              | Stato                  |
|-----|-------------------------------------|------------------------|
| 1   | invio Day1 WA                       | VERIFIED               |
| 2   | classifier intent (AMBRA)           | VERIFIED (S202)        |
| 9A  | approve → send                      | VERIFIED (S230)        |
| 9B  | reject → abort                      | VERIFIED (S241)        |
| 5/6/7 | dossier → approve → invio PDF     | PARZIALI ← focus next  |
| 8   | contract → sign_url                 | BLOCKED (Luke/terzo)   |

Pipeline core: `Scraper (28 portali) → CoVe Engine (scoring+fraud) → Opportunity Selection → Dealer Dossier`.

---

## 2. Task corrente (S242)

**PRIORITÀ #0 (in corso)**: consolidamento file di stato — questo STATE.md è il risultato.
Done quando: STATE.md unico, handoff/prompt obsoleti archiviati, hook auto-close OFF per ARGOS.

Dopo il consolidamento → anelli **5/6/7** (dossier → approve HITL → invio PDF al dealer).

---

## 3. Prossimi 3 step

1. **Verificare su CODICE** (non doc) lo stato reale degli anelli 5/6/7: generazione dossier → approvazione HITL → invio PDF. Punto di partenza file critici sotto.
2. Identificare il primo gap concreto della catena 5/6/7 e chiuderlo con E2E su **TEST_FOUNDER 393314928901** (mai dealer reale prima).
3. Solo a 5/6/7 VERIFIED → valutare anello #8 (resta BLOCKED su Luke fisico/terzo).

---

## 4. Vincoli sempre attivi

- **TEST_FOUNDER 393314928901** prima di QUALSIASI dealer reale. Max 1 Day1/numero.
- `image_sanitizer` (D-32) e **landing CONGELATI** finché anelli E2E non risalgono.
- Clock skew iMac: DB `created_at` ~−2h vs log wa-daemon (non è un bug).
- Deploy 2-path. Per OGNI path iMac consultare memoria `reference_imac_deploy_paths.md`.
- DB canonico `pending_replies` = `~/Documents/app-antigravity-auto/dealer_network.sqlite` (ROOT, via symlink shared).
- Token Telegram in `current/wa-intelligence/.env` var `ARGOS_TELEGRAM_TOKEN` (MAI stampare).

---

## 5. File critici (punto di partenza, NON ricostruire a memoria)

- CoVe Engine: `src/cove/cove_engine_v4.py` (NON modificare — solo leggere/invocare)
- Scrapers: `tools/scrapers/` · On-demand: `tools/on_demand_runner.py`
- PDF dossier: `tools/scripts/pdf_generator_enterprise.py`
- Response analyzer (AMBRA): `wa-intelligence/response-analyzer.py`
- WA daemon: `wa-intelligence/wa-daemon.js` · Dashboard: `wa-intelligence/dashboard/app.py`
- Bridge HITL Telegram: invio via daemon (bridge S173). Bot tg pid sano (S241).

---

## 6. Note di stato pulito (da S241)

- `reply_94678456`: `approved=0, sent=0` = reject completato, SAFE.
- `reply_f4a419e8`: `approved=NULL` = HOLD mai consumato, SAFE.
- Bot tg SANO (getMe ok, /help processato; `409` = vivo, non token-revocato). Residuo ~1% `read timeout` = rumore rete iMac 2012, impatto reale zero (Telegram ri-consegna). NON applicare patch timeout speculative (refutate S240).
- **Lezione delega (REGOLA #0)**: agent-ops in S240 allucinò `409→token revocato`. Verificare SEMPRE il fatto terminale (getMe/probe/log reale) prima di accettare il verdetto di un subagent.

---

## 7. Archivio storico

Handoff/prompt pre-S242 in `archive/` (HANDOFF*, AUDIT_E2E, 58 prompts/, NEXT_SESSION_PROMPT*).
Consultabili per contesto storico; NON sono stato vivo. L'hook auto-close è disattivato per ARGOS (vedi guard in `~/.claude/hooks/global_session_end.sh`).
