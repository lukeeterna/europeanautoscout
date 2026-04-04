# ARGOS — Identita' Business

**Brand**: ARGOS Automotive | **Persona**: Luca Ferretti
**Business**: B2B vehicle scouting EU→IT | **Fee**: €800-1.200 success-fee
**Target**: Concessionari family-business Sud Italia, 30-80 auto
**Mercati**: DE/NL/BE/AT/FR/SE + tutti EU (19 paesi coperti)
**Veicoli**: BMW/Mercedes/Audi + Porsche/Lambo/Ferrari/McLaren/Range Rover 2018-2025

**Landing**: https://argos-automotive.pages.dev
**Dashboard**: iMac:8080 | **WA Business**: 3281536308

## Infrastruttura
```
iMac: ssh gianlucadistasi@192.168.1.2 | Python 3.13 | Node v20
MacBook: macOS 11 | Python 3.13
PM2: wa-daemon (9191), argos-dashboard (8080), tg-bot
DB: dealer_network.sqlite (SQLite), cove_tracker.duckdb (DuckDB)
```

## Path Critici
```
CoVe Engine:       src/cove/cove_engine_v4.py              ← NON modificare
Fraud Flags:       src/cove/fraud_flags.py
Scrapers:          tools/scrapers/ (28 portali)
Fee calculator:    tools/fee_calculator.py
PDF generator:     tools/scripts/pdf_generator_enterprise.py
WA daemon:         wa-intelligence/wa-daemon.js
Dashboard:         wa-intelligence/dashboard/app.py
Response analyzer: wa-intelligence/response-analyzer.py
On-demand runner:  tools/on_demand_runner.py
Memory:            ~/.claude/projects/.../memory/MEMORY.md
```

## Reference
```
Master reference:  research/S73_MASTER_REFERENCE.md
Architettura:      research/s98_ARCHITETTURA_DEFINITIVA.md
Messaggi V3:       research/s94_MESSAGGI_DEFINITIVI_V3.md
```
