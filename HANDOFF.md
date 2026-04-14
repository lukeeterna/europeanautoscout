# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S116-S117 — 2026-04-14

---

## S116-S117 COMPLETATA — ANTI-BAN LAYER + E2E TEST

### Fix deployati su iMac (wa-daemon v2.4-antiban)

**S116 — Bug fix critici:**
- Noise filter in wa-daemon.js (body vuoti, base64, encoded → skip)
- Anti-spam cooldown 24h + sha256 dedup in response-analyzer.py
- DB cleanup: Car Plus reset CONTACTED, messaggi noise eliminati
- Direction test PASS (OUTBOUND confermato)

**S117 — Anti-ban layer (6 componenti merge FLUXION):**
- Warm-up schedule: 10→15→20 msg/giorno per settimana
- Jaccard variation check 40% min tra messaggi
- Long pause ogni 5 messaggi (5-10 min)
- daily_stats table + block rate monitor hourly (>2% → auto-stop)
- Pause/Resume API + Telegram commands
- Audit: 4 fix critici (SQL whitelist, connection leak, HELP_TEXT, isNaN)

**LLM Cascade ZERO COSTI:**
- Eliminato OpenRouter a pagamento (claude-haiku-4-5)
- Ordine: Gemini 2.5 Flash → Groq llama-3.3-70b → OpenRouter FREE (13 modelli)
- Gemini truncation fix (finishReason check)

**Token TG rinnovato** — bot operativo

**E2E Test su TEST_FOUNDER (parziale):**
- Day 1 greeting → PASS
- CURIOSITY "chi e' lei?" → template auto-send → PASS
- OBJECTION "quanto costa" → Groq LLM → 3 msg auto-send → PASS
- NEGATIVE "non mi interessa" → NON TESTATO (da fare S118)

### Bug scoperti e fixati durante E2E
- Cooldown 24h bloccava conversazione attiva → fix: bypass se inbound > outbound
- Template {source} = "manual" → fix: fallback "un portale di concessionari"
- Gemini 2.5 Flash tronca risposte (30 token) → fix: sanity check + skip a Groq
- Business hours bloccava sender subprocess serale → fix temporaneo: end=22

### DA FARE (S118)
- Ripristinare BUSINESS_HOURS.end a 20 in time-context.js
- Completare test NEGATIVE ("non mi interessa") → verifica CLOSED_NO
- Testare Day 3 scheduler (aspettare 3 giorni o forzare)
- Primo invio reale a dealer COLD (Enzo Car / Autoline / GP Cars)

---

## INFRA

```
iMac: ssh gianlucadistasi@192.168.1.2 | Python 3.13 | Node v20
WA daemon: porta 9191, version 2.4-antiban, PM2 id=3
Token TG: ARGOS_TELEGRAM_TOKEN in wa-intelligence/.env
DB: dealer_network.sqlite (SQLite) + agent_state + daily_stats
MAI: pm2 restart --update-env (crash better-sqlite3)
```

## COMANDI

```
Status:  curl http://localhost:9191/status
Pause:   curl -X POST http://localhost:9191/pause -H "X-API-Key: KEY"
Resume:  curl -X POST http://localhost:9191/resume -H "X-API-Key: KEY"
Metrics: curl http://localhost:9191/health-metrics -H "X-API-Key: KEY"
TG:      /pause /resume /metrics /status /help
```
