# ARGOS C10T1 — Official WhatsApp Cloud API Cutover

This is the canonical deployment procedure for the S292 single-writer runtime after the unofficial `whatsapp-web.js` pairing path became unusable.

The procedure is deliberately fail-closed. **C10 never calls `/resume` and never contacts a dealer.** The goal is to prove the official transport, webhook and runtime while the agent remains `PAUSED` and automation remains disabled.

## 1. Preconditions

Use only a reviewed commit for which `ARGOS S292 Production Contract` is GREEN.

Record it as:

```text
CANDIDATE_SHA=<exact 40-char Git SHA>
```

On the iMac, create/use a dedicated release tree for that exact SHA. Do not deploy into the historical `app-antigravity-auto` source tree and do not touch `ARGOS_C0_FREEZE_20260814_193356`.

The historical production databases remain external state:

```text
PRIMARY_DB=/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite
BRIDGE_DB=/Users/gianlucadistasi/Documents/app-antigravity-auto/comm-broker/bridge.sqlite
```

Back them up before any cutover. Never overwrite an earlier C10 backup.

## 2. Local secrets / `.env`

Create `wa-intelligence/.env` locally on the iMac with mode `0600`. Never commit or paste its values.

Required safety settings:

```text
ARGOS_WA_TRANSPORT=cloud
ARGOS_AUTOMATION_ENABLED=0
ARGOS_API_KEY=<local secret>
BRIDGE_DB_PATH=<existing bridge.sqlite absolute path>
```

Required official Meta settings:

```text
META_GRAPH_API_VERSION=v25.0
META_WA_ACCESS_TOKEN=<local token>
META_WA_PHONE_NUMBER_ID=<phone-number-id>
META_WA_WABA_ID=<waba-id>
META_WA_WEBHOOK_VERIFY_TOKEN=<local random secret>
META_APP_SECRET=<Meta app secret>
ARGOS_WA_WEBHOOK_PUBLIC_URL=https://<public-host>/webhooks/whatsapp
```

`ARGOS_WA_WEBHOOK_PUBLIC_URL` must be a public HTTPS route whose origin is the canonical daemon on localhost port 9191. Expose **only** the webhook path; do not publish `/send`, `/resume`, `/pause`, `/qr` or the health/admin endpoints to the Internet.

The Cloud transport fails closed if required Meta credentials are incomplete.

## 3. Meta onboarding / coexistence

Use the official WhatsApp Business Platform onboarding for the business number. If the account is eligible for WhatsApp Business App + Cloud API coexistence, use the provider/Meta coexistence onboarding flow rather than attempting another `whatsapp-web.js` QR pairing.

ARGOS already treats coexistence events conservatively:

- `messages` text events -> existing inbound pipeline;
- delivery `statuses` -> audit only;
- `smb_message_echoes` -> audit/dedupe only, never dealer inbound and never an outbound trigger;
- `history` and `smb_app_state_sync` -> audit/ignore in C10T1.

Do not enable outreach during onboarding.

## 4. Legacy runtime must remain retired

Before the canonical cutover, verify:

- `com.argos.scheduler` is disabled/unloaded;
- the historical `wa-daemon.js` is not running;
- there is only one process capable of WhatsApp transport;
- no second service is listening as another writer.

Never run the retired `wa-intelligence/deploy.sh`; it now exits fail-closed by design.

## 5. Predeploy gate

From the exact release tree:

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode predeploy \
  --repo-root "$PWD" \
  --expected-head "$CANDIDATE_SHA" \
  --pretty
```

Required outcome: all required checks GREEN, including:

- exact SHA and clean worktree;
- Python 3.13 / Node / PM2 available;
- canonical daemon + both transport adapters parse;
- `.env` present and `ARGOS_API_KEY` configured;
- `ARGOS_WA_TRANSPORT=cloud` with complete Meta configuration;
- public webhook URL is HTTPS;
- `ARGOS_AUTOMATION_ENABLED != 1`;
- primary DB and bridge DB readable;
- no authorized dealer;
- no approved/pending bridge row;
- runtime not ACTIVE.

Do not proceed if predeploy is RED.

## 6. Start canonical PM2 runtime — still PAUSED

Use only `wa-intelligence/ecosystem.config.js` from the candidate SHA.

The canonical processes are:

```text
argos-wa-daemon
argos-outreach-scheduler
```

`runtime_entrypoint.py` seeds a missing runtime state as `PAUSED` before executing the single Node writer. The scheduler remains queue-only and `ARGOS_AUTOMATION_ENABLED=0` keeps it inert.

Do not call `/resume`.

## 7. Postdeploy + official transport gate

After PM2 reports the canonical daemon online:

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode postdeploy \
  --repo-root "$PWD" \
  --expected-head "$CANDIDATE_SHA" \
  --require-connected \
  --pretty
```

For Cloud mode this proves, without sending a WhatsApp message:

- local `/health` is reachable;
- runtime identity is `argos-s292-single-writer`;
- health reports `transport=cloud`;
- `agent_status=PAUSED`;
- bridge enabled;
- Cloud transport `connected=true` after the daemon's read-only Phone Number ID/token validation;
- the public HTTPS webhook route answers the Meta-style GET verification challenge correctly.

No live dealer message is sent by this smoke gate.

## 8. Final C10 safety proof

Before persistence, verify directly from DB/health:

```text
RUNTIME_STATUS=PAUSED
ARGOS_AUTOMATION_ENABLED=0
OUTREACH_AUTHORIZED=0
BRIDGE_APPROVED_PENDING=0
OUTBOUND_DELTA=0
SINGLE_WRITER=PASS
LEGACY_SCHEDULER=DISABLED
```

Only after all C10 checks are GREEN may `pm2 save` persist the canonical process list.

`pm2 save` is not authorization to contact dealers.

## 9. Delivery ambiguity rule

The Cloud adapter performs no automatic transport retry.

If a final `/messages` POST times out, resets, or returns a 5xx after submission, ARGOS returns:

```text
TRANSPORT_DELIVERY_AMBIGUOUS
```

That error is non-transient at the bridge boundary. The row is blocked for manual reconciliation rather than automatically resent, preventing duplicate dealer contact.

A failed media upload is different: it cannot itself contact the dealer, so it may be retried by a later bridge cycle.

## 10. C11 is a separate gate

C10 ends with the official transport connected **while ARGOS is still PAUSED**.

The first real WhatsApp send is a later C11 controlled founder test and must not be smuggled into C10. Only after that controlled test may normal activation/outreach be considered.

## 11. Security closure

A Telegram token was exposed during an earlier C10 inspection and must be treated as compromised. Before declaring production security complete:

1. rotate the token at the provider;
2. store the replacement only in the local iMac `.env`;
3. never paste the replacement into chat, Git, logs or a LaunchAgent plist;
4. verify the historical plaintext token is no longer active.

This requirement is independent of the WhatsApp Cloud API gate.

## 12. Rollback

Rollback changes only the transport selection and canonical process runtime; it must never restore the historical writer or legacy scheduler.

The code retains `ARGOS_WA_TRANSPORT=wwebjs` for controlled rollback/testing, but the historical QR pairing was demonstrated unreliable. Therefore `wwebjs` is **not** a production-readiness substitute for a failed Cloud API cutover.

If Cloud validation fails, leave ARGOS `PAUSED`, keep automation `0`, restore no outbound path, and investigate before another cutover attempt.
