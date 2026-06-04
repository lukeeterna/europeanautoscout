# S239 — Ripartenza

## ✅ S238 — ESITO (2026-06-04): root cause "🔄 Rigenera" troncato TROVATA+CONFERMATA live · fix A+B implementato+verificato+DEPLOYATO · resta SOLO il GATE FISICO

### Root cause CONFERMATA a runtime (chiamata live Gemini, non assunta)
Il rigenera produceva reply troncata a ~60 char (JSON `{"messages":[...]}` mai chiuso). **Causa**: `gemini-2.5-flash` è un modello **reasoning** → i thinking-token consumavano tutto `maxOutputTokens:512`. Test live: `thoughtsTokenCount:487` / `candidatesTokenCount:21` → 21 token di output reale → `finishReason:MAX_TOKENS`. Con `thinkingConfig:{thinkingBudget:0}` → `finishReason:STOP`, output completo. **Il fix del vecchio handoff S238 (solo Markdown su send()) era SBAGLIATO** — avrebbe consegnato JSON troncato. Bug isolato al rigenera: la generazione normale usa `gemini-2.0-flash` (non-reasoning), nessun rischio.

### FATTO (delega ai-engineer impl + devops deploy, tutto verificato da CC sul codice reale)
- **FIX A (primario)** `wa-intelligence/telegram-handler.py:519-523` — `generationConfig` ora ha `maxOutputTokens:800, temperature:0.85, thinkingConfig:{thinkingBudget:0}`. Risolve il troncamento alla radice.
- **FIX B (consegna)** `telegram-handler.py:140-178` — `send()` ora ha fallback Markdown→plain su HTTP 400 (la preview operatore contiene `{ [ "` che rompe Markdown). `reply_markup` preservato, firma invariata, `tg_post()` intatto. Beneficia anche le conferme di `cmd_approva` con `_{reply_text}_`.
- **cmd_approva VERIFIED read-only**: parsa `json.loads(reply_text)['messages']` → instrada `/send-multi` (telegram-handler.py:297-311). Con JSON completo (post FIX A) splitta le bubble, NON manda JSON grezzo al dealer.
- **DEPLOY OK (daemon-safe, runtime-verified)**: telegram-handler.py su ENTRAMBI i path (release `releases/20260527_083951/wa-intelligence/` + ROOT `~/Documents/app-antigravity-auto/wa-intelligence/`), backup `.bak-pre-s238` (39255B) su entrambi. 3 md5 = `aa1716b8eff984704923e3893e8754fb`. `PYCOMPILE_OK` remoto (3.9). Restart SOLO `argos-tg-bot` (online, log pulito "DAEMON avviato 17:19"). **`argos-wa-daemon restart_time=50` INVARIATO + connected** (window-integrity OK).
- Codice già committato: `ae57e29` (telegram-handler.py fix) + `fe4ef18` (cmd_genera S237).

### NEXT (S239) — UNICO lavoro residuo = GATE FISICO human-gated (R1: MAI auto-VERIFIED). PACKET pronto:
```
PRE (CC read-only): ssh imac "pm2 jlist" → argos-wa-daemon restart_time atteso 50 · tail /tmp/argos-tg-bot-out.log
SEED (Luke ~1min): WA dalla SIM TEST_FOUNDER 393314928901 → ARGOS Business 3281536308
                   → annota reply_id dalla notifica TG (deve mostrare 3 bottoni: ✅ 🚫 🔄)
ESEGUI: tap 🔄 Rigenera
  PASS = arriva nel bot una NUOVA reply COMPLETA (JSON chiuso, testo diverso) con keyboard COMPLETA (✅/🚫/🔄)
         + riga in wa-intelligence/regenerate_log.jsonl (model_used=gemini-2.5-flash)
         + DB pending_replies: reply_text nuovo+completo, approved=NULL, sent=0
  FAIL-soft atteso se quota Gemini esaurita = "⚠️ quota Gemini esaurita" + riga DB INVARIATA (CORRETTO, è il floor guard)
POI (chiude il ciclo): tap ✅ Accetta sulla reply rigenerata → arriva sulla SIM (split multi-msg via /send-multi)
CHIUSURA: Luke "soddisfatto" → rigenera VERIFIED. POI git commit del verde.
NB iMac clock +2h · log tg-bot /tmp/argos-tg-bot-out.log · rollback = cp telegram-handler.py.bak-pre-s238 su ENTRAMBI i path + pm2 restart argos-tg-bot
```
- **Pre-req già risolto**: `GOOGLE_AI_API_KEY` è nell'env del tg-bot (in S237c cmd_genera è arrivato fino al send → la key c'è).
- **Reply di test S237c `reply_820392ee`**: ha reply_text troncato (65 char) dal bug PRE-fix — NON usarla, fare SEED NUOVO.

### Vincoli S239: TEST_FOUNDER prima di dealer reali · `image_sanitizer`/landing CONGELATI · `restart_time argos-wa-daemon`=50 · iMac clock +2h · deploy SEMPRE su 2 path.

---

> Storico sessioni precedenti (S237 e prima): `.claude/NEXT_SESSION_PROMPT.manual.md`.
