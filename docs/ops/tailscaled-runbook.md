# Runbook — `tailscaled` standalone su iMac (S155-tris)

**Created**: 2026-05-04 (S155-tris)
**Owner**: ops ARGOS
**Replaces**: Tailscale.app GUI (1.96.5 ha bug funnel/serve persistence non recuperabile su Monterey 12.7.4)

---

## Architettura

```
[Cloudflare Worker argos-proxy]
       ↓ HTTPS (WA_DAEMON_URL secret)
[Tailscale Funnel ingress 185.40.234.x]
       ↓ DNS imac-di-gianluca.tail62c468.ts.net
[tailscaled standalone iMac, port 41641]
       ↓ proxy http://127.0.0.1:9191
[wa-daemon PM2 process]
       ↓ whatsapp-web.js
[WhatsApp Business — 3281536308]
```

## Componenti installati

| File | Path | Note |
|------|------|------|
| Daemon binary | `/usr/local/bin/tailscaled` (symlink → `Cellar/tailscale/1.96.4/bin/tailscaled`) | Compilato da source da Homebrew con go 1.26.2 |
| CLI binary | `/usr/local/bin/tailscale` (symlink) | Idem |
| LaunchDaemon plist | `/Library/LaunchDaemons/com.tailscale.tailscaled.plist` | Owner `root:wheel` 644, `RunAtLoad` + `KeepAlive` |
| State | `/var/lib/tailscale/tailscaled.state` | Owner `root:wheel` 700 dir |
| Socket | `/var/run/tailscale/tailscaled.sock` | Creato dal daemon all'avvio |
| Stdout log | `/var/log/tailscaled.log` | |
| Stderr log | `/var/log/tailscaled.err.log` | |
| WG port | `41641` UDP | Configurato in plist `--port=41641` |

## Identità tailnet

- Account: `ferretti.argosautomotive@gmail.com`
- Tailnet: `tail62c468.ts.net`
- Hostname device: `imac-di-gianluca`
- IP Tailscale: `100.85.132.49` (può cambiare a re-enroll, sempre 100.x.x.x)
- DNS pubblico Funnel: `https://imac-di-gianluca.tail62c468.ts.net`
- API token: in `.env` come `TAILSCALE_API_TOKEN` (90gg validity, rigenerare se expired)

## Comandi base (tutti richiedono sudo + `--socket=`)

> ⚠️ Il binario CLI `/usr/local/bin/tailscale` è UNICO sul sistema, ma talks via socket `--socket=/var/run/tailscale/tailscaled.sock` per parlare allo standalone (NON al GUI App network extension che usa `/var/run/tailscaled.socket` standard). Senza `--socket=` il CLI prova il default e può fallire se GUI App attiva.

```bash
# Status
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock status
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock ip -4

# Funnel status
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock funnel status
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock serve status --json

# Funnel set / off
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock funnel --bg 9191
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock funnel --https=443 off

# Cert manuale (re-emit)
sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock cert imac-di-gianluca.tail62c468.ts.net
```

## Operazioni launchd

```bash
# Stato daemon
sudo launchctl print system/com.tailscale.tailscaled | head -20
ps aux | grep tailscaled | grep -v grep

# Stop
sudo launchctl bootout system /Library/LaunchDaemons/com.tailscale.tailscaled.plist

# Start
sudo launchctl bootstrap system /Library/LaunchDaemons/com.tailscale.tailscaled.plist

# Restart (bootout + bootstrap)
sudo launchctl bootout system /Library/LaunchDaemons/com.tailscale.tailscaled.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/com.tailscale.tailscaled.plist
```

## Re-enroll device (dopo logout o token expiry)

1. Genera fresh auth-key via API:
   ```bash
   TS_TOKEN=$(grep ^TAILSCALE_API_TOKEN .env | cut -d= -f2- | tr -d '"')
   curl -s -X POST "https://api.tailscale.com/api/v2/tailnet/-/keys" \
     -u "${TS_TOKEN}:" -H "Content-Type: application/json" \
     -d '{"capabilities":{"devices":{"create":{"reusable":false,"ephemeral":false,"preauthorized":true}}},"expirySeconds":3600,"description":"re-enroll"}'
   ```
2. Se vecchio device offline + occupa nome `imac-di-gianluca` → DELETE via API per evitare suffix `-1`:
   ```bash
   curl -X DELETE "https://api.tailscale.com/api/v2/device/{ID}" -u "${TS_TOKEN}:"
   ```
