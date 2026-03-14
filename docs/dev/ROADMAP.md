# ARGOS AUTOMOTIVE — ROADMAP UFFICIALE 2026
## Integrazione knowledge-work-plugins × Stack Esistente

> **Principio**: NON cancellare nulla. Ogni layer si aggiunge sopra quello precedente.
> **Ultimo aggiornamento**: S51 — 2026-03-14

---

## ARCHITETTURA TARGET (3 Layer)

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — ARGOS SPECIALIST (esistente, immutabile)         │
│  skill-argos v3       → Italian cultural protocols          │
│  skill-cove v1        → CoVe engine Bayesian FACTORED       │
│  skill-argos-debug v1 → WA troubleshooting                  │
│  skill-deep-research  → Lead scouting EU                    │
│  gh-actions           → CI/CD GitHub                        │
└─────────────────────────────────────────────────────────────┘
         ↑ si specializza sopra
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2 — OFFICIAL PLUGINS ADATTATI (da aggiungere)        │
│  skill-sales-official → account-research, draft-outreach,   │
│                         competitive-intelligence, pipeline   │
│  skill-data-official  → write-query DuckDB, analyze,        │
│                         validate, build-dashboard            │
└─────────────────────────────────────────────────────────────┘
         ↑ foundation generica su cui costruire
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — INFRASTRUTTURA (esistente, operativa)            │
│  DuckDB cove_tracker.duckdb                                  │
│  WA Intelligence daemon PM2                                  │
│  Telegram bot @ArgosautomotiveBot                            │
│  GitHub Actions CI/CD                                        │
│  Ollama mistral:7b locale                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## FRAMEWORK SCELTI (decisione definitiva S51)

| Framework | Ruolo | Perché scelto | Scartato? |
|-----------|-------|---------------|-----------|
| **CC Native Subagents** | Orchestrazione agenti | Nativo, zero costo, integra skill system | NO — PRIORITARIO |
| **knowledge-work-plugins** | Layer 2 skill foundation | Ufficiale Anthropic, Apache-2.0, B2B sales/data | NO — IN USO |
| **GSD** | Dev sprint | Spec-driven, stato tra sessioni, 29.8k stars | Solo per build, non ops |
| **gstack** | Ruoli cognitivi | CEO/Eng/Review/QA come agenti distinti | DA INSTALLARE |
| **VoltAgent subagents** | Agenti addizionali | 127+ production-ready | Futuro se gap |
| **LangGraph** | Orchestrazione stateful | Overkill ora, ARCH-001 futuro | Dopo 3+ deal |
| **Paperclip** | Zero-human company | Heartbeat scheduling, audit log | Fase scala |
| **CLEO** | Anti-hallucination ops | 4-layer validation critico | Prima di finance auto |
| **TaskMaster** | DAG task management | Dependency tracking | Dopo validazione |

**ANTI-HALLUCINATION PATTERN ATTIVI:**
1. Subagenti con tool restriction (agent-finance solo Read)
2. Hooks PreToolUse su Bash → validazione SQL read-only
3. Schema enforcement DuckDB (recommendation/analyzed_at/confidence)
4. Human-in-the-loop per ogni azione irreversibile
5. Memory persistente per coerenza cross-session
6. RAG grounding su dati reali (DuckDB, non parametri LLM)

---

## FASE 0 — OPERATIVO (completato S50)

| Task | Stato | Data |
|------|-------|------|
| CoVe Engine v4 Bayesian FACTORED | ✅ | 2026-03-13 |
| WA Daemon v2.1 DBPool + MessageQueue | ✅ | 2026-03-13 |
| OBJ codes 1-5 canonici × 5 archetipi | ✅ | 2026-03-13 |
| PersonaEngine + ObjectionLibrary | ✅ | 2026-03-13 |
| PM2: argos-wa-daemon + argos-tg-bot | ✅ | 2026-03-13 |
| CI/CD GitHub Actions | ✅ | S49 |
| Mario Day 1 WA inviato | ✅ | 2026-03-13 |

**Pendente operativo:**
- ⚠️ WA QR re-auth daemon (HUMAN ACTION)
- ⏳ Mario Recovery Day 7 → 2026-03-17

---

## FASE 1 — PLUGIN UFFICIALI FOUNDATION
**Timeline**: S51 (2026-03-14) — entro fine settimana
**Obiettivo**: Aggiungere Layer 2 senza toccare Layer 3

### Task F1-01: Install skill-sales-official
```
File: .claude/skills/skill-sales-official/SKILL.md
Fonte: github.com/anthropics/knowledge-work-plugins/sales
Capabilities da integrare:
  - account-research   → intel strutturata su dealer target
  - draft-outreach     → outreach iniziale (foundation per skill-argos)
  - competitive-intel  → battlecard competitor import EU
  - pipeline-review    → analisi salute pipeline dealer
  - call-prep          → prep chiamata/visita dealer
Configurazione ARGOS: settings.local.json con Luca Ferretti context
```
**Priorità**: 🔴 ALTA — sblocca scouting nuovi lead

### Task F1-02: Estendi skill-cove con data plugin
```
File: .claude/skills/skill-cove/SKILL.md (UPDATE, non nuovo)
Aggiungere capabilities:
  - /write-query   → SQL DuckDB auto-generated
  - /analyze       → analisi pipeline dealer
  - /validate      → QA prima di decisioni CoVe
  - /build-dashboard → HTML interattivo dealer metrics
DuckDB target: data/db/cove_tracker.duckdb
```
**Priorità**: 🟡 MEDIA — upgrade CoVe reporting

