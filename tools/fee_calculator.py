#!/usr/bin/env python3.11
"""
FEE CALCULATOR — ARGOS Automotive CoVe 2026
============================================
Calcolo fee e ROI per dealer IT.

Usage CLI:
    python3.11 tools/fee_calculator.py --price 27800 --tier 1
    python3.11 tools/fee_calculator.py --price 45000 --tier 3 --dealer-region sud

Usage Python:
    from tools.fee_calculator import FeeCalculator
    calc = FeeCalculator()
    result = calc.calculate(vehicle_price=27800, tier=1)
"""

import argparse
from dataclasses import dataclass
from typing import Literal

# ─── CONSTANTS ───────────────────────────────────────────────────────
TIER_CONFIG = {
    1: {
        "name": "Scouting Only",
        "description": "Ricerca EU + validazione + contatto venditore",
        "fee_min": 800,
        "fee_max": 1200,
        "fee_default": 800,
        "includes": ["Scheda ARGOS™", "VIN check", "Contatto venditore verificato"],
    },
    2: {
        "name": "Import Basic",
        "description": "Scouting + perizia videocall + supporto documentale",
        "fee_min": 800,
        "fee_max": 1200,
        "fee_default": 1000,
        "includes": ["Tutto Tier 1", "Perizia videocall", "Supporto documentale TD17/18/19"],
    },
    3: {
        "name": "Import Premium",
        "description": "All-inclusive: scouting + ispezione on-site + trasporto chiavi in mano",
        "fee_min": 1200,
        "fee_max": 2000,
        "fee_default": 1500,
        "includes": ["Tutto Tier 2", "Ispezione on-site", "Gestione trasporto", "Chiavi in mano IT"],
    },
}

# Margine dealer stimato per fascia prezzo
DEALER_MARGIN_BANDS = [
    (0,    15000, 0.08),   # <15k → 8% margine
    (15000, 30000, 0.10),  # 15-30k → 10%
    (30000, 50000, 0.12),  # 30-50k → 12%
    (50000, 999999, 0.14), # >50k → 14%
]

# Risparmio Fattura Svantaggiosa (reverse charge TD17/18/19)
FATTURA_SVANTAGGIOSA_SAVING = (150, 200)  # range €


@dataclass
class FeeResult:
    vehicle_price: float
    tier: int
    tier_name: str
    fee: float
    dealer_margin_est: float
    net_margin_after_fee: float
    fattura_svantaggiosa_saving: float
    roi_pct: float
    includes: list
    whatsapp_summary: str


class FeeCalculator:
    """Calcola fee ARGOS™ e ROI dealer per tier e fascia prezzo."""

    def calculate(
        self,
        vehicle_price: float,
        tier: int = 1,
        dealer_region: Literal["nord", "centro", "sud"] = "sud",
    ) -> FeeResult:
        if tier not in TIER_CONFIG:
            raise ValueError(f"Tier non valido: {tier}. Validi: 1, 2, 3")

        cfg = TIER_CONFIG[tier]
        fee = cfg["fee_default"]

        # Dealer margin estimate
        margin_pct = self._get_margin_pct(vehicle_price)
        dealer_margin_est = vehicle_price * margin_pct

        # Net margin after fee
        net_margin = dealer_margin_est - fee

        # Fattura svantaggiosa saving (media)
        fat_saving = sum(FATTURA_SVANTAGGIOSA_SAVING) / 2

        # ROI: net_margin / fee
        roi_pct = (net_margin / fee) * 100 if fee > 0 else 0

        # WhatsApp summary (max 4 righe)
        summary = self._build_whatsapp_summary(vehicle_price, tier, fee, net_margin, fat_saving)

        return FeeResult(
            vehicle_price=vehicle_price,
            tier=tier,
            tier_name=cfg["name"],
            fee=fee,
            dealer_margin_est=round(dealer_margin_est, 0),
            net_margin_after_fee=round(net_margin, 0),
            fattura_svantaggiosa_saving=fat_saving,
            roi_pct=round(roi_pct, 1),
            includes=cfg["includes"],
            whatsapp_summary=summary,
        )

    def _get_margin_pct(self, price: float) -> float:
        for lo, hi, pct in DEALER_MARGIN_BANDS:
            if lo <= price < hi:
                return pct
        return 0.10

    def _build_whatsapp_summary(
        self, price: float, tier: int, fee: float, net_margin: float, fat_saving: float
    ) -> str:
        cfg = TIER_CONFIG[tier]
        lines = [
            f"💰 Veicolo: €{price:,.0f} | Fee: €{fee:,.0f} success-only",
            f"📊 Margine netto stimato: €{net_margin:,.0f}",
            f"🧾 Fattura svantaggiosa: risparmio ~€{fat_saving:.0f}",
            f"🏆 Servizio: {cfg['name']} ({cfg['description']})",
        ]
        return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ARGOS™ Fee Calculator")
    parser.add_argument("--price", type=float, required=True, help="Prezzo veicolo EU (€)")
    parser.add_argument("--tier", type=int, default=1, choices=[1, 2, 3], help="Tier servizio (default: 1)")
    parser.add_argument("--dealer-region", default="sud", choices=["nord", "centro", "sud"])
    args = parser.parse_args()

    calc = FeeCalculator()
    r = calc.calculate(vehicle_price=args.price, tier=args.tier, dealer_region=args.dealer_region)

    print(f"\n{'='*55}")
    print(f"  ARGOS™ FEE CALCULATOR — Tier {r.tier}: {r.tier_name}")
    print(f"{'='*55}")
    print(f"  Prezzo veicolo    : €{r.vehicle_price:>10,.0f}")
    print(f"  Fee ARGOS™        : €{r.fee:>10,.0f}  (success-only)")
    print(f"  Margine dealer est: €{r.dealer_margin_est:>10,.0f}")
    print(f"  Margine netto     : €{r.net_margin_after_fee:>10,.0f}")
    print(f"  Fattura svantag.  : €{r.fattura_svantaggiosa_saving:>10.0f}  (risparmio)")
    print(f"  ROI dealer        :  {r.roi_pct:>9.1f}%")
    print(f"\n  Servizio include:")
    for item in r.includes:
        print(f"    ✅ {item}")
    print(f"\n  📱 WhatsApp snippet:")
    print(f"  {chr(10).join('  ' + l for l in r.whatsapp_summary.splitlines())}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
