#!/usr/bin/env python3
"""ARGOS S292 production daemon entrypoint.

PM2 starts this tiny process instead of invoking ``wa-daemon.js`` directly.
It establishes one deployment invariant before Node opens WhatsApp:

- on the FIRST boot of a DB, ``agent_status`` is PAUSED;
- an existing PAUSED/ACTIVE value is never overwritten, so an explicit
  ``/resume`` survives ordinary restarts.

The wrapper then ``exec``s the same single-writer Node daemon; it is not a
second writer and contains no transport code.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def initialize_runtime_state(db_path: str) -> str:
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"ARGOS_DB_PATH does not exist: {path}")

    con = sqlite3.connect(str(path), timeout=10)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=10000")
        con.execute(
            """CREATE TABLE IF NOT EXISTS argos_runtime_state (
                   key TEXT PRIMARY KEY,
                   value TEXT NOT NULL,
                   updated_at TEXT NOT NULL
               )"""
        )
        now = datetime.now(timezone.utc).isoformat()
        con.execute(
            """INSERT OR IGNORE INTO argos_runtime_state(key, value, updated_at)
               VALUES ('agent_status', 'PAUSED', ?)""",
            [now],
        )
        row = con.execute(
            "SELECT value FROM argos_runtime_state WHERE key='agent_status'"
        ).fetchone()
        con.commit()
    finally:
        con.close()

    status = str(row[0] if row else "").upper()
    if status not in {"PAUSED", "ACTIVE"}:
        raise RuntimeError(f"invalid persisted agent_status: {status!r}")
    return status


def validate_required_environment() -> tuple[str, str]:
    db_path = os.environ.get("ARGOS_DB_PATH", "").strip()
    api_key = os.environ.get("ARGOS_API_KEY", "").strip()
    if not db_path:
        raise RuntimeError("ARGOS_DB_PATH is required")
    if not api_key:
        raise RuntimeError("ARGOS_API_KEY is required in production")
    return db_path, api_key


def main(argv: Optional[list[str]] = None) -> int:
    del argv
    try:
        db_path, _ = validate_required_environment()
        status = initialize_runtime_state(db_path)
        node = shutil.which("node")
        if not node:
            raise RuntimeError("node executable not found in PATH")
        daemon = HERE / "wa-daemon.js"
        if not daemon.is_file():
            raise FileNotFoundError(str(daemon))
        print(
            json.dumps(
                {
                    "ok": True,
                    "entrypoint": "argos-s292",
                    "initial_agent_status": status,
                    "daemon": str(daemon),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        os.execv(node, [node, str(daemon)])
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "error": type(exc).__name__, "reason": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
            flush=True,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
