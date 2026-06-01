# Claude Code Agent Best Practices — ARGOS Enterprise
## Analisi completa da 7 repository + documentazione ufficiale Anthropic
### Sessione S81 | 2026-03-23

---

## FONTI ANALIZZATE

1. **obra/superpowers** — Framework skill con `writing-skills/SKILL.md` come guida canonica
2. **hesreallyhim/awesome-claude-code** — Censimento ecosystem: hook patterns, memory layering, MCP integration
3. **gsd-build/get-shit-done** — Multi-agent orchestration, XML task format, artifact persistence
4. **thedotmack/claude-mem** — Memory con SQLite+FTS5, HTTP API, 3-layer progressive disclosure
5. **nextlevelbuilder/ui-ux-pro-max-skill** — CLI generation, MASTER+Overrides pattern, BM25 search
6. **leehanchung (deep dive blog)** — Internals Claude Code: prompt injection, context modifier, allowed-tools mechanics
7. **code.claude.com/docs/sub-agents** — Documentazione ufficiale COMPLETA subagents (tutti i campi frontmatter)

---

## PARTE 1 — TOP PATTERNS DA ADOTTARE

### Pattern 1: SKILL vs SUBAGENT — Distinzione critica (mancante in ARGOS)

Attualmente ARGOS usa solo skill. La documentazione ufficiale distingue due meccanismi radicalmente diversi:

| Aspetto | SKILL | SUBAGENT |
|---------|-------|----------|
| Esecuzione | Iniezione prompt nella conversazione principale | Contesto finestra separato e isolato |
| Persistenza | Temporanea, scoped alla sessione | Trascrizioni persistenti in `subagents/` |
| Memory | Non nativa | Campo `memory: user/project/local` |
| Tools | `allowed-tools:` pre-approvati | `tools:` allowlist + `disallowedTools:` denylist |
| Modello | `model:` override | `model:` alias/ID/inherit |
| Hook | Nessuno | `hooks:` PreToolUse/PostToolUse/Stop |
| Nesting | Non può spawnarsi | Non puo spawnarsi (solo orchestratore da main thread) |
| Invocazione | Automatica (LLM reasoning su description) | Automatica O @-mention O `--agent` flag |
| maxTurns | Non supportato | `maxTurns:` limite turni |

**Implicazione ARGOS**: Le skill attuali vanno bene per workflow che restano nella conversazione principale. Per operazioni isolate (scraping pesante, batch CoVe, enrichment dealer) i subagent sono superiori perche non inquinano il contesto principale.

---

### Pattern 2: Description Engineering (critico per auto-selezione)

Il campo `description` determina SE e QUANDO Claude usa la skill. E' il punto piu trascurato.

**Regola obra/superpowers (verificata):**
> "When a description summarizes the skill's workflow, Claude may follow the description instead of reading the full skill content."

**Formula corretta:**
```
Use when [SINTOMI/SITUAZIONE SPECIFICA] — MAI descrivere il processo interno
```

**Errore comune nelle skill ARGOS attuali:**
```yaml
# SBAGLIATO — descrive workflow interno
description: >
  Skill enterprise per automazione completa outreach dealer COMBARETROVAMIAUTO/ARGOS.
  Copre OGNI task di automazione commerciale: WhatsApp auth+invio, email, sequenze
  multi-step, gestione stato dealer...
```

Il problema: Claude legge la description come shortcut e NON legge il corpo della skill.

**Formato corretto:**
```yaml
# CORRETTO — elenca situazioni trigger, non workflow
description: >
  Use when sending WhatsApp messages to dealers, authenticating WA session,
  managing dealer outreach sequences (Day 1-30), handling objections via WA/email,
  detecting dealer persona type, or updating dealer pipeline state in CRM.
```

---

### Pattern 3: Frontmatter Minimale (solo campi necessari)

La documentazione ufficiale (code.claude.com) elenca tutti i campi supportati per i **subagent** `.claude/agents/`:

