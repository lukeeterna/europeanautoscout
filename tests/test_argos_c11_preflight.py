"""Offline tests for the read-only C11 controlled-recipient preflight."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "scripts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import argos_c11_preflight as c11  # noqa: E402


class C11PreflightTests(unittest.TestCase):
    EXPECTED_HEAD = "a" * 40

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "release"
        self.intel = self.repo / "wa-intelligence"
        self.intel.mkdir(parents=True)
        self.client_id = "argos-business"
        self.session_root = base / "wa-sender"
        self.session_root.mkdir()
        self.profile = self.session_root / f"session-{self.client_id}"
        self.profile.mkdir()
        (self.profile / "profile.bin").write_bytes(b"fixture")
        self.env = self.intel / ".env"
        self.env.write_text(
            "ARGOS_API_KEY=local-test-key\n"
            "ARGOS_AUTOMATION_ENABLED=0\n"
            "ARGOS_WA_TRANSPORT=wwebjs\n"
            "ARGOS_BIND_HOST=127.0.0.1\n"
            f"ARGOS_WA_SESSION_DIR={self.session_root}\n"
            f"ARGOS_WA_CLIENT_ID={self.client_id}\n",
            encoding="utf-8",
        )
        os.chmod(self.env, 0o600)

        self.primary = base / "primary.sqlite"
        con = sqlite3.connect(self.primary)
        con.executescript(
            """
            CREATE TABLE conversations (
                dealer_id TEXT PRIMARY KEY,
                phone_number TEXT,
                outreach_authorized INTEGER DEFAULT 0,
                conversation_state TEXT DEFAULT 'COLD',
                outbound_count INTEGER DEFAULT 0,
                whatsapp_opt_in INTEGER DEFAULT 0,
                whatsapp_opt_in_at TEXT,
                whatsapp_opt_in_source TEXT,
                whatsapp_opt_in_evidence_id TEXT,
                whatsapp_opt_out_at TEXT
            );
            CREATE TABLE messages (
                id TEXT PRIMARY KEY,
                dealer_id TEXT,
                direction TEXT NOT NULL
            );
            INSERT INTO conversations (
                dealer_id, phone_number, outreach_authorized,
                conversation_state, outbound_count,
                whatsapp_opt_in, whatsapp_opt_in_at,
                whatsapp_opt_in_source, whatsapp_opt_in_evidence_id,
                whatsapp_opt_out_at
            ) VALUES (
                'controlled-test', '+390000000001', 1,
                'COLD', 0,
                1, '2026-09-05T10:00:00+00:00',
                'controlled_test_fixture', 'evidence-secret-001', NULL
            );
            """
        )
        con.executemany(
            "INSERT INTO messages(id, dealer_id, direction) VALUES (?, ?, 'OUTBOUND')",
            [(f"out-{i:03d}", f"legacy-{i:03d}") for i in range(77)],
        )
        con.commit()
        con.close()

        self.bridge = base / "bridge.sqlite"
        con = sqlite3.connect(self.bridge)
        con.execute(
            """CREATE TABLE bridge_outbound (
                   id TEXT PRIMARY KEY,
                   approved_ts INTEGER,
                   sent_ts INTEGER
               )"""
        )
        con.commit()
        con.close()

        self.health = {
            "ok": True,
            "runtime": "argos-s292-single-writer",
            "connected": True,
            "transport": "wwebjs",
            "agent_status": "PAUSED",
            "business_hours": True,
            "bridge_enabled": True,
            "pending_bridge": 0,
            "global_outbound_24h": 0,
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_gate(self, **overrides):
        kwargs = dict(
            repo_root=self.repo,
            db_path=self.primary,
            bridge_db_path=self.bridge,
            expected_head=self.EXPECTED_HEAD,
            test_dealer_id="controlled-test",
            expected_outbound_baseline=77,
            health_payload=dict(self.health),
        )
        kwargs.update(overrides)
        with mock.patch.object(c11, "_git_head", return_value=(self.EXPECTED_HEAD, "")):
            return c11.run_preflight(**kwargs)

    def check(self, report, name):
        return next(x for x in report.checks if x["name"] == name)

    def test_green_contract_is_read_only_and_redacts_recipient_details(self) -> None:
        report = self.run_gate()
        self.assertTrue(report.ok, report.as_dict())
        self.assertEqual(report.outbound_baseline, 77)
        self.assertTrue(self.check(report, "localauth_client_id_present")["ok"])
        self.assertTrue(self.check(report, "localauth_profile_persistent")["ok"])
        rendered = json.dumps(report.as_dict(), sort_keys=True)
        self.assertNotIn("+390000000001", rendered)
        self.assertNotIn("evidence-secret-001", rendered)
        self.assertNotIn("local-test-key", rendered)
        self.assertNotIn("controlled-test", rendered)
        self.assertNotIn(str(self.session_root), rendered)

    def test_nonempty_session_root_without_target_profile_is_red(self) -> None:
        shutil.rmtree(self.profile)
        decoy = self.session_root / ".wwebjs_cache"
        decoy.mkdir()
        (decoy / "cache.bin").write_bytes(b"not-auth")
        report = self.run_gate()
        self.assertFalse(report.ok)
        check = self.check(report, "localauth_profile_persistent")
        self.assertFalse(check["ok"])
        self.assertTrue(check["detail"]["session_root_present"])
        self.assertFalse(check["detail"]["profile_directory_present"])

    def test_missing_localauth_client_id_is_red(self) -> None:
        text = self.env.read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines() if not line.startswith("ARGOS_WA_CLIENT_ID=")) + "\n"
        self.env.write_text(text, encoding="utf-8")
        os.chmod(self.env, 0o600)
        report = self.run_gate()
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "localauth_client_id_present")["ok"])
        self.assertFalse(self.check(report, "localauth_profile_persistent")["ok"])

    def test_disconnected_is_red(self) -> None:
        health = dict(self.health)
        health["connected"] = False
        report = self.run_gate(health_payload=health)
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "connected")["ok"])

    def test_outside_business_hours_is_red(self) -> None:
        health = dict(self.health)
        health["business_hours"] = False
        report = self.run_gate(health_payload=health)
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "business_hours")["ok"])

    def test_second_authorized_recipient_is_red(self) -> None:
        con = sqlite3.connect(self.primary)
        con.execute(
            """INSERT INTO conversations (
                   dealer_id, phone_number, outreach_authorized,
                   conversation_state, outbound_count,
                   whatsapp_opt_in, whatsapp_opt_in_at,
                   whatsapp_opt_in_source, whatsapp_opt_in_evidence_id
               ) VALUES ('other', '+390000000002', 1, 'COLD', 0, 1,
                         '2026-09-05T10:00:00+00:00', 'fixture', 'other-proof')"""
        )
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report.ok)
        check = self.check(report, "exactly_one_authorized_recipient")
        self.assertFalse(check["ok"])
        self.assertEqual(check["detail"], 2)

    def test_opted_out_controlled_recipient_is_red(self) -> None:
        con = sqlite3.connect(self.primary)
        con.execute(
            "UPDATE conversations SET whatsapp_opt_in=0, whatsapp_opt_out_at='2026-09-05T10:05:00+00:00' WHERE dealer_id='controlled-test'"
        )
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "controlled_test_whatsapp_opt_in")["ok"])

    def test_nonfresh_controlled_recipient_is_red(self) -> None:
        con = sqlite3.connect(self.primary)
        con.execute(
            "UPDATE conversations SET conversation_state='CONTACTED', outbound_count=1 WHERE dealer_id='controlled-test'"
        )
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "controlled_test_state_cold")["ok"])
        self.assertFalse(self.check(report, "controlled_test_outbound_count_zero")["ok"])

    def test_historical_outbound_for_controlled_recipient_is_red(self) -> None:
        con = sqlite3.connect(self.primary)
        con.execute("DELETE FROM messages WHERE id='out-000'")
        con.execute(
            "INSERT INTO messages(id, dealer_id, direction) VALUES ('controlled-out', 'controlled-test', 'OUTBOUND')"
        )
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report.ok)
        baseline = self.check(report, "outbound_baseline_expected")
        history = self.check(report, "controlled_test_historical_outbound_zero")
        self.assertTrue(baseline["ok"])
        self.assertFalse(history["ok"])
        self.assertEqual(history["detail"], 1)

    def test_pending_approved_bridge_row_is_red(self) -> None:
        con = sqlite3.connect(self.bridge)
        con.execute("INSERT INTO bridge_outbound(id, approved_ts, sent_ts) VALUES ('pending-1', 1, NULL)")
        con.commit()
        con.close()
        report = self.run_gate()
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "bridge_pending_approved_zero")["ok"])

    def test_outbound_baseline_drift_is_red(self) -> None:
        report = self.run_gate(expected_outbound_baseline=76)
        self.assertFalse(report.ok)
        check = self.check(report, "outbound_baseline_expected")
        self.assertFalse(check["ok"])
        self.assertEqual(check["detail"], {"expected": 76, "actual": 77})

    def test_exact_sha_mismatch_is_red(self) -> None:
        with mock.patch.object(c11, "_git_head", return_value=("b" * 40, "")):
            report = c11.run_preflight(
                repo_root=self.repo,
                db_path=self.primary,
                bridge_db_path=self.bridge,
                expected_head=self.EXPECTED_HEAD,
                test_dealer_id="controlled-test",
                expected_outbound_baseline=77,
                health_payload=dict(self.health),
            )
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "expected_head")["ok"])

    def test_active_runtime_or_recent_outbound_is_red(self) -> None:
        health = dict(self.health)
        health["agent_status"] = "ACTIVE"
        health["global_outbound_24h"] = 1
        report = self.run_gate(health_payload=health)
        self.assertFalse(report.ok)
        self.assertFalse(self.check(report, "runtime_paused")["ok"])
        self.assertFalse(self.check(report, "health_outbound_24h_zero")["ok"])


if __name__ == "__main__":
    unittest.main()
