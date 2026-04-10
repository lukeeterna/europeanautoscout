# S112 — Audit 360° + Deep Research + Soft Launch Resume

## Approccio sessione: FRAMEWORK COMPLETO

Questa sessione usa il framework enterprise completo. Prima di scrivere codice:
1. **Audit codice** — qualita', pattern, regressioni su tutto il codebase
2. **Audit sicurezza** — OWASP top 10, credenziali, injection, API exposure
3. **Deep research** — validazione business a 360° (mercato, competitor, legal, tech)
4. Solo dopo: soft launch operativo

---

## FASE 0 — Audit Codice (skill: /backend-architect + /code-quality)

Audit completo su:
- `src/cove/` — engine, sanitizer v3, fraud flags, pipeline
- `wa-intelligence/` — daemon, state machine, validator, templates
- `tools/` — PDF generator, on_demand_runner, scrapers
- Verificare: pattern consistenti, error handling, logging, test coverage

Output atteso: report con finding + severity + fix suggeriti

---

## FASE 1 — Audit Sicurezza (skill: /infrastructure-maintainer + security.md)

Verificare su iMac deployato:
- API key auth su porta 9191
- .env permissions (600?)
- WAL mode + busy_timeout su tutti i DB
- Nessun secret nel codice/git history
- Input validation su tutti gli endpoint
- Rate limiting dashboard :8080
- GDPR: zero PII in log, DB, messaggi

Output atteso: security checklist con PASS/FAIL per ogni item

---

## FASE 2 — Deep Research Validazione 360° (skill: /deep-researcher + /trend-researcher)

### 2a. Mercato & Competitor (aggiornamento)
- Bolidem/Autotedesche/Importami: novita' 2026? Nuovi competitor?
- AUTO1/AutoProff/BCA: cambiamenti pricing o copertura IT?
- Market size import EU→IT premium 2025-2026

### 2b. Legal & Compliance
- Prestazione occasionale: limiti reddituali 2026
- Contratto scouting Art.5-bis: validita' giuridica
- GDPR: trattamento dati dealer senza consenso esplicito
- Normativa import veicoli EU: cambiamenti 2026

### 2c. Tech Stack Validation
- PaddleOCR 3.x: stabilita' produzione, alternative emergenti
- WhatsApp Business API vs green API: rischi ban 2026
- DuckDB vs SQLite: scelta corretta per il volume atteso?

### 2d. Product-Market Fit
- Il dealer del Sud Italia paga davvero €800-1200 per questo servizio?
- Esistono dealer che gia' importano da soli? Quanto costa loro?
- Il referral funziona nel mercato dealer family-business?

---

## FASE 3 — Soft Launch Operativo (dopo audit OK)

Se gli audit non bloccano:

0. Test WA reale su TEST_FOUNDER (business hours 8-20)
1. Recovery Car Plus MANUALE da telefono
2. Import 13 dealer enriched nel DB
3. Soft launch 1 dealer: Stefano Auto FG
4. Outreach scaglionato 1/giorno

Dettagli: `prompts/s110_soft_launch_outreach.md`

---

## Prerequisiti

- iMac ONLINE, WA CONNECTED (verificato S111: daemon pid 5796, 23h uptime)
- Sanitizer v3 deployato e testato (KORDICK 2/2 OK, 71.7s)
- TG alerts: configurati e testati
- on_demand_runner.py: deployato su iMac
- PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`

## Note tecniche sanitizer v3

- PaddleOCR 3.x: `ocr.predict()`, modelli `PP-OCRv5_mobile_det` + `en_PP-OCRv5_mobile_rec`
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` obbligatorio
- Timing: 20s/foto dopo model init, ~30s model init one-time
- Seller crop aggressivo: +8% margine, max 35% altezza
