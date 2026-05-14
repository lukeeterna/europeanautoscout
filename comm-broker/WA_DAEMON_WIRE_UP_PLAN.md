# wa-daemon wire-up plan (S168 ship — designed S167 CTO)

> **STATUS S168 2026-05-14**: hook 1 + hook 2 + schema migration APPLIED in commit S168.
> Tests regression: 17/17 PASS post-patch. `node --check` OK. Schema migration smoke verificato
> su DB legacy (ALTER idempotente, `mark_sent(wa_msg_id)` roundtrip).
>
> **STATUS S169 2026-05-14**: E2E reale ATTIVATO su iMac production (PID 33804, uptime stable).
> Sequenza autonoma:
> 1. rsync wa-daemon.js + ecosystem.config.js + comm-broker/ → iMac `~/Documents/app-antigravity-auto/`
> 2. `npm rebuild --build-from-source better-sqlite3` (Node 20.11.0 NODE_MODULE_VERSION 115)
> 3. `pip install python-statemachine jinja2 groq Pillow imagehash` in `comm-broker/.venv` Python 3.9
> 4. Backup `.wwebjs_auth/` (18MB tar.gz)
> 5. Append `BRIDGE_DB_PATH` + `BRIDGE_POLL_INTERVAL_MS` to `wa-intelligence/.env`
> 6. Patch `ecosystem.config.js` SHARED_ENV: expose BRIDGE_DB_PATH + BRIDGE_POLL_INTERVAL_MS + GROQ_API_KEY a process.env del daemon (mancavano da SHARED_ENV originale)
> 7. `pm2 delete + pm2 start ecosystem.config.js` (reload config completo)
>
> **Verifica E2E**:
> - `Client PRONTO` + `[bridge] polling enabled every 30000ms (batch=5, anti-ban 30-90s)` in `/tmp/argos-wa-daemon-out.log`
> - V3-rev2 queue→approve→poll(30s)→`client.sendMessage('393314928901@c.us')`
> - bridge_outbound id=1: `sent_status='ok'`, `wa_msg_id='true_141115562971357@lid_3EB0B9613EDB1E3D36675B'`
> - Founder phone (393314928901) confermato ricezione messaggio
>
> Path portable via `__dirname` (no hardcoded dir name) — funziona iMac `app-antigravity-auto` + MacBook `combaretrovamiauto-enterprise` (stesso git remote `europeanautoscout`).


> Patch additive feature-flagged a `wa-intelligence/wa-daemon.js` (1568 righe, production PM2 stack). Modifications scope-bounded e reversibili. Pattern S159 anti-pattern (auto_approve_and_send riscritto 3 volte) mitigation: HITL strict D-07.

## Vincoli operativi non-negoziabili

- **NO touch** `CONFIG.SESSION_ID` o `LocalAuth` path (riauth QR catastrophic)
- **NO touch** core dispatcher logic o scheduler Day3/7
- **NO auto-send** da bridge_outbound senza `approved_ts IS NOT NULL` (HITL D-07)
- Feature-flagged via env `BRIDGE_DB_PATH` — se non set → no-op completo
- Reversibile via git revert single commit

## Hook point 1 — Inbound dual-write to bridge_inbound

**Location**: wa-daemon.js line ~708 `client.on('message_create', ...)`

**Patch (additive, after esistente INSERT INTO messages)**:

```javascript
// ── BRIDGE WIRE-UP S168 — additive feature-flagged ─────────────
const BRIDGE_DB = process.env.BRIDGE_DB_PATH || '';
let _bridgeDb = null;
function getBridgeDb() {
    if (!BRIDGE_DB) return null;
    if (_bridgeDb) return _bridgeDb;
    try {
        _bridgeDb = new Database(BRIDGE_DB, { timeout: 5000 });
        _bridgeDb.pragma('journal_mode = WAL');
        return _bridgeDb;
    } catch (e) {
        log('WARN', `bridge_db open failed: ${e.message}`);
        return null;
    }
}

function bridgeIngestInbound(msg) {
    const bdb = getBridgeDb();
    if (!bdb) return;
    try {
        bdb.prepare(`
            INSERT INTO bridge_inbound (msg_id, party_role, party_phone, party_alias, body, received_ts)
            VALUES (?, ?, ?, NULL, ?, ?)
            ON CONFLICT(msg_id) DO NOTHING
        `).run(
            msg.id._serialized || msg.id,
            'dealer',  // role inferenza: TBD by phone lookup bridge_parties
            msg.from.replace('@c.us', ''),
            msg.body || '',
            Math.floor(Date.now() / 1000)
        );
    } catch (e) {
        log('WARN', `bridge_ingest_inbound failed: ${e.message}`);
    }
}

// Inside client.on('message_create', ...) handler, after existing INSERT INTO messages:
//   if (!msg.fromMe) bridgeIngestInbound(msg);
```

