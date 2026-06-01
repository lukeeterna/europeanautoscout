#!/usr/bin/env python3
"""
ARGOS Stress Test Autonomo — 10 scenari dealer "cattivi"
Testa il response-analyzer v2 senza daemon (classificazione + LLM + validazione locale).

Usage:
  python3 tools/stress_test_autonomous.py              # tutti gli scenari
  python3 tools/stress_test_autonomous.py --local-only  # solo classifier + validator, no LLM
  python3 tools/stress_test_autonomous.py --scenario 3  # singolo scenario
"""

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

# ── Import response-analyzer (filename has hyphen) ────────────
RA_PATH = Path(__file__).resolve().parents[1] / 'wa-intelligence' / 'response-analyzer.py'
spec = importlib.util.spec_from_file_location('response_analyzer', str(RA_PATH))
ra = importlib.util.module_from_spec(spec)

# Suppress .env loading errors (no iMac env)
_orig_env = os.environ.copy()
spec.loader.exec_module(ra)

# ── 10 Scenari Dealer Difficili ───────────────────────────────
SCENARIOS = [
    {
        'id': 1,
        'msg': "Ma chi cazzo sei? Non ti ho mai visto in vita mia",
        'expected_cls': 'NEGATIVE',
        'desc': 'Insulto + rifiuto aggressivo',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 2,
        'msg': "Quanto costa il servizio? Qual è la vostra fee?",
        'expected_cls': 'OBJECTION',
        'expected_obj': 'OBJ-2',
        'desc': 'Domanda diretta su fee/costi',
        'checks': ['fee_allowed', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 3,
        'msg': "Ho un cliente che cerca una BMW X3 2022 budget 35k, ce l'avete?",
        'expected_cls': 'VEHICLE_REQUEST',
        'desc': 'Richiesta veicolo specifica con budget',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 4,
        'msg': "Non mi fido, come faccio a sapere che non è una truffa? Ho sentito di gente che ha perso soldi con questi servizi online",
        'expected_cls': 'OBJECTION',
        'expected_obj': 'OBJ-4',
        'desc': 'Obiezione fiducia/sicurezza',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 5,
        'msg': "Ci penso e ti faccio sapere",
        'expected_cls': ['UNKNOWN', 'POSITIVE', 'OBJECTION'],  # SOFT_NO non esiste
        'desc': 'Soft-no, disimpegno gentile',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 6,
        'msg': "Già importo dalla Germania da solo, ho i miei contatti da 10 anni",
        'expected_cls': 'OBJECTION',
        'expected_obj': 'OBJ-1',
        'desc': 'Già ha fornitore/importa da solo',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 7,
        'msg': "Mandami un esempio concreto, voglio vedere un caso reale",
        'expected_cls': 'POSITIVE',
        'desc': 'Richiesta esempio concreto — deve usare dati reali',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
    },
    {
        'id': 8,
        'msg': "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAs",
        'expected_cls': 'MEDIA',
        'desc': 'Immagine JPEG base64',
        'checks': ['no_banned'],
    },
    {
        'id': 9,
        'msg': "ok",
        'expected_cls': 'POSITIVE',
        'desc': '"ok" dopo 3 scambi — deve avanzare',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned'],
        'history': [
            {'direction': 'OUTBOUND', 'body': 'ciao, ho trovato una BMW X3 interessante'},
            {'direction': 'INBOUND', 'body': 'dimmi di più'},
            {'direction': 'OUTBOUND', 'body': 'guarda, è un 2022 con 45k km dalla Germania'},
        ],
    },
    {
        'id': 10,
        'msg': "Sei un bot? Mi sembra un messaggio automatico",
        'expected_cls': 'CURIOSITY',
        'desc': 'Anti-bot detection — deve rispondere naturale',
        'checks': ['no_fee', 'no_invented_prices', 'no_banned', 'no_bot_admission'],
    },
]


def check_response(text: str, scenario: dict, cls_result: dict) -> dict:
    """Verifica la risposta contro i check dello scenario."""
    results = {'pass': True, 'violations': [], 'warnings': []}

    checks = scenario.get('checks', [])
    lower = text.lower()

    for check in checks:
        if check == 'no_fee':
            # Fee non deve comparire (tranne se scenario la permette)
            if any(w in lower for w in ['fee', '€1.000', '1.000 euro', 'costo del servizio']):
                results['violations'].append('FEE_LEAK: fee menzionata senza richiesta')
                results['pass'] = False

        elif check == 'fee_allowed':
            # Fee deve comparire ed essere €1.000
            if any(w in lower for w in ['fee', '€1.000', '1.000']):
                # Verifica importo corretto
                fee_ctx = re.findall(r'€\s*[\d.]+', lower)
                for fc in fee_ctx:
                    if '1.000' not in fc and '1000' not in fc:
                        results['violations'].append(f'FEE_WRONG: importo sbagliato {fc}')
                        results['pass'] = False

        elif check == 'no_invented_prices':
            # Cerca prezzi EUR che non sono nel contesto
            prices = re.findall(r'€\s*([\d.]+)', text)
            for p in prices:
                normalized = p.replace('.', '')
                if normalized not in ('1000', '1200', '800'):  # fee range
                    results['warnings'].append(f'PRICE_CHECK: €{p} — verificare se reale')

        elif check == 'no_banned':
            for word in ra._LLM_BANNED_WORDS:
                if word in lower:
                    results['violations'].append(f'BANNED: "{word}"')
                    results['pass'] = False

        elif check == 'no_bot_admission':
            bot_admissions = ['sono un bot', 'sono automatico', 'intelligenza artificiale',
                              'sono un programma', 'sono un assistente']
            for ba in bot_admissions:
                if ba in lower:
                    results['violations'].append(f'BOT_ADMISSION: "{ba}"')
                    results['pass'] = False

    return results


def run_scenario(scenario: dict, local_only: bool = False) -> dict:
    """Esegue un singolo scenario di stress test."""
    sid = scenario['id']
    msg = scenario['msg']

    result = {
        'id': sid,
        'desc': scenario['desc'],
        'cls_pass': False,
        'llm_pass': None,
        'validator_pass': None,
        'response_check_pass': None,
        'response_text': '',
        'violations': [],
        'warnings': [],
    }

    # 1. Classificazione
    cls = ra.classify_message(msg)
    expected = scenario['expected_cls']
    if isinstance(expected, list):
        result['cls_pass'] = cls['type'] in expected
    else:
        result['cls_pass'] = cls['type'] == expected
    result['cls_type'] = cls['type']
    result['cls_confidence'] = cls.get('confidence', 0)

    if not result['cls_pass']:
        result['violations'].append(
            f"CLS: expected {expected}, got {cls['type']} ({cls.get('method', '?')})")

    # NEGATIVE → no LLM needed
    if cls['type'] == 'NEGATIVE':
        result['llm_pass'] = True  # correct: no response
        result['validator_pass'] = True
        result['response_check_pass'] = True
        return result

    if local_only and not scenario.get('_template_response'):
        return result

    # 2. Genera risposta via LLM (o usa template se fornito)
    dealer = {
        'dealer_name': f'Stress Test #{sid}',
        'persona_type': 'RAGIONIERE',
        'current_step': 'DAY1_SENT',
        'city': 'Foggia',
        'message_history': scenario.get('history', []),
    }

    # MEDIA → tratta come POSITIVE (come fa main())
    if cls['type'] == 'MEDIA':
        cls['type'] = 'POSITIVE'
        msg = '[Il dealer ha inviato una foto/immagine]'

    # Use template response if provided (--with-templates mode)
    template_response = scenario.get('_template_response')
    if template_response:
        llm_result = {'text': template_response, 'model': 'template'}
    else:
        archetype = dealer.get('persona_type', 'DEFAULT')
        system_prompt = ra.build_system_prompt(archetype, cls['type'])
        user_prompt = ra.build_user_prompt(dealer, msg, cls, dealer.get('message_history', []))
        llm_result = ra.call_llm(system_prompt, user_prompt)

    if not llm_result.get('text'):
        result['llm_pass'] = False
        result['violations'].append(f"LLM_FAIL: {llm_result.get('error', 'no text')}")
        return result

    result['llm_pass'] = True
    result['response_text'] = llm_result['text'][:500]
    result['model'] = llm_result.get('model', '?')

    # 3. Validator v2
    msg_history = dealer.get('message_history', [])
    v2_violations = ra._validator.validate(llm_result['text'], cls['type'], msg_history, '')
    blocking = [v for v in v2_violations if any(k in v for k in ['banned', 'fee_leak', 'prezzo_inventato'])]
    result['validator_pass'] = len(blocking) == 0
    if blocking:
        result['violations'].extend(blocking)

    # 4. Response-level checks
    response_check = check_response(llm_result['text'], scenario, cls)
    result['response_check_pass'] = response_check['pass']
    result['violations'].extend(response_check['violations'])
    result['warnings'].extend(response_check['warnings'])

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='ARGOS Stress Test Autonomo')
    parser.add_argument('--local-only', action='store_true',
                        help='Solo classifier + validator, no LLM')
    parser.add_argument('--scenario', type=int,
                        help='Esegui singolo scenario (1-10)')
    parser.add_argument('--with-templates', action='store_true',
                        help='Testa validator su risposte template simulate (no LLM needed)')
    args = parser.parse_args()

    # Template responses per testare validator senza LLM
    TEMPLATE_RESPONSES = {
        2: json.dumps({"messages": [
            "ciao, guarda il servizio funziona cosi",
            "la fee e' \u20ac1.000 fissa a macchina consegnata, zero anticipi. paghi solo quando hai la macchina in salone\n\nLuca"
        ]}),
        3: json.dumps({"messages": [
            "ciao, si ho visto la richiesta",
            "guarda, al momento non ho una X3 specifica ma ci lavoro subito. ti mando i dettagli entro 48h\n\nLuca"
        ]}),
        4: json.dumps({"messages": [
            "capisco la diffidenza, e' giusto",
            "senti, io non chiedo anticipi. si paga solo a macchina consegnata e approvata da lei. km certificati, storico verificato, garanzia costruttore UE\n\nLuca"
        ]}),
        5: json.dumps({"messages": [
            "nessun problema, si prenda il tempo che serve",
            "se le capita di avere un cliente che cerca una tedesca, mi faccia un fischio\n\nLuca"
        ]}),
        6: json.dumps({"messages": [
            "capisco, 10 anni di esperienza non sono pochi",
            "guarda, molti che importano da soli mi dicono che il tempo perso a cercare, verificare e gestire le pratiche vale piu di tutto. io gestisco ogni passaggio, lei si concentra sulla vendita\n\nLuca"
        ]}),
        7: json.dumps({"messages": [
            "certo, guarda ti faccio un esempio reale",
            "ti cerco qualcosa di concreto con km certificati e prezzo verificato. ti mando tutto entro 48h\n\nLuca"
        ]}),
        8: json.dumps({"messages": [
            "grazie per la foto",
            "guarda, se mi dici marca, modello e budget ti trovo qualcosa di simile dalla Germania con km certificati\n\nLuca"
        ]}),
        9: json.dumps({"messages": [
            "perfetto",
            "allora procedo, ti mando i dettagli della macchina con km certificati e storico completo entro domani\n\nLuca"
        ]}),
        10: json.dumps({"messages": [
            "ahah no, sono Luca",
            "guarda, se vuoi ci sentiamo a voce cosi ti spiego meglio come lavoro. quando ti fa comodo?\n\nLuca"
        ]}),
    }

    scenarios = SCENARIOS
    if args.with_templates:
        scenarios = []
        for s in SCENARIOS:
            s_copy = dict(s)
            if s['id'] in TEMPLATE_RESPONSES:
                s_copy['_template_response'] = TEMPLATE_RESPONSES[s['id']]
            scenarios.append(s_copy)

    if args.scenario:
        scenarios = [s for s in SCENARIOS if s['id'] == args.scenario]
        if not scenarios:
            print(f"Scenario {args.scenario} non trovato (1-10)")
            sys.exit(1)

    print("=" * 80)
    print("ARGOS STRESS TEST AUTONOMO — 10 scenari dealer difficili")
    print(f"Mode: {'LOCAL ONLY (no LLM)' if args.local_only else 'FULL (classifier + LLM + validator)'}")
    print("=" * 80)
    print()

    results = []
    total_pass = 0
    total_violations = 0

    for scenario in scenarios:
        print(f"--- Scenario #{scenario['id']}: {scenario['desc']} ---")
        print(f"  MSG: \"{scenario['msg'][:80]}...\"" if len(scenario['msg']) > 80 else f"  MSG: \"{scenario['msg']}\"")

        result = run_scenario(scenario, local_only=args.local_only)
        results.append(result)

        # Print result
        cls_icon = "✅" if result['cls_pass'] else "❌"
        print(f"  CLS: {cls_icon} {result.get('cls_type', '?')} (conf={result.get('cls_confidence', 0):.0%})")

        if result['llm_pass'] is not None:
            llm_icon = "✅" if result['llm_pass'] else "❌"
            print(f"  LLM: {llm_icon} {result.get('model', '?')}")

        if result['validator_pass'] is not None:
            val_icon = "✅" if result['validator_pass'] else "❌"
            print(f"  VAL: {val_icon}")

        if result['response_text']:
            # Show first 150 chars of response
            preview = result['response_text'][:150].replace('\n', ' ')
            print(f"  RSP: {preview}...")

        if result['violations']:
            for v in result['violations']:
                print(f"  🔴 {v}")
            total_violations += len(result['violations'])

        if result['warnings']:
            for w in result['warnings']:
                print(f"  ⚠️  {w}")

        # Overall pass (local-only: only classifier counts)
        if args.local_only:
            scenario_pass = result['cls_pass']
        else:
            scenario_pass = (
                result['cls_pass'] and
                result.get('llm_pass', True) and
                result.get('validator_pass', True) and
                result.get('response_check_pass', True)
            )
        if scenario_pass:
            total_pass += 1

        print()

    # Summary
    print("=" * 80)
    print(f"RISULTATO: {total_pass}/{len(scenarios)} scenari PASS")
    print(f"Violazioni totali: {total_violations}")
    print()

    # Breakdown
    cls_pass = sum(1 for r in results if r['cls_pass'])
    llm_pass = sum(1 for r in results if r.get('llm_pass', True))
    val_pass = sum(1 for r in results if r.get('validator_pass', True))

    print(f"  Classificazione: {cls_pass}/{len(results)}")
    print(f"  LLM generazione: {llm_pass}/{len(results)}")
    print(f"  Validator v2:    {val_pass}/{len(results)}")

    # Criteri PASS dal prompt S103
    fee_leaks = sum(1 for r in results for v in r['violations'] if 'FEE_LEAK' in v or 'fee_leak' in v)
    prices_invented = sum(1 for r in results for v in r['violations'] if 'prezzo_inventato' in v)
    banned = sum(1 for r in results for v in r['violations'] if 'BANNED' in v or 'banned' in v)

    print()
    print(f"  Fee leak:        {fee_leaks} (target: 0)")
    print(f"  Prezzi inventati: {prices_invented} (target: 0)")
    print(f"  Banned words:    {banned} (target: 0)")
    print(f"  Classificazione: {cls_pass}/{len(results)} (target: >= 8/10)")
    print("=" * 80)

    # Exit code
    if total_pass >= 8 and fee_leaks == 0 and prices_invented == 0 and banned == 0:
        print("🟢 STRESS TEST PASSED")
        return 0
    else:
        print("🔴 STRESS TEST FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
