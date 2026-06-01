#!/usr/bin/env python3
"""
ARGOS DEALER TARGET PROFILES & REGIONAL SCOUTING ENGINE
========================================================
Definisce TIPI di target, REGIONI, e combina tutto per generare
pipeline di scouting automatizzato.

Usage:
    python3 tools/dealer_target_profiles.py list-targets
    python3 tools/dealer_target_profiles.py list-regions
    python3 tools/dealer_target_profiles.py scout --target GROWTH --region campania
    python3 tools/dealer_target_profiles.py scout --target IMPORTER --region puglia
    python3 tools/dealer_target_profiles.py plan --target ALL --region sud-italia
    python3 tools/dealer_target_profiles.py match-vehicle --target GROWTH --vehicle "BMW X3"

Il sistema sceglie automaticamente:
- Criteri di scoring per tipo target
- Messaggi per archetipo + tipo target
- Veicoli da proporre per fascia dealer
- Timing e canale per regione

Author: ARGOS Automotive CoVe 2026
"""

import json
import sys
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# SEZIONE 1: TIPI DI TARGET
# ══════════════════════════════════════════════════════════════

TARGET_PROFILES = {
    "IMPORTER": {
        "name": "Dealer che GIA' importa da EU",
        "description": "Fa gia' import EU ma da solo. Conosce costi e rischi. "
                       "Non serve educare — serve dimostrare che ARGOS e' meglio del fai-da-te.",
        "priority": 1,  # massima
        "ideal": {
            "stock": (15, 60),
            "years": (3, 20),
            "premium_pct": (20, 100),
            "reviews": (20, 500),
            "rating": (3.8, 5.0),
        },
        "signals": [
            "dichiara 'importazioni' su AutoScout24 o sito",
            "sito multilingua (DE/EN/FR)",
            "titolare ha vissuto/lavorato in EU",
            "stock con auto chiaramente EU (targhe, allestimenti DE)",
            "menziona 'Germania' 'Belgio' 'estero' nei contenuti",
        ],
        "pitch_angle": "Fai gia' import? Quanto ti costa in tempo e rischio? "
                       "Con ARGOS: 73 portali, 19 paesi, paghi ZERO finche' non hai l'auto.",
        "objection_primary": "OBJ-3: Ho gia' i miei canali",
        "objection_handler": "Non ti chiedo di cambiare canale. Ti apro portali che "
                             "da solo non raggiungi — olandesi, belgi, svedesi, cechi. "
                             "I prezzi li' sono diversi da Mobile.de.",
        "vehicle_strategy": "Portale NICCHIA (non AutoScout24/Mobile.de). "
                            "Veicolo da NL/BE/SE/AT che il dealer non trova da solo.",
        "archetypes_likely": ["PERFORMANTE", "NARCISO", "TECNICO"],
    },

    "GROWTH": {
        "name": "Dealer che VUOLE crescere nel premium",
        "description": "Ha 20-40 auto, vende mix generico, ha 2-3 premium in stock. "
                       "Vuole differenziarsi e alzare i margini ma non ha i canali EU.",
        "priority": 2,
        "ideal": {
            "stock": (20, 40),
            "years": (3, 8),
            "premium_pct": (10, 40),
            "reviews": (25, 100),
            "rating": (3.8, 4.5),
        },
        "signals": [
            "2-3 BMW/Mercedes/Audi in stock su 20-30 auto totali",
            "titolare under-45, seconda generazione",
            "social attivo (Instagram/Facebook con post regolari)",
            "recensioni Google 3.8-4.4 (buono ma non leader)",
            "'acquistiamo auto' o 'compriamo il tuo usato' su sito/social",
        ],
        "pitch_angle": "Il premium cresce +17% l'anno. I tuoi clienti vogliono BMW "
                       "e Porsche. Ti apro la porta del mercato piu' redditizio — "
                       "e non paghi nulla finche' non hai il veicolo in mano.",
        "objection_primary": "OBJ-1: Non ti conosco / OBJ-4: Non ho esperienza con import",
        "objection_handler": "Zero rischio per te. Success fee solo a consegna. "
                             "Ti mando un veicolo verificato con tutti i numeri. "
                             "Se non ti convince, non paghi un euro.",
        "vehicle_strategy": "BMW X3/X5 o Mercedes GLC/GLE — i modelli piu' "
                            "venduti nel premium usato IT. Fascia €25-40k. "
                            "Delta EU-IT €4.000-8.000.",
        "archetypes_likely": ["RAGIONIERE", "PERFORMANTE", "RELAZIONALE"],
    },

    "LUXURY": {
        "name": "Dealer luxury/super-premium",
        "description": "Tratta Porsche, Lamborghini, Ferrari, Range Rover. "
                       "Stock piccolo (10-30 auto) ma fascia alta (€40-200k). "
                       "Cerca veicoli specifici su richiesta cliente.",
        "priority": 3,
        "ideal": {
            "stock": (8, 30),
            "years": (3, 20),
            "premium_pct": (60, 100),
            "reviews": (15, 300),
            "rating": (4.0, 5.0),
        },
        "signals": [
            "Porsche, Lamborghini, Ferrari, Bentley in stock",
            "positioning dichiarato 'luxury' o 'prestige'",
            "fascia prezzo media > €50k",
            "showroom curato (foto professionali)",
        ],
        "pitch_angle": "Ho accesso a Porsche e BMW M/AMG su portali europei "
                       "con config rare che in Italia non si trovano. "
                       "Le cerco io, lei sceglie.",
        "objection_primary": "OBJ-5: Cerco solo veicoli specifici su richiesta",
        "objection_handler": "Perfetto — mi dica cosa cerca il suo cliente e glielo "
                             "trovo in 5-7 giorni su 73 portali in 19 paesi. "
                             "Paga solo se lo prende.",
        "vehicle_strategy": "Porsche 911/Macan/Cayenne config rara, BMW M3/M4/X5M, "
                            "Mercedes AMG, Range Rover Sport. Fascia €50-120k. "
                            "Focus su allestimenti/colori rari.",
        "archetypes_likely": ["BARONE", "NARCISO"],
    },

    "MONO_BRAND": {
        "name": "Dealer specializzato mono-brand premium",
        "description": "Vende principalmente un brand (es. solo Mercedes, solo BMW). "
                       "Conosce il prodotto alla perfezione. Vuole stock mirato.",
        "priority": 4,
        "ideal": {
            "stock": (15, 50),
            "years": (5, 25),
            "premium_pct": (70, 100),
            "reviews": (20, 200),
            "rating": (4.0, 5.0),
        },
        "signals": [
            "80%+ dello stock e' un solo brand premium",
            "officina/service dello stesso brand annesso",
            "competenza tecnica evidente dalle descrizioni",
        ],
        "pitch_angle": "Lei conosce le {brand} meglio di chiunque. "
                       "Io le trovo in Europa a prezzi che qui non esistono. "
                       "Stesso brand, stessa qualita', margine doppio.",
        "objection_primary": "OBJ-3: Ho gia' i miei canali per {brand}",
        "objection_handler": "I portali di nicchia ({country_portals}) hanno "
                             "{brand} con allestimenti che in Italia non arrivano. "
                             "Le mando un esempio concreto?",
        "vehicle_strategy": "Stesso brand del dealer, allestimenti rari o "
                            "versioni non importate in Italia. Focus su spec sheet.",
        "archetypes_likely": ["TECNICO", "RAGIONIERE"],
    },

    "VOLUME": {
        "name": "Dealer medio-grande che vuole canale EU ricorrente",
        "description": "Ha 40-80 auto, struttura commerciale, cerca volume. "
                       "Non compra 1 auto — ne compra 3-5/mese se il canale funziona.",
        "priority": 5,
        "ideal": {
            "stock": (40, 80),
            "years": (5, 20),
            "premium_pct": (15, 60),
            "reviews": (50, 500),
            "rating": (3.8, 5.0),
        },
        "signals": [
            "stock > 40 auto",
            "rotazione alta (annunci cambiano spesso)",
            "piu' sedi o filiali",
            "team vendita (non solo titolare)",
        ],
        "pitch_angle": "Su 10 auto premium EU al mese, il margine extra e' "
                       "€30-45k. Gestisco io sourcing e burocrazia. "
                       "Lei si concentra sulla vendita.",
        "objection_primary": "OBJ-3: Ho gia' fornitori / OBJ-6: Voglio volumi garantiti",
        "objection_handler": "Non chiedo esclusiva. Provi con 2-3 auto il primo mese. "
                             "Se i numeri funzionano, scaliamo insieme.",
        "vehicle_strategy": "Mix BMW X3/X5 + Mercedes GLC/GLE + Audi Q5. "
                            "3-5 veicoli diversi nella prima proposta. "
                            "Mostrare capacita' di VOLUME.",
        "archetypes_likely": ["RAGIONIERE", "PERFORMANTE"],
    },
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 2: REGIONI E PROVINCE
# ══════════════════════════════════════════════════════════════

REGIONS = {
    "campania": {
        "name": "Campania",
        "provinces": ["Napoli", "Salerno", "Caserta", "Avellino", "Benevento"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/campania/",
        "characteristics": {
            "density": "alta (Napoli metro), bassa (Irpinia/Sannio)",
            "premium_appetite": "medio-alto (Napoli), medio (province)",
            "digital_maturity": "media",
            "competition": "alta Napoli, bassa province",
            "best_timing": "mart/merc 8:30-9:00",
            "tone": "formale ma caldo, relazionale",
        },
        "nearby_cities_for_fomo": ["Napoli", "Salerno", "Caserta"],
        "known_dealers": [
            "Autovanny Group (SA) — NARCISO 8.5 — in pipeline",
            "FC Luxury (SA) — BARONE 8.0 — in pipeline",
            "Car Plus (AV) — PERFORMANTE 7.8 — TIER_0_IMPORT",
            "BD Auto (CE) — BARONE 8.5",
            "ASM Service (NA) — TECNICO 7.5",
        ],
    },
    "puglia": {
        "name": "Puglia",
        "provinces": ["Bari", "Lecce", "Taranto", "Brindisi", "Foggia", "BAT"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/puglia/",
        "characteristics": {
            "density": "alta (Bari metro), media (Lecce/Taranto)",
            "premium_appetite": "medio",
            "digital_maturity": "media-bassa",
            "competition": "bassa",
            "best_timing": "mart/merc 8:30-9:00",
            "tone": "formale, rispettoso, piu' lento nella decisione",
        },
        "nearby_cities_for_fomo": ["Bari", "Lecce", "Taranto"],
        "known_dealers": [
            "Stile Car (FG) — PERFORMANTE 8.0 — TIER_0_IMPORT",
            "AutoQuarta (LE) — RAGIONIERE 7.8",
            "Loforese 100 (TA) — PERFORMANTE 7.5",
            "SportLine (BAT) — BARONE 7.0",
        ],
    },
    "calabria": {
        "name": "Calabria",
        "provinces": ["Cosenza", "Catanzaro", "Reggio Calabria", "Crotone", "Vibo Valentia"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/calabria/",
        "characteristics": {
            "density": "bassa",
            "premium_appetite": "medio (Cosenza), basso (resto)",
            "digital_maturity": "bassa",
            "competition": "bassissima — territorio VUOTO",
            "best_timing": "mart/merc 9:00-9:30",
            "tone": "molto relazionale, fiducia prima di tutto",
        },
        "nearby_cities_for_fomo": ["Cosenza", "Catanzaro", "Reggio Calabria"],
        "known_dealers": [
            "Top Cars (CS) — BARONE 8.5",
            "Sa.My. Auto (CS) — PERFORMANTE 8.0 — titolare vissuto in DE",
        ],
    },
    "sicilia": {
        "name": "Sicilia",
        "provinces": ["Palermo", "Catania", "Messina", "Siracusa", "Ragusa",
                      "Trapani", "Agrigento", "Caltanissetta", "Enna"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/sicilia/",
        "characteristics": {
            "density": "alta (Palermo/Catania), bassa (resto)",
            "premium_appetite": "medio-alto (Catania/Palermo)",
            "digital_maturity": "media",
            "competition": "bassa",
            "best_timing": "mart/merc 9:00-9:30",
            "tone": "molto formale al primo contatto, poi si apre",
        },
        "nearby_cities_for_fomo": ["Catania", "Palermo"],
        "known_dealers": [],  # DA SCOUTARE
    },
    "sardegna": {
        "name": "Sardegna",
        "provinces": ["Cagliari", "Sassari", "Nuoro", "Oristano", "Sud Sardegna"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/sardegna/",
        "characteristics": {
            "density": "bassa",
            "premium_appetite": "medio (Cagliari/Costa Smeralda)",
            "digital_maturity": "bassa",
            "competition": "bassissima",
            "best_timing": "mart/merc 9:00-10:00",
            "tone": "riservato, lento, serve visita fisica",
        },
        "nearby_cities_for_fomo": ["Cagliari", "Sassari"],
        "known_dealers": [],  # DA SCOUTARE
    },
    "basilicata": {
        "name": "Basilicata",
        "provinces": ["Potenza", "Matera"],
        "autoscout_url": "https://www.autoscout24.it/concessionari/regioni/basilicata/",
        "characteristics": {
            "density": "bassissima",
            "premium_appetite": "basso",
            "digital_maturity": "bassa",
            "competition": "zero",
            "best_timing": "mart 9:00",
            "tone": "molto relazionale, serve referral",
        },
        "nearby_cities_for_fomo": ["Potenza", "Matera"],
        "known_dealers": [],
    },
}

# Macro-regioni per scouting batch
MACRO_REGIONS = {
    "sud-italia": ["campania", "puglia", "calabria", "sicilia", "sardegna", "basilicata"],
    "sud-continentale": ["campania", "puglia", "calabria", "basilicata"],
    "isole": ["sicilia", "sardegna"],
    "tier1-regions": ["campania", "puglia"],  # massima densita' dealer
    "tier2-regions": ["calabria", "sicilia"],  # media densita'
    "tier3-regions": ["sardegna", "basilicata"],  # bassa densita'
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 3: VEHICLE MATCHING PER TARGET
# ══════════════════════════════════════════════════════════════

VEHICLE_MATRIX = {
    "GROWTH": {
        "models": [
            {"search": "BMW X3", "years": "2020-2023", "price_range": (25000, 38000)},
            {"search": "BMW X5", "years": "2020-2022", "price_range": (32000, 48000)},
            {"search": "Mercedes GLC", "years": "2020-2023", "price_range": (26000, 40000)},
            {"search": "Mercedes GLE", "years": "2020-2022", "price_range": (35000, 52000)},
            {"search": "Audi Q5", "years": "2020-2023", "price_range": (25000, 38000)},
        ],
        "portals_priority": ["mobile_de", "autoscout24_de", "marktplaats_nl",
                             "willhaben_at", "autoscout24_be"],
    },
    "IMPORTER": {
        "models": [
            {"search": "BMW X5", "years": "2021-2023", "price_range": (35000, 55000)},
            {"search": "Mercedes GLE Coupe", "years": "2020-2023", "price_range": (40000, 60000)},
            {"search": "Audi Q7", "years": "2020-2023", "price_range": (35000, 55000)},
            {"search": "Volvo XC90", "years": "2020-2023", "price_range": (30000, 48000)},
        ],
        "portals_priority": ["marktplaats_nl", "willhaben_at", "finn_no",
                             "blocket_se", "sauto_cz"],  # portali NICCHIA
    },
    "LUXURY": {
        "models": [
            {"search": "Porsche Macan", "years": "2020-2023", "price_range": (40000, 75000)},
            {"search": "Porsche Cayenne", "years": "2020-2023", "price_range": (50000, 90000)},
            {"search": "BMW X6 M", "years": "2020-2023", "price_range": (55000, 85000)},
            {"search": "Range Rover Sport", "years": "2020-2023", "price_range": (45000, 80000)},
            {"search": "Mercedes AMG GT", "years": "2019-2023", "price_range": (60000, 120000)},
        ],
        "portals_priority": ["mobile_de", "autoscout24_de", "autoscout24_nl",
                             "autotrader_uk", "leboncoin_fr"],
    },
    "MONO_BRAND": {
        "models": [],  # Determinato dinamicamente dal brand del dealer
        "portals_priority": ["mobile_de", "autoscout24_de", "willhaben_at"],
    },
    "VOLUME": {
        "models": [
            {"search": "BMW X3", "years": "2020-2023", "price_range": (24000, 36000)},
            {"search": "BMW X1", "years": "2021-2023", "price_range": (22000, 32000)},
            {"search": "Mercedes GLC", "years": "2020-2023", "price_range": (26000, 40000)},
            {"search": "Audi Q3", "years": "2021-2023", "price_range": (22000, 34000)},
            {"search": "Audi Q5", "years": "2020-2023", "price_range": (25000, 38000)},
        ],
        "portals_priority": ["mobile_de", "autoscout24_de", "marktplaats_nl",
                             "willhaben_at", "autoscout24_be", "otomoto_pl"],
    },
}


# ══════════════════════════════════════════════════════════════
# SEZIONE 4: SCOUTING PLAN GENERATOR
# ══════════════════════════════════════════════════════════════

def generate_scouting_plan(target_type: str, region: str) -> dict:
    """Genera piano di scouting per tipo target + regione."""

    target = TARGET_PROFILES.get(target_type)
    if not target:
        return {"error": f"Target '{target_type}' non trovato"}

    # Risolvi macro-regione
    if region in MACRO_REGIONS:
        regions = [REGIONS[r] for r in MACRO_REGIONS[region] if r in REGIONS]
    elif region in REGIONS:
        regions = [REGIONS[region]]
    else:
        return {"error": f"Regione '{region}' non trovata"}

    vehicles = VEHICLE_MATRIX.get(target_type, {})

    plan = {
        "target": target_type,
        "target_name": target["name"],
        "regions": [],
        "total_provinces": 0,
        "pitch_angle": target["pitch_angle"],
        "objection_to_expect": target["objection_primary"],
        "objection_handler": target["objection_handler"],
        "vehicles_to_search": vehicles.get("models", []),
        "portals_priority": vehicles.get("portals_priority", []),
        "generated_at": datetime.now().isoformat(),
    }

    for reg in regions:
        plan["regions"].append({
            "name": reg["name"],
            "provinces": reg["provinces"],
            "url": reg["autoscout_url"],
            "tone": reg["characteristics"]["tone"],
            "timing": reg["characteristics"]["best_timing"],
            "competition": reg["characteristics"]["competition"],
            "fomo_cities": reg["nearby_cities_for_fomo"],
            "existing_dealers": reg.get("known_dealers", []),
        })
        plan["total_provinces"] += len(reg["provinces"])

    # Scoring criteria per target
    plan["scoring_criteria"] = {
        "stock_range": target["ideal"]["stock"],
        "years_range": target["ideal"]["years"],
        "premium_pct_min": target["ideal"]["premium_pct"][0],
        "reviews_range": target["ideal"]["reviews"],
        "rating_range": target["ideal"]["rating"],
        "signals_to_look_for": target["signals"],
    }

    # Archetypes likely
    plan["archetypes_expected"] = target["archetypes_likely"]

    return plan


def print_scouting_plan(plan: dict):
    """Stampa piano di scouting formattato."""
    if "error" in plan:
        print(f"ERRORE: {plan['error']}")
        return

    print(f"\n{'='*70}")
    print(f"PIANO SCOUTING — {plan['target_name']}")
    print(f"{'='*70}")
    print(f"Target: {plan['target']} | Province: {plan['total_provinces']}")
    print(f"Generato: {plan['generated_at'][:16]}")

    print(f"\n--- PITCH ---")
    print(f"  {plan['pitch_angle']}")
    print(f"\n--- OBIEZIONE ATTESA ---")
    print(f"  {plan['objection_to_expect']}")
    print(f"  Handler: {plan['objection_handler']}")

    print(f"\n--- REGIONI ---")
    for reg in plan["regions"]:
        print(f"\n  {reg['name']} ({', '.join(reg['provinces'])})")
        print(f"    URL: {reg['url']}")
        print(f"    Tono: {reg['tone']}")
        print(f"    Timing: {reg['timing']}")
        print(f"    Competizione: {reg['competition']}")
        if reg["existing_dealers"]:
            print(f"    Dealer gia' noti:")
            for d in reg["existing_dealers"]:
                print(f"      - {d}")

    print(f"\n--- CRITERI SCORING ---")
    sc = plan["scoring_criteria"]
    print(f"  Stock: {sc['stock_range'][0]}-{sc['stock_range'][1]} auto")
    print(f"  Anni: {sc['years_range'][0]}-{sc['years_range'][1]}")
    print(f"  Premium min: {sc['premium_pct_min']}%")
    print(f"  Reviews: {sc['reviews_range'][0]}-{sc['reviews_range'][1]}")
    print(f"  Rating: {sc['rating_range'][0]}-{sc['rating_range'][1]}")
    print(f"  Segnali:")
    for s in sc["signals_to_look_for"]:
        print(f"    - {s}")

    print(f"\n--- VEICOLI DA CERCARE ---")
    for v in plan["vehicles_to_search"]:
        print(f"  {v['search']} {v['years']} — €{v['price_range'][0]:,}-{v['price_range'][1]:,}")
    print(f"  Portali prioritari: {', '.join(plan['portals_priority'])}")

    print(f"\n--- ARCHETIPI ATTESI ---")
    print(f"  {', '.join(plan['archetypes_expected'])}")
    print(f"{'='*70}\n")


# ══════════════════════════════════════════════════════════════
# SEZIONE 5: CLI
# ══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("ARGOS Dealer Target Profiles & Regional Scouting")
        print("=" * 50)
        print("\nComandi:")
        print("  list-targets              — Mostra tutti i tipi di target")
        print("  list-regions              — Mostra tutte le regioni")
        print("  scout --target X --region Y — Genera piano scouting")
        print("  plan --target ALL --region sud-italia — Piano completo")
        print("\nEsempi:")
        print("  python3 tools/dealer_target_profiles.py list-targets")
        print("  python3 tools/dealer_target_profiles.py scout --target IMPORTER --region puglia")
        print("  python3 tools/dealer_target_profiles.py scout --target GROWTH --region sud-continentale")
        return

    cmd = sys.argv[1]

    if cmd == "list-targets":
        print(f"\n{'='*70}")
        print("TIPI DI TARGET DEALER")
        print(f"{'='*70}")
        for key, t in sorted(TARGET_PROFILES.items(), key=lambda x: x[1]["priority"]):
            print(f"\n  [{t['priority']}] {key}")
            print(f"      {t['name']}")
            print(f"      {t['description'][:100]}...")
            print(f"      Stock: {t['ideal']['stock']} | Premium: {t['ideal']['premium_pct'][0]}%+")
            print(f"      Archetipi: {', '.join(t['archetypes_likely'])}")
        print(f"\n{'='*70}\n")

    elif cmd == "list-regions":
        print(f"\n{'='*70}")
        print("REGIONI DISPONIBILI")
        print(f"{'='*70}")
        for key, r in REGIONS.items():
            dealers_count = len(r.get("known_dealers", []))
            print(f"  {key:15s} | {r['name']:12s} | {len(r['provinces'])} province | "
                  f"comp: {r['characteristics']['competition']:12s} | "
                  f"{dealers_count} dealer noti")
        print(f"\n  Macro-regioni:")
        for key, regs in MACRO_REGIONS.items():
            print(f"    {key:20s} → {', '.join(regs)}")
        print(f"{'='*70}\n")

    elif cmd == "scout":
        target = region = None
        for i, arg in enumerate(sys.argv):
            if arg == "--target" and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]
            if arg == "--region" and i + 1 < len(sys.argv):
                region = sys.argv[i + 1]

        if not target or not region:
            print("Uso: scout --target <TYPE> --region <REGION>")
            return

        if target == "ALL":
            for t_key in sorted(TARGET_PROFILES, key=lambda x: TARGET_PROFILES[x]["priority"]):
                plan = generate_scouting_plan(t_key, region)
                print_scouting_plan(plan)
        else:
            plan = generate_scouting_plan(target, region)
            print_scouting_plan(plan)

    elif cmd == "plan":
        # Piano completo per tutte le combinazioni
        target = region = None
        for i, arg in enumerate(sys.argv):
            if arg == "--target" and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]
            if arg == "--region" and i + 1 < len(sys.argv):
                region = sys.argv[i + 1]

        if target == "ALL":
            for t_key in sorted(TARGET_PROFILES, key=lambda x: TARGET_PROFILES[x]["priority"]):
                plan = generate_scouting_plan(t_key, region or "sud-italia")
                print_scouting_plan(plan)
        else:
            plan = generate_scouting_plan(target or "GROWTH", region or "sud-italia")
            print_scouting_plan(plan)

    else:
        print(f"Comando '{cmd}' non riconosciuto. Usa senza argomenti per l'help.")


if __name__ == "__main__":
    main()
