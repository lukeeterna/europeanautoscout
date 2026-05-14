"""Test message_analyzer — integration con LLMCascade reale.

Test fixtures + smoke tests parser/normalize, e (se GROQ_API_KEY available)
integration test reale 1 call.

Vincolo #1: test mockabile + opzionale live integration test.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from message_analyzer import (
    MessageAnalyzer, AnalysisResult, INTENTS, SENTIMENTS,
    _parse_response, _normalize, _msg_hash,
)


# ── Unit tests: parser robust ───────────────────────────────────────────────

def test_parse_plain_json() -> bool:
    print("\n=== test_parse_plain_json ===")
    text = '{"intent": "offer", "sentiment": "positive", "scam_flag": false, "scam_reason": "", "translation": "Hello", "summary": "interest in BMW"}'
    p = _parse_response(text)
    assert p["intent"] == "offer"
    print("  PASS")
    return True


def test_parse_markdown_wrapped() -> bool:
    print("\n=== test_parse_markdown_wrapped ===")
    text = '```json\n{"intent": "offer", "sentiment": "positive", "scam_flag": false, "scam_reason": "", "translation": "Hi", "summary": "ok"}\n```'
    p = _parse_response(text)
    assert p["intent"] == "offer"
    print("  PASS")
    return True


def test_parse_with_preamble() -> bool:
    print("\n=== test_parse_with_preamble ===")
    text = 'Here is the analysis:\n\n{"intent": "negotiation", "sentiment": "neutral", "scam_flag": false, "scam_reason": "", "translation": "test", "summary": "test"}\n\nLet me know if you need anything else.'
    p = _parse_response(text)
    assert p["intent"] == "negotiation"
    print("  PASS")
    return True


def test_normalize_unknown_intent() -> bool:
    print("\n=== test_normalize_unknown_intent ===")
    p = {"intent": "rage_quit", "sentiment": "neutral", "scam_flag": False}
    n = _normalize(p)
    assert n["intent"] == "objection", f"expected fallback to objection, got {n['intent']}"
    print("  PASS")
    return True


def test_normalize_missing_fields() -> bool:
    print("\n=== test_normalize_missing_fields ===")
    p = {"intent": "offer"}
    n = _normalize(p)
    assert n["intent"] == "offer"
    assert n["sentiment"] == "neutral"
    assert n["scam_flag"] is False
    assert n["scam_reason"] == ""
    print("  PASS")
    return True


def test_msg_hash_deterministic() -> bool:
    print("\n=== test_msg_hash_deterministic ===")
    h1 = _msg_hash("ciao", "it", "en")
    h2 = _msg_hash("ciao", "it", "en")
    h3 = _msg_hash("ciao", "it", "de")
    assert h1 == h2
    assert h1 != h3
    print("  PASS")
    return True


def test_cache_roundtrip() -> bool:
    """Cache layer salva + restituisce identico."""
    print("\n=== test_cache_roundtrip ===")
    with tempfile.TemporaryDirectory() as td:
        cache_db = Path(td) / "cache.sqlite"

        mock_response = {"text": '{"intent":"offer","sentiment":"positive","scam_flag":false,"scam_reason":"","translation":"Hello","summary":"interest"}', "provider": "groq", "tokens_used": 80}
        mock_cascade = MagicMock()
        mock_cascade.chat = MagicMock(return_value=mock_response)

        a = MessageAnalyzer(cache_db=cache_db, cascade=mock_cascade)

        # First call → llm + cache write
        r1 = a.analyze("Mi interessa la BMW X3")
        assert r1.cached is False
        assert r1.intent == "offer"
        assert mock_cascade.chat.call_count == 1

        # Second call same msg → cache hit, no llm call
        r2 = a.analyze("Mi interessa la BMW X3")
        assert r2.cached is True
        assert r2.intent == "offer"
        assert mock_cascade.chat.call_count == 1  # still 1
        print("  PASS")
    return True


def test_parse_error_fallback() -> bool:
    """LLM output non-JSON → fallback safe (intent='objection' forza HITL)."""
    print("\n=== test_parse_error_fallback ===")
    with tempfile.TemporaryDirectory() as td:
        mock_cascade = MagicMock()
        mock_cascade.chat = MagicMock(return_value={
            "text": "blablabla not json at all",
            "provider": "groq",
            "tokens_used": 50,
        })
        a = MessageAnalyzer(cache_db=Path(td)/"c.sqlite", cascade=mock_cascade)
        r = a.analyze("Mi interessa")
        assert r.intent == "objection", f"expected objection fallback, got {r.intent}"
        assert "parse_error" in r.scam_reason
        print(f"  fallback: intent={r.intent}, scam_reason={r.scam_reason}")
        print("  PASS")
    return True


# ── Live integration test (opzionale, gated on GROQ_API_KEY) ────────────────

def test_live_groq() -> bool:
    """Test reale via Groq se GROQ_API_KEY configurata (.env ARGOS)."""
    print("\n=== test_live_groq ===")
    if not os.environ.get("GROQ_API_KEY"):
        # Try load from .env
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GROQ_API_KEY="):
                    os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip()
                    break

    if not os.environ.get("GROQ_API_KEY"):
        print("  SKIP (no GROQ_API_KEY)")
        return True

    with tempfile.TemporaryDirectory() as td:
        a = MessageAnalyzer(cache_db=Path(td)/"live.sqlite")
        msgs = [
            ("Mi interessa la BMW X3 2020 sotto 35k. Mi manda dossier?", "it", "en", "offer"),
            ("Faccio bonifico in anticipo via Western Union, urgente!", "it", "en", "scam"),
            ("Hello, vehicle still available?", "en", "it", "offer"),
        ]
        for body, src, tgt, expected_intent_class in msgs:
            r = a.analyze(body, source_lang=src, target_lang=tgt)
            print(f"  msg: {body[:60]}...")
            print(f"    intent={r.intent} sentiment={r.sentiment} scam={r.scam_flag} provider={r.provider} tokens={r.tokens_used}")
            print(f"    translation: {r.translation[:80]}")
            assert r.intent in INTENTS
            assert r.sentiment in SENTIMENTS
        print("  PASS (live)")
    return True


def main() -> int:
    tests = [
        test_parse_plain_json,
        test_parse_markdown_wrapped,
        test_parse_with_preamble,
        test_normalize_unknown_intent,
        test_normalize_missing_fields,
        test_msg_hash_deterministic,
        test_cache_roundtrip,
        test_parse_error_fallback,
        test_live_groq,
    ]
    results = []
    for t in tests:
        try:
            ok = t()
            results.append((t.__name__, ok))
        except AssertionError as e:
            print(f"  FAIL: {e}")
            results.append((t.__name__, False))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  ERROR: {type(e).__name__}: {e}")
            results.append((t.__name__, False))

    print("\n=== SUMMARY ===")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
