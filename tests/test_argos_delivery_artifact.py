"""Offline tests for the S292 dealer-delivery PDF sidecar contract."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.cove.demand_contract import DemandEvidence
from tools.scripts.argos_dealer_delivery import (
    METADATA_VERSION,
    build_delivery_metadata,
    write_delivery_sidecar,
)


class DealerDeliveryArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pdf = Path(self.tmp.name) / "dealer-ready.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\nARGOS-S292-TEST\n%%EOF\n")
        self.evidence = DemandEvidence(
            dealer_id="dealer-42",
            credibility_established=True,
            dealer_commissioned_vehicle=True,
            source="whatsapp_inbound",
            evidence_id="msg-4242",
            vehicle_request={
                "listing_id": "listing-42",
                "make": "BMW",
                "model": "X3",
            },
            observed_at="2026-08-18T16:00:00+00:00",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_metadata_matches_daemon_transport_contract(self):
        metadata = build_delivery_metadata(
            pdf_path=str(self.pdf),
            listing_id="listing-42",
            demand_evidence=self.evidence,
        )
        self.assertTrue(metadata["dealer_ready"])
        self.assertEqual(metadata["metadata_version"], METADATA_VERSION)
        self.assertEqual(metadata["dealer_id"], "dealer-42")
        self.assertEqual(metadata["evidence_id"], "msg-4242")
        self.assertEqual(metadata["listing_id"], "listing-42")
        self.assertEqual(
            metadata["file_sha256"],
            hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
        )

    def test_sidecar_is_written_next_to_pdf_and_read_back_verified(self):
        artifact = write_delivery_sidecar(
            pdf_path=str(self.pdf),
            listing_id="listing-42",
            demand_evidence=self.evidence,
        )
        sidecar = Path(artifact.metadata_path)
        self.assertEqual(sidecar, Path(str(self.pdf.resolve()) + ".metadata.json"))
        self.assertTrue(sidecar.is_file())
        persisted = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertTrue(persisted["dealer_ready"])
        self.assertEqual(persisted["dealer_id"], artifact.dealer_id)
        self.assertEqual(persisted["evidence_id"], artifact.evidence_id)
        self.assertEqual(persisted["file_sha256"], artifact.file_sha256)

    def test_uncommissioned_evidence_cannot_create_delivery_metadata(self):
        evidence = DemandEvidence(
            dealer_id="dealer-42",
            credibility_established=True,
            dealer_commissioned_vehicle=False,
            source="whatsapp_inbound",
            evidence_id="msg-interest-only",
            vehicle_request={"listing_id": "listing-42", "make": "BMW"},
        )
        with self.assertRaises(PermissionError):
            build_delivery_metadata(
                pdf_path=str(self.pdf),
                listing_id="listing-42",
                demand_evidence=evidence,
            )
        self.assertFalse(Path(str(self.pdf.resolve()) + ".metadata.json").exists())

    def test_listing_binding_cannot_be_reused(self):
        with self.assertRaises(PermissionError):
            write_delivery_sidecar(
                pdf_path=str(self.pdf),
                listing_id="listing-other",
                demand_evidence=self.evidence,
            )
        self.assertFalse(Path(str(self.pdf.resolve()) + ".metadata.json").exists())

    def test_missing_or_empty_pdf_cannot_be_signed(self):
        missing = Path(self.tmp.name) / "missing.pdf"
        with self.assertRaises(FileNotFoundError):
            build_delivery_metadata(
                pdf_path=str(missing),
                listing_id="listing-42",
                demand_evidence=self.evidence,
            )

        empty = Path(self.tmp.name) / "empty.pdf"
        empty.touch()
        with self.assertRaises(FileNotFoundError):
            build_delivery_metadata(
                pdf_path=str(empty),
                listing_id="listing-42",
                demand_evidence=self.evidence,
            )


if __name__ == "__main__":
    unittest.main()
