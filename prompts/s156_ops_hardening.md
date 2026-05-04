# S156 — Ops hardening post S155-tris

**Sessione**: S156 (clean context start)
**Data target**: 2026-05-05+ (post chiusura S155-tris)
**Scope**: hardening operativo dopo deploy tailscaled standalone — sopravvivenza cross-reboot, monitoring, sicurezza credenziali.
**NO Day 1 reale** in questa sessione (regola `feedback_no_live_without_test.md`).
**Tempo stimato**: ~45-60min autonomo + ~5min azioni Luke (cambio pwd sudo + reboot test)

---

## Pre-condizioni S156

| Check | Verifica |
|-------|----------|
| iMac up | `ping -c 1 192.168.1.2` |
| WA daemon online | `ssh ... "curl -s localhost:9191/status"` → `wa_status: connected` |
| Funnel attivo | `curl -s -m 10 https://imac-di-gianluca.tail62c468.ts.net/status` → HTTP 200 |
| Worker LIVE | `curl -s https://argos-proxy.gianlucanewtech.workers.dev/health` → `status:ok` |
| tailscaled standalone running | `ssh ... "ps aux | grep tailscaled | grep -v grep"` mostra PID |

🛑 Se uno fallisce: PRIMA recovery (vedi `docs/ops/tailscaled-runbook.md` troubleshooting), POI S156.

---

## Phase 1 — REMINDER: cambio pwd sudo iMac (Luke action, 2min)

🔒 **Critico sicurezza**: pwd sudo `121181` (numerica 6 cifre) era esposta in transcript locale Claude Code di S155-tris.

**AskUserQuestion** a Luke:
- "Hai cambiato la pwd sudo iMac dopo S155-tris (`passwd` su iMac fisicamente)? [Sì / No, lo faccio ora / Skip e vado avanti]"

🛑 Se "No, lo faccio ora": pause finché Luke conferma "fatto", poi update `.env` se necessario, poi continua.
🛑 Se "Skip": documenta in BACKLOG come priority alta, continua.

---

## Phase 2 — `pm2 startup launchd` per persistenza cross-reboot (~10min)

### 2.1 Genera comando startup
```bash
ssh gianlucadistasi@192.168.1.2 'PATH=/usr/local/bin:/opt/homebrew/bin:$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 startup launchd 2>&1'
```

L'output mostrerà comando `sudo` da eseguire (path tipico: `sudo env PATH=... pm2 startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi`).

### 2.2 Esegui comando sudo (richiede pwd Luke aggiornata)

**AskUserQuestion** a Luke per pwd sudo NUOVA (post Phase 1).

Poi:
```bash
ssh gianlucadistasi@192.168.1.2 "echo '$NEW_SUDO_PWD' | sudo -S env PATH=/usr/local/bin:... pm2 startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi"
```

### 2.3 Salva snapshot pm2 attuale
```bash
ssh gianlucadistasi@192.168.1.2 'PATH=/usr/local/bin:/opt/homebrew/bin:$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 save'
```

### 2.4 Verifica plist creato
```bash
ssh gianlucadistasi@192.168.1.2 'ls -l /Library/LaunchDaemons/pm2.gianlucadistasi.plist'
sudo launchctl print system/pm2.gianlucadistasi 2>&1 | head -10
```

---

## Phase 3 — Test reboot iMac (Luke autorizza, 5-10min)

