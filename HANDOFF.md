# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 48 — 2026-03-13

---

## ⚡ STATO CORRENTE

**claude-mem**: ✅ Fix S46 confermato attivo.
**Mario Orefice**: ✅ WA DAY 1 INVIATO — 2026-03-13 ~12:00 | Account: +393281536308 (Very Mobile) | Message ID: `true_227002057543819@lid_3EB07A584C107FB7661C17` | ACK: 0
**WhatsApp stack**: ✅ whatsapp-web.js su iMac | sessione `argosautomotive` persistente in `wa-sender/.wwebjs_auth/`
**CI/CD**: ✅ `.github/workflows/ci.yml` + `cd.yml` | 3 test E2E passati | **PENDING: secrets IMAC_HOST/USER/KEY + SSH key deploy**
**Skills**: ✅ `argos-outreach-automation` v2 + `argos-wa-debug` + `gh-actions`
**gh CLI**: ✅ `~/bin/gh` v2.65.0 autenticato (lukeeterna)

---

## 🎯 MARIO OREFICE — SEQUENZA ATTIVA

| Campo | Valore |
|---|---|
| Contatto | +393336142544 |
| Nome | Mario Orefice, Mariauto Srl |
| Personalità | RAGIONIERE (confidence 0.85) |
| Veicolo | BMW 330i G20 2020, km 45.200 (LOCKED), €27.800 franco DE |
| Margine dealer | €3.100 netto dopo fee |
| Fee | €800 success-only |
| Day 1 WA | ✅ INVIATO 2026-03-13 ~12:00 | ACK 0 |
| Day 7 Email | ⏳ 2026-03-17 — se silenzio |
| Day 12 WA | ⏳ 2026-03-22 — follow-up finale |

**Trigger risposta**: silenzio >48h → Email Day 7 (2026-03-17)

---

## ✅ COMPLETATO SESSION 48

| Task | File | Note |
|---|---|---|
| WA Day 1 Mario inviato | `wa-sender/send_verified.js` su iMac | ACK 0, Message ID confermato |
| WhatsApp stack operativo | `wa-sender/.wwebjs_auth/session-argosautomotive/` | Sessione Very Mobile +393281536308 |
| Skill argos-outreach v2 | `.claude/skills/skill-argos/SKILL.md` | QR via HTTP, proof checklist, path fix |
| Skill argos-wa-debug | `.claude/skills/skill-argos-debug/SKILL.md` | D1→D6 receipt verification |
| CLAUDE.md skill rule | `configs/CLAUDE.md` | Framework ufficiale Anthropic `.claude/skills/` |

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

## 🚀 PROSSIMA SESSIONE (S49)

```
Sessione 49 — ARGOS. Leggi HANDOFF.md.

STEP 1 — Mario risposta:
  Verifica se Mario ha risposto al WA Day 1 (inviato 2026-03-13).
  Se positivo → registra €800 pipeline su DuckDB + log dealer_contacts.
  Se obiezione → skill argos-outreach-automation [E] PERSONA PROTOCOL (RAGIONIERE).
  Se silenzio al 2026-03-17 → Email Day 7 via skill [B] EMAIL PROTOCOL.

STEP 2 — WA sender persistente su iMac:
  Configurare LaunchAgent o cron su iMac per riavvio automatico send_verified.js
  se il processo muore (iMac sempre acceso = server persistente).
  ssh gianlucadistasi@192.168.1.12 — sessione argosautomotive già attiva.

STEP 3 — Nuovi lead:
  Pipeline vuota dopo Mario → cerca dealer target AutoScout24 / Carapis.
  Riferimento: .taskmaster/tasks.yaml ARCH-001 LangGraph orchestrator.
```
