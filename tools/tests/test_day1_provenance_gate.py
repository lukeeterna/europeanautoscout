#!/usr/bin/env python3
"""
test_day1_provenance_gate.py — verifica che il gate Day-1 (validate_day1) RIFIUTI
ogni riferimento alla provenienza estera/import: termini diretti E perifrasi
eufemistiche. Ogni frase vietata deve produrre una violazione "(v)" → exit 1.

Contesto: la perifrasi "auto che arrivano da fuori mercato italiano" passava il gate
(il validator non guardava la provenienza). Questo test blocca quel buco e le sue varianti.
Stdlib only. Eseguibile: python3 tools/tests/test_day1_provenance_gate.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from validate_day1 import validate_day1  # noqa: E402

# profilo minimo (nessun numero/marca in gioco: isoliamo il check provenienza)
PROFILE = {"company_name": "Test Srl", "top_brands": ["Audi"], "example_vehicles": []}
KB_LINES = []  # nessun FATTO KB → nessun numero ammesso, ok: i messaggi non usano cifre

# base conforme: identità 'Azzurra' + opt-out 'no grazie', zero numeri, zero provenienza
BASE = ("Sono Azzurra, assistente di Luca Ferretti. Lavoriamo con concessionari come "
        "il vostro. {inject} Se non interessa, un no grazie e non la disturbo. Vi va?")

# ogni voce DEVE generare almeno una violazione (v)
FORBIDDEN_PHRASES = [
    "Le auto che arrivano da fuori mercato italiano hanno piu' rischi.",
    "Parliamo di auto fuori dall'Italia.",
    "Sono vetture che vengono da oltre confine.",
    "Hanno provenienza estera.",
    "Sono auto non nazionali.",
    "Arrivano da altri paesi.",
    "Arrivano da altri mercati.",
    "Trattiamo auto dall'estero.",
    "Ci occupiamo di import.",
    "Sono auto importate di recente.",
    "Gestiamo l'importazione.",
    "Facciamo reimportazione.",
    "Le prendiamo in Germania.",
    "Sono veicoli EU.",
]


def _has_v(message):
    viol = validate_day1(message, PROFILE, KB_LINES)
    return any(v.startswith("(v)") for v in viol), viol


def main():
    failures = []
    # 1) ogni frase vietata → almeno una (v)
    for phrase in FORBIDDEN_PHRASES:
        msg = BASE.format(inject=phrase)
        hit, viol = _has_v(msg)
        status = "OK " if hit else "FAIL"
        print(f"  [{status}] vietata: {phrase!r}")
        if not hit:
            failures.append(f"NON rilevata: {phrase!r} → viol={viol}")

    # 2) control: messaggio pulito (nessuna provenienza) → NESSUNA (v)
    clean = BASE.format(inject="Ci occupiamo di controlli sui chilometri.")
    hit, viol = _has_v(clean)
    print(f"  [{'OK ' if not hit else 'FAIL'}] control pulito → nessuna (v)")
    if hit:
        failures.append(f"falso positivo su messaggio pulito → viol={viol}")

    n = len(FORBIDDEN_PHRASES) + 1
    if failures:
        print(f"\n❌ FAIL {len(failures)}/{n}:")
        for f in failures:
            print(f"   → {f}")
        return 1
    print(f"\n✅ PASS {n}/{n}: provenienza estera/import rifiutata (diretti + perifrasi).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
