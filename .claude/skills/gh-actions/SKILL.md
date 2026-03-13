---
name: gh-actions
description: >
  Gestisce CI/CD GitHub Actions per ARGOS/CoVe 2026.
  TRIGGER su: "github actions", "workflow ci", "workflow cd", "deploy imac",
  "test e2e ci", "day7 scheduler", "gh secrets", "pipeline cicd",
  "self-hosted runner", "appleboy ssh", "tailscale deploy".
  Copre: creazione/modifica workflow, gestione secrets, debug runs, E2E test setup.
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# ARGOS™ GitHub Actions — Skill CoVe 2026

## ARCHITETTURA CI/CD

```
.github/workflows/
  ci.yml   → ubuntu-22.04 | test E2E Node.js + Python | trigger: push/PR
  cd.yml   → ubuntu-22.04 | appleboy/ssh-action → iMac | trigger: push + schedule
```

## HARDWARE MAP (immutabile)

| Macchina | Ruolo | Raggiungibilità da GH Actions |
|---|---|---|
| GitHub runner | CI/CD executor | N/A |
| iMac 2012 | Deploy target, server processi | Solo via Tailscale IP (NON 192.168.1.12) |
| MacBook | Dev client | N/A |

**CRITICO**: L'iMac è dietro NAT domestico. GitHub Actions NON può raggiungere `192.168.1.12`.
Opzioni:
1. **Tailscale** (preferita) — iMac Tailscale IP stabile → secret `IMAC_HOST`
2. **Self-hosted runner sull'iMac** — si connette outbound a GitHub, no port forward

---

## SECRETS RICHIESTI (Settings → Secrets → Actions)

| Secret | Valore | Note |
|---|---|---|
| `IMAC_HOST` | Tailscale IP iMac | `tailscale ip -4` sull'iMac |
| `IMAC_USER` | `gianlucadistasi` | Username SSH iMac |
| `IMAC_SSH_KEY` | Chiave privata ED25519 | Coppia dedicata `gh-deploy`, NON chiave personale |

**MAI** mettere `192.168.1.12` come `IMAC_HOST` — non raggiungibile da runner cloud.

---

## SETUP SSH KEY DEPLOY (una tantum)

```bash
# 1. Genera coppia dedicata sul MacBook
ssh-keygen -t ed25519 -C "github-deploy-argos" -f ~/.ssh/gh_deploy_argos -N ""

# 2. Copia pubblica sull'iMac
ssh gianlucadistasi@192.168.1.12 "cat >> ~/.ssh/authorized_keys" < ~/.ssh/gh_deploy_argos.pub

# 3. Verifica
ssh -i ~/.ssh/gh_deploy_argos gianlucadistasi@192.168.1.12 "echo OK"

# 4. Aggiungi privata a GitHub Secrets
# Settings → Secrets → Actions → New secret
# Nome: IMAC_SSH_KEY
# Valore: cat ~/.ssh/gh_deploy_argos (tutto il contenuto compreso -----BEGIN-----/-----END-----)
```

---

## REGOLE WORKFLOW — IMMUTABILI

```
✅ Runner CI: ubuntu-22.04 (NON macos-latest — 10x più costoso)
✅ SSH action: appleboy/ssh-action@v1.0.3 (pin versione, non @latest)
✅ Node cache: cache-dependency-path: wa-sender/package.json
✅ Secrets: SOLO ${{ secrets.NAME }}, mai valori hardcoded
✅ .duckdb e .env: SEMPRE in .gitignore, MAI in rsync/deploy
✅ E2E test: solo format/payload/session-structure — MAI test invio reale WA
```

---

## WORKFLOW ACTIONS — COMANDI UTILI

```bash
export PATH=$HOME/bin:$PATH  # gh in ~/bin

# Stato ultimo run CI
gh run list --workflow=ci.yml --limit=5

# Log ultimo run
gh run view --log $(gh run list --workflow=ci.yml --limit=1 --json databaseId -q '.[0].databaseId')

# Trigger deploy manuale
gh workflow run cd.yml

# Verifica secrets configurati (solo nomi, non valori)
gh secret list

# Aggiungi secret
gh secret set IMAC_HOST --body "100.x.x.x"
gh secret set IMAC_USER --body "gianlucadistasi"
gh secret set IMAC_SSH_KEY < ~/.ssh/gh_deploy_argos

# Status workflow
gh workflow list
```

---

## E2E TEST — COSA TESTARE IN CI

| Test | File | Richiede sessione WA? |
|---|---|---|
| Formato numero IT → @c.us | `tests/validate-phone-format.js` | No |
| Struttura directory sessione | `tests/validate-session-structure.js` | No |
| Payload messaggio (km LOCKED, parole vietate) | `tests/validate-message-payload.js` | No |
| Invio reale WhatsApp | ❌ NON in CI | Sì — solo su iMac |

**Regola**: non testare mai il send reale in CI — rischio ban account WA.

---

## TROUBLESHOOTING

| Sintomo | Causa | Fix |
|---|---|---|
| `ssh: connect to host`: timeout | iMac non raggiungibile da runner | Verifica Tailscale attivo su iMac |
| `Host key verification failed` | Prima connessione SSH | Aggiungere `StrictHostKeyChecking no` nei ssh_options |
| `Permission denied (publickey)` | Chiave non in authorized_keys | Ripeti setup SSH key |
| CI fallisce su `npm ci` | package-lock.json mancante | Committare `wa-sender/package-lock.json` |
| `chromium-browser not found` | Apt step saltato | Verificare step install system deps in ci.yml |
