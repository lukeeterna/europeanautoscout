# S159 — Resume path post-S158

**Stato S158**: ✅ VERDE su scope ("PDF size 5KB → dealer-grade") con caveat.
- PDF dossier 5,289 → 4,161,219 bytes (BMW) / 4,761,092 (Mercedes)
- 6 immagini full-res embedded verificate (raw PDF inspection)
- Commit `61da7da` pushed

**Caveat critico (BLOCKER per Day 1 reale)**:
🟡 Sanitizer PaddleOCR NON operativo — foto full-res embeddate contengono watermark/branding del dealer tedesco originario, targhe, numeri telefono. Violazione zero-source policy ARGOS.
- **NON inviare PDF S158 a dealer reali Sud Italia** finché sanitizer non fixato.
- Pre-existing bug (era rotto anche in S157), ora esposto perché immagini embeddate.

**Violation di sessione**: Context Budget Gate violata 4 volte (50→53→65→74%). Hook automatico richiesto per enforcement futuro (`~/.claude/hooks/context_budget_gate.py`).

---

## Opzioni Luke (decide tu)

### A) S159 — Setup PaddleOCR + smoke sanitizer (PRIMA di Day 1 reale)
**Scope**: setup PaddleOCR su Python 3.12 system o venv `~/.argos-sanitizer-venv/`. Aggiornare `_SANITIZER_PYTHON` candidates. Smoke run con BMW Serie 3 → log deve mostrare `[SANITIZER] Using /path (has PaddleOCR)`. Visual inspection PDF post-fix: targhe blur + watermark dealer originale rimossi.
**Timebox**: 60min autonomo
**Rischio dealer**: ZERO (no outreach)
**Sblocca**: S160 test founder interattivo → S161 Day 1 reale Stile Car

### B) Hook Context Budget Gate (infra parallela)
**Scope**: implementare `~/.claude/hooks/context_budget_gate.py` + bridge statusline che a 50% context emette warning forzato e blocca tool calls non-closure. Riferimento: prompt esistente per "context budget gate (3 componenti hook/regola/statusline)".
**Timebox**: 90min
**Rischio dealer**: ZERO
**Sblocca**: enforcement strutturale regola Context Budget violata 4 volte in S158

### C) Test founder interattivo CON Luke (richiede autorizzazione esplicita)
**SOLO SE** Luke vuole bypassare caveat sanitizer per primo smoke (PDF tecnicamente leak, ma TEST_FOUNDER è suo numero). Sessione interattiva CON Luke davanti. **Pre-requisito**: autorizzazione esplicita in chat (`feedback_no_live_without_test.md`).

### D) Altro
- Day 1 sequence revision V3 → V4
- Health monitoring 5min cron + Telegram alert
- Dealer scouting Sud Italia espansione pipeline
- Smoke FE SIGN flow Cloudflare Pages browser

---

## Refs
- `HANDOFF.md` → STATO CORRENTE S158 con caveat sanitizer
- `BACKLOG.md` → "Image Sanitizer (PaddleOCR) NON OPERATIVO" entry
- `.planning/S158-PDF-DIAGNOSIS.md` → root cause + fix diagnosis
- Memory: `s158_pdf_fix.md`, `feedback_context_budget_gate.md`, `feedback_session_end_mandatory.md`

## Regole sessione (rispettare)
1. `feedback_no_live_without_test.md` — NO Day 1 reale auto-eseguibile
2. `feedback_context_budget_gate.md` — closure forzata >50% context
3. `feedback_session_end_mandatory.md` — commit + prompt next session OBBLIGATORI