⚠️ Distruttivo: il reboot interrompe daemon, dashboard, SSH session per ~2-3min. Richiede autorizzazione Luke (lui non sta usando l'iMac per altro).

**AskUserQuestion** a Luke:
- "Reboot iMac per testare persistenza pm2 + tailscaled? Interruzione ~2-3min. [Sì, reboot ora / No, skip test, fidiamoci della config / Defer S157]"

🛑 Se "Sì": esegui sequenza:
```bash
# Annota timestamp pre-reboot
date
# Reboot
ssh gianlucadistasi@192.168.1.2 "echo '$NEW_SUDO_PWD' | sudo -S reboot"
# Wait + retry connection
until ping -c 1 -W 2 192.168.1.2 >/dev/null 2>&1; do sleep 5; done
# Wait services up
sleep 30
# Verify cascade:
# - SSH back
ssh gianlucadistasi@192.168.1.2 "uptime"
# - tailscaled running
ssh ... "ps aux | grep tailscaled | grep -v grep"
# - pm2 + wa-daemon
ssh ... "PATH=/usr/local/bin:/opt/homebrew/bin:\$PATH pm2 list 2>&1 | head -10"
ssh ... "curl -s localhost:9191/status"
# - Funnel persistente
curl -s -m 15 https://imac-di-gianluca.tail62c468.ts.net/status
```

✅ GREEN: tutti rispondono entro 60s post-reboot senza intervento manuale.
🔴 RED: documenta cosa NON è ripartito automaticamente, fix necessario prima di chiudere S156.

🛑 Se "No, skip" o "Defer S157": documenta in HANDOFF e chiudi sessione.

---

## Phase 4 — Monitoring health-check 5min (~10min setup)

Aggiungere monitoring continuo che alerta se uno tra (tailscaled, wa-daemon, funnel external) cade.

### 4.1 Script `tools/scripts/health_monitor.sh`

Crea script bash che:
- Ping iMac
- Curl localhost:9191/status (via SSH)
- Curl https://imac-di-gianluca.tail62c468.ts.net/status (esterno)
- Se uno fallisce → Telegram alert (riusa wa-intelligence/tg-bot config)

### 4.2 Aggiungi a cron MacBook ogni 5min

```
*/5 * * * * /bin/bash /Users/macbook/Documents/combaretrovamiauto-enterprise/tools/scripts/health_monitor.sh >> /tmp/argos-health.log 2>&1
```

OR launchd plist locale MacBook se cron problematico.

### 4.3 Smoke alert (forza fail per testare)
```bash
# Stop temporaneo daemon su iMac → attendi 5min → verifica Telegram alert ricevuto → restart
```

🛑 Skip Phase 4 se Luke vuole prioritizzare altro (ops monitoring già parziale via `argos-cf-monitor` PM2 process).

---

## Phase 5 — Documentation + commit (~10min)

- [ ] Aggiorna `BACKLOG.md`:
  - Marca **PM2 daemon non resurrect post-reboot iMac** = FIXED se Phase 2+3 verde
  - Aggiungi nuova sezione monitoring se Phase 4 fatta
- [ ] Aggiorna `docs/ops/tailscaled-runbook.md` con sezione "PM2 startup persistenza" se Phase 2 verde
- [ ] Aggiorna `HANDOFF.md` STATO CORRENTE → S156 CHIUSO VERDE/PARTIAL
- [ ] Aggiorna `MEMORY.md` con entry S156
- [ ] Commit: `feat(s156): pm2 startup launchd + ops hardening` (o variant in base a Phase eseguite)

---

## Phase 6 — STOP, decisione Luke per next sprint

🛑 NIENTE Day 1 reale auto-generato. Luke deciderà tra:

- **Test interattivo dealer reale CON Luke** (richiede autorizzazione esplicita + presenza Luke + sessione separata)
- **Smoke front-end SIGN flow Cloudflare Pages** (test browser su signature page Day 1)
- **Scraper fix** (BMW Serie 3/5, Mercedes GLC/C/E/GLE attualmente rotti — vedi CLAUDE.md "Scraper ROTTI")
- **CoVe pipeline** (sblocco E2E "NON FUNZIONANTE" da CLAUDE.md)
- **Day 1 sequence revision** (template review V3 → V4 se serve)
- **Altro**

**Action S156 fine**: chiusura prompt qui. Niente prompt S157 auto-generato.

---

## Vincoli S156

- ✋ NO Day 1 reale (regola `feedback_no_live_without_test.md`)
- ✋ NO messaggi WA a numeri ≠ TEST_FOUNDER `393314928901` (e in S156 idealmente NESSUN messaggio WA — è ops, non outreach)
- ✋ Reboot iMac SOLO con autorizzazione esplicita Luke (Phase 3)
- ✋ Cambio pwd sudo è Phase 1 — NON skippare a meno che Luke chieda esplicitamente

---

## Out of scope S156

- Day 1 reale dealer (Stile Car o altri) → sessione separata con autorizzazione Luke
- Major OS upgrade (Monterey → Ventura/Sonoma) → defer, evaluate impact prima
- CoVe engine refactor → defer
- New feature business logic → defer

---

## Target di fine S156

✅ Phase 1 done: pwd sudo cambiata (o documentato skip)
✅ Phase 2 done: `pm2 startup launchd` configurato, plist esiste
✅ Phase 3 done: reboot test verde (tutti servizi auto-restart) OR documentato skip
✅ Phase 4 done: health monitoring 5min attivo (opzionale)
✅ Phase 5 done: docs aggiornati, commit pushato
✅ S156 CHIUSO VERDE/PARTIAL in HANDOFF + MEMORY.md

❌ NON in S156: Day 1 reale, prompt S157 auto, Stripe/P.IVA, OS upgrade, scraper fix, CoVe refactor

---

## Resume path se compaction durante S156

Stato sarà tracciato in TaskCreate da Phase 1. Se compaction:
1. Leggi questa entry + ultima entry MEMORY.md S156
2. Verifica ultima Phase completata via `git log` e tasks Claude
3. Riprendi da Phase successiva

---

## Riferimenti

- Runbook tailscaled: `docs/ops/tailscaled-runbook.md`
- HANDOFF S155-tris: `HANDOFF.md` STATO CORRENTE
- Bug GUI Tailscale (storico): `BACKLOG.md` "Tailscale Funnel `--bg` set ma `status` empty"
- Regola no-Day1-auto: `~/.claude/projects/.../memory/feedback_no_live_without_test.md`
