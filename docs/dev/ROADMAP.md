# ARGOS AUTOMOTIVE — ROADMAP UFFICIALE 2026
## Rolling Roadmap — si aggiorna ad ogni sessione

> **Principio**: NON cancellare nulla. Layer additivi. Ogni fase completa sblocca la successiva.
> **Formato**: ✅ completato | 🔄 in corso | ⏳ prossimo | 🔮 futuro
> **Ultimo aggiornamento**: S51 — 2026-03-14

---

## 📍 FASE CORRENTE: FASE 2 — Lead Pipeline

---

## ARCHITETTURA DEFINITIVA (immutabile da S51)

```
HUMAN-IN-THE-LOOP
  └─ approva: WA nuovo dealer | fatture | deploy | QR auth
       │
  ORCHESTRATORE (main conversation)
       │ delega per task type
  ┌────┴────────────────────────────────────────┐
  │                AGENT TEAM                   │
  ├─ agent-sales      (sonnet) outreach/OBJ/WA  │
  ├─ agent-research   (sonnet) scouting/intel   │
  ├─ agent-cove       (haiku)  DuckDB/scoring   │
  ├─ agent-finance    (haiku)  fee/ROI read-only│
  ├─ agent-ops        (haiku)  PM2/SSH/infra    │
  ├─ agent-recovery   (opus)   Day7/stallo      │
  └─ agent-marketing  (sonnet) brand/content    │
  └─────────────────────────────────────────────┘
       │ usano
  ┌────┴─────────────────────────────────────────┐
  │  SKILL SYSTEM (3 layer)                      │
  │  L3: skill-argos v3, skill-cove, gh-actions  │
  │  L2: skill-sales-official, skill-data-official│
  │  L1: DuckDB, WA daemon, Telegram, PM2        │
  └──────────────────────────────────────────────┘
```

**ANTI-HALLUCINATION (5 layer attivi)**:
1. Tool restriction — agent-finance solo `Read`
2. Schema DuckDB enforcement — `recommendation` / `analyzed_at` / `confidence`
3. Hooks `PreToolUse` — validazione SQL read-only
4. Human-in-the-loop — ogni azione irreversibile passa da umano
5. Memory persistente — coerenza cross-session senza amnesia

**FRAMEWORK SCELTI** (post deep-research CoVe 2026):
- CC Native Subagents: orchestrazione (zero costo aggiuntivo) ✅
- knowledge-work-plugins: Layer 2 skills (Apache-2.0 Anthropic ufficiale) ✅
- GSD: solo dev sprint build, non ops ✅
- gstack: roles cognitivi CEO/Eng/QA ⏳ S52
- Paperclip / CLEO / LangGraph: fase scala 🔮

---

## ✅ FASE 0 — INFRASTRUTTURA BASE (completata S46-S50)

| Task | Sessione | Stato |
|------|----------|-------|
| CoVe Engine v4 Bayesian FACTORED | S46 | ✅ |
| WA Daemon v2.1 DBPool + MessageQueue | S50 | ✅ |
| OBJ codes 1-5 canonici × 5 archetipi | S50 | ✅ |
| PersonaEngine + ObjectionLibrary | S50 | ✅ |
| PM2 argos-wa-daemon + argos-tg-bot | S49 | ✅ |
| CI/CD GitHub Actions verde | S48 | ✅ |
| Skill Layer 3: argos/cove/debug/research/gh | S49 | ✅ |
| Mario Day 1 WA inviato | S49 | ✅ 2026-03-13 |

**Pendente da F0**: WA QR re-auth daemon ⚠️ (HUMAN ACTION)

---

## ✅ FASE 1 — PLUGIN UFFICIALI + AGENT TEAM (completata S51)

| Task | File | Stato |
|------|------|-------|
| skill-sales-official | `.claude/skills/skill-sales-official/` | ✅ S51 |
| skill-data-official | `.claude/skills/skill-data-official/` | ✅ S51 |
| agent-sales | `.claude/agents/agent-sales.md` | ✅ S51 |
| agent-research | `.claude/agents/agent-research.md` | ✅ S51 |
| agent-cove | `.claude/agents/agent-cove.md` | ✅ S51 |
| agent-finance | `.claude/agents/agent-finance.md` | ✅ S51 |
| agent-ops | `.claude/agents/agent-ops.md` | ✅ S51 |
| agent-recovery | `.claude/agents/agent-recovery.md` | ✅ S51 |
| agent-marketing | `.claude/agents/agent-marketing.md` | ✅ S51 |
| ROADMAP rolling | `docs/dev/ROADMAP.md` | ✅ S51 |
| Agent registry CLAUDE.md | `configs/CLAUDE.md` | ✅ S51 |

---

## 🔄 FASE 2 — LEAD PIPELINE (in corso — S52-S53)

**Obiettivo**: 5+ dealer attivi in pipeline, Mario non unico lead

