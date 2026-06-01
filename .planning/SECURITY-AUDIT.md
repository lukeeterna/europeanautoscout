# ARGOS Automotive — Security Audit Report
**Date:** 2026-04-10  
**Auditor:** Claude Agent (claude-sonnet-4-6)  
**Scope:** Full local + remote (iMac @ 192.168.1.2)

---

## CRITICAL FINDINGS SUMMARY

| Severity | Count |
|----------|-------|
| CRITICAL | 4 |
| HIGH | 4 |
| MEDIUM | 3 |
| LOW | 2 |
| INFO | 3 |

---

## 1. SECRETS IN GIT

### 1.1 GitHub Personal Access Token — CRITICAL FAIL

**File:** `.claude/settings.local.json` (GIT TRACKED)  
**Status:** FAIL — CRITICAL

A live GitHub PAT (`<REDACTED-GITHUB-PAT>`) appears hardcoded multiple times in `.claude/settings.local.json`, committed to git. This file stores prior Bash command history approved by the user and is actively tracked.

**Risk:** Anyone with repo access (or git history access) can exfiltrate the token, push to the repo, read secrets via GitHub Actions, or enumerate repository state.

**Action required:**
1. Immediately revoke this token at https://github.com/settings/tokens
2. Generate a new PAT with minimal required scopes
3. Add `.claude/settings.local.json` to `.gitignore`
4. Purge from git history: `git filter-branch` or `git-filter-repo`

---

### 1.2 dealer_network.sqlite committed to git — CRITICAL FAIL

**File:** `dealer_network.sqlite` (GIT TRACKED — confirmed by `git ls-files`)  
**Status:** FAIL — CRITICAL

The SQLite database containing real dealer data (phone numbers, conversation state, PII) is committed to the repository and has been committed across multiple commits (earliest: `feat(S101)`). This violates GDPR and exposes operational data.

**Risk:** Database snapshots containing dealer phone numbers and outreach history are permanently in git history.

**Action required:**
1. Add to `.gitignore`: `dealer_network.sqlite`, `dealer_network.sqlite-shm`, `dealer_network.sqlite-wal`
2. Purge from git history with `git-filter-repo --invert-paths --path dealer_network.sqlite`
3. Rotate any dealer data that may have been accessible

---

### 1.3 Phone Numbers in Git-Tracked Scripts — HIGH FAIL

**Files tracked by git with hardcoded dealer phone numbers:**
- `tools/send_day1_top5_discovery.py` — contains `393683259045`, `393479227573`
- `tools/send_day1_tier1.py` — contains `393398835656`
- `tools/outreach/send_day1_stile_car.py` — check for phones

**Status:** FAIL — HIGH (partial GDPR violation)

The memory note confirms "44 numeri WA sanitizzati" was done for `research/s108_*.md` files, but the `tools/send_day1_*.py` outreach scripts with real numbers were not sanitized and remain tracked.

**Action required:** Redact real phone numbers from tracked scripts. Replace with environment variable lookups (`os.environ.get('DEALER_PHONE_...')`) or DB lookups by dealer_id.

---

### 1.4 Luca Ferretti's WhatsApp Number in Tracked Research — MEDIUM

**File:** `research/s99_backstory_internazionale.md` (GIT TRACKED)  
**Content:** `+39 328 153 6308` appears at lines 345, 368, 388  
**Status:** MEDIUM — Acceptable if intentional (public business number)

This is Luca's WA Business number, used as a public contact. Acceptable if intentional. No action required unless privacy policy demands it.

---

### 1.5 .gitignore Coverage — PARTIAL FAIL

**Status:** FAIL — HIGH

Current `.gitignore` covers:
- `.env` ✓
- `*.pyc` ✓
- `__pycache__/` ✓
- `src/cove/data/cove_tracker.duckdb` ✓ (specific path only)

Missing critical patterns:
- `dealer_network.sqlite` — NOT ignored, actively tracked
- `dealer_network.sqlite-shm` — NOT ignored
- `dealer_network.sqlite-wal` — NOT ignored
- `*.sqlite` — no wildcard
- `*.duckdb` — no wildcard (only specific path covered)
- `.claude/settings.local.json` — NOT ignored

**Action required:** Add to `.gitignore`:
```
*.sqlite
*.sqlite-shm
*.sqlite-wal
*.duckdb
.claude/settings.local.json
```

---

## 2. API KEY AUTH — PORT 9191

### 2.1 API Key Authentication — PASS (conditional)

**Status:** PASS — with caveat

`ARGOS_API_KEY` is set in `.env` on iMac (43 chars, confirmed). The daemon correctly enforces `X-API-Key` header for all endpoints except `GET /` and `GET /status`.

