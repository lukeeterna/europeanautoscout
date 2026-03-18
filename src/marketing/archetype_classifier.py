#!/usr/bin/env python3.11
"""
ARGOS Automotive — Archetype Classifier + Response Retriever
=============================================================
Classifica l'archetipo del dealer dalla conversazione e recupera
la risposta ottimale dal dataset sintetico.

Usage:
    from src.marketing.archetype_classifier import classify, get_best_response
    result = classify("Quanto costa? E se facciamo più operazioni mi fate uno sconto?")
    response = get_best_response(result['primary'], result['context'])
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
_ARCHETYPES_FILE = _ROOT / "data" / "training" / "archetypes_v2.json"
_CONVERSATIONS_FILE = _ROOT / "data" / "training" / "conversations_synthetic_v1.json"

# ── Signal patterns per archetipo ──────────────────────────────────────────
_SIGNAL_PATTERNS = {
    "RAGIONIERE": [
        "iva", "td18", "td17", "regime margine", "regelbesteuerung",
        "margine netto", "consuntivo", "voci separate", "reverse charge",
        "intracomunitario", "quanto guadagno", "quanti euro", "fattura"
    ],
    "BARONE": [
        "chi ti ha dato", "chi sei", "chi te l'ha dato",
        "ho già i miei fornitori", "non ho bisogno", "intermediari",
        "lavoro sempre con gli stessi", "non cambio",
        "parla con mio", "ne parla mio"
    ],
    "PERFORMANTE": [
        "48 ore", "entro domani", "considera chiuso", "foglio completo",
        "documento vero", "non la stima", "al centesimo",
        "se non arriva", "cerco altrove"
    ],
    "NARCISO": [
        "showroom", "come appare", "cliente finale", "bella figura",
        "immagine", "arteria principale", "sembrar", "rivenditore di import"
    ],
    "TECNICO": [
        "carfax eu", "hpi check", "dat fahrzeughistorie", "autoscout dat",
        "gutachten", "dekra", "tüv", "hauptuntersuchung", "chi firma",
        "pre-partenza", "post-trasporto", "clearance orale"
    ],
    "RELAZIONALE": [
        "come ci siamo conosciuti", "chi ti ha mandato",
        "lavoro solo con persone che conosco", "fiducia", "non ti conosco",
        "referenza", "conosce qualcuno"
    ],
    "CONSERVATORE": [
        "ho sempre fatto così", "non è il momento", "stock elevato",
        "non vedo perché cambiare", "funziona così", "non cambio sistema"
    ],
    "DELEGATORE": [
        "ne parlo con mio", "lo dico al socio", "ne parla mio fratello",
        "devo sentire", "ne parlo col commercialista", "decide mio",
        "parla con mio nipote"
    ],
    "OPPORTUNISTA": [
        "quanto costa", "mi fate uno sconto", "più operazioni",
        "ho trovato qualcuno che fa", "€400", "meno caro",
        "abbassare la fee", "sconto"
    ],
    "VISIONARIO": [
        "quanti dealer nella mia zona", "voglio essere il primo",
        "esclusiva", "se lo fanno tutti non mi interessa",
        "primo nella mia zona", "concorrenti"
    ]
}

# ── Context detection ───────────────────────────────────────────────────────
_CONTEXT_PATTERNS = {
    "day1_response": ["mi dica", "di cosa si tratta", "chi sei", "interessante", "buongiorno"],
    "objection_fee": ["€800", "costa", "tanto", "sconto", "fee", "geometra", "commercialista"],
    "objection_suppliers": ["fornitori", "ho già chi", "intermediari", "non ho bisogno"],
    "objection_timing": ["non è il momento", "stock elevato", "ci penso", "non adesso"],
    "objection_guarantee": ["garanzie", "chi copre", "problema", "rischio", "responsabilità"],
    "objection_trust": ["non ti conosco", "fiducia", "referenze", "deal chiusi"],
    "objection_process": ["gutachten", "perizia", "pre-partenza", "chi firma", "indipendente"],
    "objection_decision": ["ne parlo", "socio", "fratello", "commercialista", "titolare"],
    "closing": ["mandi", "procediamo", "quando iniziamo", "vin", "dimmi il modello"],
    "error_handling": ["voce sbagliata", "errore", "non torna", "sbagliato"]
}


@dataclass
class ArchetypeResult:
    primary: str
    secondary: Optional[str]
    vector: dict
    confidence: float
    context: str
    signals_found: list[str] = field(default_factory=list)
    overlap_weight: float = 0.0
    blend_needed: bool = False


def classify(dealer_message: str, conversation_history: list[str] = None) -> ArchetypeResult:
    """
    Classifica l'archetipo del dealer da un messaggio.

    Args:
        dealer_message: Il messaggio del dealer da classificare
        conversation_history: Lista di messaggi precedenti del dealer (opzionale)

    Returns:
        ArchetypeResult con primary, secondary, vector, confidence
    """
    msg = dealer_message.lower()

    # Calcola score per ogni archetipo
    scores = {}
    found_signals = {}
    for archetype, patterns in _SIGNAL_PATTERNS.items():
        hits = [p for p in patterns if p in msg]
        scores[archetype] = len(hits)
        if hits:
            found_signals[archetype] = hits

    # Se ho storia conversazione, aggiungo peso ai segnali precedenti (0.5x)
    if conversation_history:
        for past_msg in conversation_history:
            past = past_msg.lower()
            for archetype, patterns in _SIGNAL_PATTERNS.items():
                hits = sum(1 for p in patterns if p in past)
                scores[archetype] = scores.get(archetype, 0) + hits * 0.5

    # Normalizza in probabilità
    total = sum(scores.values()) or 1
    vector = {k: round(v / total, 3) for k, v in scores.items()}

    # Ordina per score
    sorted_archetypes = sorted(vector.items(), key=lambda x: x[1], reverse=True)

    primary = sorted_archetypes[0][0]
    primary_conf = sorted_archetypes[0][1]
    secondary = None
    overlap_weight = 0.0

    if len(sorted_archetypes) > 1 and sorted_archetypes[1][1] > 0.20:
        secondary = sorted_archetypes[1][0]
        overlap_weight = sorted_archetypes[1][1]

    # Nessun segnale trovato → incerto
    if primary_conf == 0:
        primary = "UNKNOWN"
        primary_conf = 0.0

    # Determina context
    context = _detect_context(msg)

    # Blend needed se primary non dominante
    blend_needed = primary_conf < 0.70 and secondary is not None

    return ArchetypeResult(
        primary=primary,
        secondary=secondary,
        vector=vector,
        confidence=primary_conf,
        context=context,
        signals_found=found_signals.get(primary, []),
        overlap_weight=overlap_weight,
        blend_needed=blend_needed
    )


def _detect_context(msg: str) -> str:
    """Rileva il contesto della conversazione dal messaggio."""
    scores = {}
    for ctx, patterns in _CONTEXT_PATTERNS.items():
        scores[ctx] = sum(1 for p in patterns if p in msg)

    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "day1_response"


def get_best_response(
    primary_archetype: str,
    context: str,
    secondary_archetype: str = None,
    top_k: int = 3
) -> list[dict]:
    """
    Recupera le migliori risposte dal dataset sintetico per archetype + context.

    Args:
        primary_archetype: Archetipo primario classificato
        context: Contesto della conversazione
        secondary_archetype: Archetipo secondario (per overlap)
        top_k: Numero di risposte da restituire

    Returns:
        Lista di dict con optimal_response, trap_response, why_trap, outcome_predicted
    """
    if not _CONVERSATIONS_FILE.exists():
        return []

    with open(_CONVERSATIONS_FILE) as f:
        data = json.load(f)

    conversations = data.get("conversations", [])

    # Score matching
    results = []
    for conv in conversations:
        score = 0

        # Primary match (peso 3)
        if conv.get("primary_archetype") == primary_archetype:
            score += 3

        # Context match (peso 2)
        if conv.get("context") == context:
            score += 2

        # Secondary match (peso 1)
        if secondary_archetype and conv.get("secondary_archetype") == secondary_archetype:
            score += 1

        # Overlap conversations bonus
        if conv.get("secondary_archetype") and secondary_archetype:
            score += 0.5

        if score > 0:
            results.append((score, conv))

    # Ordina per score e ritorna top_k
    results.sort(key=lambda x: x[0], reverse=True)
    return [conv for _, conv in results[:top_k]]


def get_archetype_profile(archetype_name: str) -> dict:
    """Recupera il profilo completo di un archetipo dal JSON."""
    if not _ARCHETYPES_FILE.exists():
        return {}

    with open(_ARCHETYPES_FILE) as f:
        data = json.load(f)

    return data.get("archetypes", {}).get(archetype_name, {})


def format_response_for_agent(result: ArchetypeResult, best_responses: list[dict]) -> str:
    """
    Formatta il risultato classificazione + risposta ottimale per agent-sales.

    Returns:
        Stringa formattata con classificazione + risposta suggerita
    """
    lines = [
        f"ARCHETIPO: {result.primary} (confidence: {result.confidence:.2f})",
        f"CONTEXT: {result.context}",
    ]

    if result.secondary:
        lines.append(f"SECONDARY: {result.secondary} (weight: {result.overlap_weight:.2f})")
        if result.blend_needed:
            lines.append("BLEND: richiesto — primary non dominante")

    if result.signals_found:
        lines.append(f"SEGNALI: {', '.join(result.signals_found)}")

    if best_responses:
        best = best_responses[0]
        lines.append("\n--- RISPOSTA OTTIMALE ---")
        lines.append(best.get("optimal_response", ""))
        if best.get("trap_response"):
            lines.append("\n--- EVITARE ---")
            lines.append(f"TRAP: {best.get('trap_response', '')}")
            lines.append(f"PERCHÉ: {best.get('why_trap', '')}")
        if best.get("outcome_predicted"):
            lines.append(f"\nOUTCOME ATTESO: {best['outcome_predicted']}")

    return "\n".join(lines)


# ── CLI quick test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    test_messages = [
        "Quanto costa? E se facciamo più operazioni mi fate uno sconto?",
        "CarFax EU non esiste come standard unico — lei intende un HPI check?",
        "Il prezzo sorgente è IVA esposta o regime margine? Perché cambia tutto.",
        "Chi ti ha dato questo numero?",
        "48 ore. Se non arriva il foglio considera chiuso.",
        "Lavoro solo con persone che conosco — è una questione di fiducia.",
        "Ho sempre fatto così e non ho avuto problemi — non vedo perché cambiare.",
        "Quanti dealer nella mia zona usano già questo? Se lo fanno tutti non mi interessa.",
    ]

    msg = sys.argv[1] if len(sys.argv) > 1 else test_messages[0]

    result = classify(msg)
    responses = get_best_response(result.primary, result.context, result.secondary)
    output = format_response_for_agent(result, responses)

    print(f"\nInput: {msg}\n")
    print(output)
