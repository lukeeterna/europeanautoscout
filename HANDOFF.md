# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 51 — 2026-03-14 (definitivo)

---

## ⚡ STATO CORRENTE (S51)

| Sistema | Stato | Note |
|---------|-------|------|
| CoVe Engine v4 | ✅ | Bayesian FACTORED, weights 0.35/0.25/0.20/0.20 |
| WA Daemon v2.1 | ✅ online :9191 | DBPool + prepared statements |
| WA Sessione daemon | ⚠️ QR richiesto | HUMAN ACTION: scansionare QR con Android |
| Telegram bot | ✅ | Token aggiornato, PM2 online |
| PM2 iMac | ✅ | argos-wa-daemon + argos-tg-bot |
| Agent Team | ✅ S51 | 7 subagents in `.claude/agents/` |
| Skill Layer 2 | ✅ S51 | skill-sales-official + skill-data-official |
| Skill Layer 3 | ✅ | skill-argos v3, skill-cove, skill-deep-research, gh-actions |
| CI/CD | ✅ | GitHub Actions verde |
| Mario Day 1 | ✅ INVIATO | 2026-03-13 ~12:00 |
| Mario Recovery Day 7 | ⏳ | 2026-03-17 se silenzio — usa agent-recovery |

---

## 🤖 AGENT TEAM — DEPLOYATO S51

```
.claude/agents/
├── agent-sales.md       (sonnet)  — outreach WA/email, OBJ, sequenze
├── agent-research.md    (sonnet)  — lead scouting, account intel
├── agent-cove.md        (haiku)   — CoVe scoring, DuckDB read-only
├── agent-finance.md     (haiku)   — fee/ROI/TD17 — READ ONLY
├── agent-ops.md         (haiku)   — PM2, SSH, deploy, health
├── agent-recovery.md    (opus)    — Recovery Day 7, stallo trattativa
└── agent-marketing.md   (sonnet)  — brand, content, landing, email
```

**HUMAN-IN-THE-LOOP obbligatorio**: WA nuovo dealer, fatture, deploy, QR auth

---

## 🎯 MARIO OREFICE — SEQUENZA ATTIVA

| Campo | Valore |
|-------|--------|
| Contatto | +393336142544 |
| Nome | Mario Orefice, Mariauto Srl |
| Archetipo | RAGIONIERE (confidence 0.85) |
| Veicolo | BMW 330i G20 2020, km 45.200 (LOCKED), €27.800 franco DE |
| Margine dealer | €3.100 netto dopo fee |
| Fee | €800 success-only |
| Day 1 WA | ✅ INVIATO 2026-03-13 ~12:00 |
| Day 7 WA | ⏳ 2026-03-17 se silenzio → usa **agent-recovery** |
| Day 14 Email | ⏳ 2026-03-22 se ancora silenzio |

**Recovery Day 7 — testo APPROVATO (RAGIONIERE v3):**
```
Mario, le ho scritto qualche giorno fa in modo
forse troppo diretto — mi scuso.

Verifico veicoli in Europa per dealer con dati
certificati. Zero anticipi, si paga solo
a veicolo consegnato e approvato.

Se serve una verifica su qualcosa di specifico,
sono qui. — Luca
```

---

## ✅ COMPLETATO SESSION 51 — AI COMPANY ARCHITECTURE

| Task | File/Path | Note |
|------|-----------|------|
| Deep research GSD + framework | agent deep-research | GSD = dev only, CC Subagents = prioritario |
| Deep research stato arte AI company | agent deep-research | gstack, Paperclip, CLEO, VoltAgent analizzati |
| Agent team (7 subagents) | `.claude/agents/` | sales/research/cove/finance/ops/recovery/marketing |
| skill-sales-official | `.claude/skills/skill-sales-official/` | account-research, competitive-intel, pipeline |
| skill-data-official | `.claude/skills/skill-data-official/` | /write-query DuckDB, /analyze, /validate |
| ROADMAP rolling | `docs/dev/ROADMAP.md` | Fasi F0→ARCH, framework scelti, anti-hallucination |
| Agent registry CLAUDE.md | `configs/CLAUDE.md` | 7 agenti + skill registry aggiornato |
| Memory aggiornata | `memory/MEMORY.md` | Agent team + roadmap entry |

---

## 📂 FILE CRITICI (paths definitivi)

```
CoVe Engine:   src/cove/cove_engine_v4.py        ← NON modificare MAI
DB locale:     data/db/cove_tracker.duckdb
DB iMac:       ~/Documents/app-antigravity-auto/data/db/ (via SSH)
Agents:        .claude/agents/                    ← 7 subagents S51
Skills L3:     .claude/skills/skill-argos/        ← MAI modificare struttura
Skills L2:     .claude/skills/skill-sales-official/
               .claude/skills/skill-data-official/
Roadmap:       docs/dev/ROADMAP.md
MCP config:    .mcp.json                          ← TENERLO VUOTO
Global MCP:    ~/.claude/claude_desktop_config.json
```

---

## 🚀 PROSSIMA SESSIONE (S52) — PROMPT COMPLETO

```
Sessione 52 — ARGOS. Leggi HANDOFF.md + ROADMAP.md (docs/dev/).
Sei CTO AI di ARGOS Automotive. Agent team deployato in S51 (.claude/agents/).

STATO S51:
- 7 subagents operativi + skill-sales-official + skill-data-official ✅
- Mario Day 1 inviato 2026-03-13, Day 7 Recovery = 2026-03-17 se silenzio
- WA daemon online :9191 ma ⚠️ QR re-auth pendente (HUMAN ACTION)

PRIORITY 1 — QR re-auth (se SSH disponibile):
  agent-ops → health check → QR re-auth via browser http://192.168.1.12:8765
  Scansionare con Android (stessa SIM Very Mobile +393281536308)

PRIORITY 2 — Mario Recovery Day 7 (se data ≥ 2026-03-17):
  agent-recovery → Recovery RAGIONIERE v3 → approvazione umana → agent-sales → invio

PRIORITY 3 — Lead pipeline (se Mario è unico lead):
  agent-research → batch 5 dealer Sud Italia (Campania/Puglia/Sicilia)
  Criteri: family-business, 30-80 auto, BMW/Mercedes/Audi, no partner EU
  Output: 5 schede dealer qualificate con archetipo + OBJ pre-caricato

PRIORITY 4 — gstack install (roles cognitivi CEO/Eng/QA):
  git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
  cd ~/.claude/skills/gstack && ./setup
  Aggiungere sezione gstack a configs/CLAUDE.md

PRIORITY 5 — skill-marketing-official:
  Crea .claude/skills/skill-marketing-official/SKILL.md
  Basato su knowledge-work-plugins/marketing (Apache-2.0)
  Comandi: /draft-content, /email-sequence, /brand-review, /campaign-plan

ROADMAP corrente: docs/dev/ROADMAP.md — FASE 1 ✅, FASE 2 in corso
Fine sessione: aggiorna HANDOFF.md + ROADMAP.md + MEMORY.md + commit
```

---

## 🔴 PENDENTI OPERATIVI (non bloccanti per S52)

| Task | Agente | Data |
|------|--------|------|
| WA QR re-auth daemon | agent-ops | Appena SSH torna |
| Mario Recovery Day 7 | agent-recovery | 2026-03-17 |
| Lead batch 5 dealer | agent-research | S52 |
| gstack install | — | S52 |
| skill-marketing-official | — | S52 |
| skill-finance | — | S53 |
