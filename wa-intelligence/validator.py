#!/usr/bin/env python3
"""
validator.py — ARGOS™ Blocking Validator
Blueprint approvato S105 | Validatore BLOCCANTE

Se ritorna BLOCK: il messaggio NON viene inviato, MAI.
Logga violazione e notifica Telegram.
"""

import re


def validate(message: str, template_id: str, dealer_state: dict) -> dict:
    """Validazione bloccante pre-invio.

    Returns:
        {"result": "PASS"|"BLOCK", "check_failed": str|None, "reason": str}
    """
    checks = [
        _check_fee_leak(message, template_id),
        _check_identity_inversion(message),
        _check_banned_words(message),
        _check_length(message),
        _check_tech_leak(message),
    ]

    for check in checks:
        if check["result"] == "BLOCK":
            return check

    return {"result": "PASS", "check_failed": None, "reason": "All checks passed"}


def _check_fee_leak(message: str, template_id: str) -> dict:
    """Fee menzionata fuori dal template OBJ_2_FEE = BLOCK."""
    if template_id == "OBJ_2_FEE":
        return {"result": "PASS", "check_failed": None, "reason": ""}

    lower = message.lower()
    fee_patterns = ['1.000', '1000 euro', '€1.000', '€1000', 'fee', 'commissione',
                    'compenso', 'costo del servizio', 'la mia fee']
    for p in fee_patterns:
        if p in lower:
            return {
                "result": "BLOCK",
                "check_failed": "FEE_LEAK",
                "reason": f"Fee menzionata ('{p}') in template {template_id}"
            }
    return {"result": "PASS", "check_failed": None, "reason": ""}


def _check_identity_inversion(message: str) -> dict:
    """Rileva inversione soggetto/oggetto ('posso chiederle come ha avuto')."""
    lower = message.lower()
    inversion_patterns = [
        'posso chiederle come ha avuto',
        'posso chiederti come hai avuto',
        'come ha avuto il mio numero',  # Luca non deve mai chiedere questo
        'mi dica come ha avuto',
        'posso sapere come',
    ]
    for p in inversion_patterns:
        if p in lower:
            return {
                "result": "BLOCK",
                "check_failed": "IDENTITY_INVERSION",
                "reason": f"Inversione soggetto/oggetto: '{p}'"
            }
    return {"result": "PASS", "check_failed": None, "reason": ""}


def _check_banned_words(message: str) -> dict:
    """Parole bannate nei messaggi dealer."""
    lower = message.lower()
    banned = [
        'cove', 'claude', 'anthropic', 'openai', 'gpt', 'llm',
        'algoritmo', 'machine learning', 'intelligenza artificiale',
        'bot', 'automatico', 'embedding', 'rag', 'prompt',
        'piattaforma', 'sistema', 'argos',
    ]
    for word in banned:
        if re.search(r'\b' + re.escape(word) + r'\b', lower):
            return {
                "result": "BLOCK",
                "check_failed": "BANNED_WORD",
                "reason": f"Parola bannata: '{word}'"
            }
    return {"result": "PASS", "check_failed": None, "reason": ""}


def _check_length(message: str) -> dict:
    """Messaggi troppo lunghi = spam percepito."""
    lines = [l for l in message.strip().split('\n') if l.strip()]
    if len(lines) > 8:
        return {
            "result": "BLOCK",
            "check_failed": "TOO_LONG",
            "reason": f"Messaggio troppo lungo: {len(lines)} righe (max 8)"
        }
    if len(message) > 800:
        return {
            "result": "BLOCK",
            "check_failed": "TOO_LONG",
            "reason": f"Messaggio troppo lungo: {len(message)} chars (max 800)"
        }
    return {"result": "PASS", "check_failed": None, "reason": ""}


def _check_tech_leak(message: str) -> dict:
    """Non rivelare dettagli tecnici sul sourcing."""
    lower = message.lower()
    # "28 portali" o simili
    if re.search(r'\d+\s*portal', lower):
        return {
            "result": "BLOCK",
            "check_failed": "TECH_LEAK",
            "reason": "Dettaglio tecnico sourcing esposto"
        }
    return {"result": "PASS", "check_failed": None, "reason": ""}


if __name__ == '__main__':
    # Test
    print("=== Test FEE_LEAK ===")
    r = validate("La fee è 1.000 euro a consegna", "VEHICLE_PROPOSAL", {})
    print(f"  VEHICLE_PROPOSAL + fee: {r['result']} ({r.get('check_failed', '')})")
    assert r['result'] == 'BLOCK'

    r = validate("La fee è 1.000 euro a consegna", "OBJ_2_FEE", {})
    print(f"  OBJ_2_FEE + fee: {r['result']}")
    assert r['result'] == 'PASS'

    print("\n=== Test IDENTITY_INVERSION ===")
    r = validate("posso chiederle come ha avuto il mio numero?", "IDENTITY_RESPONSE", {})
    print(f"  Inversion: {r['result']} ({r.get('check_failed', '')})")
    assert r['result'] == 'BLOCK'

    print("\n=== Test BANNED_WORD ===")
    r = validate("Il nostro algoritmo trova le auto migliori", "VEHICLE_PROPOSAL", {})
    print(f"  'algoritmo': {r['result']} ({r.get('check_failed', '')})")
    assert r['result'] == 'BLOCK'

    print("\n=== Test PASS ===")
    r = validate("Buongiorno, ho trovato una BMW X3 2022 interessante per lei.", "VEHICLE_PROPOSAL", {})
    print(f"  Clean msg: {r['result']}")
    assert r['result'] == 'PASS'

    print("\nAll tests passed!")
