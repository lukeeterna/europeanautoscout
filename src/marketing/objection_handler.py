#!/usr/bin/env python3.11
"""
OBJECTION HANDLER — ARGOS Automotive CoVe 2026
================================================
Wrapper canonico: delega a ObjectionLibrary + PersonaEngine.
Schema OBJ codes canonici (ARGOS_HANDOFF_S50 §1.2):
  OBJ-1 = "Ho già fornitori EU"
  OBJ-2 = "Il prezzo/fee non mi convince"
  OBJ-3 = "Non ho tempo / ci penso"
  OBJ-4 = "Non capisco come funziona / garanzie"
  OBJ-5 = "Devo sentire il socio/titolare"

Archetipi canonici: RAGIONIERE | BARONE | PERFORMANTE | NARCISO | TECNICO

Usage:
    from src.marketing.objection_handler import handle, ObjectionHandler
    response = handle("OBJ-1", "RAGIONIERE")
"""

import sys
import os

# ── Mapping vecchi nomi → canonici (retrocompatibilità) ────────
_PERSONA_LEGACY_MAP = {
    "TRADIZIONALE":  "RAGIONIERE",
    "STRATEGICO":    "PERFORMANTE",
    "IMPRENDITORE":  "RAGIONIERE",
    "LAUREATO":      "TECNICO",
}

# ── OBJ codes canonici ───────────────────────────────────────
OBJ_CODES = {
    "OBJ-1": "Ho già fornitori EU",
    "OBJ-2": "Il prezzo/fee non mi convince",
    "OBJ-3": "Non ho tempo / ci penso",
    "OBJ-4": "Non capisco come funziona / garanzie",
    "OBJ-5": "Devo sentire il socio/titolare",
}

# ── Template matrix (5 OBJ × 5 persona) ─────────────────────
_TEMPLATES = {
    "OBJ-1": {
        "RAGIONIERE": (
            "Mario, lo capisco. Il servizio ARGOS™ non sostituisce i suoi fornitori attuali "
            "— li affianca su segmenti specifici non coperti. "
            "Posso mostrarle 3 casi recenti con delta prezzo documentato?"
        ),
        "BARONE": (
            "La apprezzo per la sua rete consolidata. ARGOS™ serve i dealer selezionati "
            "che vogliono accesso a opportunità che gli altri non vedono. Non è per tutti."
        ),
        "PERFORMANTE": (
            "Certo, hai già qualcuno. Ma su BMW/Mercedes premium D → IT, "
            "ti mando un'analisi rapida — 2 minuti. Se non è interessante, chiudo qui."
        ),
        "NARCISO": (
            "Ha già una rete? Perfetto. ARGOS™ si integra — è un layer analytics supplementare "
            "per segmenti high-margin che i feed standard non coprono."
        ),
        "TECNICO": (
            "Comprendo. Posso mostrarle un confronto oggettivo: prezzi EU trovati da ARGOS™ "
            "vs prezzi mercato IT su stesse specifiche. Dati reali, verificabili."
        ),
    },
    "OBJ-2": {
        "RAGIONIERE": (
            "Mario, la fee è €800-1.200 success-only — zero se non procediamo. "
            "Su una BMW 5 serie con delta prezzo medio €3.800, il ROI è 3-4x. Vuole i numeri?"
        ),
        "BARONE": (
            "Il suo tempo vale molto di più. La fee copre 40+ ore di ricerca, verifica VIN, "
            "analisi mercato. Su un veicolo da €35k, è meno dell'1%."
        ),
        "PERFORMANTE": (
            "Fee unica, solo a successo. Nessun abbonamento, nessun rischio. "
            "Un'operazione copre la fee 3-4 volte."
        ),
        "NARCISO": (
            "Guarda: fee success-only, dati Vincario certificati, report analytics completo. "
            "Per dealer che fanno volume, il payback è sul primo veicolo."
        ),
        "TECNICO": (
            "La fee è parametrizzata sul valore del veicolo (1.8-3.2%). "
            "Posso mandarle il breakdown completo con scenari ROI su 3 fasce di prezzo."
        ),
    },
    "OBJ-3": {
        "RAGIONIERE": (
            "Capisco, Mario. Le mando la scheda in PDF — 2 pagine, "
            "può leggerla quando vuole. Nessun impegno."
        ),
        "BARONE": (
            "Non rubo altro tempo. Le mando il materiale "
            "— lo guarda con calma quando preferisce."
        ),
        "PERFORMANTE": (
            "Ok, nessun problema. Ti mando tutto in 30 secondi "
            "— guardi quando hai 5 minuti."
        ),
        "NARCISO": "Capito. Ti mando il deck rapido — quando sei free dai un'occhiata.",
        "TECNICO": (
            "Capisco. Le mando la documentazione tecnica completa "
            "— può esaminarlo senza fretta."
        ),
    },
    "OBJ-4": {
        "RAGIONIERE": (
            "Il processo è documentato: 1) Riceviamo il brief, 2) Scouting EU 48h, "
            "3) Report Vincario + CoVe score, 4) Presentazione offerta, "
            "5) Gestione logistica. Fee solo al punto 5."
        ),
        "BARONE": (
            "Il processo è curato nei dettagli: analisi personalizzata, "
            "verifica documentale completa, accompagnamento fino alla consegna. Trasparenza totale."
        ),
        "PERFORMANTE": (
            "Semplice: brief → scouting → verifica → deal. "
            "Tutto tracciato. Mando il flow diagram ora."
        ),
        "NARCISO": (
            "Stack tecnico: scraping multi-country, VIN check Vincario, "
            "scoring algoritmico, matching con il tuo target. Posso mostrarle l'architettura."
        ),
        "TECNICO": (
            "Posso mandarle la documentazione tecnica completa del processo di verifica: "
            "metodologia VIN, fonti dati, algoritmo di scoring. Tutto verificabile."
        ),
    },
    "OBJ-5": {
        "RAGIONIERE": (
            "Capisco. Le preparo un executive summary di 1 pagina con ROI analysis "
            "— così il titolare ha già tutto il necessario per decidere."
        ),
        "BARONE": (
            "Certo. Preparo un documento riassuntivo per la sua riunione "
            "— presentato nel modo giusto."
        ),
        "PERFORMANTE": (
            "Ok, manda al socio il materiale "
            "— glielo preparo in 10 minuti in formato presentazione."
        ),
        "NARCISO": "Perfetto. Preparo un deck breve per il team — così la presentazione è già pronta.",
        "TECNICO": (
            "Comprendo. Preparo documentazione tecnica e contrattuale completa "
            "— così il titolare ha tutto per valutare."
        ),
    },
}