**Caveat:** If `ARGOS_API_KEY` is empty or not set, the `if (API_KEY && ...)` guard is bypassed and ALL endpoints become unauthenticated. The env var is not in `ecosystem.config.js` SHARED_ENV — it relies entirely on `.env` loading at PM2 start time. If `.env` changes or PM2 is restarted without reloading env, the key could revert to empty.

**Recommendation:** Add a startup assertion:
```js
if (!process.env.ARGOS_API_KEY) {
    log('ERROR', 'FATAL: ARGOS_API_KEY not set. Port 9191 will be unauthenticated. Refusing to start.');
    process.exit(1);
}
```

---

### 2.2 /send Phone Format Validation — PASS

Italian phone regex `^(39)?3\d{8,9}$` correctly applied on `/send`. ✓

### 2.3 /send-multi Missing Phone Validation — HIGH FAIL

**File:** `wa-daemon.js:832`  
**Status:** FAIL — HIGH

The `/send-multi` endpoint accepts a `phone` parameter but does NOT apply the Italian phone format regex that `/send` uses. An attacker (or misconfigured client) could send to non-Italian or invalid numbers, bypassing the anti-spam validation.

**Fix:**
```js
// Add after the array length check in /send-multi
const cleanMultiPhone = phone.replace(/[^0-9]/g, '');
if (!/^(39)?3\d{8,9}$/.test(cleanMultiPhone)) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'invalid italian phone number', phone }));
    return;
}
```

---

### 2.4 Message Length Validation — PASS

`message.length > 4096` check in `/send`. ✓  
`/send-multi` validates `messages.length > 5`. ✓ (no per-message length check though)

---

### 2.5 Rate Limiting — PARTIAL PASS

Daily limit (30 msgs/day) and per-dealer reply cap (10/day) are implemented in-memory. ✓  
HTTP-level rate limiting (requests/second per IP) is NOT implemented. Port 9191 has no brute-force protection. Since it's LAN-only, this is acceptable for now but worth noting.

---

## 3. DASHBOARD AUTH — PORT 8080

### 3.1 Dashboard Password — FAIL — HIGH

**File:** `wa-intelligence/dashboard/auth.py:18`  
**Status:** FAIL — HIGH

```python
DASHBOARD_PASSWORD = os.environ.get('ARGOS_DASHBOARD_PASSWORD', 'argos2026')
```

`ARGOS_DASHBOARD_PASSWORD` is NOT set in the iMac `.env` (confirmed via SSH). The dashboard is running with the **default hardcoded password `argos2026`**. Port 8080 is bound to all interfaces (`*.http-alt` confirmed via `lsof`).

Anyone on the LAN can access `http://192.168.1.2:8080` and log in with `argos2026`.

**Action required:**
1. Add to `.env` on iMac: `ARGOS_DASHBOARD_PASSWORD=<strong-random-password>`
2. Restart the dashboard PM2 process
3. Verify with: `grep ARGOS_DASHBOARD_PASSWORD ~/Documents/app-antigravity-auto/wa-intelligence/.env`

---

### 3.2 Session Cookie Security — PASS

`httponly=True`, `samesite='lax'`, `max_age=604800` (7 days). Signed with `itsdangerous`. ✓  
`secure=True` only when `ARGOS_HTTPS=1`, which is appropriate for LAN HTTP. ✓

### 3.3 Rate Limiting on Login — FAIL — MEDIUM

**Status:** FAIL — MEDIUM

No rate limiting on `POST /login`. An attacker can brute-force the password endpoint without any lockout. `slowapi` or similar is not imported.

**Recommendation:** Add simple in-memory login attempt counter:
```python
_login_attempts = {}  # ip -> (count, last_attempt_ts)
MAX_LOGIN_ATTEMPTS = 10
LOCKOUT_SECONDS = 300
```

---

### 3.4 XSS in Dashboard Templates — LOW

**Status:** LOW RISK

`{{ costs | safe }}`, `{{ funnel | safe }}`, `{{ archetypes | safe }}` in Jinja2 templates use the `| safe` filter to inject JSON into JavaScript. These values come from internal DB queries (not user input), so XSS risk is low. However if a dealer's name or notes were ever surfaced this way, it would become HIGH. Current templates for dealer data use escaped output `{{ dealer.dealer_name }}` without `| safe`. ✓

---

## 4. SQL INJECTION

### 4.1 wa-daemon.js — PASS

All DB operations use `better-sqlite3` prepared statements with `?` placeholders. ✓ No string interpolation in SQL queries.

### 4.2 dashboard/db.py — FAIL — MEDIUM

**File:** `wa-intelligence/dashboard/db.py:344`  
**Status:** FAIL — MEDIUM

```python
count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
```

