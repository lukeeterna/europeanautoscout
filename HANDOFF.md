# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 60 — 2026-03-17

---

## ⚡ STATO CORRENTE (S60 — 2026-03-17)

| Sistema | Stato | Note |
|---------|-------|------|
| Dataset v2 | ✅ | 1.319 conv totali — 2.7MB |
| SVM Classifier v1 (TF-IDF) | ✅ | 79.6% CV — in produzione |
| **DuckDB → SQLite** | ✅ COMPLETATO | WAL mode, multi-processo nativo |
| **Pipeline Salerno 8 dealer** | ✅ in SQLite | 8 dealer, tutti PENDING |
| **LLM Autonomo (Haiku 4.5)** | ✅ LIVE | Auto-genera + auto-valida + auto-invia |
| **OpenRouter** | ✅ $5 credito | API key "argos" in .env iMac |
| **Cost tracker** | ✅ | `/costi` su Telegram, tabella `llm_costs` |
| **Training corrections** | ✅ | Salva originale+corretto su `/modifica` |
| **Validatore sicurezza** | ✅ | Termini vietati, fee, lunghezza |
| **WA Business** | ✅ autenticato | Sessione `argos-business`, 328-1536308 |
| **tg-bot** | ✅ online | PM2, SQLite, Telegram funzionante |
| **wa-daemon** | ⏸️ PRONTO | Da avviare per ricevere risposte WA |
| **Landing page** | ✅ LIVE | https://argos-automotive.pages.dev |
| **Loghi ARGOS** | ✅ | Shield + Badge APPROVED + Seal CERTIFIED v4 |
| **Day 1** | ⏳ pronto | Avviare wa-daemon → /outreach SALERNO_001 |

---

## ✅ S60 — COMPLETATO

**Migrazione DuckDB → SQLite:**
- 4 file migrati + ecosystem.config.js + .env
- WAL mode attivo — multi-processo nativo
- `/status` mostra 8 dealer

**Pipeline LLM Autonoma:**
- Haiku 4.5 via OpenRouter genera risposte calibrate su archetipo
- Auto-approvazione con validatore sicurezza
- NEGATIVE → chiude dealer, zero risposta
- UNKNOWN → HOLD, intervento manuale
- SAFE → auto-invia con anti-ban sleep (90-720s)
- Il founder supervisiona da Telegram, può /rifiuta per bloccare
- Training corrections: ogni /modifica salva coppia originale→corretto
- Landing page live: https://argos-automotive.pages.dev (Cloudflare Pages)
- Loghi: Shield + Badge APPROVED™ + Seal CERTIFIED™ v4
- Marchi ampliati: BMW, Mercedes, Audi, Porsche, Land Rover (€25k-90k)

**Decisione founder:** "io non approvo, approvi tu" — sistema autonomo.

---

## 📋 Pipeline Salerno (8 dealer — in SQLite)

| ID | Dealer | Città | Stock | Score | WA | Archetipo |
|----|--------|-------|-------|-------|-----|-----------|
| SALERNO_001 | Autovanny Group | Eboli | 58 | 8.5/10 | 335-5250129 ✅ | NARCISO |
| SALERNO_002 | FC Luxury Car Center | S.Egidio MA | 27 | 8.0/10 | 342-5036799 ✅ | BARONE |
| SALERNO_003 | Ferrauto Srl | S.V.Torio | 68 | 8.0/10 | 081-5187350 📞 | BARONE |
| SALERNO_004 | A.B. Motors | Montecorvino P. | 49 | 7.5/10 | 335-6418105 ✅ | RELAZIONALE |
| SALERNO_005 | Auto Genova | Salerno | 117 | 7.0/10 | 329-4357882 ✅ | RAGIONIERE |
| SALERNO_006 | Autoluce Srl | Baronissi | 26 | 7.0/10 | 089-953608 📞 | BARONE |
| SALERNO_007 | Tirrenia Auto | Cava de' Tirreni | 51 | 7.0/10 | 089-2962937 📞 | DELEGATORE |
| SALERNO_008 | Gruppo Emme | Battipaglia | 53 | 6.5/10 | 347-6832587 ✅ | TECNICO |

Ordine invio Day 1: SALERNO_001, SALERNO_002 (max 2 oggi)

---

## 🏛️ IDENTITÀ E BUSINESS MODEL

**Brand**: ARGOS Automotive | **Persona**: Luca Ferretti
**Business**: B2B vehicle scouting EU→IT | **Fee**: €800-1.200 success-fee
**Target**: Concessionari family-business Sud Italia, 30-80 auto

