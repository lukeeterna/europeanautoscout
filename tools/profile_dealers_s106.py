#!/usr/bin/env python3
"""
profile_dealers_s106.py — Profila i 30 dealer target per S106.
Legge s104_dealer_enriched_wa.json, assegna: day1_variant, brand_focus,
premium_pct, archetipo, source. Scrive s106_dealer_profiled_30.json.

Archetipo heuristics (senza web scraping):
- NARCISO: brand luxury (Lambo, Porsche, Range Rover) + citta' grande
- BARONE: multi-brand premium forte, zona Sud, dealer storico
- RAGIONIERE: mono/dual brand, focus numeri, zona piccola
- TECNICO: BMW/Audi/Volvo focus, zone nord/centro
- RELAZIONALE: Sud, citta' piccola, brand mix
"""

import json
import os
import sys

# Import templates.py per select_day1_variant e brand sets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'wa-intelligence'))
from templates import (
    select_day1_variant, PREMIUM_BRANDS_CORE, PREMIUM_BRANDS_HIGH,
    PREMIUM_BRANDS_MEDIO, BRANDS_EVITARE
)

# Province del Sud Italia (per heuristic archetipo)
SUD_PROVINCES = {
    'NA', 'SA', 'AV', 'BN', 'CE',  # Campania
    'BA', 'BT', 'BR', 'FG', 'LE', 'TA',  # Puglia
    'CS', 'CZ', 'KR', 'RC', 'VV',  # Calabria
    'PA', 'CT', 'ME', 'AG', 'CL', 'EN', 'RG', 'SR', 'TP',  # Sicilia
    'CA', 'SS', 'NU', 'OR', 'SU',  # Sardegna
    'CB', 'IS',  # Molise
    'PZ', 'MT',  # Basilicata
}

LUXURY_BRANDS = {'lamborghini', 'porsche', 'range rover', 'bentley', 'maserati'}


def compute_premium_pct(brands: list) -> float:
    """Calcola % brand premium sul totale."""
    if not brands:
        return 0.0
    all_premium = PREMIUM_BRANDS_CORE | PREMIUM_BRANDS_HIGH | PREMIUM_BRANDS_MEDIO
    brands_lower = [b.lower().strip() for b in brands]
    premium_count = sum(1 for b in brands_lower if any(p in b for p in all_premium))
    return round(premium_count / len(brands_lower), 2)


def pick_brand_focus(brands: list) -> str:
    """Seleziona il brand premium principale da proporre nel messaggio."""
    # Priority: CORE > HIGH > MEDIO > primo disponibile
    brands_lower = [b.lower().strip() for b in brands]

    for b, original in zip(brands_lower, brands):
        if any(p in b for p in PREMIUM_BRANDS_CORE):
            return original
    for b, original in zip(brands_lower, brands):
        if any(p in b for p in PREMIUM_BRANDS_HIGH):
            return original
    for b, original in zip(brands_lower, brands):
        if any(p in b for p in PREMIUM_BRANDS_MEDIO):
            return original
    return brands[0] if brands else 'auto premium'


def classify_archetype(dealer: dict, premium_pct: float) -> str:
    """Classifica archetipo dealer con heuristics data-driven.

    NARCISO: luxury focus, brand aspirazionali, citta' media-grande
    BARONE: multi-brand premium, Sud, dealer che "comanda" la zona
    RAGIONIERE: focalizzato su numeri/margine, mono-brand, pragmatico
    TECNICO: focus qualita' tecnica, BMW/Audi/Volvo, tende Nord/Centro
    RELAZIONALE: Sud, citta' piccola, rapporto personale conta piu' del prezzo
    """
    brands = [b.lower() for b in dealer.get('premium_brands', [])]
    province = dealer.get('province', '')
    is_sud = province in SUD_PROVINCES
    n_brands = len(brands)
    has_luxury = any(any(l in b for l in LUXURY_BRANDS) for b in brands)

    # NARCISO: luxury brands (Lambo, Porsche, Range Rover, Maserati)
    if has_luxury and n_brands >= 2:
        return 'NARCISO'

    # BARONE: multi-brand premium, Sud, fit alto
    if is_sud and n_brands >= 3 and premium_pct >= 0.8:
        return 'BARONE'

    # TECNICO: mono/dual brand BMW o Audi o Volvo, tende Nord/Centro
    tech_brands = {'bmw', 'audi', 'volvo'}
    tech_match = sum(1 for b in brands if any(t in b for t in tech_brands))
    if tech_match >= 1 and n_brands <= 2 and not is_sud:
        return 'TECNICO'

    # RELAZIONALE: Sud, citta' piccola, pochi brand
    if is_sud and n_brands <= 2:
        return 'RELAZIONALE'

    # RAGIONIERE: default — pragmatico, focus margine
    return 'RAGIONIERE'


