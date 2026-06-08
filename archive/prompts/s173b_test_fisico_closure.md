# S173b ARGOS — WA dedup test fisico T1-T4 + closure + handoff S174

Sessione precedente S173 (2026-05-20): implementation VERDE, deploy iMac VERDE, smoke 4/4 PASS. Test fisico T1-T4 + commit + closure deferred per context gate 56%.

## Stato input verificato S173

Leggi PRIMA di iniziare:
1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/s173_implementation_done_test_t1t4_pending.md` (stato preciso)
2. `~/venture-os/wiki/projects/ARGOS/HANDOFF-S173-WA-DEDUP.md` (decisioni scope, Appendix C memory updates, Appendix D BACKLOG)
3. Working tree MacBook (`git status`): 4 file in-scope dirty + 3 out-of-scope (auth.py + argos.db + db_utils.py + .s177b_bak)

## Stato runtime iMac (verificato S173 ~13:00)

- Daemon `argos-wa-daemon` online, restart S173 12:55:13, zero errori boot
- UNIQUE INDEX `uq_outbound_deal_phone_phase` attivo su bridge.sqlite
- Migration SQL idempotente (`/tmp/migration_bridge_s172.sql`)
- Smoke offline script (`/tmp/smoke_bridge_unique.py`) 4/4 PASS
- Test setup script (`/tmp/s173_test_setup.sh`) deployato, baseline pulita (0 pending, 0 sent last 1h)
- Codice nuovo già attivo su iMac repo `~/Documents/app-antigravity-auto/wa-intelligence/` (sync implementer S173)

## Vincoli HARD (immutabili)

- Test fisico su **393314928901** (FLUXION SIM, autorizzato S172 override REVIEW S171 #10)
- `force=true` audit log obbligatorio → `~/venture-os/state/argos-force-overrides.jsonl`
- iMac SSH PM2 workaround: `ssh imac "source ~/.zshrc; pm2 ..."`
- BRIDGE_DB_PATH = `/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite`
- NO commit prima di T1-T4 PASS 4/4
- NO modifiche codice salvo bug-fix da T1-T4 fail
- BACKLOG #S172-1 multi-msg + media schema = gating Day 1 dealer Aprile

## Step S173b

### STEP 4.1 — T1 single send (5min)

```bash
ssh imac "bash /tmp/s173_test_setup.sh t1"
# wait 60s
ssh imac "bash /tmp/s173_test_setup.sh t1-verify"
```

Luke verifica WA Business 393314928901:
- Expect: 1 messaggio testo "Test S173 T1 ${TS} — single send check"
- Screenshot opzionale
- DB row: `sent_ts NOT NULL`, `sent_status='ok'`, `wa_msg_id` reale, `attempt_count=1`

### STEP 4.2 — T2 3 distinti (5-7min, anti-ban 30-90s gap)

```bash
ssh imac "bash /tmp/s173_test_setup.sh t2"
# wait ~120-180s per 3 cycle poll + anti-ban
ssh imac "bash /tmp/s173_test_setup.sh t2-verify"
```

Luke verifica: 3 messaggi distinti (T2-A day1, T2-B day3, T2-C day7), ordine non garantito (anti-ban random).

### STEP 4.3 — T3 race UNIQUE (1min, no msg WA atteso)

```bash
ssh imac "bash /tmp/s173_test_setup.sh t3"
```

Expect output:
```
[OK] INSERT 1
[OK] INSERT 2 silenced by INSERT OR IGNORE
Row count for deal_id=S173-T3-${TS}: 1 (expect 1)
```

Luke verifica: 1 messaggio in più ricevuto WA (relativo al primo INSERT, secondo silenced).

### STEP 4.4 — T4 restart resilience (5min)

```bash
ssh imac "bash /tmp/s173_test_setup.sh t4-prep"
# entro 5s:
ssh imac "source ~/.zshrc; pm2 restart argos-wa-daemon"
# wait 60-90s
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/comm-broker/bridge.sqlite \"
  SELECT deal_id, sent_ts, sent_status, wa_msg_id, attempt_count, processing_ts
  FROM bridge_outbound WHERE deal_id LIKE 'S173-T4-%' ORDER BY created_ts DESC LIMIT 1;
\""
```

Luke verifica: 1 messaggio WA (no doppio post-restart), DB `sent_ts NOT NULL`, `attempt_count=1`.

### STEP 4.5 — cleanup test rows (1min)

```bash
ssh imac "bash /tmp/s173_test_setup.sh cleanup"
```

### STEP 4 outcome

- 4/4 PASS → STEP 5 commit + closure
- ≤3/4 PASS → analisi fail, fix mirato, ri-run test fallito (se context permette) o handoff S173c

### STEP 5 — commit + push + closure (10min)

```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git add comm-broker/wa_bridge.py \
        wa-intelligence/wa-daemon.js \
        wa-intelligence/response-analyzer.py \
        wa-intelligence/telegram-handler.py
git commit -m "$(cat <<'EOF'
fix(S173): WA daemon dedup — multi-path → bridge canonical queue

Root cause S170 duplicate sends: 7 callsite client.sendMessage, solo pollBridgeOutbound protetto da processing_ts lock.

Fix:
- Day3 scheduler → INSERT bridge_outbound (single writer)
- Day7 + /send: precheck 24h + force=true esplicito + audit log
- auto_approve_and_send mono-msg → bridge, multi-msg → Popen fallback (BACKLOG #S172-1)
- UNIQUE INDEX uq_outbound_deal_phone_phase (migration applicata iMac S173)
- INSERT OR IGNORE in wa_bridge.py

Smoke offline: 4/4 PASS
Test fisico T1-T4: 4/4 PASS su 393314928901
Sblocca: REVIEW S171 issue #9, Day 1 dealer Aprile (gated su BACKLOG #S172-1 multi-msg)

Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>
EOF
)"
git push origin master
```

NB su out-of-scope (`auth.py`, `argos.db`, `db_utils.py`, `.s177b_bak`): NON includere in commit S173. Audit + decisione separata in S173c o BACKLOG.

Closure doc: `wiki/projects/ARGOS/CLOSE-S172-WA-DEDUP.md` con:
- Root cause B confermato
- Fix scope split
- Smoke 4/4 + T1-T4 4/4
- File modificati + diff stat
- Migration applied + backup ts 1779272082
- REVIEW S171 issue #9 ✅ CLOSED

Append `~/venture-os/state/brief-actions.jsonl`:
```json
{"date":"2026-05-XX","brief_read":true,"action_taken":"S173_wa_dedup_implementation","gate":"P3_closed_P5_unblocked","notes":"single writer principle bridge canonical, 4/4 T1-T4 pass"}
```

Memory updates Appendix C HANDOFF (3 file):
1. `feedback_single_writer_principle_bridge.md`
2. `feedback_test_founder_3314928901_argos_authorized.md`
3. `s173_dedup_implementation_closed.md` (sostituisce `s173_implementation_done_test_t1t4_pending.md`)

### STEP 6 — handoff S174 BACKLOG #S172-1 (5min)

Append `BACKLOG.md` ticket #S172-1 (Appendix D HANDOFF S173).

Crea `prompts/s174_bridge_multimsg_extension.md`:
- Scope: schema extension `bridge_outbound` (media_path, media_type, msg_sequence)
- Migrate Day7 voice → bridge
- Migrate auto_approve multi-msg → bridge
- E2E test AMBRA 3 bubble → 3 WA messages distinte
- ETA 2026-04-25 (gating Day 1 dealer Aprile)
- Owner: implementer agent S174

## Outcome verde S173b

- T1-T4 4/4 PASS
- Commit pushed master
- CLOSE-S172-WA-DEDUP.md scritto
- REVIEW S171 issue #9 chiusa
- BACKLOG.md #S172-1 aggiunto
- Memory updates 3 file
- prompts/s174_bridge_multimsg_extension.md pronto

## Context budget S173b atteso

- Start: ~15-20% (lettura memory S173 + handoff S172)
- STEP 4 test fisico 4 cycle: +15-20%
- STEP 5 commit + closure: +8-10%
- STEP 6 handoff S174: +5%
- **Target close**: ≤55%

## Start

`ssh imac "bash /tmp/s173_test_setup.sh baseline"` per verificare stato pulito, poi STEP 4.1 T1.
