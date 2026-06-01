# ARGOS Automotive — Code Audit Report
**Date:** 2026-04-10  
**Audited directories:** `src/cove/`, `wa-intelligence/`, `tools/scripts/`  
**Auditor:** Claude Code (agent mode)  
**Scope:** Pattern consistency, error handling, dead code, test coverage, security, duplication, resource cleanup

---

## Severity Legend
- **CRITICAL** — Active risk of data loss, security breach, or production failure
- **HIGH** — Silent failure, incorrect behavior, or significant maintainability debt
- **MEDIUM** — Code quality issues that can cause bugs under edge conditions
- **LOW** — Style, consistency, minor smells
- **INFO** — Observations worth tracking but no immediate action required

---

## CRITICAL

### C-1: Hardcoded Telegram Bot Token in deploy.sh and agent-ops.md
**File:** `wa-intelligence/deploy.sh:87`, `.claude/agents/agent-ops.md:99`  
**Issue:** The real Telegram bot token `<REDACTED-TELEGRAM-TOKEN>` is hardcoded in two tracked files. Even if the repo is now private, the token appears in git history and is visible to anyone with repo access. An attacker with this token can send Telegram messages impersonating the ARGOS bot, read all Telegram bot updates, and potentially intercept human-approval commands (`/approva`, `/modifica`).  
**Fix:**
1. Immediately revoke and regenerate the bot token in BotFather.
2. Remove the literal token from both files — replace with `${ARGOS_TELEGRAM_TOKEN}` or a placeholder comment.
3. Run `git filter-repo --path wa-intelligence/deploy.sh --invert-paths` (or BFG) if the token must be expunged from history.

---

### C-2: NameError Risk — `llm_cost_info` Used Before Assignment
**File:** `wa-intelligence/response-analyzer.py:1516`  
**Issue:** The variable `llm_cost_info` is conditionally assigned at line 1504 (inside `if template_handled`) but then referenced unconditionally at line 1516:
```python
llm_cost_info = llm_cost_info if template_handled else ''
```
If `template_handled` is `False` (the common path), `llm_cost_info` was never defined, causing `NameError`. This would crash every response-analyzer invocation that reaches the LLM path, silently killing dealer response handling.  
**Fix:** Initialize `llm_cost_info = ''` before the `if template_handled` block (around line 1478).

---

### C-3: Incomplete Double-NEGATIVE → ARCHIVED Logic
**File:** `wa-intelligence/state_machine.py:229-241`  
**Issue:** The business rule "2+ NEGATIVE from ENGAGED → ARCHIVED" is explicitly listed in a comment but the actual implementation is a no-op:
```python
# Semplificato: se gia' in ENGAGED e riceve NEGATIVE, resta.
# Se riceve 2° NEGATIVE → ARCHIVED (da implementare con tracking)
```
The count query at line 233-238 uses the wrong filter — it counts all inbound messages (not just NEGATIVE-classified ones), and the result is never compared to a threshold. A dealer who sends 10 angry "no" messages will never be archived, continuing to waste system resources and potentially triggering repeated outbound.  
**Fix:** Track intent per-message in `messages` table with a `classified_intent` column, then count `classified_intent = 'NEGATIVE'` in the last N inbound messages. Alternatively, store a `negative_count` integer column on `conversations` and increment it on each NEGATIVE inbound.

---

### C-4: Code Injection via Dynamically-Generated Python in `auto_approve_and_send`
**File:** `wa-intelligence/response-analyzer.py:1278-1307`  
**Issue:** The `auto_approve_and_send` function builds a Python script as a multi-line f-string and executes it via `subprocess.Popen([sys.executable, '-c', send_script])`. The script embeds:
- `reply_id` (validated by DB fetch, relatively safe)
- `api_key` (from env — could contain `'` or `"` breaking the string)
- `db_path` (from env — path could contain quotes)
- `payload_dict` (JSON-serialized, but inlined into Python source)

If `api_key` or `db_path` contain single quotes, the generated Python is syntactically broken. If a dealer message somehow contaminated `payload_dict`, it could escape the JSON string context.  
**Fix:** Use a temp JSON file or pass arguments via environment variables rather than string interpolation into Python source code. A cleaner pattern:
```python
import tempfile, json
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
    json.dump(payload_dict, f)
    tmpfile = f.name
subprocess.Popen([sys.executable, 'wa-intelligence/send_later.py', '--payload', tmpfile, '--sleep', str(sleep_s)])
```

---

## HIGH

