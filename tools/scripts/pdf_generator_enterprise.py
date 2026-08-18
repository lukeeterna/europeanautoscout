"""ARGOS Automotive — production dealer dossier renderer (S292/P1).

This module intentionally replaces the historical marketing-oriented PDF
builder with an evidence renderer.  Its contract is simple:

* missing facts render as ``n/d``;
* no fuel/transmission/colour/owner/location defaults;
* no +12/+15% market uplift and no fixed logistics/fee fallback;
* CoVe, Vehicle Grade, deal economics and dossier readiness stay independent;
* only images that passed ``src.cove.image_sanitizer`` may be embedded;
* seller/source identity is rendered only when ``source_dossier`` is supplied;
* dealer-delivery mode requires a traceable S292 mandate and DEALER_READY gate.

Review artifacts may still be generated before the final gate, but they are
visibly marked ``INTERNAL REVIEW — NOT DEALER READY`` and are not delivery
artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.cove.demand_contract import (
    DemandEvidence,
    NOT_AVAILABLE,
    NO_VERDICT,
    require_listing_authorization,
)
from src.cove.image_sanitizer import SENTINEL_SKIP_PROMO

try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


ND = NOT_AVAILABLE
_VALID_GRADES = {"A", "B", "C", "D", "E"}
_VALID_ECON_VERDICTS = {"PROCEED", "REVIEW", "REJECT", NO_VERDICT}


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        value = value.strip()
        return bool(value) and value not in {ND, NO_VERDICT, "DA_VERIFICARE", "UNKNOWN"}
    return True


def _safe_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else None


def _display(value: Any) -> str:
    if not _known(value):
        return ND
    if isinstance(value, bool):
        return "sì" if value else "no"
    return str(value)


def _eur(value: Any) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return ND
    sign = "-" if parsed < 0 else ""
    amount = f"{abs(int(round(parsed))):,}".replace(",", ".")
    return f"{sign}EUR {amount}"


def _pct(value: Any) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return ND
    return f"{parsed:.1%}"


def _sha_payload(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _load_json_object(path_or_json: Optional[str]) -> Optional[Mapping[str, Any]]:
    if not path_or_json:
        return None
    path = Path(path_or_json)
    if path.exists():
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = json.loads(path_or_json)
    if not isinstance(value, Mapping):
        raise ValueError("JSON input must be an object")
    return value


def _load_demand_evidence(path_or_json: Optional[str]) -> Optional[DemandEvidence]:
    value = _load_json_object(path_or_json)
    return DemandEvidence.from_mapping(value) if value is not None else None


def _table_columns(con: Any, table: str) -> set[str]:
    try:
        rows = con.execute(f"PRAGMA table_info('{table}')").fetchall()
    except Exception:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def _fetch_row(con: Any, table: str, listing_id: str) -> Dict[str, Any]:
    columns = _table_columns(con, table)
    if "listing_id" not in columns:
        return {}
    ordered = sorted(columns)
    projection = ", ".join(f'"{name}"' for name in ordered)
    order = " ORDER BY analyzed_at DESC" if table == "cove_results" and "analyzed_at" in columns else ""
    row = con.execute(
        f'SELECT {projection} FROM "{table}" WHERE listing_id = ?{order} LIMIT 1',
        [listing_id],
    ).fetchone()
    return dict(zip(ordered, row)) if row else {}


@dataclass
class VehicleData:
    """Truth-safe vehicle payload used by the PDF renderer.

    Required legacy constructor fields are retained for compatibility.  The
    value ``price_it_estimate`` may be None and has no default derivation.
    """

    make: str
    model: str
    year: int
    km: int
    price_eu: int
    price_it_estimate: Optional[int]
    confidence: float

    engine: str = ND
    fuel_type: str = ND
    transmission: str = ND
    color: str = ND
    doors: Optional[int] = None

    km_score: Optional[int] = None
    price_score: Optional[int] = None
    age_score: Optional[int] = None
    history_score: Optional[int] = None

    source_url: str = ""
    source_country: str = ND
    listing_date: str = ND

    vin: Optional[str] = None
    first_registration: Optional[str] = None
    last_service: Optional[str] = None
    previous_owners: Optional[int] = None

    local_image_paths: List[str] = field(default_factory=list)
    safe_images_verified: bool = False

    opportunity_score: Optional[int] = None
    discount_pct: Optional[float] = None
    market_ref_price: Optional[float] = None
    estimated_margin: Optional[float] = None
    risk_level: str = ND
    market_data_quality: str = ND
    market_sample_size: Optional[int] = None
    cove_status: str = ND
    portal: str = ""

    transport_cost: Optional[float] = None
    transport_method: str = ND
    transport_distance_km: Optional[int] = None
    transport_notes: str = ND
    import_cost_total_min: Optional[float] = None
    import_cost_total_max: Optional[float] = None
    import_days: Optional[int] = None

    margin_decision: str = NO_VERDICT
    chiavi_in_mano: Optional[float] = None
    spread_lordo: Optional[float] = None
    dealer_floor: Optional[float] = None
    surplus: Optional[float] = None
    fee_argos: Optional[float] = None
    margine_netto_dealer: Optional[float] = None
    margine_netto_pct: Optional[float] = None

    it_median: Optional[float] = None
    it_p25: Optional[float] = None
    it_p75: Optional[float] = None
    it_n: Optional[int] = None
    it_source: Optional[str] = None
    relaxation_level: Optional[int] = None
    no_verdict: bool = False
    it_band_low: Optional[float] = None
    it_band_high: Optional[float] = None
    it_confidence: Optional[str] = None
    it_width_nature: Optional[str] = None
    it_n_by_level: Optional[dict] = None
    it_scrape_date: Optional[str] = None
    it_is_floor: bool = False
    it_n_priced: Optional[int] = None
    it_pages_scraped: Optional[int] = None
    it_terminated_by_empty: bool = False
    margine_netto_low: Optional[float] = None
    margine_netto_high: Optional[float] = None
    country_code: str = ""
    fraud_doc_obtained: bool = False
    fallback_declared: bool = False

    deal_economics: Optional[Mapping[str, Any]] = None
    listing_id: str = ND

    def __post_init__(self) -> None:
        self.make = str(self.make or ND).strip() or ND
        self.model = str(self.model or ND).strip() or ND
        self.year = int(self.year) if _safe_int(self.year) is not None else 0
        self.km = int(self.km) if _safe_int(self.km) is not None else 0
        self.price_eu = int(self.price_eu) if _safe_int(self.price_eu) is not None else 0
        self.price_it_estimate = _safe_int(self.price_it_estimate)
        conf = _safe_float(self.confidence)
        self.confidence = conf if conf is not None and 0.0 <= conf <= 1.0 else 0.0
        self.margin_decision = str(self.margin_decision or NO_VERDICT).upper()
        if self.margin_decision not in {"PASS", "REJECT", "REVIEW", "CONDIZIONATO", NO_VERDICT}:
            self.margin_decision = NO_VERDICT

    @classmethod
    def from_opportunity(cls, opp: Any, dealer_city: str = ND) -> "VehicleData":
        """Adapt an Opportunity without calculating missing market/cost facts."""
        def attr(name: str, default: Any = None) -> Any:
            return getattr(opp, name, default)

        explicit_economics = attr("deal_economics")
        if explicit_economics is not None and not isinstance(explicit_economics, Mapping):
            explicit_economics = None

        return cls(
            make=str(attr("make") or ND),
            model=str(attr("model") or ND),
            year=_safe_int(attr("year")) or 0,
            km=_safe_int(attr("km")) or 0,
            price_eu=_safe_int(attr("price_eur")) or 0,
            price_it_estimate=_safe_int(attr("price_it_estimate")),
            confidence=_safe_float(attr("cove_confidence")) or 0.0,
            fuel_type=str(attr("fuel_type") or ND),
            transmission=str(attr("transmission") or ND),
            color=str(attr("color") or ND),
            vin=attr("vin"),
            listing_id=str(attr("listing_id") or ND),
            opportunity_score=_safe_int(attr("opportunity_score")),
            discount_pct=_safe_float(attr("discount_pct")),
            market_ref_price=_safe_float(attr("market_ref_price")),
            # Historical ``estimated_margin_eur`` is exposed only if an evidence
            # container accompanies it; otherwise it remains n/d.
            estimated_margin=(
                _safe_float(attr("estimated_margin_eur"))
                if isinstance(explicit_economics, Mapping)
                else None
            ),
            risk_level=str(attr("risk_level") or ND),
            market_data_quality=str(attr("market_data_quality") or ND),
            market_sample_size=_safe_int(attr("market_sample_size")),
            cove_status=str(attr("cove_status") or ND),
            deal_economics=explicit_economics,
        )


@dataclass
class DealerInfo:
    name: str
    company: str
    city: str = ND
    contact_person: str = ND

    def __post_init__(self) -> None:
        self.name = str(self.name or ND).strip() or ND
        self.company = str(self.company or self.name).strip() or self.name
        self.city = str(self.city or ND).strip() or ND
        self.contact_person = str(self.contact_person or ND).strip() or ND


def _sanitize_photo(
    raw_path: str,
    image_index: int,
    listing_id: str,
    output_dir: str,
    seller_name: Optional[str] = None,
) -> Optional[str]:
    """C0 fail-closed sanitizer adapter. RAW is never returned on failure."""
    try:
        from src.cove.image_sanitizer import sanitize_image
        result = sanitize_image(
            raw_path,
            output_dir=output_dir,
            listing_id=listing_id,
            image_index=image_index,
            seller_name=seller_name,
        )
    except Exception:
        return None
    if not result or result == SENTINEL_SKIP_PROMO:
        return None
    path = Path(result)
    return str(path) if path.is_file() and path.stat().st_size > 0 else None


def _verified_economics(value: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(value, Mapping):
        return None
    source = str(value.get("source") or "").strip()
    evidence_id = str(value.get("evidence_id") or "").strip()
    verdict = str(value.get("verdict") or "").strip().upper()
    margin = _safe_float(value.get("net_margin_eur"))
    if not source or not evidence_id or margin is None or verdict not in _VALID_ECON_VERDICTS:
        return None
    result = dict(value)
    result.update(
        {
            "source": source,
            "evidence_id": evidence_id,
            "verdict": verdict,
            "net_margin_eur": margin,
        }
    )
    return result


def _vehicle_from_mapping(raw: Mapping[str, Any]) -> VehicleData:
    dist = raw.get("_it_distribution") if isinstance(raw.get("_it_distribution"), Mapping) else {}
    no_verdict = bool(dist.get("no_verdict"))
    market_median = None if no_verdict else _safe_float(dist.get("median"))
    market_low = None if no_verdict else _safe_float(dist.get("band_low", dist.get("p25")))
    market_high = None if no_verdict else _safe_float(dist.get("band_high", dist.get("p75")))

    economics = raw.get("deal_economics") if isinstance(raw.get("deal_economics"), Mapping) else None
    return VehicleData(
        make=str(raw.get("make") or ND),
        model=str(raw.get("model") or ND),
        year=_safe_int(raw.get("year")) or 0,
        km=_safe_int(raw.get("km", raw.get("mileage"))) or 0,
        price_eu=_safe_int(raw.get("price_eur", raw.get("price_eu"))) or 0,
        price_it_estimate=_safe_int(raw.get("price_it_estimate", market_median)),
        confidence=_safe_float(raw.get("_cove_confidence", raw.get("confidence"))) or 0.0,
        engine=str(raw.get("engine") or ND),
        fuel_type=str(raw.get("fuel_type", raw.get("fuel")) or ND),
        transmission=str(raw.get("transmission") or ND),
        color=str(raw.get("color") or ND),
        doors=_safe_int(raw.get("doors")),
        vin=(str(raw.get("vin")).strip() if raw.get("vin") else None),
        previous_owners=_safe_int(raw.get("previous_owners")),
        listing_id=str(raw.get("listing_id") or ND),
        market_ref_price=_safe_float(raw.get("market_ref_price")),
        margin_decision=str(raw.get("_margin_decision") or (NO_VERDICT if no_verdict else NO_VERDICT)),
        chiavi_in_mano=_safe_float(raw.get("_margin_chiavi_in_mano")),
        spread_lordo=_safe_float(raw.get("_margin_spread_lordo")),
        dealer_floor=_safe_float(raw.get("_margin_dealer_floor")),
        surplus=_safe_float(raw.get("_margin_surplus")),
        fee_argos=_safe_float(raw.get("_margin_fee_argos")),
        margine_netto_dealer=_safe_float(raw.get("_margin_netto_dealer")),
        margine_netto_pct=_safe_float(raw.get("_margin_netto_pct")),
        it_median=market_median,
        it_p25=_safe_float(dist.get("p25")),
        it_p75=_safe_float(dist.get("p75")),
        it_n=_safe_int(dist.get("n")),
        it_source=(str(dist.get("source")) if dist.get("source") else None),
        relaxation_level=_safe_int(dist.get("relaxation_level")),
        no_verdict=no_verdict,
        it_band_low=market_low,
        it_band_high=market_high,
        it_confidence=(str(dist.get("confidence")) if dist.get("confidence") else None),
        it_width_nature=(str(dist.get("width_nature")) if dist.get("width_nature") else None),
        it_n_by_level=(dict(dist.get("n_by_level")) if isinstance(dist.get("n_by_level"), Mapping) else None),
        it_scrape_date=(str(dist.get("scrape_date")) if dist.get("scrape_date") else None),
        it_is_floor=bool(dist.get("is_floor", False)),
        it_n_priced=_safe_int(dist.get("n_priced")),
        it_pages_scraped=_safe_int(dist.get("pages_scraped")),
        it_terminated_by_empty=bool(dist.get("terminated_by_empty", False)),
        country_code=str(raw.get("country") or ""),
        fraud_doc_obtained=bool(raw.get("_fraud_doc_obtained", False)),
        fallback_declared=bool(dist.get("fallback_declared", raw.get("_it_fallback_declared", False))),
        deal_economics=economics,
    )


class ARGOSPDFGenerator:
    """Minimal enterprise renderer: visual polish without semantic invention."""

    LOGO_PATH = _REPO_ROOT / "assets" / "ARGOS_logo_sobrio_horizontal.png"

    def __init__(self) -> None:
        self.brand_black = HexColor("#1A1A1A") if REPORTLAB_AVAILABLE else None
        self.brand_gold = HexColor("#C8A446") if REPORTLAB_AVAILABLE else None
        self.brand_gray = HexColor("#6B7280") if REPORTLAB_AVAILABLE else None
        self.brand_light = HexColor("#F5F5F5") if REPORTLAB_AVAILABLE else None
        self.success = HexColor("#166534") if REPORTLAB_AVAILABLE else None
        self.warning = HexColor("#92400E") if REPORTLAB_AVAILABLE else None
        self.danger = HexColor("#991B1B") if REPORTLAB_AVAILABLE else None

    def _require_reportlab(self) -> None:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab is required; text fallback is intentionally disabled")

    def _style(self, name: str, *, size: int = 9, bold: bool = False, color: Any = None, align: int = 0) -> Any:
        return ParagraphStyle(
            name,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=size,
            leading=size + 3,
            textColor=color or self.brand_black,
            alignment=align,
        )

    def _section_title(self, text: str) -> Paragraph:
        return Paragraph(text, self._style("section", size=12, bold=True, color=self.brand_black))

    def _kv_table(self, rows: Sequence[tuple[str, Any]]) -> Table:
        data = [[Paragraph(str(label), self._style("lbl", bold=True)), Paragraph(_display(value), self._style("val"))] for label, value in rows]
        table = Table(data, colWidths=[55 * mm, 115 * mm], repeatRows=0)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.brand_light),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def _safe_images(self, vehicle: VehicleData) -> List[str]:
        if not vehicle.safe_images_verified:
            return []
        result: List[str] = []
        for value in vehicle.local_image_paths:
            path = Path(value)
            if path.is_file() and path.stat().st_size > 0:
                result.append(str(path))
        return result

    def _image_grid(self, paths: Sequence[str]) -> Optional[Table]:
        if not paths:
            return None
        cells: List[Any] = []
        for path in paths[:3]:
            try:
                cells.append(Image(path, width=54 * mm, height=36 * mm, kind="proportional"))
            except Exception:
                cells.append(Paragraph(ND, self._style("imgnd")))
        table = Table([cells], colWidths=[56 * mm] * len(cells))
        table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        return table

    def _status_banner(self, delivery_authorized: bool, readiness: Optional[Mapping[str, Any]]) -> Table:
        ready = bool(readiness and readiness.get("ready"))
        if delivery_authorized and ready:
            text = "DEALER READY — S292 gate + dossier readiness satisfied"
            bg = self.success
        else:
            text = "INTERNAL REVIEW — NOT DEALER READY"
            bg = self.warning
        table = Table([[Paragraph(text, self._style("status", size=10, bold=True, color=colors.white, align=1))]], colWidths=[170 * mm])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.5, bg), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        return table

    def _dimension_table(
        self,
        vehicle: VehicleData,
        grade_data: Optional[Mapping[str, Any]],
        economics: Optional[Mapping[str, Any]],
        readiness: Optional[Mapping[str, Any]],
    ) -> Table:
        grade = str((grade_data or {}).get("grade") or NO_VERDICT).upper()
        if grade not in _VALID_GRADES:
            grade = NO_VERDICT
        grade_score = (grade_data or {}).get("score") if grade != NO_VERDICT else None
        econ = _verified_economics(economics)
        market_conf = (econ or {}).get("market_confidence") if econ else None
        rows = [
            ["DIMENSIONE", "VALORE", "SEMANTICA"],
            ["CoVe confidence", _pct(vehicle.confidence), "confidence verifica CoVe"],
            ["ARGOS Vehicle Grade", f"{grade}" + (f" ({grade_score:.2f})" if isinstance(grade_score, (int, float)) else ""), "qualità/evidenza veicolo"],
            ["Deal economics", (econ or {}).get("verdict", NO_VERDICT), "economica evidenziata, separata"],
            ["Market confidence", _pct(market_conf), "confidenza riferimento mercato"],
            ["Dossier readiness", _pct((readiness or {}).get("dossier_readiness")), "completezza dossier, separata"],
        ]
        table = Table(rows, colWidths=[45 * mm, 45 * mm, 80 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.brand_black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def _economics_table(self, economics: Optional[Mapping[str, Any]]) -> Table:
        econ = _verified_economics(economics)
        if not econ:
            return self._kv_table(
                [
                    ("Verdetto", NO_VERDICT),
                    ("Motivo", "economica completa e provenienza non disponibili"),
                ]
            )
        costs = econ.get("costs_eur") if isinstance(econ.get("costs_eur"), Mapping) else {}
        rows: List[tuple[str, Any]] = [
            ("Verdetto", econ["verdict"]),
            ("Acquisto", _eur(econ.get("acquisition_eur"))),
            ("Riferimento mercato", _eur(econ.get("market_reference_eur"))),
        ]
        for name, amount in sorted(costs.items()):
            rows.append((f"Costo — {name}", _eur(amount)))
        rows.extend(
            [
                ("Costi totali", _eur(econ.get("total_costs_eur"))),
                ("Margine netto", _eur(econ.get("net_margin_eur"))),
                ("Soglia dichiarata", _eur(econ.get("min_margin_eur"))),
                ("Fonte", econ.get("source")),
                ("Evidence ID", econ.get("evidence_id")),
            ]
        )
        return self._kv_table(rows)

    def _market_distribution_table(self, vehicle: VehicleData) -> Table:
        if vehicle.no_verdict or vehicle.it_band_low is None or vehicle.it_band_high is None:
            return self._kv_table(
                [
                    ("Stato", NO_VERDICT),
                    ("Campione comparabili", vehicle.it_n if vehicle.it_n is not None else ND),
                    ("Nota", "campione insufficiente o banda non disponibile; nessuna stima sostitutiva emessa"),
                ]
            )
        return self._kv_table(
            [
                ("Banda mercato IT", f"{_eur(vehicle.it_band_low)} – {_eur(vehicle.it_band_high)}"),
                ("Mediana", _eur(vehicle.it_median)),
                ("N comparabili", vehicle.it_n if vehicle.it_n is not None else ND),
                ("Livello rilassamento", vehicle.relaxation_level if vehicle.relaxation_level is not None else ND),
                ("Confidence", vehicle.it_confidence or ND),
                ("Natura ampiezza", vehicle.it_width_nature or ND),
                ("Data fotografia", vehicle.it_scrape_date or ND),
                ("Fallback configurazione", "sì" if vehicle.fallback_declared else "no"),
            ]
        )

    def _legacy_margin_table(self, vehicle: VehicleData) -> Table:
        values = {
            "Costo chiavi in mano": vehicle.chiavi_in_mano,
            "Spread lordo": vehicle.spread_lordo,
            "Pavimento dealer": vehicle.dealer_floor,
            "Surplus": vehicle.surplus,
            "Fee ARGOS": vehicle.fee_argos,
            "Margine netto dealer": vehicle.margine_netto_dealer,
        }
        if vehicle.margin_decision == NO_VERDICT or not any(_safe_float(v) is not None for v in values.values()):
            return self._kv_table(
                [
                    ("Verdetto legacy margin gate", NO_VERDICT),
                    ("Nota", "nessun valore mancante viene ricostruito dal renderer"),
                ]
            )
        return self._kv_table(
            [("Verdetto margin gate", vehicle.margin_decision)]
            + [(label, _eur(value)) for label, value in values.items()]
            + [("Margine netto %", _pct(vehicle.margine_netto_pct))]
        )

    def generate_vehicle_sheet(
        self,
        vehicle: VehicleData,
        dealer: DealerInfo,
        output_path: str,
        grade_data: Optional[dict] = None,
        source_dossier: Optional[dict] = None,
        *,
        economics: Optional[Mapping[str, Any]] = None,
        readiness: Optional[Mapping[str, Any]] = None,
        delivery_authorized: bool = False,
    ) -> str:
        self._require_reportlab()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=f"ARGOS dossier {vehicle.make} {vehicle.model}",
        )

        story: List[Any] = []
        if self.LOGO_PATH.is_file():
            try:
                story.append(Image(str(self.LOGO_PATH), width=62 * mm, height=16 * mm, kind="proportional"))
            except Exception:
                pass
        story.append(Paragraph("DOSSIER VEICOLO", self._style("title", size=20, bold=True)))
        story.append(Paragraph(f"Preparato per: <b>{dealer.name}</b> — {dealer.company}", self._style("dealer", size=10, color=self.brand_gray)))
        story.append(Spacer(1, 4 * mm))
        story.append(self._status_banner(delivery_authorized, readiness))
        story.append(Spacer(1, 5 * mm))

        safe_images = self._safe_images(vehicle)
        grid = self._image_grid(safe_images)
        if grid is not None:
            story.append(grid)
            story.append(Spacer(1, 5 * mm))

        story.append(self._section_title("Dati veicolo"))
        story.append(Spacer(1, 2 * mm))
        story.append(
            self._kv_table(
                [
                    ("Veicolo", f"{_display(vehicle.make)} {_display(vehicle.model)}"),
                    ("Anno", vehicle.year if vehicle.year > 0 else ND),
                    ("Chilometraggio", f"{vehicle.km:,} km".replace(",", ".") if vehicle.km >= 0 else ND),
                    ("Prezzo acquisizione osservato", _eur(vehicle.price_eu)),
                    ("Carburante", vehicle.fuel_type),
                    ("Cambio", vehicle.transmission),
                    ("Colore", vehicle.color),
                    ("Motore", vehicle.engine),
                    ("Porte", vehicle.doors if vehicle.doors is not None else ND),
                    ("VIN", vehicle.vin or ND),
                    ("Prima immatricolazione", vehicle.first_registration or ND),
                    ("Ultimo service", vehicle.last_service or ND),
                    ("Proprietari precedenti", vehicle.previous_owners if vehicle.previous_owners is not None else ND),
                ]
            )
        )
        story.append(Spacer(1, 5 * mm))

        story.append(self._section_title("Dimensioni ARGOS — separate"))
        story.append(Spacer(1, 2 * mm))
        effective_econ = economics or vehicle.deal_economics
        story.append(self._dimension_table(vehicle, grade_data, effective_econ, readiness))
        story.append(Spacer(1, 5 * mm))

        story.append(self._section_title("Deal economics"))
        story.append(Spacer(1, 2 * mm))
        story.append(self._economics_table(effective_econ))
        story.append(Spacer(1, 5 * mm))

        story.append(self._section_title("Mercato Italia — evidenza disponibile"))
        story.append(Spacer(1, 2 * mm))
        story.append(self._market_distribution_table(vehicle))
        story.append(Spacer(1, 5 * mm))

        if vehicle.margin_decision != NO_VERDICT or any(
            value is not None for value in (
                vehicle.chiavi_in_mano,
                vehicle.spread_lordo,
                vehicle.dealer_floor,
                vehicle.fee_argos,
                vehicle.margine_netto_dealer,
            )
        ):
            story.append(self._section_title("Margin gate — valori ricevuti"))
            story.append(Spacer(1, 2 * mm))
            story.append(self._legacy_margin_table(vehicle))
            story.append(Spacer(1, 5 * mm))

        if grade_data:
            story.append(self._section_title("ARGOS Vehicle Grade — evidenza"))
            story.append(Spacer(1, 2 * mm))
            story.append(
                self._kv_table(
                    [
                        ("Grade", grade_data.get("grade", NO_VERDICT)),
                        ("Score", grade_data.get("score", ND)),
                        ("Evidence coverage", _pct(grade_data.get("evidence_coverage"))),
                        ("Evidenze mancanti", ", ".join(grade_data.get("missing_evidence", [])) or "nessuna"),
                        ("Blocchi", ", ".join(grade_data.get("blocking_reasons", [])) or "nessuno"),
                    ]
                )
            )
            story.append(Spacer(1, 5 * mm))

        if readiness:
            story.append(self._section_title("Dossier readiness"))
            story.append(Spacer(1, 2 * mm))
            story.append(
                self._kv_table(
                    [
                        ("Livello", readiness.get("level", ND)),
                        ("Readiness", _pct(readiness.get("dossier_readiness"))),
                        ("Dealer-ready", readiness.get("ready", False)),
                        ("Mandatory mancanti", ", ".join(readiness.get("missing_mandatory", [])) or "nessuno"),
                        ("Important mancanti", ", ".join(readiness.get("missing_important", [])) or "nessuno"),
                        ("Prossima azione", readiness.get("next_action", ND)),
                    ]
                )
            )
            story.append(Spacer(1, 5 * mm))

        # Source is an explicit release-layer payload only. Internal vehicle
        # source fields are never rendered into the pre-payment dealer dossier.
        if source_dossier:
            story.append(self._section_title("Fonte veicolo — release autorizzata"))
            story.append(Spacer(1, 2 * mm))
            story.append(
                self._kv_table(
                    [
                        ("Venditore", source_dossier.get("seller_name", ND)),
                        ("URL", source_dossier.get("url", ND)),
                        ("Telefono", source_dossier.get("phone", ND)),
                        ("Email", source_dossier.get("email", ND)),
                    ]
                )
            )
            story.append(Spacer(1, 5 * mm))

        if len(safe_images) > 3:
            story.append(PageBreak())
            story.append(self._section_title("Galleria immagini sanificate"))
            story.append(Spacer(1, 3 * mm))
            for start in range(3, len(safe_images), 3):
                grid = self._image_grid(safe_images[start : start + 3])
                if grid is not None:
                    story.append(grid)
                    story.append(Spacer(1, 4 * mm))

        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        story.append(Spacer(1, 5 * mm))
        story.append(
            Paragraph(
                f"ARGOS Automotive — generato {generated}. I campi n/d non sono stati inferiti. "
                "Questo dossier non sostituisce documenti del venditore o verifiche legali/fiscali.",
                self._style("footer", size=7, color=self.brand_gray),
            )
        )
        doc.build(story)
        return str(output.resolve())


def _build_vehicle_from_db(listing_id: str, db_path: str) -> tuple[VehicleData, Dict[str, Any], Dict[str, Any]]:
    import duckdb

    con = duckdb.connect(db_path, read_only=True)
    try:
        cove = _fetch_row(con, "cove_results", listing_id)
        listing = _fetch_row(con, "vehicle_listings", listing_id)
    finally:
        con.close()
    if not cove:
        raise ValueError(f"listing {listing_id!r} not found in cove_results")

    merged = {**cove, **listing}
    price = _safe_int(merged.get("price_eu", cove.get("price")))
    km = _safe_int(merged.get("mileage", cove.get("km")))
    year = _safe_int(merged.get("year"))
    if price is None or km is None or year is None:
        raise ValueError("listing is missing required observed price/km/year")

    vehicle = VehicleData(
        make=str(merged.get("make") or ND),
        model=str(merged.get("model") or ND),
        year=year,
        km=km,
        price_eu=price,
        price_it_estimate=None,
        confidence=_safe_float(cove.get("confidence")) or 0.0,
        engine=str(merged.get("engine") or ND),
        fuel_type=str(merged.get("fuel_type") or ND),
        transmission=str(merged.get("transmission") or ND),
        color=str(merged.get("color") or ND),
        doors=_safe_int(merged.get("doors")),
        vin=(str(merged.get("vin")).strip() if merged.get("vin") else None),
        first_registration=(str(merged.get("first_registration")) if merged.get("first_registration") else None),
        last_service=(str(merged.get("last_service")) if merged.get("last_service") else None),
        previous_owners=_safe_int(merged.get("previous_owners")),
        cove_status=str(cove.get("recommendation") or ND),
        listing_id=listing_id,
    )
    return vehicle, cove, listing


def _sanitize_listing_images(listing_id: str, db_path: str, output_dir: str) -> List[str]:
    """Use the C0 batch sanitizer. Failure yields text-only dossier, never RAW."""
    try:
        from src.cove.image_sanitizer import sanitize_all_images
        safe_dir = str(Path(output_dir).resolve() / "safe_images")
        result = sanitize_all_images(listing_id, db_path=db_path, output_dir=safe_dir)
    except Exception:
        return []
    safe: List[str] = []
    for value in result or []:
        if not value or value == SENTINEL_SKIP_PROMO:
            continue
        path = Path(value)
        if path.is_file() and path.stat().st_size > 0:
            safe.append(str(path))
    return safe


def generate_dossier_from_db(
    listing_id: str,
    dealer_name: str,
    output_dir: str,
    db_path: Optional[str] = None,
    *,
    demand_evidence: Optional[DemandEvidence] = None,
    economics: Optional[Mapping[str, Any]] = None,
    dealer_delivery: bool = False,
    dealer_company: Optional[str] = None,
    dealer_city: str = ND,
) -> str:
    """Generate a DB-backed review or dealer-delivery dossier.

    ``dealer_delivery=True`` is fail-closed and requires both S292 listing
    authorization and ``check_dossier_readiness(...).ready``.  Review mode may
    be generated for engineering/internal work but is visibly marked as such.
    """
    db_path = db_path or str(_REPO_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")
    if not Path(db_path).is_file():
        raise FileNotFoundError(f"DB not found: {db_path}")

    vehicle, _, _ = _build_vehicle_from_db(listing_id, db_path)

    from src.cove.argos_grade import compute_argos_grade
    from src.cove.dossier_standard import check_dossier_readiness

    grade_data = compute_argos_grade(listing_id, db_path=db_path)
    readiness = check_dossier_readiness(
        listing_id,
        db_path=db_path,
        demand_evidence=demand_evidence,
        economics=economics,
        vehicle_grade=grade_data,
    )
    readiness_data = readiness.as_dict()

    if dealer_delivery:
        require_listing_authorization(demand_evidence, listing_id)
        if not readiness.ready:
            raise PermissionError(
                "DOSSIER_GATE: dealer delivery blocked; "
                f"mandatory={readiness.missing_mandatory}; important={readiness.missing_important}"
            )

    vehicle.local_image_paths = _sanitize_listing_images(listing_id, db_path, output_dir)
    vehicle.safe_images_verified = bool(vehicle.local_image_paths)
    vehicle.deal_economics = economics

    safe_dealer = re.sub(r"[^A-Za-z0-9._-]+", "_", dealer_name).strip("_") or "Dealer"
    short_id = re.sub(r"[^A-Za-z0-9_-]+", "_", listing_id)[-16:]
    filename = f"ARGOS_{vehicle.make}_{vehicle.model}_{vehicle.year}_{safe_dealer}_{short_id}.pdf"
    output_path = str(Path(output_dir).resolve() / filename)
    dealer = DealerInfo(
        name=dealer_name,
        company=dealer_company or dealer_name,
        city=dealer_city,
    )
    return ARGOSPDFGenerator().generate_vehicle_sheet(
        vehicle,
        dealer,
        output_path,
        grade_data=grade_data,
        economics=economics,
        readiness=readiness_data,
        delivery_authorized=dealer_delivery,
    )


def generate_dossier_from_data(
    data_json: str,
    dealer_name: str,
    output_path: str,
    *,
    grade_data: Optional[Mapping[str, Any]] = None,
    economics: Optional[Mapping[str, Any]] = None,
) -> str:
    """Render a deterministic internal-review dossier from supplied JSON.

    Historical S268/S296 fixture drivers use this function.  It never marks the
    artifact dealer-ready because a free-form JSON blob is not S292 evidence.
    """
    payload = json.loads(data_json)
    if not isinstance(payload, Mapping):
        raise ValueError("data JSON must be an object")
    vehicles = payload.get("vehicles")
    if isinstance(vehicles, list) and vehicles:
        raw = vehicles[0]
    else:
        raw = payload
    if not isinstance(raw, Mapping):
        raise ValueError("vehicle payload must be an object")
    vehicle = _vehicle_from_mapping(raw)
    effective_econ = economics or vehicle.deal_economics
    review = {
        "level": "REVIEW",
        "ready": False,
        "dossier_readiness": None,
        "missing_mandatory": ["s292_delivery_gate_not_evaluated"],
        "missing_important": [],
        "next_action": "Use generate_dossier_from_db(..., dealer_delivery=True) for dealer delivery",
    }
    dealer = DealerInfo(name=dealer_name, company=dealer_name, city=ND)
    return ARGOSPDFGenerator().generate_vehicle_sheet(
        vehicle,
        dealer,
        output_path,
        grade_data=dict(grade_data or {}),
        economics=effective_econ,
        readiness=review,
        delivery_authorized=False,
    )


def generate_opportunity_dossier(
    opportunities: list,
    dealer_name: str,
    dealer_company: str,
    dealer_city: str,
    output_dir: str = "/tmp/argos_dossier",
    download_images: bool = False,
    watermark: bool = False,
) -> List[str]:
    """Legacy compatibility: generate INTERNAL REVIEW PDFs from Opportunities.

    Network image downloading is intentionally not performed here.  Production
    dealer delivery must use the DB-backed C0 sanitizer path.
    """
    del download_images, watermark
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    generator = ARGOSPDFGenerator()
    dealer = DealerInfo(dealer_name, dealer_company, dealer_city)
    paths: List[str] = []
    for index, opp in enumerate(opportunities, 1):
        vehicle = VehicleData.from_opportunity(opp, dealer_city=dealer_city)
        filename = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            f"ARGOS_REVIEW_{vehicle.make}_{vehicle.model}_{vehicle.year}_{index:02d}.pdf",
        )
        output_path = str(Path(output_dir).resolve() / filename)
        review = {
            "level": "REVIEW",
            "ready": False,
            "dossier_readiness": None,
            "missing_mandatory": ["s292_delivery_gate_not_evaluated"],
            "missing_important": [],
            "next_action": "Persist candidate and use DB-backed dealer-delivery gate",
        }
        generator.generate_vehicle_sheet(
            vehicle,
            dealer,
            output_path,
            economics=vehicle.deal_economics,
            readiness=review,
            delivery_authorized=False,
        )
        paths.append(output_path)
    return paths


def generate_combined_dossier(
    opportunities: list,
    dealer_name: str,
    dealer_company: str,
    dealer_city: str,
    output_dir: str = "/tmp/argos_dossier",
    max_per_model: int = 5,
) -> str:
    """Generate a truth-safe INTERNAL REVIEW summary; never a dealer-ready artifact."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"ARGOS_REVIEW_{re.sub(r'[^A-Za-z0-9._-]+', '_', dealer_company)}_{datetime.now().strftime('%Y%m%d')}.pdf"
    gen = ARGOSPDFGenerator()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    story: List[Any] = [
        Paragraph("ARGOS AUTOMOTIVE — INTERNAL REVIEW", gen._style("ct", size=18, bold=True)),
        Paragraph(f"Dealer: {_display(dealer_name)} — {_display(dealer_company)}", gen._style("cs", size=10, color=gen.brand_gray)),
        Spacer(1, 5 * mm),
        gen._status_banner(False, {"ready": False}),
        Spacer(1, 6 * mm),
    ]
    counts: Dict[str, int] = {}
    emitted = 0
    for opp in opportunities:
        vehicle = VehicleData.from_opportunity(opp, dealer_city=dealer_city)
        key = f"{vehicle.make} {vehicle.model}"
        counts.setdefault(key, 0)
        if counts[key] >= max_per_model:
            continue
        counts[key] += 1
        emitted += 1
        if emitted > 1:
            story.append(PageBreak())
        story.append(gen._section_title(f"#{emitted} — {vehicle.make} {vehicle.model} {vehicle.year}"))
        story.append(Spacer(1, 3 * mm))
        story.append(
            gen._kv_table(
                [
                    ("Prezzo acquisizione osservato", _eur(vehicle.price_eu)),
                    ("Km", vehicle.km),
                    ("CoVe confidence", _pct(vehicle.confidence)),
                    ("Market reference", _eur(vehicle.market_ref_price)),
                    ("Deal economics", (_verified_economics(vehicle.deal_economics) or {}).get("verdict", NO_VERDICT)),
                ]
            )
        )
    if emitted == 0:
        story.append(Paragraph("Nessun candidato disponibile.", gen._style("none")))
    doc.build(story)
    return str(path.resolve())


