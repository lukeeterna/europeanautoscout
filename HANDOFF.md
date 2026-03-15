# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 54 — 2026-03-15 (definitivo)

---

## ⚡ STATO CORRENTE (S54)

| Sistema | Stato | Note |
|---------|-------|------|
| CoVe Engine v4 | ✅ | Bayesian FACTORED, weights 0.35/0.25/0.20/0.20 |
| WA Daemon v2.1 | ✅ online :9191 | DBPool + prepared statements |
| WA Sessione daemon | ⚠️ QR richiesto | HUMAN ACTION prima del 2026-03-17 (Mario Day 7) |
| Telegram bot | ✅ | Token aggiornato, PM2 online |
| PM2 iMac | ✅ | argos-wa-daemon + argos-tg-bot online |
| Agent Team | ✅ S51 | 7 subagents in `.claude/agents/` |
| Skill Layer | ✅ S52 | gstack + skill-marketing-official + skill-sales + skill-data |
| CI/CD | ✅ | GitHub Actions verde |
| Mario Day 1 | ✅ INVIATO | 2026-03-13 ~12:00 |
| **Mario Recovery Day 7** | **⚠️ DOMANI** | **2026-03-17 — usa agent-recovery** |
| TF-IDF Classifier | ✅ S54 | 35 conv, 80% accuracy — TECNICO/RAGIONIERE eccellenti |
| Dataset v2 | ❌ | Da generare in S55 via Claude diretto |
| TTS Luca | 📋 pianificato | Qwen3-TTS-12Hz-1.7B-CustomVoice + ehiweb |

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

## 🎯 MARIO OREFICE — RECOVERY DAY 7 DOMANI

| Campo | Valore |
|-------|--------|
| Contatto | +393336142544 |
| Archetipo | RAGIONIERE (confidence 0.85) |
| Day 1 WA | ✅ INVIATO 2026-03-13 ~12:00 |
| **Day 7 WA** | **⏳ 2026-03-17 — DOMANI** |
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

## 📋 LEAD PIPELINE BATCH 1

| # | Dealer | Città | Archetipo | WA | Priority |
|---|--------|-------|-----------|-----|----------|
| 1 | Mazzilli Auto | Gravina (BA) | PERFORMANTE | 335 766 2842 | ★★★★★ |
| 2 | Prime Cars Italy | Mascalucia (CT) | TECNICO | 371 417 5649 | ★★★★★ |
| 3 | Campania Sport Car | Melito (NA) | RAGIONIERE | 328 7078112 | ★★★★☆ |
| 4 | Autosannino | Ponticelli (NA) | BARONE | 370 7125777 | ★★★☆☆ |
| 5 | Magicar | Palermo (PA) | NARCISO | 333 8358858 | ★★★☆☆ |

**Stato outreach**: in attesa di dataset v2 + test classifier PERFORMANTE prima di Mazzilli.
PrimeCars (TECNICO) e CampaniaSport (RAGIONIERE) già affidabili → pronti per WA Day 1.

---

## 🧠 DATASET & CLASSIFIER — STATO S54

### TF-IDF Classifier (operativo)
- File: `src/marketing/archetype_embedder.py`
- Index: `data/tfidf_index/` (35 documenti, vocab 1609 termini)
- Test S54: 4/5 (80%) — TECNICO ✅ RAGIONIERE ✅ PERFORMANTE ⚠️ (segnali deboli senza keywords esplicite)
- Hybrid: keyword first (conf≥0.5) → TF-IDF fallback

### Dataset status
- v1: `data/training/conversations_synthetic_v1.json` — 35 conv reali (campo total_conversations: 120 è SBAGLIATO)
- v2: DA GENERARE in S55 via Claude diretto
- Target v2: 200+ conversazioni, 10 archetipi × 5 OBJ × 4 context + overlap
- Metodologia: DiaSynth + CoT (da paper 2024) — qualità > quantità
- Dopo v2: rebuild TF-IDF index → PERFORMANTE migliorerà

### Deep Research S54 — Conclusioni
- **HuggingFace**: NO dataset automotive B2B italiano esistente → ARGOS è unico al mondo
- **Dataset utili da integrare**: `goendalf666/sales-conversations` (1K-10K, persuasion signals) + `DeepMostInnovations/saas-sales-conversations` (100K+, B2B objections)
- **Paper applicabili**: DiaSynth CoT (2024), AI-Salesman (2025), Persona-aware Salesperson (2025)
- **FranckyB GGUF Qwen3-TTS**: non su HF pubblico → verificare patreon.com

