---
name: Dashboard Command Center S61
description: ARGOS Command Center dashboard deployed on iMac:8080 - FastAPI+HTMX+Tabler, F1-F5 complete, enterprise grade
type: project
---

ARGOS Command Center LIVE su iMac:8080 — F1-F5 completate (2026-03-18).

**Stack**: FastAPI + Jinja2 + HTMX 2.0 + Alpine.js 3.x + Tabler dark + ECharts (tutto CDN, zero build)
**RAM**: ~47MB | **PM2**: argos-dashboard (pid, online)

**Architettura**:
- `wa-intelligence/run_dashboard.py` — launcher (workaround wa-intelligence hyphen)
- `wa-intelligence/dashboard/app.py` — 6 page routes + 2 HTMX partials + 2 JSON API + 4 action endpoints
- `wa-intelligence/dashboard/db.py` — 14 queries + 4 write actions + ensure_tables() + audit log
- `wa-intelligence/dashboard/auth.py` — cookie session firmato itsdangerous, single user
- `wa-intelligence/dashboard/static/css/argos-theme.css` — nero #0D0D0D + oro #B8960C
- 8 templates + 3 partials

**F5 Action Endpoints**:
- POST `/api/actions/approve-reply` — approva pending_reply
- POST `/api/actions/skip-reply` — rifiuta pending_reply
- POST `/api/actions/add-note` — aggiorna note dealer
- POST `/api/actions/send-day1` — segna dealer come DAY1_SENT (solo se PENDING)

**CTO Review fixes (S61)**:
- API 401 su unauthorized (era 200)
- dealer_id inesistente → redirect (era crash)
- Rimosso import hashlib unused
- Fix conversation_detail HTMX (era template sbagliato)
- Python 3.9 compat (dict|None → Optional[dict])
- .pyc cache invalidation dopo deploy
- Audit log su ogni azione F5

**Why:** Dashboard necessaria per supervisione passiva da parte del founder (non vuole fare il commerciale).
**How to apply:** Quando si aggiungono funzionalità dashboard, usare lo stesso stack (HTMX partial, Alpine.js client-side, zero JS custom). Sempre deployare su iMac via SCP + PM2 restart + clear pycache.
