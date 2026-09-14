# ARGOS S292 — Canonical WhatsApp Runtime Architecture

ARGOS uses a **single outbound policy boundary** and a transport adapter. The production target is the official WhatsApp Business Platform / Cloud API; the historical `whatsapp-web.js` adapter is retained only as a controlled compatibility/rollback path.

## Runtime topology

```text
                           ┌──────────────────────────┐
Dealer inbound ───────────>│ Official Meta webhook    │
                           │ /webhooks/whatsapp       │
                           └────────────┬─────────────┘
                                        │ signature verified
                                        v
                               handleInbound()
                                        │
                      persist -> bridge -> analyzer

HTTP /send, /send-doc          approved bridge rows
          │                              │
          └──────────────┬───────────────┘
                         v
                    guardedSend()
                         │
          assertTransportPreconditions()
          - runtime must be ACTIVE
          - business hours
          - target/dealer match
          - global/dealer daily limits
                         │
                  finalPolicyGuard()
                         │
             dossier verifier (documents)
                         │
                         v
                  activeTransport
             ┌───────────┴───────────┐
             │                       │
      CloudApiTransport       WwebjsTransport
      official production     legacy compatibility
```

`guardedSend()` is the only daemon path that may call `activeTransport.sendText()` or `activeTransport.sendDocument()`. CI scans all production JavaScript to prevent a second send boundary.

## Production safety invariants

1. **First boot is PAUSED.** `runtime_entrypoint.py` creates a missing `agent_status` as `PAUSED` before execing the Node daemon.
2. **PAUSED blocks transport.** `assertTransportPreconditions()` fails closed before any transport call.
3. **Single writer.** Bridge, `/send` and `/send-doc` all converge on `guardedSend()`.
4. **Legacy bypasses retired.** `/send-multi` and `/send-voice` return HTTP 410.
5. **Scheduler is queue-only.** `outreach_scheduler.py` never sends WhatsApp itself and defaults disabled through `ARGOS_AUTOMATION_ENABLED=0`.
6. **Legacy launchd scheduler stays disabled.** `com.argos.scheduler` is not part of the canonical runtime.
7. **Evidence before outbound.** `outbound_guard.py` runs immediately before transport and ambiguous/legacy bridge rows fail closed.
8. **No delivery guessing.** Cloud API message IDs come from Meta; ARGOS never invents a successful `wamid`.
9. **No duplicate-send retry on ambiguous delivery.** Timeout/reset or 5xx on the final Cloud `/messages` request becomes `TRANSPORT_DELIVERY_AMBIGUOUS`, non-transient at the bridge boundary.
10. **No secret in Git.** Meta tokens, app secret, webhook verification token and ARGOS API key live only in the local `.env`.

## Official Cloud transport

Selected with:

```text
ARGOS_WA_TRANSPORT=cloud
```

The adapter uses only Node built-ins and the Graph API:

- read-only initialize: `GET /{PHONE_NUMBER_ID}?fields=id,display_phone_number`;
- text outbound: `POST /{PHONE_NUMBER_ID}/messages`;
- document outbound: upload to `/{PHONE_NUMBER_ID}/media`, then `POST /{PHONE_NUMBER_ID}/messages`;
- no automatic retry inside the transport.

`connected=true` means the Cloud transport successfully validated the configured token/Phone Number ID. It does **not** mean the ARGOS runtime is ACTIVE. The desired C10 state is:

```text
connected=true
agent_status=PAUSED
ARGOS_AUTOMATION_ENABLED=0
```

## Webhook boundary

The canonical daemon exposes only one Meta callback path:

```text
/webhooks/whatsapp
```

For POST deliveries it reads the raw body, verifies `X-Hub-Signature-256` using HMAC-SHA256 and `META_APP_SECRET` with constant-time comparison, and parses JSON only after verification succeeds.

Handled conservatively:

- `messages` text -> normalized into the existing inbound persistence/analyzer path;
- delivery `statuses` -> audit only;
- `smb_message_echoes` -> audit/dedupe only, never dealer inbound and never outbound;
- `history` / `smb_app_state_sync` -> audit/ignore in C10T1.

The public reverse proxy/tunnel must expose **only this webhook path**, not `/send`, `/resume`, `/pause`, `/qr` or local health/admin endpoints.

## Process model

PM2 canonical processes for C10 are:

```text
argos-wa-daemon
argos-outreach-scheduler
```

Existing dashboard/Telegram/monitor processes are observability/admin components and are not WhatsApp writers.

The old pre-S292 `wa-intelligence/deploy.sh` is intentionally retired because it enabled the historical scheduler and mutated the old runtime in place.

## Persistence

The primary SQLite database and bridge database are external production state and are preserved across release trees. Runtime source is deployed as an exact reviewed Git SHA into a dedicated release tree; C10 smoke checks the SHA, worktree, databases, transport configuration, PAUSED state and outbound invariants before/after PM2 cutover.

See:

- `tools/scripts/argos_c10_smoke.py`
- `docs/runbooks/ARGOS_C10T1_CLOUD_CUTOVER.md`
- `.github/workflows/argos-s292-contract.yml`