### Infrastruttura dataset — LEZIONI S54
- ❌ Ollama MacBook: binary incompatibile (macOS 11, richiede macOS 14)
- ❌ iMac Ollama: troppo lento (qwen2.5:7b e 3b entrambi >60s/token su x86_64)
- ❌ ChromaDB: incompatibile Python 3.13 (onnxruntime non ha wheel)
- ✅ TF-IDF (sklearn): funziona, leggero, efficace per 35-300 conv
- ✅ Claude diretto: qualità massima per generazione sintetica → usare in S55

---

## 🎙️ TTS LUCA — ARCHITETTURA (pianificata)

| Componente | Scelta | Note |
|-----------|--------|------|
| Modello TTS | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | Apache 2.0, IT nativo |
| Quantizzazione | GGUF Q4/Q5 FranckyB | Cerca su patreon.com |
| Voce | Luca (voice clone) | ~10s audio reference |
| Canale | ehiweb VoIP IT | numero IT dedicato |
| Alternativa TTS | `Qwen3-TTS-12Hz-0.6B-CustomVoice` | hardware leggero |

**Stack chiamata**: ehiweb → SIP/WebRTC → Qwen3-TTS → Luca parla → STT → agent-sales risponde

---

## 📂 FILE CRITICI

```
CoVe Engine:     src/cove/cove_engine_v4.py           ← NON modificare MAI
DB locale:       data/db/cove_tracker.duckdb
Agents:          .claude/agents/
Skills L3:       .claude/skills/skill-argos/
Lead Batch 1:    docs/dev/leads_s52_batch1.md
TF-IDF Index:    data/tfidf_index/                    ← NEW S54
Classifier:      src/marketing/archetype_embedder.py  ← NEW S54
Generator iMac:  tools/generate_dataset_imac.py       ← resume support
MCP config:      .mcp.json                            ← TENERLO VUOTO
```

---

## 🔴 PENDENTI OPERATIVI

| Task | Agente | Data | Note |
|------|--------|------|------|
| **QR WA daemon** | **HUMAN ACTION** | **OGGI** | Prima del Day 7 Mario |
| **Mario Recovery Day 7** | **agent-recovery** | **2026-03-17** | Testo v3 in questo file |
| Dataset v2 generazione | Claude S55 dedicata | 2026-03-15 | 200+ conv CoT quality |
| Integrazione HF datasets | S55 | dopo v2 | goendalf666 + DeepMostInnovations |
| Rebuild TF-IDF index | S55 | dopo v2 | con v1+v2 merged |
| WA Day 1 PrimeCars + CampaniaSport | agent-sales | S55/S56 | TECNICO + RAGIONIERE ok |
| WA Day 1 Mazzilli | agent-sales | dopo rebuild | PERFORMANTE ok dopo v2 |
| TTS Luca setup | S56 | — | Qwen3-TTS + ehiweb |

---

## 🚀 PROSSIMA SESSIONE (S55) — DATASET GENERATION DEDICATA

