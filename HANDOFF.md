# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 47 — 2026-03-13

---

## ⚡ STATO CORRENTE

**claude-mem**: ✅ Fix S46 confermato attivo. DB vuoto (expected post-fix — nuove sessioni catturate correttamente)
**Mario Orefice**: ⏳ PENDING invio WhatsApp — template pronto, finestra oggi 14:00-17:00
**Architettura S47**: ✅ `.taskmaster/` + OBJ-1/5 + fee calculator consegnati e testati

---

## 🎯 MARIO EXECUTION — P0

| Campo | Valore |
|---|---|
| Contatto | +393336142544 |
| Nome | Mario Orefice, Mariauto Srl |
| Personalità | IMPRENDITORE |
| Veicolo | BMW 330i 2020, 45.200 km, €27.800 |
| Fee | €800 success-only |
| ROI dealer | 247% (€1.980 margine netto) |
| Fattura svantaggiosa | ~€175 risparmio |
| Template | `docs/dev/mario_collection_message_session38.md` |
| Timing | 14:00-17:00 finestra ottimale |
| Conversione attesa | 65-75% |

**OBJ pre-caricati**: OBJ-2 IMPRENDITORE pronto (`src/marketing/objection_handler.py`)

---

## ✅ COMPLETATO SESSION 47

| Task | File | Note |
|---|---|---|
| `.taskmaster/` setup | `.taskmaster/tasks.yaml` + `AGENT.md` | Task YAML persistente cross-session |
| Objection handling OBJ-1/5 | `src/marketing/objection_handler.py` | 5 archetipi × 4 personality |
| Fee calculator | `tools/fee_calculator.py` | ROI dealer + WhatsApp snippet |

---

## 📊 BACKLOG ARCHITETTURALE

| Gap | Priorità | Stato |
|---|---|---|
| LangGraph orchestrator (8 nodi) | 🔴 ALTA | BACKLOG |
| Skill architecture `.claude/skills/` | 🔴 ALTA | BACKLOG |
| 4-layer context retrieval | 🟡 MEDIA | BACKLOG |

**Nostri vantaggi da NON toccare**: CoVe Engine v4, Ollama locale, Tailscale proxy

---

## 📂 FILE CRITICI

```
python/cove/cove_engine_v4.py              ← CoVe Engine (NON modificare)
python/cove/data/cove_tracker.duckdb       ← DB principale
src/marketing/dealer_personality_engine.py ← Agent framework
src/marketing/objection_handler.py         ← OBJ-1/5 (nuovo S47)
tools/fee_calculator.py                    ← Fee calc (nuovo S47)
.taskmaster/tasks.yaml                     ← Task tracking (nuovo S47)
.mcp.json                                  ← TENERLO VUOTO
~/.claude/claude_desktop_config.json       ← Config MCP attiva
```

---

## 🚀 PROSSIMA SESSIONE (S48)

```
Sessione 48 — ARGOS. Leggi HANDOFF.md.

STEP 1 — Mario follow-up:
  Verifica risposta Mario (+393336142544).
  Se positivo → registra €800 su DuckDB + log dealer_contacts.
  Se silenzio → OBJ-2 follow-up (objection_handler.py OBJ-2 IMPRENDITORE).
  Se obiezione → identifica OBJ code e usa objection_handler.py.

STEP 2 — Architettura:
  Prossimo gap da attaccare: LangGraph orchestrator adattato Ollama.
  Riferimento: .taskmaster/tasks.yaml ARCH-001.

STEP 3 — Nuovi lead:
  Cerca nuovi dealer target su AutoScout24 / Carapis se pipeline vuota.
```