3. Login standalone:
   ```bash
   sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock up \
     --authkey=tskey-auth-... --hostname=imac-di-gianluca --reset
   ```

## Update Worker secret WA_DAEMON_URL

Se IP/DNS Funnel cambia (raro), aggiornare:
```bash
cd argos-proxy/
export CLOUDFLARE_API_TOKEN=$(grep ^CLOUDFLARE_API_TOKEN ../.env | cut -d= -f2- | tr -d '"')
echo "https://imac-di-gianluca.tail62c468.ts.net" | npx wrangler secret put WA_DAEMON_URL
```
Worker rilegge il secret a ogni request (no redeploy needed).

## Troubleshooting

### Daemon non parte
```bash
sudo tail -50 /var/log/tailscaled.err.log
sudo launchctl print system/com.tailscale.tailscaled
```

### Funnel status empty `{}` (sintomo bug GUI App)
1. Verificare di parlare al socket standalone: `sudo /usr/local/bin/tailscale --socket=/var/run/tailscale/tailscaled.sock funnel status`
2. Se vuoto anche su standalone: verificare ACL ha `nodeAttrs: [{target:["autogroup:member"], attr:["funnel"]}]` + settings `httpsEnabled:true`
3. Re-set: `sudo /usr/local/bin/tailscale --socket=... funnel --bg 9191`

### DNS pubblico NXDOMAIN
1. `dig +short @1.1.1.1 imac-di-gianluca.tail62c468.ts.net` deve dare 3 IP `185.40.234.x`
2. Se NXDOMAIN: device non registrato presso control plane → re-enroll via auth-key

### Coexistenza GUI App
- GUI Tailscale.app è installata (logged out) ma NON deve essere fatta partire/loggare per ARGOS
- Se Luke avvia GUI per altre macchine, usa account separato OR diverso tailnet
- Standalone usa socket dedicato `/var/run/tailscale/tailscaled.sock` → nessuna interferenza con GUI socket default

## Sicurezza

- API token Tailscale: chmod 600 `.env`, MAI in commit
- `tailscaled.state` chmod 700 dir + file private (contiene chiavi WireGuard del nodo)
- Funnel espone porta 9191 al pubblico Internet via TLS — wa-daemon DEVE avere `X-API-Key` header check (già attivo)

## Backup state

Se serve clonare il device (sostituzione hardware), backup atomico:
```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.tailscale.tailscaled.plist
sudo cp /var/lib/tailscale/tailscaled.state /backup/tailscaled.state.$(date +%Y%m%d)
sudo launchctl bootstrap system /Library/LaunchDaemons/com.tailscale.tailscaled.plist
```

Ripristino: copy state, bootout/bootstrap, verifica `tailscale status`.

## Riferimenti