```
Sessione 55 — ARGOS Dataset Generation. Leggi HANDOFF.md.
Sei CTO AI di ARGOS Automotive. Questa sessione è DEDICATA alla generazione
del dataset sintetico v2 usando Claude direttamente.

CONTESTO:
- Ollama MacBook: ❌ incompatibile macOS 11 (binary richiede macOS 14)
- Ollama iMac: ❌ troppo lento (>60s/token anche 3b su x86_64)
- ChromaDB: ❌ incompatibile Python 3.13
- SOLUZIONE: generiamo il dataset direttamente qui con Claude → qualità massima
- TF-IDF index operativo con 35 conv v1 → rebuild dopo v2

PRIORITY 0 — Mario Recovery Day 7:
  Data: OGGI 2026-03-17 (potrebbe già essere oggi a seconda di quando leggi)
  Verifica data corrente → se ≥ 2026-03-17 → agent-recovery → invia testo v3 → HUMAN approva
  Testo v3 in HANDOFF.md sezione Mario Orefice

PRIORITY 1 — QR WA daemon (se non ancora fatto):
  HUMAN ACTION: scansiona QR WhatsApp daemon su Android (+393281536308)

PRIORITY 2 — Dataset v2 via Claude diretto:
  Genera 200+ conversazioni sintetiche dealer × archetipo × OBJ × context
  Metodologia: DiaSynth + Chain of Thought (paper 2024) — ogni conv ha reasoning esplicito

  STRUTTURA target per ogni conversazione:
  {
    "id": "ARCH-OBJ-CTX-NNN",
    "primary_archetype": "RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO|RELAZIONALE|CONSERVATORE|DELEGATORE|OPPORTUNISTA|VISIONARIO",
    "secondary_archetype": null,  // o archetipo overlap
    "context": "day1_cold|day1_objection|followup_interest|objection_deep",
    "obj_triggered": "OBJ-1|OBJ-2|OBJ-3|OBJ-4|OBJ-5",
    "dealer_message": "messaggio realistico WhatsApp dealer Sud Italia",
    "signals": ["segnale1", "segnale2"],
    "optimal_response": "risposta Luca calibrata (max 6 righe WA)",
    "trap_response": "risposta sbagliata da evitare",
    "why_trap": "perché è sbagliata per questo archetipo",
    "outcome_predicted": "PROCEED|PROCEED_SLOW|STALL|CONVERTED|NURTURE|CONDITIONAL"
  }

  REGOLE ASSOLUTE nei messaggi dealer:
  - Linguaggio italiano Sud Italia (Campania/Puglia/Sicilia), informale ma professionale
  - Messaggi BREVI (max 5-6 righe WhatsApp)
  - MAI menzionare CoVe/Claude/AI/Anthropic nelle risposte Luca
  - Luca = Luca Ferretti, ARGOS Automotive
  - Fee: €800-1.200 success-only
  - Documenti: DAT Fahrzeughistorie, Gutachten DEKRA/TÜV (NON CarFax EU)
  - Margine: specificare SEMPRE IVA inclusa/esclusa
  - Garanzia: solo garanzia costruttore UE (non Händlergarantie)

  ERRORI SISTEMICI DA EVITARE (dal test S53):
  - E1: MAI "CarFax EU" → usare "DAT Fahrzeughistorie / TÜV report"
  - E2: MAI margine senza IVA → specificare sempre inclusa/esclusa
  - E3: MAI Händlergarantie → solo garanzia costruttore UE
  - E4: Perito → offrire struttura buyer-commissiona
  - E5: "zero anticipi" → aggiungere clausola responsabilità pre-partenza

  PLAN generazione (fai in batch da 20 conv per non saturare contesto):
  Batch 1: RAGIONIERE × OBJ-1..5 × day1_cold + day1_objection (10 conv)
  Batch 2: RAGIONIERE × OBJ-1..5 × followup + objection_deep (10 conv)
  Batch 3: BARONE × OBJ-1..5 × tutti i context (20 conv)
  Batch 4: PERFORMANTE × OBJ-1..5 × tutti (20 conv) ← PRIORITÀ per classifier
  Batch 5: NARCISO × OBJ-1..5 × tutti (20 conv)
  Batch 6: TECNICO × OBJ-1..5 × tutti (20 conv)
  Batch 7: RELAZIONALE/CONSERVATORE/DELEGATORE/OPPORTUNISTA/VISIONARIO (40 conv)
  Batch 8: Overlap RAGIONIERE×CONSERVATORE, BARONE×DELEGATORE, etc. (30 conv)
  → TOTALE TARGET: 170 conv v2 + 35 conv v1 = 205 conv merged

  OUTPUT: scrivi direttamente su data/training/conversations_synthetic_v2.json
  Dopo ogni batch → test rapido classifier con 2-3 messaggi nuovi

PRIORITY 3 — Integrazione dataset HuggingFace:
  Download goendalf666/sales-conversations → estrai pattern obiezione → adatta a formato ARGOS
  Download DeepMostInnovations/saas-sales-conversations → seleziona subset B2B → adatta
  Scrivi script tools/integrate_hf_datasets.py

PRIORITY 4 — Rebuild TF-IDF + test finale:
  python3 src/marketing/archetype_embedder.py build --force
  Test su messaggi Mazzilli/PrimeCars/CampaniaSport
  Target accuracy: >90% su tutti gli archetipi

PRIORITY 5 — WA Day 1 PrimeCars + CampaniaSport (se accuracy >90%):
  agent-sales → testo calibrato TECNICO per PrimeCars
  agent-sales → testo calibrato RAGIONIERE per CampaniaSport
  HUMAN-IN-THE-LOOP obbligatorio prima di inviare

Fine sessione: aggiorna HANDOFF.md + MEMORY.md + commit + prompt S56
```

---

## 🔴 REGOLE CRITICHE IMMUTABILI

**OBJ codes**: OBJ-1=fornitori EU | OBJ-2=prezzo/fee | OBJ-3=tempo | OBJ-4=garanzie | OBJ-5=socio/titolare
**Archetipi**: RAGIONIERE | BARONE | PERFORMANTE | NARCISO | TECNICO | RELAZIONALE | CONSERVATORE | DELEGATORE | OPPORTUNISTA | VISIONARIO
**CoVe**: recommendation (MAI verdict) | DEALER_PREMIUM_THRESHOLD=0.75 | VIN_CHECK_THRESHOLD=0.60
**MCP**: `.mcp.json` SEMPRE VUOTO | config attiva: `~/.claude/claude_desktop_config.json`
**Fee fattura**: MAI "non possiamo fatturare" → "il bonifico è la soluzione più efficiente" (TD17 svantaggioso)
**IVA**: MAI semplificare con RAGIONIERE — spiegare regime margine come vantaggio strutturale ARGOS
