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

## 🎭 TEST ARCHETIPI — DA RIPRENDERE IN S53

**Stato test role play S52:**
- Round 1 ✅ — WA Day 1 GENERICO inviato (stesso per tutti, nessun archetipo pre-assunto)
- Round 2 ✅ — 3 risposte dealer raw analizzate → archetipi classificati correttamente:
  - [A] Matteo Mazzilli → PERFORMANTE (confidence 0.82)
  - [B] Mikael Faro → TECNICO (confidence 0.91)
  - [C] Giuseppe Orefice → RAGIONIERE (confidence 0.87)
- Round 3 ✅ — Risposte calibrate per archetipo
- Round 3 ❌ — Errore su IVA Orefice: detto "TD18 il commercialista capisce" → sbagliato
- **MEMORIZZATO**: regola IVA + regola fee fattura con dati normativi reali

**S53 — RIPRENDERE IL TEST DALL'INIZIO:**
- Messaggio Day 1 GENERICO → stesso testo per tutti
- Dealer risponde raw (nessuna etichetta archetipo)
- Agente analizza → classifica archetipo → risponde calibrato
- Includere obbligatoriamente scenario "mi fate fattura?" per testare il nuovo script
- Debrief finale con score

---

## 🚀 PROSSIMA SESSIONE (S53) — PROMPT COMPLETO

```
Sessione 53 — ARGOS. Leggi HANDOFF.md + ROADMAP.md (docs/dev/).
Sei CTO AI di ARGOS Automotive.

STATO S52:
- PM2 iMac riavviato ✅ (daemon :9191 OK)
- WA QR re-auth: ⚠️ HUMAN ACTION pendente — controlla Telegram @ArgosautomotivebotToken
- Lead batch 1: 5 dealer qualificati in docs/dev/leads_s52_batch1.md ✅
- gstack + skill-marketing-official ✅
- agent-sales aggiornato: protocollo fee (TD17, bonifico, no fattura) + IVA veicolo ✅
- Mario Day 7: ⏳ 2026-03-17 se silenzio

PRIORITY 0 — RICORDA: scansiona QR Telegram + WhatsApp (fallo subito se non fatto)

PRIORITY 1 — TEST ARCHETIPI (ripartire dall'inizio, sessione dedicata):
  Obiettivo: validare agent-sales prima di contattare dealer reali
  REGOLE TEST:
  - WA Day 1 GENERICO → stesso per tutti (nessun archetipo pre-assunto)
  - Dealer risponde raw → agente analizza risposta → classifica archetipo
  - Risposte calibrate per archetipo rilevato
  - Includere scenario "mi fate fattura?" per testare script fee TD17
  - Debrief finale con score pass/fail
  STATO PRECEDENTE (S52): Round 1-3 completati ma errore su IVA Orefice → ora corretto
  → Ricominciare dall'inizio con 3 nuovi dealer (o stessi personaggi, stesso script)

PRIORITY 2 — Mario Recovery Day 7 (se data ≥ 2026-03-17):
  agent-recovery → Recovery RAGIONIERE v3 → approvazione umana → agent-sales → invio

PRIORITY 3 — Outreach Batch 1 (SOLO dopo test archetipi superato):
  agent-sales → WA Day 1 Mazzilli (335 766 2842) + Prime Cars (371 417 5649)
  HUMAN-IN-THE-LOOP obbligatorio prima di inviare

PRIORITY 4 — skill-finance:
  .claude/skills/skill-finance/SKILL.md
  Comandi: /calcola-fee, /bonifico-template, /margine-veicolo, /pl-dealer

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
