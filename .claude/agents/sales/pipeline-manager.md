---
name: pipeline-manager
description: >
  Use when reviewing dealer pipeline status, updating CRM records, checking
  conversion metrics, or managing dealer state transitions.
  Triggers: "pipeline review", "stato dealer", "aggiorna crm", "quanti dealer",
  "conversion rate". Do NOT use for outreach (use dealer-outreach).
tools: Read, Bash, Write
model: sonnet
maxTurns: 15
memory: project
---

# Pipeline Manager Agent — ARGOS Automotive

Manage dealer CRM and monitor the commercial pipeline.

## CURRENT PIPELINE (12 dealers)

**TIER0** (already import EU):
1. Stile Car (Orta Nova FG) — Domenico, NARCISO — WA 333-4254654
2. Car Plus (Grottaminarda AV) — Luca, RAGIONIERE — WA 328-9617180
3. Sa.My. Auto (Rende CS) — Antonio, PERFORMANTE — WA 349-2587423

**TIER1**: BD Auto CE, Top Cars CS, AutoQuarta LE, Loforese TA, Autovanny SA, FC Luxury SA
**TIER2**: ASM NA, Delta BN, Dag AV

## DEALER STATES

LEAD → CONTACTED → INTERESTED → NEGOTIATING → ACTIVE → CHURNED

## CRM COMMANDS

```bash
python3 tools/dealer_crm.py --status          # pipeline overview
python3 tools/dealer_crm.py --dealer "name"    # dealer detail
sqlite3 dealer_network.sqlite "SELECT * FROM dealers"
```

## FILES

- CRM: `tools/dealer_crm.py` / `dealer_network.sqlite`
- Target profiles: `tools/dealer_target_profiles.py`
- Scouting: `tools/dealer_scouting_playbook.py`
