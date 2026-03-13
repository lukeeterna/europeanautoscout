# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 49 — 2026-03-13 (definitivo)

---

## ⚡ STATO CORRENTE (aggiornato S50 fine)

**claude-mem**: ✅ Fix S46 confermato attivo.
**Mario Orefice**: ✅ WA DAY 1 INVIATO — 2026-03-13 ~12:00 | silenzio → Recovery Day 7 il 2026-03-17 se nessuna risposta
**WhatsApp stack**: ✅ whatsapp-web.js su iMac | sessione `wa-sender` persistente in `wa-sender/.wwebjs_auth/`
**CI/CD**: ✅ CI verde su GitHub Actions | CD deploy iMac + Day7 cron attivo
**WA Intelligence**: ✅ v2.1 ONLINE S50 | PM2 online: argos-wa-daemon + argos-tg-bot | health ✅ http://192.168.1.12:9191
**WA Daemon sessione**: ⚠️ RICHIEDE QR RE-AUTH — basta scansionare QR una volta con Android
**Telegram token**: ✅ AGGIORNATO S50 — `8691360619:AAG_R9bKLtAtRuMS5VD-AP7E-CKt_o-xOmA` in `.env` iMac
**Codebase fixes S50**: ✅ T-01..T-06 completati — DBPool, OBJ canonici, PersonaEngine, weights, datetime, zombie files
**Skills**: ✅ `skill-argos` v3 + `skill-argos-debug` + `gh-actions` + `skill-deep-research` + `skill-cove`
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

## ✅ COMPLETATO SESSION 50 — CRISIS RECOVERY

| Task | Stato | Note |
|---|---|---|
| STEP 0 — Telegram token iMac | ✅ | `8691360619:AAG_R9...` aggiornato in .env + `pm2 restart argos-tg-bot` |
| T-01 — Zombie files eliminati | ✅ | `cove_quantum_integration.py` + `cove_neural_crisis_prevention.py` → DELETE |
| T-02 — cove_engine_v4.py fix | ✅ | Import path `_HERE` + `datetime.now(timezone.utc)` + Weights 0.35/0.25/0.20/0.20 |
| T-03 — wa-daemon.js rewrite | ✅ | DBPool (duckdb npm) + prepared statements `?` + MessageQueue anti-ban | v2.1 online |
| T-04 — Schema personalità unificato | ✅ | `objection_handler.py` → OBJ codes canonici + 5 archetipi | `PersonaEngine` in `dealer_personality_engine.py` |
| T-05 — Keyword false positive fix | ✅ | `vediamo` → rimosso da POSITIVE | `PersonaEngine`+`ObjectionLibrary` aggiunti a `response-analyzer.py` |
| T-06 — Deploy + health check | ✅ | v2.1 online — `"status":"OK"` su :9191 | Schema DB verificato da log |
| WA Daemon QR auth | ⚠️ | HUMAN ACTION: scansionare QR una volta per ripristinare sessione WA |
| Mario Day 7 Recovery | ⏳ | 2026-03-17 — se silenzio → Recovery RAGIONIERE v3 (testo in §MARIO OREFICE) |

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

## 🔴 CRITICAL ISSUES TROVATI — DEEP RESEARCH S49

Vedi analisi completa sotto. Issues prioritari da fixare in S50:

| # | File | Issue | Severità |
|---|---|---|---|
| 1 | `wa-daemon.js` | SQL injection via string interpolation in tutte le query | 🔴 CRITICO |
| 2 | `wa-daemon.js` | `dbExec` via `python3 -c` — lento, fragile, causa schema errors | 🔴 CRITICO |
| 3 | Schema OBJ codes | `objection_handler.py` OBJ-1=prezzo vs `response-analyzer.py` OBJ-1=competition — INVERTITI | 🔴 CRITICO |
| 4 | Schema personalità | 3 sistemi incompatibili: `personality_engine` (4 tipi), `response-analyzer` (RAGIONIERE/BARONE), `objection_handler` (IMPRENDITORE) | 🔴 CRITICO |
| 5 | `cove_engine_v4.py` | Import paths `python.cove.*` wrong — file è in `src/cove/`, non funziona da enterprise dir | 🔴 CRITICO |
| 6 | `cove_quantum_integration.py` | File "quantum" AI-generated buzzword, mai integrato, numpy inutile — DELETE | 🟡 MEDIO |
| 7 | `response-analyzer.py` | False positive "vediamo" → POSITIVE (in IT = scetticismo), "aspetta" → OBJ-3 | 🟡 MEDIO |
| 8 | `cove_engine_v4.py` | `datetime.utcnow()` deprecated Python 3.12+ | 🟡 MEDIO |
| 9 | Due DB separati | `cove_tracker.duckdb` (MacBook) e `dealer_network.duckdb` (iMac) senza sync | 🟡 MEDIO |