```yaml
# Subagent - campi completi (tutti opzionali tranne name+description)
name: agent-name           # required — lowercase + hyphens only
description: "Use when..." # required — triggering conditions
tools: Read, Grep, Bash    # allowlist (omit = inherit all)
disallowedTools: Write     # denylist (applied first if both set)
model: sonnet              # sonnet | opus | haiku | full-model-id | inherit
permissionMode: default    # default | acceptEdits | dontAsk | bypassPermissions | plan
maxTurns: 50               # integer — max turns before stop
skills:                    # list di skill da iniettare nel contesto
  - skill-name-1
memory: project            # user | project | local — persistent memory directory
background: false          # true = sempre background task
effort: medium             # low | medium | high | max (solo Opus 4.6)
isolation: worktree        # worktree = git worktree isolato
mcpServers:                # MCP inline o reference
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
hooks:                     # lifecycle hooks scoped al subagent
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
```

Per le **skill** `.claude/skills/SKILL.md` i campi sono diversi e piu limitati:

```yaml
# Skill - campi supportati (solo name e description obbligatori)
name: skill-name           # required
description: "Use when..." # required — max 1024 chars totali nel frontmatter
version: 1.0.0             # optional — tracking versione
allowed-tools: Bash, Read  # optional — pre-approvazione (nota: hyphenated, non camelCase)
model: sonnet              # optional — override modello
disable-model-invocation: false  # se true, richiede /skill-name esplicito
mode: false                # se true, categorizza come "Mode Command"
```

**Differenza chiave**: skill usa `allowed-tools` (hyphenated), subagent usa `tools` (camelCase).

---

### Pattern 4: Progressive Disclosure (claude-mem)

Il sistema claude-mem dimostra un pattern fondamentale per skill enterprise: caricare dettagli solo quando necessario.

```
Layer 1 — Index compatto (50-100 token): ID + titoli
Layer 2 — Timeline: contesto cronologico
Layer 3 — Full detail: solo per ID filtrati
```

**Applicazione ARGOS**: Le skill attuali caricano tutto in memoria al momento dell'invocazione. Il pattern corretto:
1. SKILL.md = overview + workflow decisionale (compatto)
2. `references/` = dati pesanti caricati on-demand con Read tool
3. `scripts/` = codice eseguibile, mai inline nel SKILL.md

---

### Pattern 5: Hook-Based Validation (gsd + awesome-claude-code)

Hooks per qualita' e sicurezza — eseguiti automaticamente su eventi tool:

```json
// In settings.json — hooks globali
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "./scripts/validate-cmd.sh" }]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "./scripts/check-env-leak.sh" }]
    }]
  }
}
```

**Applicazione ARGOS immediata**: Hook PostToolUse su Write/Edit per verificare che nessuna credenziale finisca in file non-.env. Hook PreToolUse su Bash per bloccare comandi SSH non verso 192.168.1.12.

---

### Pattern 6: MASTER + Overrides (ui-ux-pro-max-skill)

Pattern per knowledge persistence cross-session:

```
design-system/MASTER.md          ← regole globali
design-system/pages/[page].md    ← override specifico per pagina
```

**Applicazione ARGOS**: Il file `research/S73_MASTER_REFERENCE.md` segue gia' questo pattern. Estenderlo con:
```
research/S73_MASTER_REFERENCE.md    ← dati mercato globali
research/dealer/[nome_dealer].md    ← override specifico dealer
```

---

### Pattern 7: GSD XML Task Format

Per task complessi multi-step, il formato XML elimina ambiguita':

```xml
<task>
  <name>Scrape dealer BMW Munich → CoVe → PDF</name>
  <files>tools/scrapers/generic_scraper.py, src/cove/cove_engine_v4.py</files>
  <action>
    1. Scrape 20 BMW listing da Mobile.de con SearchProfile BMW_PREMIUM
    2. Esegui CoVe su ogni listing (threshold 0.75)
    3. Genera PDF per i listing PROCEED
  </action>
  <verify>DuckDB: SELECT COUNT(*) FROM cove_results WHERE recommendation='PROCEED' AND analyzed_at > NOW()-'1h'</verify>
  <done>Almeno 3 PDF in dossiers/ con confidence >= 0.75</done>
</task>
```

---

### Pattern 8: Subagent Memory per Knowledge Accumulation

