"""Offline regressions that must be GREEN before WhatsApp device pairing.

No test contacts WhatsApp or any dealer. This module protects the final send
boundary and the workflow topology so pairing/cutover/pilot cannot silently
become an automatic side effect of ordinary repository pushes.
"""
from __future__ import annotations

import importlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WA_DIR = ROOT / "wa-intelligence"
if str(WA_DIR) not in sys.path:
    sys.path.insert(0, str(WA_DIR))

outbound_guard = importlib.import_module("outbound_guard")
state_machine = importlib.import_module("state_machine")
templates = importlib.import_module("templates")
whatsapp_consent = importlib.import_module("whatsapp_consent")


class FinalOutboundBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "dealer.sqlite")
        con = sqlite3.connect(self.db_path)
        try:
            con.executescript(
                """
                CREATE TABLE conversations (
                    dealer_id TEXT PRIMARY KEY,
                    dealer_name TEXT,
                    phone_number TEXT,
                    current_step TEXT DEFAULT 'COLD',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    dealer_id TEXT,
                    direction TEXT,
                    body TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO conversations
                    (dealer_id, dealer_name, phone_number, current_step)
                VALUES ('c11-test', 'Test autorizzato', '+390000000001', 'COLD');
                """
            )
            con.commit()
        finally:
            con.close()
        state_machine.ensure_state_columns(self.db_path)
        whatsapp_consent.ensure_consent_columns(self.db_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _set_authorized(self, value: int) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "UPDATE conversations SET outreach_authorized=? WHERE dealer_id='c11-test'",
                [value],
            )
            con.commit()
        finally:
            con.close()

    def _grant_consent(self) -> None:
        whatsapp_consent.grant_consent(
            db_path=self.db_path,
            dealer_id="c11-test",
            source="controlled_test_fixture",
            evidence_id="c11-consent-proof",
            granted_at="2026-09-05T10:00:00+00:00",
        )

    def _message(self) -> str:
        return templates.fill_template(
            "DAY1_PREMIUM",
            {
                "source": "contatto di test autorizzato",
                "brand_focus": "BMW",
            },
        )

    def _evaluate(self) -> dict:
        return outbound_guard.evaluate(
            db_path=self.db_path,
            dealer_id="c11-test",
            template_id="DAY1_PREMIUM",
            message=self._message(),
        )

    def test_internal_authorization_is_required_at_final_boundary(self) -> None:
        self._grant_consent()
        result = self._evaluate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "OUTREACH_NOT_AUTHORIZED")
        self.assertEqual(result["check"], "authorization")

    def test_traceable_whatsapp_opt_in_is_required_at_final_boundary(self) -> None:
        self._set_authorized(1)
        result = self._evaluate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "WHATSAPP_OPT_IN_REQUIRED")
        self.assertEqual(result["check"], "whatsapp_consent")

    def test_opt_out_blocks_even_when_internal_authorization_remains(self) -> None:
        self._set_authorized(1)
        self._grant_consent()
        whatsapp_consent.revoke_consent(
            db_path=self.db_path,
            dealer_id="c11-test",
            revoked_at="2026-09-05T10:01:00+00:00",
        )
        result = self._evaluate()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "WHATSAPP_OPT_IN_REQUIRED")

    def test_authorized_opted_in_test_record_reaches_existing_policy_chain(self) -> None:
        self._set_authorized(1)
        self._grant_consent()
        result = self._evaluate()
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["check"], "all")


