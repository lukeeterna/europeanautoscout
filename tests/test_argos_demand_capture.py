"""Offline tests for deterministic dealer demand capture."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WA_DIR = Path(__file__).resolve().parents[1] / "wa-intelligence"
if str(WA_DIR) not in sys.path:
    sys.path.insert(0, str(WA_DIR))

from demand_capture import capture_vehicle_request  # noqa: E402


class DemandCaptureTests(unittest.TestCase):
    def test_interest_is_discovery_not_commission(self):
        capture = capture_vehicle_request(
            "msg-1",
            "Sto cercando una BMW X3 dal 2020 al 2023, max 45 mila euro e 80 mila km.",
        )
        self.assertTrue(capture.is_vehicle_request)
        self.assertFalse(capture.explicit_commission)
        self.assertFalse(capture.authorization_ready)
        self.assertEqual(capture.criteria["make"], "BMW")
        self.assertIn("X3", capture.criteria["model"])
        self.assertEqual(capture.criteria["year_min"], 2020)
        self.assertEqual(capture.criteria["year_max"], 2023)
        self.assertEqual(capture.criteria["budget_max_eur"], 45000)
        self.assertEqual(capture.criteria["km_max"], 80000)

    def test_explicit_search_instruction_can_become_commission_evidence(self):
        capture = capture_vehicle_request(
            "msg-2",
            "Cercami una Porsche Macan 2021 o 2022, diesel, massimo 60k euro.",
        )
        self.assertTrue(capture.explicit_commission)
        self.assertTrue(capture.authorization_ready)
        evidence = capture.to_evidence(
            dealer_id="dealer-1",
            credibility_established=True,
        )
        self.assertTrue(evidence.sourcing_authorized)
        self.assertEqual(evidence.evidence_id, "msg-2")
        self.assertEqual(evidence.source, "whatsapp_inbound")
        self.assertEqual(evidence.vehicle_request["make"], "Porsche")
        self.assertEqual(evidence.vehicle_request["year_min"], 2021)
        self.assertEqual(evidence.vehicle_request["year_max"], 2022)
        self.assertEqual(evidence.vehicle_request["budget_max_eur"], 60000)

    def test_negated_request_never_authorizes(self):
        capture = capture_vehicle_request(
            "msg-3",
            "Non sto cercando BMW X3, grazie.",
        )
        self.assertFalse(capture.is_vehicle_request)
        self.assertFalse(capture.explicit_commission)
        self.assertFalse(capture.authorization_ready)

    def test_vehicle_mention_alone_is_not_commission(self):
        capture = capture_vehicle_request("msg-4", "BMW X3 bella macchina.")
        self.assertTrue(capture.is_vehicle_request)
        self.assertFalse(capture.explicit_commission)
        self.assertFalse(capture.authorization_ready)

    def test_model_only_explicit_instruction_can_authorize(self):
        capture = capture_vehicle_request("msg-5", "Trovami una Macan 2022 max 55k.")
        self.assertTrue(capture.authorization_ready)
        self.assertEqual(capture.criteria["model"].lower(), "macan")
        self.assertEqual(capture.criteria["budget_max_eur"], 55000)

    def test_missing_criteria_are_reported_without_invention(self):
        capture = capture_vehicle_request("msg-6", "Cerco una Audi Q5.")
        self.assertIn("year_range", capture.missing_for_search)
        self.assertIn("budget_max_eur", capture.missing_for_search)
        self.assertIn("km_max", capture.missing_for_search)
        self.assertNotIn("year_min", capture.criteria)
        self.assertNotIn("budget_max_eur", capture.criteria)

    def test_invalid_message_id_or_empty_body_is_rejected(self):
        with self.assertRaises(ValueError):
            capture_vehicle_request("", "Cerco BMW X3")
        with self.assertRaises(ValueError):
            capture_vehicle_request("msg-7", "   ")


if __name__ == "__main__":
    unittest.main()
