# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 46 — 2026-03-12

---

## ⚡ STATO CORRENTE

**claude-mem**: ✅ FIX DEFINITIVO APPLICATO — richiede restart Claude Code
**Mario Orefice**: ⏳ PENDING execution — template pronto, window critica
**Architettura**: Gap identificati da analisi sales-agent-enterprise

---

## 🔧 CLAUDE-MEM FIX (Session 46 — DEFINITIVO)

**Root cause**: `.mcp.json` ridefiniva claude-mem → conflitto con `~/.claude/claude_desktop_config.json`
**Fix**: `.mcp.json` svuotato `{"mcpServers":{}}` — config attiva solo da global
**Evidenza**: FLUXION (stesso PC, no `.mcp.json`) funziona perfettamente
**REGOLA**: Non aggiungere MAI claude-mem a `.mcp.json`

---

## 🎯 MARIO EXECUTION

| Campo | Valore |
|---|---|
| Contatto | +393336142544 |
| Nome | Mario Orefice, Mariauto Srl |
| Personalità | IMPRENDITORE |
| Response time | 1-4h |
| Conversione attesa | 65-75% |
| Veicolo | BMW 330i 2020, 45.200 km |
| Opportunità | €800 success fee |
| Vantaggio | Fattura Svantaggiosa €150-200 |
| Template | `mario_collection_message_session38.md` |
| Agent competency | 85/100 ✅ validato |

---

## 📊 GAP ARCHITETTURALI (analisi sales-agent-enterprise)

| Gap | Priorità | Note |
|---|---|---|
| LangGraph orchestrator (8 nodi) | 🔴 ALTA | Conversazione autonoma end-to-end |
| Skill architecture `.claude/skills/` | 🔴 ALTA | Prerequisito agent autonomy |
| `.taskmaster/` task management | 🟡 MEDIA | YAML persistente vs handoff manuale |
| Objection handling OBJ-1/5 | 🟡 MEDIA | Escalation Telegram automatica |
| Fee calculator standalone | 🟡 MEDIA | ROI dealer per veicolo |
| 4-layer context retrieval | 🟡 MEDIA | Static→DuckDB→ChromaDB→episodic |

**Nostri vantaggi da NON toccare**: CoVe Engine v4, Ollama locale, Tailscale proxy

---

## 🚀 PROSSIMA SESSIONE (S47)

```
Sessione 47 — ARGOS. Leggi HANDOFF.md.
STEP 1: search("mario orefice") → valida claude-mem post-restart
STEP 2: Mario execution → invia WhatsApp +393336142544 con template session38
STEP 3: Proponi piano .taskmaster/ + objection handling OBJ-1/5
```

---

## 📂 FILE CRITICI

```
python/cove/cove_engine_v4.py              ← CoVe Engine (NON modificare)
python/cove/data/cove_tracker.duckdb       ← DB principale
src/marketing/dealer_personality_engine.py ← Agent framework
.mcp.json                                  ← TENERLO VUOTO
~/.claude/claude_desktop_config.json       ← Config MCP attiva
```
