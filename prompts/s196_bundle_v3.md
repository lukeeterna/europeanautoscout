# S196 QUALITY VALIDATION BUNDLE V3 — INLINE diff + runtime test reale

> Bundle per re-validation esterna su claude.ai web. Gate `external_score ≥ 7.0/10` per sblocco STEP 6 deploy iMac + AMBRA stress + E2E + Day 1 Stile Car decision.

---

## Contesto storico (perché siamo qui)

| Gate | Self-score | External | Delta | Outcome |
|------|-----------|----------|-------|---------|
| S194 STEP 0.5 | 7.2 | 6.3 | -0.9 | GO_WITH_PRECONDITIONS — handoff S195 |
| S195 STEP 0.5 V2 | 6.3 | 5.5 | -0.8 | NO_GO — handoff S196 |
| **S196 STEP 0.5 V3** | **?** | **?** | **?** | **da te (claude.ai web)** |

**Pattern strutturale 2 gate consecutivi**: self-assessment inflation -0.8/-0.9pt. Root cause: validation interna con segnali deboli (py_compile + code-reviewer LLM). **Mitigation S196**: runtime test reale come gate primario per self-score.

---

## Cosa fa S196 (4 fix paralleli)

### P1 — Runtime functional test approve_reply (CORE)
Nuovo `tools/tests/test_approve_reply_runtime.py`. **5 scenari** su fixture SQLite con schema **reale produzione iMac** (dump 2026-05-26):
- A: happy path (INSERT bridge_outbound OK)
- B: schema drift (conversations.phone_number rinominata → exception path)
- C: BRIDGE_DB_PATH unset (env missing → skip bridge)
- D: duplicate approve (idempotency UPDATE rowcount=0)
- E: orphaned reply (pending_reply senza conversations row → phone_or_text_missing)

**Output runtime reale** (eseguito 2026-05-26 21:14):
```
RUNTIME TEST RESULT: 5/5 PASS
```

### P2 — Signature `approve_reply` bool → dict
File: `wa-intelligence/dashboard/db.py` + `app.py`. Refactor da `-> bool` a `-> dict` con 7 error codes strutturati. Caller singolo `action_approve_reply` propaga stato + alert Telegram se `bridge_queued=False`. **Trade-off motivato**: breaking change su un solo callsite — silent-failure precedente era bug peggiore.

### P3 — BRIDGE_DB_PATH precondition hard
File: `wa-intelligence/ecosystem.config.js`. **Root cause confermato via SSH iMac `pm2 jlist`**: argos-dashboard era startato manualmente fuori ecosystem → SHARED_ENV vuoto → BRIDGE_DB_PATH mancante → silent-failure. Fix: aggiunto 4° processo `argos-dashboard` con SHARED_ENV. Startup event in app.py: log ERROR + TG alert se path missing/invalid.

### P4 — Costante `SENTINEL_SKIP_PROMO` modulo-level
File: `src/cove/image_sanitizer.py` + `tools/scripts/pdf_generator_enterprise.py`. 4 hardcoded `"__SKIP_PROMO__"` → costante import. Gate `grep "__SKIP_PROMO__" src/ tools/` → **1 match (solo definizione)**.

---

## Code-review S196 — risultato delegation

