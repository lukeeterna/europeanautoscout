# S112 — Audit 360° Agent-First + Deep Research + Soft Launch

## ISTRUZIONI OPERATIVE

Questa sessione usa il framework enterprise COMPLETO. Ogni fase DEVE:
- Attivare `/skill-loader` per determinare skill necessarie
- Delegare a sub-agent specializzati (MAI fare tutto nel main context)
- Produrre output strutturato (report, checklist, score)

---

## WAVE 1 — AUDIT PARALLELI (3 agent in parallelo)

### Agent 1: Code Audit
```
Spawna: agent quality-auditor (subagent_type: general-purpose)
Skill: /backend-architect + /api-tester + /workflow-optimizer
Scope: src/cove/, wa-intelligence/, tools/scripts/
Check: pattern consistency, error handling, dead code, test coverage gaps
Output: CODE-AUDIT.md con findings ranked by severity
```

### Agent 2: Security Audit
```
Spawna: agent infra-monitor + network-hardener
Skill: /infrastructure-maintainer
Scope: iMac deployment, .env, API auth, DB permissions, GDPR
Check: OWASP top 10, secrets in git, input validation, rate limiting
       WA daemon auth, dashboard auth, SQLite/DuckDB permissions
Output: SECURITY-AUDIT.md con PASS/FAIL per ogni check
SSH: gianlucadistasi@192.168.1.2
```

### Agent 3: Pipeline E2E Validation
```
Spawna: agent pipeline-validator
Skill: /skill-cove + /api-tester
Scope: scrape → CoVe score → PDF → sanitizer → outreach flow
Check: catena completa funzionante, nessun anello rotto
       Test listing reale end-to-end
Output: E2E-REPORT.md con status per ogni stage
```

---

## WAVE 2 — DEEP RESEARCH (4 researcher in parallelo, dopo Wave 1)

### Research 1: Mercato & Competitor Update 2026
```
Spawna: agent competitive-intel + trend-researcher
Skill: /trend-researcher + /skill-deep-research
Query: Bolidem, Autotedesche, Importami, AUTO1, AutoProff — novita' Q1 2026?
       Market size import premium EU→IT. Nuovi player?
Output: MARKET-RESEARCH-2026.md
```

### Research 2: Legal & Compliance
```
Spawna: agent legal-compliance-checker + tax-compliance
Skill: /legal-compliance-checker
Query: Prestazione occasionale limiti 2026, contratto Art.5-bis validita',
       GDPR trattamento dati dealer, normativa import EU 2026 cambiamenti
Output: LEGAL-COMPLIANCE.md
```

### Research 3: Tech Stack Risk Assessment
```
Spawna: agent general-purpose (model: opus)
Skill: /tool-evaluator + /backend-architect
Query: PaddleOCR 3.x produzione stability, WA green API ban risk 2026,
       DuckDB vs SQLite per volume 50-200 dealer, SimpleLama license/maintenance
Output: TECH-RISK.md
```

### Research 4: Product-Market Fit Validation
```
Spawna: agent dealer-persona-researcher + lead-researcher
Skill: /skill-deep-research + /growth-hacker
Query: Dealer Sud Italia: pagano davvero €800-1200? Quanti gia' importano da soli?
       Costo self-import per un dealer (tempo, rischi, burocrazia).
       Referral rate in mercati B2B family-business. Success-fee vs subscription.
Output: PMF-VALIDATION.md
```

---

## WAVE 3 — DECISION GATE

Dopo Wave 1+2, il founder riceve:
- 3 audit report (code, security, E2E)
- 4 research report (market, legal, tech, PMF)

**Se audit PASS e research non bloccano:**
→ Procedi a Wave 4 (soft launch)

**Se audit FAIL o research blocca:**
→ Fix critici prima, poi soft launch

---

## WAVE 4 — SOFT LAUNCH OPERATIVO (dopo gate OK)

### 4.0 Test WA reale su TEST_FOUNDER
```
Business hours 8-20. Skill: /skill-argos
iMac: python3 tools/on_demand_runner.py --marca BMW --budget 40000 --dealer "TEST_FOUNDER"
```

### 4.1 Recovery Car Plus AV
```
Azione MANUALE da telefono (dealer reale, ENGAGED, silenzio da 2026-04-07)
Messaggio: research/s108_day1_messages_top5.md
```

### 4.2 Import 13 dealer + Soft Launch
```
Skill: /skill-argos-orchestrator
1. Import da research/s108_enrichment_13_dealer_validati.json
2. Soft launch: Stefano Auto FG (RELAZIONALE, 4.98/5)
3. Se OK → 1 dealer/giorno
```

---

## Contesto tecnico

- iMac: WA daemon ONLINE, pid 5796, version 2.3-ambra
- Sanitizer v3: deployato, testato (KORDICK 2/2 OK, 71.7s)
- TG alerts: configurati e testati
- on_demand_runner: deployato su iMac
- PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`
- DB iMac: ~/Documents/app-antigravity-auto/dealer_network.sqlite
- DuckDB: ~/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb
