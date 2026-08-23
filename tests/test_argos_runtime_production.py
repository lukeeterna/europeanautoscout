"""Offline production-runtime tests for ARGOS S292 automation boundaries."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WA_DIR = ROOT / "wa-intelligence"
if str(WA_DIR) not in sys.path:
    sys.path.insert(0, str(WA_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from outreach_scheduler import run_cycle  # noqa: E402
from post_send_update import apply_post_send  # noqa: E402
from state_machine import ensure_state_columns  # noqa: E402
from whatsapp_consent import ensure_consent_columns, grant_consent  # noqa: E402


class RuntimeProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "primary.sqlite")
        self.bridge_path = os.path.join(self.tmp.name, "bridge.sqlite")
        con = sqlite3.connect(self.db_path)
        con.executescript(
            """
            CREATE TABLE conversations (
                dealer_id TEXT PRIMARY KEY,
                dealer_name TEXT,
                phone_number TEXT,
                source TEXT,
                current_step TEXT DEFAULT 'COLD',
                conversation_state TEXT DEFAULT 'COLD',
                outbound_count INTEGER DEFAULT 0,
                inbound_count INTEGER DEFAULT 0,
                outreach_authorized INTEGER DEFAULT 0,
                handoff_source TEXT DEFAULT 'cold'
            );
            CREATE TABLE messages (
                id TEXT PRIMARY KEY,
                dealer_id TEXT,
                direction TEXT,
                body TEXT,
                wa_msg_id TEXT,
                processed INTEGER DEFAULT 0,
                created_at TEXT,
                template_id TEXT
            );
            """
        )
        con.commit()
        con.close()
        ensure_state_columns(self.db_path)
        ensure_consent_columns(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _dealer(
        self,
        dealer_id: str,
        *,
        state: str = "COLD",
        outbound_count: int = 0,
        authorized: int = 0,
        opted_in: bool = False,
    ) -> None:
        con = sqlite3.connect(self.db_path)
        con.execute(
            """INSERT INTO conversations
               (dealer_id, dealer_name, phone_number, source, current_step,
                conversation_state, outbound_count, inbound_count,
                outreach_authorized, handoff_source)
               VALUES (?, ?, ?, 'sito pubblico', ?, ?, ?, 0, ?, 'cold')""",
            [dealer_id, f"Dealer {dealer_id}", f"39333123{len(dealer_id):03d}", state, state, outbound_count, authorized],
        )
        con.commit()
        con.close()
        if opted_in:
            grant_consent(
                db_path=self.db_path,
                dealer_id=dealer_id,
                source="offline_test_fixture",
                evidence_id=f"consent-{dealer_id}",
                granted_at="2026-08-01T10:00:00+00:00",
            )

    def _message(self, dealer_id: str, direction: str, when: datetime, *, template_id: str | None = None, wa_id: str | None = None):
        con = sqlite3.connect(self.db_path)
        msg_id = f"{direction.lower()}-{dealer_id}-{int(when.timestamp())}"
        con.execute(
            """INSERT INTO messages
               (id, dealer_id, direction, body, wa_msg_id, processed, created_at, template_id)
               VALUES (?, ?, ?, 'test', ?, 1, ?, ?)""",
            [msg_id, dealer_id, direction, wa_id, when.isoformat(), template_id],
        )
        con.commit()
        con.close()
        return msg_id

    def test_scheduler_disabled_is_zero_mutation(self):
        self._dealer("d-disabled", authorized=1)
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=False,
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["enabled"])
        self.assertFalse(os.path.exists(self.bridge_path))

    def test_unauthorized_dealer_never_queues(self):
        self._dealer("d-noauth", authorized=0, opted_in=True)
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
        )
        self.assertEqual(result["candidates"], 0)
        self.assertEqual(result["queued"], 0)

    def test_internal_authorization_without_whatsapp_opt_in_never_queues(self):
        self._dealer("d-no-consent", authorized=1, opted_in=False)
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
        )
        self.assertEqual(result["candidates"], 0)
        self.assertEqual(result["queued"], 0)

    def test_authorized_opted_in_day1_is_guarded_and_idempotent(self):
        self._dealer("d-day1", authorized=1, opted_in=True)
        first = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
        )
        self.assertEqual(first["candidates"], 1)
        self.assertEqual(first["blocked"], 0)
        self.assertEqual(first["queued"], 1)

        second = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
        )
        self.assertEqual(second["queued"], 0)

        con = sqlite3.connect(self.bridge_path)
        row = con.execute(
            """SELECT deal_id, template_id, action_type, approved_ts, sent_ts,
                      whatsapp_opt_in_evidence_id
                 FROM bridge_outbound"""
        ).fetchone()
        con.close()
        self.assertEqual(row[0], "d-day1")
        self.assertEqual(row[1], "DAY1_PREMIUM")
        self.assertEqual(row[2], "s292_scheduler")
        self.assertIsNotNone(row[3])
        self.assertIsNone(row[4])
        self.assertEqual(row[5], "consent-d-day1")

    def test_cloud_day1_persists_exact_meta_template_payload(self):
        self._dealer("d-cloud", authorized=1, opted_in=True)
        env = {
            "META_WA_TEMPLATE_LANGUAGE": "it",
            "META_WA_TEMPLATE_DAY1_NAME": "argos_day1_premium_v1",
            "META_WA_TEMPLATE_DAY7_NAME": "argos_day7_recovery_v1",
            "META_WA_TEMPLATE_DAY12_NAME": "argos_day12_final_v1",
        }
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
            transport_mode="cloud",
            env=env,
        )
        self.assertEqual(result["queued"], 1)
        con = sqlite3.connect(self.bridge_path)
        raw, evidence = con.execute(
            "SELECT meta_template_json, whatsapp_opt_in_evidence_id FROM bridge_outbound WHERE deal_id='d-cloud'"
        ).fetchone()
        con.close()
        payload = json.loads(raw)
        self.assertEqual(payload["name"], "argos_day1_premium_v1")
        self.assertEqual(payload["language"]["code"], "it")
        self.assertEqual(payload["internal_template_id"], "DAY1_PREMIUM")
        self.assertEqual(len(payload["components"][0]["parameters"]), 2)
        self.assertEqual(evidence, "consent-d-cloud")

    def test_cloud_missing_template_config_blocks_without_enqueue(self):
        self._dealer("d-cloud-missing", authorized=1, opted_in=True)
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
            transport_mode="cloud",
            env={},
        )
        self.assertEqual(result["candidates"], 1)
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["queued"], 0)

    def test_day7_requires_no_newer_inbound(self):
        now = datetime.now(timezone.utc)
        self._dealer("d-day7", state="CONTACTED", outbound_count=1, authorized=1, opted_in=True)
        self._message("d-day7", "OUTBOUND", now - timedelta(days=8), template_id="DAY1_PREMIUM", wa_id="wa-old")
        result = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
            now_ts=now.timestamp(),
        )
        self.assertEqual(result["queued"], 1)
        con = sqlite3.connect(self.bridge_path)
        template = con.execute("SELECT template_id FROM bridge_outbound WHERE deal_id='d-day7'").fetchone()[0]
        con.close()
        self.assertEqual(template, "DAY7_RECOVERY")

        self._dealer("d-inbound", state="CONTACTED", outbound_count=1, authorized=1, opted_in=True)
        self._message("d-inbound", "OUTBOUND", now - timedelta(days=8), template_id="DAY1_PREMIUM", wa_id="wa-old-2")
        self._message("d-inbound", "INBOUND", now - timedelta(days=1), wa_id="wa-in")
        result2 = run_cycle(
            db_path=self.db_path,
            bridge_path=self.bridge_path,
            enabled=True,
            now_ts=now.timestamp(),
        )
        con = sqlite3.connect(self.bridge_path)
        count = con.execute("SELECT COUNT(*) FROM bridge_outbound WHERE deal_id='d-inbound'").fetchone()[0]
        con.close()
        self.assertEqual(count, 0)
        self.assertGreaterEqual(result2["candidates"], 0)

    def test_post_send_is_idempotent_and_transitions_day1_once(self):
        self._dealer("d-post", authorized=1)
        now = datetime.now(timezone.utc)
        self._message(
            "d-post",
            "OUTBOUND",
            now,
            template_id="DAY1_PREMIUM",
            wa_id="wa-real-1",
        )
        first = apply_post_send(
            db_path=self.db_path,
            dealer_id="d-post",
            template_id="DAY1_PREMIUM",
            event_id="wa-real-1",
        )
        second = apply_post_send(
            db_path=self.db_path,
            dealer_id="d-post",
            template_id="DAY1_PREMIUM",
            event_id="wa-real-1",
        )
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["new_state"], "CONTACTED")
        self.assertEqual(second["outbound_count"], 1)

        con = sqlite3.connect(self.db_path)
        row = con.execute(
            "SELECT conversation_state, outbound_count, current_step FROM conversations WHERE dealer_id='d-post'"
        ).fetchone()
        events = con.execute("SELECT COUNT(*) FROM argos_post_send_events").fetchone()[0]
        con.close()
        self.assertEqual(row, ("CONTACTED", 1, "DAY1_SENT"))
        self.assertEqual(events, 1)

    def test_post_send_compatibility_resolves_persisted_wa_id(self):
        self._dealer("d-compat", authorized=1)
        self._message(
            "d-compat",
            "OUTBOUND",
            datetime.now(timezone.utc),
            template_id="DAY1_PREMIUM",
            wa_id="wa-compat",
        )
        result = apply_post_send(
            db_path=self.db_path,
            dealer_id="d-compat",
            template_id="DAY1_PREMIUM",
        )
        self.assertEqual(result["event_id"], "wa-compat")
        self.assertEqual(result["outbound_count"], 1)


if __name__ == "__main__":
    unittest.main()
