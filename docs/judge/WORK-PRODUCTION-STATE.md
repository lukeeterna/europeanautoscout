# ARGOS Work production checkpoint — 2026-09-09

## Verified coordinates
- Repository: lukeeterna/europeanautoscout
- Branch: sol/argos-wwebjs-c10-production
- PR #4: open draft; base sol/argos-canonicalization-20260817; not merged.
- Observed remote HEAD before this unit: 00183f325b8fe7d098e2b8f5789b2b53560d65c8.
- This checkpoint's containing commit records the new unit; resolve it with Git.
- Last observed SHA with all three hosted contracts passing:
  af37fc3a5a4a6b92193161e0e6d30e996cf73eae. This is NOT full offline
  certification because the security gate remains open.
- Runs: https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437228
  (S292), https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437189
  (pre-pairing), https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437282
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

Third unit published: d987a685e4332c7128fd5f84b65cbfa6fce0c8ce.
All three contracts succeeded: S292 34313737237; pre-pairing 34313737233; post-pilot 34313737214.
Run URL prefix: https://github.com/lukeeterna/europeanautoscout/actions/runs/
Third-unit work: reproduced four transport ambiguity failures,
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
  Fourth-unit localhost integration covers HTTP/bridge/inbound/analyzer with real
  Python guards and SQLite; live receipt and reconciliation remain unclosed.
- Full cutover script, runtime/C11, durability/security and release audit incomplete.
- No immutable certified release candidate produced in this session yet.
- Security RED: 5 high npm audit entries remain after js-yaml fix; upstream
  extract-zip has no published patched version observed. History secret findings
  require triage/revocation evidence. See WORK-SECURITY-REVIEW.md.

## Next executable action
Publish and verify the native exact-SHA checkout correction, then download and
verify the hosted source-candidate artifact. Continue cutover-shell failure
injection and outstanding security mitigation/triage.

## External gates and truth levels
REPO GREEN: three functional contracts observed on af37fc3; the newer 00183f
candidate is RED at checkout, so it is not certified.
Full release certification remains RED because of the open security gate.
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


## Fourth unit
Compatible js-yaml lock update to 4.3.2; no direct dependency changes.
Kernel writer/profile locks inherited across exec, direct daemon launch guard,
and PM2 scheduler credential separation. 81 Node tests pass. New integrated test
runs real wrapper/HTTP/SQLite/Python/analyzer with only transport mocked:
one outbound, replay, bridge marker recovery without second send, duplicate
inbound once, CONTACTED -> ENGAGED, second writer rejection. Initial test expected
an undefined NOT_INTERESTED state; corrected fixture to canonical CURIOSITY ->
ENGAGED after checking existing TRANSITIONS (no production logic changed).
Full history scanner found 21 suspected exposures; runtime scan zero findings.
Reports contain counts only; no credentials or message contents persisted here.

Fourth unit published: af37fc3a5a4a6b92193161e0e6d30e996cf73eae.
Hosted runs all succeeded:
- S292: https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437228
- pre-pairing: https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437189
- post-pilot: https://github.com/lukeeterna/europeanautoscout/actions/runs/34314437282

## Fifth unit

Added an allowlisted, deterministic source-candidate builder that reads only exact
Git objects. It rejects dirty-worktree substitution, duplicate paths, symlinks,
database/LocalAuth/secret paths, and package/lock disagreement. Six functional
bundle tests cover reproducibility, contamination and tampering. The hosted S292
contract builds and retains the exact-SHA bundle plus external checksum for 30
days. All third-party actions in the three hosted contracts are pinned to exact
commit SHAs; checkout credentials are not persisted and PR runs explicitly build
the PR head SHA rather than GitHub's synthetic merge ref.

This is a source candidate only. Its manifest records security OPEN, machine
NOT_CERTIFIED and production NOT_CERTIFIED. It is not a production release.

Fifth unit published: 00183f325b8fe7d098e2b8f5789b2b53560d65c8.
All three hosted contracts failed before tests because the repository contains
the historical gitlink `tools/gsd` but no `.gitmodules`; actions/checkout attempted
submodule cleanup and reported `No url found for submodule path 'tools/gsd'`.
Observed RED runs:
- S292: https://github.com/lukeeterna/europeanautoscout/actions/runs/34345672998
- pre-pairing: https://github.com/lukeeterna/europeanautoscout/actions/runs/34345673033
- post-pilot: https://github.com/lukeeterna/europeanautoscout/actions/runs/34345672997

The pending correction replaces actions/checkout in the three hosted contracts
with a credential-free native fetch of the event's exact SHA and verifies HEAD
before any test. A regression test requires that boundary. Local validation:
three YAML parses, 22 shell blocks parse, 12 pre-pairing Python tests pass and
19 isolated pairing Node tests pass. Publication and hosted proof remain pending.

First correction published: ec87371321df2d5c6262f4aaf091a03f4cc7d15c.
Its push and PR runs all failed at the new first guard because the documented
runner variable is `RUNNER_ENVIRONMENT`, not `GITHUB_RUNNER_ENVIRONMENT`; no Git
operation or test ran. Representative PR runs: S292 34346252448, pre-pairing
34346252445, post-pilot 34346252456. The pending correction uses the real variable
and tests that the nonexistent name cannot return.