**Notes**:
- `party_role` default 'dealer' è temporaneo. Per identity masking correct, lookup `bridge_parties WHERE phone = msg.from`. Se trova → use role registered. Se non trova → log + skip (unknown party).
- `msg.id._serialized` è il WA msg ID, idempotent ON CONFLICT.
- Failure mode: log warn + continue (bridge_db down ≠ stop wa-daemon).

## Hook point 2 — Outbound poll from bridge_outbound

**Location**: wa-daemon.js init section, dopo `client.initialize()`.

**Patch (additive setInterval poll)**:

```javascript
const BRIDGE_POLL_INTERVAL_MS = parseInt(process.env.BRIDGE_POLL_INTERVAL_MS || '30000');
const BRIDGE_ANTI_BAN_DELAY_MS_MIN = 30000;  // riusa D-04 anti-ban
const BRIDGE_ANTI_BAN_DELAY_MS_MAX = 90000;

async function pollBridgeOutbound() {
    const bdb = getBridgeDb();
    if (!bdb) return;
    try {
        const pending = bdb.prepare(`
            SELECT id, deal_id, target_role, target_phone, body, template_phase
            FROM bridge_outbound
            WHERE approved_ts IS NOT NULL AND sent_ts IS NULL
            ORDER BY approved_ts ASC
            LIMIT 5
        `).all();

        for (const row of pending) {
            const chatId = `${row.target_phone}@c.us`;
            try {
                log('INFO', `[bridge] sending outbound id=${row.id} deal=${row.deal_id} phase=${row.template_phase}`);
                const sentMsg = await client.sendMessage(chatId, row.body);
                bdb.prepare(`
                    UPDATE bridge_outbound SET sent_ts = ?, sent_status = 'ok' WHERE id = ?
                `).run(Math.floor(Date.now() / 1000), row.id);
                log('INFO', `[bridge] sent ok wa_msg_id=${sentMsg.id._serialized}`);

                // Anti-ban delay 30-90s before next (riusa pattern D-04)
                const delay = BRIDGE_ANTI_BAN_DELAY_MS_MIN +
                              Math.random() * (BRIDGE_ANTI_BAN_DELAY_MS_MAX - BRIDGE_ANTI_BAN_DELAY_MS_MIN);
                await new Promise(r => setTimeout(r, delay));
            } catch (e) {
                log('ERROR', `[bridge] send failed id=${row.id}: ${e.message}`);
                bdb.prepare(`
                    UPDATE bridge_outbound SET sent_status = ? WHERE id = ?
                `).run(`error: ${e.message.substring(0, 200)}`, row.id);
            }
        }
    } catch (e) {
        log('ERROR', `[bridge] poll error: ${e.message}`);
    }
}

// Start polling AFTER client ready (existing pattern)
client.on('ready', () => {
    // ... existing ready handler ...
    if (BRIDGE_DB) {
        log('INFO', `[bridge] polling enabled every ${BRIDGE_POLL_INTERVAL_MS}ms`);
        setInterval(pollBridgeOutbound, BRIDGE_POLL_INTERVAL_MS);
    }
});
```

**Notes**:
- LIMIT 5 per poll = max 5 send per 30s ciclo → throughput cap built-in
- Anti-ban delay 30-90s tra send rispetta D-04 conseguenze
- Errori send → status logged, no retry automatico (HITL inspect + re-approve manual)

## Hook point 3 — Schema bridge_outbound add wa_msg_id column

```sql
ALTER TABLE bridge_outbound ADD COLUMN wa_msg_id TEXT;
```

Per audit trail: link tra bridge_outbound.id e WA message ID reale ricevuto da sendMessage.

## Test plan E2E manuale S168