def _cli_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="ARGOS evidence-safe dealer dossier generator")
    parser.add_argument("--listing", help="listing_id in cove_results")
    parser.add_argument("--dealer", required=True, help="dealer display name")
    parser.add_argument("--company", help="dealer company name")
    parser.add_argument("--city", default=ND, help="dealer city only if known")
    parser.add_argument("--output", required=True, help="output directory, or PDF path with --data")
    parser.add_argument("--db", help="DuckDB path")
    parser.add_argument("--data", help="JSON string or JSON file for INTERNAL REVIEW")
    parser.add_argument("--evidence-json", help="DemandEvidence JSON/file for dealer delivery")
    parser.add_argument("--economics-json", help="DealEconomics JSON/file")
    parser.add_argument("--dealer-delivery", action="store_true", help="enforce S292 + DEALER_READY and mark artifact deliverable")
    args = parser.parse_args(argv)

    economics = _load_json_object(args.economics_json)
    if args.data:
        data_value = Path(args.data).read_text(encoding="utf-8") if Path(args.data).is_file() else args.data
        result = generate_dossier_from_data(
            data_value,
            dealer_name=args.dealer,
            output_path=args.output,
            economics=economics,
        )
    elif args.listing:
        evidence = _load_demand_evidence(args.evidence_json)
        if args.dealer_delivery and evidence is None:
            parser.error("--evidence-json is required with --dealer-delivery")
        result = generate_dossier_from_db(
            args.listing,
            dealer_name=args.dealer,
            dealer_company=args.company,
            dealer_city=args.city,
            output_dir=args.output,
            db_path=args.db,
            demand_evidence=evidence,
            economics=economics,
            dealer_delivery=args.dealer_delivery,
        )
    else:
        parser.error("either --listing or --data is required")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())
