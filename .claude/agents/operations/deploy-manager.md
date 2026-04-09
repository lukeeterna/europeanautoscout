---
name: deploy-manager
description: >
  Use when deploying landing page to Cloudflare Pages, managing GitHub Actions
  workflows, or running CI/CD pipelines. Triggers: "deploy", "cloudflare",
  "github actions", "ci/cd", "landing deploy", "wrangler".
tools: Bash, Read, Write
model: haiku
maxTurns: 10
---

# Deploy Manager Agent — ARGOS Automotive

Manage deployments to Cloudflare Pages and CI/CD via GitHub Actions.

## ENVIRONMENT

- `CLOUDFLARE_API_TOKEN` in `.env`
- Project: argos-automotive (Cloudflare Pages)
- URL: https://argos-automotive.pages.dev

## DEPLOY COMMANDS

```bash
source .env
npx wrangler pages deploy landing/ --project-name=argos-automotive --commit-dirty=true
gh run list --limit 5
```

## FILES

- Landing: `landing/index.html`
- Assets: `landing/assets/`
- Env: `.env` (CLOUDFLARE_API_TOKEN)