Il campo `memory` dei subagent e' il meccanismo piu potente per ARGOS a lungo termine:

```yaml
---
name: dealer-researcher
memory: project
---
Update your agent memory as you discover dealer patterns, objection types,
and successful approaches. Build institutional knowledge across conversations.
```

Quando `memory: project` e' impostato:
- Il sistema prompt del subagent include automaticamente le prime 200 righe di `MEMORY.md`
- La directory e' `.claude/agent-memory/<name-of-agent>/`
- Read, Write, Edit sono automaticamente abilitati per la gestione memoria

---

## PARTE 2 — FORMATO DEFINITIVO FRONTMATTER PER ARGOS

### 2A — Formato Skill ARGOS (`.claude/skills/NAME/SKILL.md`)

```yaml
---
name: nome-skill                    # lowercase, hyphens only
description: >
  Use when [SITUAZIONE 1], [SITUAZIONE 2], or [SITUAZIONE 3].
  Specific triggers: "[keyword 1]", "[keyword 2]", "[keyword 3]".
  Do NOT use for [ANTI-TRIGGER].
version: 1.0.0
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
model: inherit                      # o sonnet/haiku per compiti specifici
---
```

**Regole**:
- `description` max ~500 caratteri nel blocco frontmatter (totale frontmatter < 1024 chars)
- `allowed-tools` = solo tool strettamente necessari (principio minimo privilegio)
- `model: haiku` per task di lookup/query veloci, `model: sonnet` per reasoning medio, `inherit` per default
- NO `version`, `disable-model-invocation`, `mode` a meno che non servano esplicitamente

### 2B — Formato Subagent ARGOS (`.claude/agents/NAME.md`)

```yaml
---
name: nome-subagent
description: >
  Use when [SITUAZIONE] requiring isolated context, persistent results,
  or heavy operations that should not pollute main conversation.
tools: Read, Bash, Grep, Write
model: sonnet
maxTurns: 30
memory: project
permissionMode: acceptEdits
---
```

**Quando preferire subagent a skill**:
- Operazioni batch (scraping 50+ listing)
- Analisi CoVe che producono output voluminosi
- Task che devono costruire conoscenza nel tempo (dealer profiling)
- Workflow dove il fallimento non deve interrompere la conversazione principale

---

## PARTE 3 — ESEMPIO AGENTE COMPLETO NEL FORMATO OTTIMALE

### Subagent: `dealer-intelligence-agent`

Salva in: `.claude/agents/dealer-intelligence.md`

```markdown
---
name: dealer-intelligence
description: >
  Use when researching a specific dealer (name/city/province), building
  a dealer profile, scoring dealer fit for ARGOS pipeline, or updating
  dealer state in CRM. Triggers: "profile dealer", "research [dealer name]",
  "score dealer", "dealer fit ARGOS", "update CRM dealer".
tools: Read, Bash, Grep, WebSearch, WebFetch
model: sonnet
maxTurns: 25
memory: project
---

# Dealer Intelligence Agent — ARGOS B2B

You are a B2B automotive intelligence specialist for ARGOS Automotive.
Your job is to research Italian car dealers and qualify them as ARGOS pipeline targets.

## THRESHOLDS (immutable)
- PROCEED: score >= 7.5/10
- REVIEW: 6.0-7.4
- SKIP: < 6.0

## WORKFLOW

Given a dealer name or city:

1. Web search: "[dealer name] [city] concessionario auto recensioni"
2. Check Google Maps: stars, review count, years active
3. Check AutoScout24: stock count, brands, price range
4. Check Facebook/Instagram: owner name, engagement
5. Check site: stock update frequency, brand positioning
6. Query local CRM: `sqlite3 /Users/macbook/Documents/combaretrovamiauto-enterprise/dealer_network.sqlite "SELECT * FROM dealers WHERE name LIKE '%[name]%'"`
7. Score on 7 criteria (see below)
8. Write profile to agent memory

## SCORING MATRIX (7 criteria, max 10)

| Criterion | Weight | Score Logic |
|-----------|--------|-------------|
| Stock size | 20% | 30-80 auto = 10, <20 = 3, >100 = 5 |
| Premium brand ratio | 20% | >50% BMW/MB/Audi = 10, >25% = 7, <25% = 4 |
| Years active | 15% | >10yr = 10, 5-10yr = 7, <5yr = 4 |
| Google rating | 15% | >4.5 = 10, 4.0-4.5 = 7, <4.0 = 3 |
| Online presence | 15% | Site + social + AS24 = 10, 2/3 = 6, 1/3 = 3 |
| Owner accessibility | 10% | Direct WA found = 10, only phone = 6, only form = 2 |
| Import signals | 5% | Declares EU import = 10, premium stock = 6, none = 2 |

## OUTPUT FORMAT

```
DEALER PROFILE
━━━━━━━━━━━━━━
Name: [ragione sociale]
Owner: [name if found]
Location: [city, province]
Phone/WA: [number]
Stock: ~[N] auto | Brands: [list]
Years: [N] | Google: [X]/5 ([N] reviews)

