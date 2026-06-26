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
    # Firma: Azzurra, assistente di Luca Ferretti (S274-S277, NON negoziabile).
    # Margine: condizionale/banda, MAI promessa secca.
    # Opt-out: presente in ogni variante.
    "DAY1_PREMIUM": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — lavora con {brand_focus}, giusto?\n"
        "Per conto di Luca seleziono auto premium in tutta Europa: "
        "km tracciati dalla revisione TUV, tagliandi certificati, garanzia costruttore valida in Italia.\n"
        "Auto con allestimenti rari qui — su questo segmento il margine puo' essere interessante, "
        "ma dipende sempre dal veicolo.\n"
        "Se non e' interessato, mi scriva 'no' e non la disturbo piu'. "
        "Altrimenti: ha 2 minuti per capire come funziona?"
    ),

    "DAY1_MIXED": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — tra le altre, tratta anche {brand_focus}.\n"
        "Le capita che un cliente le chieda una {brand_focus} specifica e non la trova in Italia?\n"
        "In Europa ci sono auto premium con km certificati TUV e garanzia costruttore — "
        "il margine varia per veicolo, ma spesso vale la pena.\n"
        "Se non e' interessato basta scrivermi 'no'. "
        "Ha 2 minuti per capire come funziona?"
    ),

    "DAY1_GENERALIST": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho visto il suo salone su {source}.\n"
        "Le faccio una domanda diretta: le capita che un cliente le chieda "
        "una BMW, una Mercedes, una Porsche e lei non ce l'ha?\n"
        "Molti concessionari aggiungono auto premium dall'Europa: "
        "storico tagliandi verificabile, km certificati dalla revisione TUV tedesca, "
        "garanzia costruttore valida in Italia — margini che dipendono dal veicolo.\n"
        "Se non e' il momento giusto, mi scriva 'no' e non la disturbo piu'. "
        "Ha 2 minuti per capire come funziona?"
    ),

    # DAY1 VEICOLO-FIRST (S4) — apre col veicolo reale + numeri + domanda chiusa.
    # MAI presentazione iniziale, MAI "ho visto il tuo profilo/Instagram".
    # Il segnale-profilo entra come PERTINENZA implicita ({segmento} per la sua vetrina).
    # Firma Azzurra (assistente digitale dichiarata) + provenienza + opt-out in coda.
    "DAY1_VEHICLE_FIRST": (
        "{vehicle_brand} {vehicle_model} {vehicle_variant}, {vehicle_year}, {km} km — {country}, EUR {price_eur} consegnata.\n"
        "Km tracciati TUV, tagliandi certificati, garanzia costruttore valida in Italia.\n"
        "Un {segmento} in piu' per la sua vetrina: le interesserebbe?\n"
        "Sono Azzurra, assistente digitale di Luca Ferretti; ho preso il suo contatto da {source}. "
        "Se preferisce non ricevere messaggi mi scriva 'no'."
    ),

    # Alias per backward compatibility — identico a DAY1_PREMIUM
    "DAY1_INTRO": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho visto il suo salone su {source} — lavora con {brand_focus}, giusto?\n"
        "Per conto di Luca seleziono auto premium in tutta Europa: "
        "km tracciati dalla revisione TUV, tagliandi certificati, garanzia costruttore valida in Italia.\n"
        "Auto con allestimenti rari qui — su questo segmento il margine puo' essere interessante, "
        "ma dipende sempre dal veicolo.\n"
        "Se non e' interessato, mi scriva 'no' e non la disturbo piu'. "
        "Altrimenti: ha 2 minuti per capire come funziona?"
    ),

    "IDENTITY_RESPONSE": (
        "Ho trovato il suo contatto su {source}.\n"
        "Scrivo per conto di Luca Ferretti — seleziona auto premium in tutta Europa per concessionari italiani.\n"
        "Km certificati TUV, storico tagliandi completo, garanzia costruttore valida in Italia.\n"
        "{dealer_name}, le capita di avere clienti che cercano {brand_focus} con allestimenti che qui non girano?\n"
        "Se non e' interessato mi scriva 'no', non la contatto piu'."
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

    # ── S152 Contract+Payment templates ───────────────────────
    # Inviato dopo INTEREST conf>=0.85 + Telegram HOLD approval.
    # Crea contratto via argos-proxy/contract/create e include sign_url.
    "DAY_INTEREST": (
        "{dealer_name}, perfetto.\n"
        "Le mando il contratto per {vehicle_brand} {vehicle_model}: solo dato + firma stilizzata.\n"
        "{sign_url}\n"
        "Fee €{fee_eur}, paga solo dopo consegna documenti auto.\n"
        "Mi conferma quando ha firmato?"
    ),

    # Inviato post-firma quando documenti consegnati (status AWAITING_DELIVERY → IBAN_SENT).
    # Mirror del template TS in argos-proxy/src/routes/send-iban.ts (consistency).
    "IBAN_SEND": (
        "Pronto per il bonifico {dealer_name}.\n\n"
        "IBAN: {iban}\n"
        "Intestatario: {intestatario}\n"
        "Importo: €{fee_eur}\n"
        "Causale: ARGOS-{contract_id}\n\n"
        "Per il bonifico la banca verifica il nome del titolare del conto: {intestatario}. "
        "ARGOS è il brand, Luca Ferretti il referente.\n\n"
        "Mi invii ricevuta quando fatto. Grazie."
    ),

    # Inviato post-mark-paid (status IBAN_SENT → PAID).
    "PAYMENT_RECEIVED": (
        "Bonifico ricevuto {dealer_name}, grazie. Operazione conclusa.\n\n"
        "A presto per il prossimo veicolo."
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
    "vehicle_variant": "",
    "vehicle_year": "",
    "country": "Germania",
    "segmento": "SUV premium tedesco",
    # S152 contract+payment slots
    "sign_url": "",
    "fee_eur": "800",
    "iban": "",
    "intestatario": "",
    "contract_id": "",
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


def generate_cold_day1(dealer_brands: list, source: str, dealer_name: str = "",
                       vehicle: dict = None, profile: dict = None) -> str:
    """Genera il messaggio cold Day-1 in modo offline, ZERO LLM, ZERO invio.

    Args:
        dealer_brands: lista brand trattati dal dealer (es. ["BMW", "Mercedes"]).
        source: portale/canale da cui e' stato trovato il contatto (es. "AutoScout24").
        dealer_name: nome/ragione sociale del dealer (opzionale, non usato nei template DAY1).
        vehicle: dict veicolo-match reale {brand,model,variant,year,km,price_eur,country}
                 (opzionale). Se fornito → Day-1 VEICOLO-FIRST: apre col veicolo reale +
                 numeri + UNA domanda chiusa, firma Azzurra + provenienza + opt-out.
        profile: dict payload-profilo {business_name, segmento, anchor} (opzionale).
                 segmento entra come PERTINENZA implicita, MAI come anchor citato.

    Returns:
        Testo del messaggio Day-1 pronto per revisione umana.
    """
    # S4 — variante VEICOLO-FIRST (retro-compatibile: senza vehicle resta legacy)
    if vehicle:
        prof = profile or {}
        variant_short = " ".join(str(vehicle.get("variant", "")).split()[:1])
        data = {
            "vehicle_brand": vehicle.get("brand", ""),
            "vehicle_model": vehicle.get("model", ""),
            "vehicle_variant": variant_short,
            "vehicle_year": str(vehicle.get("year", "")),
            "km": f"{int(vehicle.get('km', 0)):,}".replace(",", "."),
            "country": vehicle.get("country", "Germania"),
            "price_eur": f"{int(vehicle.get('price_eur', 0)):,}".replace(",", "."),
            "segmento": prof.get("segmento", "SUV premium tedesco"),
            "source": source,
        }
        return fill_template("DAY1_VEHICLE_FIRST", data)

    template_id = select_day1_variant(dealer_brands)

    # brand_focus = stringa leggibile del/dei brand premium trovati
    brands_lower = [b.lower().strip() for b in dealer_brands]
    premium_hits = [b for b in dealer_brands if b.lower().strip() in PREMIUM_BRANDS]
    brand_focus = " e ".join(premium_hits[:2]) if premium_hits else "auto premium"

    data = {
        "source": source,
        "brand_focus": brand_focus,
        "dealer_name": dealer_name,
    }
    return fill_template(template_id, data)


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
