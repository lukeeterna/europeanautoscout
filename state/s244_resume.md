S244 — continua il consolidamento stato ARGOS (verdetto Claude AI state/s242_claude_ai_verdict.md).

PRIMA AZIONE: `cd ~/Documents/combaretrovamiauto-enterprise && bash state/refresh.sh S244`
poi leggi STATE.md (tabella anelli rigenerata) + sezioni 2/3. NON riscrivere handoff a mano.

Fatto in S243 (commit ccc3639): substrato Gate A vivo. STATE.md tabella GENERATA da
state/refresh.sh (legge state/rings.json). Anelli 2 + 9A = VERIFIED (smoke offline). 8 = BLOCKED.
1/9B/5-6-7 = UNVERIFIED onesti.

DA FARE (in ordine, high-stakes → checkpoint git prima di 6-8):
- Step 4: scrivi smoke check per anelli 5/6/7 (dossier→approve HITL→invio PDF), aggiungi check_cmd
  in rings.json, esegui refresh. Rosso = gap reale → E2E su TEST_FOUNDER 393314928901 (mai dealer reale).
- Step 6: gate A-C + .harness/ — PreToolUse hook che (a) reject scrittura manuale dentro
  <!-- GENERATED:rings --> in STATE.md, (b) reject token VERIFIED in file stato per anello non-pass,
  (c) reject edit a .harness/file-hook. SessionStart hook esegue refresh smoke prima di CC.
- Step 7: redirect ~/.claude/hooks/global_session_end.sh → breadcrumb = pointer a STATE.md + task,
  ZERO ri-asserzione status. NON disattivarlo (memoria feedback_keep_autoclose_hook_context_control).
- Step 8: backup verificato Rule 1d → move HANDOFF*/prompts(58)/.claude/NEXT_SESSION_PROMPT in archive/
  → 1 riga pointer STATE.md → commit checkpoint.
- Step 9: classe azioni high-stakes + Gate E (hook blocca, scrive pending_review/<azione>.md, exit!=0).

Done-condition finale: sessione fresh, refresh parte da solo, CC procede da stato GENERATO.
