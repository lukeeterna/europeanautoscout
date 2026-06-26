"""
ig_collector.py -- PARTE B2: collector Instagram (web_profile_info).

Costruito SOLO perche' B1 (ig_probe.py) ha dato >=3/5 a 200 da questa macchina.
Persiste bio / link-in-bio / categoria / follower / recency in
dealer_operational_profile. Stessa degradazione + idempotenza di PARTE A.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import connect, recompute_sources_ok  # noqa: E402
from ig_probe import probe_one  # noqa: E402


def collect_ig(handle: str) -> dict:
    """Riusa probe_one (read-only) e normalizza in campi persistibili."""
    r = probe_one(handle)
    out = {
        "ig_handle": r["handle"], "ig_bio": None, "ig_external_url": None,
        "ig_category": None, "ig_followers": None, "ig_last_post_ts": None,
        "ig_source": "error",
    }
    if r.get("status") == 200:
        out["ig_bio"] = r.get("bio")
        out["ig_external_url"] = r.get("external_url")
        out["ig_category"] = r.get("category_name")
        out["ig_followers"] = r.get("followers")
        out["ig_last_post_ts"] = r.get("last_post_ts")
        out["ig_source"] = "ok"
    elif r.get("status") in (401, 403, 429):
        out["ig_source"] = "blocked"
    return out


def persist_ig(conn: sqlite3.Connection, dealer_id: str, ig: dict) -> None:
    cols = ["ig_handle", "ig_bio", "ig_external_url", "ig_category",
            "ig_followers", "ig_last_post_ts", "ig_source"]
    set_clause = ", ".join(f"{c}=excluded.{c}" for c in cols)
    placeholders = ", ".join(["?"] * (len(cols) + 1))
    conn.execute(
        f"""INSERT INTO dealer_operational_profile
            (dealer_id, {", ".join(cols)})
            VALUES ({placeholders})
            ON CONFLICT(dealer_id) DO UPDATE SET
            {set_clause}, updated_at=datetime('now')""",
        [dealer_id] + [ig.get(c) for c in cols],
    )
    conn.commit()
    recompute_sources_ok(conn, dealer_id)


def run(limit: int = 5) -> list[dict]:
    conn = connect()
    rows = conn.execute(
        "SELECT dealer_id, name, instagram FROM dealers "
        "WHERE instagram IS NOT NULL AND instagram != '' "
        "ORDER BY dealer_id LIMIT ?", (limit,)).fetchall()
    results = []
    for r in rows:
        ig = collect_ig(r["instagram"])
        persist_ig(conn, r["dealer_id"], ig)
        ig["dealer_id"] = r["dealer_id"]
        results.append(ig)
        print(f"[ig] {r['dealer_id']:16} {ig['ig_source']:8} "
              f"foll={ig['ig_followers']} cat={ig['ig_category']!r} "
              f"link={ig['ig_external_url']!r}", flush=True)
    conn.close()
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = run(a.limit)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
