"""ARGOS semantic photo-coverage contract.

A photo count is not evidence that a required view exists.  This module is the
single source of truth for vehicle-image view labels used by seller-contact and
dossier readiness.  Existing unlabelled images remain useful assets, but they
do not satisfy semantic coverage until a traceable view observation is stored.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set, Tuple

from src.cove.demand_contract import NOT_AVAILABLE


MANDATORY_VIEWS: tuple[str, ...] = (
    "front",
    "rear",
    "side_left",
    "side_right",
    "front_three_quarter",
    "rear_three_quarter",
    "interior_front",
    "dashboard",
)

DEALER_READY_VIEWS: tuple[str, ...] = MANDATORY_VIEWS + (
    "interior_rear",
    "trunk",
    "engine",
    "wheels_front",
)

EXTENDED_VIEWS: tuple[str, ...] = DEALER_READY_VIEWS + (
    "wheels_rear",
    "underbody",
    "infotainment",
    "service_book",
    "hu_report",
    "damage_detail",
)

VIEW_DESCRIPTIONS: Dict[str, str] = {
    "front": "Front view — full vehicle",
    "rear": "Rear view — full vehicle",
    "side_left": "Left side profile",
    "side_right": "Right side profile",
    "front_three_quarter": "Front three-quarter view",
    "rear_three_quarter": "Rear three-quarter view",
    "interior_front": "Front cabin / seats / centre console",
    "interior_rear": "Rear seats",
    "dashboard": "Dashboard with odometer visible",
    "infotainment": "Infotainment screen",
    "trunk": "Boot / cargo area",
    "engine": "Engine bay",
    "wheels_front": "Front wheel/tyre close-up",
    "wheels_rear": "Rear wheel/tyre close-up",
    "service_book": "Relevant service-history documentation",
    "hu_report": "HU/TÜV documentation where applicable",
    "damage_detail": "Close-up of disclosed damage/repairs, if any",
    "underbody": "Underbody view, if available",
}

VIEW_ALIASES: Dict[str, str] = {
    "front_view": "front",
    "rear_view": "rear",
    "left_side": "side_left",
    "sideleft": "side_left",
    "right_side": "side_right",
    "sideright": "side_right",
    "front_3q": "front_three_quarter",
    "front_3_4": "front_three_quarter",
    "front_threequarter": "front_three_quarter",
    "rear_3q": "rear_three_quarter",
    "rear_3_4": "rear_three_quarter",
    "rear_threequarter": "rear_three_quarter",
    "cabin": "interior_front",
    "interior": "interior_front",
    "rear_seats": "interior_rear",
    "boot": "trunk",
    "cargo": "trunk",
    "engine_bay": "engine",
    "front_wheel": "wheels_front",
    "rear_wheel": "wheels_rear",
    "service_history": "service_book",
    "tuv_report": "hu_report",
    "tüv_report": "hu_report",
    "damage": "damage_detail",
}

_GENERIC_LABELS = {
    "listing",
    "photo",
    "image",
    "vehicle",
    "unknown",
    "other",
    "general",
    "gallery",
}

SEMANTIC_COLUMNS = {
    "semantic_view": "VARCHAR",
    "semantic_confidence": "DOUBLE",
    "semantic_source": "VARCHAR",
    "semantic_evidence_id": "VARCHAR",
}


def normalize_view(value: Any) -> Optional[str]:
    """Return canonical view or None; generic labels never count as semantics."""
    if value is None:
        return None
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not raw or raw in _GENERIC_LABELS:
        return None
    raw = VIEW_ALIASES.get(raw, raw)
    return raw if raw in set(EXTENDED_VIEWS) else None


def _table_columns(con: Any, table: str) -> Set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def ensure_photo_semantic_columns(con: Any) -> None:
    """Idempotently add semantic metadata to existing vehicle_images tables."""
    columns = _table_columns(con, "vehicle_images")
    if not columns:
        raise RuntimeError("vehicle_images table is missing")
    for name, sql_type in SEMANTIC_COLUMNS.items():
        if name not in columns:
            con.execute(f'ALTER TABLE vehicle_images ADD COLUMN "{name}" {sql_type}')


@dataclass(frozen=True)
class PhotoSemanticEvidence:
    image_id: int
    view: str
    source: str
    evidence_id: str
    confidence: Optional[float] = None

    def __post_init__(self) -> None:
        canonical = normalize_view(self.view)
        if canonical is None:
            raise ValueError(f"unsupported photo view: {self.view!r}")
        if int(self.image_id) <= 0:
            raise ValueError("image_id must be positive")
        source = str(self.source or "").strip()
        evidence_id = str(self.evidence_id or "").strip()
        if not source or not evidence_id:
            raise ValueError("photo semantic evidence requires source and evidence_id")
        confidence = self.confidence
        if confidence is not None:
            confidence = float(confidence)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("semantic confidence must be between 0 and 1")
        object.__setattr__(self, "view", canonical)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "evidence_id", evidence_id)
        object.__setattr__(self, "confidence", confidence)


def record_photo_semantics(con: Any, evidence: PhotoSemanticEvidence) -> None:
    """Persist a traceable view observation for an existing image row."""
    ensure_photo_semantic_columns(con)
    row = con.execute(
        "SELECT listing_id FROM vehicle_images WHERE id = ?", [evidence.image_id]
    ).fetchone()
    if not row:
        raise LookupError(f"vehicle image id {evidence.image_id} not found")
    con.execute(
        """UPDATE vehicle_images
           SET semantic_view = ?, semantic_confidence = ?,
               semantic_source = ?, semantic_evidence_id = ?
           WHERE id = ?""",
        [
            evidence.view,
            evidence.confidence,
            evidence.source,
            evidence.evidence_id,
            evidence.image_id,
        ],
    )


@dataclass(frozen=True)
class PhotoCoverage:
    listing_id: str
    image_count: int
    observed_views: tuple[str, ...]
    traceable_views: tuple[str, ...]
    missing_mandatory: tuple[str, ...]
    missing_dealer_ready: tuple[str, ...]
    semantics_available: bool
    evidence_by_view: Mapping[str, tuple[Mapping[str, Any], ...]] = field(default_factory=dict)

    @property
    def mandatory_complete(self) -> bool:
        return self.semantics_available and not self.missing_mandatory

    @property
    def dealer_ready_complete(self) -> bool:
        return self.semantics_available and not self.missing_dealer_ready

    def missing_with_descriptions(self, *, dealer_ready: bool = False) -> list[tuple[str, str]]:
        values = self.missing_dealer_ready if dealer_ready else self.missing_mandatory
        return [(view, VIEW_DESCRIPTIONS.get(view, view)) for view in values]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "image_count": self.image_count,
            "observed_views": list(self.observed_views),
            "traceable_views": list(self.traceable_views),
            "missing_mandatory": list(self.missing_mandatory),
            "missing_dealer_ready": list(self.missing_dealer_ready),
            "semantics_available": self.semantics_available,
            "mandatory_complete": self.mandatory_complete,
            "dealer_ready_complete": self.dealer_ready_complete,
            "evidence_by_view": {
                key: [dict(item) for item in values]
                for key, values in self.evidence_by_view.items()
            },
        }


def load_photo_coverage(
    con: Any,
    listing_id: str,
    *,
    min_confidence: float = 0.0,
) -> PhotoCoverage:
    """Load semantics without promoting raw image_type/listing labels to evidence.

    New rows should carry ``semantic_view`` + provenance.  For backward
    compatibility, an explicit recognised legacy view column may be observed,
    but only rows with semantic_source/evidence_id count as *traceable* views.
    Readiness currently uses observed recognised views; consumers can tighten to
    traceable-only without changing storage again.
    """
    listing_id = str(listing_id or "").strip()
    if not listing_id:
        raise ValueError("listing_id is required")
    if not 0.0 <= float(min_confidence) <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    columns = _table_columns(con, "vehicle_images")
    if "listing_id" not in columns:
        return PhotoCoverage(
            listing_id=listing_id,
            image_count=0,
            observed_views=(),
            traceable_views=(),
            missing_mandatory=tuple(MANDATORY_VIEWS),
            missing_dealer_ready=tuple(DEALER_READY_VIEWS),
            semantics_available=False,
        )

    view_columns = [
        name
        for name in ("semantic_view", "view", "view_type", "photo_view", "image_type")
        if name in columns
    ]
    select = ["id"] + view_columns
    for name in ("semantic_confidence", "semantic_source", "semantic_evidence_id"):
        if name in columns:
            select.append(name)
    projection = ", ".join(f'"{name}"' for name in select)
    rows = con.execute(
        f"SELECT {projection} FROM vehicle_images WHERE listing_id = ?", [listing_id]
    ).fetchall()
    index = {name: i for i, name in enumerate(select)}

    observed: Set[str] = set()
    traceable: Set[str] = set()
    evidence: Dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        chosen_view: Optional[str] = None
        for name in view_columns:
            chosen_view = normalize_view(row[index[name]])
            if chosen_view:
                break
        if not chosen_view:
            continue

        confidence = None
        if "semantic_confidence" in index and row[index["semantic_confidence"]] is not None:
            try:
                confidence = float(row[index["semantic_confidence"]])
            except (TypeError, ValueError):
                continue
            if not 0.0 <= confidence <= 1.0 or confidence < min_confidence:
                continue
        observed.add(chosen_view)

        source = (
            str(row[index["semantic_source"]]).strip()
            if "semantic_source" in index and row[index["semantic_source"]] is not None
            else ""
        )
        evidence_id = (
            str(row[index["semantic_evidence_id"]]).strip()
            if "semantic_evidence_id" in index and row[index["semantic_evidence_id"]] is not None
            else ""
        )
        if source and evidence_id:
            traceable.add(chosen_view)
            evidence.setdefault(chosen_view, []).append(
                {
                    "image_id": int(row[index["id"]]),
                    "source": source,
                    "evidence_id": evidence_id,
                    "confidence": confidence if confidence is not None else NOT_AVAILABLE,
                }
            )

    missing_mandatory = tuple(view for view in MANDATORY_VIEWS if view not in observed)
    missing_dealer_ready = tuple(view for view in DEALER_READY_VIEWS if view not in observed)
    frozen_evidence = {
        key: tuple(values)
        for key, values in evidence.items()
    }
    return PhotoCoverage(
        listing_id=listing_id,
        image_count=len(rows),
        observed_views=tuple(sorted(observed)),
        traceable_views=tuple(sorted(traceable)),
        missing_mandatory=missing_mandatory,
        missing_dealer_ready=missing_dealer_ready,
        semantics_available=bool(observed),
        evidence_by_view=frozen_evidence,
    )
