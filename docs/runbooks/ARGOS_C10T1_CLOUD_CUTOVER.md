# ARGOS C10T1 — Official WhatsApp Cloud API Cutover

This is the canonical deployment procedure for the S292 single-writer runtime after the unofficial `whatsapp-web.js` pairing path became unusable.

The procedure is deliberately fail-closed. **C10 never calls `/resume` and never contacts a dealer.** The goal is to prove the official transport, webhook and runtime while the agent remains `PAUSED` and automation remains disabled.

## 1. Preconditions

Use only a reviewed commit for which `ARGOS S292 Production Contract` is GREEN.

Record it as:

```text
CANDIDATE_SHA=<exact 40-char Git SHA>
```

On the iMac, create/use a dedicated release tree for that exact SHA. Do not deploy into or rewrite the historical source tree and do not touch frozen historical evidence.

Production SQLite files are **external state**, not release artifacts. Resolve their actual machine-local paths before cutover, then configure both explicitly in `.env`:

```text
ARGOS_DB_PATH=<absolute existing dealer_network.sqlite path>
BRIDGE_DB_PATH=<absolute existing bridge.sqlite path>
```

Back up both files before any process cutover. Never overwrite an earlier C10 backup. The release must fail rather than create a fresh empty production DB because a checkout moved.

## 2. Local secrets / `.env`

Create `wa-intelligence/.env` locally on the iMac with mode `0600`. Never commit or paste its values.

Required safety settings:

```text
ARGOS_DB_PATH=<existing primary SQLite path>
BRIDGE_DB_PATH=<existing bridge SQLite path>
ARGOS_WA_TRANSPORT=cloud
ARGOS_AUTOMATION_ENABLED=0
ARGOS_API_KEY=<local secret>
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

Required proactive-template settings:

```text
META_WA_TEMPLATE_LANGUAGE=it
META_WA_TEMPLATE_DAY1_NAME=<approved template name>
META_WA_TEMPLATE_DAY7_NAME=<approved template name>
META_WA_TEMPLATE_DAY12_NAME=<approved template name>
```

The three Meta templates must be approved and their BODY text/language/category must match `wa-intelligence/meta_templates.json`. Cloud initialization revalidates these definitions read-only before reporting connected.

`ARGOS_WA_WEBHOOK_PUBLIC_URL` must be a public HTTPS route whose origin is the canonical daemon on localhost port 9191. Expose **only** `/webhooks/whatsapp`; do not publish `/send`, `/send-doc`, `/resume`, `/pause`, `/qr`, `/health`, `/status` or `/` to the Internet.

The Cloud transport fails closed if required credentials/configuration are incomplete.

## 3. WhatsApp consent is a separate production gate

`outreach_authorized=1` is ARGOS' internal business authorization. It is **not** WhatsApp opt-in and a public/business phone number is not consent evidence.

Business-initiated WhatsApp outreach requires traceable consent with all of:

```text
whatsapp_opt_in=1
whatsapp_opt_in_at=<timestamp>
whatsapp_opt_in_source=<source>
whatsapp_opt_in_evidence_id=<traceable evidence id>
whatsapp_opt_out_at=NULL
```

Use `wa-intelligence/whatsapp_consent.py grant` only when such evidence really exists. Revocation uses `revoke` and immediately invalidates proactive authorization.

Outside the 24-hour customer-service window, ARGOS Cloud sends only the exact Meta template persisted in the claimed bridge row, and only when that row references the dealer's current opt-in evidence. A replaced/revoked consent cannot authorize an older queued row. Free-form documents are blocked outside the 24-hour window.

## 4. Meta onboarding / coexistence

Use the official WhatsApp Business Platform onboarding for the business number. If the account is eligible for WhatsApp Business App + Cloud API coexistence, use the official coexistence onboarding flow rather than attempting another `whatsapp-web.js` QR pairing.

ARGOS treats coexistence events conservatively:

- `messages` text events -> existing inbound pipeline;
- delivery `statuses` -> audit only;
- `smb_message_echoes` -> audit/dedupe only, never dealer inbound and never an outbound trigger;
- `history` and `smb_app_state_sync` -> audit/ignore in C10T1.

Do not enable outreach during onboarding.

## 5. Legacy runtime must remain retired

Before canonical cutover, verify:

- `com.argos.scheduler` is disabled/unloaded;
- the historical writer is not running in parallel;
- there is exactly one process capable of WhatsApp transport;
- no second service is listening as another writer.

Never run the retired `wa-intelligence/deploy.sh`; it exits fail-closed by design.

Production PM2 must enter the writer only through `runtime_entrypoint.py`. Do not start `wa-daemon.js` directly.

## 6. Predeploy gate

From the exact release tree:

```bash
/usr/local/bin/python3.13 tools/scripts/argos_c10_smoke.py \
  --mode predeploy \
  --repo-root "$PWD" \
  --expected-head "$CANDIDATE_SHA" \
  --pretty
