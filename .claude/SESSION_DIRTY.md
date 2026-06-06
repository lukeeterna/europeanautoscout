# SESSION DIRTY — chiusura senza commit auto

Sessione: `2e939036-d63c-4591-9c2b-07731fe03ccc`  Timestamp: `2026-06-06T15:33:49Z`

Motivo: `git diff --check` fail (whitespace errors o conflict markers).

## Output git diff --check
```
.claude/NEXT_SESSION_PROMPT.md:31: trailing whitespace.
+Non lo eseguo ora: 62% context, deploy shared-state a saturazione = EV negativo (`feedback_global_context_gate_lag`, 3 sessioni bruciate). 
```

## Status
```
 M .claude/NEXT_SESSION_PROMPT.md
 M vos-out/decisions.jsonl
?? .claude/SESSION_DIRTY.md
```

Risolvi manualmente, poi commit. Sessione successiva legge questo file.