### H-1: Missing `busy_timeout` in Most SQLite Connections
**File:** `wa-intelligence/telegram-handler.py:92-101`, `wa-intelligence/scheduler.py:103-120`, `wa-intelligence/response-analyzer.py:1519-1526`, `wa-intelligence/response-analyzer.py:1145-1158`  
**Issue:** `state_machine.py` correctly sets `PRAGMA busy_timeout=10000` on all its connections, but multiple other files open SQLite connections without it:
- `telegram-handler.py`: `db_query()` and `db_exec()` use plain `sqlite3.connect(DB_PATH)` with no busy_timeout
- `scheduler.py`: `load_active_dealers()` uses plain connect
- `response-analyzer.py`: inline `sqlite3.connect` blocks for NEGATIVE handling and `save_pending_reply` have no busy_timeout

With 4 concurrent processes (wa-daemon, tg-bot, scheduler, response-analyzer) all writing to the same SQLite, this is a real risk of `OperationalError: database is locked` under load.  
**Fix:** Create a shared `_connect(db_path)` helper in each module (or a shared `db_utils.py`) that always sets both WAL and busy_timeout:
```python
def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=10000')
    return con
```

---

### H-2: OBJ-3 and OBJ-4 Swapped in TEMPLATE_MAP
**File:** `wa-intelligence/templates.py:172-173`  
**Issue:** The template map has:
```python
("OBJ-3", "ENGAGED"):  "OBJ_4_TIMING",   # OBJ-3 = "non ho tempo" → sends trust/references template
("OBJ-4", "ENGAGED"):  "OBJ_3_TRUST",    # OBJ-4 = "garanzie/fiducia" → sends timing template
```
OBJ-3 in the classifier patterns (`response-analyzer.py:901`) is "non ho tempo / occupato" (timing objection). The correct template for timing is `OBJ_4_TIMING`. But `OBJ_4_TIMING` says "Se preferisce, la ricontatto tra {followup_days} giorni" — that is correct for timing. The swap means dealers asking about trust/guarantees (OBJ-4) get a timing reply, and dealers saying they're busy (OBJ-3) get the trust/references reply.  
**Fix:**
```python
("OBJ-3", "ENGAGED"):  "OBJ_4_TIMING",   # ← should be OBJ_3_TRUST (trust/references)
("OBJ-4", "ENGAGED"):  "OBJ_3_TRUST",    # ← should be OBJ_4_TIMING (timing/patience)
```
Wait — verify intent: OBJ-3 patterns are timing ("non ho tempo"), OBJ-4 patterns are trust ("garanzie, referenze"). `OBJ_3_TRUST` template contains "Ho lavorato con concessionari" (trust content). `OBJ_4_TIMING` template contains "la ricontatto tra X giorni" (timing content). So the swap should be:
```python
("OBJ-3", "ENGAGED"):  "OBJ_4_TIMING",   # timing objection → timing template (already correct numerically)
("OBJ-4", "ENGAGED"):  "OBJ_3_TRUST",    # trust objection → trust template (already correct numerically)
```
Actually the naming is OBJ_3_TRUST and OBJ_4_TIMING where the number reflects the template's purpose, not the objection number. The current code has OBJ-3 (timing) mapped to OBJ_4_TIMING (timing content) which IS correct. Re-reading:  `OBJ_3_TRUST = "Ho lavorato con concessionari in {reference_area} — posso chiedere una referenza"` and `OBJ_4_TIMING = "Se preferisce, la ricontatto tra {followup_days} giorni"`. With OBJ-3=timing objection mapped to OBJ_4_TIMING, and OBJ-4=trust objection mapped to OBJ_3_TRUST — this is **correct by content** but visually confusing. Mark as INFO: the naming is misleading but functional.

### H-2 (revised): Template Name / Objection Number Mismatch is Confusing but Functionally Correct — demoted to LOW (see L-2)

---

### H-2: `DAY1_INTRO` is a Silent Duplicate of `DAY1_PREMIUM`
**File:** `wa-intelligence/templates.py:44-53`  
**Issue:** `DAY1_INTRO` is an exact copy of `DAY1_PREMIUM` (same text character-for-character). The comment says "Alias per backward compatibility". However both templates are live in `STATES["COLD"]["allowed_templates"]` and both are active candidates for `can_send()`. If `select_day1_variant()` returns `DAY1_PREMIUM` but the caller passes `DAY1_INTRO`, the dedup check (`is_duplicate`) will pass because the hash is of the message text — identical text would actually be caught. But `can_send()` checks template_id against allowed_templates, so both pass. This is dead code masquerading as a feature.  
**Fix:** Remove `DAY1_INTRO` from `TEMPLATES` dict and from `STATES["COLD"]["allowed_templates"]`. Replace any existing usages with `DAY1_PREMIUM`.

---

