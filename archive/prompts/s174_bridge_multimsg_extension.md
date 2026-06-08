# S174 ARGOS — bridge_outbound multi-msg + media schema extension

Sessione precedente S173b (2026-05-20): WA dedup VERDE 4/4 T1-T4 + Luke 6/6 fisico + commit 1cdb5e1. Day 1 dealer Aprile gated su questo ticket.

## Stato input verificato S173b

Leggi PRIMA di iniziare:
1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s173_dedup_implementation_closed.md` (closure ciclo)
2. `~/venture-os/wiki/projects/ARGOS/CLOSE-S172-WA-DEDUP.md` (closure doc completo)
3. BACKLOG #S172-1 (target ticket questo prompt)

## Scope S174

Estendere `bridge_outbound` (iMac `~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`) per supportare:
- N>1 messaggi consecutivi (AMBRA reply multi-bubble) — oggi cade su Popen fallback con WARN Telegram
- MessageMedia binario (Day7 voice .mp3, future immagini PDF) — oggi `client.sendMessage` diretto

## Vincoli HARD (immutabili)

- Backup pre-migration obbligatorio (timestamp Unix in nome file)
- Migration idempotente (`ALTER TABLE ADD COLUMN IF NOT EXISTS` non esiste in SQLite → check `PRAGMA table_info` prima)
- Backward compat: NULL media_path = single text msg, msg_sequence DEFAULT 0
- NO physical WA send durante implementation — solo smoke offline + test fisico T-E2E finale
- TEST_FOUNDER_PHONE=393314928901 (autorizzato S172/S173b)
- macOS 11 Big Sur compat (no librerie ML pesanti)
- `force=true` audit log preservato (S173 invariato)
- UNIQUE INDEX `uq_outbound_deal_phone_phase` preservato (NO drop)

## Step S174

### STEP 0 (5min) — pre-flight audit Day7 voice + auto_approve multi-msg

```bash
ssh imac "grep -n 'sendMessage.*MessageMedia\|client.sendMessage' ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js"
grep -n 'Popen.*send\|_run_subprocess_send\|multi-msg' wa-intelligence/response-analyzer.py
```

Output atteso: 1 callsite Day7 voice (wa-daemon.js ~1593-1669) + 1 fallback Popen (response-analyzer.py ~1565-1739, branch `len(messages) > 1`).

### STEP 1 (5min) — smoke distribuzione media-msg storici

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
  SELECT COUNT(*) FROM pending_replies WHERE approved=1 AND json_array_length(json_extract(reply_obj, '\$.messages')) > 1;
\""
```

Se 0 multi-msg storici → scope conferma solo Day7 voice + future-proof N>1. Se >0 → priority alta per migration retroattiva.

### STEP 2 (15min) — schema extension + migration

```sql
-- File: /tmp/migration_bridge_s174.sql
-- Step 1: backup
.shell cp /Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite /Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite.s174-$(date +%s).bak

-- Step 2: check columns (idempotenza)
SELECT name FROM pragma_table_info('bridge_outbound') WHERE name IN ('media_path','media_type','msg_sequence');

-- Step 3: ALTER (esegui solo se output Step 2 = 0 rows)
ALTER TABLE bridge_outbound ADD COLUMN media_path TEXT;
ALTER TABLE bridge_outbound ADD COLUMN media_type TEXT;
ALTER TABLE bridge_outbound ADD COLUMN msg_sequence INTEGER DEFAULT 0;

-- Step 4: index su msg_sequence per ORDER BY efficiente
CREATE INDEX IF NOT EXISTS idx_outbound_sequence ON bridge_outbound(deal_id, msg_sequence) WHERE sent_ts IS NULL;

-- Step 5: verifica
SELECT name FROM pragma_table_info('bridge_outbound');
```

### STEP 3 (10min) — smoke offline `/tmp/smoke_bridge_multimsg.py`

