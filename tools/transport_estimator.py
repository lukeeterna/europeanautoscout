"""
transport_estimator.py -- ARGOS Transport Cost Estimator
CoVe 2026 | Enterprise Grade | Zero Costi

Stima costi trasporto veicolo da paese EU origine a citta' dealer IT.
Integra nel dossier dealer: "Trasporto stimato: EUR 650 (Amburgo → Eboli, ~1.600 km)"

Metodi:
  1. Distanza stimata (km) × costo/km (bisarca vs drive-it-home)
  2. Lookup tabella rotte principali (calibrata su preventivi reali 2025-2026)
  3. Flat rate per paese se dati insufficienti

Reference:
  - Macingo.com preventivi reali 2024-2025
  - Clicktrans.com aste trasporto completate
  - Autorola Transport tariffe 2025
  - Costi reali autotrasporto Italia (gasolio + pedaggi + vignette)

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger("argos.transport")


# ---------------------------------------------------------------------------
# Distanze stimate (km) dalle citta' hub principali EU a citta' IT target
# Fonte: Google Maps route planner, percorso autostradale
# ---------------------------------------------------------------------------
# {(country_code, city_hub): {it_city: (distanza_km, ore_guida)}}
ROUTE_DISTANCES: Dict[Tuple[str, str], Dict[str, Tuple[int, float]]] = {
    # GERMANIA
    ("DE", "Amburgo"):    {"Eboli": (1850, 18), "Salerno": (1870, 18), "Napoli": (1900, 18.5), "Roma": (1650, 16), "Milano": (1100, 11)},
    ("DE", "Monaco"):     {"Eboli": (1250, 12), "Salerno": (1270, 12), "Napoli": (1280, 12.5), "Roma": (1050, 10), "Milano": (500, 5)},
    ("DE", "Francoforte"):{"Eboli": (1550, 15), "Salerno": (1570, 15), "Napoli": (1580, 15), "Roma": (1350, 13), "Milano": (800, 8)},
    ("DE", "Berlino"):    {"Eboli": (1950, 19), "Salerno": (1970, 19), "Napoli": (1980, 19), "Roma": (1750, 17), "Milano": (1200, 12)},
    ("DE", "Stoccarda"):  {"Eboli": (1350, 13), "Salerno": (1370, 13), "Napoli": (1380, 13.5), "Roma": (1150, 11), "Milano": (600, 6)},
    # OLANDA
    ("NL", "Amsterdam"):  {"Eboli": (1900, 18.5), "Salerno": (1920, 18.5), "Napoli": (1930, 19), "Roma": (1700, 17), "Milano": (1100, 11)},
    ("NL", "Rotterdam"):  {"Eboli": (1850, 18), "Salerno": (1870, 18), "Napoli": (1880, 18.5), "Roma": (1650, 16), "Milano": (1050, 10.5)},
    # BELGIO
    ("BE", "Bruxelles"):  {"Eboli": (1750, 17), "Salerno": (1770, 17), "Napoli": (1780, 17.5), "Roma": (1550, 15), "Milano": (950, 9.5)},
    ("BE", "Anversa"):    {"Eboli": (1800, 17.5), "Salerno": (1820, 17.5), "Napoli": (1830, 18), "Roma": (1600, 16), "Milano": (1000, 10)},
    # AUSTRIA
    ("AT", "Vienna"):     {"Eboli": (1300, 13), "Salerno": (1320, 13), "Napoli": (1330, 13), "Roma": (1100, 11), "Milano": (850, 8.5)},
    ("AT", "Salisburgo"):  {"Eboli": (1150, 11), "Salerno": (1170, 11), "Napoli": (1180, 11.5), "Roma": (950, 9.5), "Milano": (500, 5)},
    # FRANCIA
    ("FR", "Parigi"):     {"Eboli": (1700, 17), "Salerno": (1720, 17), "Napoli": (1730, 17), "Roma": (1500, 15), "Milano": (900, 9)},
    ("FR", "Lione"):      {"Eboli": (1350, 13), "Salerno": (1370, 13), "Napoli": (1380, 13.5), "Roma": (1150, 11.5), "Milano": (600, 6)},
    # SVEZIA
    ("SE", "Stoccolma"):  {"Eboli": (2800, 28), "Salerno": (2820, 28), "Napoli": (2830, 28), "Roma": (2600, 26), "Milano": (2050, 20)},
    ("SE", "Goteborg"):   {"Eboli": (2400, 24), "Salerno": (2420, 24), "Napoli": (2430, 24), "Roma": (2200, 22), "Milano": (1650, 16.5)},
    # DANIMARCA
    ("DK", "Copenaghen"): {"Eboli": (2200, 22), "Salerno": (2220, 22), "Napoli": (2230, 22), "Roma": (2000, 20), "Milano": (1450, 14.5)},
    # NORVEGIA
    ("NO", "Oslo"):       {"Eboli": (2700, 27), "Salerno": (2720, 27), "Napoli": (2730, 27), "Roma": (2500, 25), "Milano": (1950, 19.5)},
    # FINLANDIA (ferry Helsinki→Tallinn + drive, o ferry Helsinki→Travemunde)
    ("FI", "Helsinki"):   {"Eboli": (3200, 36), "Salerno": (3220, 36), "Napoli": (3230, 36), "Roma": (3000, 34), "Milano": (2450, 28)},
    # POLONIA
    ("PL", "Varsavia"):   {"Eboli": (2000, 20), "Salerno": (2020, 20), "Napoli": (2030, 20), "Roma": (1800, 18), "Milano": (1400, 14)},
    ("PL", "Danzica"):    {"Eboli": (2200, 22), "Salerno": (2220, 22), "Napoli": (2230, 22), "Roma": (2000, 20), "Milano": (1600, 16)},
    # REP. CECA
    ("CZ", "Praga"):      {"Eboli": (1500, 15), "Salerno": (1520, 15), "Napoli": (1530, 15), "Roma": (1300, 13), "Milano": (850, 8.5)},
    # ROMANIA
    ("RO", "Bucarest"):   {"Eboli": (1700, 20), "Salerno": (1720, 20), "Napoli": (1730, 20), "Roma": (1500, 18), "Milano": (1700, 19)},
    # PORTOGALLO
    ("PT", "Lisbona"):    {"Eboli": (2800, 27), "Salerno": (2820, 27), "Napoli": (2830, 27), "Roma": (2600, 25), "Milano": (2200, 22)},
    # BALTICI
    ("EE", "Tallinn"):    {"Eboli": (3100, 34), "Salerno": (3120, 34), "Napoli": (3130, 34), "Roma": (2900, 32), "Milano": (2350, 26)},
    ("LV", "Riga"):       {"Eboli": (2800, 30), "Salerno": (2820, 30), "Napoli": (2830, 30), "Roma": (2600, 28), "Milano": (2050, 22)},
    ("LT", "Vilnius"):    {"Eboli": (2500, 26), "Salerno": (2520, 26), "Napoli": (2530, 26), "Roma": (2300, 24), "Milano": (1750, 18)},
    # BULGARIA
    ("BG", "Sofia"):      {"Eboli": (1300, 15), "Salerno": (1320, 15), "Napoli": (1330, 15), "Roma": (1400, 16), "Milano": (1600, 17)},
}

# Flat rate per paese se non troviamo la rotta specifica
COUNTRY_FLAT_RATE: Dict[str, int] = {
    "DE": 700, "NL": 800, "BE": 750, "AT": 600, "FR": 750,
    "SE": 1200, "DK": 1000, "NO": 1300, "FI": 1400,
    "PL": 800, "CZ": 700, "RO": 900, "PT": 1200,
    "EE": 1300, "LV": 1200, "LT": 1100, "BG": 900,
    "ES": 1000, "HR": 600, "SI": 500, "SK": 700, "HU": 700,
    "IT": 200,  # Interno Italia
}

# Costi al km per metodo di trasporto
COST_PER_KM = {
    "bisarca": 0.45,       # EUR/km — bisarca professionale (media preventivi 2025)
    "carrello": 0.55,      # EUR/km — carrello singolo auto
    "drive": 0.22,         # EUR/km — guida diretta (gasolio + pedaggio + vignette)
}

# Costi fissi aggiuntivi
FIXED_COSTS = {
    "vignette_at": 11,     # Vignetta Austria 10 giorni
    "vignette_ch": 42,     # Vignetta Svizzera (se rotta via CH)
    "vignette_si": 16,     # Vignetta Slovenia 7 giorni
    "vignette_cz": 16,     # Vignetta Rep. Ceca 10 giorni
    "ferry_fi_de": 180,    # Ferry Helsinki → Travemunde (auto + conducente)
    "ferry_se_de": 120,    # Ferry Goteborg → Kiel (auto + conducente)
    "ferry_dk_de": 0,      # Oresund bridge gia' incluso nel pedaggio
}


@dataclass
class TransportEstimate:
    """Stima trasporto per un singolo veicolo."""
    origin_country: str
    origin_city: str
    destination_city: str
    distance_km: int
    drive_hours: float

    # Costi per metodo
    cost_bisarca: int       # Bisarca professionale
    cost_drive: int         # Drive-it-home
    cost_recommended: int   # Costo raccomandato (il piu' conveniente sicuro)
    method_recommended: str # "bisarca" | "drive" | "carrello"

    # Extra
    vignettes: int          # Costi vignette (se applicabili)
    ferry: int              # Costi ferry (se applicabili)
    notes: str              # Note per il dealer


def _find_closest_hub(country: str) -> Optional[Tuple[str, str]]:
    """Trova hub principale per un paese."""
    # Primo hub trovato per il paese
    for (cc, city) in ROUTE_DISTANCES:
        if cc == country:
            return (cc, city)
    return None


def _find_route(
    country: str,
    destination: str = "Eboli",
) -> Tuple[int, float, str]:
    """
    Trova distanza e tempo per una rotta specifica.
    Returns: (distanza_km, ore_guida, city_hub)
    """
    # Cerca tutte le rotte dal paese
    best = None
    for (cc, city), destinations in ROUTE_DISTANCES.items():
        if cc != country:
            continue
        if destination in destinations:
            km, hours = destinations[destination]
            if best is None or km < best[0]:
                best = (km, hours, city)

    if best:
        return best

    # Fallback: cerca qualsiasi citta' IT come destinazione
    for (cc, city), destinations in ROUTE_DISTANCES.items():
        if cc != country:
            continue
        # Prendi la prima destinazione come stima
        for dest, (km, hours) in destinations.items():
            if dest in ("Eboli", "Salerno", "Napoli"):
                return (km, hours, city)
        # Fallback a qualsiasi destinazione
        for dest, (km, hours) in destinations.items():
            return (km + 200, hours + 2, city)  # +200km stima

    return (0, 0, "")


def estimate_transport(
    origin_country: str,
    destination_city: str = "Eboli",
    vehicle_value: float = 0,
) -> TransportEstimate:
    """
    Stima costi trasporto da paese EU a citta' IT.

    Args:
        origin_country: Codice paese 2 lettere (DE, NL, BE, AT, ...)
        destination_city: Citta' destinazione IT (default Eboli per Autovanny)
        vehicle_value: Valore veicolo (per suggerire metodo: >40k → bisarca)

    Returns: TransportEstimate con costi per metodo
    """
    country = origin_country.upper()[:2]

    km, hours, hub_city = _find_route(country, destination_city)

    if km == 0:
        # Fallback flat rate
        flat = COUNTRY_FLAT_RATE.get(country, 900)
        return TransportEstimate(
            origin_country=country,
            origin_city="(stima)",
            destination_city=destination_city,
            distance_km=0,
            drive_hours=0,
            cost_bisarca=flat,
            cost_drive=int(flat * 0.6),
            cost_recommended=flat,
            method_recommended="bisarca",
            vignettes=0,
            ferry=0,
            notes=f"Stima flat rate per {country}. Richiedere preventivo specifico.",
        )

    # Calcola costi per metodo
    cost_bisarca = max(350, int(km * COST_PER_KM["bisarca"]))
    cost_drive = max(150, int(km * COST_PER_KM["drive"]))

    # Vignette (rotte tipiche)
    vignettes = 0
    route_notes = []
    if country in ("DE", "NL", "BE", "FR") and destination_city in ("Eboli", "Salerno", "Napoli"):
        # Rotta via Svizzera/Brennero
        vignettes += FIXED_COSTS["vignette_at"]  # Austria quasi sempre in rotta
        route_notes.append("Vignetta AT inclusa")

    if country in ("CZ", "PL"):
        vignettes += FIXED_COSTS.get("vignette_cz", 0)
        vignettes += FIXED_COSTS["vignette_at"]
        route_notes.append("Vignette CZ+AT incluse")

    if country in ("SI", "HR"):
        vignettes += FIXED_COSTS["vignette_si"]
        route_notes.append("Vignetta SI inclusa")

    # Ferry (paesi nordici/finlandia)
    ferry = 0
    if country == "FI":
        ferry = FIXED_COSTS["ferry_fi_de"]
        route_notes.append("Ferry Helsinki-Travemunde incluso")
    elif country == "SE" and km > 2000:
        ferry = FIXED_COSTS["ferry_se_de"]
        route_notes.append("Ferry Goteborg-Kiel incluso")

    cost_drive += vignettes + ferry
    cost_bisarca += ferry  # Bisarca include vignette nel prezzo ma non ferry

    # Metodo raccomandato
    if vehicle_value > 40000:
        method = "bisarca"
        recommended = cost_bisarca
        route_notes.append("Veicolo premium: bisarca raccomandata per sicurezza")
    elif km > 2000:
        method = "bisarca"
        recommended = cost_bisarca
        route_notes.append("Distanza lunga: bisarca piu' pratica")
    elif km < 800:
        method = "drive"
        recommended = cost_drive
        route_notes.append("Distanza breve: drive-it-home conveniente")
    else:
        # Confronto costi
        if cost_drive < cost_bisarca * 0.65:
            method = "drive"
            recommended = cost_drive
        else:
            method = "bisarca"
            recommended = cost_bisarca

    return TransportEstimate(
        origin_country=country,
        origin_city=hub_city,
        destination_city=destination_city,
        distance_km=km,
        drive_hours=hours,
        cost_bisarca=cost_bisarca,
        cost_drive=cost_drive,
        cost_recommended=recommended,
        method_recommended=method,
        vignettes=vignettes,
        ferry=ferry,
        notes=". ".join(route_notes) if route_notes else f"Rotta {hub_city} → {destination_city}",
    )


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_routes = [
        ("DE", "Eboli", 30000),
        ("NL", "Eboli", 28000),
        ("BE", "Eboli", 25000),
        ("AT", "Salerno", 35000),
        ("SE", "Eboli", 45000),
        ("FI", "Napoli", 32000),
        ("PL", "Eboli", 22000),
        ("RO", "Salerno", 18000),
        ("BG", "Eboli", 20000),
    ]

    print(f"\n{'='*80}")
    print("ARGOS TRANSPORT ESTIMATOR — Preventivi EU→IT")
    print(f"{'='*80}")

    for country, dest, value in test_routes:
        est = estimate_transport(country, dest, value)
        print(f"\n{est.origin_country} ({est.origin_city}) → {est.destination_city}")
        print(f"  Distanza: {est.distance_km:,} km | {est.drive_hours:.0f}h guida")
        print(f"  Bisarca:  EUR {est.cost_bisarca:,}")
        print(f"  Drive:    EUR {est.cost_drive:,}")
        print(f"  → Raccomandato: EUR {est.cost_recommended:,} ({est.method_recommended})")
        if est.notes:
            print(f"  Note: {est.notes}")