### H-3: Response Analyzer Env Var Name Mismatch (ARGOS_TELEGRAM_TOKEN vs TELEGRAM_BOT_TOKEN)
**File:** `wa-intelligence/response-analyzer.py:51` vs `src/cove/image_sanitizer.py:173`  
**Issue:** `response-analyzer.py` reads `ARGOS_TELEGRAM_TOKEN` into `TELEGRAM_BOT_TOKEN` (local var). `image_sanitizer.py` reads `TELEGRAM_BOT_TOKEN` (different env var name). `scheduler.py` and `telegram-handler.py` also use `ARGOS_TELEGRAM_TOKEN`. This split means the sanitizer's TG alerts will silently fail if only `ARGOS_TELEGRAM_TOKEN` is set in `.env` (the common case). The `.env` template in `ecosystem.config.js` only exports `ARGOS_TELEGRAM_TOKEN`.  
**Fix:** Standardize on `ARGOS_TELEGRAM_TOKEN` everywhere. In `image_sanitizer.py` change:
```python
token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
```
to:
```python
token = os.environ.get("ARGOS_TELEGRAM_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
```
Similarly for `TELEGRAM_ADMIN_CHAT_IDS` — standardize to `ARGOS_TELEGRAM_CHAT_ID`.

---

### H-4: `save_pending_reply` Returns `reply_id` Even on DB Error
**File:** `wa-intelligence/response-analyzer.py:1142-1158`  
**Issue:**
```python
def save_pending_reply(...):
    reply_id = f"reply_{uuid.uuid4().hex[:8]}"
    con = sqlite3.connect(db_path, timeout=10)
    try:
        con.execute("INSERT INTO pending_replies ...")
        con.commit()
        return reply_id
    except Exception as e:
        print(f'[ERROR] save_pending_reply: {e}')
        return reply_id   # ← returns same id even on failure!
    finally:
        con.close()
```
If the INSERT fails (schema mismatch, locked DB), the function returns the `reply_id` as if it succeeded. Callers will then attempt to approve a non-existent reply, triggering a silent no-op or a later KeyError.  
**Fix:** Return `None` on exception and add a null-check at every call site.

---

### H-5: `db_query` in `telegram-handler.py` Missing WAL + busy_timeout, Also Swallows All Errors
**File:** `wa-intelligence/telegram-handler.py:91-101`  
**Issue:** `db_query` connects without WAL/busy_timeout and catches all exceptions, returning `[]` silently. For the `/approva` command this means a locked DB returns empty rows, causing the bot to reply "Reply ID non trovato" — a confusing false negative that may cause Luke to retry the command, creating duplicate approvals.  
**Fix:** Add WAL/busy_timeout (see H-1). For `db_query`, let `OperationalError: database is locked` propagate so the caller can handle it specifically (retry or inform user).

---

### H-6: `process_inbound` Counter Race: `record_inbound` Updates DB Before Re-Reading State
**File:** `wa-intelligence/state_machine.py:220-246`  
**Issue:** `process_inbound` calls `record_inbound()` (which commits) then immediately calls `get_dealer_state()` to read the updated row. Between the two calls another process (e.g. the scheduler) could read the state mid-update. More critically, `record_inbound` and the subsequent `update_state` are two separate transactions — if the process dies between them, the inbound is counted but the state is not updated. This leaves the dealer stuck with `inbound_count > 0` but wrong state.  
**Fix:** Combine `record_inbound` + state transition into a single atomic transaction:
```python
def process_inbound(db_path, dealer_id, intent):
    con = sqlite3.connect(db_path, timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=10000')
    try:
        con.execute("UPDATE conversations SET inbound_count = COALESCE(inbound_count,0)+1, last_inbound_at = datetime('now') WHERE dealer_id = ?", [dealer_id])
        row = con.execute("SELECT * FROM conversations WHERE dealer_id = ?", [dealer_id]).fetchone()
        # ... compute new_state ...
        if new_state != current_state:
            con.execute("UPDATE conversations SET conversation_state = ?, state_updated_at = datetime('now') WHERE dealer_id = ?", [new_state, dealer_id])
        con.commit()
        return new_state
    finally:
        con.close()
```

---

### H-7: `fill_template` Double-Format Bug on KeyError Fallback
**File:** `wa-intelligence/templates.py:141-151`  
**Issue:** The `except KeyError` block attempts to fix missing slots by removing them from the template string, then calls `result.format(**merged)` a second time. But `result` at this point has already had some `{placeholder}` substitutions from the first `template.format(**merged)` call — which raises `KeyError` for the first missing key. The partially-formatted `result` still contains already-substituted content mixed with remaining `{slot}` patterns. The regex remove loop then modifies `result` correctly, but the final `result.format(**merged)` can still fail if the regex removal missed edge cases (e.g. slots with format specs like `{price:.2f}`).  
**Fix:** Pre-validate slot presence before calling `format()`:
```python
def fill_template(template_id, data):
    template = TEMPLATES.get(template_id, "")
    merged = {**SLOT_DEFAULTS, **{k: v for k, v in data.items() if v}}
    # Fill all unknowns with empty string proactively
    for match in re.finditer(r'\{(\w+)\}', template):
        merged.setdefault(match.group(1), '')
    return template.format(**merged)
```