### Task F1-03: Configura sales settings.local.json
```json
{
  "name": "Luca Ferretti",
  "title": "Vehicle Sourcing Specialist EU",
  "company": "ARGOS Automotive",
  "quota": { "monthly": 5, "value_per_deal": 1000 },
  "product": {
    "name": "EU Vehicle Scouting B2B",
    "value_props": [
      "BMW/Mercedes/Audi 2018-2023 EU a prezzi di mercato",
      "€800-1200 success-fee, zero upfront",
      "ROI medio dealer 200-300%",
      "Perizia + documentale incluso tier 2-3"
    ],
    "competitors": [
      "AutoScout24 privati (no garanzie)",
      "Import fai-da-te (rischio legale)",
      "Dealer Germania diretti (barriera linguistica)",
      "Aste EU (no pre-selezione qualità)"
    ]
  },
  "target_market": "Concessionari family-business Sud Italia 30-80 auto"
}
```

---

## FASE 2 — LEAD PIPELINE AUTOMATION
**Timeline**: S52-S53 (settimana 2026-03-16)
**Obiettivo**: Pipeline dealer → 10+ prospect attivi in parallelo

### Task F2-01: Account Research sistematico
```
Usa skill-sales-official → account-research per ogni lead
Output: scheda dealer strutturata (dimensione, personalità stimata, storia)
Integra con: CoVe dealer scoring prima del primo contatto
```

### Task F2-02: Deep Research batch nuovi lead
```
Usa skill-deep-research → 5 dealer target Sud Italia
Criteri: family-business, 30-80 auto, BMW/Mercedes/Audi stock
Output: lista qualificata con personalità stimata + OBJ pre-caricato
```

### Task F2-03: Sequenza outreach multi-dealer
```
Day 1:  WA primo contatto (skill-argos template × archetipo)
Day 7:  Recovery WA se silenzio (template Recovery RAGIONIERE v3)
Day 14: Email follow-up (skill-argos [B])
Day 21: LinkedIn/tel se qualificato
Tracking: DuckDB dealer_pipeline table
```

---

## FASE 3 — INTELLIGENCE UPGRADE
**Timeline**: S54-S55 (settimana 2026-03-23)
**Obiettivo**: Decisioni data-driven, competitive positioning

### Task F3-01: Competitive Battlecard EU import
```
skill-sales-official → competitive-intelligence
Competitor: AutoScout24 privati, import fai-da-te, aste EU, dealer DE
Output: battlecard pronta per obiezioni dealer
Integra con: skill-argos OBJ handler
```

### Task F3-02: Pipeline Review dashboard
```
skill-data-official → /build-dashboard
Data source: cove_tracker.duckdb dealer pipeline
Metriche: dealer per archetipo, conversion rate, avg deal size
Output: HTML interattivo per review settimanale
```

### Task F3-03: Forecast mensile
```
skill-sales-official → /forecast
Input: pipeline attiva DuckDB
Output: proiezione revenue mensile + gap vs quota
```

---

## FASE 4 — ARCHITETTURA AVANZATA (BACKLOG)
**Timeline**: Q2 2026 — dopo validazione pipeline commerciale
**Prerequisito**: 3+ deal chiusi, pipeline 10+ dealer attivi

### ARCH-001: LangGraph Orchestrator
```
8 nodi: Ingest → Research → Score → PersonaDetect →
        DraftOutreach → ObjHandle → FollowUp → Close
LLM: Ollama mistral:7b locale
Skill da creare: skill-langgraph/
```

### ARCH-002: 4-Layer RAG Context
```
Layer 1: ChromaDB locale (KB dealer + veicoli)
Layer 2: DuckDB storico interazioni
Layer 3: Memoria sessione (MEMORY.md)
Layer 4: Web real-time (AutoScout24 prezzi)
Skill da creare: skill-rag/
```

### ARCH-003: Scraping Pipeline EU
```
AutoScout24 DE/BE/NL/AT + Carapis
curl_cffi + Camoufox + proxy Tailscale WindTre
Skill da creare: skill-scraping/
```

### ARCH-004: VIN Intelligence
```
Vincario + NHTSA vPIC + vininfo EU WMI
Fraud detection pre-deal
Skill da creare: skill-vin/
```

---

## SKILL REGISTRY COMPLETO (target architettura finale)

| Skill | Layer | Fonte | Stato |
|-------|-------|-------|-------|
| `skill-argos` v3 | 3 | Custom ARGOS | ✅ Attivo |
| `skill-argos-debug` v1 | 3 | Custom ARGOS | ✅ Attivo |
| `skill-cove` v1 | 3 | Custom ARGOS | ✅ Attivo |
| `skill-deep-research` v1 | 3 | Custom ARGOS | ✅ Attivo |
| `gh-actions` v1 | 3 | Custom ARGOS | ✅ Attivo |
| `skill-sales-official` v1 | 2 | Anthropic Official | ⏳ F1-01 |
| `skill-data-official` v1 | 2 | Anthropic Official | ⏳ F1-02 |
| `skill-langgraph` v1 | 3 | Custom ARGOS | ⏳ ARCH-001 |
| `skill-rag` v1 | 3 | Custom ARGOS | ⏳ ARCH-002 |
| `skill-scraping` v1 | 3 | Custom ARGOS | ⏳ ARCH-003 |
| `skill-vin` v1 | 3 | Custom ARGOS | ⏳ ARCH-004 |

---

## METRICHE DI SUCCESSO PER FASE

| Fase | KPI | Target |
|------|-----|--------|
| F1 | Skill installate e testate | 2 skill operative |
| F2 | Lead pipeline attiva | 5+ dealer in sequenza |
| F3 | Deal pipeline | 2+ deal in negoziazione |
| F4 | Revenue mensile | €2.400+ (3 deal × €800) |
| ARCH | Automazione | <30min/lead da research a primo contatto |

---

*ARGOS Automotive CoVe 2026 | Roadmap v1.0 | S51 2026-03-14*
