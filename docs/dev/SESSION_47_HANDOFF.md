# SESSION 47 HANDOFF

**Data**: 2026-03-12
**Incoming from**: Session 46 (claude-mem fix definitivo + analisi sales-agent-enterprise)
**Working directory**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`

---

## 🚨 AZIONE IMMEDIATA: RESTART CLAUDE CODE

Il fix claude-mem è stato applicato. **Riavviare Claude Code prima di qualsiasi operazione.**

**Cosa è stato fatto**:
- `.mcp.json` svuotato (era duplicato del global config → causava conflitto)
- Config funzionante: `~/.claude/claude_desktop_config.json` (stesso setup FLUXION che funziona)
- Root cause definitivo: doppia definizione claude-mem = conflitto MCP

---

## ✅ SESSION 46 COMPLETATA

### 1. CLAUDE-MEM FIX DEFINITIVO
- **Root cause**: `.mcp.json` progetto aveva claude-mem duplicato rispetto a `~/.claude/claude_desktop_config.json`
- **Evidenza**: Progetto FLUXION (stesso PC) funziona → NON ha `.mcp.json`, usa solo config globale
- **Fix applicato**: `.mcp.json` svuotato → `{"mcpServers": {}}`
- **Status**: Richiede restart Claude Code per attivazione

### 2. ANALISI SALES-AGENT-ENTERPRISE (29 file)
File ZIP analizzato: `/Users/macbook/Downloads/files (3).zip`
Confronto completo eseguito con nostro modello attuale.

**Gap critici identificati**:
| Gap | Priorità |
|---|---|
| Nessun orchestratore (LangGraph 8 nodi) | 🔴 ALTA |
| Nessuna skill architecture (.claude/skills/) | 🔴 ALTA |
| Nessun task management (.taskmaster/) | 🟡 MEDIA |
| Objection handling non codificato (OBJ-1/5) | 🟡 MEDIA |
| 4-layer context retrieval mancante | 🟡 MEDIA |
| Fee calculator standalone assente | 🟡 MEDIA |

**Nostri vantaggi vs incoming**:
- ✅ CoVe Engine v4 (Bayesian FACTORED) — non esiste nel loro sistema
- ✅ Ollama locale (zero costo) vs loro DeepSeek API
- ✅ Cultural protocols (Nord/Centro/Sud Italia)
- ✅ Conversion rate % per persona con timeline decisione

---

## 🎯 PRIORITÀ SESSION 47

### PRIORITÀ 1: Validare claude-mem post-restart
```
search("Session 46 sales agent analisi")
search("mario orefice BMW 330i")
```
Se funziona → ✅ problema risolto definitivamente.

### PRIORITÀ 2: Mario execution (window critica)
- **Target**: +393336142544 (Mario Orefice, Mariauto Srl)
- **Personalità**: IMPRENDITORE (WhatsApp preferred, 1-4h response)
- **Revenue**: €800 success fee
- **Veicolo**: BMW 330i 2020, 45.200 km, €27.800
- **Vantaggio**: Fattura Svantaggiosa €150-200
- **Template**: `mario_collection_message_session38.md`

### PRIORITÀ 3: Decisione architetturale
Sulla base dell'analisi sales-agent-enterprise, decidere cosa adottare:
- **Fast win**: `.taskmaster/` + `AGENT.md` (struttura task persistente)
- **Medium**: Objection handling codificato (OBJ-1/5)
- **Long term**: LangGraph orchestrator adattato a Ollama

---

## 📂 FILE CHIAVE

```
.mcp.json                                    → SVUOTATO (fix claude-mem)
~/.claude/claude_desktop_config.json         → CONFIG ATTIVA claude-mem
docs/dev/SESSION_47_HANDOFF.md              → questo file
mario_collection_message_session38.md        → template WhatsApp Mario
dealer_personality_engine.py                → agent framework
python/cove/cove_engine_v4.py               → CoVe engine (NON toccare)
```

---

## 📊 STATO DATABASE

```
dealer_contacts: Mario Orefice (COLLECTION_MARKET_VALIDATED)
                 Agent insights loggati (Session 45)
cove_tracker.duckdb: operativo
```
