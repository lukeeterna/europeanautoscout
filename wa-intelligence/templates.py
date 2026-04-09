#!/usr/bin/env python3
"""
templates.py — ARGOS™ Template Engine
Blueprint approvato S105 | Template-first, LLM-second

10 template fissi. Fill con str.format(). Zero LLM per fill standard.
Fee appare SOLO in OBJ_2_FEE. Mai altrove.
"""

# ── I 10 Template ──────────────────────────────────────────
TEMPLATES = {

    # DAY1 — 3 varianti per segmento dealer
    "DAY1_PREMIUM": (
        "Buongiorno, sono Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — lavora con {brand_focus}, giusto?\n"
        "Seleziono auto premium in tutta Europa per concessionari italiani: "
        "tagliandi certificati digitalmente, km tracciati dalla revisione TUV, "
        "garanzia costruttore europea valida in Italia.\n"
        "Auto con allestimenti che qui non arrivano — e margine netto di 3-5.000 euro per lei.\n"
        "Ha 2 minuti per capire come funziona?"
    ),

    "DAY1_MIXED": (
        "Buongiorno, sono Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — tra le altre, tratta anche {brand_focus}.\n"
        "Le capita che un cliente le chieda una {brand_focus} specifica e non la trova in Italia?\n"
        "In Europa ci sono migliaia di auto premium con storico tagliandi completo, "
        "km certificati e garanzia costruttore — a 3-5.000 euro in meno.\n"
        "Il margine per lei e' netto, l'auto arriva pronta per la vetrina.\n"
        "Ha 2 minuti per capire come funziona?"
    ),

    "DAY1_GENERALIST": (
        "Buongiorno, sono Luca Ferretti.\n"
        "Ho visto il suo salone su {source}.\n"
        "Le faccio una domanda diretta: le capita che un cliente le chieda "
        "una BMW, una Mercedes, una Porsche e lei non ce l'ha?\n"
        "Molti concessionari stanno aggiungendo auto premium dall'Europa al loro stock: "
        "margine 3x superiore, storico tagliandi verificabile, km certificati dalla revisione TUV tedesca, "
        "garanzia costruttore valida in Italia.\n"
        "Ha 2 minuti per capire come funziona?"
    ),

    # Alias per backward compatibility
    "DAY1_INTRO": (
        "Buongiorno, sono Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — lavora con {brand_focus}, giusto?\n"
        "Seleziono auto premium in tutta Europa per concessionari italiani: "
        "tagliandi certificati digitalmente, km tracciati dalla revisione TUV, "
        "garanzia costruttore europea valida in Italia.\n"
        "Auto con allestimenti che qui non arrivano — e margine netto di 3-5.000 euro per lei.\n"
        "Ha 2 minuti per capire come funziona?"
    ),

    "IDENTITY_RESPONSE": (
        "Ho trovato il suo contatto su {source}.\n"
        "Mi chiamo Luca Ferretti — seleziono auto premium in tutta Europa per concessionari italiani.\n"
        "Km certificati TUV, storico tagliandi completo, garanzia costruttore valida in Italia.\n"
        "Auto che arrivano da strade perfette, con margini netti di 3-5.000 euro per lei.\n"
        "{dealer_name}, le capita di avere clienti che cercano {brand_focus} con allestimenti che qui non girano?"
    ),

    "VEHICLE_PROPOSAL": (
        "{dealer_name}, un'opportunita' concreta.\n\n"
        "{vehicle_brand} {vehicle_model} {vehicle_year}\n"
        "{km} km certificati TUV — tagliandi timbrati, garanzia costruttore europea\n"
        "EUR {price_eur} consegnata a {city}\n\n"
        "In Italia la stessa auto parte da EUR {price_delta} in piu'.\n"
        "Margine netto per lei, auto pronta per la vetrina. Vuole la scheda completa?"
    ),

    "OBJ_1_NO_INTEREST": (
        "Capisco, {dealer_name}. Non serve rispondermi adesso.\n"
        "Se in futuro arriva un cliente che cerca {brand_focus} "
        "e non trova quello che vuole in Italia, mi faccia uno squillo.\n"
        "Buon lavoro."
    ),

    "OBJ_2_FEE": (
        "La mia fee e' EUR 1.000 a veicolo consegnato, pagata solo a consegna avvenuta.\n"
        "Zero anticipo, zero rischio per lei.\n"
        "Se il veicolo non va bene, non paga nulla."
    ),

    "OBJ_3_TRUST": (
        "E' normale che voglia sapere con chi ha a che fare.\n"
        "Ho lavorato con concessionari in {reference_area} — posso chiedere una referenza se vuole.\n"
        "Nel frattempo posso mandarle la documentazione del veicolo: foto HD, storico tagliandi, report km."
    ),

    "OBJ_4_TIMING": (
        "Nessun problema, {dealer_name}.\n"
        "Se preferisce, la ricontatto tra {followup_days} giorni.\n"
        "Le lascio il mio numero, mi scriva quando ha un momento."
    ),

    "OBJ_5_SOURCING": (
        "Il veicolo viene dalla Germania, con {km} km verificati tramite revisione TUV tedesca.\n"
        "Posso mandarle il rapporto completo con storico revisioni e tagliandi."
    ),

    "DAY7_RECOVERY": (
        "{dealer_name}, la disturbo un momento.\n"
        "Le avevo scritto la settimana scorsa riguardo auto {brand_focus} dalla Germania.\n"
        "Ha avuto modo di leggere?"
    ),

    "DAY12_FINAL": (
        "{dealer_name}, ultima volta che le scrivo su questo argomento.\n"
        "Se non fa al caso suo, nessun problema — magari una prossima volta.\n"
        "Buon lavoro."
    ),
}

