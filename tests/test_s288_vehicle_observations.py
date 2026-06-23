#!/usr/bin/env python3
"""
tests/test_s288_vehicle_observations.py — S288 metrica-tempo OSSERVATA.

Gate codice (no rete, sqlite IN-MEMORY) per snapshot_observations: la prova del diff
GONE NON doctora data/dealers.db (CORREZIONE #3), gira tutta su :memory:.

FALSIFICATORI (devono FALLIRE se la logica viene degradata):
  - GONE senza delete: se snapshot cancellasse la riga assente invece di status='GONE'
    -> test_gone_marks_not_deletes (assert riga ancora presente + status GONE).
  - first_observed_at stabile: se il re-osservare riscrivesse first_observed_at
    -> test_reobserve_keeps_first (assert first INVARIATO, last avanzato).
  - guardia run parziale (CORR #2): se il diff GONE girasse a run incompleto
    -> test_partial_run_no_gone (assert status resta PRESENT).

Run: python3 tests/test_s288_vehicle_observations.py   (oppure pytest)
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.dealer_collector import init_db, snapshot_observations  # noqa: E402

DEALER = "rossettomotors-srl"


def _mem_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def _status(conn, vk):
    row = conn.execute(
        "SELECT status FROM vehicle_observations WHERE dealer_id=? AND vehicle_key=?",
        (DEALER, vk),
    ).fetchone()
    return row[0] if row else None


def test_gone_marks_not_deletes():
    """RUN1 {A,B} PRESENT; RUN2 completo {A} -> B GONE, riga B NON cancellata."""
    conn = _mem_conn()
    snapshot_observations(conn, DEALER, ["A", "B"], "2026-06-23T10:00:00+00:00", run_complete=True)
    assert _status(conn, "A") == "PRESENT"
    assert _status(conn, "B") == "PRESENT"

    res = snapshot_observations(conn, DEALER, ["A"], "2026-06-24T10:00:00+00:00", run_complete=True)
    assert res["gone"] == 1, res
    assert _status(conn, "B") == "GONE", "B doveva passare a GONE"
    # NO delete: la riga B esiste ancora (la prova del non-delete)
    cnt = conn.execute(
        "SELECT count(*) FROM vehicle_observations WHERE dealer_id=? AND vehicle_key='B'",
        (DEALER,),
    ).fetchone()[0]
    assert cnt == 1, "riga B cancellata: violato 'no delete'"
    conn.close()


def test_reobserve_keeps_first():
    """Ri-osservare A mantiene first_observed_at, avanza last_observed_at."""
    conn = _mem_conn()
    snapshot_observations(conn, DEALER, ["A"], "2026-06-23T10:00:00+00:00", run_complete=True)
    first1 = conn.execute(
        "SELECT first_observed_at, last_observed_at FROM vehicle_observations "
        "WHERE dealer_id=? AND vehicle_key='A'", (DEALER,)).fetchone()

    res = snapshot_observations(conn, DEALER, ["A"], "2026-06-25T10:00:00+00:00", run_complete=True)
    assert res["updated"] == 1 and res["inserted"] == 0, res
    first2 = conn.execute(
        "SELECT first_observed_at, last_observed_at FROM vehicle_observations "
        "WHERE dealer_id=? AND vehicle_key='A'", (DEALER,)).fetchone()
    assert first2[0] == first1[0], "first_observed_at NON deve cambiare"
    assert first2[1] == "2026-06-25T10:00:00+00:00", "last_observed_at deve avanzare"
    conn.close()


def test_partial_run_no_gone():
    """RUN2 INCOMPLETO senza A -> A resta PRESENT (guardia CORR #2), 0 GONE."""
    conn = _mem_conn()
    snapshot_observations(conn, DEALER, ["A", "B"], "2026-06-23T10:00:00+00:00", run_complete=True)
    res = snapshot_observations(conn, DEALER, ["B"], "2026-06-24T10:00:00+00:00", run_complete=False)
    assert res["gone"] == 0 and res["diff_ran"] is False, res
    assert _status(conn, "A") == "PRESENT", "run parziale NON deve marcare GONE"
    conn.close()


def test_idempotent_same_instant():
    """Stesso run due volte (stesso istante) -> 0 nuovi insert, 0 duplicati."""
    conn = _mem_conn()
    snapshot_observations(conn, DEALER, ["A", "B"], "2026-06-23T10:00:00+00:00", run_complete=True)
    res = snapshot_observations(conn, DEALER, ["A", "B"], "2026-06-23T10:00:00+00:00", run_complete=True)
    assert res["inserted"] == 0 and res["gone"] == 0, res
    cnt = conn.execute(
        "SELECT count(*) FROM vehicle_observations WHERE dealer_id=?", (DEALER,)
    ).fetchone()[0]
    assert cnt == 2, "PK composta deve impedire duplicati"
    conn.close()


if __name__ == "__main__":
    tests = [
        test_gone_marks_not_deletes,
        test_reobserve_keeps_first,
        test_partial_run_no_gone,
        test_idempotent_same_instant,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} PASS")
    sys.exit(1 if failed else 0)
