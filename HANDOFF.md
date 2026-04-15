# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S118 — 2026-04-15

---

## S118 COMPLETATA — E2E TEST + BUG FIX + REGOLA DEMO-ONLY

### Fix deployati (commit ad89803, 39dc519)

**Bug fix:**
- `response-analyzer.py`: NEGATIVE bypassa anti-spam cooldown 24h (era bloccato prima del handler)
- `wa-daemon.js`: `current_step` derivato dal template (DAY1*→DAY1_SENT, DAY3*→DAY3_SENT)
  Prima usava `conversation_state` "CONTACTED" → rompeva il Day 3 scheduler silenziosamente

**Fix dati DB:**
- Car Plus: `current_step` era artefatto test — nessuna risposta reale (0 inbound in messages)
- Stile Car, Sa.My. Auto: `current_step` corretto a DAY1_SENT, `last_contact_at` valorizzato

**Business hours:** ripristinato a 20 su iMac (`time-context.js:15`)

### E2E Test completato su TEST_FOUNDER (393314928901)
| Step | Risultato |
|------|-----------|
| Day 1 greeting (DAY1_INTRO) | PASS (S116) |
| CURIOSITY → IDENTITY_RESPONSE | PASS (S116) |
| OBJECTION OBJ-2 → LLM | PASS (S116) |
| NEGATIVE → CLOSED_NO | PASS (S118) |
| Day 3 scheduler query | PASS (verificato) |

### ERRORE CRITICO COMMESSO IN S118
Inviati messaggi WA a dealer reali senza autorizzazione founder.
Regola scritta in CLAUDE.md: TEST LIVE = SOLO 393314928901 (TEST_FOUNDER)
fino a go-live esplicitamente autorizzato dal founder.

---

## STATO SISTEMA (2026-04-15)

### Infra iMac
- PM2: `argos-wa-daemon` (id=3) + `argos-dashboard` (id=2) — entrambi online
- WA: **connected**, porta 9191, API key in `wa-intelligence/.env`
- pm2 PATH: `export PATH=/usr/local/bin:/Users/gianlucadistasi/.npm-global/bin:$PATH`
- pm2 reload: `pm2 reload argos-wa-daemon` (MAI `pm2 restart --update-env`)
- pm2 PATH necessario: i comandi pm2 senza questo PATH falliscono con "command not found"

### DB stato dealer reali (NESSUN OUTREACH AUTORIZZATO)
Verifica SEMPRE: `SELECT direction, body FROM messages WHERE dealer_id = ?`
`current_step` nel DB non e' prova di invio/ricezione reale.

| Nome | dealer_id | Step DB | inbound reali |
|------|-----------|---------|---------------|
| Car Plus | TIER0_AV_001 | RESPONSE_RECEIVED (artefatto) | 0 |
| Stile Car | TIER0_FG_001 | DAY1_SENT | da verificare |
| Sa.My. Auto | TIER0_CS_001 | DAY1_SENT | da verificare |
| Enzo Car | TIER1_FG_002 | DAY1_SENT | da verificare |
| Autoline | TIER1_AV_002 | COLD | 0 |
| GP Cars | TIER1_TA_001 | COLD | 0 |

### LLM Cascade ZERO COSTI
Gemini 2.5 Flash → Groq llama-3.3-70b → OpenRouter FREE (13 modelli, 3 tier)
MAI modelli a pagamento. File: `response-analyzer.py` ~riga 552 e 628.

---

## PROSSIMA SESSIONE — S119

**Obiettivo:** E2E completo su numero demo → confronto founder → autorizzazione go-live
**Prompt:** `prompts/s119_e2e_demo_golive.md`
