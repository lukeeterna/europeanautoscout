"""
detail_enricher.py -- ARGOS Detail Page Enrichment Module
CoVe 2026 | Enterprise Grade

Enriches listings that have year=0 or km=0 by fetching the detail page
and extracting missing data from JSON-LD, meta tags, and HTML patterns.

Primary targets: Nordic portals (Finn.no, Blocket.se, DBA.dk) where
search-page JSON-LD lacks year/km, but detail pages have full data.

Works with ANY portal — extraction strategies are layered from
structured (JSON-LD) to semi-structured (meta tags) to regex fallback.

Author: ARGOS Automotive CTO Stack
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    from .models import Listing
    from .resilient_fetcher import ResilientFetcher
except ImportError:
    from models import Listing
    from resilient_fetcher import ResilientFetcher

logger = logging.getLogger("argos.detail_enricher")


# ---------------------------------------------------------------------------
# Portal-specific field labels (for HTML regex extraction)
# ---------------------------------------------------------------------------
# Maps portal domain fragments to (year_labels, km_labels) tuples.
# Labels are case-insensitive regex alternations.
_PORTAL_LABELS: Dict[str, Tuple[str, str]] = {
    "finn.no": (
        r"Årsmodell|Modellår|Registrert",
        r"Kilometerstand|Kilometer",
    ),
    "blocket.se": (
        r"Årsmodell|Modellår|Registreringsår",
        r"Miltal|Mätarställning|Kilometer|Mil",
    ),
    "dba.dk": (
        r"Årgang|Modelår|Registrerings.r",
        r"Kilometer|Km\.?\s*stand|Kilometertal",
    ),
}

# Generic labels that work across most EU portals
_GENERIC_YEAR_LABELS = r"Årsmodell|Årgang|Modellår|Model\s*year|Baujahr|Année|Anno|Rok|Year|Registrerings.r|Erstzulassung|1st\s*reg|Eerste\s*registratie|Bouwjaar|Registratiedatum|Datum\s*eerste\s*toelating"
_GENERIC_KM_LABELS = r"Kilometerstand|Kilometer|Miltal|Mätarställning|Mileage|Laufleistung|Kilométrage|Chilometraggio|Przebieg|Km\.?\s*stand"


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _safe_int(val: Any) -> int:
    """Parse a value to int, stripping separators. Returns 0 on failure."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    # Remove common thousands separators and units
    s = re.sub(r'\s*(km|mil|miles|kr|€)\s*', '', s, flags=re.IGNORECASE)
    s = s.replace('\xa0', '').replace(' ', '').replace('.', '').replace(',', '')
    # For "mil" (Scandinavian miles = 10 km), handled at caller level
    try:
        return int(s)
    except (ValueError, TypeError):
        return 0