```

Required outcome: every required check GREEN, including:

- exact SHA and clean worktree;
- Python 3.13 / Node / PM2 available;
- canonical daemon + all transport/policy adapters parse;
- `.env` exists and is private (`0600` or equivalently no group/other bits);
- `ARGOS_API_KEY` configured;
- `ARGOS_DB_PATH` and `BRIDGE_DB_PATH` explicitly point to existing SQLite state;
- `ARGOS_WA_TRANSPORT=cloud` with complete Meta configuration;
- all Day1/Day7/Day12 proactive template names configured;
- public webhook URL is HTTPS;
- `ARGOS_AUTOMATION_ENABLED != 1`;
- no authorized dealer and no approved/pending bridge row during C10;
- runtime not ACTIVE.

Do not proceed if predeploy is RED.

## 7. Start canonical PM2 runtime — still PAUSED

Use only `wa-intelligence/ecosystem.config.js` from the candidate SHA. Start only the C10 canonical pair:

```text
argos-wa-daemon
argos-outreach-scheduler
```

Do not restart unrelated dashboard/monitor/Telegram processes as part of this transport cutover.

`runtime_entrypoint.py` seeds a missing runtime state as `PAUSED`, ensures consent columns exist, and only then `exec`s the single Node writer. The scheduler remains queue-only and `ARGOS_AUTOMATION_ENABLED=0` keeps it inert.

Do not call `/resume`.

## 8. Postdeploy + official transport gate

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
- Cloud transport `connected=true` after read-only Phone Number ID/token/template validation;
- the public HTTPS webhook route answers the Meta-style GET verification challenge correctly.

No live dealer message is sent by this smoke gate.

## 9. Final C10 safety proof

Before persistence, verify directly from DB/health/process facts:

```text
RUNTIME_STATUS=PAUSED
ARGOS_AUTOMATION_ENABLED=0
OUTREACH_AUTHORIZED=0
BRIDGE_APPROVED_PENDING=0
OUTBOUND_DELTA=0
SINGLE_WRITER=PASS
LEGACY_SCHEDULER=DISABLED
EXTERNAL_PRIMARY_DB=PASS
EXTERNAL_BRIDGE_DB=PASS
META_TEMPLATES_VALIDATED=PASS
PUBLIC_WEBHOOK=PASS
```

Only after all C10 checks are GREEN may `pm2 save` persist the canonical process list.

`pm2 save` is not authorization to contact dealers.

## 10. Delivery ambiguity rule

The Cloud adapter performs no automatic transport retry.

If a final `/messages` POST times out, resets, or returns a 5xx after submission, ARGOS returns:

```text
TRANSPORT_DELIVERY_AMBIGUOUS
```

That error is non-transient at the bridge boundary. The row is blocked for reconciliation rather than automatically resent, preventing duplicate dealer contact.

A failed media upload is different: it cannot itself contact the dealer, so it may be retried by a later bridge cycle.

## 11. C11 is a separate gate

C10 ends with the official transport connected **while ARGOS is still PAUSED**.

The first real WhatsApp send is a separate C11 controlled test to a recipient for whom valid consent is demonstrable. It must not be smuggled into C10. Only after that controlled result may normal activation/outreach be considered.

## 12. Security closure

A Telegram token was exposed during an earlier inspection and must be treated as compromised. Before declaring production security complete:

1. rotate the token at the provider;
2. store the replacement only in the local iMac `.env`;
3. never paste the replacement into chat, Git, logs or a LaunchAgent plist;
4. verify the historical plaintext token is no longer active.

This requirement is independent of the WhatsApp Cloud API gate.

## 13. GitHub/iMac automation lane

Repository workflows may use `IMAC_HOST`, `IMAC_USER` and `IMAC_SSH_KEY` only to reach the target host. Their values must never be printed.

`argos-c10t1-imac-preflight.yml` is read-only and reports one of:

```text
PASS
BLOCKED_SECRETS
SSH_FAILED
```

A blocked SSH lane is an infrastructure blocker, not a code PASS and not permission to bypass C10 manually or merge without the machine gate.

## 14. Rollback

Rollback changes only the transport selection and canonical process runtime; it must never restore the historical writer or legacy scheduler.

The code retains `ARGOS_WA_TRANSPORT=wwebjs` for controlled diagnostic/rollback testing, but the historical QR pairing was demonstrated unreliable. Therefore `wwebjs` is **not** a production-readiness substitute for a failed Cloud API cutover.

If Cloud validation fails, leave ARGOS `PAUSED`, keep automation `0`, restore no outbound path, and investigate before another cutover attempt.