---

## 🧠 ARCHITETTURA (aggiornata S60)

```
CLASSIFICATORE: Claude (training) → Dataset → SVM (TF-IDF) → locale
RESPONSE GEN:   Haiku 4.5 via OpenRouter → auto-valida → auto-invia
REVIEW:         Claude Code periodico → profila dealer → migliora prompt
```

---

## 🖥️ INFRASTRUTTURA

**iMac**: `ssh gianlucadistasi@192.168.1.2` | Python 3.13 | Node v22.14.0
**DB Pipeline**: `~/Documents/app-antigravity-auto/dealer_network.sqlite` (SQLite WAL)
**DB CoVe**: `dealer_network.duckdb` (DuckDB, single-process)
**OpenRouter**: Haiku 4.5, $5 credito, key in .env
**PM2**: tg-bot ONLINE, wa-daemon PRONTO

---

## 📂 FILE CRITICI

```
CoVe Engine:        src/cove/cove_engine_v4.py                 ← NON modificare MAI (DuckDB)
Response analyzer:  wa-intelligence/response-analyzer.py        ← LLM autonomo (S60)
Telegram handler:   wa-intelligence/telegram-handler.py         ← /costi + training (S60)
WA daemon:          wa-intelligence/wa-daemon.js                ← SQLite (S60)
Ecosystem:          wa-intelligence/ecosystem.config.js          ← OpenRouter env (S60)
Review tool:        tools/review_conversations.py               ← NUOVO S60
Pipeline loader:    tools/salerno_pipeline_loader.py            ← SQLite (S60)
WA sender:          ~/Documents/app-antigravity-auto/wa-sender/send_message.js
.env iMac:          ~/Documents/app-antigravity-auto/wa-intelligence/.env
```

---

## 🔴 REGOLE CRITICHE IMMUTABILI

```
Fee:            €1.000 (MAI €400) | "bonifico più efficiente" (MAI "non fatturiamo")
MAI:            CoVe/RAG/Claude/Anthropic/AI/embedding nei messaggi dealer
MAI:            "CarFax EU" → "report DAT" | "Händlergarantie" → "garanzia costruttore UE"
NEGATIVE:       NON rispondere, chiudere dealer, porta aperta
Lead silenti:   NON fare follow-up — passare al prossimo
Founder:        NON vuole approvare — sistema autonomo
```

---

## 🚀 PROSSIMA SESSIONE (S61) — PROMPT COMPLETO

```
Sessione 61 — ARGOS Avvio wa-daemon + Day 1 + sistema autonomo live.
Leggi HANDOFF.md prima di qualsiasi altra azione.
Sei CTO AI di ARGOS Automotive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
S60 COMPLETATO:
- SQLite migrazione done, /status 8 dealer
- LLM autonomo: Haiku genera + valida + auto-invia
- OpenRouter $5, cost tracker, training corrections
- Landing live: https://argos-automotive.pages.dev
- Loghi ARGOS: Shield + APPROVED + CERTIFIED
- Founder NON approva — sistema autonomo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIORITY 0 — Avvia wa-daemon
  ssh gianlucadistasi@192.168.1.2
  export PATH=/usr/local/bin:$HOME/.npm-global/bin:$PATH
  cd ~/Documents/app-antigravity-auto/wa-intelligence
  pm2 start ecosystem.config.js --only argos-wa-daemon
  Verifica: pm2 list (entrambi online), health check 127.0.0.1:9191

PRIORITY 1 — Invio Day 1
  /outreach SALERNO_001  (Autovanny, Eboli, NARCISO, 8.5/10)
  /outreach SALERNO_002  (FC Luxury, S.Egidio, BARONE, 8.0/10)
  Anti-ban: 90-720s sleep. Max 2 dealer oggi.

PRIORITY 2 — Monitoraggio
  Il sistema è autonomo. Quando dealer rispondono:
  - Haiku genera → validatore → auto-invia
  - Founder riceve notifica Telegram (può /rifiuta)
  - UNKNOWN/UNSAFE → HOLD su Telegram

  Claude Code review: tools/review_conversations.py
  Cost check: /costi su Telegram

INFRA:
  iMac SSH: ssh gianlucadistasi@192.168.1.2
  WA Business: autenticato, sessione argos-business
  DB: dealer_network.sqlite (WAL mode)
  OpenRouter: $5 credito, Haiku 4.5

Fine S61: HANDOFF + MEMORY + commit
```
