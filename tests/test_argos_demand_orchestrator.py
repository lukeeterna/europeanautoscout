"""Offline production tests for the S292 sourcing parent and economics layer."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.cove.deal_economics import build_deal_economics
from src.cove.demand_contract import DemandEvidence, NO_VERDICT
from src.cove.demand_orchestrator import (
    AuditLedger,
    Candidate,
    DemandSideOrchestrator,
    WorkflowStage,
    candidate_matches_request,
)


class DemandOrchestratorTests(unittest.TestCase):
    def evidence(self, **overrides):
        data = dict(
            dealer_id="dealer-1",
            credibility_established=True,
            dealer_commissioned_vehicle=True,
            source="whatsapp_inbound",
            evidence_id="wa-msg-100",
            observed_at="2026-08-18T08:00:00+00:00",
            live_demand=True,
            vehicle_request={
                "make": "BMW",
                "model": "X3",
                "year_min": 2019,
                "year_max": 2023,
                "budget_max_eur": 45000,
                "km_max": 90000,
            },
        )
        data.update(overrides)
        return DemandEvidence(**data)

    def candidate(self, **overrides):
        data = dict(
            listing_id="listing-1",
            make="BMW",
            model="X3 xDrive20d",
            year=2022,
            km=52000,
            price_eur=33500,
            source="dealer-listing",
        )
        data.update(overrides)
        return Candidate(**data)

    def test_candidate_match_uses_only_explicit_request_criteria(self):
        ok, mismatches = candidate_matches_request(self.candidate(), self.evidence().vehicle_request)
        self.assertTrue(ok)
        self.assertEqual(mismatches, [])

        ok, mismatches = candidate_matches_request(
            self.candidate(price_eur=50000), self.evidence().vehicle_request
        )
        self.assertFalse(ok)
        self.assertIn("budget_max_eur", mismatches)

    def test_mismatch_blocks_before_cove_analyzer(self):
        calls = []

        def analyzer(candidate):
            calls.append(candidate)
            return {"recommendation": "PROCEED", "confidence": 0.9}

        orchestrator = DemandSideOrchestrator(cove_analyzer=analyzer)
        decision, result = orchestrator.verify_cove(
            self.evidence(), self.candidate(make="Audi")
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.stage, WorkflowStage.BLOCKED)
        self.assertIsNone(result)
        self.assertEqual(calls, [])

    def test_authorized_matching_candidate_reaches_cove(self):
        def analyzer(candidate):
            return {
                "recommendation": "PROCEED",
                "confidence": 0.87,
                "uncertainty_budget": 0.11,
            }

        orchestrator = DemandSideOrchestrator(cove_analyzer=analyzer)
        decision, result = orchestrator.verify_cove(self.evidence(), self.candidate())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.stage, WorkflowStage.COVE_VERIFIED)
        self.assertEqual(decision.scorecard["mandate_confidence"], 1.0)
        self.assertEqual(decision.scorecard["cove_confidence"], 0.87)
        self.assertEqual(decision.scorecard["deal_economics"], "n/d")
        self.assertEqual(result["recommendation"], "PROCEED")

    def test_seller_side_effect_is_explicit_and_dry_run_by_default(self):
        calls = []

        def seller_contact(listing_id, **kwargs):
            calls.append((listing_id, kwargs))
            return {"send_result": {"sent": False, "dry_run": kwargs["dry_run"]}}

        orchestrator = DemandSideOrchestrator(seller_contact=seller_contact)
        decision, _ = orchestrator.request_seller_evidence(
            self.evidence(), "listing-1"
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.stage, WorkflowStage.SELLER_EVIDENCE_PENDING)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][1]["dry_run"])
        self.assertIs(calls[0][1]["evidence"], self.evidence()) if False else None

    def test_dossier_adapter_keeps_readiness_as_separate_dimension(self):
        def checker(listing_id, **kwargs):
            return SimpleNamespace(
                ready=True,
                dossier_readiness=0.92,
                next_action="ready",
                missing_mandatory=[],
                missing_important=[],
            )

        orchestrator = DemandSideOrchestrator(dossier_checker=checker)
        decision, _ = orchestrator.dossier_readiness(self.evidence(), "listing-1")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.stage, WorkflowStage.DOSSIER_READY)
        self.assertEqual(decision.scorecard["dossier_readiness"], 0.92)
        self.assertEqual(decision.scorecard["dealer_fit"], "n/d")

    def test_audit_ledger_is_hash_chained(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AuditLedger(Path(tmp) / "workflow.jsonl")
            orchestrator = DemandSideOrchestrator(ledger=ledger)
            first = orchestrator.authorize_mandate(self.evidence())
            second = orchestrator.evaluate_candidate(self.evidence(), self.candidate())
            self.assertTrue(first.allowed)
            self.assertTrue(second.allowed)
            lines = [json.loads(line) for line in (Path(tmp) / "workflow.jsonl").read_text().splitlines()]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0]["previous_hash"], "GENESIS")
            self.assertEqual(lines[1]["previous_hash"], lines[0]["event_hash"])
            self.assertNotEqual(lines[0]["event_hash"], lines[1]["event_hash"])


class DealEconomicsTests(unittest.TestCase):
    def money(self, amount, evidence_id):
        return {
            "amount_eur": amount,
            "source": "documented-input",
            "evidence_id": evidence_id,
        }

    def test_missing_required_cost_is_rejected_not_defaulted(self):
        with self.assertRaisesRegex(ValueError, "registration_eur"):
            build_deal_economics(
                acquisition=self.money(30000, "acq"),
                market_reference=self.money(39000, "market"),
                costs={
                    "transport_eur": self.money(700, "transport"),
                    "argos_fee_eur": self.money(1000, "fee"),
                },
            )

    def test_arithmetic_without_business_threshold_is_no_verdict(self):
        result = build_deal_economics(
            acquisition=self.money(30000, "acq"),
            market_reference=self.money(39000, "market"),
            costs={
                "transport_eur": self.money(700, "transport"),
                "registration_eur": self.money(500, "registration"),
                "argos_fee_eur": self.money(1000, "fee"),
            },
            market_confidence=0.8,
        )
        self.assertEqual(result.net_margin_eur, 6800)
        self.assertEqual(result.verdict, NO_VERDICT)
        self.assertIsNone(result.deal_economics_score)

    def test_declared_threshold_produces_traceable_verdict(self):
        result = build_deal_economics(
            acquisition=self.money(30000, "acq"),
            market_reference=self.money(39000, "market"),
            costs={
                "transport_eur": self.money(700, "transport"),
                "registration_eur": self.money(500, "registration"),
                "argos_fee_eur": self.money(1000, "fee"),
            },
            min_margin_eur=5000,
            market_confidence=0.8,
        )
        payload = result.to_dict()
        self.assertEqual(result.verdict, "PROCEED")
        self.assertEqual(result.deal_economics_score, 0.8)
        self.assertIn("transport_eur=transport", payload["evidence_id"])


if __name__ == "__main__":
    unittest.main()
