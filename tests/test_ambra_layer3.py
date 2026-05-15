#!/usr/bin/env python3
"""
tests/test_ambra_layer3.py — S173 D-27 / D-28
Test AMBRA Layer 3 post mystery shopper handoff + micro-dealer commissione lexicon.

Scope: validation che build_system_prompt + ResponseValidator si comportano
correttamente nei 3 scenari Layer 3 (D-27 handoff_source='mystery_shopper').

3 mock scenarios (specifica AMBRA-AUDIT.md sez 6.3):
  Mock 1 — Reactive identity: dealer "ah si' Argos, mi ha detto X"
           → no self-introduction, "argos" allowed in response
  Mock 2 — Skeptical objection: dealer "boh non mi convince"
           → KB micro-dealer + obiezione "non mi fido"
  Mock 3 — Cost question: dealer "quanto costa"
           → COSTI variante commissione (no margine premium)

Validation per ogni mock:
  (a) "ARGOS" bannato se handoff_source='cold', OK se 'mystery_shopper'
  (b) Lessico target presente se is_micro_dealer=True (almeno 2 termini D-28)
  (c) ResponseValidator pass / fail come atteso

Usage:
  python3 tests/test_ambra_layer3.py          # all tests
  python3 -m unittest tests.test_ambra_layer3 -v
"""

import os
import sys
import unittest
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'wa-intelligence'))

# Import target. NB: response-analyzer.py contiene trattino → import via importlib.
import importlib.util
_ra_path = PROJECT_ROOT / 'wa-intelligence' / 'response-analyzer.py'
_spec = importlib.util.spec_from_file_location('response_analyzer', _ra_path)
ra = importlib.util.module_from_spec(_spec)
# Side-effect: response_analyzer at import-time tenta load .env + KB.
# Per test unit, isoliamo: stubbiamo env minimo prima dell'exec_module.
os.environ.setdefault('ARGOS_API_KEY', 'test-key-s173')
_spec.loader.exec_module(ra)

# Helpers state_machine (clean import — no trattini)
import state_machine as sm  # noqa: E402


# ── Mock LLM responses ────────────────────────────────────────
# Risposte LLM simulate: rappresentano cosa AMBRA dovrebbe produrre
# nei 3 scenari Layer 3. NB: questi NON sono "ground truth" verificati
# su micro-dealer reali (vedi AMBRA-AUDIT sez 8.4 critica strutturale #4)
# — sono assumption iniziali da calibrare S175 mystery shopper pilot fisico.

MOCK_RESPONSE_REACTIVE_IDENTITY = (
    '{"messages": ['
    '"si\' guardi, sono Luca di Argos, '
    'il cliente che e\' passato da lei le aveva accennato di me", '
    '"riprendo io il filo, '
    'mi diceva che cercava una X3 sotto i 35k"'
    ']}'
)

MOCK_RESPONSE_SKEPTICAL_MICRO = (
    '{"messages": ['
    '"capisco perfettamente, e\' normale stare attenti", '
    '"se vuole le mando una scheda completa su una macchina su ordine, '
    'gratis e senza impegno — lavoro su richiesta cliente, non tengo stock"'
    ']}'
)

MOCK_RESPONSE_COST_COMMISSION = (
    '{"messages": ['
    '"ne parliamo quando trova l\'auto giusta, zero anticipo", '
    '"lei addebita al cliente il totale, '
    'la commissione sua e\' la differenza — '
    'tipicamente €1.500-3.000 a macchina su ordine"'
    ']}'
)

# Risposta scorretta (control test): contiene "argos" in scenario cold
MOCK_RESPONSE_VIOLATING_COLD = (
    '{"messages": ['
    '"buongiorno, sono Luca di Argos, le scrivo per proporle..."'
    ']}'
)


class TestLayer3PromptBuilding(unittest.TestCase):
    """Verifica build_system_prompt risponde a handoff_source + is_micro_dealer."""

    def test_cold_default_identity(self):
        """cold (default) → identity attuale, no TARGET_LEXICON."""
        prompt = ra.build_system_prompt('NARCISO', 'INBOUND', handoff_source='cold')
        self.assertIn('Sei Luca Ferretti', prompt)
        self.assertIn('contattato il dealer PER PRIMO', prompt)
        self.assertNotIn('TARGET_LEXICON', prompt)
        # Hard rules: ban ARGOS attivo
        self.assertIn('MAI menzionare queste parole', prompt)

    def test_mystery_shopper_post_handoff_identity(self):
        """mystery_shopper → identity_post_handoff, ban ARGOS rilassato."""
        prompt = ra.build_system_prompt(
            'RAGIONIERE', 'INBOUND', handoff_source='mystery_shopper'
        )
        self.assertIn('gia\' sentito parlare di te', prompt)
        self.assertIn('NON SEI il first-contact', prompt)
        # Hard rules variant: "Argos" OK come reaction
        self.assertIn("\"Argos\" e' OK come reaction", prompt)

    def test_micro_dealer_injects_lexicon(self):
        """is_micro_dealer=True → TARGET_LEXICON presente con lessico commissione."""
        prompt = ra.build_system_prompt(
            'DEFAULT', 'INBOUND',
            handoff_source='mystery_shopper',
            is_micro_dealer=True,
        )
        self.assertIn('TARGET_LEXICON', prompt)
        self.assertIn('commissione', prompt)
        self.assertIn('non tengo stock', prompt)
        # Esclusioni esplicite
        self.assertIn("EVITA", prompt)

    def test_referral_fallback_to_cold(self):
        """referral attualmente fallback a cold (deferred D-12)."""
        prompt_referral = ra.build_system_prompt(
            'DEFAULT', 'INBOUND', handoff_source='referral'
        )
        prompt_cold = ra.build_system_prompt(
            'DEFAULT', 'INBOUND', handoff_source='cold'
        )
        # Stessa identity per ora (referral non implementato → fallback cold)
        self.assertEqual(prompt_referral, prompt_cold)

    def test_invalid_handoff_source_fallback_safe(self):
        """handoff_source invalido (in caller) → comportamento safe = identity cold."""
        # Note: build_system_prompt non valida (fallback implicito: else branch).
        # Wire-up in main() valida e collassa a 'cold'.
        prompt = ra.build_system_prompt(
            'DEFAULT', 'INBOUND', handoff_source='invalid_xyz'
        )
        self.assertIn('contattato il dealer PER PRIMO', prompt)


