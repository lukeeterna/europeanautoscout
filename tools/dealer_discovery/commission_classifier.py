#!/usr/bin/env python3
"""
ARGOS Dealer Discovery — Commission Classifier
Analizza un profilo dealer e determina se lavora "su commissione" del cliente.

Segnali forti:
  - Pochi annunci (3-15) con marche diverse = non specializzato = cerca per il cliente
  - Keyword "su richiesta", "cerchiamo per voi", ecc.
  - Alta rotazione stock (annunci che cambiano spesso)
  - Nessun sito web strutturato (solo Facebook)

Segnali deboli:
  - Foto da cellulare (non professionali)
  - Poche recensioni (< 30)
  - Indirizzo in zona residenziale
"""

import re
from typing import List, Optional
from tools.dealer_discovery.config import COMMISSION_KEYWORDS, PREMIUM_BRANDS, COMMISSION_SCORING


def classify_commission(
    listing_count: int,
    brands: List[str],
    descriptions: Optional[List[str]] = None,
    has_website: bool = False,
    review_count: int = 0,
    shop_description: str = "",
) -> dict:
    """
    Classify a dealer as commission-based or stock-based.

    Returns:
        dict with:
          - is_commission: bool
          - score: float (0-10)
          - signals: list of matched signals
          - confidence: "high" / "medium" / "low"
    """
    score = 0.0
    signals = []
    cfg = COMMISSION_SCORING

    # 1. Few listings (3-15)
    if cfg["few_listings_min"] <= listing_count <= cfg["few_listings_max"]:
        score += cfg["few_listings_weight"]
        signals.append(f"few_listings ({listing_count})")
    elif listing_count < cfg["few_listings_min"]:
        score += cfg["few_listings_weight"] * 0.3
        signals.append(f"very_few_listings ({listing_count})")
    elif listing_count <= 25:
        score += cfg["few_listings_weight"] * 0.2
        signals.append(f"moderate_listings ({listing_count})")

    # 2. Brand diversity
    unique_brands = len(set(b.upper() for b in brands))
    if unique_brands >= cfg["brand_diversity_min"]:
        score += cfg["brand_diversity_weight"]
        signals.append(f"brand_diversity ({unique_brands} brands)")
    elif unique_brands >= 3:
        score += cfg["brand_diversity_weight"] * 0.5
        signals.append(f"moderate_diversity ({unique_brands} brands)")

    # 3. Commission keywords in descriptions or shop description
    all_text = " ".join(descriptions or []) + " " + (shop_description or "")
    all_text_lower = all_text.lower()
    matched_kw = [kw for kw in COMMISSION_KEYWORDS if kw.lower() in all_text_lower]
    if matched_kw:
        score += cfg["keyword_match_weight"]
        signals.append(f"keywords: {', '.join(matched_kw[:3])}")

    # 4. Premium brand presence
    premium = [b for b in brands if b.upper() in [p.upper() for p in PREMIUM_BRANDS]]
    if premium:
        score += cfg["premium_presence_weight"]
        signals.append(f"premium_brands: {', '.join(premium[:3])}")

    # 5. No website (commission dealers often have no structured site)
    if not has_website:
        score += cfg["low_reviews_weight"] * 0.5
        signals.append("no_website")

    # 6. Low review count (< 30 = small operation)
    if 0 < review_count < 30:
        score += cfg["low_reviews_weight"]
        signals.append(f"low_reviews ({review_count})")

    # Determine classification
    is_commission = score >= cfg["threshold_commission"]

    # Confidence based on number of signals
    if len(signals) >= 4:
        confidence = "high"
    elif len(signals) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "is_commission": is_commission,
        "score": round(score, 2),
        "signals": signals,
        "confidence": confidence,
        "matched_keywords": matched_kw,
        "brand_diversity": unique_brands,
        "premium_brands": premium,
    }
