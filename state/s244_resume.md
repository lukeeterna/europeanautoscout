S245 — continua il consolidamento stato ARGOS (verdetto Claude AI state/s242_claude_ai_verdict.md).

PRIMA AZIONE: `cd ~/Documents/combaretrovamiauto-enterprise && bash state/refresh.sh S245`
poi leggi STATE.md (tabella anelli rigenerata) + sezioni 2/3. NON riscrivere handoff a mano.

Fatto in S244 (Step 4 chiuso):
- smoke `tools/tests/test_dossier_hitl_smoke.py` scritto + eseguito (1/1 PASS).
- ring `5-6-7` SPLITTATO in **5** (PDF gen, smoke VERIFIED) e **6-7** (HITL+invio WA, tier full).
- anello 5 ora VERIFIED. Stato: 2 + 9A + 5 = VERIFIED; 8 = BLOCKED; 1/9B/6-7 = UNVERIFIED onesti.
- NOTA onestà: anello 6 (gate HITL `app.py _update_dossier_status`) è fastapi-coupled → su MacBook
  fa SKIP non-gating; lo smoke lo esercita davvero SOLO su iMac/CI dove fastapi è installato.

DA FARE (in ordine, high-stakes → checkpoint git PRIMA di 6-8):
- Step 6: gate A-C + .harness/ — PreToolUse hook che (a) reject scrittura manuale dentro
  `<!-- GENERATED:rings -->` in STATE.md, (b) reject token VERIFIED in file stato per anello non-pass,
  (c) reject edit a .harness/file-hook. SessionStart hook esegue refresh smoke prima di CC.
- Step 7: redirect ~/.claude/hooks/global_session_end.sh → breadcrumb = pointer a STATE.md + task,
  ZERO ri-asserzione status. NON disattivarlo (memoria feedback_keep_autoclose_hook_context_control).
- Step 8: backup verificato Rule 1d → move HANDOFF*/prompts(58)/.claude/NEXT_SESSION_PROMPT in archive/
  → 1 riga pointer STATE.md → commit checkpoint.
- Step 9: classe azioni high-stakes + Gate E (hook blocca, scrive pending_review/<azione>.md, exit!=0).
- 6-7 E2E: gate HITL su iMac (fastapi presente) + invio PDF su TEST_FOUNDER 39<TEST_FOUNDER_NUM> (mai dealer reale).

Done-condition finale: sessione fresh, refresh parte da solo, CC procede da stato GENERATO.
