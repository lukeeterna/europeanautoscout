#!/usr/bin/env python3
"""ARGOS S292 dealer-delivery artifact boundary.

This is the production entrypoint for a dossier that may leave ARGOS.
``pdf_generator_enterprise.generate_dossier_from_db`` owns the evidence/readiness
rendering gate; this module adds the transport contract required by the
single-writer WhatsApp daemon.

A successful result always contains two files:
- the dealer-ready PDF;
- ``<pdf>.metadata.json`` with dealer/evidence/listing binding and exact PDF
  SHA-256.

A review PDF is never promoted here. Missing/invalid evidence or a failed
readiness gate propagates as an exception and no dealer-ready sidecar is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.cove.demand_contract import DemandEvidence, require_listing_authorization
from tools.scripts.pdf_generator_enterprise import generate_dossier_from_db


METADATA_VERSION = "argos-s292-delivery-v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_object(path_or_json: str) -> Mapping[str, Any]:
    value = str(path_or_json or "").strip()
    if not value:
        raise ValueError("JSON input is required")
    path = Path(value)
    raw = path.read_text(encoding="utf-8") if path.is_file() else value
    parsed = json.loads(raw)
    if not isinstance(parsed, Mapping):
        raise ValueError("JSON input must be an object")
    return parsed


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


@dataclass(frozen=True)
class DealerDeliveryArtifact:
    pdf_path: str
    metadata_path: str
    dealer_id: str
    evidence_id: str
    listing_id: str
    file_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "dealer_ready": True,
            "pdf_path": self.pdf_path,
            "metadata_path": self.metadata_path,
            "dealer_id": self.dealer_id,
            "evidence_id": self.evidence_id,
            "listing_id": self.listing_id,
            "file_sha256": self.file_sha256,
            "metadata_version": METADATA_VERSION,
        }


def build_delivery_metadata(
    *,
    pdf_path: str,
    listing_id: str,
    demand_evidence: DemandEvidence,
) -> dict[str, Any]:
    """Build metadata only for a real file and an authorized S292 mandate."""
    authorized = require_listing_authorization(demand_evidence, listing_id)
    path = Path(pdf_path).resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise FileNotFoundError(f"dealer-ready PDF missing or empty: {path}")
    file_sha = _sha256_file(path)
    return {
        "metadata_version": METADATA_VERSION,
        "dealer_ready": True,
        "dealer_id": authorized.dealer_id,
        "evidence_id": authorized.evidence_id,
        "evidence_source": authorized.source,
        "listing_id": str(listing_id),
        "pdf_filename": path.name,
        "file_sha256": file_sha,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def write_delivery_sidecar(
    *,
    pdf_path: str,
    listing_id: str,
    demand_evidence: DemandEvidence,
) -> DealerDeliveryArtifact:
    metadata = build_delivery_metadata(
        pdf_path=pdf_path,
        listing_id=listing_id,
        demand_evidence=demand_evidence,
    )
    pdf = Path(pdf_path).resolve()
    metadata_path = Path(str(pdf) + ".metadata.json")
    _atomic_write_json(metadata_path, metadata)

    # Read-back verification prevents a partial/corrupt sidecar from being
    # returned as transport-ready.
    persisted = json.loads(metadata_path.read_text(encoding="utf-8"))
    for key in ("dealer_ready", "dealer_id", "evidence_id", "listing_id", "file_sha256"):
        if persisted.get(key) != metadata.get(key):
            raise RuntimeError(f"delivery metadata verification failed: {key}")
    if _sha256_file(pdf) != persisted["file_sha256"]:
        raise RuntimeError("delivery metadata verification failed: PDF hash changed")

    return DealerDeliveryArtifact(
        pdf_path=str(pdf),
        metadata_path=str(metadata_path),
        dealer_id=str(metadata["dealer_id"]),
        evidence_id=str(metadata["evidence_id"]),
        listing_id=str(metadata["listing_id"]),
        file_sha256=str(metadata["file_sha256"]),
    )


def generate_dealer_delivery(
    *,
    listing_id: str,
    dealer_name: str,
    output_dir: str,
    db_path: Optional[str],
    demand_evidence: DemandEvidence,
    economics: Optional[Mapping[str, Any]] = None,
    dealer_company: Optional[str] = None,
    dealer_city: str = "n/d",
) -> DealerDeliveryArtifact:
    """Generate PDF and matching sidecar as the only production dossier path."""
    authorized = require_listing_authorization(demand_evidence, listing_id)
    pdf_path = generate_dossier_from_db(
        listing_id,
        dealer_name=dealer_name,
        dealer_company=dealer_company,
        dealer_city=dealer_city,
        output_dir=output_dir,
        db_path=db_path,
        demand_evidence=authorized,
        economics=economics,
        dealer_delivery=True,
    )
    return write_delivery_sidecar(
        pdf_path=pdf_path,
        listing_id=listing_id,
        demand_evidence=authorized,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARGOS S292 dealer-ready PDF + sidecar")
    parser.add_argument("--listing", required=True)
    parser.add_argument("--dealer", required=True)
    parser.add_argument("--company")
    parser.add_argument("--city", default="n/d")
    parser.add_argument("--output", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--evidence-json", required=True)
    parser.add_argument("--economics-json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        evidence = DemandEvidence.from_mapping(_load_object(args.evidence_json))
        economics = _load_object(args.economics_json) if args.economics_json else None
        artifact = generate_dealer_delivery(
            listing_id=args.listing,
            dealer_name=args.dealer,
            dealer_company=args.company,
            dealer_city=args.city,
            output_dir=args.output,
            db_path=args.db,
            demand_evidence=evidence,
            economics=economics,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(artifact.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