---

### H-8: `image_sanitizer.py` — `_send_tg_alert` Uses `requests` Without Import Guard
**File:** `src/cove/image_sanitizer.py:179`  
**Issue:** `_send_tg_alert` imports `requests` inline but the top of the file only has a try/except guard for `PIL` and `cv2`. If `requests` is not installed (it is not in stdlib), this raises `ImportError` inside the alert function — which is already inside a broad `except Exception` — silently swallowing the alert entirely. Given that TG alerts are the only human notification channel for inpainting quality issues, silent failure here is a production gap.  
**Fix:** Add a top-level import guard for `requests`:
```python
try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    log.warning("requests not installed — TG photo alerts disabled")
```
And in `_send_tg_alert`, check `REQUESTS_AVAILABLE` before proceeding.

---

## MEDIUM

### M-1: `_check_km_per_anno` Uses Calendar Year Subtraction, Not Actual Age
**File:** `src/cove/fraud_flags.py:251`  
**Issue:**
```python
age_years = max(ref_date.year - year, 1)
```
A vehicle registered in December 2022 evaluated in January 2023 would compute `age_years = 1` but has been on the road for only ~1 month. A vehicle with 15,000 km would show `15,000 km/year` which is normal — but is actually `180,000 km/year` annualized. This generates false CLEAN results for nearly-new high-km vehicles.  
**Fix:** Use fractional years based on registration month if available, or flag when vehicle age < 6 months and km > threshold.

---

### M-2: `classify_message` Has No Confidence Threshold Gate
**File:** `wa-intelligence/response-analyzer.py:1045-1138`  
**Issue:** The classifier returns classifications with confidence as low as 0.60 (`question_fallback`). Classifications with confidence < 0.70 feed directly into the state machine and template selection. A misclassification at 0.60 confidence can trigger a VEHICLE_PROPOSAL template send to a dealer who was simply asking a general question.  
**Fix:** Add a confidence gate: if `confidence < 0.70` and `cls_type not in ('NEGATIVE', 'POSITIVE')`, return `UNKNOWN` and route to HOLD flow (human approval required).

---

### M-3: `auto_approve_and_send` Opens Log Files Without `encoding` or Error Handling
**File:** `wa-intelligence/response-analyzer.py:1303-1307`  
**Issue:**
```python
stdout=open('/tmp/argos-auto-send.log', 'a'),
stderr=open('/tmp/argos-auto-send.log', 'a'),
```
These file handles are opened but never closed (the `Popen` call does not close them). If the analyzer is called many times (one per message), this leaks file descriptors. On macOS the default NOFILE limit is 256 per process.  
**Fix:** Use `subprocess.DEVNULL` or a context manager. The subprocess `close_fds=True` handles the child's FDs but not the parent's opened handles.

---

### M-4: `scheduler.py` `send_daily_digest` Re-reads State After Writing It — Race Condition
**File:** `wa-intelligence/scheduler.py:262-287`  
**Issue:** `send_daily_digest` calls `load_state()` at line 265, then checks `state.get(digest_key)`. But the main `run()` function already modified `state` and called `save_state(state)` before reaching `send_daily_digest`. The function loads a fresh copy from disk (potentially updated by another process), setting the digest key, then saves again. If two scheduler processes run simultaneously (e.g., LaunchAgent fires twice), both could pass the `state.get(digest_key)` check before either saves, causing duplicate morning digests.  
**Fix:** Pass the in-memory `state` dict to `send_daily_digest` instead of reloading from disk.

---

### M-5: `validate_response` in `response-analyzer.py` and `_check_banned_words` in `validator.py` Have Diverging Ban Lists
**File:** `wa-intelligence/response-analyzer.py:1162-1172` vs `wa-intelligence/validator.py:141-146`  
**Issue:** Two separate ban lists:
- `validator.py` bans: `cove, claude, anthropic, openai, gpt, llm, algoritmo, machine learning, intelligenza artificiale, bot, automatico, embedding, rag, prompt, piattaforma, sistema, argos, reimportazione`
- `response-analyzer.py` FORBIDDEN_TERMS bans: `carfax, cove engine, claude, anthropic, openai, chatgpt, intelligenza artificiale, machine learning, algoritmo, embedding, vincario, händlergarantie, non possiamo fatturare`
- `response-analyzer.py` FORBIDDEN_WORDS_EXACT bans only: `cove, gpt, rag, bot`