```bash
# 1. Setup bridge DB con test party (single dealer = TEST_FOUNDER)
.venv/bin/python -c "
from wa_bridge import WABridge
from deal_state_machine import Deal, DealStateMachine
bridge = WABridge('/tmp/bridge.sqlite', '/tmp/deals.sqlite')
DealStateMachine(Deal(deal_id='TEST-001', dealer_alias='TEST', seller_alias='SELF'), '/tmp/deals.sqlite')
bridge.register_party('393314928901', 'dealer', 'TEST', 'IT')
"

# 2. Configure wa-daemon con BRIDGE_DB_PATH
echo "BRIDGE_DB_PATH=/tmp/bridge.sqlite" >> ~/Documents/combaretrovamiauto-enterprise/wa-intelligence/.env

# 3. Restart wa-daemon
pm2 restart argos-wa-daemon

# 4. Verify polling enabled (log)
pm2 logs argos-wa-daemon --lines 20 | grep "bridge"

# 5. Inject outbound candidate manually (HITL approved)
.venv/bin/python -c "
from wa_bridge import WABridge, OutboundCandidate
bridge = WABridge('/tmp/bridge.sqlite', '/tmp/deals.sqlite')
oid = bridge.queue_outbound(OutboundCandidate(
    deal_id='TEST-001', target_role='dealer', target_phone='393314928901',
    template_phase='offer', template_lang='it',
    body='[TEST BRIDGE] Hello from comm-broker pipeline',
    state_at_send='offer_sent',
))
bridge.approve_outbound(oid)
print(f'queued + approved: {oid}')
"

# 6. Wait <30s for poll, verify TEST_FOUNDER receives msg
# 7. Reply from TEST_FOUNDER → verify bridge_inbound row created
sqlite3 /tmp/bridge.sqlite "SELECT * FROM bridge_inbound;"
```

## Rollback plan

```bash
# 1. Stop wa-daemon
pm2 stop argos-wa-daemon

# 2. Unset env
sed -i '' '/^BRIDGE_DB_PATH=/d' ~/Documents/combaretrovamiauto-enterprise/wa-intelligence/.env

# 3. Restart
pm2 restart argos-wa-daemon

# OR full revert
git -C ~/Documents/combaretrovamiauto-enterprise revert <commit-hash-wire-up>
pm2 restart argos-wa-daemon
```

## DoD (Definition of Done) S168

- [x] Patch wa-daemon.js applied (hook 1 + hook 2 + schema alter) — commit S168
- [x] Schema migration idempotent verificato su legacy DB
- [x] Tests regression 17/17 PASS post-patch
- [x] `node --check wa-daemon.js` OK
- [x] **S169**: ecosystem.config.js BASE portable via `__dirname` (funziona entrambe le macchine)
- [x] **S169**: `BRIDGE_DB_PATH` + `BRIDGE_POLL_INTERVAL_MS` aggiunti a iMac `.env`
- [x] **S169**: SHARED_ENV in ecosystem.config.js expose BRIDGE_DB_PATH + GROQ_API_KEY a daemon process.env
- [x] **S169**: pm2 reload (delete+start) → `Client PRONTO` + `[bridge] polling enabled`
- [x] **S169 Test E2E outbound**: V3-rev2 queue→approve→sendMessage→`sent_status='ok'`+`wa_msg_id` valido + founder phone receipt confermato
- [ ] **S170**: Test E2E inbound: dealer/founder reply → bridge_inbound INSERT → classifier Groq → state transition
- [ ] No regression Day3/7 scheduler (verify pm2 logs scheduler)
- [ ] No regression anti-ban delay esistente
- [x] Commit + rollback plan documented

## Stima tempo S168

- Patch + test base: 1h
- Test E2E reale con TEST_FOUNDER: 30 min (singolo send + 1 reply)
- Verify no regression scheduler: 30 min
- Edge case handling (errori send, bridge_db lock): 30 min
- **Totale: ~2-3h focused session**

## Riferimenti

- wa-daemon.js production: `wa-intelligence/wa-daemon.js` (1568 righe, PM2 managed)
- wa_bridge schema: `comm-broker/wa_bridge.py` BRIDGE_SCHEMA
- D-06 stack ARGOS + D-07 HITL + D-22 F1 SHIPPED
- VOS handoff S168 `~/venture-os/.claude/PROMPT-S168.md`
