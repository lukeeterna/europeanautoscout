# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 48 — 2026-03-13 (definitivo)

---

## ⚡ STATO CORRENTE

**claude-mem**: ✅ Fix S46 confermato attivo.
**Mario Orefice**: ✅ WA DAY 1 INVIATO — 2026-03-13 ~12:00 | Account: +393281536308 (Very Mobile) | Message ID: `true_227002057543819@lid_3EB07A584C107FB7661C17` | ACK: 0
**WhatsApp stack**: ✅ whatsapp-web.js su iMac | sessione `wa-sender` persistente in `wa-sender/.wwebjs_auth/`
**CI/CD**: ✅ CI verde su GitHub Actions | CD deploy iMac + Day7 cron attivo
**WA Intelligence**: ✅ DEPLOYATO S49 | PM2 online: argos-wa-daemon + argos-tg-bot | LaunchAgent scheduler ogni 5min | health ✅ http://192.168.1.12:9191
**WA Daemon sessione**: ⚠️ RICHIEDE RE-AUTH QR — usa `send_qr_server.js` da `wa-sender/`, poi copia session in `wa-intelligence/.wwebjs_auth/` | Telegram alert inviato
**Skill argos**: ✅ v3 ATTIVA in `.claude/skills/skill-argos/` | v2 backup in `skill-argos-v2-backup/`
**OUTREACH REVIEW**: ⚠️ Msg Day1 Mario troppo diretto per RAGIONIERE — Recovery Day7 corretto pronto
**Secrets GitHub**: ✅ `IMAC_HOST=100.79.153.61` | `IMAC_USER` | `IMAC_SSH_KEY` (ED25519 gh-deploy)
**SSH deploy key**: ✅ `~/.ssh/gh_deploy_argos` — autorizzata su iMac
**Skills**: ✅ `skill-argos` v3 (attiva) + `skill-argos-debug` + `gh-actions` | v2 backup in `skill-argos-v2-backup/`
**gh CLI**: ✅ `~/bin/gh` v2.65.0 | `export PATH=$HOME/bin:$PATH`
**PM2 PATH iMac**: `export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:$PATH`

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

**Trigger risposta**: silenzio >48h → Recovery WA Day 7 (2026-03-17) — NON email

**Recovery Day 7 APPROVATO (RAGIONIERE v3):**
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

## ✅ COMPLETATO SESSION 48

| Task | File | Note |
|---|---|---|
| WA Day 1 Mario inviato | `wa-sender/send_verified.js` su iMac | ACK 0, Message ID confermato, numero verificato |
| WhatsApp stack operativo | `wa-sender/.wwebjs_auth/session-argosautomotive/` | Sessione Very Mobile +393281536308 |
| Skill argos-outreach v2 | `.claude/skills/skill-argos/SKILL.md` | QR via HTTP, proof checklist, path fix |
| Skill argos-wa-debug | `.claude/skills/skill-argos-debug/SKILL.md` | D1→D6 receipt verification |
| Skill gh-actions | `.claude/skills/gh-actions/SKILL.md` | setup SSH key, secrets, troubleshooting |
| CI workflow verde | `.github/workflows/ci.yml` | ubuntu-22.04, 3 test E2E passati |
| CD workflow | `.github/workflows/cd.yml` | appleboy/ssh-action + Day7 cron |
| SSH deploy key | `~/.ssh/gh_deploy_argos` | ED25519, autorizzata su iMac |
| GitHub Secrets | repo settings | IMAC_HOST/USER/SSH_KEY configurati |
| gh CLI | `~/bin/gh` v2.65.0 | autenticato lukeeterna |
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
| Skill architecture `.claude/skills/` | 🔴 ALTA | ✅ DONE S48 |
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

## ✅ COMPLETATO SESSION 49

| Task | Stato | Note |
|---|---|---|
| Skill v3 attiva | ✅ | `skill-argos-v3` → `skill-argos` | v2 backup |
| WA Intelligence deploy | ✅ | PM2 online, LaunchAgent scheduler ogni 5min |
| Telegram bot | ✅ | Token configurato, alert sessione scaduta inviato |
| deploy.sh bug fix | ✅ | REMOTE_BASE iMac path + PM2/npm PATH fix |
| Mario Day 1 status | ⏳ | Inviato 2026-03-13, silenzio → Recovery Day 7 il 2026-03-17 |
| WA Daemon QR auth | ⚠️ | HUMAN ACTION: ri-autenticare daemon (vedi S50) |

---

## 🚀 PROSSIMA SESSIONE (S50)

```
Sessione 50 — ARGOS. Leggi HANDOFF.md.

STEP 1 — WA Daemon re-auth (PRIORITÀ):
  Il daemon argos-wa-daemon gira su PM2 ma ha sessione separata da wa-sender.
  Sessione daemon: ~/Documents/app-antigravity-auto/wa-intelligence/.wwebjs_auth/
  Sessione wa-sender: ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/

  OPZIONE A (preferita): Avvia QR server da wa-intelligence dir, scansiona.
    ssh imac "export PATH=... && cd ~/Documents/app-antigravity-auto/wa-intelligence && node ../wa-sender/send_qr_server.js"
    open http://192.168.1.12:8765 → scansiona con Android

  OPZIONE B: Copia sessione da wa-sender a wa-intelligence:
    ssh imac "cp -r ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/ ~/Documents/app-antigravity-auto/wa-intelligence/.wwebjs_auth/"
    pm2 restart argos-wa-daemon

STEP 2 — Mario Day 7 Recovery (2026-03-17):
  Se silenzio da Mario al 2026-03-17 → invia Recovery Day 7 RAGIONIERE (testo in HANDOFF sopra).
  Approvazione Telegram PRIMA di ogni invio.
  Canale: WhatsApp (NON email — aggiornato da HANDOFF S48).

STEP 3 — Mario risposta (se ha risposto):
  Se positivo → registra €800 pipeline su DuckDB dealer_network.duckdb.
  Se obiezione → skill argos [E] PERSONA PROTOCOL.

STEP 4 — Nuovi lead se pipeline vuota:
  AutoScout24 / Carapis dealer target Sud Italia.
```