The `table` variable is drawn from a hardcoded list `['conversations', 'messages', ...]` — not user-controllable — so this is **low actual risk** but a bad pattern. If the list source ever changes, SQL injection becomes possible.

**Fix:** Use a whitelist check before the f-string, which it already does implicitly via the loop. No change needed for security, but consider: `con.execute(f'SELECT COUNT(*) FROM "{table}"')` to prevent schema confusion.

### 4.3 tools/dealer_crm.py — PASS (with note)

**File:** `tools/dealer_crm.py:537`  
```python
f"UPDATE dealers SET {field} = ?, updated_at = datetime('now') WHERE dealer_id = ?"
```

`field` is validated against an explicit `allowed` set before use (lines 525-533). ✓ This is safe as implemented — SQL injection is not possible since field names are allowlisted.

### 4.4 Python files — PASS

All wa-intelligence Python files use parameterized queries (`sqlite3.execute('...', (param,))`). No raw SQL string interpolation with user data found. ✓

---

## 5. COMMAND INJECTION

### 5.1 sanitizeShellArg() — PASS

**File:** `wa-daemon.js:52-60`  
Applied to `dealer_id` and `template_id` when constructing shell commands for `outbound_guard.py`. ✓

### 5.2 runOutboundGuard() using execSync — MEDIUM RISK

**File:** `wa-daemon.js:330-342`  
**Status:** MEDIUM RISK

`execSync` with shell string interpolation is used (not `spawn` with array args). While `sanitizeShellArg` is applied to `dealerId` and `templateId`, the message text is truncated to 2000 chars and shell-escaped. The safer approach would be to use `spawn` with array args (as done for `triggerAnalyzer`). The current approach is functional but fragile.

**Recommendation:** Migrate `runOutboundGuard` and `runPostSendUpdate` from `execSync` string interpolation to `spawn` with argv array to completely eliminate shell injection surface.

### 5.3 response-analyzer.py subprocess spawned with args array — PASS

`spawn(CONFIG.PYTHON_BIN, args, ...)` uses argv array, not shell string. ✓

---

## 6. GDPR / PII

### 6.1 PII in git history (dealer_network.sqlite) — CRITICAL

Covered in section 1.2. The committed database contains real dealer phone numbers, conversation states, and interaction history. This is a GDPR violation under Art. 5(1)(f) (integrity and confidentiality).

### 6.2 PII in tracked outreach scripts — HIGH

Covered in section 1.3. Real dealer phone numbers in `tools/send_day1_*.py` scripts.

### 6.3 PII minimization in LLM calls — PASS

`response-analyzer.py` sends `--dealer-name` and `--persona` but not phone numbers to LLM contexts. ✓

### 6.4 Database PII — ACCEPTABLE

Phone numbers stored in `dealer_network.sqlite` on iMac (not MacBook). Accessible only on LAN. Acceptable given the B2B nature and small scale (7 active dealers). No encryption at rest — acceptable for current phase.

---

## 7. DEPENDENCIES

### 7.1 Python requirements.txt — PASS

```
fastapi==0.104.1  — 2023 release, no critical CVEs known
uvicorn[standard]==0.24.0  — stable
itsdangerous==2.1.2  — stable
```

No known critical vulnerabilities in pinned versions. Note: `fastapi==0.104.1` is outdated (current 0.115+). Not critical but update recommended.

### 7.2 Node.js package.json — NOT CHECKED

`package.json` for `wa-intelligence` is not committed. Cannot audit remotely. Recommend running `npm audit` on iMac.

**Action:** `ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto/wa-intelligence && npm audit 2>&1"`

---

## 8. REMOTE: iMac INFRASTRUCTURE

### 8.1 SSH: REACHABLE — 192.168.1.2 ✓

### 8.2 DB File Permissions — FAIL — HIGH

```
-rw-r--r-- dealer_network.sqlite     (644)
-rw-r--r-- cove_tracker.duckdb       (644)
```

Both databases are world-readable on the iMac filesystem. While the iMac is a single-user machine, best practice per security.md requires `chmod 600`.

**Action required:**
```bash
ssh gianlucadistasi@192.168.1.2 "
  chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite
  chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite-shm
  chmod 600 ~/Documents/app-antigravity-auto/dealer_network.sqlite-wal
  chmod 600 ~/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb
"
```

### 8.3 .env Permissions — PASS

`.env` on iMac: `-rw-------` (600). ✓

### 8.4 macOS Application Firewall — FAIL — HIGH

**Status:** FAIL — HIGH

`/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate` returns: **"Firewall is disabled. (State = 0)"**

Both port 9191 and 8080 are bound to `*` (all interfaces). The macOS Application Firewall is OFF. Any device on the LAN can reach:
- Port 9191 (WA daemon) — protected by API key ✓, but `GET /` and `GET /status` are unauthenticated
- Port 8080 (dashboard) — protected only by default password `argos2026` ✗

