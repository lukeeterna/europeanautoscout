# ARGOS Work production checkpoint — 2026-09-08

## Verified coordinates
- Repository: lukeeterna/europeanautoscout
- Branch: sol/argos-wwebjs-c10-production
- PR #4: open draft; base sol/argos-canonicalization-20260817; not merged.
- Observed remote HEAD before this unit: 5222ae4665a6a9aaacab97e2ddfee6a4d5fa9551.
- This checkpoint's containing commit records the new unit; resolve it with Git.
- Last observed SHA with all three existing hosted contracts passing:
  5222ae4665a6a9aaacab97e2ddfee6a4d5fa9551. This was NOT full offline certification.
- Runs: https://github.com/lukeeterna/europeanautoscout/actions/runs/34273512797
  (S292), https://github.com/lukeeterna/europeanautoscout/actions/runs/34273512796
  (pre-pairing), https://github.com/lukeeterna/europeanautoscout/actions/runs/34273512814
  (post-pilot). All success, observed through GitHub connector.

## Completed unit
Recovered versioned pairing helper and 12 tests from exact HEAD; cloud run 12/12.
Confirmed no workflow invoked that test file. Added mandatory Node test step and
both helper/test paths to pre-pairing push/PR triggers. Expanded to 19 passing
mock-client tests: auth without QR, disconnect before/after auth, SIGINT/SIGTERM,
failed READY persistence, allowed dependencies and isolated filesystem access.
Published pairing unit: 2928c863072c7395077e33a05eb3a3db90eb4be6.
Hosted pre-pairing run 34275500270 succeeded, including the new Node step.
https://github.com/lukeeterna/europeanautoscout/actions/runs/34275500270

Second unit: reproduced 3 polling RED tests and 6 LocalAuth recovery RED tests.
Corrected auth-without-QR polling, terminal destroy failure handling, closed-profile
backup order, exact client/nonempty profile checks, recoverable rename promotion,
EXIT/signal traps, and browser guards before internal/external restore.
9 filesystem/SQLite/process-mock recovery tests pass; 3 polling tests pass.
All modified workflow shell steps parse. These are simulations, not machine proof.
Second unit published: 7b9078ad53ae99f4d61404f681474a719a0b5b26.
All three hosted contracts succeeded:
https://github.com/lukeeterna/europeanautoscout/actions/runs/34275932165 (pre-pairing)
https://github.com/lukeeterna/europeanautoscout/actions/runs/34275932172 (S292)
https://github.com/lukeeterna/europeanautoscout/actions/runs/34275932195 (post-pilot)

Third unit (publication pending): reproduced four transport ambiguity failures,
restart/DB-write/key-reuse failures. Added durable pre-send journal in primary DB,
FULL synchronization, nonretryable ambiguous wwebjs outcomes, stored message ID
before post-send persistence, and post-pilot unresolved-intent gate. Uses existing
S292 transport-test discovery (mandatory). Real child process exit during send and
restart proves no second send. 9 intent tests, 5 adapter ambiguity tests.
Native better-sqlite3 smoke passes from unchanged lockfile; initial npm install
failed extracting Node headers (fchown); explicit local headers resolved the build.
New WhatsApp Web runbook records safe reconciliation and old-runtime rollback limits.

## Open RED / unclosed gates
- Full cutover shell rollback and process recovery still need additional audit;
  promotion tests above do not certify the entire machine cutover.
- Full HTTP/bridge/inbound/analyzer end-to-end reconciliation remains unclosed;
  the guardedSend boundary and crash journal now have functional SQLite coverage.
- Full cutover script, runtime/C11, durability/security and release audit incomplete.
- No immutable certified release candidate produced in this session yet.

## Next executable action
Verify third-unit hosted CI, then complete cutover-shell process recovery tests,
full runtime integration, dependency/security audit and reproducible release packaging.

## External gates and truth levels
REPO GREEN: previous three contracts only; expanded unit pending hosted CI.
MACHINE GREEN: NOT VERIFIED. Existing read-only workflow triggered by second-unit
push is queued: https://github.com/lukeeterna/europeanautoscout/actions/runs/34275927601.
Runner inventory/protection REST endpoints returned HTTP 401 unauthenticated;
no tool for authenticated runner inventory or protection changes is exposed.
Do not infer runner online or branch-protection required status from passing CI.
PRODUCTION GREEN: NOT VERIFIED. Real pairing/C10/C11/reboot/security remain gated.
No live sends, production process changes, credential mutations or merges executed.
No new recipient authorization. PR #2 not advanced; PR #3 not reopened.

## Continuity
Git clone works in this Work environment; do not assume prior DNS failure persists.
Canonical STATE.md is dated July 30 and its transport/operating procedures are stale
relative to the current user mandate. Read WORK-PRODUCTION-MANDATE.md for precedence.
No unattended AI agent or persistent execution has been provisioned.
