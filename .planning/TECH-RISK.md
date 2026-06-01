# ARGOS Automotive — Tech Stack Risk Assessment
**Date:** 2026-04-10
**Scope:** Production system at 50-200 dealer scale
**Author:** Architecture review (Claude Sonnet 4.6)

---

## Executive Summary

| Component | Risk Level | Action Required |
|---|---|---|
| PaddleOCR 3.x (3.4.0) | HIGH | Pin version + memory guard |
| WhatsApp via whatsapp-web.js | HIGH | Operational mitigations (no safe alternative at zero cost) |
| DuckDB (CoVe scoring) | LOW | Keep as-is, it is the right tool for the job |
| SQLite (dealer CRM) | MEDIUM | Add write serialization guard |
| simple-lama-inpainting | MEDIUM | Acceptable risk, plan contingency |
| Single-server iMac | HIGH | Cold standby plan required before first paying dealer |

---

## Risk 1 — PaddleOCR 3.x (3.4.0)

### What is confirmed

**Memory leak — REAL, CONFIRMED, PARTIALLY FIXED**

PaddleOCR 3.0.0 and 3.0.1 have a documented unbounded memory growth bug when running CPU inference (issue #15631). The root cause is `config.set_mkldnn_cache_capacity(-1)` — unlimited MKLDNN cache — introduced when PaddleOCR 3.x removed the cap of 10 that existed in 2.x. A fix was merged in PaddleX PR #4148 restoring the cap to 10. As of 3.4.0 (released 2026-01-29), this fix is present in PaddleX but it is not confirmed whether paddleocr 3.4.0 on PyPI includes it.

**macOS-specific freeze**

Issue #11079 documents PaddleOCR freezing on macOS (Apple Silicon + Intel). A separate issue on macOS 15.5 with M4 reported 25 GB RAM consumed processing a single standard image after changing `limit_side_len` (issue #16168). The iMac runs Intel — the risk profile is different from Apple Silicon but not zero.

**Batch processing behavior**

RAM usage under batch (multiple images per process run) grows linearly and never returns to baseline. This is the ARGOS use case: sanitize 5-15 images per listing, triggered on demand.

**3.4.0 release quality**

v3.4.0 (2026-01-29) focused on PaddleOCR-VL document parsing features. It is a feature release, not a stability patch. There are no explicit memory leak fixes listed in the changelog.

### ARGOS-specific exposure

The sanitizer is invoked via `on_demand_runner.py` as a subprocess (per the S111 implementation). If PaddleOCR is initialized once per process run and that process exits after finishing, the memory leak is contained — each invocation starts clean. This is the correct architecture. The risk materializes only if the sanitizer is ever integrated as a long-running service or called in a tight loop without process restart.

### Mitigations

1. **Keep the subprocess isolation pattern** — one OS process per listing, exits cleanly. Confirmed safe per current architecture.
2. **Pin to 3.4.0** in `requirements.txt` with a comment. Do not auto-upgrade. New releases may reset the MKLDNN fix.
3. **Add a memory ceiling guard** in the sanitizer script: check available RAM before init; abort and alert via Telegram if below 2 GB free.
4. **Monitor iMac memory** via PM2 ecosystem metrics or a LaunchAgent cron that sends a Telegram alert if RAM > 80% for 5 minutes.
5. **Test on each PaddleOCR upgrade** before updating production. Run the KORDICK listing test (2 images) and measure peak RSS.

### Recommended version

Stay on **3.4.0** (current). Do not upgrade to 3.5.x until release notes confirm memory fixes. If a critical bug forces an upgrade, re-run the full sanitizer test suite before deploying to iMac.

---

## Risk 2 — WhatsApp via whatsapp-web.js

### What is confirmed

**whatsapp-web.js is officially unsupported by Meta**

The library (latest: v1.34.6 as of early 2026) reverse-engineers WhatsApp Web. Meta's Terms of Service explicitly prohibit this. The library maintainer warns: "It is not guaranteed you will not be blocked by using this method."

**Meta's enforcement posture has hardened in 2025-2026**

Meta rolled out a policy in October 2025 banning general-purpose AI chatbots from WhatsApp, effective January 15, 2026. While this targets chatbot platforms, it signals aggressive platform lock-down. Meta's automated detection systems flag non-standard browser fingerprints, abnormal messaging patterns, and headless Chrome sessions.

**The ARGOS daemon's specific risk profile**

- Low volume (DAILY_LIMIT = 30), single-threaded queue — LOW risk from bulk detection.
- Business hours only (`TC.isBusinessHours()` check) — LOW risk from off-hours automation signature.
- Randomized delays with lognormal distribution (min 2s) — MEDIUM risk reduction.
- API key auth on port 9191, not exposed publicly — no external abuse vector.
- Uses `LocalAuth` (session persistence) — reduces QR re-scan frequency but means session files contain auth tokens.
- Single WA Business number (3281536308) — if banned, the entire pipeline stops. Zero fallback.

**What triggers bans (confirmed from whatsapp-web.js issue #532, #2701)**

- Sending to numbers that have not saved your contact (high-volume cold outreach)
- Recipients clicking "Report Spam" — the primary trigger for automated bans
- Sending identical or near-identical messages to many numbers in a short window
- Headless Chrome fingerprint detection (less common but reported)
- Unusual session activity (multiple device connections, rapid reconnects)

**Current ARGOS behavior**: all outreach is cold (dealers have not saved the number). This is structurally the highest-risk pattern regardless of volume.

### Mitigations already in place (confirm functioning)

- Daily cap 30 messages
- Business hours gate
- Randomized delays
- API key auth
- outbound_guard.py blocking duplicates

### Additional mitigations required

1. **Warm the number first** — before first real dealer outreach, have 5-10 organic WA conversations from the number (friends, test contacts). Meta's risk model weights account age and organic activity heavily.
2. **Never send to the same cold number twice in 24h** — already in place via outbound_guard.py, but verify the deduplication window is 24h not session-scoped.
3. **Keep daily volume under 20 for the first 30 days** — despite DAILY_LIMIT=30, set effective limit to 15-20 during the soft launch period.
4. **Rotate message copy** — sending structurally identical messages to 10+ numbers in a day is a ban signal. The template system must ensure no two messages sent the same day are character-for-character identical.
5. **Have a recovery plan** — if the number is temporarily banned (24-72h), know the exact steps: stop PM2, wait, restart, re-scan QR. Document this in `ops/WA_BAN_RECOVERY.md`.
6. **Session file backup** — `.wwebjs_auth/` directory should be included in the 6h backup cycle. Session loss forces full QR re-scan.
7. **No viable zero-cost alternative exists** — Green API, WATI, and official WABA all cost money. The risk is accepted by design. Document the acceptance explicitly.

---

## Risk 3 — DuckDB (CoVe scoring engine)

### Assessment: LOW RISK — correct tool for the job

DuckDB is an OLAP (analytical) database. ARGOS uses it for CoVe scoring: computing confidence scores, aggregating vehicle data across 28 portal scrapers, running analytical queries on `cove_tracker.duckdb`. This is exactly the use case DuckDB is optimized for.

**DuckDB vs SQLite for this specific workload**

| Criterion | DuckDB | SQLite |
|---|---|---|
| Vectorized analytical queries | Excellent | Poor |
| Columnar storage (score aggregation) | Native | Emulated |
| Concurrent read-heavy analytics | Excellent | Adequate |
| OLTP (frequent small writes) | Not designed for | Excellent |
| 50-200 dealer scale | Fine | Fine |

**The dual-DB architecture (DuckDB for CoVe + SQLite for CRM) is correct.** These are fundamentally different workloads. Consolidating to one engine would mean either:
- Using DuckDB for CRM: wrong — DuckDB has poor concurrent write support, locking issues for OLTP, and its WAL/transaction model is not designed for multi-process writes.
- Using SQLite for CoVe: suboptimal — analytical queries on vehicle scoring data run significantly slower.

**Known DuckDB risks at this scale**

- DuckDB is not designed for concurrent writes from multiple processes. If `cove_tracker.duckdb` is ever written from more than one process simultaneously, expect lock conflicts. Currently, only the CoVe engine writes to it — verify this remains the case.
- DuckDB file format changes between major versions. Pin DuckDB version in requirements and test on upgrade.
- DuckDB 1.x is stable for production use as of 2025.

**Action items**

1. Verify only one process writes to `cove_tracker.duckdb` at any time.
2. Pin DuckDB version in `requirements.txt`.
3. Include `cove_tracker.duckdb` in the 6h backup cycle (same as dealer_network.sqlite).

---

## Risk 4 — SQLite (dealer CRM, 4 concurrent writers)

### Assessment: MEDIUM RISK — architecture mismatch needs a guard

**The problem**

SQLite is designed for multi-reader, single-writer access. With 4 concurrent processes writing to `dealer_network.sqlite` (wa-daemon.js via better-sqlite3, state_machine.py, outbound_guard.py, post_send_update.py), write contention is the primary risk.

WAL mode (confirmed active) significantly reduces the problem: readers never block writers, and writers only block writers. With `busy_timeout=10000` set on both Node and Python connections, brief lock waits are handled without errors.

**At 50-200 dealer scale with low write frequency, this is manageable.** The risk profile is:
- Concurrent writes are infrequent (triggered by WA messages, not polling)
- Write operations are short (single row inserts/updates)
- WAL + busy_timeout provides adequate protection

**Risks that remain**

- `PRAGMA integrity_check` is scheduled every 5 min. If the iMac goes to sleep mid-write, WAL recovery on next open is the first defense. A `cp` on a live SQLite file would corrupt it — the backup uses `sqlite3 .backup` (correct).
- Schema drift: 4 codebases touch the same schema. A Python migration that adds a column must be coordinated with the Node.js better-sqlite3 access patterns.
- The current test suite ran 23/23 PASS after chaos tests including rapid restart 5x and DB stress — this provides confidence.

**Action items**

1. No new writers. Enforce a rule: all new write paths must go through post_send_update.py or wa-daemon.js, not create new direct connections.
2. Run `PRAGMA integrity_check` on startup and log result to Telegram — already in monitoring spec, verify it is running.
3. For future scale (500+ dealers), consider a serializing write queue (e.g., all writes via the wa-daemon HTTP API) to eliminate multi-process contention entirely.

---

## Risk 5 — simple-lama-inpainting

### What is confirmed

- **Latest version:** 0.1.2 (released July 28, 2023 — no update in ~3 years)
- **License:** Apache 2.0 (confirmed via socket.dev and upstream lama repo)
- **GitHub:** enesmsahin/simple-lama-inpainting — 292 stars, 40 forks, ~29 commits
- **Last activity:** Issues opened as recently as August 2025 suggest community still uses it, but no releases since mid-2023
- **Underlying model:** The LaMa algorithm itself (advimman/lama, Apache 2.0) is stable and well-validated

### Assessment: MEDIUM RISK — dormant wrapper around a stable model

The wrapper is minimal — it loads the LaMa model weights and provides a Python API. If it stops working due to a PyTorch version update or Python 3.12+ incompatibility, the fix is typically straightforward (update import paths, dependency pins). The model weights themselves are not going anywhere.

**Practical risks**

- Python 3.12 or 3.13 compatibility: the wrapper requires Python >=3.10, <4.0. No issues reported currently on 3.11 (the version on iMac).
- PyTorch API breaking changes: if PyTorch 3.x drops a function used internally, the wrapper breaks silently. The underlying LaMa model would still be usable via the OpenCV inpainting_lama integration (HuggingFace: `opencv/inpainting_lama`, Apache 2.0).
- No security patches: dormant libraries do not receive CVE fixes. The library has no network access and only processes local images, so the attack surface is near zero.

**Contingency plan (if simple-lama-inpainting breaks)**

Primary fallback: `opencv/inpainting_lama` via HuggingFace (same Apache 2.0 model, actively maintained by OpenCV team). Migration cost: ~2 hours to swap the inpainting call in `image_sanitizer.py`.

Secondary fallback: `lama-cleaner` (renamed to `IOPaint`) — more dependencies but active maintenance.

**Action items**

1. Pin `simple-lama-inpainting==0.1.2` explicitly in requirements.
2. Add a comment documenting the fallback path.
3. Test the sanitizer pipeline after any Python or PyTorch upgrade before deploying to iMac.
4. No action required now — risk is acceptable given the fallback is clear and cheap.

---

## Risk 6 — Single iMac Server (192.168.1.2)

### What is confirmed

This is the highest structural risk in the stack. A single physical machine at a home address running all production services:
- wa-daemon.js (PM2)
- argos-dashboard (PM2)
- tg-bot (PM2)
- SQLite and DuckDB databases

**Failure modes and recovery times**

| Failure | Probability | Recovery Time | Data Loss Risk |
|---|---|---|---|
| macOS crash / kernel panic | Low | 10-30 min (PM2 restarts on boot) | None (WAL recovery) |
| Power outage | Medium (home environment) | 10-30 min after power restored | None if UPS; up to 5 min if not |
| Hardware failure (disk, logic board) | Low per year | 2-7 days (replace + restore) | Up to 6h (backup cycle) |
| iMac in sleep (idle overnight) | High | Immediate on wake; LaunchAgent prevents | None |
| ISP outage | Medium | Hours (ISP-dependent) | None |
| macOS auto-update reboot | Medium | 10-30 min | None |
| WA session corruption (Chrome zombie) | Low (fixed S109) | 5-15 min (PM2 restart + QR) | None |

**At current scale (0 paying dealers, soft launch), this risk is acceptable.** The cost of VPS migration exceeds the value protected.

**At first paying dealer, the calculus changes.** A 24h outage during active negotiation with a dealer could lose a €1,000 transaction and damage the relationship permanently.

**PM2's protection boundary**

PM2 protects against process crashes and server reboots (via `pm2 startup`). It does NOT protect against:
- The iMac going to sleep (LaunchAgent `caffeinate` is required and must be verified as active)
- Hardware failure
- Network outage

### Mitigations for current stage (zero cost)

1. **Verify `caffeinate` LaunchAgent is active** — `launchctl list | grep caffeinate`. If not running, add it. This is the most important single action.
2. **Enable UPS or surge protector** — prevents the most common hardware killer.
3. **Automate the 6h backup offsite** — current spec says every 6h to local path. Add an rsync or rclone step to a free cloud target (Backblaze B2 free tier: 10 GB). This converts hardware failure from "days down + data loss" to "days down + no data loss."
4. **Document the QR re-scan procedure** — if PM2 restarts wa-daemon.js but the WA session is invalidated, someone must be at the iMac to scan QR. This is a manual step with no automated fix.
5. **macOS auto-update: disable automatic reboots** — set macOS to download updates but not install automatically. Install manually during off-hours.

### Migration path when first dealer goes live

- **VPS option (cheapest):** Hetzner CX22 (€5.77/month, 2 vCPU, 4 GB RAM, 40 GB SSD, Germany). Sufficient for the entire stack. WhatsApp Web requires a display/X11 or Chrome headless — this is the primary migration complication.
- **whatsapp-web.js on VPS:** Requires headless Chrome on Linux. This is a supported configuration (Puppeteer + Chromium). Tested by the community. Main cost: setup time (~4 hours).
- **Trigger for migration:** First confirmed paying dealer, or if the iMac suffers any downtime >2h during business hours.

---

## Consolidated Action List

### Immediate (before first real outreach)

- [ ] Verify `caffeinate` LaunchAgent running on iMac (`launchctl list | grep caffeinate`)
- [ ] Add UPS or surge protector to iMac
- [ ] Pin all package versions: `paddleocr==3.4.0`, `simple-lama-inpainting==0.1.2`, `duckdb==<current>` in requirements
- [ ] Add offsite backup target (rclone to Backblaze B2 or similar) for both SQLite and DuckDB
- [ ] Document WA ban recovery procedure in `ops/WA_BAN_RECOVERY.md`
- [ ] Reduce effective daily WA send limit to 15-20 for first 30 days
- [ ] Warm the WA number with 5-10 organic conversations before first dealer outreach
- [ ] Verify `outbound_guard.py` deduplication window is exactly 24h (not session-scoped)

### Short-term (before first paying dealer)

- [ ] Add memory guard in `image_sanitizer.py`: check free RAM before PaddleOCR init, abort + alert if <2 GB
- [ ] Add macOS RAM alert: Telegram notification if system RAM >80% for 5+ minutes
- [ ] Verify only one process writes to `cove_tracker.duckdb` (no concurrent DuckDB writers)
- [ ] Disable macOS automatic reboots for OS updates
- [ ] Document VPS migration procedure (Hetzner CX22 + headless Chrome setup)

### Accepted risks (no action required now)

- **simple-lama-inpainting dormancy**: library is stable, fallback is clear, cost to swap is ~2h
- **DuckDB for CoVe**: correct tool choice, no action needed
- **whatsapp-web.js unofficial status**: no zero-cost alternative; risk accepted, mitigated operationally

---

## References

- PaddleOCR memory leak (CPU device): https://github.com/PaddlePaddle/PaddleOCR/issues/15631
- PaddleOCR macOS freeze: https://github.com/PaddlePaddle/PaddleOCR/issues/11079
- PaddleOCR memory leak (limit_side_len): https://github.com/PaddlePaddle/PaddleOCR/issues/16168
- PaddleOCR v3.4.0 release: https://github.com/PaddlePaddle/PaddleOCR/releases
- whatsapp-web.js ban issues: https://github.com/pedroslopez/whatsapp-web.js/issues/532
- WhatsApp ban mitigation (Green API): https://green-api.com/en/blog/reduce-the-risk-of-WA-blocking/
- simple-lama-inpainting GitHub: https://github.com/enesmsahin/simple-lama-inpainting
- DuckDB vs SQLite comparison: https://betterstack.com/community/guides/scaling-python/duckdb-vs-sqlite/
- OpenCV LaMa fallback: https://huggingface.co/opencv/inpainting_lama
