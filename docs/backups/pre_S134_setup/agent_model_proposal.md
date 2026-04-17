# Agent Model Audit — 2026-04-17 (Sessione S134 safe)

## Esito audit: presupposto del prompt originale SMENTITO

Il prompt S134_SETUP_v3_FINAL.md assumeva "Agent in 15 sottocartelle: molti senza `model:`. AUDITARE + tabella per Luke."

**Realtà misurata sul filesystem (2026-04-17 17:45):**

| Metrica | Valore |
|---------|--------|
| Totale file `.md` in `.claude/agents/` | 68 |
| Agent funzionali con `model:` in frontmatter | 66 |
| File senza `model:` | 2 |

**Conclusione**: non c'è lavoro di assegnazione `model:` da fare. I 2 file senza frontmatter **non sono agent**: sono documenti di riferimento mal posizionati.

---

## Distribuzione `model:` sui 66 agent funzionali

```
28 × sonnet               (alias, auto-latest)
22 × haiku                (alias, auto-latest)
11 × claude-sonnet-4-6    (pinnato)
 2 × opus                 (alias, auto-latest)
 2 × claude-opus-4-6      (pinnato)
 1 × claude-haiku-4-5-20251001  (pinnato)
```

**Osservazione:** coesistenza alias + versioni pinnate. 14 agent su 66 (~21%) sono pinnati a versioni specifiche. Gli altri usano alias.

**Best practice Anthropic:** alias per agent in evoluzione (auto-upgrade), pin specifico per agent critici dove determinismo conta più di nuove capacità.

**Decisione attuale:** coerente — i 4 core GSD (`architect`, `context-loader`, `implementer`, `validator`) sono pinnati, il resto usa alias.

---

## I 2 file senza frontmatter

### 1. `.claude/agents/intelligence/deep-researcher.md`
- Prima riga: `# DEEP_RESEARCH_SKILL.md`
- Natura: **protocollo di ricerca** (skill documentation), non agent invocabile
- **Proposta:** spostare in `.claude/skills/deep-research/SKILL.md` OPPURE convertire in agent con frontmatter YAML se deve essere invocato via Task tool

### 2. `.claude/agents/sales/sales-agent-blueprint.md`
- Prima riga: `# ARGOS SALES AGENT — ENTERPRISE BLUEPRINT`
- Natura: **blueprint architetturale** (documento di design), non agent invocabile
- **Proposta:** spostare in `docs/architecture/sales_agent_blueprint.md`

---

## Raccomandazione per Luke

**Nessuna modifica urgente.** I 2 file sono documentazione di riferimento, non rompono nulla. Decisione sul riposizionamento può attendere post-E2E.

**Se vuoi procedere dopo lo sblocco E2E:**
- Opzione A (conservativa): lasciare come sono, aggiungere `# NOT AN AGENT — see README` a inizio file
- Opzione B (pulita): spostare fuori da `.claude/agents/` come proposto sopra

**Zero azioni in questa sessione.** Report-only come da piano Sessione A-SAFE.
