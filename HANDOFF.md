# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 52 — 2026-03-14 (definitivo)

---

## ⚡ STATO CORRENTE (S52)

| Sistema | Stato | Note |
|---------|-------|------|
| CoVe Engine v4 | ✅ | Bayesian FACTORED, weights 0.35/0.25/0.20/0.20 |
| WA Daemon v2.1 | ✅ online :9191 | DBPool + prepared statements |
| WA Sessione daemon | ⚠️ QR richiesto | HUMAN ACTION: controlla Telegram @ArgosautomotivebotToken → scansiona QR con Android (+393281536308 Very Mobile) |
| Telegram bot | ✅ | Token aggiornato, PM2 online |
| PM2 iMac | ✅ riavviato S52 | argos-wa-daemon + argos-tg-bot online |
| Agent Team | ✅ S51 | 7 subagents in `.claude/agents/` |
| Skill Layer 2 | ✅ S52 | skill-sales-official + skill-data-official + **gstack** + **skill-marketing-official** |
| Skill Layer 3 | ✅ | skill-argos v3, skill-cove, skill-deep-research, gh-actions |
| CI/CD | ✅ | GitHub Actions verde |
| Mario Day 1 | ✅ INVIATO | 2026-03-13 ~12:00 |
| Mario Recovery Day 7 | ⏳ | 2026-03-17 se silenzio — usa agent-recovery |
| Lead Batch 1 | ✅ S52 | 5 dealer qualificati → `docs/dev/leads_s52_batch1.md` |

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

## 📋 LEAD PIPELINE BATCH 1 — S52

**File**: `docs/dev/leads_s52_batch1.md` (dati reali da WebSearch)

| # | Dealer | Città | Archetipo | OBJ | WA | Priority |
|---|--------|-------|-----------|-----|----|----------|
| 1 | Mazzilli Auto | Gravina (BA) | PERFORMANTE | OBJ-3/2 | 335 766 2842 | ★★★★★ |
| 2 | Prime Cars Italy | Mascalucia (CT) | TECNICO | OBJ-1/4 | 371 417 5649 | ★★★★★ |
| 3 | Campania Sport Car | Melito (NA) | RAGIONIERE | OBJ-2/4 | 328 7078112 | ★★★★☆ |
| 4 | Autosannino | Ponticelli (NA) | BARONE | OBJ-5/1 | 370 7125777 | ★★★☆☆ |
| 5 | Magicar | Palermo (PA) | NARCISO | OBJ-4/2 | 333 8358858 | ★★★☆☆ |

**Prossimo step**: agent-sales prepara WA Day 1 per Mazzilli + Prime Cars Italy

---

## ✅ COMPLETATO SESSION 52 — LEAD PIPELINE + SKILLS

| Task | File/Path | Note |
|------|-----------|------|
| PM2 restart iMac | SSH → pm2 start ecosystem.config.js | argos-wa-daemon + argos-tg-bot online |
| QR server avviato | :8765 attivo | QR inviato su Telegram — HUMAN ACTION scan |
| gstack skill | `.claude/skills/gstack/` | CEO/Eng/QA cognitive roles |
| skill-marketing-official | `.claude/skills/skill-marketing-official/` | /draft-content, /email-sequence, /brand-review, /campaign-plan |
| configs/CLAUDE.md aggiornato | — | Skill registry + task log aggiornati |
| Lead Batch 1 | `docs/dev/leads_s52_batch1.md` | 5 dealer reali, Campania/Puglia/Sicilia |
| ROADMAP.md aggiornato | `docs/dev/ROADMAP.md` | S52 completato, F2 avanzata |

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
               .claude/skills/gstack/              ← NEW S52
               .claude/skills/skill-marketing-official/ ← NEW S52
Lead Batch 1:  docs/dev/leads_s52_batch1.md       ← NEW S52
Roadmap:       docs/dev/ROADMAP.md
MCP config:    .mcp.json                          ← TENERLO VUOTO
Global MCP:    ~/.claude/claude_desktop_config.json
```

---

## 🚀 PROSSIMA SESSIONE (S53) — PROMPT COMPLETO

```
Sessione 53 — ARGOS. Leggi HANDOFF.md + ROADMAP.md (docs/dev/).
Sei CTO AI di ARGOS Automotive. Lead pipeline batch 1 disponibile.

STATO S52:
- PM2 iMac riavviato ✅ (daemon :9191 OK)
- WA QR re-auth: ⚠️ HUMAN ACTION pendente — controlla Telegram @ArgosautomotivebotToken
- Lead batch 1: 5 dealer qualificati in docs/dev/leads_s52_batch1.md ✅
- Nuove skills: gstack + skill-marketing-official ✅
- Mario Day 7: ⏳ 2026-03-17 se silenzio

PRIORITY 1 — WA QR re-auth (se non fatto):
  Controlla Telegram per QR → scansiona con Android (Very Mobile +393281536308)
  Poi verifica: curl http://192.168.1.12:9191/health

PRIORITY 2 — Mario Recovery Day 7 (se data ≥ 2026-03-17):
  agent-recovery → Recovery RAGIONIERE v3 → approvazione umana → agent-sales → invio
  Testo approvato in HANDOFF.md sezione Mario

PRIORITY 3 — Outreach Batch 1 (max 2 dealer/giorno):
  agent-sales → WA Day 1 per Mazzilli Auto (335 766 2842) + Prime Cars Italy (371 417 5649)
  Vedi docs/dev/leads_s52_batch1.md per pitch personalizzato per archetipo
  HUMAN-IN-THE-LOOP: mostra bozza WA → attendi OK → invia

PRIORITY 4 — skill-finance:
  Crea .claude/skills/skill-finance/SKILL.md
  Comandi: /calcola-fee, /td17-template, /pl-dealer, /margine-veicolo
  Basato su business rules ARGOS (TD17/18/19, reverse charge)

PRIORITY 5 — Pipeline review dashboard:
  skill-data-official → /build-dashboard → HTML Chart.js
  Dati: cove_tracker.duckdb + leads_s52_batch1.md

ROADMAP corrente: docs/dev/ROADMAP.md — FASE 2 in corso
Fine sessione: aggiorna HANDOFF.md + ROADMAP.md + MEMORY.md + commit
```

---

## 🔴 PENDENTI OPERATIVI

| Task | Agente | Data |
|------|--------|------|
| WA QR re-auth daemon | HUMAN ACTION | Appena Telegram ricevuto |
| Mario Recovery Day 7 | agent-recovery | 2026-03-17 |
| WA Day 1 Mazzilli + Prime Cars | agent-sales | S53 (max 2/giorno) |
| skill-finance | — | S53 |
| Pipeline dashboard | skill-data-official | S54 |
