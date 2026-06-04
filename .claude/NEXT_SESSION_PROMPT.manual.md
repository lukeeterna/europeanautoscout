# S239 — Ripartenza

## ✅ S238 — ESITO (2026-06-04): "🔄 Rigenera" VERIFIED a runtime — root cause thinking-token trovata, fix A+B deployato, GATE FISICO PASSATO

### Gate fisico PASSATO (Luke "perfetto" 17:26)
- SEED dalla SIM TEST_FOUNDER → notifica TG con 3 bottoni (✅ 🚫 🔄) → tap 🔄 → **nuova reply COMPLETA arrivata** con keyboard.
- DB ROOT `pending_replies` `reply_3c270690`: `length(reply_text)=564`, finisce con `]}` + fence chiuso, firmata "Luca", `approved=NULL`, `sent=0`. **JSON COMPLETO** (vs il bug pre-fix a 65 char). 3 messaggi multi-bubble.
- Path ✅→SIM (split `/send-multi`) già VERIFIED da S230 (Scenario A), non ri-testato.

### Root cause CONFERMATA a runtime (chiamata live Gemini, NON assunta)
`gemini-2.5-flash` è un modello **reasoning** → i thinking-token consumavano tutto `maxOutputTokens:512` (`thoughtsTokenCount:487` / `candidatesTokenCount:21` → 21 token output → `finishReason:MAX_TOKENS`). Fix = `thinkingConfig:{thinkingBudget:0}` → `STOP`, output completo. **Il fix del vecchio handoff (solo Markdown su send()) era SBAGLIATO** — avrebbe consegnato JSON troncato. Bug isolato al rigenera: generazione normale usa `gemini-2.0-flash` (non-reasoning), nessun rischio. **Lezione riusabile**: ogni chiamata a modello Gemini 2.5+ con `maxOutputTokens` basso → mettere `thinkingBudget:0` o il thinking mangia il budget.

### FATTO (codice committato + deployato + verificato)
- **FIX A** `telegram-handler.py:519-523` — `generationConfig` con `maxOutputTokens:800, thinkingConfig:{thinkingBudget:0}`.
- **FIX B** `telegram-handler.py:140-178` — `send()` fallback Markdown→plain su HTTP 400 (preview con `{ [ "` rompeva Markdown). Firma invariata, `tg_post()` intatto.
- **cmd_approva** parsa `json.loads(reply_text)['messages']` → `/send-multi` (telegram-handler.py:297-311). Con JSON completo splitta le bubble, no JSON grezzo al dealer.
- **DEPLOY OK** su 2 path (release `releases/20260527_083951/wa-intelligence/` + ROOT), backup `.bak-pre-s238` (39255B), 3 md5 `aa1716b8eff984704923e3893e8754fb`, `PYCOMPILE_OK`, `argos-tg-bot` online, `argos-wa-daemon restart_time=50` invariato.
- Commit: `ae57e29` (telegram-handler.py fix) + `fe4ef18` (cmd_genera S237).

### NEXT (S239) — scegliere scope con Luke. Rigenera è CHIUSO. Candidati:
1. **Caveat minore da chiudere (~5 min)**: `regenerate_log.jsonl` non trovato su path ROOT (`~/Documents/app-antigravity-auto/wa-intelligence/`). Sta nel **release path** (dove gira il tg-bot, `REGEN_LOG_PATH` è relativo a `__file__`). Verificare `tail releases/20260527_083951/wa-intelligence/regenerate_log.jsonl` — la riga `reply_3c270690 model_used=gemini-2.5-flash` dovrebbe esserci. Se sì → audit log OK. Solo conferma.
2. **Anelli E2E rimanenti** (VERIFIED ~3/9 storico) — vedi `.claude/NEXT_SESSION_PROMPT.manual.md` per la mappa anelli. Day 1 dealer reale ancora BLOCKED finché E2E completo + Luke "pienamente soddisfatto".
3. **Scope congelati**: `image_sanitizer` (D-32 over-mask), landing page — NON riaprire senza decisione founder.

### Vincoli S239: TEST_FOUNDER 393314928901 prima di dealer reali · `image_sanitizer`/landing CONGELATI · `restart_time argos-wa-daemon`=50 · iMac clock +2h · deploy SEMPRE su 2 path · rollback rigenera = `cp telegram-handler.py.bak-pre-s238 telegram-handler.py` su ENTRAMBI i path + `pm2 restart argos-tg-bot`.

### TODO memoria (deferred per budget): aggiungere a MEMORY.md index entry progetto "S238 rigenera VERIFIED + lezione thinkingBudget:0 su Gemini 2.5".

---

> Storico sessioni precedenti (S237 e prima): `.claude/NEXT_SESSION_PROMPT.manual.md`.
