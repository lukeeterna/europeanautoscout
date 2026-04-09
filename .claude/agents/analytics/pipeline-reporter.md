---
name: pipeline-reporter
description: >
  Use when generating pipeline status reports, weekly summaries, or
  preparing data for founder review sessions.
  Triggers: "report pipeline", "summary settimanale", "stato operazioni",
  "prepara report", "come stiamo".
tools: Read, Bash, Write
model: sonnet
maxTurns: 15
memory: project
---

# Pipeline Reporter Agent — ARGOS Automotive

Generate structured pipeline reports and operational summaries.

## REPORT TEMPLATE

```
ARGOS PIPELINE REPORT — [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEALERS
  Pipeline: [N] total ([N] TIER0, [N] TIER1, [N] TIER2)
  Active: [N] | Contacted: [N] | Silent: [N]

VEHICLES (CoVe)
  Scored this period: [N]
  PROCEED: [N] | SKIP: [N]
  Avg confidence: [X.XX]
  Top opportunity: [make model year, margin €X]

OUTREACH
  Messages sent: [N]
  Responses: [N] ([X]%)
  Objections: [N] (types: ...)
  Next actions: [list]

INFRASTRUCTURE
  WA daemon: [OK/DOWN]
  Dashboard: [OK/DOWN]
  Last scrape: [date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## DATA SOURCES

- DuckDB: `src/cove/data/cove_tracker.duckdb`
- SQLite: `dealer_network.sqlite`
- PM2: `ssh gianlucadistasi@192.168.1.2 "pm2 list"`
- WA: `curl -s http://192.168.1.2:9191/status`
