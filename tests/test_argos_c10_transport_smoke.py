"""Offline tests for the transport-aware C10 smoke gate."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_PATH = ROOT / "tools" / "scripts" / "argos_c10_smoke.py"
SPEC = importlib.util.spec_from_file_location("argos_c10_smoke", SMOKE_PATH)
assert SPEC and SPEC.loader
SMOKE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SMOKE
SPEC.loader.exec_module(SMOKE)


class C10TransportSmokeTests(unittest.TestCase):
    def _cloud_env(self, **overrides: str) -> dict[str, str]:
        env = {
            "ARGOS_WA_TRANSPORT": "cloud",
            "META_WA_ACCESS_TOKEN": "local-test-token",
            "META_WA_PHONE_NUMBER_ID": "123",
            "META_WA_WABA_ID": "456",
            "META_WA_WEBHOOK_VERIFY_TOKEN": "verify-local",
            "META_APP_SECRET": "secret-local",
            "ARGOS_WA_WEBHOOK_PUBLIC_URL": "https://example.invalid/webhooks/whatsapp",
        }
        env.update(overrides)
        return env

    def test_cloud_mode_does_not_require_localauth_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = SMOKE.SmokeReport("predeploy")
            transport, _ = SMOKE._transport_checks(report, self._cloud_env(), Path(tmp))
            self.assertEqual(transport, "cloud")
            self.assertTrue(report.ok)
            session = next(check for check in report.checks if check["name"] == "existing_wa_session")
            self.assertFalse(session["required"])

    def test_cloud_mode_requires_complete_meta_and_public_https_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = SMOKE.SmokeReport("predeploy")
            env = self._cloud_env(META_APP_SECRET="", ARGOS_WA_WEBHOOK_PUBLIC_URL="http://localhost/hook")
            SMOKE._transport_checks(report, env, Path(tmp))
            self.assertFalse(report.ok)
            failed = {c["name"] for c in report.checks if c["required"] and not c["ok"]}
            self.assertIn("cloud_required_env", failed)
            self.assertIn("cloud_public_webhook_https", failed)

    def test_wwebjs_mode_still_requires_existing_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = SMOKE.SmokeReport("predeploy")
            transport, _ = SMOKE._transport_checks(
                report,
                {"ARGOS_WA_TRANSPORT": "wwebjs"},
                Path(tmp),
            )
            self.assertEqual(transport, "wwebjs")
            self.assertFalse(report.ok)
            session = next(check for check in report.checks if check["name"] == "existing_wa_session")
            self.assertTrue(session["required"])
            self.assertFalse(session["ok"])

    def test_invalid_transport_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = SMOKE.SmokeReport("predeploy")
            SMOKE._transport_checks(report, {"ARGOS_WA_TRANSPORT": "unknown"}, Path(tmp))
            self.assertFalse(report.ok)
            supported = next(check for check in report.checks if check["name"] == "transport_supported")
            self.assertFalse(supported["ok"])


if __name__ == "__main__":
    unittest.main()
