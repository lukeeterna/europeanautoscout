#!/usr/bin/env python3
"""ARGOS S292 production daemon entrypoint.

PM2 starts this tiny process instead of invoking ``wa-daemon.js`` directly.
Before Node opens any WhatsApp transport it establishes deployment invariants:

- on the FIRST boot of a DB, ``agent_status`` is PAUSED;
- an existing PAUSED/ACTIVE value is never overwritten, so an explicit
  ``/resume`` survives ordinary restarts;
- traceable WhatsApp consent columns exist before the official Cloud policy
  adapter can resolve a dealer.

The wrapper then ``exec``s the same single-writer Node daemon; it is not a
second writer and contains no transport code.
"""
from __future__ import annotations

import json
import fcntl
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from whatsapp_consent import ensure_consent_columns  # noqa: E402


def acquire_writer_lock(state_path: str) -> int:
    """Hold a kernel lock across exec; never unlink it on shutdown.

    A PID file is insufficient: a stale PID or unlink/recreate can admit a second
    writer. The inherited descriptor closes only when its owner exits.
    """
    lock_path = str(Path(state_path).expanduser().resolve()) + ".argos-writer.lock"
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.set_inheritable(fd, True)
    except Exception as exc:
        os.close(fd)
        raise RuntimeError("canonical writer lock is unavailable") from exc
    return fd


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
        # Lock before migrations or transport initialization. The profile lock
        # also rejects a second writer pointed at another DB but the same auth.
        writer_fd = acquire_writer_lock(db_path)
        os.environ["ARGOS_WRITER_LOCK_FD"] = str(writer_fd)
        if os.environ.get("ARGOS_WA_TRANSPORT", "wwebjs") == "wwebjs":
            session_root = os.environ.get("ARGOS_WA_SESSION_DIR", "").strip()
            client_id = os.environ.get("ARGOS_WA_CLIENT_ID", "").strip()
            if not session_root or client_id != "argos-business":
                raise RuntimeError("canonical wwebjs session and argos-business identity required")
            root = Path(session_root).expanduser().resolve()
            if not root.is_dir():
                raise RuntimeError("canonical LocalAuth root is missing")
            profile_fd = acquire_writer_lock(str(root / ("session-" + client_id)))
            os.environ["ARGOS_PROFILE_LOCK_FD"] = str(profile_fd)
        status = initialize_runtime_state(db_path)
        ensure_consent_columns(db_path)
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
                    "consent_schema": "ready",
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