class TestLayer3ResponseValidator(unittest.TestCase):
    """Verifica ResponseValidator riconosce handoff_source per ban ARGOS."""

    def setUp(self):
        self.validator = ra.ResponseValidator()

    def test_mock1_reactive_argos_allowed_post_handoff(self):
        """Mock 1: 'argos' OK quando handoff_source='mystery_shopper'."""
        violations = self.validator.validate(
            MOCK_RESPONSE_REACTIVE_IDENTITY,
            cls_type='POSITIVE',
            prev_msgs=[],
            vehicle_ctx='',
            handoff_source='mystery_shopper',
        )
        # No "banned_exact: argos" deve apparire
        argos_violations = [v for v in violations if 'argos' in v.lower()]
        self.assertEqual(
            argos_violations, [],
            f"argos non doveva essere flagged in mystery_shopper, violations={violations}"
        )

    def test_mock1_reactive_argos_blocked_cold(self):
        """Control: 'argos' BLOCKED quando handoff_source='cold' (default)."""
        violations = self.validator.validate(
            MOCK_RESPONSE_VIOLATING_COLD,
            cls_type='POSITIVE',
            prev_msgs=[],
            vehicle_ctx='',
            handoff_source='cold',
        )
        argos_violations = [v for v in violations if 'argos' in v.lower()]
        self.assertGreaterEqual(
            len(argos_violations), 1,
            "argos doveva essere flagged in handoff_source=cold"
        )

    def test_mock2_skeptical_micro_dealer_lexicon_present(self):
        """Mock 2: risposta skeptical contiene 2+ termini D-28 lexicon."""
        text = MOCK_RESPONSE_SKEPTICAL_MICRO.lower()
        d28_terms = ['su ordine', 'non tengo stock', 'su richiesta']
        present = [t for t in d28_terms if t in text]
        self.assertGreaterEqual(
            len(present), 2,
            f"Mock 2 deve contenere ≥2 termini D-28, trovati: {present}"
        )

    def test_mock3_cost_no_margin_lexicon(self):
        """Mock 3: risposta cost usa 'commissione', NON 'margine premium'."""
        text = MOCK_RESPONSE_COST_COMMISSION.lower()
        self.assertIn('commissione', text)
        # Non deve usare lessico V3 transactional (margine premium €4-7k)
        self.assertNotIn('margine premium', text)
        self.assertNotIn('€4.000', text)
        self.assertNotIn('€7.000', text)

    def test_mock3_cost_no_fee_leak_when_OBJ2(self):
        """Mock 3: cost question = OBJ-2 → fee_leak check non triggera."""
        violations = self.validator.validate(
            MOCK_RESPONSE_COST_COMMISSION,
            cls_type='OBJ-2',
            prev_msgs=[],
            vehicle_ctx='',
            handoff_source='mystery_shopper',
        )
        fee_leaks = [v for v in violations if 'fee_leak' in v]
        self.assertEqual(fee_leaks, [], f"OBJ-2 non deve flag fee_leak, got {violations}")


class TestLayer3StateMachineHelpers(unittest.TestCase):
    """Verifica helper state_machine S173 (no DB write — solo logic)."""

    def test_is_post_handoff_true(self):
        dealer = {'handoff_source': 'mystery_shopper'}
        self.assertTrue(sm.is_post_handoff(dealer))

    def test_is_post_handoff_false_cold(self):
        self.assertFalse(sm.is_post_handoff({'handoff_source': 'cold'}))
        self.assertFalse(sm.is_post_handoff({}))  # default

    def test_is_post_handoff_false_referral(self):
        # referral NON e' post-handoff (D-12 deferred)
        self.assertFalse(sm.is_post_handoff({'handoff_source': 'referral'}))

    def test_valid_handoff_sources_enum(self):
        self.assertIn('cold', sm.VALID_HANDOFF_SOURCES)
        self.assertIn('mystery_shopper', sm.VALID_HANDOFF_SOURCES)
        self.assertIn('referral', sm.VALID_HANDOFF_SOURCES)
        self.assertNotIn('invalid_xyz', sm.VALID_HANDOFF_SOURCES)


if __name__ == '__main__':
    unittest.main(verbosity=2)
