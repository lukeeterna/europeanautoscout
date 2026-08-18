"""Offline tests for the S292 PM2 runtime entrypoint."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

ROOT = Path(__file__).resolve().parents[1]
WA_DIR = ROOT / "wa-intelligence"
if str(WA_DIR) not in sys.path:
    sys.path.insert(0, str(WA_DIR))

from runtime_entrypoint import initialize_runtime_state, validate_required_environment  # noqa: E402


class RuntimeEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "dealer_network.sqlite"
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE seed(id INTEGER)")
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_boot_is_paused(self):
        status = initialize_runtime_state(str(self.db))
        self.assertEqual(status, "PAUSED")
        con = sqlite3.connect(self.db)
        row = con.execute(
            "SELECT value FROM argos_runtime_state WHERE key='agent_status'"
        ).fetchone()
        con.close()
        self.assertEqual(row[0], "PAUSED")

    def test_explicit_active_state_survives_restart(self):
        self.assertEqual(initialize_runtime_state(str(self.db)), "PAUSED")
        con = sqlite3.connect(self.db)
        con.execute(
            "UPDATE argos_runtime_state SET value='ACTIVE' WHERE key='agent_status'"
        )
        con.commit()
        con.close()
        self.assertEqual(initialize_runtime_state(str(self.db)), "ACTIVE")

    def test_missing_database_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            initialize_runtime_state(str(Path(self.tmp.name) / "missing.sqlite"))

    def test_production_api_key_is_required(self):
        with patch.dict(
            os.environ,
            {"ARGOS_DB_PATH": str(self.db), "ARGOS_API_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                validate_required_environment()

    def test_required_environment_is_returned_without_secret_logging(self):
        with patch.dict(
            os.environ,
            {"ARGOS_DB_PATH": str(self.db), "ARGOS_API_KEY": "secret-value"},
            clear=False,
        ):
            db_path, api_key = validate_required_environment()
        self.assertEqual(db_path, str(self.db))
        self.assertEqual(api_key, "secret-value")


if __name__ == "__main__":
    unittest.main()