- [Tailscale wiki — Tailscaled-on-macOS](https://github.com/tailscale/tailscale/wiki/Tailscaled-on-macOS)
- [Tailscale Funnel docs](https://tailscale.com/kb/1223/funnel)
- [Homebrew tailscale formula](https://formulae.brew.sh/formula/tailscale)
- BACKLOG entries: "CF Workers → LAN daemon unreachable" + "Tailscale Funnel `--bg` set ma `status` empty su macOS App"

---

# Appendice — PM2 startup persistenza (S156)

Setup parallelo per ARGOS PM2 processes (`argos-wa-daemon`, `argos-cf-monitor`) che devono ripartire automaticamente al boot iMac, indipendente da login GUI utente.

## Componenti installati S156

| File | Path | Note |
|------|------|------|
| pm2 binary | `/Users/gianlucadistasi/.npm-global/bin/pm2` (v6.0.14) | npm global install |
| pm2 source | `/Users/gianlucadistasi/.npm-global/lib/node_modules/pm2/bin/pm2` | path completo richiesto da launchd plist |
| LaunchDaemon plist | `/Library/LaunchDaemons/pm2.gianlucadistasi.plist` | **System-level** (NOT LaunchAgents!), Owner `root:wheel` 644, Label `com.PM2`, `RunAtLoad` + `LaunchOnlyOnce` |
| Process snapshot | `/Users/gianlucadistasi/.pm2/dump.pm2` | Auto-loaded da `pm2 resurrect` al bootstrap launchd |
| Stdout log | `/tmp/com.PM2.out` | Output di `pm2 resurrect` al boot |
| Stderr log | `/tmp/com.PM2.err` | |

## Setup (one-shot, già eseguito S156)

```bash
# 1. Genera plist (PM2 bug: scrive sempre in ~/Library/LaunchAgents/ invece di /Library/LaunchDaemons/)
sudo env PATH=$PATH:/usr/local/bin \
  /Users/gianlucadistasi/.npm-global/lib/node_modules/pm2/bin/pm2 \
  startup launchd -u gianlucadistasi --hp /Users/gianlucadistasi

# 2. Workaround: sposta a system-level LaunchDaemon (parte al boot senza GUI login)
sudo mv /Users/gianlucadistasi/Library/LaunchAgents/pm2.gianlucadistasi.plist \
        /Library/LaunchDaemons/pm2.gianlucadistasi.plist
sudo chown root:wheel /Library/LaunchDaemons/pm2.gianlucadistasi.plist
sudo chmod 644 /Library/LaunchDaemons/pm2.gianlucadistasi.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/pm2.gianlucadistasi.plist

# 3. Salva snapshot processi attivi (richiesto per resurrect)
PATH=/usr/local/bin:/opt/homebrew/bin:/Users/gianlucadistasi/.npm-global/bin:$PATH \
  /Users/gianlucadistasi/.npm-global/bin/pm2 save
```

## Operazioni base

```bash
# Lista processi PM2 (richiede PATH fix per node)
ssh gianlucadistasi@192.168.1.2 \
  'PATH=/usr/local/bin:/opt/homebrew/bin:$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 list'

# Re-snapshot dopo aggiunta/rimozione processo
PATH=/usr/local/bin:/opt/homebrew/bin:/Users/gianlucadistasi/.npm-global/bin:$PATH \
  /Users/gianlucadistasi/.npm-global/bin/pm2 save

# Stato launchd (job auto-removed da registry attivo dopo execution con LaunchOnlyOnce, normale)
sudo launchctl list | grep -iE 'PM2|argos'

# Restart manuale Daemon (forza ri-execution resurrect)
sudo launchctl bootout system /Library/LaunchDaemons/pm2.gianlucadistasi.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/pm2.gianlucadistasi.plist
```

## Test cross-reboot (verifica S156)

```bash
# Pre-reboot timestamp + SSH back loop
date && ssh gianlucadistasi@192.168.1.2 "echo '<PWD>' | sudo -S reboot"
until ping -c 1 -W 2 192.168.1.2 >/dev/null 2>&1; do sleep 3; done
sleep 45  # services startup

# Verifica cascade
ssh gianlucadistasi@192.168.1.2 'ps aux | grep tailscaled | grep -v grep'  # tailscaled standalone
ssh gianlucadistasi@192.168.1.2 'PATH=/usr/local/bin:/opt/homebrew/bin:$PATH /Users/gianlucadistasi/.npm-global/bin/pm2 list | head -10'
ssh gianlucadistasi@192.168.1.2 'curl -s -m 5 localhost:9191/status'
curl -s -m 15 https://imac-di-gianluca.tail62c468.ts.net/status  # funnel external
```

Atteso: tutto verde in <2min post-reboot. Test S156 (18:46-18:48) completato in 110s totali.

## Troubleshooting PM2

### `pm2 list` "env: node: No such file or directory" via SSH
PATH SSH session non include `/usr/local/bin` o `/opt/homebrew/bin`. Pattern: prefissa con `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH` oppure usa path assoluto del binary.

### Daemon resurrect non parte al boot
1. Verifica plist in posizione system-level: `ls -l /Library/LaunchDaemons/pm2.gianlucadistasi.plist` (deve essere root:wheel)
2. Log resurrect: `cat /tmp/com.PM2.out` + `cat /tmp/com.PM2.err`
3. Forza re-bootstrap: `sudo launchctl bootout system .../pm2.gianlucadistasi.plist && sudo launchctl bootstrap system .../pm2.gianlucadistasi.plist`

### Plist in `~/Library/LaunchAgents/` invece di `/Library/LaunchDaemons/`
Bug noto pm2 startup macOS. NON funziona su iMac headless (LaunchAgents richiedono GUI login utente). Sposta manualmente come da setup S156 sopra.

### Processi pm2 desincronizzati con dump.pm2
Se aggiungi/rimuovi processo PM2, ricorda `pm2 save` per aggiornare snapshot. Senza save, prossimo reboot resurrect con stato vecchio.

## Sicurezza

- LaunchDaemon parte come `root` ma esegue pm2 come user `gianlucadistasi` (via `UserName` in plist)
- Processi child argos-* girano user-level (no privilegi escalation)
- `dump.pm2` chmod 600 user-only (può contenere env vars sensibili)