Delegato a `code-reviewer` agent (CLAUDE.md #0 delegation-first mandatory):

| Severity | Issue | Status |
|----------|-------|--------|
| HIGH | — | 0 |
| MED-1 | Token TG potenzialmente in URL log via `urllib` exception | **FIXED inline** (catch `type(e).__name__`, no raw `{e}`) |
| MED-2 | `_audit('BRIDGE_INSERTED')` può perdersi silent se commit fallisce | BACKLOG #S196-1 (audit ≠ operational, accepted by reviewer) |
| LOW-1 | `fresh_db_module` test cache fragile | FIXED (comment esplicito) |
| LOW-2 | Gap coverage scenario orphaned reply | **FIXED inline** (scenario E aggiunto, 5/5 PASS) |

---

## Output runtime test (PRIMARY GATE — riproducibile)

Comando: `python3 tools/tests/test_approve_reply_runtime.py` (working dir repo root).

```
======================================================================
S196-P1 runtime test approve_reply (dealer_network + bridge fixtures)
======================================================================
Fixtures dir: /var/folders/wt/df_f2d0j1892qm4jyxgjgfsh0000gn/T/s196_runtime_*

[SCENARIO A] Happy path
  Result: {'approved': True, 'bridge_queued': True, 'error': None}
  bridge_outbound rows: [{'deal_id': 'reply_a001', 'target_phone': '393281234567', 'body': 'Ciao Mario, ho un BMW X3 2021 a 18000.'}]
  → PASS

[SCENARIO B] Schema drift (conversations.phone_number rinominata)
  Result: {'approved': True, 'bridge_queued': False, 'error': 'schema_drift'}
  bridge_outbound count: 0
  pending_replies.approved: 1
  → PASS

[SCENARIO C] BRIDGE_DB_PATH missing
  Result: {'approved': True, 'bridge_queued': False, 'error': 'bridge_db_path_missing'}
  → PASS

[SCENARIO D] Duplicate approve (idempotency)
  1st result: {'approved': True, 'bridge_queued': True, 'error': None}
  2nd result: {'approved': False, 'bridge_queued': False, 'error': 'not_found_or_processed'}
  bridge_outbound count: 1
  → PASS

[SCENARIO E] Orphaned reply (no conversations row)
  Result: {'approved': True, 'bridge_queued': False, 'error': 'phone_or_text_missing'}
  bridge_outbound count: 0
  → PASS

======================================================================
SUMMARY:
  [PASS] A_happy_path
  [PASS] B_schema_drift
  [PASS] C_bridge_missing
  [PASS] D_duplicate
  [PASS] E_orphaned_reply

RUNTIME TEST RESULT: 5/5 PASS
======================================================================
```

---

## DIFF S196 completo INLINE (commit db311b7 vs 88875a8)

`git diff 88875a8..db311b7` — 819 righe totali su 6 file in-scope (BACKLOG.md escluso):

```diff
diff --git a/src/cove/image_sanitizer.py b/src/cove/image_sanitizer.py
index 5571cf9..94ff14c 100644
--- a/src/cove/image_sanitizer.py
+++ b/src/cove/image_sanitizer.py
@@ -135,6 +135,10 @@ MIN_IMAGE_BYTES = 30 * 1024  # 30 KB
 # Area-based check non funziona (inpaint preserva dimensioni anche se contenuto = bianco).
 MIN_OUTPUT_SIZE_RATIO = 0.20
 
+# S196-P4: Modulo-level sentinel — distinguishes intentional skip (promo-slide)
+# from crash (None). Import this rather than hardcoding the string.
+SENTINEL_SKIP_PROMO = "__SKIP_PROMO__"
+
 # Words to keep (car specs, our own branding)
 # S179: expanded with BMW/Mercedes/Audi numeric trims vulnerable in S176
 KEEP_WORDS = frozenset({
@@ -956,7 +960,7 @@ def sanitize_image(
                   f"({ratio_pct:.0f}% of orig) — probable dealer marketing slide")
             # S192 FIX: sentinel string distinct from None (which means crash).
             # Caller must exclude this image from PDF (NOT fallback to RAW).
-            return "__SKIP_PROMO__"
+            return SENTINEL_SKIP_PROMO
 
         # ── STAGE 4: Post-verify + Alert (only if text was masked or SOSPETTO) ──
         if has_mask or sospetti:
@@ -1063,11 +1067,11 @@ def sanitize_all_images(
         if src_path and os.path.exists(src_path):
             safe = sanitize_image(src_path, output_dir, listing_id, i,
                                   seller_name=seller_name)
-            # S193-fix HIGH-1: sentinel "__SKIP_PROMO__" e' truthy → esplicito check
+            # S193-fix HIGH-1 / S196-P4: SENTINEL_SKIP_PROMO e' truthy → esplicito check
             # Senza questo, sentinel string verrebbe trattato come path file → leak
-            if safe and safe != "__SKIP_PROMO__":
+            if safe and safe != SENTINEL_SKIP_PROMO:
                 safe_paths.append(safe)
-            elif safe == "__SKIP_PROMO__":
+            elif safe == SENTINEL_SKIP_PROMO:
                 # Promo-slide intenzionalmente esclusa dal PDF (no leak insegna dealer)
                 pass
 
@@ -1164,8 +1168,8 @@ if __name__ == "__main__":
 
     if sys.argv[1] == "--file" and len(sys.argv) >= 3:
         result = sanitize_image(sys.argv[2])
-        # S193-fix HIGH-1: sentinel "__SKIP_PROMO__" e' truthy → 3-way explicit branch
-        if result == "__SKIP_PROMO__":
+        # S193-fix HIGH-1 / S196-P4: sentinel SENTINEL_SKIP_PROMO e' truthy → 3-way explicit branch
+        if result == SENTINEL_SKIP_PROMO:
             print(f"\nSkipped: {sys.argv[2]} (promo-slide detected)")
         elif result:
             print(f"\nSanitized: {result}")
diff --git a/tools/scripts/pdf_generator_enterprise.py b/tools/scripts/pdf_generator_enterprise.py
index 5d4585d..e3d55ef 100644
--- a/tools/scripts/pdf_generator_enterprise.py
+++ b/tools/scripts/pdf_generator_enterprise.py
@@ -32,6 +32,15 @@ try:
 except ImportError:
     _requests_module = None
 
+# S196-P4: import sentinel costante. image_sanitizer.py guarda le sue deps pesanti
+# (PIL/cv2) con try/except — import della costante stringa funziona sempre.
+# sys.path setup pattern matcha argos_grade (~r.2033) e sanitize_all_images (~r.2043).
+_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
+_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
+if _REPO_ROOT not in sys.path:
+    sys.path.insert(0, _REPO_ROOT)
+from src.cove.image_sanitizer import SENTINEL_SKIP_PROMO
+
 # PDF generation imports
 try:
     from reportlab.pdfgen import canvas
@@ -1649,8 +1658,9 @@ print(json.dumps({{"result": result, "size": os.path.getsize(result) if result a
                 result_path = data.get('result')
                 size = data.get('size', 0)
 
-                # S192 FIX: distinguish promo-skip (sentinel) from crash (None)
-                if result_path == "__SKIP_PROMO__":
+                # S192 FIX / S196-P4: distinguish promo-skip (sentinel) from crash (None)
+                # SENTINEL_SKIP_PROMO importata a module-level (vedi top del file)
+                if result_path == SENTINEL_SKIP_PROMO:
                     print(f"  [SANITIZER] img[{image_index}] EXCLUDED (promo-slide detected — dealer marketing)")
                     return None  # signal exclude to caller
                 if result_path and os.path.exists(result_path) and size > 500:
diff --git a/tools/tests/test_approve_reply_runtime.py b/tools/tests/test_approve_reply_runtime.py
new file mode 100644
index 0000000..ca593cd
--- /dev/null
+++ b/tools/tests/test_approve_reply_runtime.py
@@ -0,0 +1,373 @@
+#!/usr/bin/env python3
+"""
+test_approve_reply_runtime.py — S196-P1 runtime functional test (CORE)
+
+S195 NO_GO root cause: tutti i fix S193 validati solo py_compile + code-reviewer LLM.
+Nessun test runtime con DB reale → silent-failure approve_reply non rilevato.
+
+S196 fix: runtime test con SQLite fixtures schema identico a produzione iMac
+(dealer_network.sqlite + comm-broker/bridge.sqlite). NO mock, NO stub, NO subprocess.
+
+5 scenari:
+  A. happy path        → approved=True, bridge_queued=True, error=None
+  B. schema drift      → approved=True, bridge_queued=False, error="schema_drift"
+  C. BRIDGE_DB_PATH    → approved=True, bridge_queued=False, error="bridge_db_path_missing"
+  D. duplicate         → 1st approve OK, 2nd approve approved=False, error="not_found_or_processed"
+  E. orphaned reply    → pending_reply senza conversations row → error="phone_or_text_missing"
+                          (path raggiungibile in produzione se INSERT race)
+
+Esecuzione:
+  cd /Users/macbook/Documents/combaretrovamiauto-enterprise
+  python3 tools/tests/test_approve_reply_runtime.py
+
+Output gate: "RUNTIME TEST RESULT: 4/4 PASS" → STEP 4 VERDE.
+"""
+
+import os
+import sys
+import tempfile
+import sqlite3
+import shutil
+import importlib
+from pathlib import Path
+
+PROJECT_ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(PROJECT_ROOT))
+
+
+# Schemi REALI iMac (ssh + sqlite3 .schema su 2026-05-26 produzione)
+SCHEMA_PENDING_REPLIES = """
+CREATE TABLE pending_replies (
+    id              TEXT PRIMARY KEY,
+    dealer_id       TEXT,
+    dealer_name     TEXT,
+    inbound_msg_id  TEXT,
+    reply_text      TEXT,
+    reply_label     TEXT,
+    cialdini_trigger TEXT,
+    approved        INTEGER DEFAULT NULL,
+    sent            INTEGER DEFAULT 0,
+    scheduled_at    TEXT,
+    created_at      TEXT DEFAULT (datetime('now')),
+    msg_checksum    TEXT
+);
+"""
+
+SCHEMA_CONVERSATIONS = """
+CREATE TABLE conversations (
+    dealer_id       TEXT PRIMARY KEY,
+    dealer_name     TEXT,
+    city            TEXT,
+    phone_number    TEXT,
+    stock_size      INTEGER,
+    persona_type    TEXT,
+    score           REAL,
+    source          TEXT,
+    notes           TEXT,
+    current_step    TEXT DEFAULT 'PENDING',
+    day1_message    TEXT,
+    recommendation  TEXT DEFAULT 'PENDING',
+    created_at      TEXT DEFAULT (datetime('now')),
+    last_contact_at TEXT,
+    analyzed_at     TEXT,
+    conversation_state TEXT DEFAULT 'COLD',
+    outbound_count INTEGER DEFAULT 0,
+    inbound_count INTEGER DEFAULT 0,
+    last_inbound_at TEXT,
+    state_updated_at TEXT,
+    escalation_flag INTEGER DEFAULT 0,
+    is_active_partner INTEGER DEFAULT 0,
+    partner_since TEXT,
+    total_transactions INTEGER DEFAULT 0,
+    total_revenue_dealer REAL DEFAULT 0,
+    last_analytics_sent TEXT,
+    trusted_partner_sent INTEGER DEFAULT 0,
+    opt_out INTEGER DEFAULT 0,
+    opt_out_at TIMESTAMP,
+    opt_out_source TEXT,
+    opt_out_raw_message TEXT,
+    handoff_source TEXT DEFAULT 'cold',
+    is_micro_dealer INTEGER DEFAULT 0
+);
+"""
+
+SCHEMA_AUDIT_LOG = """
+CREATE TABLE audit_log (
+    id              TEXT PRIMARY KEY,
+    event_type      TEXT,
+    dealer_id       TEXT,
+    payload         TEXT,
+    timestamp_it    TEXT,
+    created_at      TEXT DEFAULT (datetime('now'))
+);
+"""
+
+SCHEMA_BRIDGE_OUTBOUND = """
+CREATE TABLE bridge_outbound (
+    id             INTEGER PRIMARY KEY AUTOINCREMENT,
+    deal_id        TEXT NOT NULL,
+    target_role    TEXT NOT NULL CHECK(target_role IN ('dealer', 'seller')),
+    target_phone   TEXT NOT NULL,
+    template_phase TEXT NOT NULL,
+    template_lang  TEXT NOT NULL,
+    body           TEXT NOT NULL,
+    state_at_send  TEXT NOT NULL,
+    created_ts     INTEGER NOT NULL,
+    approved_ts    INTEGER,
+    sent_ts        INTEGER,
+    sent_status    TEXT,
+    wa_msg_id      TEXT,
+    processing_ts  INTEGER,
+    attempt_count  INTEGER DEFAULT 0
+);
+CREATE UNIQUE INDEX uq_outbound_deal_phone_phase
+    ON bridge_outbound(deal_id, target_phone, template_phase)
+    WHERE sent_ts IS NULL;
+"""
+
+
+def make_fixtures(tmpdir: Path) -> tuple[Path, Path]:
+    """Crea dealer_network.sqlite + bridge.sqlite vuoti con schema reale."""
+    tmpdir.mkdir(parents=True, exist_ok=True)
+    dealer_db = tmpdir / 'dealer_network.sqlite'
+    bridge_db = tmpdir / 'bridge.sqlite'
+
+    con = sqlite3.connect(str(dealer_db))
+    con.executescript(SCHEMA_PENDING_REPLIES + SCHEMA_CONVERSATIONS + SCHEMA_AUDIT_LOG)
+    con.commit()
+    con.close()
+
+    con = sqlite3.connect(str(bridge_db))
+    con.executescript(SCHEMA_BRIDGE_OUTBOUND)
+    con.commit()
+    con.close()
+
+    return dealer_db, bridge_db
+
+
+def seed_pending_reply(dealer_db: Path, reply_id: str, dealer_id: str,
+                       phone: str, reply_text: str, register_conversation: bool = True):
+    """Inserisci una pending_reply + (opz.) conversation con phone."""
+    con = sqlite3.connect(str(dealer_db))
+    if register_conversation:
+        con.execute(
+            "INSERT INTO conversations (dealer_id, dealer_name, phone_number, current_step) "
+            "VALUES (?, ?, ?, ?)",
+            (dealer_id, 'Test Dealer', phone, 'RESPONSE_RECEIVED')
+        )
+    con.execute(
+        "INSERT INTO pending_replies (id, dealer_id, dealer_name, reply_text, approved) "
+        "VALUES (?, ?, ?, ?, NULL)",
+        (reply_id, dealer_id, 'Test Dealer', reply_text)
+    )
+    con.commit()
+    con.close()
+
+
+def fresh_db_module(dealer_db: Path, bridge_db: str = ''):
+    """Re-import db.py con env override (DB_PATH letto a module-level).
+
+    code-review LOW-1: tutti gli scenari DEVONO usare questo helper, NON
+    `from wa-intelligence.dashboard import db`. Il modulo legge DB_PATH a
+    module-level — un import standard congelerebbe il path al primo env.
+    """
+    os.environ['ARGOS_DB_PATH'] = str(dealer_db)
+    if bridge_db:
+        os.environ['BRIDGE_DB_PATH'] = bridge_db
+    else:
+        os.environ.pop('BRIDGE_DB_PATH', None)
+    # forza reimport
+    mod_name = 'wa-intelligence.dashboard.db'
+    # path import workaround per il dash nel nome cartella
+    import importlib.util
+    db_path = PROJECT_ROOT / 'wa-intelligence' / 'dashboard' / 'db.py'
+    spec = importlib.util.spec_from_file_location('argos_dashboard_db', str(db_path))
+    mod = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def scenario_a_happy_path(tmpdir: Path) -> bool:
+    """A: happy path → approved=True, bridge_queued=True, error=None"""
+    print('\n[SCENARIO A] Happy path')
+    dealer_db, bridge_db = make_fixtures(tmpdir / 'a')
+    seed_pending_reply(dealer_db, 'reply_a001', 'dealer_001', '+393281234567',
+                       'Ciao Mario, ho un BMW X3 2021 a 18000.')
+    db = fresh_db_module(dealer_db, str(bridge_db))
+    result = db.approve_reply('reply_a001')
+    print(f'  Result: {result}')
+
+    # Verifica bridge_outbound reale
+    con = sqlite3.connect(str(bridge_db))
+    con.row_factory = sqlite3.Row
+    rows = con.execute("SELECT deal_id, target_phone, body FROM bridge_outbound").fetchall()
+    con.close()
+    print(f'  bridge_outbound rows: {[dict(r) for r in rows]}')
+
+    ok = (
+        result.get('approved') is True
+        and result.get('bridge_queued') is True
+        and result.get('error') is None
+        and len(rows) == 1
+        and rows[0]['deal_id'] == 'reply_a001'
+        and rows[0]['target_phone'] == '393281234567'  # normalizzato (no +)
+        and 'BMW X3' in rows[0]['body']
+    )
+    print(f'  → {"PASS" if ok else "FAIL"}')
+    return ok
+
+
+def scenario_b_schema_drift(tmpdir: Path) -> bool:
+    """B: schema drift → approved=True, bridge_queued=False, error=schema_drift"""
+    print('\n[SCENARIO B] Schema drift (conversations.phone_number rinominata)')
+    Path(tmpdir / 'b').mkdir(parents=True, exist_ok=True)
+    dealer_db, bridge_db = make_fixtures(tmpdir / 'b')
+    seed_pending_reply(dealer_db, 'reply_b001', 'dealer_002', '+393281112222', 'test b')
+
+    # Schema drift: rinomina phone_number
+    con = sqlite3.connect(str(dealer_db))
+    con.execute("ALTER TABLE conversations RENAME COLUMN phone_number TO phone_num_old")
+    con.commit()
+    con.close()
+
+    db = fresh_db_module(dealer_db, str(bridge_db))
+    result = db.approve_reply('reply_b001')
+    print(f'  Result: {result}')
+
+    con = sqlite3.connect(str(bridge_db))
+    rows = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()
+    con.close()
+    print(f'  bridge_outbound count: {rows[0]}')
+
+    # Verifica anche che UPDATE approved=1 sia stato salvato
+    con = sqlite3.connect(str(dealer_db))
+    approved_val = con.execute("SELECT approved FROM pending_replies WHERE id='reply_b001'").fetchone()[0]
+    con.close()
+    print(f'  pending_replies.approved: {approved_val}')
+
+    ok = (
+        result.get('approved') is True
+        and result.get('bridge_queued') is False
+        and result.get('error') == 'schema_drift'
+        and rows[0] == 0
+        and approved_val == 1
+    )
+    print(f'  → {"PASS" if ok else "FAIL"}')
+    return ok
+
+
+def scenario_c_bridge_missing(tmpdir: Path) -> bool:
+    """C: BRIDGE_DB_PATH unset → approved=True, bridge_queued=False, error=bridge_db_path_missing"""
+    print('\n[SCENARIO C] BRIDGE_DB_PATH missing')
+    Path(tmpdir / 'c').mkdir(parents=True, exist_ok=True)
+    dealer_db, _ = make_fixtures(tmpdir / 'c')
+    seed_pending_reply(dealer_db, 'reply_c001', 'dealer_003', '+393283334444', 'test c')
+
+    db = fresh_db_module(dealer_db, bridge_db='')  # env unset
+    result = db.approve_reply('reply_c001')
+    print(f'  Result: {result}')
+
+    ok = (
+        result.get('approved') is True
+        and result.get('bridge_queued') is False
+        and result.get('error') == 'bridge_db_path_missing'
+    )
+    print(f'  → {"PASS" if ok else "FAIL"}')
+    return ok
+
+
+def scenario_d_duplicate(tmpdir: Path) -> bool:
+    """D: doppio approve → 1° OK, 2° approved=False, error=not_found_or_processed"""
+    print('\n[SCENARIO D] Duplicate approve (idempotency)')
+    Path(tmpdir / 'd').mkdir(parents=True, exist_ok=True)
+    dealer_db, bridge_db = make_fixtures(tmpdir / 'd')
+    seed_pending_reply(dealer_db, 'reply_d001', 'dealer_004', '+393285556666', 'test d')
+
+    db = fresh_db_module(dealer_db, str(bridge_db))
+
+    result1 = db.approve_reply('reply_d001')
+    print(f'  1st result: {result1}')
+
+    result2 = db.approve_reply('reply_d001')
+    print(f'  2nd result: {result2}')
+
+    con = sqlite3.connect(str(bridge_db))
+    bridge_count = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()[0]
+    con.close()
+    print(f'  bridge_outbound count: {bridge_count}')
+
+    ok = (
+        result1.get('approved') is True
+        and result1.get('bridge_queued') is True
+        and result2.get('approved') is False
+        and result2.get('error') == 'not_found_or_processed'
+        and bridge_count == 1  # niente doppio insert
+    )
+    print(f'  → {"PASS" if ok else "FAIL"}')
+    return ok
+
+
+def scenario_e_orphaned_reply(tmpdir: Path) -> bool:
+    """E: pending_reply senza conversations row (orphan) → error=phone_or_text_missing"""
+    print('\n[SCENARIO E] Orphaned reply (no conversations row)')
+    Path(tmpdir / 'e').mkdir(parents=True, exist_ok=True)
+    dealer_db, bridge_db = make_fixtures(tmpdir / 'e')
+    # SOLO pending_reply, NO conversations row (race INSERT in produzione)
+    seed_pending_reply(dealer_db, 'reply_e001', 'dealer_orphan', '+393287778888',
+                       'test orphan', register_conversation=False)
+
+    db = fresh_db_module(dealer_db, str(bridge_db))
+    result = db.approve_reply('reply_e001')
+    print(f'  Result: {result}')
+
+    con = sqlite3.connect(str(bridge_db))
+    bridge_count = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()[0]
+    con.close()
+    print(f'  bridge_outbound count: {bridge_count}')
+
+    # LEFT JOIN su conversations vuota → row.phone IS NULL → branch phone_or_text_missing
+    ok = (
+        result.get('approved') is True
+        and result.get('bridge_queued') is False
+        and result.get('error') == 'phone_or_text_missing'
+        and bridge_count == 0
+    )
+    print(f'  → {"PASS" if ok else "FAIL"}')
+    return ok
+
+
+def main():
+    print('=' * 70)
+    print('S196-P1 runtime test approve_reply (dealer_network + bridge fixtures)')
+    print('=' * 70)
+
+    tmpdir = Path(tempfile.mkdtemp(prefix='s196_runtime_'))
+    print(f'Fixtures dir: {tmpdir}')
+
+    results = {
+        'A_happy_path':     scenario_a_happy_path(tmpdir),
+        'B_schema_drift':   scenario_b_schema_drift(tmpdir),
+        'C_bridge_missing': scenario_c_bridge_missing(tmpdir),
+        'D_duplicate':      scenario_d_duplicate(tmpdir),
+        'E_orphaned_reply': scenario_e_orphaned_reply(tmpdir),
+    }
+
+    print('\n' + '=' * 70)
+    print('SUMMARY:')
+    for name, ok in results.items():
+        marker = 'PASS' if ok else 'FAIL'
+        print(f'  [{marker}] {name}')
+
+    passed = sum(1 for v in results.values() if v)
+    total = len(results)
+    print(f'\nRUNTIME TEST RESULT: {passed}/{total} {"PASS" if passed == total else "FAIL"}')
+    print('=' * 70)
+
+    # Cleanup
+    shutil.rmtree(tmpdir, ignore_errors=True)
+
+    sys.exit(0 if passed == total else 1)
+
+
+if __name__ == '__main__':
+    main()
diff --git a/wa-intelligence/dashboard/app.py b/wa-intelligence/dashboard/app.py
index 9f23cc1..042dbca 100644
--- a/wa-intelligence/dashboard/app.py
+++ b/wa-intelligence/dashboard/app.py
@@ -65,6 +65,69 @@ def _require_auth_api(request: Request):
     return None
 
 
+# S196-P2/P3: Telegram alert per silent-failure HITL e BRIDGE_DB_PATH missing
+def _send_telegram_alert(text: str) -> bool:
+    """Best-effort Telegram alert. Non blocca mai il chiamante.
+
+    Pattern allineato a wa-intelligence/response-analyzer.py:1738 (urllib stdlib).
+    Env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID. Se mancano → log warning + skip.
+    """
+    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
+    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
+    if not (token and chat_id):
+        log.warning(f'[TG-alert] skip (TELEGRAM_BOT_TOKEN/CHAT_ID missing): {text[:80]}')
+        return False
+    try:
+        import urllib.request
+        import urllib.parse
+        url = f'https://api.telegram.org/bot{token}/sendMessage'
+        data = urllib.parse.urlencode({
+            'chat_id': chat_id,
+            'text': f'[ARGOS-Dashboard] {text}',
+        }).encode('utf-8')
+        req = urllib.request.Request(url, data=data, method='POST')
+        with urllib.request.urlopen(req, timeout=5) as resp:
+            return resp.status == 200
+    except Exception as e:
+        # S196 code-review MED-1: NON loggare {e} raw — urllib exceptions
+        # possono includere l'URL completo con bot token embedded. Log solo
+        # tipo eccezione + testo del messaggio (no credenziali).
+        log.error(f'[TG-alert] failed: {type(e).__name__} — text={text[:80]}')
+        return False
+
+
+# ── Startup pre-flight (S196-P3) ─────────────────────────
+
+@app.on_event('startup')
+async def verify_bridge_db_path():
+    """Pre-flight check BRIDGE_DB_PATH per HITL approve_reply (S196-P3).
+
+    NON crasha l'app (operatore puo' usare dashboard read-only/audit).
+    Log + Telegram alert se path mancante o invalido. Path felice fix
+    S193-fix HIGH-2 dipende da questa env, silent-failure precedente
+    bloccava daemon senza segnalazione.
+    """
+    bp = os.environ.get('BRIDGE_DB_PATH', '')
+    if not bp:
+        msg = (
+            'BRIDGE_DB_PATH non impostato su processo argos-dashboard. '
+            'Reply HITL approvate non andranno in coda al daemon WA. '
+            'Fix: aggiungere env var in ecosystem.config.js + pm2 reload.'
+        )
+        log.error(f'[STARTUP][FATAL] {msg}')
+        _send_telegram_alert(msg)
+        return
+    if not os.path.exists(bp):
+        msg = (
+            f'BRIDGE_DB_PATH impostato ({bp}) ma file NON esiste. '
+            'Verificare path comm-broker/bridge.sqlite su iMac.'
+        )
+        log.error(f'[STARTUP][FATAL] {msg}')
+        _send_telegram_alert(msg)
+        return
+    log.info(f'[STARTUP] BRIDGE_DB_PATH OK: {bp}')
+
+
 # ── Auth Routes ──────────────────────────────────────────
 
 @app.get('/login', response_class=HTMLResponse)
@@ -690,10 +753,41 @@ async def action_approve_reply(request: Request):
     reply_id = body.get('reply_id')
     if not reply_id:
         return JSONResponse({'error': 'reply_id required'}, status_code=400)
-    ok = db.approve_reply(reply_id)  # reply_id e' TEXT PK (es. 'reply_abc12345')
-    if ok:
-        log.info(f'Reply {reply_id} approved from dashboard')
-    return {'ok': ok}
+
+    # S196-P2: db.approve_reply ora ritorna dict {approved, bridge_queued, error}
+    result = db.approve_reply(reply_id)  # reply_id e' TEXT PK (es. 'reply_abc12345')
+    approved = result.get('approved', False)
+    bridge_queued = result.get('bridge_queued', False)
+    error_code = result.get('error')
+
+    if approved and bridge_queued:
+        log.info(f'Reply {reply_id} approved + bridge queued')
+        ui_message = 'Inviato a daemon'
+        ui_level = 'success'
+    elif approved and not bridge_queued:
+        # Silent-failure precedente: ora alertiamo operatore (P2 fix)
+        log.error(
+            f'Reply {reply_id} approved BUT bridge NOT queued (error={error_code}) — daemon non riceve'
+        )
+        _send_telegram_alert(
+            f'HITL reply {reply_id} approvata ma bridge_outbound non in coda: {error_code}. '
+            f'Verificare BRIDGE_DB_PATH e schema DB. Daemon NON inviera\' fino a fix manuale.'
+        )
+        ui_message = f'Approvato ma daemon NON in coda ({error_code})'
+        ui_level = 'warning'
+    else:
+        log.warning(f'Reply {reply_id} approval failed: {error_code}')
+        ui_message = f'Reply non trovata o gia\' processata ({error_code})'
+        ui_level = 'error'
+
+    return {
+        'ok': approved,
+        'approved': approved,
+        'bridge_queued': bridge_queued,
+        'error': error_code,
+        'message': ui_message,
+        'level': ui_level,
+    }
 
 
 @app.post('/api/actions/skip-reply')
diff --git a/wa-intelligence/dashboard/db.py b/wa-intelligence/dashboard/db.py
index 596c1e5..2666c2a 100644
--- a/wa-intelligence/dashboard/db.py
+++ b/wa-intelligence/dashboard/db.py
@@ -230,14 +230,38 @@ def get_llm_cost_total() -> dict:
 
 # ── Action Queries (F5) ────────────────────────────────
 
-def approve_reply(reply_id: str) -> bool:
+def approve_reply(reply_id: str) -> dict:
     """Approva una pending_reply e inserisce in bridge_outbound per invio daemon.
 
+    S196-P2: signature dict per propagare stato bridge_outbound a caller (app.py).
+    Risolve silent-failure return True senza INSERT bridge (schema drift, env mancante,
+    insert exception) che bloccava il daemon senza segnalarlo all'operatore.
+
     S192: reply_id e' TEXT PK (es. 'reply_abc12345'), non int.
-    Dopo UPDATE approved=1, tenta INSERT bridge_outbound via BRIDGE_DB_PATH.
-    Degrada gracefully se BRIDGE_DB_PATH non e' impostato (UPDATE resta valido,
-    ma il daemon non ricevera' il messaggio finche' non aggiornato manualmente).
+
+    Returns:
+        {
+          "approved": bool,           # True se UPDATE pending_replies ha avuto effetto
+          "bridge_queued": bool,      # True se INSERT bridge_outbound OK (riga nuova)
+          "error": Optional[str],     # codice strutturato (None se path felice)
+        }
+
+    Error codes (caller interpretation):
+        None                       — happy path completo (approved + bridge_queued)
+        "not_found_or_processed"   — reply non trovata o gia' approvata
+        "schema_drift"             — sqlite3.OperationalError su SELECT pending_replies
+        "bridge_db_path_missing"   — env var BRIDGE_DB_PATH non impostata
+        "bridge_duplicate"         — riga gia' in bridge_outbound (INSERT OR IGNORE rowcount=0)
+        "bridge_insert_failed"     — eccezione su INSERT bridge_outbound
+        "phone_or_text_missing"    — phone o reply_text vuoti — bridge skip
+
+    Trade-off: cambia signature pubblica (era bool). Path felice S193-fix HIGH-2
+    dipende da env var non verificata — degradazione silenziosa e' bug peggiore
+    di breaking change su un solo callsite (app.py action_approve_reply).
     """
+    import logging as _log
+    _logger = _log.getLogger(__name__)
+
     con = _connect()
     try:
         cur = con.execute(
@@ -245,7 +269,7 @@ def approve_reply(reply_id: str) -> bool:
             (reply_id,)
         )
         if cur.rowcount == 0:
-            return False
+            return {"approved": False, "bridge_queued": False, "error": "not_found_or_processed"}
 
         # S193-fix HIGH-2: rimosso LEFT JOIN dealers (tabella inesistente in dealer_network.sqlite)
         # Schema dump iMac 2026-05-26 conferma: solo conversations ha phone_number (PK dealer_id 1:1).
@@ -261,14 +285,13 @@ def approve_reply(reply_id: str) -> bool:
                 (reply_id,)
             ).fetchone()
         except sqlite3.OperationalError as schema_err:
-            import logging as _log
-            _log.getLogger(__name__).error(
+            _logger.error(
                 f'[HITL][approve_reply] schema drift SELECT fallita per {reply_id}: {schema_err} '
                 f'— UPDATE approved=1 gia\' committato, bridge_outbound NON inserito'
             )
-            # UPDATE gia' rowcount=1, ritorniamo True ma daemon non ricevera' (richiede intervento manuale)
+            # UPDATE gia' rowcount=1: approved=True, bridge_queued=False, errore strutturato
             con.commit()
-            return True
+            return {"approved": True, "bridge_queued": False, "error": "schema_drift"}
 
         dealer_id = dict(row)['dealer_id'] if row else None
         _audit(con, 'REPLY_APPROVED', dealer_id, {'reply_id': reply_id})
@@ -276,59 +299,65 @@ def approve_reply(reply_id: str) -> bool:
 
         # INSERT bridge_outbound — single-writer pattern (S173)
         bridge_db_path = os.environ.get('BRIDGE_DB_PATH', '')
-        if bridge_db_path and row:
-            r = dict(row)
-            phone = (r.get('phone') or '').replace('+', '').replace(' ', '').replace('-', '')
-            reply_text = r.get('reply_text') or ''
-            current_step = r.get('current_step') or 'RESPONSE_RECEIVED'
-            if phone and reply_text:
-                try:
-                    import sqlite3 as _sqlite3
-                    b_con = _sqlite3.connect(bridge_db_path, timeout=10)
-                    b_con.execute('PRAGMA journal_mode=WAL')
-                    b_con.execute('PRAGMA busy_timeout=10000')
-                    b_res = b_con.execute(
-                        """INSERT OR IGNORE INTO bridge_outbound
-                               (deal_id, target_role, target_phone, template_phase, template_lang,
-                                body, state_at_send, created_ts, approved_ts)
-                           VALUES (?, 'dealer', ?, 'response', 'it', ?, ?, strftime('%s','now'), strftime('%s','now'))""",
-                        (reply_id, phone, reply_text, current_step)
-                    )
-                    b_con.commit()
-                    bridge_inserted = b_res.rowcount == 1
-                    b_con.close()
-                    if bridge_inserted:
-                        # Audit separato bridge insert
-                        # S193-fix LOW-2: phone masking corretto — nasconde ultime 4 cifre
-                        _audit(con, 'BRIDGE_INSERTED', dealer_id,
-                               {'reply_id': reply_id, 'phone': phone[:-4] + '****' if len(phone) > 4 else '****'})
-                        con.commit()
-                        import logging as _log
-                        _log.getLogger(__name__).info(
-                            f'[HITL][bridge] reply {reply_id} → bridge_outbound queued'
-                        )
-                    else:
-                        import logging as _log
-                        _log.getLogger(__name__).warning(
-                            f'[HITL][bridge][dedup] reply {reply_id} gia\' in bridge_outbound — skip'
-                        )
-                except Exception as b_err:
-                    import logging as _log
-                    _log.getLogger(__name__).error(
-                        f'[HITL][bridge] INSERT fallito per {reply_id}: {b_err} — approvazione gia\' salvata'
-                    )
-            else:
-                import logging as _log
-                _log.getLogger(__name__).warning(
-                    f'[HITL][bridge] reply {reply_id}: phone o reply_text mancante — bridge skip'
-                )
-        elif not bridge_db_path:
-            import logging as _log
-            _log.getLogger(__name__).warning(
+        if not bridge_db_path:
+            _logger.warning(
                 f'[HITL][bridge] BRIDGE_DB_PATH non impostato — reply {reply_id} approvata ma NON in coda daemon'
             )
+            return {"approved": True, "bridge_queued": False, "error": "bridge_db_path_missing"}
+
+        if not row:
+            # row None solo se pending_replies non aveva pr.dealer_id risolvibile
+            _logger.warning(
+                f'[HITL][bridge] reply {reply_id}: SELECT post-UPDATE ha ritornato NULL — bridge skip'
+            )
+            return {"approved": True, "bridge_queued": False, "error": "phone_or_text_missing"}
+
+        r = dict(row)
+        phone = (r.get('phone') or '').replace('+', '').replace(' ', '').replace('-', '')
+        reply_text = r.get('reply_text') or ''
+        current_step = r.get('current_step') or 'RESPONSE_RECEIVED'
+
+        if not (phone and reply_text):
+            _logger.warning(
+                f'[HITL][bridge] reply {reply_id}: phone o reply_text mancante — bridge skip'
+            )
+            return {"approved": True, "bridge_queued": False, "error": "phone_or_text_missing"}
+
+        try:
+            import sqlite3 as _sqlite3
+            b_con = _sqlite3.connect(bridge_db_path, timeout=10)
+            b_con.execute('PRAGMA journal_mode=WAL')
+            b_con.execute('PRAGMA busy_timeout=10000')
+            b_res = b_con.execute(
+                """INSERT OR IGNORE INTO bridge_outbound
+                       (deal_id, target_role, target_phone, template_phase, template_lang,
+                        body, state_at_send, created_ts, approved_ts)
+                   VALUES (?, 'dealer', ?, 'response', 'it', ?, ?, strftime('%s','now'), strftime('%s','now'))""",
+                (reply_id, phone, reply_text, current_step)
+            )
+            b_con.commit()
+            bridge_inserted = b_res.rowcount == 1
+            b_con.close()
+        except Exception as b_err:
+            _logger.error(
+                f'[HITL][bridge] INSERT fallito per {reply_id}: {b_err} — approvazione gia\' salvata'
+            )
+            return {"approved": True, "bridge_queued": False, "error": "bridge_insert_failed"}
+
+        if not bridge_inserted:
+            _logger.warning(
+                f'[HITL][bridge][dedup] reply {reply_id} gia\' in bridge_outbound — skip'
+            )
+            return {"approved": True, "bridge_queued": False, "error": "bridge_duplicate"}
+
+        # Audit separato bridge insert
+        # S193-fix LOW-2: phone masking corretto — nasconde ultime 4 cifre
+        _audit(con, 'BRIDGE_INSERTED', dealer_id,
+               {'reply_id': reply_id, 'phone': phone[:-4] + '****' if len(phone) > 4 else '****'})
+        con.commit()
+        _logger.info(f'[HITL][bridge] reply {reply_id} → bridge_outbound queued')
 
-        return True
+        return {"approved": True, "bridge_queued": True, "error": None}
     finally:
         con.close()
 
diff --git a/wa-intelligence/ecosystem.config.js b/wa-intelligence/ecosystem.config.js
index c00469a..d7f850f 100644
--- a/wa-intelligence/ecosystem.config.js
+++ b/wa-intelligence/ecosystem.config.js
@@ -13,6 +13,7 @@
  *   1. argos-wa-daemon    — WA listener persistente (Node.js)
  *   2. argos-tg-bot       — Telegram human-in-loop (Python)
  *   3. argos-cf-monitor   — Cloudflare alerts → Telegram push (Python, S153)
+ *   4. argos-dashboard    — FastAPI HITL dashboard :8080 (Python, S189/S196)
  */
 
 'use strict';
@@ -144,5 +145,35 @@ module.exports = {
                 ...SHARED_ENV,
             },
         },
+
+        // ── 4. Dashboard FastAPI HITL (S189/S196-P3) ─────────
+        // Prima di S196 era avviato manualmente fuori ecosystem → BRIDGE_DB_PATH
+        // mancante → silent-failure approve_reply (UPDATE OK ma INSERT bridge skip).
+        // Ora eredita SHARED_ENV (BRIDGE_DB_PATH + ARGOS_DB_PATH + Telegram).
+        {
+            name:             'argos-dashboard',
+            script:           path.join(INTEL, 'run_dashboard.py'),
+            cwd:              INTEL,
+            interpreter:      'python3',
+
+            autorestart:      true,
+            watch:            false,
+            max_restarts:     20,
+            min_uptime:       '30s',
+            restart_delay:    5000,
+
+            max_memory_restart: '256M',
+
+            log_file:         '/tmp/argos-dashboard-combined.log',
+            out_file:         '/tmp/argos-dashboard-out.log',
+            error_file:       '/tmp/argos-dashboard-err.log',
+            log_date_format:  'DD/MM/YYYY HH:mm:ss',
+            merge_logs:       true,
+
+            env: {
+                ...SHARED_ENV,
+                ARGOS_DASHBOARD_PASSWORD: dotEnv.ARGOS_DASHBOARD_PASSWORD || '',
+            },
+        },
     ],
 };

```

---

## Auto-valutazione CTO interna

**Caveat trasparente**: py_compile + code-reviewer LLM NON sono validation gate; **runtime test 5/5 PASS** lo è. Self-score sotto basato su gate cumulato + delegation effettiva + critica strutturale post-review.

| Asse | Score | Note |
|------|-------|------|
| Correctness | 8/10 | 5/5 runtime test PASS con SELECT reale bridge_outbound. Path felice + 4 path errore coperti. -2 per MED-2 audit-loss documentato. |
| Security | 7/10 | MED-1 token in URL log fixed inline. -3 per ecosystem.config.js che embeddа dotEnv direttamente in env block (acceptable: pattern preesistente). |
| Idempotency | 9/10 | UPDATE `approved IS NULL` + UNIQUE INDEX bridge_outbound → doppio approve = no-op verificato in scenario D. -1 per assunzione single-operator non documentata (60gg risk). |
| Test coverage | 8/10 | 5/5 scenari fixture schema reale. -2 per: no test concurrency multi-operator (SQLite WAL serializza writers ma race window 267-271 non testata), no test bridge.sqlite UNIQUE constraint reject. |
| Big Sur compat | 10/10 | urllib stdlib + sqlite3 stdlib + importlib stdlib. Niente match/case, niente API macOS 12+. |
| Delegation | 9/10 | code-reviewer agent invocato come da CLAUDE.md #0. -1 per zero invocation Task tool nelle prime 2 sessioni (S194/S195) sullo stesso scope. |

**Self-score complessivo**: **8.5/10** (range 7-9).

**Gate atteso revisore esterno**: ≥7.0/10 per sblocco STEP 6.

---

## Critica strutturale 4 punti (CLAUDE.md #4)

1. **Assunzione single-operator non documentata** — se in futuro 2 operatori usano dashboard contemporaneamente, race window tra UPDATE rowcount=1 e INSERT bridge_outbound non protetta. SQLite WAL serializza ma non garantisce ordine. **Mitigation**: documentare in db.py + se serve, BEGIN IMMEDIATE.

2. **BRIDGE_DB_PATH drift a 90gg** — se path bridge.sqlite cambia (rinomina/migrazione), startup check logga FATAL ma NON aggiorna ecosystem.config.js. Operatore deve fixare manualmente + `pm2 reload`. **Mitigation**: BACKLOG ARGOS healthcheck periodico tipo `infra-monitor`.

3. **Pattern errore noto applicato S196** — runtime test come unico gate self-score è scaffold S189 (HITL smoke 3/3) generalizzato. Funziona PERCHÉ usa fixture schema reale dump produzione. Se schema iMac drifta, fixture S196 diventa stale silently. **Mitigation**: BACKLOG #S196-3 auto-dump schema iMac → fixture.

4. **Dove sovradimensiono**: scenario E orphaned reply — path raggiungibile solo via race INSERT pending_reply prima di conversations. In produzione non è mai successo (no log evidence). Aggiunto comunque su LOW-2 reviewer per portare 4/5→5/5. Coverage extra vs ROI: marginalmente positivo (hardening difensivo) ma non strettamente necessario.

---

## Files cambiati (commit db311b7)

```
 BACKLOG.md                                |  21 ++
 src/cove/image_sanitizer.py               |  16 +-
 tools/scripts/pdf_generator_enterprise.py |  14 +-
 tools/tests/test_approve_reply_runtime.py | 373 ++++++++++++++++++++++++++++++
 wa-intelligence/dashboard/app.py          | 102 +++++++-
 wa-intelligence/dashboard/db.py           | 147 +++++++-----
 wa-intelligence/ecosystem.config.js       |  31 +++
 7 files changed, 633 insertions(+), 71 deletions(-)
```

---

## Cosa ti chiedo (revisore esterno claude.ai web)

Verdict JSON strutturato:

```json
{
  "external_score": <float 0-10>,
  "go_no_go": "GO" | "GO_WITH_PRECONDITIONS" | "NO_GO",
  "fix_status": {
    "P1_runtime_test": "PASS" | "PARTIAL" | "FAIL",
    "P2_signature_dict": "PASS" | "PARTIAL" | "FAIL",
    "P3_bridge_env": "PASS" | "PARTIAL" | "FAIL",
    "P4_sentinel_const": "PASS" | "PARTIAL" | "FAIL"
  },
  "red_flags": [<lista diff-grounded, ogni item con file:line + descrizione>],
  "preconditions_if_any": [<lista>],
  "rationale_score": "<1-3 frasi>"
}
```

Gate per sblocco STEP 6: `external_score ≥ 7.0/10` AND `go_no_go in ("GO", "GO_WITH_PRECONDITIONS")`.

Se NO_GO o score < 7.0 → handoff S197 con preconditions.

---

## STEP 6 sbloccato da gate VERDE

1. Deploy iMac (rsync atomico + symlink swap)
2. SSH iMac `pm2 reload ecosystem.config.js` (test che argos-dashboard riparte con BRIDGE_DB_PATH ereditato)
3. 5 scenari AMBRA stress (response-analyzer reactive)
4. 9-step E2E TEST_FOUNDER fisico Luke (approve+reject)
5. Matrix decisione Day 1 Stile Car 2026-06-03