def _safe_float(val: Any) -> float:
    """Parse a value to float, stripping separators. Returns 0.0 on failure."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    s = re.sub(r'\s*(EUR|€|kr|SEK|CZK|PLN)\s*', '', s, flags=re.IGNORECASE)
    s = s.replace('\xa0', '').replace(' ', '').rstrip(',-')
    # Handle European format: 27.800,50 or 27.800
    if ',' in s and '.' in s:
        if s.rindex(',') > s.rindex('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(',', '')
        elif len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif '.' in s:
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace('.', '')
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _extract_year_from_text(text: str) -> int:
    """Extract a plausible model year (2000-2026) from free text."""
    matches = re.findall(r'\b(20[0-2]\d)\b', text)
    for m in matches:
        y = int(m)
        if 2000 <= y <= 2026:
            return y
    return 0


def _is_mil_portal(domain: str) -> bool:
    """Check if portal uses Scandinavian 'mil' (1 mil = 10 km)."""
    return any(frag in domain for frag in ("blocket.se", "bytbil.se", "kvd.se"))


# ---------------------------------------------------------------------------
# JSON-LD extraction (Layer 1 — most reliable)
# ---------------------------------------------------------------------------

def _extract_from_jsonld(html: str) -> dict:
    """Extract year, km, and price from JSON-LD on detail page."""
    result: dict = {}

    # Find all JSON-LD blocks
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE,
    ):
        try:
            data = json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue

        # Handle @graph arrays
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if "@graph" in data:
                items = data["@graph"] if isinstance(data["@graph"], list) else [data["@graph"]]
            else:
                items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            item_type = item.get("@type", "")
            if isinstance(item_type, list):
                item_type = " ".join(item_type)

            # Look for Vehicle, Car, Product, or Offer types
            if not any(t in item_type for t in ("Vehicle", "Car", "Product", "Offer", "Auto")):
                # Also check nested offers
                if "offers" not in item and "name" not in item:
                    continue

            # Year extraction from JSON-LD
            if "year" not in result or result["year"] == 0:
                for key in ("modelDate", "vehicleModelDate", "productionDate",
                            "dateVehicleFirstRegistered", "releaseDate",
                            "model_year", "year", "modelYear"):
                    val = item.get(key)
                    if val:
                        y = _safe_int(str(val)[:4])
                        if 2000 <= y <= 2026:
                            result["year"] = y
                            break

                # Try nested vehicleConfiguration or additionalProperty
                for prop_key in ("additionalProperty", "vehicleConfiguration"):
                    props = item.get(prop_key, [])
                    if isinstance(props, dict):
                        props = [props]
                    if isinstance(props, list):
                        for prop in props:
                            if not isinstance(prop, dict):
                                continue
                            pname = str(prop.get("name", "")).lower()
                            if any(lbl in pname for lbl in ("year", "år", "årgang", "modell", "baujahr", "anno")):
                                y = _safe_int(prop.get("value", prop.get("unitText", "")))
                                if 2000 <= y <= 2026:
                                    result["year"] = y

            # Mileage extraction from JSON-LD
            if "km" not in result or result["km"] == 0:
                # schema.org mileageFromOdometer
                odo = item.get("mileageFromOdometer")
                if isinstance(odo, dict):
                    val = odo.get("value", odo.get("maxValue", 0))
                    km = _safe_int(val)
                    unit = str(odo.get("unitCode", odo.get("unitText", "KMT"))).upper()
                    if unit in ("SMI", "MI", "MILE"):
                        km = int(km * 1.60934)
                    if km > 0:
                        result["km"] = km
                elif odo is not None:
                    km = _safe_int(odo)
                    if km > 0:
                        result["km"] = km

                # Direct km/mileage fields
                for key in ("mileage", "km", "kilometer", "odometer", "milage"):
                    val = item.get(key)
                    if val:
                        km = _safe_int(val)
                        if km > 0:
                            result["km"] = km
                            break

                # additionalProperty for km
                for prop_key in ("additionalProperty", "vehicleConfiguration"):
                    props = item.get(prop_key, [])
                    if isinstance(props, dict):
                        props = [props]
                    if isinstance(props, list):
                        for prop in props:
                            if not isinstance(prop, dict):
                                continue
                            pname = str(prop.get("name", "")).lower()
                            if any(lbl in pname for lbl in ("km", "kilometer", "mileage", "miltal", "laufleistung")):
                                km = _safe_int(prop.get("value", ""))
                                if km > 0:
                                    result["km"] = km

            # Price extraction from JSON-LD
            if "price" not in result or result["price"] == 0:
                # schema.org offers.price
                offers = item.get("offers", item.get("offer", {}))
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                if isinstance(offers, dict):
                    price_raw = offers.get("price", offers.get("lowPrice"))
                    if price_raw is not None:
                        p = _safe_float(price_raw)
                        if 500 < p < 5_000_000:
                            result["price"] = p
                # Direct price field
                if "price" not in result:
                    for key in ("price", "priceSpecification"):
                        val = item.get(key)
                        if isinstance(val, dict):
                            val = val.get("price", val.get("value"))
                        if val is not None:
                            p = _safe_float(val)
                            if 500 < p < 5_000_000:
                                result["price"] = p
                                break

            # Color extraction from JSON-LD
            if "color" not in result:
                color = item.get("color", item.get("vehicleColor", ""))
                if isinstance(color, str) and color.strip():
                    result["color"] = color.strip()

            # Image URL extraction from JSON-LD
            if "image_url" not in result:
                img = item.get("image", item.get("photo", ""))
                if isinstance(img, str) and img.startswith("http"):
                    result["image_url"] = img
                elif isinstance(img, list) and img:
                    result["image_url"] = img[0] if isinstance(img[0], str) else str(img[0])

            # Fuel type from JSON-LD
            if "fuel_type" not in result:
                fuel = item.get("fuelType", item.get("fuel", ""))
                if isinstance(fuel, str) and fuel.strip():
                    result["fuel_type"] = fuel.strip().lower()

    return result


# ---------------------------------------------------------------------------
# Meta tags extraction (Layer 2)
# ---------------------------------------------------------------------------

def _extract_from_meta(html: str) -> Dict[str, int]:
    """Extract year and km from meta tags (og:*, product:*, etc.)."""
    result: Dict[str, int] = {}

    # Collect all meta tags content
    meta_tags: Dict[str, str] = {}
    for m in re.finditer(
        r'<meta\s+(?:property|name)=["\']([^"\']+)["\'][^>]*content=["\']([^"\']*)["\']',
        html, re.IGNORECASE,
    ):
        meta_tags[m.group(1).lower()] = m.group(2)

    # Also reversed attribute order
    for m in re.finditer(
        r'<meta\s+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    ):
        meta_tags[m.group(2).lower()] = m.group(1)

    # Year from meta
    for key in ("product:year", "vehicle:year", "og:year", "product:model_year",
                "vehicle:model_year", "product:registration_year"):
        if key in meta_tags:
            y = _safe_int(meta_tags[key][:4])
            if 2000 <= y <= 2026:
                result["year"] = y
                break

    # Km from meta
    for key in ("product:mileage", "vehicle:mileage", "product:km",
                "vehicle:km", "og:mileage", "product:odometer"):
        if key in meta_tags:
            km = _safe_int(meta_tags[key])
            if km > 0:
                result["km"] = km
                break

    # Try to get year from og:title or og:description
    if "year" not in result:
        for key in ("og:title", "og:description"):
            if key in meta_tags:
                y = _extract_year_from_text(meta_tags[key])
                if y > 0:
                    result["year"] = y
                    break

    return result


# ---------------------------------------------------------------------------
# HTML regex extraction (Layer 3 — portal-specific + generic)
# ---------------------------------------------------------------------------

def _extract_from_html_labels(html: str, domain: str) -> Dict[str, int]:
    """
    Extract year/km by finding label-value pairs in HTML.

    Strategy: find known labels (e.g., 'Årsmodell') and grab the adjacent
    numeric value, handling various HTML structures (tables, dl/dt/dd, spans).
    """
    result: Dict[str, int] = {}

    # Determine labels: portal-specific first, then generic fallback
    year_labels = _GENERIC_YEAR_LABELS
    km_labels = _GENERIC_KM_LABELS

    for portal_frag, (yl, kl) in _PORTAL_LABELS.items():
        if portal_frag in domain:
            year_labels = yl + "|" + _GENERIC_YEAR_LABELS
            km_labels = kl + "|" + _GENERIC_KM_LABELS
            break

    # Strip HTML tags for cleaner regex matching, but keep structure hints
    # Create a "flat" version with tag boundaries marked
    flat = re.sub(r'<[^>]+>', ' | ', html)
    flat = re.sub(r'\s+', ' ', flat)

    # --- Year extraction ---
    # Pattern: label ... value (within 100 chars)
    # Handles: "2021", "06/2018", "03-2020", "2021-06"
    year_pattern = (
        r'(?:' + year_labels + r')'
        r'[\s|:]*'
        r'(?:\d{1,2}[\s/.-])?'  # optional month prefix (06/ or 03-)
        r'(\d{4})'
    )
    m = re.search(year_pattern, flat, re.IGNORECASE)
    if m:
        y = int(m.group(1))
        if 2000 <= y <= 2026:
            result["year"] = y

    # Fallback: look in raw HTML for structured data (table cells, dd elements)
    if "year" not in result:
        # <th>Årsmodell</th><td>2021</td> or <dt>Årgang</dt><dd>2021</dd>
        for tag_pair in [("th", "td"), ("dt", "dd"), ("span", "span"), ("div", "div")]:
            pattern = (
                r'<' + tag_pair[0] + r'[^>]*>[\s]*(?:' + year_labels + r')[\s]*</' + tag_pair[0] + r'>'
                r'\s*<' + tag_pair[1] + r'[^>]*>[\s]*(.*?)</' + tag_pair[1] + r'>'
            )
            m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if m:
                y = _extract_year_from_text(m.group(1))
                if y > 0:
                    result["year"] = y
                    break

    # --- Km extraction ---
    km_pattern = (
        r'(?:' + km_labels + r')'
        r'[\s|:]*'
        r'([\d\s.,]+)'
    )
    m = re.search(km_pattern, flat, re.IGNORECASE)
    if m:
        raw_km = m.group(1).strip()
        km = _safe_int(raw_km)
        if km > 0:
            # Check if this is "mil" (Scandinavian) — multiply by 10
            # Look at context around match for "mil" unit
            context_start = max(0, m.start() - 20)
            context_end = min(len(flat), m.end() + 30)
            context = flat[context_start:context_end].lower()
            if _is_mil_portal(domain) and km < 100_000:
                # Check if "mil" is the unit (not "kilometer")
                if re.search(r'\bmil\b', context) and not re.search(r'kilometer', context):
                    km = km * 10
            result["km"] = km

    # Fallback: structured HTML for km
    if "km" not in result:
        for tag_pair in [("th", "td"), ("dt", "dd"), ("span", "span"), ("div", "div")]:
            pattern = (
                r'<' + tag_pair[0] + r'[^>]*>[\s]*(?:' + km_labels + r')[\s]*</' + tag_pair[0] + r'>'
                r'\s*<' + tag_pair[1] + r'[^>]*>[\s]*(.*?)</' + tag_pair[1] + r'>'
            )
            m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if m:
                raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                km = _safe_int(raw)
                if km > 0:
                    # Mil conversion for Scandinavian portals
                    if _is_mil_portal(domain) and km < 100_000:
                        full_context = m.group(0).lower()
                        if "mil" in full_context and "kilometer" not in full_context:
                            km = km * 10
                    result["km"] = km
                    break

    return result


# ---------------------------------------------------------------------------
# Title fallback (Layer 4 — last resort for year)
# ---------------------------------------------------------------------------

def _extract_year_from_title(html: str) -> int:
    """Extract year from <title> or <h1> tag as last resort."""
    for pattern in [r'<title[^>]*>(.*?)</title>', r'<h1[^>]*>(.*?)</h1>']:
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if m:
            text = re.sub(r'<[^>]+>', '', m.group(1))
            y = _extract_year_from_text(text)
            if y > 0:
                return y
    return 0


# ---------------------------------------------------------------------------
# Main enrichment orchestrator
# ---------------------------------------------------------------------------

def _extract_detail_data(html: str, domain: str) -> dict:
    """
    Multi-layer extraction from a detail page.

    Layers (in priority order):
      1. JSON-LD structured data
      2. Meta tags (og:*, product:*)
      3. HTML label-value regex (portal-specific + generic)
      4. Title/H1 fallback (year only)
      5. Price regex fallback

    Returns dict with 'year', 'km', and/or 'price' keys if found.
    """
    result: dict = {}

    # Layer 1: JSON-LD
    jsonld = _extract_from_jsonld(html)
    result.update(jsonld)

    # Layer 2: Meta tags (fill gaps)
    if "year" not in result or "km" not in result:
        meta = _extract_from_meta(html)
        if "year" not in result and "year" in meta:
            result["year"] = meta["year"]
        if "km" not in result and "km" in meta:
            result["km"] = meta["km"]

    # Layer 2b: Meta price (og:price, product:price)
    if "price" not in result:
        price_meta = _extract_price_from_meta(html)
        if price_meta > 0:
            result["price"] = price_meta

    # Layer 3: HTML label-value patterns
    if "year" not in result or "km" not in result:
        labels = _extract_from_html_labels(html, domain)
        if "year" not in result and "year" in labels:
            result["year"] = labels["year"]
        if "km" not in result and "km" in labels:
            result["km"] = labels["km"]

    # Layer 4: Title fallback (year only)
    if "year" not in result:
        y = _extract_year_from_title(html)
        if y > 0:
            result["year"] = y

    # Layer 5: Price regex fallback (EUR patterns in HTML)
    if "price" not in result:
        price_re = _extract_price_from_html(html)
        if price_re > 0:
            result["price"] = price_re

    # Layer 5b: Fuel type from HTML Kraftstoff label, title, URL slug
    if "fuel_type" not in result:
        fuel_text = ""

        # Source 1: HTML Kraftstoff/Fuel label (most reliable for AS24)
        kraft_match = re.search(
            r'(?:Kraftstoff|Fuel|Treibstoff)[^<]*?</[^>]+>\s*<[^>]+>([^<]+)',
            html, re.I,
        )
        if kraft_match:
            fuel_text = kraft_match.group(1).strip().lower()

        # Source 2: Fuel keyword in dd/span near fuel label
        if not fuel_text:
            dd_match = re.search(
                r'(?:Benzin|Diesel|Elektro|Hybrid|Plug-in)\s*</(?:dd|span)',
                html, re.I,
            )
            if dd_match:
                fuel_text = dd_match.group(0).split('<')[0].strip().lower()

        # Source 3: URL slug (e.g. ...-diesel-schwarz-UUID or ...-benzin-schwarz-UUID)
        if not fuel_text:
            slug = html  # fallback to full text for URL-based extraction
            for kw in ['plug-in-hybrid', 'plugin-hybrid', 'hybrid', 'elektro', 'diesel', 'benzin', 'electric', 'lpg', 'cng']:
                if kw in (result.get('_source_url', '') or '').lower():
                    fuel_text = kw
                    break

        # Source 4: Page title
        if not fuel_text:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
            if title_match:
                fuel_text = title_match.group(1).lower()

        # Map to standard fuel types
        if fuel_text:
            fuel_map = [
                ('plug-in', 'plugin_hybrid'), ('plugin', 'plugin_hybrid'), ('phev', 'plugin_hybrid'),
                ('elektro/benzin', 'hybrid'), ('elektro/diesel', 'hybrid'),
                ('hybrid', 'hybrid'),
                ('elektro', 'electric'), ('electric', 'electric'), ('bev', 'electric'),
                ('diesel', 'diesel'),
                ('benzin', 'petrol'), ('petrol', 'petrol'), ('gasoline', 'petrol'), ('ottomotor', 'petrol'),
                ('lpg', 'lpg'), ('autogas', 'lpg'),
                ('cng', 'cng'), ('erdgas', 'cng'),
            ]
            for keyword, fuel_val in fuel_map:
                if keyword in fuel_text:
                    result["fuel_type"] = fuel_val
                    break

    # Layer 6: Image URLs from og:image meta tag
    if "image_url" not in result:
        og_img = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)', html, re.I)
        if og_img:
            result["image_url"] = og_img.group(1)

    # Layer 6b: All image URLs from gallery (AS24 + generic portals)
    if "image_urls" not in result:
        # Strategy 0: __NEXT_DATA__ JSON (AS24 React — most images are here, not in HTML)
        gallery = []
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
        )
        if next_data_match:
            try:
                nd = json.loads(next_data_match.group(1))
                # AS24 stores images in props.pageProps.listingDetails.images (detail)
                # or props.pageProps.listings[].images (search)
                page_props = nd.get("props", {}).get("pageProps", {})
                nd_images = (
                    page_props.get("listingDetails", {}).get("images", [])
                    or page_props.get("listing", {}).get("images", [])
                )
                for img_url in nd_images:
                    if isinstance(img_url, str) and "listing-images" in img_url:
                        # Ensure HD resolution
                        if "1280x960" not in img_url:
                            # Try to construct HD URL from base
                            img_url = re.sub(r'/\d+x\d+\.', '/1280x960.', img_url)
                        gallery.append(img_url)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Strategy 1: Extract HD image URLs from JS/JSON strings (catches all AS24 images)
        if not gallery:
            gallery = re.findall(
                r'"(https://prod\.pictures\.autoscout24\.net/listing-images/[^"]*1280x960[^"]*\.jpg)"',
                html, re.I
            )
        # Strategy 2: src/srcset attributes (generic portals)
        if not gallery:
            gallery = re.findall(
                r'(?:src|srcset)=["\']?(https://[^"\'>\s]*listing-images[^"\'>\s]*(?:1280x960|640x480)[^"\'>\s]*\.(?:jpg|webp))',
                html, re.I
            )
        # Strategy 3: Any HD listing-images (webp ok, converter handles it)
        if not gallery:
            gallery = re.findall(
                r'"(https://[^"]*listing-images/[^"]*1280x960[^"]*)"',
                html, re.I
            )
        # Strategy 4: og:image fallback
        if not gallery:
            gallery = re.findall(
                r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)',
                html, re.I
            )
        if gallery:
            # Deduplicate by image UUID (the part before /resolution)
            seen = set()
            unique = []
            for u in gallery:
                u = u.rstrip('",;)')
                # Extract image UUID for dedup (e.g. ...UUID.jpg/1280x960.jpg)
                parts = u.split('/')
                # Find the part that looks like a UUID filename
                img_key = '/'.join(parts[-2:]) if len(parts) > 2 else u
                if img_key not in seen:
                    seen.add(img_key)
                    unique.append(u)
            result["image_urls"] = unique[:10]  # max 10 images

    # Layer 7: Description verbatim (S206 — corpus register)
    # Estratta da __NEXT_DATA__, JSON-LD, o HTML container comune.
    # Salvata in result["description"] senza trimming ne normalizzazione.
    if "description" not in result:
        desc = ""

        # Source 1: __NEXT_DATA__ (AS24 IT / React portals)
        if not desc:
            nd_match = re.search(
                r'<script id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
                html, re.DOTALL,
            )
            if nd_match:
                try:
                    nd = json.loads(nd_match.group(1).strip())
                    props = nd.get("props", {}).get("pageProps", {})
                    desc = (
                        props.get("listingDetails", {}).get("description", "") or
                        props.get("listing", {}).get("description", "") or
                        ""
                    )
                except Exception:
                    pass

        # Source 2: JSON-LD description
        if not desc:
            for m in re.finditer(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html, re.DOTALL | re.IGNORECASE,
            ):
                try:
                    data = json.loads(m.group(1).strip())
                    items_jld = data if isinstance(data, list) else [data]
                    for item in items_jld:
                        if isinstance(item, dict):
                            d = item.get("description", "")
                            if d and len(d) > 30:
                                desc = d
                                break
                except Exception:
                    pass
                if desc:
                    break

        # Source 3: HTML semantic containers
        if not desc:
            html_patterns = [
                r'<div[^>]*data-cy=["\']vehicle-description["\'][^>]*>(.*?)</div>',
                r'<div[^>]*id=["\']description["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
                r'<section[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</section>',
                r'<p[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</p>',
            ]
            for pat in html_patterns:
                m2 = re.search(pat, html, re.DOTALL | re.IGNORECASE)
                if m2:
                    raw = re.sub(r'<[^>]+>', ' ', m2.group(1))
                    raw = re.sub(r'\s+', ' ', raw).strip()
                    if len(raw) > 40:
                        desc = raw
                        break

        # Source 4: JSON string field in page JS (last resort)
        if not desc:
            m3 = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\["\\/bfnrtu]){40,})"', html)
            if m3:
                try:
                    desc = m3.group(1).encode('utf-8').decode('unicode_escape')
                except Exception:
                    desc = m3.group(1)

        if desc and isinstance(desc, str) and len(desc) > 20:
            result["description"] = desc.strip()

    return result


def _extract_price_from_meta(html: str) -> float:
    """Extract price from og:price or product:price:amount meta tags."""
    patterns = [
        r'<meta[^>]*property=["\'](?:og:price:amount|product:price:amount)["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\'](?:og:price:amount|product:price:amount)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            p = _safe_float(m.group(1))
            if 500 < p < 5_000_000:
                return p
    return 0.0


def _extract_price_from_html(html: str) -> float:
    """Extract price from common HTML patterns (EUR amounts)."""
    patterns = [
        re.compile(r'(?:EUR|€)\s*(\d{1,3}(?:[.\s]\d{3})+)', re.IGNORECASE),
        re.compile(r'(\d{1,3}(?:[.\s]\d{3})+)\s*(?:EUR|€)', re.IGNORECASE),
        re.compile(r'data-price=["\'](\d+)["\']'),
        re.compile(r'"price"\s*:\s*["\']?(\d[\d.,]+)'),
    ]
    for pat in patterns:
        m = pat.search(html)
        if m:
            p = _safe_float(m.group(1))
            if 500 < p < 5_000_000:
                return p
    return 0.0


# ---------------------------------------------------------------------------
# DetailEnricher class
# ---------------------------------------------------------------------------

class DetailEnricher:
    """
    Enriches listings with missing year/km by fetching detail pages.

    Uses ResilientFetcher for HTTP (multi-backend anti-bot) and
    rate-limits requests per portal domain (default: 2s between requests).

    Usage:
        enricher = DetailEnricher()
        enriched, attempted = enricher.enrich(listings)
    """

    def __init__(
        self,
        fetcher: Optional[ResilientFetcher] = None,
        delay_seconds: float = 2.0,
        max_failures_per_portal: int = 5,
    ):
        """
        Args:
            fetcher: ResilientFetcher instance (created if None).
            delay_seconds: Minimum delay between requests to same portal.
            max_failures_per_portal: Stop enriching a portal after N consecutive failures.
        """
        self._fetcher = fetcher or ResilientFetcher(timeout=25, max_retries=2)
        self._owns_fetcher = fetcher is None
        self._delay = delay_seconds
        self._max_failures = max_failures_per_portal
        # Track last request time per domain for rate limiting
        self._last_request: Dict[str, float] = {}
        # Track consecutive failures per domain
        self._consecutive_failures: Dict[str, int] = {}

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

    def _rate_limit(self, domain: str) -> None:
        """Wait if needed to respect per-portal rate limit."""
        last = self._last_request.get(domain, 0)
        elapsed = time.time() - last
        if elapsed < self._delay:
            wait = self._delay - elapsed
            logger.debug("[enricher] Rate-limit: sleeping %.1fs for %s", wait, domain)
            time.sleep(wait)
        self._last_request[domain] = time.time()

    def _should_skip_portal(self, domain: str) -> bool:
        """Check if we've had too many consecutive failures for this portal."""
        return self._consecutive_failures.get(domain, 0) >= self._max_failures

    def _needs_enrichment(self, listing: Listing) -> bool:
        """Check if a listing needs detail page enrichment."""
        return listing.year == 0 or listing.km == 0 or listing.price_eur == 0

    def enrich(self, listings: List[Listing]) -> Tuple[int, int]:
        """
        Enrich listings in-place by fetching detail pages for those
        missing year or km data.

        Args:
            listings: List of Listing objects. Modified in-place.

        Returns:
            Tuple of (enriched_count, total_attempted).
            enriched_count = listings where at least one field was filled.
            total_attempted = listings for which a detail page fetch was tried.
        """
        candidates = [l for l in listings if self._needs_enrichment(l) and l.listing_url]

        if not candidates:
            logger.info("[enricher] No listings need enrichment (all have year+km)")
            return 0, 0

        logger.info(
            "[enricher] Starting detail enrichment: %d/%d listings need year/km",
            len(candidates), len(listings),
        )

        # Group by domain for rate-limiting awareness
        enriched_count = 0
        attempted = 0
        skipped_portal = 0

        for listing in candidates:
            domain = self._get_domain(listing.listing_url)

            if self._should_skip_portal(domain):
                skipped_portal += 1
                continue

            # Rate limit per domain
            self._rate_limit(domain)
            attempted += 1

            try:
                html = self._fetcher.fetch(
                    listing.listing_url,
                    accept_language=self._accept_lang_for_domain(domain),
                )

                if not html or len(html) < 500:
                    logger.warning(
                        "[enricher] Empty/short response for %s", listing.listing_url
                    )
                    self._consecutive_failures[domain] = \
                        self._consecutive_failures.get(domain, 0) + 1
                    continue

                # Extract data from detail page
                data = _extract_detail_data(html, domain)

                # Apply enrichment
                filled = False
                if listing.year == 0 and data.get("year", 0) > 0:
                    listing.year = data["year"]
                    filled = True
                    logger.debug(
                        "[enricher] %s: year → %d", listing.listing_id, listing.year
                    )

                if listing.km == 0 and data.get("km", 0) > 0:
                    listing.km = data["km"]
                    filled = True
                    logger.debug(
                        "[enricher] %s: km → %d", listing.listing_id, listing.km
                    )

                if listing.price_eur == 0 and data.get("price", 0) > 0:
                    listing.price_eur = data["price"]
                    listing.price_current = data["price"]
                    filled = True
                    logger.debug(
                        "[enricher] %s: price → %.0f", listing.listing_id, listing.price_eur
                    )

                # Enrich image URLs from detail page (ALWAYS replace — search page has thumbnails)
                if data.get("image_urls"):
                    listing.image_urls = data["image_urls"]
                    filled = True
                elif data.get("image_url") and not listing.image_urls:
                    listing.image_urls = [data["image_url"]]
                    filled = True

                # Enrich description verbatim (S206 — corpus register)
                # Stored in extra_data["description"] (non-breaking for existing schema)
                if data.get("description") and not listing.extra_data.get("description"):
                    listing.extra_data["description"] = data["description"]
                    filled = True
                    logger.debug(
                        "[enricher] %s: description → %d chars",
                        listing.listing_id, len(data["description"]),
                    )

                # Enrich color (stored in extra_data since Listing has no color field)
                if data.get("color") and not listing.extra_data.get("color"):
                    listing.extra_data["color"] = data["color"]

                # Enrich fuel type
                if listing.fuel_type.value == "unknown" and data.get("fuel_type"):
                    from tools.scrapers.models import FuelType
                    fuel_map = {
                        "diesel": FuelType.DIESEL, "benzin": FuelType.PETROL,
                        "petrol": FuelType.PETROL, "gasoline": FuelType.PETROL,
                        "hybrid": FuelType.HYBRID, "electric": FuelType.ELECTRIC,
                        "elektro": FuelType.ELECTRIC, "plug-in": FuelType.PLUGIN_HYBRID,
                        "plugin": FuelType.PLUGIN_HYBRID, "lpg": FuelType.LPG,
                        "cng": FuelType.CNG,
                    }
                    raw = data["fuel_type"].lower()
                    for key, val in fuel_map.items():
                        if key in raw:
                            listing.fuel_type = val
                            break

                if filled:
                    enriched_count += 1
                    self._consecutive_failures[domain] = 0
                    n_img = len(listing.image_urls) if listing.image_urls else 0
                    logger.info(
                        "[enricher] Enriched %s: year=%d km=%d price=%.0f fuel=%s imgs=%d (from %s)",
                        listing.listing_id, listing.year, listing.km,
                        listing.price_eur, listing.fuel_type.value, n_img, domain,
                    )
                else:
                    # Fetched OK but couldn't extract — not a portal failure
                    logger.debug(
                        "[enricher] No new data extracted from %s",
                        listing.listing_url,
                    )

            except RuntimeError as exc:
                logger.warning(
                    "[enricher] Fetch failed for %s: %s", listing.listing_url, exc
                )
                self._consecutive_failures[domain] = \
                    self._consecutive_failures.get(domain, 0) + 1

            except Exception as exc:
                logger.error(
                    "[enricher] Unexpected error for %s: %s",
                    listing.listing_url, exc, exc_info=True,
                )
                self._consecutive_failures[domain] = \
                    self._consecutive_failures.get(domain, 0) + 1

        logger.info(
            "[enricher] Done: enriched %d/%d attempted (%d skipped due to portal failures)",
            enriched_count, attempted, skipped_portal,
        )

        return enriched_count, attempted

    def _accept_lang_for_domain(self, domain: str) -> str:
        """Return appropriate Accept-Language header for portal domain."""
        if "finn.no" in domain:
            return "nb-NO,nb;q=0.9,no;q=0.8,en;q=0.5"
        elif "blocket.se" in domain or "bytbil.se" in domain or "kvd.se" in domain:
            return "sv-SE,sv;q=0.9,en;q=0.5"
        elif "dba.dk" in domain or "bilbasen.dk" in domain:
            return "da-DK,da;q=0.9,en;q=0.5"
        elif ".de" in domain:
            return "de-DE,de;q=0.9,en;q=0.5"
        elif ".nl" in domain or "marktplaats" in domain:
            return "nl-NL,nl;q=0.9,en;q=0.5"
        elif ".fr" in domain:
            return "fr-FR,fr;q=0.9,en;q=0.5"
        elif ".it" in domain:
            return "it-IT,it;q=0.9,en;q=0.5"
        elif ".pl" in domain:
            return "pl-PL,pl;q=0.9,en;q=0.5"
        elif ".fi" in domain:
            return "fi-FI,fi;q=0.9,en;q=0.5"
        return "en-US,en;q=0.9"

    def close(self) -> None:
        """Clean up fetcher if we created it."""
        if self._owns_fetcher:
            self._fetcher.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
