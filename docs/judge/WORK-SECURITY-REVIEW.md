# ARGOS security review — 2026-09-09

Status: **OPEN / release security RED**. This report does not waive findings.

## Observed dependency audit

Full production lockfile audit including optional WhatsApp/browser dependencies:
initially 6 high entries, no critical entries. Updating the compatible transitive
js-yaml version from 4.3.1 to 4.3.2 removes its high advisory. Remaining: 5 high
entries propagated through extract-zip, @puppeteer/browsers, puppeteer-core,
puppeteer and whatsapp-web.js. These are a dependency chain, not five independently
confirmed exploits of ARGOS.

- https://github.com/advisories/GHSA-jmr9-qjv8-65gv
- https://github.com/advisories/GHSA-7pqw-9j4j-h8q3
- Corrected js-yaml advisory: https://github.com/advisories/GHSA-2883-xcg3-v3hh

Registry observation: extract-zip latest 2.0.1, whatsapp-web.js latest 1.34.7.
The reviewed extract-zip advisory lists no patched release. Do not apply npm's
suggested whatsapp-web.js downgrade automatically. Current production browser is
explicitly configured. Pairing and cutover now set `PUPPETEER_SKIP_DOWNLOAD=true`
on their locked optional dependency installs, so the deployment path cannot invoke
Puppeteer's browser archive download/extraction and must find the separately
provisioned executable first. This narrows the reviewed path; it does not remove
the vulnerable dependency or certify every archive-extraction path unreachable.
Browser provenance and upstream remediation remain open.

## Secret scanning

Gitleaks v8.30.1 Linux release binary, verified against its publisher's SHA256 file.
Commands used redaction=100 and stored only redacted local reports.

- Current wa-intelligence directory: 0 findings.
- Exact full tree bb1172ac had one strong current-tree finding: a historical
  Gmail app-password-shaped value in BACKLOG.md. The value was never copied into
  this report and is redacted in the pending tree; provider revocation/rotation
  still requires external evidence.
- Git history: 21 findings across generic-api-key, curl-auth-header, curl-auth-user.
  Findings are suspected exposures, not verified active credentials. No credential
  was tested with a provider. No secret values are included in this report.
- Historical provider rotation and exposure triage remain external/security gates.
  Do not rewrite history or treat deleting a current value as revocation.
- Repository-native full-history scan: 12 unique historical blob matches, all the
  strong `gmail-app-password` rule. See WORK-SECRET-HISTORY.md for the redacted
  scope and required closure evidence; its counting model differs from Gitleaks.
- The repository-native exact-Git-object scanner is published and mandatory in
  S292. It reports only path, line, rule and count, scans binary/text blobs, and
  has tests for exact-revision isolation, token/app-password detection, history
  persistence and redacted output. Exact current tree `5c4980b` is GREEN; the
  historical findings and provider-side revocation remain RED.

## Runtime hardening verified offline

- Durable intent journal before send, full SQLite synchronization; uncertain
  delivery survives real process termination and blocks resend.
- Writer DB lock and canonical LocalAuth profile lock acquired before migration;
  inherited by Node. Second entrypoint with a different port is rejected.
- Queue-only scheduler no longer receives outbound/admin/email/Telegram credential
  keys from the PM2 configuration. Inherited host environment still needs machine
  inspection; this proves declared configuration only.
- PM2 declarations are now split by process: the wwebjs daemon receives only its
  localhost API key; the scheduler receives no sensitive key; Telegram, alert
  monitor and dashboard receive only the keys their source consumes. No process
  receives Meta Cloud credentials in the PR #4 wwebjs release. A functional Node
  test compares every app against its allowed sensitive-key set. Inherited PM2
  host environment still requires real machine inspection.
- Localhost integration exercises real guards, primary/bridge persistence,
  inbound dedupe and analyzer state transition using synthetic fixtures.
- Hosted workflow actions for checkout, Node, Python and artifact upload are
  pinned to resolved commit SHAs. Checkout does not persist its token.
- The candidate bundle is generated from an explicit allowlist and exact Git
  blobs, with per-file hashes and an external archive checksum. Its security
  status remains OPEN in the embedded manifest.
- S292 executes a fail-closed npm audit regression gate. It accepts a clean audit
  or only the exact five-node, two-advisory optional dependency chain documented
  above at the reviewed lock versions. New advisories, critical severity, package
  versions or dependency edges fail CI. Acceptance of the known result emits
  `ARGOS_RELEASE_SECURITY=OPEN`; it is explicitly not a waiver.

These tests do not prove live WhatsApp receipt, iMac reboot, Chrome shutdown,
provider credential revocation, or an independent production security review.