# ── Defaults per slot mancanti ─────────────────────────────
SLOT_DEFAULTS = {
    "source": "un portale di concessionari",
    "brand_focus": "auto premium",
    "dealer_name": "",
    "city": "la sua zona",
    "reference_area": "Nord Italia",
    "followup_days": "10",
    "km": "certificati",
    "price_eur": "",
    "price_delta": "",
    "vehicle_brand": "",
    "vehicle_model": "",
    "vehicle_year": "",
}


def fill_template(template_id: str, data: dict) -> str:
    """Riempe un template con i dati forniti. Usa defaults per slot mancanti."""
    template = TEMPLATES.get(template_id)
    if not template:
        return ""

    # Merge defaults con dati forniti
    merged = {**SLOT_DEFAULTS, **{k: v for k, v in data.items() if v}}

    try:
        return template.format(**merged)
    except KeyError as e:
        # Slot mancante non nei defaults — rimuovi il placeholder
        import re
        result = template
        for match in re.finditer(r'\{(\w+)\}', template):
            key = match.group(1)
            if key not in merged:
                result = result.replace(match.group(0), '')
        return result.format(**merged)


# ── Template selector: (intent, state) → template_id ──────
TEMPLATE_MAP = {
    # (intent, state) → template_id
    ("OUTBOUND_DAY1", "COLD"):          "DAY1_INTRO",
    ("OUTBOUND_DAY7", "CONTACTED"):     "DAY7_RECOVERY",
    ("OUTBOUND_DAY12", "CONTACTED"):    "DAY12_FINAL",
    ("CURIOSITY", "CONTACTED"):         "IDENTITY_RESPONSE",
    ("CURIOSITY", "ENGAGED"):           "IDENTITY_RESPONSE",
    ("POSITIVE", "ENGAGED"):            "VEHICLE_PROPOSAL",
    ("POSITIVE", "CONTACTED"):          "VEHICLE_PROPOSAL",
    ("VEHICLE_REQUEST", "ENGAGED"):     "VEHICLE_PROPOSAL",
    ("VEHICLE_REQUEST", "CONTACTED"):   "VEHICLE_PROPOSAL",
    ("VEHICLE_REQUEST", "INTERESTED"):  "VEHICLE_PROPOSAL",
    ("NEGATIVE", "ENGAGED"):            "OBJ_1_NO_INTEREST",
    ("NEGATIVE", "CONTACTED"):          "OBJ_1_NO_INTEREST",
    ("OBJ-1", "ENGAGED"):              "OBJ_1_NO_INTEREST",
    ("OBJ-2", "ENGAGED"):              "OBJ_2_FEE",
    ("OBJ-2", "INTERESTED"):           "OBJ_2_FEE",
    ("OBJ-3", "ENGAGED"):              "OBJ_4_TIMING",
    ("OBJ-4", "ENGAGED"):              "OBJ_3_TRUST",
    ("OBJ-5", "ENGAGED"):              "OBJ_5_SOURCING",
}


def select_template(intent: str, state: str) -> str:
    """Seleziona il template giusto per intent + stato. Ritorna template_id o ''."""
    return TEMPLATE_MAP.get((intent, state), "")


# ── Premium brands per classificazione dealer ──────────────
# Brand classification per template selection
# CORE + HIGH = premium sicuro. MEDIO = premium su richiesta.
PREMIUM_BRANDS_CORE = {
    'bmw', 'mercedes', 'audi', 'porsche',
}
PREMIUM_BRANDS_HIGH = {
    'volvo', 'land rover', 'range rover',
}
PREMIUM_BRANDS_MEDIO = {
    'lexus', 'jaguar', 'lamborghini', 'bentley',
}
# Unione per classificazione dealer
PREMIUM_BRANDS = PREMIUM_BRANDS_CORE | PREMIUM_BRANDS_HIGH | PREMIUM_BRANDS_MEDIO

# Brand da evitare — MAI proporre
BRANDS_EVITARE = {
    'ferrari', 'maserati', 'mclaren', 'alfa romeo',
    'cupra', 'ds', 'peugeot', 'tesla', 'polestar', 'genesis',
    'aston martin',
}


def select_day1_variant(dealer_brands: list) -> str:
    """Seleziona la variante DAY1 giusta in base ai brand del dealer.

    - 50%+ premium → DAY1_PREMIUM
    - Almeno 1 premium → DAY1_MIXED
    - Zero premium → DAY1_GENERALIST
    """
    if not dealer_brands:
        return "DAY1_GENERALIST"

    brands_lower = [b.lower().strip() for b in dealer_brands]
    premium_count = sum(1 for b in brands_lower if any(p in b for p in PREMIUM_BRANDS))
    total = len(brands_lower)

    if total == 0:
        return "DAY1_GENERALIST"
    elif premium_count / total >= 0.5:
        return "DAY1_PREMIUM"
    elif premium_count > 0:
        return "DAY1_MIXED"
    else:
        return "DAY1_GENERALIST"


if __name__ == '__main__':
    # Test
    msg = fill_template("DAY1_INTRO", {
        "source": "AutoScout24",
        "brand_focus": "BMW e Mercedes",
    })
    print(msg)
    print("---")
    msg2 = fill_template("VEHICLE_PROPOSAL", {
        "dealer_name": "Mario",
        "vehicle_brand": "BMW",
        "vehicle_model": "X3 xDrive20d",
        "vehicle_year": "2022",
        "km": "50.000",
        "price_eur": "34.100",
        "price_delta": "4.900",
        "city": "Foggia",
    })
    print(msg2)