The analyzer does NOT ban: `llm`, `automatico`, `prompt`, `piattaforma`, `sistema`, `argos`, `reimportazione`. The word `argos` — probably the highest-priority ban — is missing from the analyzer's validation. A LLM could write "ARGOS Automotive" in a reply and the analyzer would pass it.  
**Fix:** Consolidate into a single `BANNED_WORDS` module imported by both. Add `argos`, `llm`, `automatico`, `prompt`, `reimportazione` to the analyzer's forbidden list.

---

### M-6: `image_sanitizer.py` Interior Classifier is Heuristic-Only with a Known 0/10 Track Record
**File:** `src/cove/image_sanitizer.py:236-248`  
**Issue:** The classifier comment explicitly states the OpenCV heuristics "FAILED 0/10 in S110". The current implementation uses only `image_index >= INTERIOR_INDEX_THRESHOLD` (photos at position >= 4 are treated as interior). This means:
- Photos at index 0-3 are always processed even if they're interior shots
- Photos at index 4+ are skipped even if they're exterior with dealer text
Listing photos from some portals don't follow the index convention, potentially leaking dealer identity on interior photos (index 0-3) or missing sanitization on exterior photos (index 4+).  
**Fix:** Add a simple lightweight classifier using color histograms or aspect ratio heuristics as a secondary signal. At minimum, document the known failure mode and add a TODO with priority level.

---

### M-7: `telegram-handler.py` Inline `CREATE TABLE IF NOT EXISTS` in Command Handler
**File:** `wa-intelligence/telegram-handler.py:188-198`  
**Issue:** The `cmd_modifica` function executes a `CREATE TABLE IF NOT EXISTS training_corrections` every time a message is modified. This DDL statement runs inside a user-triggered command handler rather than on startup. While idempotent, it adds latency to every `/modifica` command and is an architectural smell — schema creation belongs in initialization code.  
**Fix:** Move the `training_corrections` table creation into `ensure_tables()` in `dashboard/db.py` or into a startup initialization function.

---

### M-8: `track_cost` Creates the `llm_costs` Table Inline but Dashboard `db.py` Already Creates It
**File:** `wa-intelligence/response-analyzer.py:768-779` vs `wa-intelligence/dashboard/db.py:69-75`  
**Issue:** Both files contain `CREATE TABLE IF NOT EXISTS llm_costs` with different schemas:
- `response-analyzer.py`: `(id TEXT PRIMARY KEY, dealer_id TEXT, model TEXT, input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER, cost_usd REAL, created_at TEXT)`
- `dashboard/db.py`: `(id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT, tokens INTEGER, cost_usd REAL, dealer_id TEXT, purpose TEXT, created_at TEXT)`

The schemas are incompatible: the analyzer uses `input_tokens/output_tokens` columns that the dashboard schema doesn't have; the dashboard uses `tokens` (total) and `purpose` columns that the analyzer doesn't write. The dashboard's `get_llm_costs()` query reads `cost_usd` which works, but `tokens` would always return NULL for rows written by the analyzer.  
**Fix:** Reconcile into a single schema. Use the analyzer's richer schema and update `dashboard/db.py`.

---

### M-9: `tools/scripts/` Contains Many Session-Specific Dead Scripts
**Files:** `tools/scripts/SESSION_33_MARIO_MONITORING.py`, `mario_collection_monitor_session38.py`, `mario_deployment_setup.py`, `mario_kb_test_session40.py`, `enterprise_subagent_architecture.py`, `dealer_database_structure_session41.py`, `immediate_email_campaign.py`, `thepopebot_integration_evaluation.py`, `storico_credibilita_argos.py`, `github_actions_deployment.py`  
**Issue:** At least 10 of the 20 Python files in `tools/scripts/` appear to be one-time session scripts from a previous project era (Mario = old project name, session 33/38/40/41). These are dead code that:
- Pollute the module namespace
- Can be accidentally imported
- Create confusion about what is production vs exploratory
- Some may have hardcoded paths or credentials from the old project  
**Fix:** Move to `archive/` directory or delete. Keep only: `pdf_generator_enterprise.py`, `price_validator_realtime.py`, `price_validator_v2.py`, `smoke_test_autoscout.py`.

---

## LOW

