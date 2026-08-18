"""ARGOS S292 demand-side workflow orchestrator.

This is the production parent for the vehicle sourcing path.  It deliberately
does not discover dealers, send Azzurra messages, or infer demand from dealer
profiles.  A caller must provide a traceable DemandEvidence first; only then can
candidate sourcing, CoVe verification, seller evidence and dossier readiness
run.

The module is dependency-injection friendly so the full workflow can be tested
offline without replacing the existing CoVe/seller/dossier implementations.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from src.cove.demand_contract import (
    ArgosScorecard,
    DemandEvidence,
    NOT_AVAILABLE,
    require_listing_authorization,
    require_sourcing_authorization,
)


class WorkflowStage(str, Enum):
    MANDATE_CONFIRMED = "MANDATE_CONFIRMED"
    CANDIDATE_MATCHED = "CANDIDATE_MATCHED"
    COVE_VERIFIED = "COVE_VERIFIED"
    SELLER_EVIDENCE_PENDING = "SELLER_EVIDENCE_PENDING"
    DOSSIER_REVIEW = "DOSSIER_REVIEW"
    DOSSIER_READY = "DOSSIER_READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Candidate:
    listing_id: str
    make: str
    model: str
    year: int
    km: int
    price_eur: float
    vin: Optional[str] = None
    source: str = NOT_AVAILABLE

    def __post_init__(self) -> None:
        if not str(self.listing_id or "").strip():
            raise ValueError("listing_id is required")
        if not str(self.make or "").strip() or not str(self.model or "").strip():
            raise ValueError("candidate make/model are required")
        if int(self.year) <= 0:
            raise ValueError("candidate year must be positive")
        if int(self.km) < 0:
            raise ValueError("candidate km cannot be negative")
        if float(self.price_eur) <= 0:
            raise ValueError("candidate price_eur must be positive")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Candidate":
        return cls(
            listing_id=str(value.get("listing_id") or ""),
            make=str(value.get("make") or value.get("marca") or ""),
            model=str(value.get("model") or value.get("modello") or ""),
            year=int(value.get("year") or value.get("anno") or 0),
            km=int(value.get("km") if value.get("km") is not None else value.get("mileage") or 0),
            price_eur=float(value.get("price_eur") if value.get("price_eur") is not None else value.get("price") or 0),
            vin=(str(value.get("vin")).strip() if value.get("vin") else None),
            source=str(value.get("source") or NOT_AVAILABLE),
        )


@dataclass(frozen=True)
class WorkflowDecision:
    dealer_id: str
    listing_id: str
    stage: WorkflowStage
    allowed: bool
    reason: str
    scorecard: Mapping[str, Any] = field(default_factory=dict)
    details: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


class AuditLedger:
    """Append-only hash-chained JSONL ledger for workflow decisions.

    The ledger is optional; when enabled it makes decisions reviewable without
    becoming a CRM or source of business truth.  Evidence remains in the
    upstream system referenced by ``evidence_id``.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "GENESIS"
        with self.path.open("rb") as handle:
            try:
                handle.seek(-min(self.path.stat().st_size, 65536), os.SEEK_END)
            except OSError:
                handle.seek(0)
            lines = [line for line in handle.read().splitlines() if line.strip()]
        if not lines:
            return "GENESIS"
        try:
            return str(json.loads(lines[-1].decode("utf-8"))["event_hash"])
        except (KeyError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("ARGOS audit ledger is corrupt; refusing to append") from exc

    def append(self, decision: WorkflowDecision) -> str:
        previous_hash = self._last_hash()
        payload = decision.to_dict()
        payload["previous_hash"] = previous_hash
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        payload["event_hash"] = event_hash
        line = json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
        fd = os.open(self.path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        return event_hash


_STRING_REQUEST_KEYS = {
    "make": ("make", "marca"),
    "model": ("model", "modello"),
}
_NUMERIC_REQUEST_KEYS = {
    "year_min": ("year_min", "anno_min"),
    "year_max": ("year_max", "anno_max"),
    "km_max": ("km_max", "mileage_max"),
    "budget_max_eur": ("budget_max_eur", "price_max", "price_max_eur"),
}


def _request_value(request: Mapping[str, Any], aliases: Sequence[str]) -> Any:
    for key in aliases:
        value = request.get(key)
        if value not in (None, "", NOT_AVAILABLE, "DA_VERIFICARE"):
            return value
    return None


def candidate_matches_request(candidate: Candidate, request: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Evaluate only explicit dealer criteria; absent criteria are not invented."""
    mismatches: list[str] = []
    make = _request_value(request, _STRING_REQUEST_KEYS["make"])
    model = _request_value(request, _STRING_REQUEST_KEYS["model"])
    if make and str(make).strip().casefold() != candidate.make.strip().casefold():
        mismatches.append("make")
    if model and str(model).strip().casefold() not in candidate.model.strip().casefold():
        mismatches.append("model")

    year_min = _request_value(request, _NUMERIC_REQUEST_KEYS["year_min"])
    year_max = _request_value(request, _NUMERIC_REQUEST_KEYS["year_max"])
    km_max = _request_value(request, _NUMERIC_REQUEST_KEYS["km_max"])
    budget = _request_value(request, _NUMERIC_REQUEST_KEYS["budget_max_eur"])
    try:
        if year_min is not None and candidate.year < int(year_min):
            mismatches.append("year_min")
        if year_max is not None and candidate.year > int(year_max):
            mismatches.append("year_max")
        if km_max is not None and candidate.km > int(km_max):
            mismatches.append("km_max")
        if budget is not None and candidate.price_eur > float(budget):
            mismatches.append("budget_max_eur")
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid numeric criterion in vehicle_request") from exc

    listing_id = _request_value(request, ("listing_id",))
    if listing_id and str(listing_id).strip() != candidate.listing_id:
        mismatches.append("listing_id")
    return not mismatches, mismatches


class DemandSideOrchestrator:
    """Canonical S292 parent workflow.

    External side effects are explicit methods.  Merely constructing or
    evaluating a candidate never contacts a dealer or seller.
    """

    def __init__(
        self,
        *,
        cove_analyzer: Optional[Callable[[Candidate], Any]] = None,
        dossier_checker: Optional[Callable[..., Any]] = None,
        seller_contact: Optional[Callable[..., Any]] = None,
        ledger: Optional[AuditLedger] = None,
    ) -> None:
        self._cove_analyzer = cove_analyzer
        self._dossier_checker = dossier_checker
        self._seller_contact = seller_contact
        self._ledger = ledger

    def _record(self, decision: WorkflowDecision) -> WorkflowDecision:
        if self._ledger:
            self._ledger.append(decision)
        return decision

    def authorize_mandate(self, evidence: DemandEvidence) -> WorkflowDecision:
        try:
            authorized = require_sourcing_authorization(evidence)
        except (PermissionError, TypeError, ValueError) as exc:
            return self._record(
                WorkflowDecision(
                    dealer_id=getattr(evidence, "dealer_id", NOT_AVAILABLE),
                    listing_id=str(getattr(evidence, "vehicle_request", {}).get("listing_id") or NOT_AVAILABLE),
                    stage=WorkflowStage.BLOCKED,
                    allowed=False,
                    reason=str(exc),
                )
            )
        return self._record(
            WorkflowDecision(
                dealer_id=authorized.dealer_id,
                listing_id=str(authorized.vehicle_request.get("listing_id") or NOT_AVAILABLE),
                stage=WorkflowStage.MANDATE_CONFIRMED,
                allowed=True,
                reason="S292_GATE: verified dealer commission",
                scorecard=ArgosScorecard(mandate_confidence=1.0).as_dict(display_missing=True),
                details={"evidence_id": authorized.evidence_id, "source": authorized.source},
            )
        )

    def evaluate_candidate(self, evidence: DemandEvidence, candidate: Candidate) -> WorkflowDecision:
        require_listing_authorization(evidence, candidate.listing_id)
        matches, mismatches = candidate_matches_request(candidate, evidence.vehicle_request)
        if not matches:
            return self._record(
                WorkflowDecision(
                    dealer_id=evidence.dealer_id,
                    listing_id=candidate.listing_id,
                    stage=WorkflowStage.BLOCKED,
                    allowed=False,
                    reason="candidate does not match commissioned request",
                    details={"mismatches": mismatches, "evidence_id": evidence.evidence_id},
                )
            )
        return self._record(
            WorkflowDecision(
                dealer_id=evidence.dealer_id,
                listing_id=candidate.listing_id,
                stage=WorkflowStage.CANDIDATE_MATCHED,
                allowed=True,
                reason="candidate matches explicit commissioned criteria",
                scorecard=ArgosScorecard(mandate_confidence=1.0).as_dict(display_missing=True),
                details={"evidence_id": evidence.evidence_id},
            )
        )

    def verify_cove(self, evidence: DemandEvidence, candidate: Candidate) -> tuple[WorkflowDecision, Any]:
        matched = self.evaluate_candidate(evidence, candidate)
        if not matched.allowed:
            return matched, None

        if self._cove_analyzer is not None:
            result = self._cove_analyzer(candidate)
        else:
            from src.cove.cove_engine_v4 import CoVeEngine, Listing

            result = CoVeEngine().analyze(
                Listing(
                    listing_id=candidate.listing_id,
                    make=candidate.make,
                    model=candidate.model,
                    year=candidate.year,
                    km=candidate.km,
                    price=candidate.price_eur,
                    vin=candidate.vin,
                    source=candidate.source,
                )
            )

        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        confidence = data.get("confidence")
        cove_confidence = None
        try:
            if confidence is not None:
                cove_confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            cove_confidence = None

        recommendation = str(data.get("recommendation") or data.get("status") or NOT_AVAILABLE).upper()
        allowed = recommendation in {"PROCEED", "VIN_CHECK"}
        decision = WorkflowDecision(
            dealer_id=evidence.dealer_id,
            listing_id=candidate.listing_id,
            stage=WorkflowStage.COVE_VERIFIED if allowed else WorkflowStage.BLOCKED,
            allowed=allowed,
            reason=f"CoVe recommendation={recommendation}",
            scorecard=ArgosScorecard(
                mandate_confidence=1.0,
                cove_confidence=cove_confidence,
            ).as_dict(display_missing=True),
            details={
                "evidence_id": evidence.evidence_id,
                "cove_recommendation": recommendation,
                "cove_uncertainty": data.get("uncertainty_budget", NOT_AVAILABLE),
            },
        )
        return self._record(decision), result

    def request_seller_evidence(
        self,
        evidence: DemandEvidence,
        listing_id: str,
        *,
        db_path: Optional[str] = None,
        dry_run: bool = True,
    ) -> tuple[WorkflowDecision, Any]:
        require_listing_authorization(evidence, listing_id)
        if self._seller_contact is not None:
            result = self._seller_contact(
                listing_id,
                db_path=db_path,
                dry_run=dry_run,
                evidence=evidence,
            )
        else:
            from src.cove.seller_contact import request_missing_data

            result = request_missing_data(
                listing_id,
                db_path=db_path,
                dry_run=dry_run,
                evidence=evidence,
            )
        send_result = result.get("send_result", {}) if isinstance(result, Mapping) else {}
        complete = bool(result.get("complete")) if isinstance(result, Mapping) else False
        allowed = complete or bool(send_result.get("sent") or send_result.get("dry_run"))
        decision = WorkflowDecision(
            dealer_id=evidence.dealer_id,
            listing_id=listing_id,
            stage=WorkflowStage.SELLER_EVIDENCE_PENDING,
            allowed=allowed,
            reason="seller evidence request prepared" if dry_run else "seller evidence request attempted",
            details={
                "dry_run": dry_run,
                "sent": bool(send_result.get("sent")),
                "evidence_id": evidence.evidence_id,
            },
        )
        return self._record(decision), result

    def dossier_readiness(
        self,
        evidence: DemandEvidence,
        listing_id: str,
        *,
        db_path: Optional[str] = None,
        economics: Optional[Mapping[str, Any]] = None,
    ) -> tuple[WorkflowDecision, Any]:
        require_listing_authorization(evidence, listing_id)
        if self._dossier_checker is not None:
            result = self._dossier_checker(
                listing_id,
                db_path=db_path,
                demand_evidence=evidence,
                economics=economics,
            )
        else:
            from src.cove.dossier_standard import check_dossier_readiness

            result = check_dossier_readiness(
                listing_id,
                db_path=db_path,
                demand_evidence=evidence,
                economics=economics,
            )
        ready = bool(getattr(result, "ready", False))
        readiness = getattr(result, "dossier_readiness", None)
        decision = WorkflowDecision(
            dealer_id=evidence.dealer_id,
            listing_id=listing_id,
            stage=WorkflowStage.DOSSIER_READY if ready else WorkflowStage.DOSSIER_REVIEW,
            allowed=ready,
            reason="dossier evidence complete" if ready else "dossier not yet dealer-ready",
            scorecard=ArgosScorecard(
                mandate_confidence=1.0,
                dossier_readiness=readiness,
            ).as_dict(display_missing=True),
            details={
                "evidence_id": evidence.evidence_id,
                "next_action": getattr(result, "next_action", NOT_AVAILABLE),
                "missing_mandatory": getattr(result, "missing_mandatory", []),
                "missing_important": getattr(result, "missing_important", []),
            },
        )
        return self._record(decision), result