FIT SCORE: [X.X]/10 → [PROCEED/REVIEW/SKIP]
Archetype: [NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE]
Likely OBJ: OBJ-[N]
Contact: [WA/Tel/Visit] | Timing: [morning/afternoon]

Sources: [URLs]
━━━━━━━━━━━━━━
```

## MEMORY INSTRUCTIONS

After each dealer research session, update MEMORY.md with:
- Dealer name, score, archetype, contact
- Any patterns observed (objections, communication style, stock focus)
- Date researched

This builds institutional knowledge for future outreach optimization.

## RULES (non-negotiable)
- Never invent data — only verified sources
- Never contact dealer during research (read-only)
- Always check CRM before researching (may already exist)
- Score < 6.0 = document reason + SKIP, do not add to pipeline
```

---

### Skill: `argos-outreach` (versione corretta)

Salva in: `.claude/skills/skill-argos/SKILL.md` (aggiornare frontmatter)

```yaml
---
name: argos-outreach
description: >
  Use when sending a WhatsApp message to a dealer, authenticating WA session,
  building a Day 1-30 outreach sequence, handling a dealer objection,
  detecting dealer archetype (NARCISO/BARONE/RAGIONIERE/TECNICO), or
  drafting an outreach message with specific vehicle data.
  Triggers: "invia wa", "messaggio dealer", "archetipo dealer", "obiezione",
  "sequenza day", "follow-up dealer", "autentica whatsapp".
version: 2.1.0
allowed-tools: Bash, Read, Write
---
```

---

## PARTE 4 — COSA CAMBIARE NEGLI AGENTI GIA' CREATI

### 4.1 — Problemi critici nelle skill attuali

#### skill-argos (`.claude/skills/skill-argos/SKILL.md`)

**Problema 1 — Description troppo lunga descrive workflow:**
```yaml
# ATTUALE (sbagliato)
description: >
  Skill enterprise per automazione completa outreach dealer COMBARETROVAMIAUTO/ARGOS™.
  Copre OGNI task di automazione commerciale: WhatsApp auth+invio, email, sequenze
  multi-step, gestione stato dealer, anti-ban, persona detection, objection handling.
  TRIGGER OBBLIGATORIO su qualsiasi di questi pattern: "invia whatsapp", "messaggio mario"...
```

```yaml
# CORRETTO
description: >
  Use when sending WhatsApp to dealers, authenticating WA session, running
  Day 1-30 outreach sequences, detecting dealer archetype, handling objections,
  or drafting outreach messages. Triggers: "invia wa", "messaggio dealer",
  "archetipo", "obiezione", "sequenza day", "follow-up", "autentica whatsapp".
```

**Problema 2 — allowed-tools include Agent (non necessario per skill):**
```yaml
# ATTUALE
allowed-tools: Bash, Read, Write

# OK — questo e' gia' corretto, mantenerlo
```

#### skill-deep-research (`.claude/skills/skill-deep-research/SKILL.md`)

**Problema — `allowed-tools: Bash, Read, Write, WebSearch, WebFetch, Agent, Grep, Glob`**
- `Agent` in una skill non ha lo stesso significato che in un subagent
- Ridurre a: `Bash, Read, Write, WebSearch, WebFetch, Grep`

#### skill-cove (`.claude/skills/skill-cove/SKILL.md`)