| Task | Agente | Priorità | Stato |
|------|--------|----------|-------|
| QR re-auth WA daemon | agent-ops | 🔴 | ⚠️ HUMAN ACTION |
| Mario Recovery Day 7 | agent-recovery | 🔴 | ⏳ 2026-03-17 |
| gstack install (CEO/Eng/QA) | — | 🔴 | ✅ S52 `.claude/skills/gstack/` |
| skill-marketing-official | — | 🟡 | ✅ S52 `.claude/skills/skill-marketing-official/` |
| Batch 5 nuovi lead | agent-research | 🔴 | ✅ S52 `docs/dev/leads_s52_batch1.md` |
| Schede dealer qualificate | agent-research | 🔴 | ✅ S52 (5 schede con archetipo + OBJ + ROI pitch) |
| Sequenza outreach 5 dealer | agent-sales | 🟡 | ⏳ S53 (max 2 dealer/giorno anti-ban) |

**KPI Fase 2**: 5 dealer in sequenza attiva | Mario risposta o Recovery eseguito

---

## ⏳ FASE 3 — INTELLIGENCE UPGRADE (S54-S55)

**Prerequisito**: almeno 3 dealer in conversazione attiva

| Task | Agente | Note |
|------|--------|------|
| skill-finance (TD17/18/19, P&L) | agent-finance | fatture semi-automatiche |
| Competitive battlecard EU import | agent-research | skill-sales-official [C] |
| Pipeline review dashboard HTML | agent-cove + skill-data-official | Chart.js, DuckDB |
| Forecast mensile automatico | agent-finance | proiezione revenue |
| Email sequence nurture (4 email) | agent-marketing | template × archetipo |

**KPI Fase 3**: 2+ deal in negoziazione | prima fattura emessa

---

## ⏳ FASE 4 — SCALA OPERATIVA (S56-S60)

**Prerequisito**: 3+ deal chiusi, pipeline 10+ dealer attivi

| Task | Note |
|------|------|
| skill-langgraph (ARCH-001) | 8 nodi, Ollama mistral:7b, GSD per build |
| skill-rag (ARCH-002) | 4-layer ChromaDB + DuckDB + MEMORY + web |
| skill-scraping (ARCH-003) | AutoScout24 EU + Carapis + proxy Tailscale |
| skill-vin (ARCH-004) | Vincario + NHTSA + EU WMI fraud check |
| Paperclip install | heartbeat scheduling, audit log, budget enforcement |
| CLEO anti-hallucination ops | 4-layer validation per operazioni finanziarie |

**KPI Fase 4**: €2.400+/mese | <30min/lead research→contatto | zero errori DB

---

## 🔮 FASE 5 — AI COMPANY FULL AUTONOMOUS (Q3 2026)

| Visione | Descrizione |
|---------|-------------|
| Orchestratore Paperclip | Heartbeat 24/7, agenti attivi senza intervento umano |
| Pipeline dealer self-filling | agent-research genera lead autonomamente ogni settimana |
| Fatturazione automatica | agent-finance emette TD18 a veicolo consegnato (dopo approvazione) |
| Team-on-demand | Agent Teams sperimentale per campagne intensive parallele |
| Revenue target | €8.000+/mese (8+ deal × €1.000 avg) |

---

## 📊 METRICHE DI SUCCESSO (rolling)

| Fase | KPI | Target | Attuale |
|------|-----|--------|---------|
| F0 | Infra operativa | PM2 online, WA auth | ✅ (QR pendente) |
| F1 | Agent team deployato | 7 agents + 2 skills | ✅ S51 |
| F2 | Pipeline attiva | 5+ dealer in sequenza | ⏳ 0 (Mario only) |
| F3 | Deal in negoziazione | 2+ | ⏳ |
| F4 | Revenue | €2.400+/mese | ⏳ |
| F5 | Autonomia | <1h/settimana human time | 🔮 |

---

## 📋 LOG SESSIONI (rolling)

| Sessione | Data | Completato | Fase avanzata |
|----------|------|-----------|---------------|
| S46 | 2026-03-12 | claude-mem fix, enterprise migration | F0 |
| S47 | 2026-03-12 | OBJ handler, fee calculator, .taskmaster | F0 |
| S48 | 2026-03-13 | WA stack iMac, CI/CD, skill-argos v2 | F0 |
| S49 | 2026-03-13 | WA Intelligence deploy, skill v3, deep-research | F0 |
| S50 | 2026-03-13 | Crisis recovery: T-01..T-06, wa-daemon v2.1 | F0 ✅ |
| S51 | 2026-03-14 | AI company arch: 7 agents + 2 skills + roadmap | F1 ✅ |
| S52 | 2026-03-14 | PM2 restart, gstack + skill-marketing, lead batch 1 (5 dealer) | F2 🔄 |
| S53 | 2026-03-14 | Test archetipi 3 dealer (8.1/9.2/8.7), archetipi 5→10, dataset v1+v2, classifier | F2 🔄 |

---

*ARGOS Automotive CoVe 2026 | Rolling Roadmap | Aggiornare ogni sessione*
