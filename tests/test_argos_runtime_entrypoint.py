"""Offline tests for the S292 PM2 runtime entrypoint."""
from __future__ import annotations

import os
import subprocess
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

from runtime_entrypoint import initialize_runtime_state, validate_required_environment, acquire_writer_lock  # noqa: E402


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

    def test_second_process_is_blocked_until_lock_owner_exits(self):
        fd = acquire_writer_lock(str(self.db))
        self.addCleanup(os.close, fd)
        code = "from runtime_entrypoint import acquire_writer_lock; import sys; acquire_writer_lock(sys.argv[1])"
        env = {**os.environ, 'PYTHONPATH': str(WA_DIR)}
        child = subprocess.run([sys.executable, '-c', code, str(self.db)], env=env, capture_output=True)
        self.assertNotEqual(child.returncode, 0)

    def test_lock_survives_exec_and_is_released_by_process_exit(self):
        code = "from runtime_entrypoint import acquire_writer_lock; import os,sys; fd=acquire_writer_lock(sys.argv[1]); os.execvp('node',['node','-e',\"console.log('LOCKED');setInterval(()=>{},1000)\"])"
        env = {**os.environ, 'PYTHONPATH': str(WA_DIR)}
        child = subprocess.Popen([sys.executable, '-c', code, str(self.db)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        self.assertEqual(child.stdout.readline().strip(), 'LOCKED')
        with self.assertRaises(RuntimeError):
            acquire_writer_lock(str(self.db))
        child.terminate(); child.wait(timeout=5)
        fd = acquire_writer_lock(str(self.db))
        os.close(fd)
        child.stdout.close(); child.stderr.close()

    def test_symlink_lockfile_is_rejected(self):
        target = Path(self.tmp.name) / 'untouched'
        target.write_text('preserve')
        Path(str(self.db) + '.argos-writer.lock').symlink_to(target)
        with self.assertRaises(OSError):
            acquire_writer_lock(str(self.db))
        self.assertEqual(target.read_text(), 'preserve')


if __name__ == "__main__":
    unittest.main()