class WorkflowSafetyTests(unittest.TestCase):
    def _workflow(self, name: str) -> str:
        return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def _on_block(self, name: str) -> str:
        return self._workflow(name).split("\npermissions:", 1)[0]

    def test_pairing_mutation_and_live_pilot_workflows_are_manual_only(self) -> None:
        manual_only = (
            "argos-c10-local-pairing.yml",
            "argos-c10-wwebjs-cutover.yml",
            "argos-c10-alt-localauth-probe.yml",
            "argos-c10-auth-lifecycle-diagnostic.yml",
            "argos-c11-controlled-pilot.yml",
        )
        for name in manual_only:
            with self.subTest(name=name):
                block = self._on_block(name)
                self.assertIn("workflow_dispatch:", block)
                self.assertNotIn("\n  push:", block)
                self.assertNotIn("pull_request:", block)

    def test_pairing_is_single_staged_qr_not_a_retry_loop(self) -> None:
        pairing = self._workflow("argos-c10-local-pairing.yml")
        helper = (WA_DIR / "tools" / "argos_c10_pairing_helper.js").read_text(encoding="utf-8")
        self.assertNotIn("http://127.0.0.1:9191/qr", pairing)
        self.assertEqual(helper.count("client.initialize()"), 1)
        self.assertIn("firstQrCaptured", helper)
        self.assertIn("if (firstQrCaptured || finished) return;", helper)
        self.assertIn("PAIRING_QR_FETCH_COUNT=1", pairing)
        self.assertIn("PAIRING_AUTOMATIC_RETRY=DISABLED", pairing)
        self.assertIn("PAIRING_READY_PROFILE=STAGED", pairing)
        self.assertIn("CANONICAL_LOCALAUTH_MUTATION=NONE", pairing)
        self.assertIn("PRODUCTION_PROCESS_MUTATION=NONE", pairing)
        self.assertIn("OUTBOUND_ACTION=NONE", pairing)

    def test_machine_green_requires_persistent_target_localauth_profile(self) -> None:
        probe = (ROOT / "tools" / "scripts" / "argos_c10_machine_probe.sh").read_text(encoding="utf-8")
        for marker in (
            "LOCALAUTH_SESSION_ROOT_CANONICAL=",
            "LOCALAUTH_CLIENT_ID_CONFIGURED=",
            "LOCALAUTH_PROFILE_PRESENT=",
            "LOCALAUTH_PROFILE_FILE_COUNT_POSITIVE=",
            'blockers.append("WRITER_SESSION_DIR_NOT_CANONICAL")',
            'blockers.append("LOCALAUTH_CLIENT_ID_MISSING")',
            'blockers.append("LOCALAUTH_PROFILE_NOT_PERSISTED")',
        ):
            self.assertIn(marker, probe)
        self.assertIn('profile = root / f"session-{client_id}"', probe)

    def test_cutover_has_backup_rollback_exact_sha_and_zero_outbound_contract(self) -> None:
        workflow = self._workflow("argos-c10-wwebjs-cutover.yml")
        script = (WA_DIR / "tools" / "argos_c10_wwebjs_cutover.sh").read_text(encoding="utf-8")
        self.assertIn("Require S292 GREEN on this exact SHA", workflow)
        self.assertIn("S292_EXACT_SHA=GREEN", workflow)
        self.assertIn("Promote staged READY LocalAuth with rollback boundary", workflow)
        self.assertIn("PAIRING_PROFILE_PROMOTION=PASS", workflow)
        self.assertIn("PAIRING_PROFILE_ROLLBACK=ATTEMPTED", workflow)
        self.assertIn("PAIRING_SOURCE=STAGED_READY", workflow)
        for marker in (
            "DB_BACKUP=PASS",
            "PREDEPLOY=GREEN",
            "rollback()",
            "ROLLBACK=PASS",
            "WWEBJS_CONNECTED=YES",
            "POST_OUTBOUND_DELTA",
            "PM2_SAVE=PASS",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("curl /resume", script)
        self.assertIn("TARGET_RUNTIME_STATUS=PAUSED", script)
        self.assertIn("TARGET_AUTOMATION_ENABLED=0", script)

    def test_c11_live_pilot_is_one_shot_fail_closed(self) -> None:
        workflow = self._workflow("argos-c11-controlled-pilot.yml")
        self.assertIn("Require real C10 machine GREEN immediately before pilot", workflow)
        self.assertIn("C10_MACHINE=GREEN", workflow)
        self.assertIn("C11_PREFLIGHT=GREEN", workflow)
        self.assertIn("ARGOS_C11_TEST_DEALER_ID", workflow)
        self.assertIn("C11_SINGLE_SEND_ACK=PASS", workflow)
        self.assertIn("C11_OUTBOUND_DELTA=1", workflow)
        self.assertIn("C11_TEST_RECIPIENT_DEAUTHORIZED=YES", workflow)
        self.assertIn("C11_RUNTIME_STATUS=PAUSED", workflow)
        self.assertIn("trap cleanup EXIT INT TERM", workflow)
        self.assertEqual(workflow.count("http://127.0.0.1:9191/send)"), 1)
        self.assertNotIn("/send-doc", workflow)
        self.assertNotIn("/send-multi", workflow)
        self.assertNotIn("/send-voice", workflow)

    def test_health_surface_exposes_required_observability_without_secrets(self) -> None:
        daemon = (WA_DIR / "wa-daemon.js").read_text(encoding="utf-8")
        health = daemon[daemon.index("if (req.method === 'GET' && (url.pathname === '/' ") :]
        health = health[: health.index("if (req.method === 'GET' && url.pathname === '/qr')")]
        for field in (
            "connected:",
            "transport:",
            "agent_status:",
            "business_hours:",
            "bridge_enabled:",
            "pending_bridge:",
            "global_outbound_24h:",
            "limits:",
        ):
            self.assertIn(field, health)
        self.assertNotIn("API_KEY", health)
        self.assertNotIn("ACCESS_TOKEN", health)

    def test_env_template_contains_no_real_telegram_identity_or_secret_values(self) -> None:
        env = (WA_DIR / ".env.example").read_text(encoding="utf-8")
        values = {}
        for raw in env.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip()
        for key in (
            "ARGOS_API_KEY",
            "META_WA_ACCESS_TOKEN",
            "META_WA_WEBHOOK_VERIFY_TOKEN",
            "META_APP_SECRET",
            "OPENROUTER_API_KEY",
            "ARGOS_TELEGRAM_TOKEN",
            "GMAIL_FERRETTI_APP_PASSWORD",
            "ARGOS_ADMIN_SECRET",
            "ARGOS_TELEGRAM_CHAT_ID",
            "ARGOS_C11_TEST_DEALER_ID",
        ):
            self.assertIn(key, values)
            self.assertEqual(values[key], "", f"{key} must be a blank local-only placeholder")


if __name__ == "__main__":
    unittest.main()