Test cases:
- T1: INSERT 3 rows stesso deal_id con msg_sequence 0/1/2 → SELECT ORDER BY msg_sequence ASC restituisce ordine corretto
- T2: INSERT row con media_path + media_type='audio/ogg' → poll legge correttamente
- T3: UNIQUE constraint ancora attivo (no duplicati silently)
- T4: poll mono-msg (msg_sequence=0, media_path=NULL) backward compat → OK

### STEP 4 (20-30min) — delega `implementer` agent

Prompt implementer:
1. Refactor `comm-broker/wa_bridge.py.queue_outbound()` — accept optional `media_path`, `media_type`, `msg_sequence` params (default None/None/0)
2. Refactor `wa-intelligence/wa-daemon.js.pollBridgeOutbound()` — read media columns, dispatch `MessageMedia.fromFilePath()` se `media_path NOT NULL`, ORDER BY `created_ts ASC, msg_sequence ASC`
3. Migrate `wa-daemon.js` Day7 scheduler (linee ~1593-1669) → INSERT bridge con `media_path=voice_mp3_path, media_type='audio/ogg'`, rimuovi `client.sendMessage` diretto Day7
4. Migrate `wa-intelligence/response-analyzer.py.auto_approve_and_send()` multi-msg branch → loop INSERT bridge con msg_sequence 0..N-1, rimuovi Popen fallback (preserva WARN log come info, no più alert Telegram)
5. NO modifica `/send` HTTP HITL (resta force=true esplicito + precheck 24h S173)

### STEP 5 (15min) — test fisico E2E T-E2E1 + T-E2E2 su 393314928901

- **T-E2E1 multi-msg**: INSERT bridge 3 rows stesso deal_id `S174-MULTI-${TS}`, msg_sequence 0/1/2, body distinti. Atteso: 3 messaggi WA in ordine + 30-60s gap anti-ban
- **T-E2E2 voice**: prep mp3 dummy 5s, INSERT bridge `S174-VOICE-${TS}` con media_path + media_type='audio/ogg'. Atteso: 1 voice note WA recapitato
- Luke verifica fisica → conferma 4/4 (3 multi + 1 voice)

### STEP 6 (10min) — commit + push + closure

```bash
git add comm-broker/wa_bridge.py wa-intelligence/wa-daemon.js wa-intelligence/response-analyzer.py
git commit -m "feat(S174): bridge_outbound multi-msg + media schema extension"
git push origin master
```

Closure doc: `wiki/projects/ARGOS/CLOSE-S174-BRIDGE-EXTENSION.md`
Append `~/venture-os/state/brief-actions.jsonl`

### STEP 7 (5min) — Day 1 dealer Aprile UNGATE check

Verifica gate condition: BACKLOG #S172-1 chiuso, REVIEW S171 #9 chiuso, sanitizer D-32 (S179) status, contract E2E S178 VERDE.

Se tutti VERDE → `prompts/s175_day1_dealer_reale_first.md` (handoff Day 1 Stile Car o nuovo dealer Sud Italia).

## Outcome verde S174

- Schema migration applied + smoke 4/4 PASS
- Implementer 3 file modificati (wa_bridge.py + wa-daemon.js + response-analyzer.py)
- T-E2E1 + T-E2E2 PASS su 393314928901 (Luke conferma fisica)
- Commit pushed master
- CLOSE-S174-BRIDGE-EXTENSION.md scritto
- BACKLOG #S172-1 ✅ CLOSED
- Day 1 dealer Aprile gate condition update

## Context budget S174 atteso

- Start: ~15-20% (lettura closure S173b + audit)
- STEP 0-3 pre-flight + smoke: +10%
- STEP 4 implementer delega (context isolato): +8%
- STEP 5 test fisico E2E: +10%
- STEP 6-7 closure + handoff: +10%
- **Target close**: ≤55%

## Start

`ssh imac "grep -n 'sendMessage.*MessageMedia\|client.sendMessage' ~/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js"` per audit Day7 voice callsite, poi STEP 1 smoke distribuzione.
