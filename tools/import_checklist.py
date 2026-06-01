"""
import_checklist.py -- ARGOS Import Checklist Generator
CoVe 2026 | Enterprise Grade

Genera checklist documenti personalizzata per paese di origine.
Import intra-EU = libera circolazione, ma servono documenti precisi.

Reference:
  - ACI Servizi: procedure immatricolazione veicoli esteri
  - Motorizzazione Civile: moduli TT2119, CDPD
  - Agenzia delle Entrate: reverse charge art. 17 DPR 633/72
  - Codice della Strada art. 132: circolazione veicoli esteri

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("argos.import_checklist")


@dataclass
class ChecklistItem:
    """Singolo step della checklist import."""
    step: int
    title: str
    description: str
    responsible: str    # "venditore" | "ARGOS" | "dealer" | "agenzia"
    cost_eur: int       # Costo stimato (0 se incluso)
    required: bool      # True = obbligatorio, False = consigliato
    country_specific: bool = False  # True = varia per paese
    notes: str = ""


@dataclass
class ImportChecklist:
    """Checklist completa per import veicolo EU→IT."""
    origin_country: str
    origin_country_name: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    items: List[ChecklistItem] = field(default_factory=list)
    total_cost_min: int = 0
    total_cost_max: int = 0
    estimated_days: int = 0
    warnings: List[str] = field(default_factory=list)


COUNTRY_NAMES = {
    "DE": "Germania", "NL": "Olanda", "BE": "Belgio", "AT": "Austria",
    "FR": "Francia", "SE": "Svezia", "DK": "Danimarca", "NO": "Norvegia",
    "FI": "Finlandia", "PL": "Polonia", "CZ": "Rep. Ceca", "RO": "Romania",
    "IT": "Italia", "ES": "Spagna", "PT": "Portogallo", "BG": "Bulgaria",
    "LT": "Lituania", "LV": "Lettonia", "EE": "Estonia", "HR": "Croazia",
    "SI": "Slovenia", "SK": "Slovacchia", "HU": "Ungheria",
}

# Documenti specifici per paese di origine
COUNTRY_EXPORT_DOCS: Dict[str, List[str]] = {
    "DE": ["Fahrzeugbrief (Zulassungsbescheinigung Teil II)", "Abmeldebescheinigung (cancellazione targa DE)", "TUV/HU Bericht (se disponibile)"],
    "NL": ["Kentekenbewijs (carta di circolazione NL)", "Vrijwaringsbewijs (certificato cancellazione)", "NAP rapport (storico km)"],
    "BE": ["Certificat d'immatriculation / Inschrijvingsbewijs", "Certificat de radiation (cancellazione)", "Car-Pass (storico km obbligatorio BE)"],
    "AT": ["Zulassungsschein / Typenschein", "Abmeldebescheinigung AT", "Pickerl (revisione AT, se valido)"],
    "FR": ["Carte grise (certificat d'immatriculation)", "Certificat de cession", "Controle technique (se > 4 anni)"],
    "SE": ["Registreringsbevis (Part I + II)", "Avregistreringsbevis (cancellazione)", "Besiktningsprotokoll (revisione SE)"],
    "DK": ["Registreringsattest", "Afmelding (cancellazione)", "Synsrapport (revisione DK)"],
    "PL": ["Dowod rejestracyjny (carta circolazione PL)", "Karta pojazdu", "Zaswiadczenie o wyrejestrowaniu (cancellazione)"],
    "CZ": ["Techicky prukaz (libretto)", "ORV (carta circolazione)", "Protokol STK (revisione CZ)"],
    "RO": ["Certificat de inmatriculare (carta circolazione RO)", "Certificat de radiere (cancellazione)", "ITP valabil (revisione RO)"],
    "BG": ["Свидетелство за регистрация / Registration certificate Part I+II", "Удостоверение за дерегистрация (cancellazione)", "ГТП протокол (revisione BG)"],
    "LT": ["Registracijos liudijimas (carta circolazione LT)", "Isregistravimo pazymejimas (cancellazione)", "Technines apziuros ataskaita (revisione LT)"],
    "LV": ["Transportlidzekla registracijas aplieciba (carta circolazione LV)", "Noregistresanas apliecinajums (cancellazione)"],
    "EE": ["Registreerimistunnistus (carta circolazione EE)", "Ajutine registreerimistunnistus (cancellazione)", "Tehnoulevaatuse protokoll (revisione EE)"],
    "HR": ["Prometna dozvola (carta circolazione HR)", "Potvrda o odjavi (cancellazione)", "Tehnicki pregled (revisione HR)"],
    "SI": ["Prometno dovoljenje (carta circolazione SI)", "Potrdilo o odjavi (cancellazione)", "Tehnicki pregled (revisione SI)"],
    "SK": ["Osvedcenie o evidencii vozidla (carta circolazione SK)", "Odhlasenie vozidla (cancellazione)", "STK protokol (revisione SK)"],
    "HU": ["Forgalmi engedely (carta circolazione HU)", "Igazolas a forgalombol kivonasrol (cancellazione)", "Muegyeri vizsgalat (revisione HU)"],
    "NO": ["Vognkort (carta circolazione NO)", "Avregistreringsbevis (cancellazione)", "EU-kontroll (revisione NO)"],
    "FI": ["Rekisterointiote (carta circolazione FI)", "Liikennekaytostapoisto (cancellazione)", "Katsastustodistus (revisione FI)"],
    "ES": ["Permiso de circulacion + Ficha tecnica", "Baja temporal/definitiva (cancellazione)", "ITV vigente (revisione ES)"],
    "PT": ["Documento Unico Automovel / Livrete", "Cancelamento de matricula (cancellazione)", "Inspecao periodica (revisione PT)"],
}


def generate_checklist(
    origin_country: str,
    vehicle_make: str = "",
    vehicle_model: str = "",
    vehicle_year: int = 0,
    is_b2b: bool = True,
    dealer_city: str = "Eboli",
) -> ImportChecklist:
    """
    Genera checklist import personalizzata.

    Args:
        origin_country: Codice paese origine (DE, NL, BE, ...)
        vehicle_make/model/year: Dati veicolo
        is_b2b: True se acquisto B2B (reverse charge), False se privato
        dealer_city: Citta' dealer destinazione

    Returns: ImportChecklist con tutti gli step
    """
    country = origin_country.upper()[:2]
    country_name = COUNTRY_NAMES.get(country, country)
    items = []
    warnings = []
    step = 1

    # ── FASE 1: PRE-ACQUISTO ──────────────────────────────────────────────

    items.append(ChecklistItem(
        step=step, title="Verifica annuncio e contatto venditore",
        description=f"Verificare disponibilita', condizioni reali, foto aggiuntive. Richiedere VIN completo.",
        responsible="ARGOS", cost_eur=0, required=True,
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="VIN check e storico veicolo",
        description="Verificare storico km, incidenti, furti tramite database paese origine.",
        responsible="ARGOS", cost_eur=0, required=True,
        notes="Vincario/carVertical se disponibile, altrimenti database nazionale",
    ))
    step += 1

    # COC — Certificate of Conformity
    items.append(ChecklistItem(
        step=step, title="Certificate of Conformity (COC)",
        description="Documento rilasciato dal costruttore che certifica conformita' alle norme EU. "
                    "Necessario per immatricolazione IT. Se non presente nel veicolo, richiedere al costruttore.",
        responsible="venditore", cost_eur=0, required=True,
        notes=f"BMW/Mercedes/Audi: richiedere via dealer ufficiale {country_name} (~EUR 100-200 se non incluso). "
              "Senza COC serve omologazione individuale (piu' costosa).",
    ))
    step += 1

    # ── FASE 2: ACQUISTO ──────────────────────────────────────────────────

    items.append(ChecklistItem(
        step=step, title="Contratto di vendita bilingue",
        description=f"Kaufvertrag / contratto di vendita in lingua {country_name.lower()} e italiano. "
                    "Deve includere: dati completi veicolo, prezzo, VIN, dati venditore e acquirente.",
        responsible="ARGOS", cost_eur=0, required=True,
        notes="MAI bonifico totale anticipato. Acconto 10-20% + saldo a consegna/verifica.",
    ))
    step += 1

    # Documenti export specifici per paese
    export_docs = COUNTRY_EXPORT_DOCS.get(country, [f"Carta di circolazione {country_name}", "Certificato cancellazione targa"])
    for doc in export_docs:
        items.append(ChecklistItem(
            step=step, title=f"Ottenere: {doc}",
            description=f"Documento necessario da {country_name} per export.",
            responsible="venditore", cost_eur=0, required=True,
            country_specific=True,
        ))
        step += 1

    # ── FASE 3: IVA E FISCALITA' ─────────────────────────────────────────

    if is_b2b:
        items.append(ChecklistItem(
            step=step, title="Reverse charge IVA (art. 17 DPR 633/72)",
            description="Acquisto intra-UE B2B: il venditore emette fattura SENZA IVA. "
                        "Il dealer IT effettua autofattura (reverse charge TD17). "
                        "IVA versata e detratta nello stesso periodo = costo zero.",
            responsible="dealer", cost_eur=0, required=True,
            notes="Comunicazione INTRASTAT obbligatoria per acquisti > EUR 200.000/anno.",
        ))
    else:
        items.append(ChecklistItem(
            step=step, title="IVA regime margine",
            description="Se venditore applica regime margine: IVA pagata solo sul margine del dealer IT, "
                        "non sull'intero prezzo. Risparmio significativo.",
            responsible="dealer", cost_eur=0, required=True,
        ))
    step += 1

    # ── FASE 4: TRASPORTO ─────────────────────────────────────────────────

    items.append(ChecklistItem(
        step=step, title="Targa export / transit",
        description=f"Targa temporanea per trasporto da {country_name} a Italia. "
                    "In alternativa: trasporto su bisarca (non serve targa export).",
        responsible="venditore", cost_eur=80, required=True,
        country_specific=True,
        notes="DE: Ausfuhrkennzeichen (~EUR 50-100, valida 2-12 mesi). "
              "NL: exportkenteken. AT: Überstellungskennzeichen.",
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="Assicurazione temporanea trasporto",
        description="Polizza RCA temporanea per circolazione su strada EU durante trasporto. "
                    "Non necessaria se trasporto su bisarca.",
        responsible="ARGOS", cost_eur=50, required=True,
        notes="Validita' consigliata: 15-30 giorni. Copertura internazionale EU.",
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="Trasporto veicolo",
        description=f"Trasporto da {country_name} a {dealer_city}. "
                    "Opzioni: bisarca professionale, drive-it-home, carrello.",
        responsible="ARGOS", cost_eur=700, required=True,
        notes="Preventivo specifico in base a rotta e metodo. Vedi stima trasporto nel dossier.",
    ))
    step += 1

    # ── FASE 5: IMMATRICOLAZIONE IT ──────────────────────────────────────

    items.append(ChecklistItem(
        step=step, title="Richiesta immatricolazione (Motorizzazione)",
        description="Presentare domanda di immatricolazione alla Motorizzazione Civile. "
                    "Documenti: COC, contratto vendita, carta circolazione estera, "
                    "documento cancellazione targa estera, modulo TT2119.",
        responsible="agenzia", cost_eur=200, required=True,
        notes="Tramite agenzia pratiche auto: ~EUR 150-250 onorario + bolli.",
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="IPT (Imposta Provinciale Trascrizione)",
        description="Imposta dovuta alla Provincia per la trascrizione al PRA.",
        responsible="agenzia", cost_eur=180, required=True,
        notes="Importo varia per provincia e potenza veicolo. Media: EUR 150-250.",
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="Targhe italiane + carta circolazione IT",
        description="Rilascio targhe italiane e carta di circolazione definitiva.",
        responsible="agenzia", cost_eur=50, required=True,
        notes="Tempistica: 5-15 giorni lavorativi dalla presentazione pratica.",
    ))
    step += 1

    # ── FASE 6: POST-IMMATRICOLAZIONE ────────────────────────────────────

    items.append(ChecklistItem(
        step=step, title="Assicurazione RCA definitiva",
        description="Stipula polizza RCA con compagnia italiana.",
        responsible="dealer", cost_eur=0, required=True,
        notes="Costo variabile. Non incluso nei costi import.",
    ))
    step += 1

    items.append(ChecklistItem(
        step=step, title="Revisione (se necessaria)",
        description="Se il veicolo ha piu' di 4 anni dall'immatricolazione originale, "
                    "potrebbe essere necessaria la revisione.",
        responsible="dealer", cost_eur=70, required=vehicle_year <= 2022,
        notes="Revisione obbligatoria entro 4 anni dalla prima immatricolazione, poi ogni 2 anni.",
    ))
    step += 1

    # ── WARNINGS ──────────────────────────────────────────────────────────

    if country in ("RO", "BG", "LV", "LT", "HU", "PL"):
        warnings.append(
            f"ATTENZIONE: {country_name} ha tasso di frode odometro > 6%. "
            "Verificare storico km con database nazionale PRIMA dell'acquisto."
        )

    if country in ("HR", "SI"):
        warnings.append(
            f"Veicoli da {country_name}: verificare che non siano stati utilizzati come taxi "
            "o noleggio — molto comune in questa area. Richiedere storico completo."
        )

    if country in ("DK", "NO"):
        warnings.append(
            f"I prezzi annuncio in {country_name} INCLUDONO tasse di registrazione elevate. "
            "Il prezzo reale export e' significativamente inferiore al prezzo annuncio."
        )

    if country == "SE" and vehicle_year < 2020:
        warnings.append(
            "Svezia: controllare se il veicolo ha 'miltal' (contachilometri) in MIL svedesi. "
            "1 mil = 10 km. Conversione necessaria."
        )

    if not is_b2b:
        warnings.append(
            "Acquisto privato: IVA regime margine applicabile solo se il venditore e' un dealer "
            "che ha acquistato il veicolo senza IVA detraibile."
        )

    # Calcola costi totali
    costs = [item.cost_eur for item in items if item.required]
    total_min = sum(costs)
    total_max = int(total_min * 1.3)  # +30% margine sicurezza

    # Stima giorni
    if country in ("DE", "AT", "NL", "BE"):
        days = 14
    elif country in ("FR", "CZ", "PL"):
        days = 18
    else:
        days = 21

    return ImportChecklist(
        origin_country=country,
        origin_country_name=country_name,
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        vehicle_year=vehicle_year,
        items=items,
        total_cost_min=total_min,
        total_cost_max=total_max,
        estimated_days=days,
        warnings=warnings,
    )


def format_checklist_text(cl: ImportChecklist) -> str:
    """Formatta checklist come testo leggibile."""
    lines = [
        f"{'='*70}",
        f"ARGOS AUTOMOTIVE — CHECKLIST IMPORT {cl.origin_country_name.upper()} → ITALIA",
        f"Veicolo: {cl.vehicle_make} {cl.vehicle_model} {cl.vehicle_year}",
        f"{'='*70}",
        "",
    ]

    for item in cl.items:
        req = "OBBLIGATORIO" if item.required else "Consigliato"
        cost = f"EUR {item.cost_eur}" if item.cost_eur > 0 else "Incluso"
        lines.append(f"  {item.step:2d}. [{item.responsible:10}] {item.title}")
        lines.append(f"      {item.description[:100]}")
        lines.append(f"      Costo: {cost} | {req}")
        if item.notes:
            lines.append(f"      Nota: {item.notes[:100]}")
        lines.append("")

    lines.append(f"{'─'*70}")
    lines.append(f"COSTI TOTALI STIMATI: EUR {cl.total_cost_min:,} - {cl.total_cost_max:,}")
    lines.append(f"TEMPISTICA STIMATA: {cl.estimated_days} giorni lavorativi")
    lines.append(f"{'─'*70}")

    if cl.warnings:
        lines.append("\nAVVERTENZE:")
        for w in cl.warnings:
            lines.append(f"  ! {w}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cl = generate_checklist("DE", "BMW", "X3", 2020, is_b2b=True, dealer_city="Eboli")
    print(format_checklist_text(cl))

    print("\n\n")

    cl2 = generate_checklist("RO", "BMW", "X5", 2019, is_b2b=True, dealer_city="Salerno")
    print(format_checklist_text(cl2))