def determine_source(dealer: dict) -> str:
    """Determina fonte discovery verosimile per il messaggio DAY1."""
    # I dealer sono stati trovati via AS24/Subito/portali — usiamo source generica
    province = dealer.get('province', '')
    if province in SUD_PROVINCES:
        return 'Subito.it'
    return 'AutoScout24'


def profile_dealer(dealer: dict) -> dict:
    """Profila un singolo dealer con tutti i campi richiesti."""
    brands = dealer.get('premium_brands', [])
    premium_pct = compute_premium_pct(brands)
    brand_focus = pick_brand_focus(brands)
    day1_variant = select_day1_variant(brands)
    archetype = classify_archetype(dealer, premium_pct)
    source = determine_source(dealer)

    # Filtro brand da evitare dal brand_focus
    if brand_focus.lower() in BRANDS_EVITARE or any(
        e in brand_focus.lower() for e in BRANDS_EVITARE
    ):
        # Fallback: prendi il prossimo brand non in EVITARE
        for b in brands:
            if not any(e in b.lower() for e in BRANDS_EVITARE):
                brand_focus = b
                break
        else:
            brand_focus = 'auto premium'

    return {
        'dealer_id': dealer['id'],
        'name': dealer['name'],
        'phone_wa': dealer['phone_wa'],
        'province': dealer['province'],
        'city': dealer['city'],
        'brands': brands,
        'premium_pct': premium_pct,
        'day1_variant': day1_variant,
        'brand_focus': brand_focus,
        'archetype': archetype,
        'source_found': source,
        'fit_score': dealer.get('fit_score', 0),
    }


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'research', 's104_dealer_enriched_wa.json')
    output_path = os.path.join(base_dir, 'research', 's106_dealer_profiled_30.json')

    with open(input_path) as f:
        dealers = json.load(f)

    print(f'Profilazione {len(dealers)} dealer...\n')

    profiled = []
    for d in dealers:
        p = profile_dealer(d)
        profiled.append(p)
        print(f'  {p["name"]:30s} | {p["province"]} | {p["archetype"]:12s} | {p["day1_variant"]:16s} | focus: {p["brand_focus"]}')

    # Ordina per fit_score desc, poi per archetipo
    profiled.sort(key=lambda x: (-x['fit_score'], x['archetype']))

    with open(output_path, 'w') as f:
        json.dump(profiled, f, indent=2, ensure_ascii=False)

    print(f'\nScritto: {output_path}')
    print(f'\nDistribuzione archetipi:')
    from collections import Counter
    arch_count = Counter(p['archetype'] for p in profiled)
    for arch, count in arch_count.most_common():
        print(f'  {arch:15s}: {count}')

    variant_count = Counter(p['day1_variant'] for p in profiled)
    print(f'\nDistribuzione varianti DAY1:')
    for var, count in variant_count.most_common():
        print(f'  {var:20s}: {count}')

    print(f'\nTop 5 per fit_score:')
    for p in profiled[:5]:
        print(f'  {p["name"]:30s} | fit={p["fit_score"]} | {p["archetype"]} | {p["day1_variant"]}')


if __name__ == '__main__':
    main()
