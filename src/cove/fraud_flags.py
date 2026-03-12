"""
COMBARETROVAMIAUTO — CoVe 2026
Module: Fraud Flags Checker

Standalone module da integrare in cove_engine_v4.py
Compatibile con CoVeResult return format.

CoVe 2026 Tags:
  [VERIFIED]  = validato su dati reali o fonti esterne
  [ESTIMATED] = ragionevole ma non benchmarkato
  [UNKNOWN]   = placeholder, richiede calibrazione su dati reali
  [SUSPICIOUS]= trigger automatico fraud alert
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# THRESHOLDS — CoVe 2026 tagged
# ---------------------------------------------------------------------------

# Chilometraggio annuo — [UNKNOWN] DA VALIDARE SU DATI REALI BMW/Merc/Audi EU
MAX_KM_PER_ANNO: int = 60_000
MIN_KM_PER_ANNO: int = 1_000

# Delta prezzo vs mercato — [ESTIMATED] basato su esperienza settore
WARN_PRICE_DELTA: float = 0.20       # -20% → WARNING
SUSPICIOUS_PRICE_DELTA: float = 0.35  # -35% → SUSPICIOUS (probabile frode/keepen)

# Anno minimo veicolo accettato nel segmento target — [VERIFIED]
MIN_YEAR: int = 2018
MAX_YEAR: int = 2023

# Km massimi assoluti nel segmento target — [VERIFIED] da business spec
MAX_KM_ABSOLUTE: int = 150_000

# Odometer fraud rate EU per paese sorgente — [VERIFIED] carVertical EU Report 2025
# Domestic: 5-12% | Cross-border: 30-50%
# Fonte: carVertical + EU Parliament study (EPRS 2018 + Odometer Fraud 14% jump 2025)
ODOMETER_RISK_BY_COUNTRY: dict[str, str] = {
    # ALTO RISCHIO — fraud rate ≥6%
    "Latvia": "HIGH",       # 11.2% [VERIFIED carVertical 2025]
    "Ukraine": "HIGH",      # 9.1%
    "Lithuania": "HIGH",    # 7.8%
    "Romania": "HIGH",      # 6.5%
    "Bulgaria": "HIGH",     # stimato >6% [ESTIMATED]
    "Poland": "HIGH",       # stimato >5% [ESTIMATED]
    # MEDIO RISCHIO — fraud rate 3-6%
    "Italy": "MEDIUM",      # [ESTIMATED] EU enforcement variabile
    "Spain": "MEDIUM",      # [ESTIMATED] EU enforcement variabile
    "France": "MEDIUM",     # [ESTIMATED]
    # BASSO RISCHIO — Car-Pass/NAP anti-odometer
    "Belgium": "LOW",       # Car-Pass [VERIFIED]
    "Netherlands": "LOW",   # Nationale Auto Pas (NAP) [VERIFIED]
    "Germany": "LOW",       # HU/AU + digital records [ESTIMATED]
    "United Kingdom": "LOW",  # 2.1% [VERIFIED carVertical 2025]
    "Switzerland": "LOW",   # 2.1% [VERIFIED carVertical 2025]
    "Portugal": "LOW",      # 2.3% [VERIFIED carVertical 2025]
    "Sweden": "LOW",        # [ESTIMATED] rigido enforcement
}

# Penalità score per rischio odometer paese sorgente [ESTIMATED]
ODOMETER_COUNTRY_PENALTY: dict[str, float] = {
    "HIGH": 0.10,    # segnale di attenzione elevata
    "MEDIUM": 0.03,
    "LOW": 0.0,
    "UNKNOWN": 0.05,  # default conservativo se paese non noto
}

# Price velocity — [ESTIMATED] spike/drop >20% in 14gg = segnale red flag
PRICE_VELOCITY_WARN_PCT: float = 0.20   # 20% variazione → WARNING
PRICE_VELOCITY_SUSPICIOUS_PCT: float = 0.35  # 35% → SUSPICIOUS


# ---------------------------------------------------------------------------
# ENUMS & DATACLASSES
# ---------------------------------------------------------------------------

class FraudSeverity(str, Enum):
    CLEAN = "CLEAN"
    WARNING = "WARNING"
    SUSPICIOUS = "SUSPICIOUS"
    REJECTED = "REJECTED"


@dataclass
class FraudFlag:
    code: str                    # es. "KM_TOO_HIGH", "PRICE_SUSPICIOUS"
    severity: FraudSeverity
    detail: str                  # messaggio leggibile
    cove_tag: str                # [VERIFIED] | [ESTIMATED] | [UNKNOWN]
    value: Optional[float] = None
    threshold: Optional[float] = None


@dataclass
class FraudFlagsResult:
    """
    Return format compatibile con CoVeResult.fraud_flags field.
    Merge in cove_engine_v4.py:
        result.fraud_flags = FraudFlagsChecker.run(listing)
    """
    overall: FraudSeverity = FraudSeverity.CLEAN
    flags: list[FraudFlag] = field(default_factory=list)
    score_penalty: float = 0.0   # da sottrarre al CoVe confidence score
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def has_flags(self) -> bool:
        return len(self.flags) > 0

    def is_rejected(self) -> bool:
        return self.overall == FraudSeverity.REJECTED

    def to_dict(self) -> dict:
        return {
            "overall": self.overall.value,
            "flags": [
                {
                    "code": f.code,
                    "severity": f.severity.value,
                    "detail": f.detail,
                    "cove_tag": f.cove_tag,
                    "value": f.value,
                    "threshold": f.threshold,
                }
                for f in self.flags
            ],
            "score_penalty": self.score_penalty,
            "checked_at": self.checked_at,
        }


# ---------------------------------------------------------------------------
# CHECKER
# ---------------------------------------------------------------------------

class FraudFlagsChecker:
    """
    Utilizzo in cove_engine_v4.py:

        from python.cove.fraud_flags import FraudFlagsChecker

        fraud_result = FraudFlagsChecker.run(
            km=listing["km"],
            year=listing["year"],
            price=listing["price"],
            market_price=market_ref_price,  # da auto.dev o stima interna
        )

        if fraud_result.is_rejected():
            return CoVeResult(status="REJECTED", fraud=fraud_result)

        cove_score -= fraud_result.score_penalty
    """

    @staticmethod
    def run(
        km: int,
        year: int,
        price: float,
        market_price: Optional[float] = None,
        reference_date: Optional[datetime] = None,
        source_country: Optional[str] = None,
        price_delta_14d_pct: Optional[float] = None,
    ) -> FraudFlagsResult:
        """
        Esegue tutti i check e restituisce FraudFlagsResult aggregato.

        Args:
            km:                 chilometri dichiarati nel listing
            year:               anno immatricolazione
            price:              prezzo listing (EUR)
            market_price:       prezzo di riferimento mercato (EUR) — può essere None
            reference_date:     data di riferimento (default: oggi)
            source_country:     paese sorgente listing (es. "Belgium", "Romania")
                                → usato per odometer EU risk weighting [DeepResearch 2026]
            price_delta_14d_pct: variazione prezzo in 14 giorni (es. 0.22 = +22%)
                                → segnale price velocity fraud [DeepResearch 2026]
        """
        result = FraudFlagsResult()
        ref_date = reference_date or datetime.utcnow()

        flags: list[FraudFlag] = []

        # --- CHECK 1: km assoluti ---
        flags += FraudFlagsChecker._check_km_absolute(km)

        # --- CHECK 2: km/anno ---
        flags += FraudFlagsChecker._check_km_per_anno(km, year, ref_date)

        # --- CHECK 3: anno segmento ---
        flags += FraudFlagsChecker._check_year(year)

        # --- CHECK 4: prezzo vs mercato ---
        if market_price is not None and market_price > 0:
            flags += FraudFlagsChecker._check_price_delta(price, market_price)

        # --- CHECK 5: odometer EU risk by country [DeepResearch 2026] ---
        if source_country is not None:
            flags += FraudFlagsChecker._check_odometer_eu_risk(source_country)

        # --- CHECK 6: price velocity (spike/drop >20% in 14gg) [DeepResearch 2026] ---
        if price_delta_14d_pct is not None:
            flags += FraudFlagsChecker._check_price_velocity(price_delta_14d_pct)

        result.flags = flags
        result.overall = FraudFlagsChecker._aggregate_severity(flags)
        result.score_penalty = FraudFlagsChecker._compute_penalty(flags)

        if flags:
            logger.warning(
                "FraudFlags triggered | overall=%s | flags=%s | km=%d | year=%d | price=%.0f",
                result.overall.value,
                [f.code for f in flags],
                km, year, price,
            )

        return result

    # -----------------------------------------------------------------------
    # PRIVATE CHECKS
    # -----------------------------------------------------------------------

    @staticmethod
    def _check_km_absolute(km: int) -> list[FraudFlag]:
        flags = []
        if km > MAX_KM_ABSOLUTE:
            flags.append(FraudFlag(
                code="KM_EXCEEDS_SEGMENT",
                severity=FraudSeverity.REJECTED,
                detail=f"Km {km:,} supera soglia massima segmento {MAX_KM_ABSOLUTE:,} km — fuori target",
                cove_tag="[VERIFIED]",  # definito da business spec
                value=float(km),
                threshold=float(MAX_KM_ABSOLUTE),
            ))
        return flags

    @staticmethod
    def _check_km_per_anno(km: int, year: int, ref_date: datetime) -> list[FraudFlag]:
        flags = []
        age_years = max(ref_date.year - year, 1)  # evita divisione per zero
        km_per_anno = km / age_years

        if km_per_anno > MAX_KM_PER_ANNO:
            flags.append(FraudFlag(
                code="KM_TOO_HIGH",
                severity=FraudSeverity.SUSPICIOUS,
                detail=(
                    f"Km/anno {km_per_anno:,.0f} > soglia MAX {MAX_KM_PER_ANNO:,} — "
                    f"probabile uso commerciale/taxi [UNKNOWN: soglia da validare]"
                ),
                cove_tag="[UNKNOWN]",
                value=round(km_per_anno, 1),
                threshold=float(MAX_KM_PER_ANNO),
            ))

        if km_per_anno < MIN_KM_PER_ANNO:
            flags.append(FraudFlag(
                code="KM_TOO_LOW",
                severity=FraudSeverity.WARNING,
                detail=(
                    f"Km/anno {km_per_anno:,.0f} < soglia MIN {MIN_KM_PER_ANNO:,} — "
                    f"possibile odometro alterato o veicolo fermo [UNKNOWN: soglia da validare]"
                ),
                cove_tag="[UNKNOWN]",
                value=round(km_per_anno, 1),
                threshold=float(MIN_KM_PER_ANNO),
            ))

        return flags

    @staticmethod
    def _check_year(year: int) -> list[FraudFlag]:
        flags = []
        if year < MIN_YEAR or year > MAX_YEAR:
            flags.append(FraudFlag(
                code="YEAR_OUT_OF_SEGMENT",
                severity=FraudSeverity.REJECTED,
                detail=f"Anno {year} fuori finestra segmento {MIN_YEAR}-{MAX_YEAR}",
                cove_tag="[VERIFIED]",
                value=float(year),
                threshold=None,
            ))
        return flags

    @staticmethod
    def _check_price_delta(price: float, market_price: float) -> list[FraudFlag]:
        flags = []
        delta = (market_price - price) / market_price  # positivo = listing più basso del mercato

        if delta >= SUSPICIOUS_PRICE_DELTA:
            flags.append(FraudFlag(
                code="PRICE_SUSPICIOUS",
                severity=FraudSeverity.SUSPICIOUS,
                detail=(
                    f"Prezzo €{price:,.0f} è -{delta:.0%} sotto mercato €{market_price:,.0f} — "
                    f"soglia SUSPICIOUS {SUSPICIOUS_PRICE_DELTA:.0%} [ESTIMATED]"
                ),
                cove_tag="[ESTIMATED]",
                value=round(delta, 4),
                threshold=SUSPICIOUS_PRICE_DELTA,
            ))
        elif delta >= WARN_PRICE_DELTA:
            flags.append(FraudFlag(
                code="PRICE_WARNING",
                severity=FraudSeverity.WARNING,
                detail=(
                    f"Prezzo €{price:,.0f} è -{delta:.0%} sotto mercato €{market_price:,.0f} — "
                    f"verifica motivazione [ESTIMATED]"
                ),
                cove_tag="[ESTIMATED]",
                value=round(delta, 4),
                threshold=WARN_PRICE_DELTA,
            ))

        return flags

    @staticmethod
    def _check_odometer_eu_risk(source_country: str) -> list[FraudFlag]:
        """
        Penalizza listing da paesi ad alto tasso di odometer fraud.
        [VERIFIED] carVertical EU Report 2025: cross-border 30-50% fraud rate.
        Paesi HIGH: Latvia 11.2%, Ukraine 9.1%, Lithuania 7.8%, Romania 6.5%.
        Paesi LOW: Belgium (Car-Pass), Netherlands (NAP), UK 2.1%, CH 2.1%.
        """
        flags = []
        risk_level = ODOMETER_RISK_BY_COUNTRY.get(source_country, "UNKNOWN")

        if risk_level == "HIGH":
            flags.append(FraudFlag(
                code="ODOMETER_COUNTRY_HIGH_RISK",
                severity=FraudSeverity.WARNING,
                detail=(
                    f"Paese sorgente '{source_country}' ha tasso odometer fraud elevato "
                    f"(≥6% veicoli con km alterati). Verifica Car-Pass/NAP equivalente locale. "
                    f"[VERIFIED carVertical EU 2025]"
                ),
                cove_tag="[VERIFIED]",
                value=None,
                threshold=None,
            ))
        elif risk_level == "UNKNOWN":
            flags.append(FraudFlag(
                code="ODOMETER_COUNTRY_UNKNOWN",
                severity=FraudSeverity.WARNING,
                detail=(
                    f"Paese sorgente '{source_country}' non presente nel database risk EU. "
                    f"Applico penalità conservativa. [ESTIMATED]"
                ),
                cove_tag="[ESTIMATED]",
                value=None,
                threshold=None,
            ))
        # LOW e MEDIUM: nessun flag — variazione inclusa solo in penalty

        return flags

    @staticmethod
    def _check_price_velocity(price_delta_14d_pct: float) -> list[FraudFlag]:
        """
        Segnala variazioni di prezzo >20% in 14 giorni come anomalia.
        Pattern: dealer abbassa prezzo rapidamente = pressione vendita urgente.
        Pattern: prezzo sale rapidamente = listing duplicato con markup.
        [ESTIMATED] soglie da calibrare su dati reali.
        """
        flags = []
        abs_delta = abs(price_delta_14d_pct)

        if abs_delta >= PRICE_VELOCITY_SUSPICIOUS_PCT:
            direction = "rialzo" if price_delta_14d_pct > 0 else "ribasso"
            flags.append(FraudFlag(
                code="PRICE_VELOCITY_SUSPICIOUS",
                severity=FraudSeverity.SUSPICIOUS,
                detail=(
                    f"Variazione prezzo {price_delta_14d_pct:+.0%} in 14gg ({direction}) — "
                    f"anomalia prezzo SUSPICIOUS (soglia: ±{PRICE_VELOCITY_SUSPICIOUS_PCT:.0%}). "
                    f"Possibile wash trade o listing duplicato con markup. [ESTIMATED]"
                ),
                cove_tag="[ESTIMATED]",
                value=round(price_delta_14d_pct, 4),
                threshold=PRICE_VELOCITY_SUSPICIOUS_PCT,
            ))
        elif abs_delta >= PRICE_VELOCITY_WARN_PCT:
            direction = "rialzo" if price_delta_14d_pct > 0 else "ribasso"
            flags.append(FraudFlag(
                code="PRICE_VELOCITY_WARNING",
                severity=FraudSeverity.WARNING,
                detail=(
                    f"Variazione prezzo {price_delta_14d_pct:+.0%} in 14gg ({direction}) — "
                    f"verifica motivazione (soglia: ±{PRICE_VELOCITY_WARN_PCT:.0%}). [ESTIMATED]"
                ),
                cove_tag="[ESTIMATED]",
                value=round(price_delta_14d_pct, 4),
                threshold=PRICE_VELOCITY_WARN_PCT,
            ))

        return flags

    # -----------------------------------------------------------------------
    # AGGREGATION
    # -----------------------------------------------------------------------

    @staticmethod
    def _aggregate_severity(flags: list[FraudFlag]) -> FraudSeverity:
        if not flags:
            return FraudSeverity.CLEAN
        severities = {f.severity for f in flags}
        if FraudSeverity.REJECTED in severities:
            return FraudSeverity.REJECTED
        if FraudSeverity.SUSPICIOUS in severities:
            return FraudSeverity.SUSPICIOUS
        if FraudSeverity.WARNING in severities:
            return FraudSeverity.WARNING
        return FraudSeverity.CLEAN

    @staticmethod
    def _compute_penalty(flags: list[FraudFlag]) -> float:
        """
        Penalità sul CoVe confidence score (0.0 - 1.0).
        [ESTIMATED] — da calibrare su dati reali post-benchmark.

        Override penalty per flag specifici con calibrazione country-risk:
        - ODOMETER_COUNTRY_HIGH_RISK: usa ODOMETER_COUNTRY_PENALTY["HIGH"] = 0.10
        - ODOMETER_COUNTRY_UNKNOWN: usa ODOMETER_COUNTRY_PENALTY["UNKNOWN"] = 0.05
        """
        penalty_map = {
            FraudSeverity.WARNING: 0.05,
            FraudSeverity.SUSPICIOUS: 0.15,
            FraudSeverity.REJECTED: 1.00,  # score → 0, listing scartato
        }
        # Override per flag country-specific
        override_penalty = {
            "ODOMETER_COUNTRY_HIGH_RISK": ODOMETER_COUNTRY_PENALTY["HIGH"],
            "ODOMETER_COUNTRY_UNKNOWN": ODOMETER_COUNTRY_PENALTY["UNKNOWN"],
        }
        total = sum(
            override_penalty.get(f.code, penalty_map.get(f.severity, 0.0))
            for f in flags
        )
        return min(total, 1.0)


# ---------------------------------------------------------------------------
# QUICK TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    test_cases = [
        # (km, year, price, market_price, label)
        (45_000,  2020, 28_000, 32_000, "CLEAN — normale"),
        (120_000, 2020, 28_000, 32_000, "WARNING — km alti"),
        (200_000, 2019, 15_000, 28_000, "REJECTED — km assoluti + prezzo suspicious"),
        (500,     2021, 35_000, 36_000, "WARNING — km troppo bassi"),
        (38_000,  2020, 18_000, 32_000, "SUSPICIOUS — prezzo -44%"),
        (50_000,  2015, 22_000, 25_000, "REJECTED — anno fuori segmento"),
    ]

    print("\n" + "="*70)
    print("FRAUD FLAGS TEST — CoVe 2026")
    print("="*70)

    for km, year, price, mkt, label in test_cases:
        result = FraudFlagsChecker.run(km=km, year=year, price=price, market_price=mkt)
        print(f"\n[{result.overall.value:10}] {label}")
        print(f"  penalty={result.score_penalty:.2f} | flags={[f.code for f in result.flags]}")
        for f in result.flags:
            print(f"  → {f.code} {f.cove_tag}: {f.detail}")