### L-1: Inconsistent `datetime.utcnow()` vs `datetime.now(timezone.utc)`
**Files:** `src/cove/fraud_flags.py:115`, `src/cove/scraper_cove_pipeline.py:76`, vs `src/cove/pipeline_orchestrator.py:59`  
**Issue:** `fraud_flags.py` and other cove modules use the deprecated `datetime.utcnow()` (naive datetime, deprecated in Python 3.12). `pipeline_orchestrator.py` correctly uses `datetime.now(timezone.utc)`. This inconsistency can cause off-by-timezone bugs when comparing timestamps across modules.  
**Fix:** Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`. For `FraudFlagsResult.checked_at`, use `.isoformat()` on the timezone-aware object.

---

### L-2: OBJ Template Naming Inverted (Cosmetic, Functionally Correct)
**File:** `wa-intelligence/templates.py:85-99`  
**Issue:** Template `OBJ_3_TRUST` handles trust/reference objections and `OBJ_4_TIMING` handles timing/patience objections. The classifier uses `OBJ-3` for timing and `OBJ-4` for trust. The template map correctly cross-maps them (OBJ-3 → OBJ_4_TIMING, OBJ-4 → OBJ_3_TRUST), but the naming is confusing to any developer reading the code.  
**Fix:** Rename templates to `TPL_TRUST_OBJECTION` and `TPL_TIMING_OBJECTION`, or align the numbering. Document the inversion explicitly.

---

### L-3: Inconsistent `print()` vs `log()` Usage Across WA Intelligence
**Files:** `wa-intelligence/response-analyzer.py`, `wa-intelligence/telegram-handler.py`, `wa-intelligence/scheduler.py`  
**Issue:** `scheduler.py` and `telegram-handler.py` use a `log(msg)` function that writes to both stdout and a log file. `response-analyzer.py` uses only `print()` statements. PM2 captures stdout, so both work, but the analyzer's output is not written to `/tmp/argos-*.log` — making it invisible to file-based log monitoring.  
**Fix:** Add a `log()` function to `response-analyzer.py` consistent with the other modules, writing to `/tmp/argos-analyzer.log`.

---

### L-4: `is_duplicate` Computes `msg_hash` But Never Uses It
**File:** `wa-intelligence/state_machine.py:193-216`  
**Issue:**
```python
msg_hash = hashlib.md5(message_text.strip().lower().encode()).hexdigest()
...
row = con.execute("SELECT COUNT(*) FROM messages ...").fetchone()
```
The `msg_hash` is computed and the `row` count is fetched, but neither is actually used in the dedup logic. The function only checks the `recent` list of body texts by recomputing hashes inline. The `row` count variable is completely unused. This is dead code that wastes computation.  
**Fix:** Remove the unused `msg_hash` computation and the unused `row = con.execute(...)` query (the COUNT query at line 197-202).

---

### L-5: `SLOT_DEFAULTS` `dealer_name` Defaults to Empty String
**File:** `wa-intelligence/templates.py:119`  
**Issue:** `SLOT_DEFAULTS["dealer_name"] = ""`. When a dealer's name is missing and the `VEHICLE_PROPOSAL` template starts with `"{dealer_name}, un'opportunita' concreta."`, the result is `", un'opportunita' concreta."` — a grammatically broken opening that erodes credibility.  
**Fix:** Default to `"Buongiorno"` instead of `""`, or add validation in `fill_template` to reject templates where `dealer_name` is required but empty.

---

### L-6: `response-analyzer.py` Imports `re` Both at Top Level and Inside Functions
**File:** `wa-intelligence/response-analyzer.py:23`, and inside `validate_response:1176`, `extract_vehicle_request:954`  
**Issue:** `import re` appears at line 23 (top-level) and then again with `import re` inside `validate_response` and `extract_vehicle_request`. The inner imports are no-ops (Python caches modules) but are noise that implies the developer was unsure about scope.  
**Fix:** Remove all inline `import re` statements since it's already imported at module level.

---

### L-7: `auth.py` Default Password Hardcoded as Fallback
**File:** `wa-intelligence/dashboard/auth.py:18`  
**Issue:**
```python
DASHBOARD_PASSWORD = os.environ.get('ARGOS_DASHBOARD_PASSWORD', 'argos2026')
```
If `ARGOS_DASHBOARD_PASSWORD` is not in `.env`, the dashboard uses the hardcoded default `argos2026`. Anyone who knows this default (e.g., from reading the codebase) can access the dashboard.  
**Fix:** Remove the default value — raise an error on startup if the variable is missing:
```python
DASHBOARD_PASSWORD = os.environ.get('ARGOS_DASHBOARD_PASSWORD')
if not DASHBOARD_PASSWORD:
    raise ValueError("ARGOS_DASHBOARD_PASSWORD must be set in .env")
