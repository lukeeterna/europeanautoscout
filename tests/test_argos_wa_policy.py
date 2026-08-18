"""Offline integration tests for Azzurra/FSM/S292 outbound policy.

The tests use a temporary SQLite database and never contact WhatsApp, Telegram,
OpenRouter or a dealer.  They verify that natural-language intent detection may
enter demand discovery but cannot create a sourcing mandate by itself.
"""
from __future__ import annotations

import importlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from src.cove.demand_contract import DemandEvidence


WA_DIR = Path(__file__).resolve().parents[1] / "wa-intelligence"
if str(WA_DIR) not in sys.path:
    sys.path.insert(0, str(WA_DIR))

state_machine = importlib.import_module("state_machine")
templates = importlib.import_module("templates")
policy = importlib.import_module("s292_outbound_policy")


class WhatsAppS292PolicyTests(unittest.TestCase):
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
                    current_step TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    dealer_id TEXT,
                    direction TEXT,
                    body TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO conversations (
                    dealer_id, dealer_name, phone_number, current_step
                ) VALUES ('dealer-1', 'Dealer Uno', '+390000000001', 'CONTACTED');
                """
            )
            con.commit()
        finally:
            con.close()
        state_machine.ensure_state_columns(self.db_path)
        state_machine.update_state(self.db_path, "dealer-1", "CONTACTED")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def evidence(self, **overrides) -> DemandEvidence:
        data = dict(
            dealer_id="dealer-1",
            credibility_established=True,
            dealer_commissioned_vehicle=True,
            live_demand=True,
            source="whatsapp_inbound",
            evidence_id="msg-in-001",
            observed_at="2026-08-18T08:00:00+00:00",
            vehicle_request={
                "make": "BMW",
                "model": "X3",
                "year_min": 2019,
                "year_max": 2023,
                "budget_max_eur": 45000,
            },
        )
        data.update(overrides)
        return DemandEvidence(**data)

    def dealer_state(self) -> dict:
        return state_machine.get_dealer_state(self.db_path, "dealer-1")

    def test_vehicle_request_enters_discovery_not_mandate(self) -> None:
        new_state = state_machine.process_inbound(
            self.db_path, "dealer-1", "VEHICLE_REQUEST"
        )
        self.assertEqual(new_state, "DEMAND_DISCOVERY")
        row = self.dealer_state()
        self.assertEqual(row["conversation_state"], "DEMAND_DISCOVERY")
        self.assertIsNone(row.get("demand_evidence_id"))
        self.assertIsNone(state_machine.get_verified_mandate(self.db_path, "dealer-1"))

    def test_demand_discovery_selects_ack_not_vehicle_offer(self) -> None:
        state_machine.process_inbound(self.db_path, "dealer-1", "VEHICLE_REQUEST")
        template_id = templates.select_template(
            "VEHICLE_REQUEST", "DEMAND_DISCOVERY"
        )
        self.assertEqual(template_id, "VEHICLE_REQUEST_ACK")
        message = templates.fill_template(
            template_id,
            {"request_summary": "BMW X3, 2019-2023, budget massimo EUR 45.000"},
        )
        self.assertIn("Ho registrato questa richiesta", message)
        self.assertIn("Non le sto promettendo una disponibilità", message)
        ok, reason = state_machine.can_send(
            self.db_path, "dealer-1", "VEHICLE_REQUEST_ACK"
        )
        self.assertTrue(ok, reason)

    def test_request_ack_fails_closed_without_request_summary(self) -> None:
        self.assertEqual(
            templates.fill_template("VEHICLE_REQUEST_ACK", {}),
            "",
        )

    def test_vehicle_offer_is_blocked_during_discovery(self) -> None:
        state_machine.process_inbound(self.db_path, "dealer-1", "VEHICLE_REQUEST")
        ok, reason = state_machine.can_send(
            self.db_path, "dealer-1", "VEHICLE_PROPOSAL"
        )
        self.assertFalse(ok)
        self.assertIn("TEMPLATE_NOT_ALLOWED", reason)

        result = policy.evaluate_outbound_policy(
            dealer_state=self.dealer_state(),
            template_id="VEHICLE_PROPOSAL",
            message="BMW X3 disponibile.",
        )
        self.assertFalse(result.ok)
        self.assertIn("S292_GATE", result.reason)

    def test_classifier_positive_does_not_promote_discovery_to_mandate(self) -> None:
        state_machine.process_inbound(self.db_path, "dealer-1", "VEHICLE_REQUEST")
        state_machine.process_inbound(self.db_path, "dealer-1", "POSITIVE")
        self.assertEqual(
            self.dealer_state()["conversation_state"],
            "DEMAND_DISCOVERY",
        )

    def test_verified_commission_is_only_path_to_mandate_confirmed(self) -> None:
        state_machine.process_inbound(self.db_path, "dealer-1", "VEHICLE_REQUEST")
        evidence = self.evidence()
        persisted = state_machine.record_verified_mandate(
            self.db_path, "dealer-1", evidence
        )
        self.assertEqual(persisted.evidence_id, "msg-in-001")
        row = self.dealer_state()
        self.assertEqual(row["conversation_state"], "MANDATE_CONFIRMED")
        self.assertEqual(row["demand_evidence_id"], "msg-in-001")
        reloaded = state_machine.get_verified_mandate(
            self.db_path, "dealer-1"
        )
        self.assertIsNotNone(reloaded)
        self.assertTrue(reloaded.sourcing_authorized)

    def test_unverified_or_empty_commission_cannot_create_mandate(self) -> None:
        evidence = self.evidence(
            dealer_commissioned_vehicle=False,
            vehicle_request={},
        )
        with self.assertRaises(PermissionError):
            state_machine.record_verified_mandate(
                self.db_path, "dealer-1", evidence
            )
        self.assertNotEqual(
            self.dealer_state()["conversation_state"],
            "MANDATE_CONFIRMED",
        )

    def test_vehicle_offer_policy_allows_only_after_verified_mandate(self) -> None:
        state_machine.process_inbound(self.db_path, "dealer-1", "VEHICLE_REQUEST")
        state_machine.record_verified_mandate(
            self.db_path, "dealer-1", self.evidence()
        )
        result = policy.evaluate_outbound_policy(
            dealer_state=self.dealer_state(),
            template_id="VEHICLE_PROPOSAL",
            message=(
                "Dealer Uno, ho un candidato coerente con la richiesta che ci ha affidato. "
                "I dettagli verificati sono disponibili nel dossier."
            ),
        )
        self.assertTrue(result.ok, result.reason)

    def test_unverified_certification_claim_is_blocked_even_after_mandate(self) -> None:
        state_machine.record_verified_mandate(
            self.db_path, "dealer-1", self.evidence()
        )
        result = policy.evaluate_outbound_policy(
            dealer_state=self.dealer_state(),
            template_id="VEHICLE_PROPOSAL",
            message="BMW X3 con km certificati dalla revisione TUV.",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "UNVERIFIED_CERTAINTY")

    def test_legacy_mystery_shopper_handoff_is_blocked(self) -> None:
        row = self.dealer_state()
        row["handoff_source"] = "mystery_shopper"
        result = policy.evaluate_outbound_policy(
            dealer_state=row,
            template_id="IDENTITY_RESPONSE",
            message="Sono Azzurra, assistente di Luca.",
        )
        self.assertFalse(result.ok)
        self.assertIn("UNVERIFIED_HANDOFF_SOURCE", result.reason)
        self.assertFalse(
            state_machine.set_handoff_source(
                self.db_path, "dealer-1", "mystery_shopper"
            )
        )

    def test_vehicle_first_day1_is_retired_and_vehicle_argument_is_ignored(self) -> None:
        self.assertEqual(
            templates.fill_template(
                "DAY1_VEHICLE_FIRST",
                {"vehicle_brand": "BMW", "price_eur": "31.000"},
            ),
            "",
        )
        cold = templates.generate_cold_day1(
            ["BMW"],
            "sito pubblico",
            vehicle={
                "brand": "BMW",
                "model": "X3",
                "year": 2022,
                "price_eur": 31000,
            },
        )
        self.assertNotIn("31.000", cold)
        self.assertNotIn("X3", cold)
        self.assertIn("richieste", cold.lower())


if __name__ == "__main__":
    unittest.main()
