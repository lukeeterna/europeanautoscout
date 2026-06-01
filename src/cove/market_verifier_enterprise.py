"""
MarketVerifierEnterprise — Bridge tra CoVe Engine e MarketPriceIndex + ADAC
CoVe 2026 | Enterprise Grade | Zero Costi

DUAL-SOURCE price verification:
  1. MarketPriceIndex ARGOS (28+ portali EU reali) — primary
  2. ADAC Gebrauchtwagenpreise (gold standard DE) — secondary cross-reference

Il CoVe Engine v4 chiama:
    market_result = await self.market_verifier.verify(
        listing_id, make, model, year, km, price, vin
    )
    market_result.ref_price       → float
    market_result.ref_price_sigma → float
    market_result.stolen_check    → dict | None

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

try:
    from .market_price_index import MarketPriceIndex
except ImportError:
    from market_price_index import MarketPriceIndex

try:
    from .adac_price_reference import ADACPriceReference
except ImportError:
    try:
        from adac_price_reference import ADACPriceReference
    except ImportError:
        ADACPriceReference = None

logger = logging.getLogger("argos.market_verifier")


@dataclass
class MarketVerificationResult:
    """Risultato verifica market price — compatibile con CoVe Engine v4."""
    ref_price: Optional[float]
    ref_price_sigma: float
    sample_size: int
    data_quality: str
    stolen_check: Optional[dict] = None
    source: str = "argos_market_price_index"
    adac_ref: Optional[float] = None  # ADAC cross-reference (se disponibile)


class MarketVerifierEnterprise:
    """
    Market price verifier enterprise — DUAL SOURCE:
      1. MarketPriceIndex (28+ portali EU) — primary
      2. ADAC Gebrauchtwagenpreise — secondary cross-reference

    Se entrambe le fonti sono disponibili, la sigma si riduce (piu' certezza).
    """

    def __init__(self, duckdb_path: str = ""):
        self._index = MarketPriceIndex()
        self._adac = ADACPriceReference() if ADACPriceReference else None
        sources = ["MarketPriceIndex"]
        if self._adac:
            sources.append("ADAC")
        logger.info("MarketVerifierEnterprise: %s (%d chiavi indice)",
                     " + ".join(sources), len(self._index._index))

    async def verify(
        self,
        listing_id: str,
        make: str,
        model: str,
        year: int,
        km: int,
        price: float,
        vin: Optional[str] = None,
    ) -> MarketVerificationResult:
        """
        Verifica prezzo vs mercato EU usando dual-source.

        Triangolazione:
        - Se solo MarketPriceIndex: usa quella con sigma originale
        - Se solo ADAC: usa quella con sigma 0.20 (alta affidabilita)
        - Se entrambe: media ponderata, sigma ridotta (cross-confirmation)
        """
        estimate = self._index.estimate(make, model, year, km)
        adac_price = None

        # ADAC cross-reference (non blocca se fallisce)
        if self._adac:
            try:
                adac_est = self._adac.fetch(make, model, year, km)
                if adac_est:
                    adac_price = adac_est.price_mid
                    logger.info("ADAC: %s %s %d → EUR %.0f (%s)",
                               make, model, year, adac_price, adac_est.method)
            except Exception as e:
                logger.debug("ADAC fetch error: %s", e)

        has_index = estimate.ref_price > 0 and estimate.sample_size >= 2
        has_adac = adac_price is not None and adac_price > 0

        if has_index and has_adac:
            # DUAL SOURCE — triangolazione: media ponderata
            # Index: peso basato su sample_size, ADAC: peso fisso 0.4 (gold standard)
            index_weight = min(0.7, 0.3 + estimate.sample_size * 0.02)
            adac_weight = 1.0 - index_weight
            ref_price = estimate.ref_price * index_weight + adac_price * adac_weight
            # Sigma ridotta per cross-confirmation
            sigma = max(0.05, estimate.ref_price_sigma * 0.6)
            source = "argos_index+adac"
            quality = estimate.data_quality
            logger.info("MarketVerifier DUAL: EUR %.0f (index %.0f * %.0f + adac %.0f * %.0f) σ=%.3f",
                        ref_price, estimate.ref_price, index_weight, adac_price, adac_weight, sigma)

        elif has_index:
            ref_price = estimate.ref_price
            sigma = estimate.ref_price_sigma
            source = "argos_market_price_index"
            quality = estimate.data_quality

        elif has_adac:
            ref_price = adac_price
            sigma = 0.20  # ADAC = alta affidabilita ma singola fonte
            source = "adac_only"
            quality = "MEDIUM"

        else:
            logger.warning("MarketVerifier: nessun dato per %s %s %d", make, model, year)
            return MarketVerificationResult(
                ref_price=None,
                ref_price_sigma=0.50,
                sample_size=0,
                data_quality="NONE",
            )

        logger.info(
            "MarketVerifier: %s %s %d → EUR %.0f (n=%d, σ=%.3f, src=%s)",
            make, model, year, ref_price, estimate.sample_size, sigma, source,
        )

        return MarketVerificationResult(
            ref_price=ref_price,
            ref_price_sigma=sigma,
            sample_size=estimate.sample_size,
            data_quality=quality,
            source=source,
            adac_ref=adac_price,
        )

    def ingest_from_scraper(self, listings: list) -> int:
        """Ingerisce listing freschi dal scraper nel price index."""
        n = self._index.ingest_listings(listings)
        if n:
            self._index.save()
        return n