```

---

### L-8: Missing Type Hints in Core WA Intelligence Functions
**Files:** `wa-intelligence/state_machine.py`, `wa-intelligence/validator.py`, `wa-intelligence/templates.py`  
**Issue:** Some functions have type hints (e.g., `validate()`, `FraudFlagsChecker.run()`), others don't (e.g., `can_send()` returns `tuple` without type annotation, `fill_template()` has no return hint, `select_day1_variant()` lacks type hints on the list parameter). This is inconsistent within the same module.  
**Fix:** Add `from __future__ import annotations` and consistent type hints to all public functions in these modules.

---

## INFO

### I-1: No Unit Tests for `src/cove/fraud_flags.py` Beyond `__main__` Block
**File:** `src/cove/fraud_flags.py:455-477`  
**Issue:** The fraud flag checker has a `__main__` test block but no pytest-compatible tests. `tools/test_e2e_full.py` and `wa-intelligence/test_pipeline_s106.py` test the WA pipeline but do not exercise the CoVe scoring or fraud detection code paths. A regression in `fraud_flags.py` thresholds would not be caught by CI.  
**Recommendation:** Extract the test cases from the `__main__` block into a `tests/test_fraud_flags.py` pytest file.

---

### I-2: No Tests for `image_sanitizer.py`
**File:** `src/cove/image_sanitizer.py`  
**Issue:** The sanitizer has no test file. The `__main__` test from S110/S111 validated it manually but no automated regression exists. Changes to PaddleOCR thresholds or inpainting logic could silently degrade sanitization quality.  
**Recommendation:** Add at minimum a smoke test that runs the pipeline on a synthetic image with known text and verifies output.

---

### I-3: `cove_params_calibrated.py` Is Not Imported Anywhere
**File:** `src/cove/cove_params_calibrated.py`  
**Issue:** A grep across the codebase shows no imports of `cove_params_calibrated`. The calibrated parameters may be intended for use in `cove_engine_v4.py` (read-only) but if they're not currently wired in, they have no effect.  
**Recommendation:** Verify whether `cove_engine_v4.py` imports this module (audit the read-only file). If not, document why or remove.

---

### I-4: `MAX_YEAR` in `fraud_flags.py` is a Manual Constant
**File:** `src/cove/fraud_flags.py:41`  
**Issue:** `MAX_YEAR: int = 2025` is a hardcoded constant that needs manual update each January. In 2027, a 2026 vehicle would be incorrectly flagged as `YEAR_OUT_OF_SEGMENT` (REJECTED).  
**Recommendation:** Replace with `datetime.now().year` or `datetime.now().year + 1` to be dynamic.

---

### I-5: `TEMPLATE_MAP` Missing Several State/Intent Combinations
**File:** `wa-intelligence/templates.py:155-175`  
**Issue:** No template exists for:
- `("POSITIVE", "INTERESTED")` — dealer confirms interest but no next template
- `("CURIOSITY", "INTERESTED")` — dealer asks follow-up question in INTERESTED state
- `("VEHICLE_REQUEST", "CONVERTING")` — dealer requests specific vehicle while converting
- Any template for `CONVERTING` state except `OBJ_2_FEE` from an objection

When these combinations occur, `select_template()` returns `""`, falling through to the LLM path. This is by design (LLM handles edge cases) but the missing combinations should be documented as intentional gaps.  
**Recommendation:** Add a `# INTENTIONAL_GAPS` comment block listing these combinations explicitly.

---

### I-6: `response-analyzer.py` Env Var `ARGOS_DB_PATH` Falls Back to Empty String
**File:** `wa-intelligence/response-analyzer.py:62`  
**Issue:**
```python
DB_PATH = os.environ.get('ARGOS_DB_PATH', '')
```
If `ARGOS_DB_PATH` is not set, the script runs with `DB_PATH = ''`. SQLite with an empty path string creates an in-memory database (`:memory:` behavior varies — actually `sqlite3.connect('')` raises `OperationalError: unable to open database file`). This would cause a runtime crash rather than a clear startup error.  
**Recommendation:** Validate `DB_PATH` on startup and fail fast with a clear error message if unset.

---

## Summary Table

