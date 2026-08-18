"""Offline tests for semantic photo coverage and Second Brain demand separation."""
from __future__ import annotations

import unittest

from src.cove.demand_contract import DemandEvidence, UNKNOWN
from src.cove.photo_coverage import (
    DEALER_READY_VIEWS,
    MANDATORY_VIEWS,
    PhotoSemanticEvidence,
    normalize_view,
)
from src.cove.second_brain_contract import build_second_brain_context


class PhotoCoverageContractTests(unittest.TestCase):
    def test_generic_image_labels_never_count_as_semantic_views(self):
        for value in (None, "", "listing", "photo", "image", "unknown", "gallery"):
            self.assertIsNone(normalize_view(value))

    def test_known_aliases_are_normalized(self):
        self.assertEqual(normalize_view("front_3q"), "front_three_quarter")
        self.assertEqual(normalize_view("Rear Seats"), "interior_rear")
        self.assertEqual(normalize_view("engine-bay"), "engine")

    def test_photo_semantic_evidence_requires_provenance(self):
        with self.assertRaises(ValueError):
            PhotoSemanticEvidence(
                image_id=1,
                view="front",
                source="",
                evidence_id="classifier-1",
            )
        with self.assertRaises(ValueError):
            PhotoSemanticEvidence(
                image_id=1,
                view="not-a-view",
                source="human-labelled-import",
                evidence_id="label-1",
            )

    def test_mandatory_views_are_subset_of_dealer_ready_views(self):
        self.assertTrue(set(MANDATORY_VIEWS).issubset(set(DEALER_READY_VIEWS)))
        self.assertGreater(len(DEALER_READY_VIEWS), len(MANDATORY_VIEWS))


class SecondBrainBoundaryTests(unittest.TestCase):
    def artifact(self):
        return {
            "schema_version": "second-brain.v1",
            "synthesis": {
                "specializzazione_reale": {
                    "value": "marchi rilevati: BMW; segmento SUV",
                    "sources": ["https://dealer.example/"],
                },
                "marche": {"value": "BMW", "sources": ["https://dealer.example/"]},
                "segmenti": {"value": "SUV/crossover", "sources": ["https://dealer.example/"]},
                "fascia_prezzo": {"value": "EUR 25.000-EUR 45.000", "sources": ["https://dealer.example/"]},
                "registro_comunicativo": {"sintesi": {"value": "tecnico"}},
                "aggancio_specifico": {
                    "value": "mette in evidenza la garanzia",
                    "sources": ["https://dealer.example/"]
                },
            },
            "compatibility": {
                "dealer_crm": {"dealer_id": "dealer-1", "name": "Dealer Uno"},
                "on_demand_runner_search_params": {
                    "make": "BMW",
                    "price_max": 45000,
                    "year_min": "n/d",
                },
            },
        }

    def evidence(self, **overrides):
        values = dict(
            dealer_id="dealer-1",
            credibility_established=True,
            dealer_commissioned_vehicle=True,
            source="whatsapp_inbound",
            evidence_id="msg-10",
            live_demand=True,
            segmenti_richiesti=["BMW X3"],
            vehicle_request={"make": "BMW", "model": "X3", "budget_max_eur": 45000},
        )
        values.update(overrides)
        return DemandEvidence(**values)

    def test_profile_hint_does_not_become_demand_without_direct_evidence(self):
        context = build_second_brain_context(self.artifact())
        self.assertEqual(context.profile_observations["marche"], "BMW")
        self.assertEqual(context.non_authoritative_search_hint["make"], "BMW")
        self.assertFalse(context.sourcing_authorized)
        self.assertEqual(
            context.demand_claims,
            {
                "lavora_su_mandato": UNKNOWN,
                "accesso_clienti_altospendenti": UNKNOWN,
                "segmenti_richiesti": UNKNOWN,
                "live_demand": UNKNOWN,
            },
        )

    def test_verified_demand_is_kept_separate_from_profile(self):
        evidence = self.evidence()
        context = build_second_brain_context(
            self.artifact(), demand_evidence=evidence
        )
        self.assertTrue(context.sourcing_authorized)
        self.assertEqual(context.demand_claims["live_demand"], True)
        self.assertEqual(context.demand_claims["segmenti_richiesti"], ["BMW X3"])
        self.assertEqual(context.demand_evidence_id, "msg-10")
        self.assertEqual(context.non_authoritative_search_hint["make"], "BMW")

    def test_dealer_mismatch_fails_closed(self):
        with self.assertRaises(PermissionError):
            build_second_brain_context(
                self.artifact(),
                demand_evidence=self.evidence(dealer_id="dealer-2"),
            )

    def test_bad_schema_or_missing_dealer_id_is_rejected(self):
        bad = self.artifact()
        bad["schema_version"] = "other.v1"
        with self.assertRaises(ValueError):
            build_second_brain_context(bad)

        missing = self.artifact()
        missing["compatibility"]["dealer_crm"] = {}
        with self.assertRaises(ValueError):
            build_second_brain_context(missing)


if __name__ == "__main__":
    unittest.main()
