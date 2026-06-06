# SESSION DIRTY — chiusura senza commit auto

Sessione: `963b00f0-65e3-4a49-b076-a416ce4bc7fc`  Timestamp: `2026-06-06T18:52:19Z`

Motivo: `git diff --check` fail (whitespace errors o conflict markers).

## Output git diff --check
```
.claude/NEXT_SESSION_PROMPT.md:31: trailing whitespace.
+**La cosa importante che ti devo dire chiaro:** non posso *garantire* che S242 esegua la priorità #0 solo perché è scritta nell'handoff — è esattamente quello che è fallito finora (gli handoff vengono ignorati o contraddetti). Il consolidamento è scritto in cima al next prompt, ma se all'avvio di S242 la sessione parte con un altro task, ricaschiamo. Per renderlo a prova di sessione servirebbe il fix dell'hook (che è parte di S242 stesso). 
```

## Status
```
 M .claude/NEXT_SESSION_PROMPT.md
?? .claude/SESSION_DIRTY.md
?? STATE.md
```

Risolvi manualmente, poi commit. Sessione successiva legge questo file.