| ID | Severity | File | Issue |
|----|----------|------|-------|
| C-1 | CRITICAL | `wa-intelligence/deploy.sh:87`, `.claude/agents/agent-ops.md:99` | Hardcoded live Telegram bot token |
| C-2 | CRITICAL | `wa-intelligence/response-analyzer.py:1516` | NameError on `llm_cost_info` in LLM path |
| C-3 | CRITICAL | `wa-intelligence/state_machine.py:229-241` | Double-NEGATIVE → ARCHIVED rule is dead code |
| C-4 | CRITICAL | `wa-intelligence/response-analyzer.py:1278-1307` | Dynamic Python source generation with injection risk |
| H-1 | HIGH | Multiple WA intelligence files | Missing `busy_timeout` on SQLite connections |
| H-2 | HIGH | `wa-intelligence/templates.py:172-173` | `DAY1_INTRO` is exact duplicate of `DAY1_PREMIUM` (dead alias) |
| H-3 | HIGH | `wa-intelligence/response-analyzer.py:51` vs `src/cove/image_sanitizer.py:173` | TG env var name mismatch — sanitizer alerts silently fail |
| H-4 | HIGH | `wa-intelligence/response-analyzer.py:1155` | `save_pending_reply` returns ID on DB failure |
| H-5 | HIGH | `wa-intelligence/telegram-handler.py:92-101` | `db_query` missing WAL/busy_timeout, swallows all errors |
| H-6 | HIGH | `wa-intelligence/state_machine.py:220-246` | Non-atomic inbound recording + state transition |
| H-7 | HIGH | `wa-intelligence/templates.py:141-151` | Double-format bug in `fill_template` KeyError fallback |
| H-8 | HIGH | `src/cove/image_sanitizer.py:179` | `requests` import not guarded — TG alerts silently fail |
| M-1 | MEDIUM | `src/cove/fraud_flags.py:251` | Calendar-year age calculation causes false negatives |
| M-2 | MEDIUM | `wa-intelligence/response-analyzer.py:1045` | No confidence threshold gate — low-confidence classification triggers template sends |
| M-3 | MEDIUM | `wa-intelligence/response-analyzer.py:1303` | File descriptor leak in `auto_approve_and_send` |
| M-4 | MEDIUM | `wa-intelligence/scheduler.py:265` | `send_daily_digest` race condition via disk state reload |
| M-5 | MEDIUM | `response-analyzer.py:1162` vs `validator.py:141` | Diverging ban lists — `argos` missing from analyzer |
| M-6 | MEDIUM | `src/cove/image_sanitizer.py:236` | Interior classifier 0/10 accuracy — undocumented failure mode |
| M-7 | MEDIUM | `wa-intelligence/telegram-handler.py:188` | DDL in command handler instead of initialization |
| M-8 | MEDIUM | `response-analyzer.py:768` vs `dashboard/db.py:69` | `llm_costs` table has two incompatible schemas |
| M-9 | MEDIUM | `tools/scripts/` | 10+ dead session scripts from previous project |
| L-1 | LOW | `src/cove/fraud_flags.py:115` | `datetime.utcnow()` deprecated (Python 3.12+) |
| L-2 | LOW | `wa-intelligence/templates.py` | OBJ template naming inverted vs classifier numbering |
| L-3 | LOW | `wa-intelligence/response-analyzer.py` | `print()` instead of `log()` — no file logging |
| L-4 | LOW | `wa-intelligence/state_machine.py:193` | `msg_hash` and COUNT query computed but never used |
| L-5 | LOW | `wa-intelligence/templates.py:119` | `dealer_name` defaults to `""` — broken grammar in output |
| L-6 | LOW | `wa-intelligence/response-analyzer.py` | Redundant inline `import re` inside functions |
| L-7 | LOW | `wa-intelligence/dashboard/auth.py:18` | Hardcoded default password `argos2026` |
| L-8 | LOW | `wa-intelligence/` core modules | Inconsistent type hints |
| I-1 | INFO | `src/cove/fraud_flags.py` | No pytest tests for fraud checker |
| I-2 | INFO | `src/cove/image_sanitizer.py` | No automated tests for sanitizer |
| I-3 | INFO | `src/cove/cove_params_calibrated.py` | Module may not be imported anywhere |
| I-4 | INFO | `src/cove/fraud_flags.py:41` | `MAX_YEAR` hardcoded, needs manual update each January |
| I-5 | INFO | `wa-intelligence/templates.py` | Several state/intent gaps in TEMPLATE_MAP |
| I-6 | INFO | `wa-intelligence/response-analyzer.py:62` | `ARGOS_DB_PATH` empty-string fallback causes confusing crash |

---

## Priority Fix Order (next sprint)

1. **C-1** — Rotate Telegram token immediately (5 min, zero risk)
2. **C-2** — Fix NameError: `llm_cost_info = ''` before template block (2 min)
3. **H-3** — Fix TG env var mismatch in sanitizer (5 min)
4. **M-5** — Add `argos` to analyzer ban list (2 min)
5. **L-5** — Fix `dealer_name` default to avoid broken grammar (2 min)
6. **H-1** — Add `busy_timeout` to all SQLite connections (30 min)
7. **H-4** — `save_pending_reply` return `None` on error (5 min)
8. **H-2** — Remove `DAY1_INTRO` dead alias (5 min)
9. **C-3** — Implement double-NEGATIVE → ARCHIVED properly (1h)
10. **M-8** — Reconcile `llm_costs` table schemas (30 min)