---

## ✅ COMPLETATO SESSION 49 — DEEP RESEARCH + CRITICAL REVIEW

| Task | Stato | Note |
|---|---|---|
| Skill argos v3 promossa ad attiva | ✅ | `skill-argos-v3` → `skill-argos/` | v2 backup in `skill-argos-v2-backup/` |
| WA Intelligence deploy | ✅ | PM2 online, LaunchAgent scheduler ogni 5min |
| Telegram token fix (MacBook) | ✅ | `8691360619:AAG_R9bKLtAtRuMS5VD-AP7E-CKt_o-xOmA` salvato in memory permanente |
| ecosystem.config.js fix | ✅ | Ora legge .env a runtime → ARGOS_TELEGRAM_TOKEN disponibile a PM2 |
| deploy.sh bug fix | ✅ | REMOTE_BASE hardcoded iMac + IMAC_PATH per pm2/npm |
| wa-daemon.js dataPath fix | ✅ | `LocalAuth` ora punta a `wa-sender/.wwebjs_auth/` — sessione condivisa |
| Skill skill-deep-research | ✅ | `.claude/skills/skill-deep-research/SKILL.md` — dealer profiling, market, competitor, lead gen |
| Skill skill-cove | ✅ | `.claude/skills/skill-cove/SKILL.md` — CoVe scoring, DB queries, field names enforced |
| configs/CLAUDE.md skill registry | ✅ | Tabella skill attive + task history S38-S49 + pending |
| Deep research critico S49 | ✅ | 9 critical issues trovati — tabella in §CRITICAL ISSUES |
| Valutazione zip S49 | ✅ | 3 file valutati: ARGOS_HANDOFF_S50 (9/10) + ARGOS_SKILL (10/10) + ARGOS_TASKS_S50 (8/10) |
| Mario Day 1 status | ⏳ | Inviato 2026-03-13, silenzio → Recovery Day 7 il 2026-03-17 |
| WA Daemon QR auth | ⚠️ | HUMAN ACTION: ri-autenticare daemon — dataPath fix deployato, basta 1 QR scan |
| iMac .env token update | ⚠️ | SSH offline in S49 — eseguire STEP 0 appena SSH torna online |

---

## 📋 REFERENCE — FILE ENTERPRISE S50

