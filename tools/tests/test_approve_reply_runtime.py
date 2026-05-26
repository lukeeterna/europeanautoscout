#!/usr/bin/env python3
"""
test_approve_reply_runtime.py — S196-P1 runtime functional test (CORE)

S195 NO_GO root cause: tutti i fix S193 validati solo py_compile + code-reviewer LLM.
Nessun test runtime con DB reale → silent-failure approve_reply non rilevato.

S196 fix: runtime test con SQLite fixtures schema identico a produzione iMac
(dealer_network.sqlite + comm-broker/bridge.sqlite). NO mock, NO stub, NO subprocess.

5 scenari:
  A. happy path        → approved=True, bridge_queued=True, error=None
  B. schema drift      → approved=True, bridge_queued=False, error="schema_drift"
  C. BRIDGE_DB_PATH    → approved=True, bridge_queued=False, error="bridge_db_path_missing"
  D. duplicate         → 1st approve OK, 2nd approve approved=False, error="not_found_or_processed"
  E. orphaned reply    → pending_reply senza conversations row → error="phone_or_text_missing"
                          (path raggiungibile in produzione se INSERT race)

Esecuzione:
  cd /Users/macbook/Documents/combaretrovamiauto-enterprise
  python3 tools/tests/test_approve_reply_runtime.py

Output gate: "RUNTIME TEST RESULT: 4/4 PASS" → STEP 4 VERDE.
"""

import os
import sys
import tempfile
import sqlite3
import shutil
import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# Schemi REALI iMac (ssh + sqlite3 .schema su 2026-05-26 produzione)
SCHEMA_PENDING_REPLIES = """
CREATE TABLE pending_replies (
    id              TEXT PRIMARY KEY,
    dealer_id       TEXT,
    dealer_name     TEXT,
    inbound_msg_id  TEXT,
    reply_text      TEXT,
    reply_label     TEXT,
    cialdini_trigger TEXT,
    approved        INTEGER DEFAULT NULL,
    sent            INTEGER DEFAULT 0,
    scheduled_at    TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    msg_checksum    TEXT
);
"""

SCHEMA_CONVERSATIONS = """
CREATE TABLE conversations (
    dealer_id       TEXT PRIMARY KEY,
    dealer_name     TEXT,
    city            TEXT,
    phone_number    TEXT,
    stock_size      INTEGER,
    persona_type    TEXT,
    score           REAL,
    source          TEXT,
    notes           TEXT,
    current_step    TEXT DEFAULT 'PENDING',
    day1_message    TEXT,
    recommendation  TEXT DEFAULT 'PENDING',
    created_at      TEXT DEFAULT (datetime('now')),
    last_contact_at TEXT,
    analyzed_at     TEXT,
    conversation_state TEXT DEFAULT 'COLD',
    outbound_count INTEGER DEFAULT 0,
    inbound_count INTEGER DEFAULT 0,
    last_inbound_at TEXT,
    state_updated_at TEXT,
    escalation_flag INTEGER DEFAULT 0,
    is_active_partner INTEGER DEFAULT 0,
    partner_since TEXT,
    total_transactions INTEGER DEFAULT 0,
    total_revenue_dealer REAL DEFAULT 0,
    last_analytics_sent TEXT,
    trusted_partner_sent INTEGER DEFAULT 0,
    opt_out INTEGER DEFAULT 0,
    opt_out_at TIMESTAMP,
    opt_out_source TEXT,
    opt_out_raw_message TEXT,
    handoff_source TEXT DEFAULT 'cold',
    is_micro_dealer INTEGER DEFAULT 0
);
"""

SCHEMA_AUDIT_LOG = """
CREATE TABLE audit_log (
    id              TEXT PRIMARY KEY,
    event_type      TEXT,
    dealer_id       TEXT,
    payload         TEXT,
    timestamp_it    TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

SCHEMA_BRIDGE_OUTBOUND = """
CREATE TABLE bridge_outbound (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id        TEXT NOT NULL,
    target_role    TEXT NOT NULL CHECK(target_role IN ('dealer', 'seller')),
    target_phone   TEXT NOT NULL,
    template_phase TEXT NOT NULL,
    template_lang  TEXT NOT NULL,
    body           TEXT NOT NULL,
    state_at_send  TEXT NOT NULL,
    created_ts     INTEGER NOT NULL,
    approved_ts    INTEGER,
    sent_ts        INTEGER,
    sent_status    TEXT,
    wa_msg_id      TEXT,
    processing_ts  INTEGER,
    attempt_count  INTEGER DEFAULT 0
);
CREATE UNIQUE INDEX uq_outbound_deal_phone_phase
    ON bridge_outbound(deal_id, target_phone, template_phase)
    WHERE sent_ts IS NULL;
