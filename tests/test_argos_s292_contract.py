"""Production contract tests for ARGOS S292 canonicalization.

These tests are deliberately offline: no dealer contact, no network, no live DB.
They protect the business invariants that must remain true across C1-C9.
"""
from __future__ import annotations

import unittest

from src.cove.demand_contract import (
    ArgosScorecard,
    DemandEvidence,
    NOT_AVAILABLE,
    UNKNOWN,
    mandate_confidence_from_evidence,
    require_listing_authorization,
    require_sourcing_authorization,
)
from src.cove.dossier_standard import (
    NO_VERDICT,
    _extract_confirmed_availability,
    _normalise_economics,
)


class DemandEvidenceContractTests(unittest.TestCase):
    def _reply(self, **overrides):
        payload = dict(
            dealer_id="dealer-42",
            credibility_established=True,
            source="whatsapp_inbound",
            evidence_id="msg-001",
            observed_at="2026-08-18T08:00:00+00:00",
        )
        payload.update(overrides)
        return DemandEvidence(**payload)

    def test_profile_or_crm_guess_never_becomes_direct_evidence(self):
        evidence = DemandEvidence(
            dealer_id="dealer-42",
            credibility_established=True,
            live_demand=True,
            segmenti_richiesti=["Porsche Macan"],
        )
        self.assertFalse(evidence.has_verifiable_evidence)
        self.assertFalse(evidence.sourcing_authorized)
        self.assertEqual(
            evidence.normalized_claims(),
            {
                "lavora_su_mandato": UNKNOWN,
                "accesso_clienti_altospendenti": UNKNOWN,
                "segmenti_richiesti": UNKNOWN,
                "live_demand": UNKNOWN,
            },
        )

    def test_verified_reply_is_evidence_but_not_automatically_a_mandate(self):
        evidence = self._reply(live_demand=False, segmenti_richiesti="SUV premium")
        self.assertTrue(evidence.has_verifiable_evidence)
        self.assertTrue(evidence.is_direct)
        self.assertFalse(evidence.sourcing_authorized)
        self.assertEqual(evidence.normalized_claims()["live_demand"], False)
        self.assertEqual(evidence.normalized_claims()["segmenti_richiesti"], "SUV premium")
        self.assertIsNone(mandate_confidence_from_evidence(evidence))
        with self.assertRaises(PermissionError):
            require_sourcing_authorization(evidence)

    def test_commission_without_vehicle_request_fails_closed(self):
        evidence = self._reply(dealer_commissioned_vehicle=True)
        self.assertFalse(evidence.sourcing_authorized)
        with self.assertRaisesRegex(PermissionError, "vehicle request is empty"):
            require_sourcing_authorization(evidence)

    def test_full_traceable_commission_authorizes_sourcing(self):
        evidence = self._reply(
            dealer_commissioned_vehicle=True,
            live_demand=True,
            vehicle_request={
                "make": "Porsche",
                "model": "Macan",
                "year_min": 2019,
                "year_max": 2023,
                "budget_max_eur": 65000,
            },
        )
        self.assertTrue(evidence.sourcing_authorized)
        self.assertIs(require_sourcing_authorization(evidence), evidence)
        self.assertEqual(mandate_confidence_from_evidence(evidence), 1.0)

    def test_listing_bound_evidence_cannot_be_reused_for_other_vehicle(self):
        evidence = self._reply(
            dealer_commissioned_vehicle=True,
            vehicle_request={"listing_id": "listing-A"},
        )
        self.assertIs(require_listing_authorization(evidence, "listing-A"), evidence)
        with self.assertRaisesRegex(PermissionError, "listing-A"):
            require_listing_authorization(evidence, "listing-B")

    def test_mapping_adapter_rejects_non_mapping_vehicle_request(self):
        with self.assertRaises(TypeError):
            DemandEvidence.from_mapping(
                {
                    "dealer_id": "dealer-42",
                    "vehicle_request": "Porsche Macan",
                }
            )

    def test_scorecard_never_fills_missing_dimensions(self):
        scorecard = ArgosScorecard(dealer_fit=0.8, mandate_confidence=1.0)
        raw = scorecard.as_dict()
        display = scorecard.as_dict(display_missing=True)
        self.assertEqual(raw["dealer_fit"], 0.8)
        self.assertIsNone(raw["cove_confidence"])
        self.assertEqual(display["cove_confidence"], NOT_AVAILABLE)
        self.assertEqual(display["deal_economics"], NOT_AVAILABLE)

    def test_scorecard_rejects_out_of_range_dimension(self):
        with self.assertRaises(ValueError):
            ArgosScorecard(dealer_fit=1.01)


class DossierTruthfulnessTests(unittest.TestCase):
    def test_missing_economics_is_no_verdict_not_zero_margin(self):
        result = _normalise_economics(None)
        self.assertEqual(result["verdict"], NO_VERDICT)
        self.assertIsNone(result["net_margin_eur"])

    def test_economics_requires_traceable_source_and_evidence_id(self):
        result = _normalise_economics({"net_margin_eur": 4200})
        self.assertEqual(result["verdict"], NO_VERDICT)
        self.assertIsNone(result["net_margin_eur"])

        traced = _normalise_economics(
            {
                "net_margin_eur": 4200,
                "source": "deal-economics-v1",
                "evidence_id": "econ-123",
                "verdict": "PROCEED",
            }
        )
        self.assertEqual(traced["net_margin_eur"], 4200.0)
        self.assertEqual(traced["verdict"], "PROCEED")

    def test_contact_sent_is_not_seller_availability_confirmation(self):
        legacy_row = {
            "seller_contact_sent_at": "2026-08-18T08:00:00Z",
            "seller_followup_count": 2,
        }
        self.assertFalse(_extract_confirmed_availability(legacy_row))

    def test_only_explicit_availability_confirmation_counts(self):
        self.assertTrue(
            _extract_confirmed_availability(
                {"seller_confirmed_available": True}
            )
        )
        self.assertTrue(
            _extract_confirmed_availability(
                {"availability_status": "AVAILABLE_CONFIRMED"}
            )
        )
        self.assertFalse(
            _extract_confirmed_availability(
                {"availability_status": "UNKNOWN"}
            )
        )


if __name__ == "__main__":
    unittest.main()
