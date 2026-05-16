# S177a — Report esecuzione fix strutturali pre-classifier

**Data**: 2026-05-16 18:00-18:15 (~15min execution)
**Sprint scope-cut**: da S177 (90-150min) → S177a (15min) on CTO decision con 3 deviation pre-flight strutturali.

## Pre-flight deviation rilevate (scope-blocker S177 originale)

### Deviation 1 — Reply errata GIÀ INVIATA (HITL LLM_MULTI bypass)
`pending_replies.reply_e9be3ac6` row inspection:
```
id=reply_e9be3ac6 | created=2026-05-16 17:53:08 | label=LLM_MULTI
approved=0 | sent=1
reply_text={"messages": ["ciao, non ho ancora trovato la bmw x1...", "sto verificando..."]}
```
DB messages OUTBOUND TEST_FOUNDER:
```
17:57:44 OUTBOUND "ciao, senti, non ho ancora trovato la bmw x1 del 2020..."
17:57:48 OUTBOUND "sto verificando alcune opzioni, ti aggiornero entro 24-48h..."
```
Prompt S177 atteso: `approved=0 sent=0` BLOCKED. Reale: `approved=0 sent=1` → reply hallucinata DELIVERED al SIM TEST_FOUNDER mai approvata. **D-07 violation**.

### Deviation 2 — `current_step=DAY1_SENT` (root cause hallucination 17:57)
Lo state non era `DOSSIER_SENT` benché PDF S176 inviato 16:17. Quindi quando arriva inbound 17:52 `"Va bene mi mandi il contratto"`, classifier vede `current_step=DAY1_SENT` → routing fallback su VEHICLE_REQUEST → AMBRA LLM hallucination (stesso pattern S175.0).

### Deviation 3 — D-OPEN-Q2 violation nel template prompt S177 riga 107
`"appena firmato le mando IBAN per il bonifico di 800"` contraddice DECIDED 2026-05-13: **cash a consegna**, IBAN solo path secondario ~10% dealer con P.IVA. Template hardcodato come default = drift cross-conversazione.

## Decisione CTO scope-cut