**Action required:**
1. Enable macOS firewall: System Preferences → Security & Privacy → Firewall → Turn On Firewall
2. Configure to block incoming connections to 9191 and 8080 from outside LAN, or use `pf` rules

### 8.5 Database Backups — PARTIAL FAIL

A `.bak_20260402` backup exists from April 2. No automated 6h backup process found (as required by `security.md`). The WAL file is 483KB and uncommitted — a crash now without backup could lose data.

**Action required:** Set up `cron` or PM2 scheduled job:
```bash
sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite ".backup '/tmp/argos_backup_$(date +%Y%m%d_%H%M).sqlite'"
```

### 8.6 PM2 Process Status — INFO

`argos-wa-daemon` running, pid 5796, 23h uptime, 45MB RAM, 2488 restarts (high restart count — investigate).  
`argos-dashboard` (Python, 8080) running, 1.2M uptime.  
`argos-tg-bot` — NOT in PM2 list (may have been removed or stopped).

---

## 9. SUMMARY TABLE

| Check | Status | Severity | Notes |
|-------|--------|----------|-------|
| GitHub PAT in settings.local.json | **FAIL** | CRITICAL | `ghp_zgws...` committed to git — REVOKE IMMEDIATELY |
| dealer_network.sqlite committed | **FAIL** | CRITICAL | PII in git history — GDPR violation |
| .gitignore missing *.sqlite, settings.local | **FAIL** | HIGH | DB and local settings unprotected |
| Phone numbers in tracked scripts | **FAIL** | HIGH | `send_day1_*.py` with real numbers |
| ARGOS_API_KEY auth on 9191 | **PASS** | — | Key set, 43 chars, enforced |
| API_KEY bypass if empty | **WARN** | MEDIUM | No startup fail-fast if unset |
| /send phone format validation | **PASS** | — | Italian phone regex enforced |
| /send-multi missing phone validation | **FAIL** | HIGH | No phone format check |
| Dashboard password default `argos2026` | **FAIL** | HIGH | ARGOS_DASHBOARD_PASSWORD not in .env |
| Dashboard rate limiting on login | **FAIL** | MEDIUM | No brute-force protection |
| Session cookie security | **PASS** | — | httponly, signed, samesite=lax |
| SQL injection (wa-daemon.js) | **PASS** | — | Prepared statements throughout |
| SQL injection (db.py table name) | **WARN** | LOW | Hardcoded list, low actual risk |
| SQL injection (dealer_crm.py) | **PASS** | — | Allowlist validation before f-string |
| Command injection (sanitizeShellArg) | **PASS** | — | Implemented for dealer_id/template |
| execSync vs spawn (outbound guard) | **WARN** | MEDIUM | Recommend migration to spawn |
| XSS in dashboard templates | **PASS** | LOW | `| safe` only on internal JSON data |
| .env permissions (iMac) | **PASS** | — | chmod 600 ✓ |
| DB file permissions (iMac) | **FAIL** | HIGH | chmod 644 — should be 600 |
| macOS Firewall | **FAIL** | HIGH | Disabled — all ports open on LAN |
| DB backups | **PARTIAL** | MEDIUM | Manual only, no automated 6h backup |
| PM2 restart count (2488) | **WARN** | INFO | Investigate root cause |

---

## 10. PRIORITY ACTION PLAN

### Immediate (do now, before next outreach)

1. **REVOKE GitHub PAT** `<REDACTED-GITHUB-PAT>` at https://github.com/settings/tokens
2. **Set ARGOS_DASHBOARD_PASSWORD** in `.env` on iMac — current default `argos2026` is exposed
3. **Update .gitignore** — add `*.sqlite`, `*.sqlite-shm`, `*.sqlite-wal`, `.claude/settings.local.json`

### This session (today)

4. **chmod 600** on dealer_network.sqlite and cove_tracker.duckdb on iMac
5. **Fix /send-multi** — add Italian phone regex validation (5 lines of code)
6. **Enable macOS Firewall** on iMac

### This week

7. **Purge git history** — remove `dealer_network.sqlite` and `settings.local.json` using `git-filter-repo`
8. **Sanitize phone numbers** in tracked `tools/send_day1_*.py` scripts
9. **Add login rate limiting** to dashboard `/login` endpoint
10. **Add API_KEY startup assertion** in wa-daemon.js
11. **Set up automated DB backup** (6h cron as per security.md)
12. **Run `npm audit`** on iMac for wa-intelligence dependencies
13. **Migrate `runOutboundGuard`** from execSync to spawn

---

*Report generated: 2026-04-10 | Next audit recommended: before beta launch*