def _normalize_persona(persona: str) -> str:
    """Mappa nomi legacy → canonici."""
    p = persona.upper().strip()
    return _PERSONA_LEGACY_MAP.get(p, p)


def handle(obj_code: str, dealer_persona: str = "RAGIONIERE", **kwargs) -> str:
    """
    Genera risposta per obiezione data l'archetipo del dealer.

    Args:
        obj_code: OBJ-1..OBJ-5
        dealer_persona: RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO
                        (supporta anche nomi legacy: TRADIZIONALE, IMPRENDITORE, ecc.)

    Returns:
        Stringa template risposta pronto per WhatsApp.
    """
    code    = obj_code.upper().strip()
    persona = _normalize_persona(dealer_persona)

    if code not in _TEMPLATES:
        return "Capisco la sua posizione. Posso mandarle materiale dettagliato per valutare con calma?"

    persona_templates = _TEMPLATES[code]
    return persona_templates.get(persona, persona_templates.get("RAGIONIERE",
        "Capisco la sua posizione. Posso mandarle materiale dettagliato per valutare con calma?"))


class ObjectionHandler:
    """
    Wrapper classe per retrocompatibilità con codice esistente.
    Internamente delega a handle() canonico.
    """

    def handle(
        self,
        obj_code: str,
        dealer_personality: str = "RAGIONIERE",
        dealer_name: str = "",
        vehicle_info: str = "",
    ) -> dict:
        persona  = _normalize_persona(dealer_personality)
        message  = handle(obj_code, persona)

        # Sostituisci placeholder nome se presente
        if dealer_name:
            name = dealer_name.split()[0]
            message = message.replace("{name}", f" {name}").replace("[Nome]", name)

        return {
            "obj_code":              obj_code.upper(),
            "message":               message,
            "follow_up_delay_hours": 48,
            "escalate":              False,
        }

    def list_objections(self) -> dict:
        return dict(OBJ_CODES)


# ─────────────────────────────────────────────────────────────────────
# CLI quick-test
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Verifica OBJ codes canonici × 5 archetipi:")
    print("=" * 60)
    personas = ["RAGIONIERE", "BARONE", "PERFORMANTE", "NARCISO", "TECNICO"]
    errors   = []
    for obj in OBJ_CODES:
        for p in personas:
            t = handle(obj, p)
            if not t or len(t) < 20:
                errors.append(f"VUOTO: {obj} × {p}")
            else:
                print(f"✅ {obj} × {p}: {t[:60]}...")

    # Test retrocompatibilità legacy
    legacy_tests = [("OBJ-1", "TRADIZIONALE"), ("OBJ-2", "IMPRENDITORE"), ("OBJ-3", "LAUREATO")]
    for obj, legacy in legacy_tests:
        t = handle(obj, legacy)
        print(f"✅ Legacy {legacy} → {_normalize_persona(legacy)}: {t[:50]}...")

    if errors:
        print(f"\n❌ Errori ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    else:
        print(f"\n✅ Tutti {len(OBJ_CODES) * len(personas)} template OK")
