#!/usr/bin/env python3
"""ARGOS template engine — S292 credibility-first, evidence-safe.

Template-first remains the production rule.  Missing factual slots do not get
filled with invented defaults: a template that needs a vehicle/economic fact
returns an empty string until the caller supplies that fact.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping, Sequence

ND = "n/d"

TEMPLATES: Dict[str, str] = {
    "DAY1_PREMIUM": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho trovato la sua attività tramite {source}. "
        "Luca lavora sulla ricerca e verifica di auto premium europee per operatori italiani, soprattutto quando c'è una richiesta specifica da coprire.\n"
        "Le capita di ricevere richieste per {brand_focus} o SUV premium che non riesce a coprire subito?\n"
        "Se non è un tema utile, mi scriva pure 'no' e chiudo qui."
    ),
    "DAY1_MIXED": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho trovato la sua attività tramite {source}. "
        "Seguiamo ricerche e verifiche documentali di auto premium europee quando un operatore ha già una richiesta cliente da soddisfare.\n"
        "Le capita di cercare {brand_focus} su ordine, senza voler aumentare lo stock?\n"
        "Se non le serve, mi scriva 'no' e non la ricontatto su questo tema."
    ),
    "DAY1_GENERALIST": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti.\n"
        "Ho trovato la sua attività tramite {source}. "
        "Luca supporta operatori italiani quando devono cercare e verificare un'auto premium europea su richiesta di un cliente.\n"
        "Le capita di ricevere richieste specifiche che preferisce gestire su ordine invece di tenere l'auto in stock?\n"
        "Se non è pertinente, mi scriva 'no' e chiudo qui."
    ),
    "DAY1_CREDIBILITY": (
        "Buongiorno, sono Azzurra, assistente di Luca Ferretti. Ho trovato la sua attività tramite {source}.\n\n"
        "Luca segue ricerca e verifica documentale di auto premium europee per operatori italiani quando c'è già una richiesta da coprire.\n\n"
        "Se le capita di avere un cliente che cerca un'auto specifica e vuole verificare anche il mercato europeo, posso raccogliere i criteri e far partire la ricerca. "
        "Se preferisce non essere contattato, basta scrivermi 'no'."
    ),
    "IDENTITY_RESPONSE": (
        "Sono Azzurra, assistente di Luca Ferretti. Ho trovato il contatto della sua attività tramite {source}.\n"
        "Luca supporta operatori italiani nella ricerca e verifica di auto europee su richiesta.\n"
        "Non le sto proponendo un'auto a caso: volevo capire se questo tipo di supporto può servirle quando ha una richiesta specifica."
    ),
    "VEHICLE_REQUEST_ACK": (
        "Ricevuto. Ho registrato questa richiesta: {request_summary}.\n"
        "{missing_question}\n"
        "Appena i criteri sono completi posso passare la ricerca a Luca. Non le sto promettendo una disponibilità finché non abbiamo verificato un candidato concreto."
    ),
    "VEHICLE_PROPOSAL": (
        "{dealer_name}, ho un candidato coerente con la richiesta che ci ha affidato.\n\n"
        "{vehicle_summary}\n\n"
        "Verifiche disponibili: {evidence_summary}.\n"
        "Economica: {economics_summary}.\n\n"
        "Se vuole, preparo la scheda completa con soli dati documentati."
    ),
    "VEHICLE_DETAILS": (
        "{dealer_name}, ecco i dettagli verificati del candidato richiesto:\n"
        "{vehicle_summary}\n"
        "{evidence_summary}\n"
        "{economics_summary}\n"
        "I campi non verificati restano indicati come n/d."
    ),
    "OBJ_1_NO_INTEREST": (
        "Capisco, {dealer_name}. Chiudo qui.\n"
        "Se in futuro avrà una richiesta specifica da cercare sul mercato europeo, potrà riscrivermi quando vuole. Buon lavoro."
    ),
    "OBJ_2_FEE": (
        "La fee prevista per questa operazione è EUR {fee_eur}. "
        "Le condizioni complete sono quelle riportate nel contratto prima di qualsiasi impegno."
    ),
    "OBJ_3_TRUST": (
        "È una domanda corretta. Posso farle vedere come lavoriamo su fonti, verifiche e dossier senza chiederle di fidarsi di una promessa.\n"
        "Se ha già un'auto o una richiesta concreta, partiamo dai dati verificabili."
    ),
    "OBJ_4_TIMING": (
        "Nessun problema, {dealer_name}. Non la sollecito adesso.\n"
        "Se vuole essere ricontattato, mi indichi pure lei quando; altrimenti resto ferma."
    ),
    "OBJ_5_SOURCING": (
        "La provenienza e i dati dipendono dal singolo candidato. "
        "Prima di presentarlo verifichiamo ciò che è documentabile; quello che manca resta n/d e viene richiesto al venditore."
    ),
    "DAY7_RECOVERY": (
        "{dealer_name}, le avevo scritto riguardo al supporto per ricerche auto su richiesta. "
        "Se non è un tema utile, nessun problema: mi basta un 'no' e chiudo il contatto."
    ),
    "DAY12_FINAL": (
        "{dealer_name}, chiudo qui il contatto su questo tema. "
        "Se in futuro avrà una richiesta specifica da verificare sul mercato europeo, potrà riscrivermi. Buon lavoro."
    ),
    "CLOSING_PUSH": (
        "Se il candidato e il dossier sono coerenti con la sua richiesta, il prossimo passo è quello indicato nelle condizioni dell'operazione. "
        "Se qualcosa non torna, lo fermiamo prima."
    ),
    "DAY_INTEREST": (
        "{dealer_name}, le invio il link del contratto relativo alla richiesta/candidato già verificato:\n"
        "{sign_url}\n"
        "Fee: EUR {fee_eur}. Prima della firma può leggere tutte le condizioni."
    ),
    "IBAN_SEND": (
        "Dopo la condizione prevista dal contratto, questi sono i dati di pagamento:\n"
        "IBAN: {iban}\nIntestatario: {intestatario}\nImporto: EUR {fee_eur}\nCausale: ARGOS-{contract_id}"
    ),
    "PAYMENT_RECEIVED": (
        "Pagamento registrato, {dealer_name}. Grazie. L'operazione viene aggiornata come conclusa."
    ),
}

DEPRECATED_TEMPLATES = {"DAY1_VEHICLE_FIRST"}

# Only non-factual presentation defaults live here. Factual vehicle/economic
# fields deliberately have no default.
SLOT_DEFAULTS: Dict[str, str] = {
    "source": "il sito/contatto pubblico della sua attività",
    "brand_focus": "auto premium",
    "dealer_name": "",
    "missing_question": "Se manca un criterio (budget, anno, km o allestimento) glielo chiedo prima di cercare.",
}

_REQUIRED_SLOTS: Dict[str, set[str]] = {
    "VEHICLE_REQUEST_ACK": {"request_summary"},
    "VEHICLE_PROPOSAL": {"vehicle_summary", "evidence_summary", "economics_summary"},
    "VEHICLE_DETAILS": {"vehicle_summary", "evidence_summary", "economics_summary"},
    "OBJ_2_FEE": {"fee_eur"},
    "DAY_INTEREST": {"sign_url", "fee_eur"},
    "IBAN_SEND": {"iban", "intestatario", "fee_eur", "contract_id"},
}


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in {ND, "DA_VERIFICARE", "NO-VERDICT"}
    return True


def fill_template(template_id: str, data: Mapping[str, Any]) -> str:
    """Fill a fixed template; fail closed when a factual slot is missing."""
    if template_id in DEPRECATED_TEMPLATES:
        return ""
    template = TEMPLATES.get(template_id)
    if not template:
        return ""
    required = _REQUIRED_SLOTS.get(template_id, set())
    if any(not _known(data.get(slot)) for slot in required):
        return ""

    merged: Dict[str, Any] = dict(SLOT_DEFAULTS)
    merged.update({key: value for key, value in data.items() if _known(value)})
    placeholders = set(re.findall(r"\{(\w+)\}", template))
    if any(key not in merged for key in placeholders):
        return ""
    return template.format(**merged).strip()


TEMPLATE_MAP = {
    ("OUTBOUND_DAY1", "COLD"): "DAY1_INTRO",
    ("OUTBOUND_DAY7", "CONTACTED"): "DAY7_RECOVERY",
    ("OUTBOUND_DAY12", "CONTACTED"): "DAY12_FINAL",
    ("CURIOSITY", "CONTACTED"): "IDENTITY_RESPONSE",
    ("CURIOSITY", "ENGAGED"): "IDENTITY_RESPONSE",
    ("CURIOSITY", "DEMAND_DISCOVERY"): "IDENTITY_RESPONSE",
    ("VEHICLE_REQUEST", "DEMAND_DISCOVERY"): "VEHICLE_REQUEST_ACK",
    ("POSITIVE", "DEMAND_DISCOVERY"): "VEHICLE_REQUEST_ACK",
    ("VEHICLE_REQUEST", "MANDATE_CONFIRMED"): "VEHICLE_REQUEST_ACK",
    ("POSITIVE", "MANDATE_CONFIRMED"): "VEHICLE_PROPOSAL",
    ("NEGATIVE", "ENGAGED"): "OBJ_1_NO_INTEREST",
    ("NEGATIVE", "DEMAND_DISCOVERY"): "OBJ_1_NO_INTEREST",
    ("NEGATIVE", "CONTACTED"): "OBJ_1_NO_INTEREST",
    ("OBJ-1", "ENGAGED"): "OBJ_1_NO_INTEREST",
    ("OBJ-1", "DEMAND_DISCOVERY"): "OBJ_1_NO_INTEREST",
    ("OBJ-2", "ENGAGED"): "OBJ_2_FEE",
    ("OBJ-2", "DEMAND_DISCOVERY"): "OBJ_2_FEE",
    ("OBJ-2", "MANDATE_CONFIRMED"): "OBJ_2_FEE",
    ("OBJ-3", "ENGAGED"): "OBJ_4_TIMING",
    ("OBJ-3", "DEMAND_DISCOVERY"): "OBJ_4_TIMING",
    ("OBJ-4", "ENGAGED"): "OBJ_3_TRUST",
    ("OBJ-4", "DEMAND_DISCOVERY"): "OBJ_3_TRUST",
    ("OBJ-5", "ENGAGED"): "OBJ_5_SOURCING",
    ("OBJ-5", "DEMAND_DISCOVERY"): "OBJ_5_SOURCING",
}


def select_template(intent: str, state: str) -> str:
    return TEMPLATE_MAP.get((str(intent or "").upper(), str(state or "").upper()), "")


PREMIUM_BRANDS_CORE = {"bmw", "mercedes", "mercedes-benz", "audi", "porsche"}
PREMIUM_BRANDS_HIGH = {"volvo", "land rover", "range rover", "lexus", "jaguar"}
PREMIUM_BRANDS_MEDIO: set[str] = set()
PREMIUM_BRANDS = PREMIUM_BRANDS_CORE | PREMIUM_BRANDS_HIGH | PREMIUM_BRANDS_MEDIO
BRANDS_EVITARE = {
    "ferrari", "lamborghini", "mclaren", "bentley", "aston martin",
    "maserati", "tesla", "polestar", "genesis",
}


def select_day1_variant(dealer_brands: Sequence[str]) -> str:
    """Choose copy only from observed brand profile; never infer live demand."""
    if not dealer_brands:
        return "DAY1_GENERALIST"
    normalized = [str(value).strip().lower() for value in dealer_brands if str(value).strip()]
    if not normalized:
        return "DAY1_GENERALIST"
    premium_count = sum(1 for brand in normalized if brand in PREMIUM_BRANDS)
    if premium_count / len(normalized) >= 0.5:
        return "DAY1_PREMIUM"
    if premium_count:
        return "DAY1_MIXED"
    return "DAY1_GENERALIST"


def generate_cold_day1(
    dealer_brands: Sequence[str],
    source: str,
    dealer_name: str = "",
    vehicle: Mapping[str, Any] | None = None,
    profile: Mapping[str, Any] | None = None,
) -> str:
    """Generate credibility-first Day1. Vehicle/profile cannot create an offer.

    ``vehicle`` is accepted only for backward API compatibility and is ignored:
    S292 retired vehicle-first outreach. ``profile`` may influence neither
    mandate nor claims in this function.
    """
    template_id = select_day1_variant(dealer_brands)
    premium_hits = [
        str(brand).strip()
        for brand in dealer_brands
        if str(brand).strip().lower() in PREMIUM_BRANDS
    ]
    data = {
        "source": source or SLOT_DEFAULTS["source"],
        "brand_focus": " e ".join(premium_hits[:2]) if premium_hits else "auto premium",
        "dealer_name": dealer_name,
    }
    return fill_template(template_id, data)


# Backward-compatible alias, intentionally credibility-only.
TEMPLATES["DAY1_INTRO"] = TEMPLATES["DAY1_PREMIUM"]


if __name__ == "__main__":
    print(generate_cold_day1(["BMW", "Audi"], "sito pubblico"))
