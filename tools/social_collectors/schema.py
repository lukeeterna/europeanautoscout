"""
schema.py -- Schema operativo S4-OPS (additivo).

Tabelle:
  - dealer_operational_profile: canali/contatti per dealer (FB + IG).
  - operational_anchors: 4 ancore operative per dealer
    (qualifica / canale / vivo / volume), una riga per (dealer_id, anchor).

Idempotente: CREATE ... IF NOT EXISTS. Nessuna colonna personale (PII).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parents[2] / "dealer_network.sqlite")

_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS dealer_operational_profile (
    dealer_id        TEXT PRIMARY KEY,
    -- Facebook (pubblico via og:/meta)
    fb_url           TEXT,
    fb_name          TEXT,
    fb_category      TEXT,
    fb_likes         INTEGER,
    fb_talking       INTEGER,
    fb_phone         TEXT,
    fb_email         TEXT,
    fb_website       TEXT,
    fb_last_post     TEXT,
    fb_source        TEXT,           -- ok | js_only | login_gated | error
    -- Instagram (web_profile_info)
    ig_handle        TEXT,
    ig_bio           TEXT,
    ig_external_url  TEXT,
    ig_category      TEXT,
    ig_followers     INTEGER,
    ig_last_post_ts  INTEGER,        -- taken_at_timestamp ultimo post
    ig_source        TEXT,           -- ok | blocked | error | not_probed
    -- meta
    sources_ok       TEXT,           -- csv dei canali che hanno prodotto dati
    updated_at       TEXT DEFAULT (datetime('now'))
);
"""

_ANCHORS_DDL = """
CREATE TABLE IF NOT EXISTS operational_anchors (
    dealer_id    TEXT NOT NULL,
    anchor       TEXT NOT NULL,      -- qualifica | canale | vivo | volume
    value        TEXT,
    source       TEXT,               -- fb | ig | db
    updated_at   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (dealer_id, anchor)
);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA busy_timeout=10000;")
    conn.execute(_PROFILE_DDL)
    conn.execute(_ANCHORS_DDL)
    conn.commit()


_SOURCE_FIELDS = [
    "fb_category", "fb_likes", "fb_phone", "fb_email", "fb_website",
    "fb_last_post", "ig_bio", "ig_external_url", "ig_category",
    "ig_followers", "ig_last_post_ts",
]


def recompute_sources_ok(conn: sqlite3.Connection, dealer_id: str) -> None:
    """Ricalcola sources_ok dai campi non-null della riga (deterministico)."""
    row = conn.execute(
        "SELECT * FROM dealer_operational_profile WHERE dealer_id=?",
        (dealer_id,)).fetchone()
    if not row:
        return
    present = [f for f in _SOURCE_FIELDS if row[f] not in (None, "")]
    conn.execute(
        "UPDATE dealer_operational_profile SET sources_ok=? WHERE dealer_id=?",
        (",".join(present), dealer_id))
    conn.commit()


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


if __name__ == "__main__":
    c = connect()
    print("schema OK ->", DB_PATH)
    for t in ("dealer_operational_profile", "operational_anchors"):
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
        print(f"  {t}: {len(cols)} cols")
    c.close()