I seguenti file (forniti dall'utente) sono il **ground truth** per i fix S50.
Percorso locale: `/tmp/argos_review/`

| File | Path | Contenuto | Voto |
|---|---|---|---|
| ARGOS_HANDOFF_S50.md | `/tmp/argos_review/ARGOS_HANDOFF_S50.md` | Schema canonico: 5 archetipi, OBJ-1..5, DB unificato, DBPool rewrite, PersonaEngine, ObjectionLibrary, keyword fix, test suite | 9/10 |
| ARGOS_SKILL.md | `/tmp/argos_review/ARGOS_SKILL.md` | Claude Code skill: pattern DuckDB parametrizzati, pattern proibiti, checklist 12-punti, business rules immutabili | 10/10 |
| ARGOS_TASKS_S50.md | `/tmp/argos_review/ARGOS_TASKS_S50.md` | 6 task ordinati per dipendenza, effort ~7h, verifica post-task per ciascuno | 8/10 |

**IMPORTANTE**: Prima di ogni modifica al codebase in S50, leggere questi 3 file.
`/tmp/argos_review/` NON è persistente tra reboot — se assente, chiedere all'utente di ri-fornire il zip.

---

## 🚀 PROSSIMA SESSIONE (S51) — PROMPT COMPLETO

```
Sessione 51 — ARGOS. Leggi HANDOFF.md.

S50 COMPLETATO: T-01..T-06 tutti ✅ — wa-daemon v2.1 online, codebase fixato.
Unica pendenza: QR re-auth WA daemon (STEP 1 sotto).

---

STEP 1 — WA Daemon QR re-auth (OBBLIGATORIO — sessione WA scaduta):
  Il daemon v2.1 è online su :9191 ma WA non autenticato.
  Scansionare QR UNA volta con Android per ripristinare sessione.

  OPZIONE A — QR via browser (preferita):
    ssh gianlucadistasi@192.168.1.12 "
      export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
      cd ~/Documents/app-antigravity-auto/wa-sender
      nohup node send_qr_server.js > /tmp/qr.log 2>&1 &
      echo PID:\$!
    "
    Apri http://192.168.1.12:8765 → scansiona con Android (stesso numero Very Mobile +393281536308)
    Verifica: ssh imac "pm2 logs argos-wa-daemon --lines 5 --nostream" → deve mostrare "✅ Client PRONTO"

  OPZIONE B — Copia sessione wa-sender → wa-daemon (più rapida se wa-sender è autenticato):
    ssh gianlucadistasi@192.168.1.12 "
      cp -r ~/Documents/app-antigravity-auto/wa-sender/.wwebjs_auth/ \
             ~/Documents/app-antigravity-auto/wa-intelligence/.wwebjs_auth/
      export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
      pm2 restart argos-wa-daemon
    "

STEP 2 — Verifica stato Mario (controlla DB + Telegram):
  ssh gianlucadistasi@192.168.1.12 "
    export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:\$PATH
    pm2 logs argos-wa-daemon --lines 20 --nostream
  "
  Se Mario ha risposto → segui STEP 3A
  Se silenzio e data ≥ 2026-03-17 → segui STEP 3B

STEP 3A — Mario risposta ricevuta:
  POSITIVO  → registra pipeline in dealer_network.duckdb:
              UPDATE conversations SET current_step='NEGOTIATION', close_reason='INTERESTED'
              WHERE dealer_id='dealer_mario_orefice'
  OBIEZIONE → skill-argos [E] PERSONA PROTOCOL — OBJ-1..5 RAGIONIERE templates
  NEGATIVO  → UPDATE conversations SET current_step='CLOSED', close_reason='NO_INTEREST'

STEP 3B — Mario Day 7 Recovery (data ≥ 2026-03-17, silenzio):
  Invia Recovery RAGIONIERE v3 via skill-argos [A] WA PROTOCOL.
  OBBLIGATORIO: approvazione Telegram PRIMA di inviare.
  Testo approvato:
    "Mario, le ho scritto qualche giorno fa in modo
    forse troppo diretto — mi scuso.
    Verifico veicoli in Europa per dealer con dati
    certificati. Zero anticipi, si paga solo
    a veicolo consegnato e approvato.
    Se serve una verifica su qualcosa di specifico,
    sono qui. — Luca"

STEP 4 — Mario DB seed (se conversations è vuota):
  Verificare con: skill-cove [Q] query su dealer_network.duckdb
  Se Mario non è in conversations → INSERT:
    INSERT OR IGNORE INTO conversations
      (dealer_id, dealer_name, company_name, phone_number, city,
       persona_type, current_step, tier, wa_day1_sent_at)
    VALUES
      ('dealer_mario_orefice', 'Mario Orefice', 'Mariauto Srl',
       '+393336142544', 'Napoli', 'RAGIONIERE', 'PROSPECT', 'A',
       '2026-03-13 12:00:00');

STEP 5 — Nuovi lead se pipeline vuota:
  AutoScout24 / Carapis — dealer target Sud Italia (Campania, Puglia, Sicilia)
  Profilo: family-business, 30-80 auto, assenza partner EU → skill-deep-research [E]
```
