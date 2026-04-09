---
name: session-handoff
description: >
  Use at the end of a work session to update memory, create next session
  prompt, and ensure clean handoff. Triggers: "fine sessione", "handoff",
  "aggiorna memory", "chiudi sessione", "salva stato".
tools: Read, Write, Edit, Bash
model: sonnet
maxTurns: 15
---

# Session Handoff Agent — ARGOS Automotive

Execute end-of-session protocol: update memory, create next prompt, prepare handoff.

## PROTOCOL (from CLAUDE.md section 7)

1. Update `~/.claude/projects/.../memory/MEMORY.md` — current state
2. Create/update prompt S(N+1) in `prompts/`
3. Git commit (if requested)
4. Output: what was done + next session prompt

## MEMORY UPDATE TEMPLATE

```markdown
## STATO CORRENTE (S[N] completato — S[N+1] handoff — [date])

**S[N] COMPLETATO**: [what was accomplished]
**S[N+1] DA ESEGUIRE**: [next steps]

### Output S[N]
[key deliverables with paths]

### HANDOFF S[N+1]
[step-by-step instructions for next session]
```

## PROMPT TEMPLATE

```markdown
# PROMPT S[N+1] — [TITLE]
## Prerequisiti: [what must exist before starting]

## FASE 1 — [first task]
## FASE 2 — [second task]
...

## OBIETTIVI MISURABILI S[N+1]
[ ] ...
```

## FILES

- Memory: `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md`
- Prompts: `prompts/s{N}_*.md`
