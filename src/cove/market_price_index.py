"""
ARGOS Market Price Index — SOSTITUZIONE auto.dev (che e' US-ONLY!)
CoVe 2026 | Enterprise Grade | ZERO COSTI

Costruisce un indice prezzi EU in tempo reale dai nostri 28+ portali scraper.
Questo e' il CUORE del vantaggio competitivo ARGOS:
- Prezzi REALI da venditori REALI in 19 paesi EU
- Aggiornamento ad ogni run scraper
- Media ponderata per paese, con esclusione outlier
- Uncertainty calcolata da dispersione dati (piu' listing = piu' certezza)

Cross-industry reference:
- Zillow Zestimate: median error 2.4%, usa comparable sales (noi usiamo comparable listings)
- KBB/NADA: usa transaction data + listing data + depreciation curves
- DAT/Schwacke: gold standard DE, usa dealer transaction prices

Noi: listing prices from 28 portals, weighted by country reliability.
Non abbiamo transaction prices (yet) ma i listing prices sono il best proxy gratuito.

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import json
import logging
import math
import os
import statistics
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("argos.market_price_index")

# Persistenza indice su file JSON (zero dipendenze DB)
_INDEX_PATH = Path(__file__).parent / "data" / "market_price_index.json"

# ---------------------------------------------------------------------------
# Country weights — basati su maturita' mercato e affidabilita' dati
# Reference: ACEA EU registration data 2024, carVertical odometer fraud rates
# ---------------------------------------------------------------------------
COUNTRY_WEIGHTS: Dict[str, float] = {
    # Tier 1: mercati maturi, basso fraud, prezzi affidabili
    "DE": 1.00,  # Germania — benchmark EU
    "NL": 0.95,  # Olanda — NAP anti-odometer
    "BE": 0.95,  # Belgio — Car-Pass
    "AT": 0.90,  # Austria
    "SE": 0.85,  # Svezia — rigido enforcement
    "DK": 0.85,  # Danimarca — tasse alte ma prezzi netti affidabili
    "FI": 0.85,  # Finlandia
    "NO": 0.80,  # Norvegia — mercato EV-heavy, prezzi NOK
    # Tier 2: mercati intermedi
    "FR": 0.80,  # Francia
    "IT": 0.75,  # Italia — reference price per calcolo margine dealer
    "ES": 0.75,  # Spagna
    "PT": 0.70,  # Portogallo
    # Tier 3: mercati est EU — prezzi piu' bassi, fraud rate piu' alto
    "PL": 0.65,  # Polonia — mercato grande ma odometer fraud 5%+
    "CZ": 0.65,  # Repubblica Ceca
    "LT": 0.60,  # Lituania — fraud rate 7.8%
    "LV": 0.55,  # Lettonia — fraud rate 11.2%
    "EE": 0.60,  # Estonia
    "RO": 0.55,  # Romania — fraud rate 6.5%
    "BG": 0.50,  # Bulgaria — fraud rate >6%
    "HR": 0.60,  # Croazia
    "SI": 0.65,  # Slovenia
    "SK": 0.60,  # Slovacchia
    "HU": 0.55,  # Ungheria
}

# ---------------------------------------------------------------------------
# Tax adjustment — normalizza prezzi a "netto export" per cross-border comparison
# ---------------------------------------------------------------------------
# Alcuni paesi hanno tasse di registrazione INCLUSE nel prezzo annuncio.
# Per confrontare mele con mele, normalizziamo al prezzo NETTO (senza tasse locali).
#
# Reference:
#   DK: Registreringsafgift — 85% su primi 197,700 DKK + 150% sopra (2025)
#        Effetto: un'auto da 30k EUR netti viene annunciata a ~55-70k EUR
#        Fonte: skat.dk/registreringsafgift
#   NO: Engangsavgift — tassa basata su peso/CO2/NOx, piu' bassa per EV
#        Effetto: +20-40% su ICE, ~0% su EV
#        Fonte: skatteetaten.no/engangsavgift
#   NL: BPM (Belasting Personenauto's) — CO2-based, inclusa nel prezzo
#        Effetto: +10-25% su ICE, ~0% su EV
#        Fonte: belastingdienst.nl/bpm
#   FI: Autovero — CO2-based, 2.7-48.9%
#        Effetto: +5-20% medio
#        Fonte: vero.fi/autovero
#
# Fattore di sconto: moltiplica il prezzo annuncio per ottenere prezzo netto stimato.
# Questi sono STIME CONSERVATIVE — meglio sottostimare lo sconto che sovrastimarlo.
COUNTRY_TAX_DEFLATOR: Dict[str, float] = {
    "DK": 0.55,   # Prezzo DK ≈ 1.8x prezzo netto → *0.55 per normalizzare
    "NO": 0.75,   # Prezzo NO ≈ 1.3x prezzo netto (varia molto per CO2)
    "NL": 0.90,   # BPM relativamente basso, gia' nel prezzo
    "FI": 0.88,   # Autovero medio ~12%
    # Tutti gli altri paesi: prezzo annuncio ≈ prezzo netto (tasse a parte)
}

# Depreciation curve per anno (% valore residuo rispetto a nuovo)
# Reference: DAT residual values, ADAC Restwert
DEPRECIATION_CURVE = {
    0: 1.00,  # Nuovo
    1: 0.80,  # -20% primo anno (steepest drop)
    2: 0.70,  # -30%
    3: 0.62,  # -38%
    4: 0.55,  # -45%
    5: 0.48,  # -52%
    6: 0.42,  # -58%
    7: 0.37,  # -63%
    8: 0.33,  # -67%
}


@dataclass
class PricePoint:
    """Un singolo data point prezzo."""
    price_eur: float
    year: int
    km: int
    country: str
    portal: str
    listing_url: str = ""
    scraped_at: str = ""


@dataclass
class MarketPriceEstimate:
    """Stima prezzo di mercato con uncertainty."""
    ref_price: float          # Prezzo medio ponderato EU
    ref_price_sigma: float    # Uncertainty (0.05 = molto certo, 0.50 = quasi nessun dato)
    sample_size: int          # Quanti listing usati per la stima
    price_range: Tuple[float, float]  # (P10, P90)
    country_prices: Dict[str, float]  # Media per paese
    data_quality: str         # "HIGH" (>20 listing), "MEDIUM" (5-20), "LOW" (<5)


class MarketPriceIndex:
    """
    Indice prezzi EU costruito dai dati scraper ARGOS.

    Sostituisce auto.dev API (che era US-ONLY — bug critico scoperto S69).

    Architettura ispirata a:
    - Zillow: comparable sales con adjustment per features
    - KBB: listing + transaction weighted average
    - Bloomberg BVAL: multi-source aggregation con quality weighting
    """

    def __init__(self):
        self._index: Dict[str, List[PricePoint]] = defaultdict(list)
        self._load_persisted()

    def _make_key(self, make: str, model: str) -> str:
        return f"{make.upper()}_{model.upper()}"

    def _load_persisted(self):
        """Carica indice persistito da disco."""
        if _INDEX_PATH.exists():
            try:
                data = json.loads(_INDEX_PATH.read_text())
                for key, points in data.items():
                    self._index[key] = [PricePoint(**p) for p in points]
                logger.info("Market Price Index caricato: %d chiavi, %d price points",
                           len(self._index), sum(len(v) for v in self._index.values()))
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Errore caricamento indice: %s", e)

    def save(self):
        """Persisti indice su disco."""
        _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for key, points in self._index.items():
            data[key] = [asdict(p) for p in points]
        _INDEX_PATH.write_text(json.dumps(data, indent=2, default=str))
        logger.info("Market Price Index salvato: %d chiavi", len(self._index))

    def ingest_listings(self, listings: list) -> int:
        """
        Ingerisce listing dal scraper nell'indice.
        Accetta sia scraper Listing che dict con campi standard.
        Returns: numero di price points aggiunti.
        """
        added = 0
        for lst in listings:
            # Duck-typing: accetta oggetti con attributi o dict
            if hasattr(lst, 'price_eur'):
                price = lst.price_eur
                year = lst.year
                km = lst.km
                country = getattr(lst, 'country', '') or ''
                portal = getattr(lst, 'portal', '') or ''
                make = lst.make
                model = lst.model
                url = getattr(lst, 'listing_url', '') or ''
            elif isinstance(lst, dict):
                price = lst.get('price_eur', 0)
                year = lst.get('year', 0)
                km = lst.get('km', 0)
                country = lst.get('country', '')
                portal = lst.get('portal', '')
                make = lst.get('make', '')
                model = lst.get('model', '')
                url = lst.get('listing_url', '')
            else:
                continue

            # Validazione minima: prezzo e anno devono esistere
            if not price or price < 500 or price > 200_000:
                continue
            if not year or year < 2010:
                continue
            if not make or not model:
                continue

            # Tax normalization: DK/NO/NL/FI hanno tasse incluse nel prezzo annuncio
            country_code = country.upper()[:2] if country else ""
            deflator = COUNTRY_TAX_DEFLATOR.get(country_code, 1.0)
            if deflator < 1.0:
                price = price * deflator

            key = self._make_key(make, model)
            point = PricePoint(
                price_eur=float(price),
                year=int(year),
                km=int(km) if km else 0,
                country=country.upper()[:2] if country else "",
                portal=portal,
                listing_url=url,
                scraped_at=datetime.now(timezone.utc).isoformat(),
            )
            self._index[key].append(point)
            added += 1

        if added:
            logger.info("Ingeriti %d price points nell'indice", added)
        return added

    def estimate(
        self,
        make: str,
        model: str,
        year: int,
        km: int = 0,
    ) -> MarketPriceEstimate:
        """
        Stima prezzo di mercato per un veicolo specifico.

        Algoritmo:
        1. Trova tutti i price points per make/model
        2. Filtra per anno (±2 anni) e km (±30k se disponibile)
        3. Pesa per country reliability
        4. Calcola media ponderata + uncertainty
        5. Adjust per km difference se dati sufficienti

        Returns: MarketPriceEstimate con ref_price e sigma
        """
        key = self._make_key(make, model)
        all_points = self._index.get(key, [])

        if not all_points:
            return MarketPriceEstimate(
                ref_price=0, ref_price_sigma=0.50, sample_size=0,
                price_range=(0, 0), country_prices={}, data_quality="NONE",
            )

        # Step 1: Filtra per anno (±1 per premium, fallback ±2)
        year_filtered = [p for p in all_points if abs(p.year - year) <= 1]
        if len(year_filtered) < 3:
            year_filtered = [p for p in all_points if abs(p.year - year) <= 2]
        if not year_filtered:
            year_filtered = all_points  # fallback a tutto se nessun match anno

        # Step 2: Filtra per km (±30k) se km fornito e disponibile
        if km > 0:
            km_filtered = [p for p in year_filtered
                          if p.km > 0 and abs(p.km - km) <= 30_000]
            if len(km_filtered) >= 3:
                year_filtered = km_filtered

        # Step 3: Escludi outlier (P5-P95)
        prices = sorted(p.price_eur for p in year_filtered)
        if len(prices) >= 10:
            p5 = prices[len(prices) // 20]
            p95 = prices[int(len(prices) * 0.95)]
            filtered = [p for p in year_filtered if p5 <= p.price_eur <= p95]
            if len(filtered) >= 5:
                year_filtered = filtered

        # Step 4: Media ponderata per country
        weighted_sum = 0.0
        weight_total = 0.0
        country_prices: Dict[str, list] = defaultdict(list)

        for p in year_filtered:
            w = COUNTRY_WEIGHTS.get(p.country, 0.50)
            # Anno adjustment: listing piu' vicini al target anno pesano di piu'
            year_diff = abs(p.year - year)
            year_w = 1.0 / (1.0 + year_diff * 0.3)
            total_w = w * year_w

            weighted_sum += p.price_eur * total_w
            weight_total += total_w
            country_prices[p.country].append(p.price_eur)

        if weight_total == 0:
            return MarketPriceEstimate(
                ref_price=0, ref_price_sigma=0.50, sample_size=0,
                price_range=(0, 0), country_prices={}, data_quality="NONE",
            )

        ref_price = weighted_sum / weight_total
        n = len(year_filtered)

        # Step 5: Calcola uncertainty
        # Formula ispirata a Zillow: sigma decresce con sqrt(n), base su dispersione
        prices_list = [p.price_eur for p in year_filtered]
        if len(prices_list) >= 2:
            stdev = statistics.stdev(prices_list)
            cv = stdev / ref_price if ref_price > 0 else 0.5  # coefficient of variation
            sigma = max(0.05, min(0.45, cv / math.sqrt(n)))
        else:
            sigma = 0.40

        # Data quality classification
        if n >= 20:
            quality = "HIGH"
        elif n >= 5:
            quality = "MEDIUM"
        else:
            quality = "LOW"

        # Price range (P10-P90)
        if len(prices_list) >= 4:
            p10 = prices_list[max(0, len(prices_list) // 10)]
            p90 = prices_list[min(len(prices_list) - 1, int(len(prices_list) * 0.9))]
            price_range = (p10, p90)
        else:
            price_range = (min(prices_list), max(prices_list))

        # Country averages
        country_avgs = {
            c: round(sum(ps) / len(ps)) for c, ps in country_prices.items()
        }

        return MarketPriceEstimate(
            ref_price=round(ref_price, 2),
            ref_price_sigma=round(sigma, 4),
            sample_size=n,
            price_range=price_range,
            country_prices=country_avgs,
            data_quality=quality,
        )

    def find_opportunities(
        self,
        make: str,
        model: str,
        min_discount_pct: float = 0.08,
        max_results: int = 20,
    ) -> list:
        """
        Trova listing sotto la media di mercato per make/model.

        Un'OPPORTUNITA' e' un listing con prezzo < (media - min_discount_pct).
        Ordina per discount % decrescente.

        Cross-industry ref:
        - Commodity arbitrage: buy below fair value, sell at market
        - Insurance: total loss threshold = market value - repair cost
        """
        key = self._make_key(make, model)
        all_points = self._index.get(key, [])
        if not all_points:
            return []

        opportunities = []
        for point in all_points:
            if point.year < 2018 or point.price_eur < 500:
                continue

            estimate = self.estimate(make, model, point.year, point.km)
            if estimate.ref_price <= 0 or estimate.sample_size < 3:
                continue

            discount = (estimate.ref_price - point.price_eur) / estimate.ref_price
            if discount >= min_discount_pct:
                opportunities.append({
                    "listing": asdict(point),
                    "market_ref": estimate.ref_price,
                    "discount_pct": round(discount, 4),
                    "sigma": estimate.ref_price_sigma,
                    "sample_size": estimate.sample_size,
                    "data_quality": estimate.data_quality,
                    "country_avg": estimate.country_prices.get(point.country, estimate.ref_price),
                })

        opportunities.sort(key=lambda x: x["discount_pct"], reverse=True)
        return opportunities[:max_results]

    def get_stats(self) -> dict:
        """Statistiche indice corrente."""
        total_points = sum(len(v) for v in self._index.values())
        countries = set()
        portals = set()
        for points in self._index.values():
            for p in points:
                if p.country:
                    countries.add(p.country)
                if p.portal:
                    portals.add(p.portal)
        return {
            "total_keys": len(self._index),
            "total_price_points": total_points,
            "countries": sorted(countries),
            "portals": sorted(portals),
            "keys": sorted(self._index.keys()),
        }


# ---------------------------------------------------------------------------
# CLI Test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    idx = MarketPriceIndex()

    # Test con dati sintetici
    test_data = [
        {"make": "BMW", "model": "X3", "year": 2020, "km": 45000, "price_eur": 32000, "country": "DE", "portal": "autoscout24_de"},
        {"make": "BMW", "model": "X3", "year": 2020, "km": 52000, "price_eur": 29500, "country": "NL", "portal": "marktplaats_nl"},
        {"make": "BMW", "model": "X3", "year": 2020, "km": 38000, "price_eur": 34000, "country": "DE", "portal": "auto_de"},
        {"make": "BMW", "model": "X3", "year": 2020, "km": 48000, "price_eur": 27000, "country": "PL", "portal": "otomoto_pl"},
        {"make": "BMW", "model": "X3", "year": 2020, "km": 41000, "price_eur": 31500, "country": "BE", "portal": "2dehands_be"},
        {"make": "BMW", "model": "X3", "year": 2021, "km": 35000, "price_eur": 36000, "country": "DE", "portal": "autoscout24_de"},
        {"make": "BMW", "model": "X3", "year": 2019, "km": 62000, "price_eur": 25000, "country": "AT", "portal": "willhaben_at"},
        {"make": "BMW", "model": "X3", "year": 2020, "km": 50000, "price_eur": 22000, "country": "RO", "portal": "autovit_ro"},
    ]

    n = idx.ingest_listings(test_data)
    print(f"Ingeriti: {n} price points")

    est = idx.estimate("BMW", "X3", 2020, 45000)
    print(f"\nBMW X3 2020 ~45k km:")
    print(f"  Prezzo mercato EU: EUR {est.ref_price:,.0f}")
    print(f"  Sigma: {est.ref_price_sigma:.4f}")
    print(f"  Range P10-P90: EUR {est.price_range[0]:,.0f} - EUR {est.price_range[1]:,.0f}")
    print(f"  Campione: {est.sample_size} listing")
    print(f"  Quality: {est.data_quality}")
    print(f"  Per paese: {est.country_prices}")

    opps = idx.find_opportunities("BMW", "X3", min_discount_pct=0.05)
    print(f"\nOpportunita' ({len(opps)}):")
    for o in opps[:5]:
        l = o["listing"]
        print(f"  EUR {l['price_eur']:,.0f} vs mercato EUR {o['market_ref']:,.0f} "
              f"(-{o['discount_pct']:.1%}) | {l['country']} | {l['portal']}")
