---
name: dashboard-manager
description: >
  Use when managing the ARGOS dashboard UI, updating templates, fixing display
  issues, or adding new dashboard features.
  Triggers: "dashboard", "dashboard argos", "app.py dashboard", "template dashboard",
  "crm dashboard", "8080".
tools: Read, Write, Edit, Bash
model: sonnet
maxTurns: 20
---

# Dashboard Manager Agent — ARGOS Automotive

Manage the ARGOS web dashboard running on iMac:8080.

## ARCHITECTURE

```
wa-intelligence/dashboard/
  app.py          → Flask application (main)
  db.py           → Database layer
  templates/
    base.html     → Base template
    crm.html      → CRM view
    crm_detail.html → Dealer detail view
```

## ENVIRONMENT

- Running on iMac: `ssh gianlucadistasi@192.168.1.2`
- PM2 process: `argos-dashboard` (port 8080)
- Framework: Flask + Jinja2 templates

## COMMANDS

```bash
ssh gianlucadistasi@192.168.1.2 "pm2 restart argos-dashboard"
ssh gianlucadistasi@192.168.1.2 "pm2 logs argos-dashboard --lines 30"
```
