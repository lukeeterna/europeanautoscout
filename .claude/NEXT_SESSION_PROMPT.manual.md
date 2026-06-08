# PROSSIMA SESSIONE — S246

**Entrypoint unico**: `state/s246_resume.md` (reboot-safe nel repo).

PRIMA AZIONE: `cd ~/Documents/combaretrovamiauto-enterprise && bash state/refresh.sh S246`
→ poi leggi `STATE.md` (tabella anelli GENERATA + sezioni 2/3). NON editare il blocco
`<!-- GENERATED:rings -->` (Gate A lo blocca da S245).

## Fatto in S245 (Step 6 CHIUSO)
- `.harness/state_guard.py` PreToolUse hook Gate A/B/C/D-via-B (commit d97d353, 11 test PASS).
- `session_start.sh` esegue `refresh.sh` PRIMA di CC. Checkpoint pre-hook: 858ca32.
- Guard ATTIVO da S246. Editare guard/generatori richiede `ARGOS_HARNESS_UNLOCK=1`.

## Restano (ordine)
1. Step 7 — redirect `~/.claude/hooks/global_session_end.sh` a breadcrumb (NON disattivare). Backup Rule 1d.
2. Step 8 — archivio prompts(58)/HANDOFF*/NEXT_SESSION_PROMPT → pointer STATE.md. Backup Rule 1d.
3. Step 9 — Gate E azioni high-stakes.
4. 6-7 E2E — gate HITL iMac + invio PDF TEST_FOUNDER 393314928901 (mai dealer reale).

Stato anelli atteso: 2 + 9A + 5 = VERIFIED · 8 = BLOCKED · 1/9B/6-7 = UNVERIFIED.
