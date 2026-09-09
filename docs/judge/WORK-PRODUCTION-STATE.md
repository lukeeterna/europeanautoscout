# ARGOS Work production checkpoint — 2026-09-09

## Verified coordinates
- Repository: lukeeterna/europeanautoscout
- Branch: sol/argos-wwebjs-c10-production
- PR #4: open draft; base sol/argos-canonicalization-20260817; not merged.
- Observed remote HEAD before this final checkpoint:
  45b61494b05ba7c90b84fb6787f32975d5a3301a.
- This checkpoint's containing commit records the new unit; resolve it with Git.
- Last observed SHA with all three hosted contracts passing:
  45b61494b05ba7c90b84fb6787f32975d5a3301a. This is NOT full production
  certification because the security gate remains open.
- PR runs: https://github.com/lukeeterna/europeanautoscout/actions/runs/34382871855
  (S292), https://github.com/lukeeterna/europeanautoscout/actions/runs/34382871951
  (pre-pairing), https://github.com/lukeeterna/europeanautoscout/actions/runs/34382872479
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
- Fourth-unit localhost integration covers HTTP/bridge/inbound/analyzer with real
  Python guards and SQLite; live receipt and reconciliation remain unclosed.
- Runtime/C11 live proof, machine durability/reboot and security remain incomplete.
- A reproducible source candidate exists, but no artifact is a production release
  while its manifest truthfully records security OPEN and machine NOT_CERTIFIED.
- Security RED: 5 high npm audit entries remain after js-yaml fix; upstream
  extract-zip has no published patched version observed. History secret findings
  require triage/revocation evidence. See WORK-SECURITY-REVIEW.md.

## Next executable action
Publish and verify the containing provenance-attestation unit. If the repository
accepts the OIDC attestation, no independent offline implementation gate remains.
Next is branch-protection/review configuration plus external credential revocation
and coordinated history rewrite, then real iMac pairing/cutover/C10, an explicitly
authorized C11 recipient, and reboot/recovery proof. Do not dispatch those without
the required administrative/provider access, machine/session and authorization.

## External gates and truth levels
REPO GREEN: all three functional contracts and the S292 push build are observed
GREEN on 45b6149. Release security remains OPEN, so REPO GREEN is not a claim of
full release certification.
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

Second correction published: e5411d5e8d2e36ca1fface8b082a77fac0bba0c2.
All push contracts succeeded: S292 34346762623, pre-pairing 34346763279,
post-pilot 34346762462. All PR contracts also succeeded: S292 34346766016,
pre-pairing 34346766135, post-pilot 34346765963. Run URL prefix:
https://github.com/lukeeterna/europeanautoscout/actions/runs/

S292 artifact 10102017608 is named
`argos-source-e5411d5e8d2e36ca1fface8b082a77fac0bba0c2`, retained through
2026-10-09. Downloaded archive checksum verified:
`41fd8316b7a533b837b76559d103f181ddd33fd29804db7635e506d8fbde5a22`.
The independent bundle verifier passed and confirmed source SHA e5411d5, tree
c01c80a9743e2e47b7e85213cf5b56e1967e7d55, 37 inventoried source files,
security OPEN, machine/production NOT_CERTIFIED. No database, LocalAuth or secret
was found in the allowlisted artifact.

## Sixth unit (publication pending)

The actual remote body of `argos_c10_wwebjs_cutover.sh` now runs in a temporary
filesystem with real SQLite online backups and integrity checks while only its
external process/network commands are mocked. Seven full-body scenarios cover
success with outbound delta zero, failure before process mutation, new-runtime
start failure, postdeploy failure, PM2 save failure, browser shutdown timeout and
old-runtime restart failure. The existing nine exact-profile promotion/recovery
tests remain GREEN. A discovered rollback defect was fixed: internal rollback now
refuses to restart over a browser still holding canonical LocalAuth, and it cannot
claim PASS unless the old runtime restart succeeds with exactly one writer.
These are controlled simulations, not iMac execution.

## Seventh unit (publication pending)

Strong-signature scanning of the exact bb1172ac Git tree reproduced one current
finding in BACKLOG.md without printing it: an app-password-shaped historical value.
The pending tree redacts that value. Five functional scanner tests prove exact Git
revision isolation, text and binary token detection, app-password detection and
metadata-only reporting. S292 now runs the scanner on exact HEAD and packages the
scanner in the source candidate. Deleting the current copy is not proof of provider
revocation and does not clean the existing history; the security gate remains RED.

Seventh unit published: dd51e7e7f4d9488f6de4a551c7629e29467ba898.
Hosted runs succeeded: S292 push 34378644317; S292 PR 34378651935;
pre-pairing PR 34378651801; post-pilot PR 34378651970. The S292 run includes
the exact-tree scanner and completed GREEN with zero current strong findings.

## Eighth unit (publication pending)

PM2 declared credential scope is separated per process. The wwebjs daemon has
only `ARGOS_API_KEY`; scheduler has no sensitive keys; Telegram, CF monitor and
dashboard have explicit minimal sets matching their source. No app receives Meta
Cloud credentials. Ten ecosystem security tests and all 63 transport tests pass.
This certifies repository declarations only; inherited host/PM2 environment needs
read-only machine inspection before MACHINE GREEN.

## Ninth unit (publication pending)