Audit completo HITL LLM_MULTI bypass = 30+min → sforerebbe context 60% (vincolo #7). Differito S177b con priority HIGH BACKLOG. Per TEST_FOUNDER simulato il bug è non-bloccante (sandbox sicuro), per dealer reali D-15 founder HITL 100% Telegram approve resta path verificato manuale.

**S177a scope (15min)**:
1. State transition `DOSSIER_SENT` post `/send-doc` in `wa-daemon.js`
2. Backfill TEST_FOUNDER `current_step=DOSSIER_SENT`
3. Worker `/api/v1/contract/create` health check
4. BACKLOG entries deviation 1+3 + Worker auth bug

## Esecuzione

### STEP 1 — Patch wa-daemon.js state transition (✅ VERDE)
File: `/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js` (iMac autonomous repo)
Backup: `wa-daemon.js.s177a_bak` (85210 bytes)

Patch applicata via Python idempotent (anchor `incrementDailyStats('sent');` riga ~1115, single-occurrence verified):
```javascript
// S177a: state transition DAY1_SENT/DAY3_SENT → DOSSIER_SENT post-send-doc
try {
    if (dealer_id) {
        const stateDb = getDb();
        const upd = stateDb.prepare("UPDATE conversations SET current_step='DOSSIER_SENT', state_updated_at=datetime('now') WHERE dealer_id=? AND current_step IN ('DAY1_SENT','DAY3_SENT')").run(dealer_id);
        if (upd.changes > 0) log('INFO', `[state] ${dealer_id} → DOSSIER_SENT (post send-doc)`);
    }
} catch (e) {
    log('ERROR', `[state] DOSSIER_SENT update failed for ${dealer_id}: ${e.message}`);
}
```

Validation:
- `node -c wa-daemon.js` → SYNTAX_OK
- `diff` mostra solo 11 righe aggiunte, anchor preservato
- Defensive try/catch (no crash daemon su error)
- Guard `current_step IN ('DAY1_SENT','DAY3_SENT')` evita downgrade da CONTRACT_REQUESTED

### STEP 2 — Backfill TEST_FOUNDER (✅ VERDE)
```sql
UPDATE conversations SET current_step='DOSSIER_SENT', state_updated_at=datetime('now') WHERE dealer_id='TEST_FOUNDER';
```
Result: `TEST_FOUNDER|DOSSIER_SENT|2026-05-16 16:11:52`. State ora consistente con PDF S176 inviato 16:17.

### STEP 3 — Daemon restart (✅ VERDE)
```
pm2 restart argos-wa-daemon
[PM2] [argos-wa-daemon](2) ✓ → online pid 38788
Better-sqlite3 WAL OK, HTTP server up :9191, no syntax/dlopen errors
```

### STEP 4 — Worker contract endpoint health (🔴 401 INVALID_TOKEN)
```bash
curl -X POST 'https://argos-proxy.gianlucanewtech.workers.dev/api/v1/contract/create' \
     -H "X-API-Key: $ARGOS_API_KEY" \
     -d '{"dealer_id":"PROBE_S177","vehicle_ref":"BMW_X1_2022","fee":800}'
→ {"error":"Unauthorized","code":"INVALID_TOKEN"}
```
Token `ARGOS_API_KEY` da `.env` iMac (presente, S164 lo usava). Probabile auth Worker cambiata (Bearer? rotated token?). **BLOCKER S177b** classifier handler. Aggiunto BACKLOG priorità 4-ter.

## Verdict S177a

**VERDE 3/4** (STEP 1-3 VERDE, STEP 4 FLAGGED non bloccante per S177a scope).

Root cause AMBRA hallucination 17:57 **rimossa strutturalmente**: prossima volta che `/send-doc` viene chiamato per qualsiasi dealer, `current_step` si aggiorna a `DOSSIER_SENT` automatico, classifier gating `_matches_contract_request` (da implementare S177b) avrà state corretto.

## Gating S177b (prossima sessione)

Pre-conditions soddisfatte per implementazione classifier CONTRACT_REQUEST:
- ✅ `current_step=DOSSIER_SENT` settato (backfill + auto)
- ✅ INBOUND `msg_1778946767736_b0a4v` preservato per replay
- ❌ Worker auth: risolvere prima di handler (path: ispeziona `wrangler.toml` + `_worker.js` su repo Cloudflare)
- ❌ HITL LLM_MULTI bypass: audit dove `sent=1` viene scritto fuori da bridge_outbound flow

## Output S177a

1. `data/s177a_report.md` — questo file
2. `wa-daemon.js` patch in-place iMac (backup `.s177a_bak`)
3. TEST_FOUNDER `current_step=DOSSIER_SENT` backfill DB iMac
4. `BACKLOG.md` 3 entries aggiornate (P4 risolto, P4-bis HITL LLM_MULTI NEW HIGH, P4-ter Worker 401 NEW)

## Context budget closure

Pre-flight 12% + audit 18% + patch 8% + report 6% = ~44%. Sotto soglia 60%. Sessione VERDE clean.

## Handoff next session

**S177b** = (a) fix Worker auth `/api/v1/contract/create` 401, (b) implement classifier `_matches_contract_request` + handler `_handle_contract_request` in response-analyzer.py, (c) template reply COMPATIBILE D-OPEN-Q2 cash (NO "IBAN bonifico" hardcode → es. `"perfetto. firmiamo qui: {sign_url} — appena firmato ci sentiamo per consegna e saldo. Luca"`), (d) replay TEST_FOUNDER STEP 7-9 reactive.

**S177-bis-hitl** (parallelo o S177c) = audit + fix path auto-send `pending_replies.sent=1` bypass `approved`. Priorità HIGH pre-Day 1 reale Stile Car.