"""


def make_fixtures(tmpdir: Path) -> tuple[Path, Path]:
    """Crea dealer_network.sqlite + bridge.sqlite vuoti con schema reale."""
    tmpdir.mkdir(parents=True, exist_ok=True)
    dealer_db = tmpdir / 'dealer_network.sqlite'
    bridge_db = tmpdir / 'bridge.sqlite'

    con = sqlite3.connect(str(dealer_db))
    con.executescript(SCHEMA_PENDING_REPLIES + SCHEMA_CONVERSATIONS + SCHEMA_AUDIT_LOG)
    con.commit()
    con.close()

    con = sqlite3.connect(str(bridge_db))
    con.executescript(SCHEMA_BRIDGE_OUTBOUND)
    con.commit()
    con.close()

    return dealer_db, bridge_db


def seed_pending_reply(dealer_db: Path, reply_id: str, dealer_id: str,
                       phone: str, reply_text: str, register_conversation: bool = True):
    """Inserisci una pending_reply + (opz.) conversation con phone."""
    con = sqlite3.connect(str(dealer_db))
    if register_conversation:
        con.execute(
            "INSERT INTO conversations (dealer_id, dealer_name, phone_number, current_step) "
            "VALUES (?, ?, ?, ?)",
            (dealer_id, 'Test Dealer', phone, 'RESPONSE_RECEIVED')
        )
    con.execute(
        "INSERT INTO pending_replies (id, dealer_id, dealer_name, reply_text, approved) "
        "VALUES (?, ?, ?, ?, NULL)",
        (reply_id, dealer_id, 'Test Dealer', reply_text)
    )
    con.commit()
    con.close()


def fresh_db_module(dealer_db: Path, bridge_db: str = ''):
    """Re-import db.py con env override (DB_PATH letto a module-level).

    code-review LOW-1: tutti gli scenari DEVONO usare questo helper, NON
    `from wa-intelligence.dashboard import db`. Il modulo legge DB_PATH a
    module-level — un import standard congelerebbe il path al primo env.
    """
    os.environ['ARGOS_DB_PATH'] = str(dealer_db)
    if bridge_db:
        os.environ['BRIDGE_DB_PATH'] = bridge_db
    else:
        os.environ.pop('BRIDGE_DB_PATH', None)
    # forza reimport
    mod_name = 'wa-intelligence.dashboard.db'
    # path import workaround per il dash nel nome cartella
    import importlib.util
    db_path = PROJECT_ROOT / 'wa-intelligence' / 'dashboard' / 'db.py'
    spec = importlib.util.spec_from_file_location('argos_dashboard_db', str(db_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenario_a_happy_path(tmpdir: Path) -> bool:
    """A: happy path → approved=True, bridge_queued=True, error=None"""
    print('\n[SCENARIO A] Happy path')
    dealer_db, bridge_db = make_fixtures(tmpdir / 'a')
    seed_pending_reply(dealer_db, 'reply_a001', 'dealer_001', '+393281234567',
                       'Ciao Mario, ho un BMW X3 2021 a 18000.')
    db = fresh_db_module(dealer_db, str(bridge_db))
    result = db.approve_reply('reply_a001')
    print(f'  Result: {result}')

    # Verifica bridge_outbound reale
    con = sqlite3.connect(str(bridge_db))
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT deal_id, target_phone, body FROM bridge_outbound").fetchall()
    con.close()
    print(f'  bridge_outbound rows: {[dict(r) for r in rows]}')

    ok = (
        result.get('approved') is True
        and result.get('bridge_queued') is True
        and result.get('error') is None
        and len(rows) == 1
        and rows[0]['deal_id'] == 'reply_a001'
        and rows[0]['target_phone'] == '393281234567'  # normalizzato (no +)
        and 'BMW X3' in rows[0]['body']
    )
    print(f'  → {"PASS" if ok else "FAIL"}')
    return ok


def scenario_b_schema_drift(tmpdir: Path) -> bool:
    """B: schema drift → approved=True, bridge_queued=False, error=schema_drift"""
    print('\n[SCENARIO B] Schema drift (conversations.phone_number rinominata)')
    Path(tmpdir / 'b').mkdir(parents=True, exist_ok=True)
    dealer_db, bridge_db = make_fixtures(tmpdir / 'b')
    seed_pending_reply(dealer_db, 'reply_b001', 'dealer_002', '+393281112222', 'test b')

    # Schema drift: rinomina phone_number
    con = sqlite3.connect(str(dealer_db))
    con.execute("ALTER TABLE conversations RENAME COLUMN phone_number TO phone_num_old")
    con.commit()
    con.close()

    db = fresh_db_module(dealer_db, str(bridge_db))
    result = db.approve_reply('reply_b001')
    print(f'  Result: {result}')

    con = sqlite3.connect(str(bridge_db))
    rows = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()
    con.close()
    print(f'  bridge_outbound count: {rows[0]}')

    # Verifica anche che UPDATE approved=1 sia stato salvato
    con = sqlite3.connect(str(dealer_db))
    approved_val = con.execute("SELECT approved FROM pending_replies WHERE id='reply_b001'").fetchone()[0]
    con.close()
    print(f'  pending_replies.approved: {approved_val}')

    ok = (
        result.get('approved') is True
        and result.get('bridge_queued') is False
        and result.get('error') == 'schema_drift'
        and rows[0] == 0
        and approved_val == 1
    )
    print(f'  → {"PASS" if ok else "FAIL"}')
    return ok


def scenario_c_bridge_missing(tmpdir: Path) -> bool:
    """C: BRIDGE_DB_PATH unset → approved=True, bridge_queued=False, error=bridge_db_path_missing"""
    print('\n[SCENARIO C] BRIDGE_DB_PATH missing')
    Path(tmpdir / 'c').mkdir(parents=True, exist_ok=True)
    dealer_db, _ = make_fixtures(tmpdir / 'c')
    seed_pending_reply(dealer_db, 'reply_c001', 'dealer_003', '+393283334444', 'test c')

    db = fresh_db_module(dealer_db, bridge_db='')  # env unset
    result = db.approve_reply('reply_c001')
    print(f'  Result: {result}')

    ok = (
        result.get('approved') is True
        and result.get('bridge_queued') is False
        and result.get('error') == 'bridge_db_path_missing'
    )
    print(f'  → {"PASS" if ok else "FAIL"}')
    return ok


def scenario_d_duplicate(tmpdir: Path) -> bool:
    """D: doppio approve → 1° OK, 2° approved=False, error=not_found_or_processed"""
    print('\n[SCENARIO D] Duplicate approve (idempotency)')
    Path(tmpdir / 'd').mkdir(parents=True, exist_ok=True)
    dealer_db, bridge_db = make_fixtures(tmpdir / 'd')
    seed_pending_reply(dealer_db, 'reply_d001', 'dealer_004', '+393285556666', 'test d')

    db = fresh_db_module(dealer_db, str(bridge_db))

    result1 = db.approve_reply('reply_d001')
    print(f'  1st result: {result1}')

    result2 = db.approve_reply('reply_d001')
    print(f'  2nd result: {result2}')

    con = sqlite3.connect(str(bridge_db))
    bridge_count = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()[0]
    con.close()
    print(f'  bridge_outbound count: {bridge_count}')

    ok = (
        result1.get('approved') is True
        and result1.get('bridge_queued') is True
        and result2.get('approved') is False
        and result2.get('error') == 'not_found_or_processed'
        and bridge_count == 1  # niente doppio insert
    )
    print(f'  → {"PASS" if ok else "FAIL"}')
    return ok


def scenario_e_orphaned_reply(tmpdir: Path) -> bool:
    """E: pending_reply senza conversations row (orphan) → error=phone_or_text_missing"""
    print('\n[SCENARIO E] Orphaned reply (no conversations row)')
    Path(tmpdir / 'e').mkdir(parents=True, exist_ok=True)
    dealer_db, bridge_db = make_fixtures(tmpdir / 'e')
    # SOLO pending_reply, NO conversations row (race INSERT in produzione)
    seed_pending_reply(dealer_db, 'reply_e001', 'dealer_orphan', '+393287778888',
                       'test orphan', register_conversation=False)

    db = fresh_db_module(dealer_db, str(bridge_db))
    result = db.approve_reply('reply_e001')
    print(f'  Result: {result}')

    con = sqlite3.connect(str(bridge_db))
    bridge_count = con.execute("SELECT COUNT(*) FROM bridge_outbound").fetchone()[0]
    con.close()
    print(f'  bridge_outbound count: {bridge_count}')

    # LEFT JOIN su conversations vuota → row.phone IS NULL → branch phone_or_text_missing
    ok = (
        result.get('approved') is True
        and result.get('bridge_queued') is False
        and result.get('error') == 'phone_or_text_missing'
        and bridge_count == 0
    )
    print(f'  → {"PASS" if ok else "FAIL"}')
    return ok


def main():
    print('=' * 70)
    print('S196-P1 runtime test approve_reply (dealer_network + bridge fixtures)')
    print('=' * 70)

    tmpdir = Path(tempfile.mkdtemp(prefix='s196_runtime_'))
    print(f'Fixtures dir: {tmpdir}')

    results = {
        'A_happy_path':     scenario_a_happy_path(tmpdir),
        'B_schema_drift':   scenario_b_schema_drift(tmpdir),
        'C_bridge_missing': scenario_c_bridge_missing(tmpdir),
        'D_duplicate':      scenario_d_duplicate(tmpdir),
        'E_orphaned_reply': scenario_e_orphaned_reply(tmpdir),
    }

    print('\n' + '=' * 70)
    print('SUMMARY:')
    for name, ok in results.items():
        marker = 'PASS' if ok else 'FAIL'
        print(f'  [{marker}] {name}')

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f'\nRUNTIME TEST RESULT: {passed}/{total} {"PASS" if passed == total else "FAIL"}')
    print('=' * 70)

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)

    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
