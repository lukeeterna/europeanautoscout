"""Offline contract tests for ARGOS post-C11 production readiness."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "scripts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import argos_postpilot_readiness as gate  # noqa: E402


class PostPilotReadinessTests(unittest.TestCase):
    SHA = "a" * 40

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo = root / "release"
        (self.repo / ".git").mkdir(parents=True)
        self.client_id = "argos-business"
        self.session_root = root / "localauth"
        self.session_root.mkdir()
        self.profile = self.session_root / f"session-{self.client_id}"
        self.profile.mkdir()
        (self.profile / "profile.bin").write_bytes(b"fixture")
        self.env = self.repo / ".env"
        self.env.write_text(
            "ARGOS_AUTOMATION_ENABLED=0\n"
            "ARGOS_WA_TRANSPORT=wwebjs\n"
            "ARGOS_BIND_HOST=127.0.0.1\n"
            f"ARGOS_WA_SESSION_DIR={self.session_root}\n"
            f"ARGOS_WA_CLIENT_ID={self.client_id}\n",
            encoding="utf-8",
        )
        os.chmod(self.env, 0o600)

        self.primary = root / "primary.sqlite"
        con = sqlite3.connect(self.primary)
        con.executescript(
            """
            CREATE TABLE messages (id TEXT PRIMARY KEY, direction TEXT NOT NULL);
            CREATE TABLE conversations (dealer_id TEXT PRIMARY KEY, outreach_authorized INTEGER DEFAULT 0);
            INSERT INTO conversations VALUES ('controlled', 0);
            """
        )
        con.executemany(
            "INSERT INTO messages(id,direction) VALUES (?, 'OUTBOUND')",
            [("m%03d" % i,) for i in range(78)],
        )
        con.commit()
        con.close()

        self.bridge = root / "bridge.sqlite"
        con = sqlite3.connect(self.bridge)
        con.execute(
            "CREATE TABLE bridge_outbound (id TEXT PRIMARY KEY, approved_ts INTEGER, sent_ts INTEGER, template_id TEXT)"
        )
        con.commit()
        con.close()

        self.health = {
            "runtime": "argos-s292-single-writer",
            "connected": True,
            "transport": "wwebjs",
            "agent_status": "PAUSED",
            "pending_bridge": 0,
            "global_outbound_24h": 1,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_gate(self, **overrides):
        kwargs = dict(
            repo_root=self.repo,
            db_path=self.primary,
            bridge_db_path=self.bridge,
            env_path=self.env,
            expected_head=self.SHA,
            expected_outbound_total=78,
            health_payload=dict(self.health),
            pre_reboot_boot_epoch=100,
            current_boot_epoch=200,
        )
        kwargs.update(overrides)
        with mock.patch.object(gate, "_git_head", return_value=self.SHA), mock.patch.object(
            gate, "_git_tracked_clean", return_value=True
        ):
            return gate.run_gate(**kwargs)

    def check(self, report, name):
        return next(item for item in report["checks"] if item["name"] == name)

    def test_green_postpilot_contract(self):
        report = self.run_gate()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["safety"]["production_db_mutation"], "NONE")
        self.assertEqual(report["safety"]["restore_target"], "TEMPORARY_ONLY")
        self.assertTrue(self.check(report, "localauth_client_id_present")["ok"])
        self.assertTrue(self.check(report, "localauth_session_present")["ok"])
        self.assertTrue(self.check(report, "reboot_proven")["ok"])
        self.assertTrue(self.check(report, "primary_restore_drill")["ok"])
        self.assertTrue(self.check(report, "bridge_restore_drill")["ok"])

    def test_nonempty_root_without_target_profile_is_red(self):
        shutil.rmtree(self.profile)
        decoy = self.session_root / "node_modules"
        decoy.mkdir()
        (decoy / "sentinel.txt").write_text("not a LocalAuth profile", encoding="utf-8")
        report = self.run_gate()
        self.assertFalse(report["ok"])
        check = self.check(report, "localauth_session_present")
        self.assertFalse(check["ok"])
        self.assertTrue(check["detail"]["session_root_present"])
        self.assertFalse(check["detail"]["profile_directory_present"])

    def test_missing_client_id_is_red_even_with_profile_files(self):
        text = self.env.read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines() if not line.startswith("ARGOS_WA_CLIENT_ID=")) + "\n"
        self.env.write_text(text, encoding="utf-8")
        os.chmod(self.env, 0o600)
        report = self.run_gate()
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "localauth_client_id_present")["ok"])
        self.assertFalse(self.check(report, "localauth_session_present")["ok"])

    def test_outbound_increment_beyond_single_pilot_is_red(self):
        con = sqlite3.connect(self.primary)
        con.execute("INSERT INTO messages(id,direction) VALUES ('unexpected','OUTBOUND')")
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "postpilot_outbound_total")["ok"])

    def test_authorized_recipient_after_cleanup_is_red(self):
        con = sqlite3.connect(self.primary)
        con.execute("UPDATE conversations SET outreach_authorized=1")
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "authorized_recipients_zero")["ok"])

    def test_disconnected_or_active_runtime_is_red(self):
        health = dict(self.health)
        health["connected"] = False
        health["agent_status"] = "ACTIVE"
        report = self.run_gate(health_payload=health)
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "health_connected")["ok"])
        self.assertFalse(self.check(report, "runtime_paused")["ok"])

    def test_reboot_must_be_real_when_preboot_epoch_is_supplied(self):
        report = self.run_gate(pre_reboot_boot_epoch=200, current_boot_epoch=200)
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "reboot_proven")["ok"])

    def test_env_permissions_are_fail_closed(self):
        os.chmod(self.env, 0o644)
        report = self.run_gate()
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "env_private")["ok"])

    def test_pending_bridge_is_red(self):
        con = sqlite3.connect(self.bridge)
        con.execute("INSERT INTO bridge_outbound VALUES ('p',1,NULL,'DAY1_PREMIUM')")
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "bridge_pending_approved_zero")["ok"])

    def test_recent_outbound_must_remain_bounded_to_pilot(self):
        health = dict(self.health)
        health["global_outbound_24h"] = 2
        report = self.run_gate(health_payload=health)
        self.assertFalse(report["ok"])
        self.assertFalse(self.check(report, "health_recent_outbound_bounded")["ok"])


if __name__ == "__main__":
    unittest.main()
