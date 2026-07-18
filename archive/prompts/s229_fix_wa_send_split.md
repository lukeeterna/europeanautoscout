# S229 — fix C-WA-SEND-SPLIT poi gate #9

Leggi `.claude/NEXT_SESSION_PROMPT.manual.md` (sezione S228 in cima). Internalizza R1–R4 + budget-rule.
Stato: #9 **PENDING-GATE, BLOCKED-ON fix codice C-WA-SEND-SPLIT** (NON Luke fisico — SEED già raggiungibile). VERIFIED **2/9**.

**UNA cosa: chiudere C-WA-SEND-SPLIT, poi ri-eseguire gate #9.** Delega `devops-automator`.

**Root cause (verificata S228):** `/approva` (`telegram-handler.py:45-47`) spawna standalone `~/Documents/app-antigravity-auto/wa-sender/send_message.js` (CLIENT_ID `argos-business`) → cerca auth `~/.wwebjs_auth/session-argos-business` INESISTENTE. Daemon connesso usa `wa-intelligence/.wwebjs_auth`. Due client whatsapp-web.js → invio sempre fallito (`rc=1`, log `/tmp/argos-tg-send.log`).

**Fix:** instradare invio path-TG via daemon connesso (bridge single-writer S173) — POST `:9191/send` + X-API-Key. SCARTA secondo client standalone (LocalAuth lock).

**Ordine:**
1. Fix su MacBook + code-review.
2. Deploy iMac (rsync atomico + healthcheck).
3. GATE PACKET #9 v2: SEED Luke SIM TEST_FOUNDER 39<TEST_FOUNDER_NUM> → `/approva` → **Scenario A** = msg ARRIVA + log `[SENT]` (sent TAINTED). Window-integrity via `uptime_sec` PRE/POST (`curl :9191/status` — `pm2` NON in PATH ssh).
4. **Scenario B** (mai provato): `/approva` poi subito `/rifiuta` → nessun msg + `[ABORT]` + `approved=0`.

**Chiusura:** #9 → VERIFIED 3/9 (Luke "soddisfatto") o handoff PENDING-GATE.
**Vincoli:** Domenica OFF Luke. `image_sanitizer.py` + scope partner-unico CONGELATI.
