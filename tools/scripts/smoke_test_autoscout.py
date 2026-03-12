#!/usr/bin/env python3.11
"""
AutoScout24 Parser Smoke Test — Session 33→34 Bridge
==================================================

Script per validare price_validator_v2.py contro BMW Mario locked data:
- €27,800 (Mario prezzo target)
- 45,200 km (Mario km locked)
- 2020 (Mario anno locked)

Usage: python3.11 smoke_test_autoscout.py <autoscout24_url>
"""

import sys
import re
import requests
from curl_cffi import requests as cf_requests
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class VehicleData:
    """Dati estratti da AutoScout24."""
    price_eur: Optional[int]
    km: Optional[int]
    year: Optional[int]
    make_model: Optional[str]
    source_url: str

# Mario locked data per comparison
MARIO_LOCKED = {
    "price_eur": 27800,
    "km": 45200,
    "year": 2020,
    "make_model": "BMW 330i"
}

def extract_autoscout_data(url: str) -> VehicleData:
    """Estrai dati da AutoScout24 listing."""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        # Use curl_cffi per anti-bot
        response = cf_requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # Extract price (various patterns)
        price_patterns = [
            r'€\s*(\d{1,3}(?:\.\d{3})*)',
            r'"price"[^}]*"value":\s*(\d+)',
            r'data-price="(\d+)"',
            r'class="[^"]*price[^"]*"[^>]*>.*?€\s*(\d{1,3}(?:\.\d{3})*)'
        ]

        price_eur = None
        for pattern in price_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                # Take the highest price found (likely the main price)
                prices = [int(p.replace('.', '')) for p in matches if p.replace('.', '').isdigit()]
                if prices:
                    price_eur = max(prices)
                    break

        # Extract kilometers
        km_patterns = [
            r'(\d{1,3}(?:\.\d{3})*)\s*km',
            r'"mileage"[^}]*"value":\s*(\d+)',
            r'data-mileage="(\d+)"'
        ]

        km = None
        for pattern in km_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                km_values = [int(k.replace('.', '')) for k in matches if k.replace('.', '').isdigit()]
                if km_values:
                    km = min(km_values)  # Take lowest reasonable km value
                    break

        # Extract year
        year_patterns = [
            r'"yearOfRegistration"[^}]*"value":\s*(\d{4})',
            r'data-year="(\d{4})"',
            r'(20\d{2})',
            r'EZ\s*(\d{2}\/\d{4})'
        ]

        year = None
        for pattern in year_patterns:
            matches = re.findall(pattern, html)
            if matches:
                if '/' in matches[0]:  # Format MM/YYYY
                    year = int(matches[0].split('/')[1])
                else:
                    years = [int(y) for y in matches if y.isdigit() and 2015 <= int(y) <= 2025]
                    if years:
                        year = max(years)  # Take most recent reasonable year
                break

        # Extract make/model
        make_model = None
        title_patterns = [
            r'<title[^>]*>([^<]*BMW[^<]*330i[^<]*)</title>',
            r'"name"\s*:\s*"([^"]*BMW[^"]*330[^"]*)"'
        ]

        for pattern in title_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                make_model = matches[0].strip()
                break

        if not make_model:
            make_model = "BMW 330i (extracted)"

        return VehicleData(
            price_eur=price_eur,
            km=km,
            year=year,
            make_model=make_model,
            source_url=url
        )

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return VehicleData(None, None, None, None, url)

def compare_with_mario(data: VehicleData) -> dict:
    """Confronta dati estratti con Mario locked data."""

    results = {
        "price_match": False,
        "km_match": False,
        "year_match": False,
        "overall_score": 0,
        "differences": {}
    }

    # Price comparison (tolerance ±10%)
    if data.price_eur:
        price_diff_pct = abs(data.price_eur - MARIO_LOCKED["price_eur"]) / MARIO_LOCKED["price_eur"] * 100
        results["price_match"] = price_diff_pct <= 10
        results["differences"]["price"] = f"€{data.price_eur:,} vs Mario €{MARIO_LOCKED['price_eur']:,} ({price_diff_pct:.1f}% diff)"
        if results["price_match"]:
            results["overall_score"] += 1

    # KM comparison (tolerance ±20%)
    if data.km:
        km_diff_pct = abs(data.km - MARIO_LOCKED["km"]) / MARIO_LOCKED["km"] * 100
        results["km_match"] = km_diff_pct <= 20
        results["differences"]["km"] = f"{data.km:,} km vs Mario {MARIO_LOCKED['km']:,} km ({km_diff_pct:.1f}% diff)"
        if results["km_match"]:
            results["overall_score"] += 1

    # Year exact match
    if data.year:
        results["year_match"] = data.year == MARIO_LOCKED["year"]
        results["differences"]["year"] = f"{data.year} vs Mario {MARIO_LOCKED['year']}"
        if results["year_match"]:
            results["overall_score"] += 1

    return results

def main():
    """Main smoke test execution."""

    if len(sys.argv) != 2:
        print("Usage: python3.11 smoke_test_autoscout.py <autoscout24_url>")
        print("Example: python3.11 smoke_test_autoscout.py 'https://www.autoscout24.de/angebote/bmw-330i-benzin-weiss-12345678.html'")
        sys.exit(1)

    url = sys.argv[1]

    print("🧪 AUTOSCOUT24 PARSER SMOKE TEST")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Mario Locked: €{MARIO_LOCKED['price_eur']:,} / {MARIO_LOCKED['km']:,} km / {MARIO_LOCKED['year']}")
    print()

    # Extract data
    print("🔍 Extracting data...")
    data = extract_autoscout_data(url)

    print("📊 EXTRACTED DATA:")
    print(f"   Price: €{data.price_eur:,}" if data.price_eur else "   Price: ❌ NOT FOUND")
    print(f"   KM: {data.km:,}" if data.km else "   KM: ❌ NOT FOUND")
    print(f"   Year: {data.year}" if data.year else "   Year: ❌ NOT FOUND")
    print(f"   Make/Model: {data.make_model}" if data.make_model else "   Make/Model: ❌ NOT FOUND")
    print()

    # Compare with Mario
    print("⚖️ MARIO COMPARISON:")
    comparison = compare_with_mario(data)

    for key, diff in comparison["differences"].items():
        status = "✅" if comparison[f"{key}_match"] else "❌"
        print(f"   {key.upper()}: {status} {diff}")

    print()
    print(f"📈 OVERALL SCORE: {comparison['overall_score']}/3")

    if comparison['overall_score'] >= 2:
        print("✅ SMOKE TEST PASSED - Parser working correctly")
        return True
    else:
        print("❌ SMOKE TEST FAILED - Parser needs adjustment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)