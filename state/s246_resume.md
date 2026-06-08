S246 — continua il consolidamento substrato stato ARGOS (verdetto `state/s242_claude_ai_verdict.md`).

PRIMA AZIONE: `cd ~/Documents/combaretrovamiauto-enterprise && bash state/refresh.sh S246`
poi leggi STATE.md (tabella anelli rigenerata + sezioni 2/3). NON riscrivere handoff a mano,
NON editare il blocco `<!-- GENERATED:rings -->` (Gate A lo blocca da S245).

Fatto in S245 (Step 6 CHIUSO, commit d97d353):
- `.harness/state_guard.py` = PreToolUse hook Gate A/B/C/D-via-B. 11 test stdin PASS.
- registrato in `.claude/settings.json` (PreToolUse Write|Edit|MultiEdit).
- `session_start.sh` esegue `bash state/refresh.sh` PRIMA di CC (auto-downgrade stale).
- NB: gli hook si leggono a SessionStart → il guard è ATTIVO da S246. Per editare
  guard/generatori serve lanciare CC con `ARGOS_HARNESS_UNLOCK=1`.
- Checkpoint pre-hook: commit 858ca32 (rollback point pulito).

DA FARE (ordine — high-stakes, backup Rule 1d PRIMA di file globali/lossy):
- Step 7: redirect `~/.claude/hooks/global_session_end.sh` → breadcrumb = pointer a STATE.md,
  ZERO ri-asserzione status. NON disattivarlo (memoria feedback_keep_autoclose_hook_context_control).
  File GLOBALE fuori repo: backup verificato (size>0, mtime precedente, fuori /tmp, citato) PRIMA.
- Step 8: backup verificato → move HANDOFF*/prompts(58)/.claude/NEXT_SESSION_PROMPT in archive/
  → 1 riga pointer STATE.md → commit reversibile.
- Step 9: classe azioni high-stakes + Gate E (hook blocca, scrive pending_review/<azione>.md, exit!=0).
- 6-7 E2E: gate HITL su iMac (fastapi presente) + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale).

Done-condition finale: sessione fresh, refresh parte da solo a SessionStart, guard attivo,
CC procede da stato GENERATO + protetto.
