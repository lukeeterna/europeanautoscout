# ARGOS WhatsApp Web release and recovery

Production authority: WORK-PRODUCTION-MANDATE.md. The Cloud API cutover runbook is
historical/superseded for PR #4; do not provision Meta credentials or switch transport.

## Release prerequisites

Pin a full commit SHA and require all three ARGOS hosted contracts on that exact
SHA. Keep PR #4 draft until real machine/C11/post-pilot gates pass. A successful
mock test is not evidence of a live WhatsApp session or a delivered message.

Install only from package-lock.json with
`PUPPETEER_SKIP_DOWNLOAD=true npm ci --include=optional`; production requires the
optional whatsapp-web.js dependency but uses the separately provisioned exact
Chrome executable. Native dependency smoke and all transport tests must pass. Use
the canonical runtime_entrypoint.py via PM2.

## Safe machine sequence

1. Observe an online, reachable trusted runner. No unattended pairing/QR retry.
2. Run manual isolated pairing only if the exact canonical profile needs it.
   READY is published only after client destruction; wait for process exit before
   accepting the SHA/client manifest. Never log/upload QR or LocalAuth.
3. Require exact-SHA hosted contracts before cutover. Keep PAUSED, automation 0,
   no approved bridge work, no authorized dealers, and the verified outbound baseline.
4. Close the writer/browser before preserving the old LocalAuth. Profile promotion
   keeps the closed original and uses same-volume renames. A surviving browser
   blocks restore and restart; retain recovery files for inspection.
5. Run exact-SHA C10 smoke and independent machine probe. Only then persist PM2.
6. C11 is separately authorized: a verified test recipient, consent and preflights,
   one send, one receipt proof, then PAUSED and authorization removed.
7. Verify primary/bridge/inbound/analyzer state, real reboot and real recovery.
   Only then merge PR #4, certify the merge SHA, and advance PR #2.

## Durable send intents

The primary SQLite journal `argos_send_intents` is created idempotently by the
canonical daemon. Its reservation commits with synchronous FULL before transport.
It holds only hashed request/key identity, timestamps, status and transport ID.
HTTP accepts optional `idempotency_key`; bridge uses its row ID. Requests without
an explicit key use a deterministic hash of dealer, normalized destination,
template, body and document hash. A changed key cannot bypass an uncertain identical
request. A reused key with a different request fails closed.

- IN_FLIGHT: transport may have delivered; never automatically clear or resend.
- DELIVERED: message ID is known but persistence/state completion was not certified.
- SENT: primary persistence and post-send state update completed. The same key can
  return its existing message ID without another transport call.

There is no expiration or automatic journal cleanup. An identical request under a
new key fails closed after delivery; do not treat it as a new successful send.
Known failures proven before submission may release their reservation. All other
transport errors, missing IDs, post-send DB errors and process crashes require
reconciliation. Post-pilot GREEN now requires the journal and zero unresolved rows.

Reconciliation is an explicit gate, not a retry command. Keep PAUSED. Preserve a
consistent primary and bridge backup including the intent journal. Verify actual
receipt/message ID and primary/bridge/state facts before any reviewed repair.
Do not delete an intent, change its hash, or repeat a send to discover delivery.
Automated reconciliation and its complete live inbound proof are not certified yet.

## Rollback constraints

During C10, restore only a closed profile and the verified previous canonical
runtime, remaining PAUSED with automation 0 and outbound delta zero. A backup made
while Chrome is writing is not a valid credential backup. Never run the historical
writer or scheduler. Preserve backups until independent recovery proof succeeds.

After a possible C11 delivery, never restore a pre-send primary DB or an older
runtime without accounting for its intent journal: doing so can erase dedupe
history. Keep the release PAUSED and reconcile instead. No rollback may authorize
another send. Real machine rollback/reboot remains a separate gate.
