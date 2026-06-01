# S173 ARGOS — WA daemon dedup IMPLEMENTATION

Sessione precedente S172 (2026-05-20): diagnosi VERDE, scope decisions approvate founder, backup eseguito, implementation deferred per context budget 62% (vincolo #7).

## Stato input verificato

Leggi PRIMA di iniziare (ordine obbligatorio):
1. `~/venture-os/wiki/projects/ARGOS/HANDOFF-S173-WA-DEDUP.md` — handoff completo (decisioni scope, valutazione enterprise, piano, smoke script, BACKLOG)
2. `~/venture-os/wiki/projects/ARGOS/PROMPT-S172-WA-DAEMON-DEDUP.md` — audit Fase 2 dettagliato (sezioni A/B/C/D/E, diff testuali)
3. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md` — entry S172 data 2026-05-20

## Vincoli HARD (immutabili)

- backup già fatto (timestamp **1779272082**) — NON re-fare
- Scope split (approved S172):
  - Day3 → bridge
  - Day7 → diretto + precheck 24h + force=true esplicito
  - auto_approve_and_send mono-msg → bridge
  - auto_approve_and_send multi-msg → Popen fallback + Telegram alert
- force=true esplicito sempre (NO exclusion logic su template_phase)
- Test fisico su **393314928901** (autorizzato S172 — override REVIEW S171 #10 motivato: FLUXION zero contatti esterni)
- BACKLOG #S172-1 multi-msg + media schema = **gating Day 1 dealer Aprile**
- macOS 11 Big Sur compat
- `force=true` audit log obbligatorio → `~/venture-os/state/argos-force-overrides.jsonl`
- iMac SSH PM2 workaround: `ssh imac "source ~/.zshrc; pm2 ..."`
- `BRIDGE_DB_PATH=/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`

## Step S173

### STEP 0 — smoke distribuzione reply mono vs multi-msg (5min)

Verifica condizione scope split (founder caveat S172):

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite '
  SELECT reply_id,
         LENGTH(reply_text) as chars,
         (LENGTH(reply_text) - LENGTH(REPLACE(reply_text, char(10), \"\"))) as newlines
  FROM pending_replies
  WHERE approved=1
  ORDER BY created_at DESC
  LIMIT 30;
'"
```

Decision tree:
- newlines > 2 in >50% righe → reply multi-paragraph spesso → **STOP, riapri scope S172** (multi-msg blocca >50% beneficio)
- newlines ≤ 2 in ≥50% → mono-msg dominante → procedi STEP 1

Se schema diverso (pending_replies non esiste o reply_text JSON): audit `response-analyzer.py` per identificare codepath reale dei reply storici.

### STEP 1 — smoke test offline UNIQUE constraint (5min)

Crea `/tmp/smoke_bridge_unique.py` su iMac da Appendix A di HANDOFF-S173-WA-DEDUP.md.

NOTA: deve PASS solo DOPO migration UNIQUE INDEX (STEP 3). Prima della migration, INSERT 2 NON fallirà → test atteso fallirà. Eseguire DOPO STEP 3.

### STEP 2 — delega implementer agent (20-30min agent isolato)

Prompt implementer deve includere:
- Full context HANDOFF-S173-WA-DEDUP.md
- Audit Fase 2 (PROMPT-S172-WA-DAEMON-DEDUP.md sezioni A/B/C/D/E con diff testuali)
- Scope decisions founder-approved (1)(2)(3)
- Tutti i vincoli HARD sopra
- Output atteso: 5 file modificati committed:
  1. `wa-intelligence/wa-daemon.js` (Day3 refactor + Day7 precheck + /send precheck + 2 helper bridge insert)
  2. `wa-intelligence/response-analyzer.py` (auto_approve_and_send mono-msg → bridge, multi-msg → Popen + alert)
  3. `wa-intelligence/telegram-handler.py` (precheck 24h + force=true parsing + audit log jsonl)
  4. `comm-broker/wa_bridge.py` (INSERT OR IGNORE / ON CONFLICT DO NOTHING)
  5. `wa-intelligence/ecosystem.config.js` (SHARED_ENV +BRIDGE_DB_PATH per response-analyzer)
- Migration SQL applicata via SSH iMac (Appendix B HANDOFF)
- Smoke test offline 4/4 PASS PRIMA del commit
- Commit message format dal PROMPT-S172 sezione STEP 4 VERDE

### STEP 3 — applica migration SQL iMac (5min)

```bash
cat > /tmp/migration_bridge_s172.sql <<'EOF'
-- Step 1 verifica
SELECT deal_id, target_phone, template_phase, COUNT(*)
FROM bridge_outbound WHERE sent_ts IS NULL
GROUP BY 1,2,3 HAVING COUNT(*) > 1;

-- Step 2 INDEX
CREATE UNIQUE INDEX IF NOT EXISTS uq_outbound_deal_phone_phase
    ON bridge_outbound(deal_id, target_phone, template_phase)
    WHERE sent_ts IS NULL;
EOF
scp /tmp/migration_bridge_s172.sql imac:/tmp/
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite < /tmp/migration_bridge_s172.sql"
```

### STEP 4 — test fisico T1-T4 su 393314928901 (20-30min LUKE FISICO RICHIESTO)

Luke attivo su WhatsApp Business 393314928901 (FLUXION SIM, autorizzato test ARGOS).

T1: queue 1 bridge row test → Luke screenshot WhatsApp = 1 messaggio
T2: queue 3 simultanei distinti → 3 messaggi distinti
T3: simula race Day3 + auto_approve_and_send stesso (deal_id, phone, template_phase) → UNIQUE blocca 2°, solo 1 messaggio
T4: `pm2 restart argos-wa-daemon` mid-send → no re-invio post-restart

Outcome:
- 4/4 PASS → VERDE
- ≤3/4 PASS → GIALLO handoff S174 con stato + diff parziale

### STEP 5 — commit + push + closure doc (10min)

- `wiki/projects/ARGOS/CLOSE-S172-WA-DEDUP.md` con root cause + fix + test results
- Append `~/venture-os/state/brief-actions.jsonl`:
  ```json
  {"date":"2026-05-XX","brief_read":true,"action_taken":"S172_wa_dedup_fix","gate":"P3_closed_P5_unblocked","notes":"single writer principle bridge canonical"}
  ```
- REVIEW S171 issue #9 chiusa (markdown ✅ CLOSED)
- Memory updates da Appendix C HANDOFF (3 nuovi memory file)
- `BACKLOG.md` append ticket #S172-1 (Appendix D HANDOFF)

### STEP 6 — handoff parallelo S174 per BACKLOG #S172-1 (3min)

Prepara prompt `prompts/s174_bridge_multimsg_extension.md` con:
- Scope: schema extension + Day7 voice migration + auto_approve multi-msg migration
- Acceptance criteria (Definition of Done) da HANDOFF Section "Recommendation enterprise"
- ETA target 2026-04-25
- Gating: Day 1 dealer reale Aprile bloccato fino merge S174

## Outcome verde sessione S173

- 4/4 test fisici PASS
- Smoke offline 4/4 PASS
- Commit pushed master
- REVIEW S171 issue #9 chiusa
- HANDOFF S174 pronto (BACKLOG multi-msg)
- Day 1 Stile Car STILL gated (su BACKLOG #S172-1 merge)

## Context budget S173 atteso

- Start: ~15-20% (lettura HANDOFF + PROMPT-S172 + MEMORY entry)
- STEP 0-1: +5% (query SSH + smoke)
- STEP 2 implementer delega: +5-10% (context isolato agent, solo output return)
- STEP 3 migration: +2%
- STEP 4 test fisico: +15-20% (4 cycle test, ogni cycle query DB + verify)
- STEP 5-6 closure: +5%
- **Target close**: ≤55% (sotto soglia 60% vincolo #7)

## Start

Leggi HANDOFF-S173-WA-DEDUP.md completo (Section "STATO INPUT" + "DECISIONI SCOPE" + "APPENDIX A/B/C/D"), poi STEP 0 smoke distribuzione reply.