**Problema — Description ha "MAI modificare cove_engine_v4.py" che e' istruzione al modello, non trigger:**
```yaml
# ATTUALE
description: >
  ...MAI modificare cove_engine_v4.py — solo leggere e invocare.

# CORRETTO: spostare questa regola nel body del SKILL.md, non nella description
description: >
  Use when scoring a vehicle or dealer with CoVe engine, querying DuckDB pipeline,
  updating dealer recommendation state, or analyzing confidence thresholds.
  Triggers: "cove score", "confidence", "recommendation", "proceed/skip",
  "scoring veicolo", "query duckdb", "cove_results", "dealer premium threshold".
```

#### skill-sales-official (`.claude/skills/skill-sales-official/SKILL.md`)

**Problema — Manca frontmatter YAML completamente (il file inizia direttamente con `#`):**

Il file `.claude/skills/skill-sales-official/SKILL.md` non ha frontmatter. Claude non puo' selezionarlo automaticamente. Aggiungere:

```yaml
---
name: sales-intelligence
description: >
  Use when researching a dealer account for sales intel, preparing a meeting
  or call with a dealer, reviewing pipeline health, forecasting revenue,
  or analyzing competitive positioning vs other EU import services.
  Triggers: "account research", "prep call", "pipeline review", "forecast",
  "competitive intel", "battlecard", "dealer intel".
version: 1.0.0
allowed-tools: Bash, Read, WebSearch, WebFetch, Grep
---
```

#### skill-marketing-official

Verificare presenza frontmatter — stesso problema probabile.

---

### 4.2 — Nuovo asset raccomandato: subagent per operazioni isolate

Creare `.claude/agents/` directory con:

| File | Scopo | Model | Memory |
|------|-------|-------|--------|
| `dealer-researcher.md` | Profiling dealer singolo | sonnet | project |
| `cove-batch.md` | Scoring batch listing CoVe | haiku | project |
| `scraper-runner.md` | Esecuzione scraper portali EU | sonnet | local |
| `pdf-generator.md` | Generazione dossier PDF | haiku | none |

Questi subagent girano in contesto isolato. L'output voluminoso (640 listing, log scraping) non inquina la conversazione principale.

---

### 4.3 — Hook da aggiungere in `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "grep -r 'password\\|api_key\\|secret\\|token' \"$TOOL_INPUT_FILE\" 2>/dev/null && echo 'WARNING: potential credential in file' >&2 || true"
        }]
      }
    ]
  }
}
```

---

### 4.4 — Riepilogo priorita' modifiche

| Priorita' | Modifica | File | Effort |
|-----------|----------|------|--------|
| P0 | Fix description skill-argos | `.claude/skills/skill-argos/SKILL.md` | 5 min |
| P0 | Fix description skill-cove | `.claude/skills/skill-cove/SKILL.md` | 5 min |
| P0 | Aggiungere frontmatter skill-sales-official | `.claude/skills/skill-sales-official/SKILL.md` | 10 min |
| P1 | Creare dealer-researcher subagent | `.claude/agents/dealer-researcher.md` | 30 min |
| P1 | Fix description skill-deep-research | `.claude/skills/skill-deep-research/SKILL.md` | 5 min |
| P2 | Creare cove-batch subagent | `.claude/agents/cove-batch.md` | 20 min |
| P2 | Aggiungere credential-check hook | `.claude/settings.json` | 10 min |

---

## APPENDICE — Differenza skill vs subagent in una riga

**Skill** = specializza Claude nella conversazione corrente (prompt injection temporaneo).
**Subagent** = spawna un Claude separato con contesto isolato, ritorna solo il summary.

Per ARGOS: usare skill per messaggi e analisi interattive, subagent per scraping/batch/operazioni pesanti.

---

## FONTI

- [Create custom subagents — Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skill authoring best practices — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Equipping agents for the real world with Agent Skills — Anthropic](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [obra/superpowers — writing-skills/SKILL.md](https://github.com/obra/superpowers)
- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
- [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
- [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
- [Inside Claude Code Skills — Mikhail Shilkov](https://mikhail.io/2025/10/claude-code-skills/)