C10 online SQLite backups are now forced to mode 0600 and receive an atomically
published mode-0600 manifest with candidate SHA, previous deployed SHA, UTC stamp
and SHA-256 for both primary and bridge copies. The full cutover test verifies
manifest provenance, checksums, permissions and `PRAGMA quick_check`. Post-pilot
restore tests additionally prove a consistent committed snapshot while another
connection holds a WAL `BEGIN IMMEDIATE` write and reject corrupt source bytes.
These are temporary/offline drills only, not production DB or reboot evidence.

Ninth unit published: 9b5661fe6d31fec8ddb4249ba763d35040a18e75.
All push contracts succeeded: S292 34379764768, pre-pairing 34379764763,
post-pilot 34379764776. PR contracts also succeeded: S292 34379768923,
pre-pairing 34379768974, post-pilot 34379768942. The read-only iMac run
34379764770 remains pending and is not machine evidence.

## Tenth unit (publication pending)

The repository-native scanner now supports a redacted all-refs history mode.
Against the Work clone (1,049 commits / 7,093 objects), it found 12 unique
historical blob matches, all `gmail-app-password`, without emitting values.
WORK-SECRET-HISTORY.md records scope and closure requirements. Gitleaks' prior
21-finding result uses broader rules/counting and remains separately recorded.

Tenth unit published: 5c4980b60bd3242d2b9094adce40a4213c1c3091.
All applicable hosted runs succeeded: S292 push 34380856720; S292 PR
34380862558; pre-pairing PR 34380862548; post-pilot PR 34380862555. Hosted
artifact 10115791491 has GitHub archive SHA-256
`00e44ac4b433008b26fd9bc540722520e641defee63b59e480855540966a5a74`.
Its external checksum and independent bundle verifier passed; manifest source SHA
is 5c4980b, source tree 54035806dbc31e9a4c8c0217b4dbfc6193fe3ee4,
with 39 inventoried source files and truthful security OPEN / machine and
production NOT_CERTIFIED gates. Full local regression: 152 Python and 82 Node
tests passed. PR #4 remains open, draft, mergeable and unmerged.

## Eleventh unit (publication pending)

Added a mandatory npm audit regression boundary. A clean audit passes; otherwise
only the exact reviewed five-node optional WhatsApp/Puppeteer/extract-zip chain,
two advisory identifiers and locked versions may pass. New vulnerabilities,
critical severity, version changes, topology changes and malformed reports fail
closed. Six functional tests pass against synthetic positive/negative cases and
the current real npm audit JSON passes as `KNOWN_OPEN_EXCEPTION` while explicitly
emitting `ARGOS_RELEASE_SECURITY=OPEN`. S292 source-artifact triggers now include
every allowlisted WORK/runbook document, preventing an artifact from silently
lagging a documentation-only candidate change.

Eleventh unit published: b2752a20a0a4f9bd8a5254137d28cbea12677ec3.
All applicable runs succeeded: S292 push 34382407787; S292 PR 34382412705;
pre-pairing PR 34382412723; post-pilot PR 34382412729. Hosted artifact
10116396479, retained through 2026-10-09, has GitHub archive SHA-256
`78e2014f945dc3499150542361a8aecbae5d1f91dbc38626527b8c882f66269a`.
The external checksum and independent verifier passed; its manifest binds SHA
b2752a2 to tree 4444cfecf24f421fff4ce9c068cb8dc06fc3ef1b, contains 40
allowlisted source files including the audit gate, and remains truthfully OPEN /
NOT_CERTIFIED / NOT_CERTIFIED.

## Twelfth unit (publication pending)

Release-trigger coverage review found that several allowlisted machine/readiness
scripts could change without starting a new S292 source artifact. Added wildcard
coverage for `tools/scripts/argos_*.py` and `tools/scripts/argos_*.sh`, plus a
functional test that matches every release inventory entry against the S292 path
filters. Seven bundle tests pass, including the new complete-coverage assertion.

Twelfth unit published: 45b61494b05ba7c90b84fb6787f32975d5a3301a.
All applicable runs succeeded: S292 push 34382865135; S292 PR 34382871855;
pre-pairing PR 34382871951; post-pilot PR 34382872479. Hosted artifact
10116563976, retained through 2026-10-09, has GitHub archive SHA-256
`ca09ee77b34713ff05be67131361eb8973fc04225a624bdacce840156376263b`.
External checksum and independent verification passed. The manifest binds source
SHA 45b6149 to tree ab4d819216fbe976a971c2a702e1026856a263f6,
contains 40 allowlisted files and records security OPEN, machine NOT_CERTIFIED and
production NOT_CERTIFIED. This exact SHA is the immutable offline source candidate.

## Thirteenth unit (publication pending)

GitHub repository inspection found the production, canonicalization and audit
branches all report `protected:false`; the repository ruleset list and PR #4
review list are empty. The connector exposes repository admin identity but no
branch-protection/ruleset mutation operation, so merge governance is an external
repository-settings gate and PR #4 remains draft/unmerged. The latest checkpoint
commit is also reported `unsigned`; this is recorded, not disguised as signed.

Added push-only GitHub/Sigstore build provenance for the source candidate. The
attestation runs in a separate job after S292 succeeds, downloads the exact named
artifact and attests its checksum file. OIDC, attestation and artifact-metadata
write permissions are isolated to that push-only job; PR test execution remains
read-only. Both official actions are pinned to exact commits. Functional tests
require the event boundary, privilege separation, pins and exact checksum subject.
