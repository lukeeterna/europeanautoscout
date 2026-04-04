#!/usr/bin/env python3
"""
llm_cascade.py — ARGOS™ LLM Cascade Engine
CoVe 2026 | 5-level fallback with circuit breaker

Levels (all FREE):
  1. Gemini Flash       — gemini-2.0-flash          — 250 req/day
  2. Groq               — llama-3.3-70b-versatile    — 1000 req/day
  3. OpenRouter free    — llama-3.3-70b-instruct     — 1000 req/day
  4. Gemini Lite        — gemini-2.0-flash-lite       — 1000 req/day
  5. Ollama locale      — llama3.2:8b                — unlimited

Usage:
    from src.llm_cascade import LLMCascade
    cascade = LLMCascade()
    result = cascade.chat(system_prompt="...", user_message="...", max_tokens=200)
    # {"text": "...", "provider": "gemini-flash", "tokens_used": 150}
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Env loader ────────────────────────────────────────────────────────────────
def _load_dotenv(path: Optional[str] = None):
    """Load .env from project root into os.environ (does not overwrite)."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ.setdefault(key.strip(), val.strip())

_load_dotenv()


# ── Custom exceptions ─────────────────────────────────────────────────────────
class AllProvidersDown(Exception):
    """Raised when all 5 cascade levels have failed or are circuit-broken."""
    pass


class ProviderError(Exception):
    """A single provider call failed (non-fatal — cascade continues)."""
    def __init__(self, provider: str, reason: str):
        super().__init__(f"[{provider}] {reason}")
        self.provider = provider
        self.reason = reason


# ── Circuit breaker ───────────────────────────────────────────────────────────
class CircuitBreaker:
    """
    Per-provider circuit breaker.
    State: CLOSED (normal) → OPEN (skip) → HALF-OPEN (retry after cool-down).

    Rules:
      - 3 failures within 5 minutes  → OPEN for 10 minutes
      - After 10 minutes             → HALF-OPEN (allow 1 probe call)
      - Probe succeeds               → CLOSED
      - Probe fails                  → OPEN for another 10 minutes
    """
    FAIL_WINDOW    = 300   # 5 min  — window to count failures
    FAIL_THRESHOLD = 3     # failures before opening
    OPEN_DURATION  = 600   # 10 min — how long to stay open

    def __init__(self, name: str):
        self.name = name
        self._lock = threading.Lock()
        self._failures: list[float] = []   # timestamps of recent failures
        self._opened_at: Optional[float] = None

    # ── Public helpers ────────────────────────────────────────────────────────
    def is_open(self) -> bool:
        with self._lock:
            return self._check_open()

    def record_success(self):
        with self._lock:
            was_open = self._opened_at is not None
            self._failures.clear()
            self._opened_at = None
            if was_open:
                logger.info(f"[circuit] {self.name} CLOSED (probe succeeded)")

    def record_failure(self):
        with self._lock:
            now = time.time()
            # Prune old failures outside the window
            self._failures = [t for t in self._failures if now - t < self.FAIL_WINDOW]
            self._failures.append(now)

            if len(self._failures) >= self.FAIL_THRESHOLD and self._opened_at is None:
                self._opened_at = now
                opens_until = datetime.fromtimestamp(now + self.OPEN_DURATION).strftime('%H:%M:%S')
                logger.warning(
                    f"[circuit] {self.name} OPENED "
                    f"({self.FAIL_THRESHOLD} failures in {self.FAIL_WINDOW}s) "
                    f"— skipping until {opens_until}"
                )

    def status(self) -> dict:
        with self._lock:
            now = time.time()
            if self._opened_at is None:
                state = 'CLOSED'
                retry_in = None
            elif now - self._opened_at >= self.OPEN_DURATION:
                state = 'HALF-OPEN'
                retry_in = 0
            else:
                state = 'OPEN'
                retry_in = int(self.OPEN_DURATION - (now - self._opened_at))
            return {
                'state': state,
                'recent_failures': len(self._failures),
                'retry_in_seconds': retry_in,
            }

    # ── Private ───────────────────────────────────────────────────────────────
    def _check_open(self) -> bool:
        if self._opened_at is None:
            return False
        elapsed = time.time() - self._opened_at
        if elapsed >= self.OPEN_DURATION:
            # Transition to HALF-OPEN — allow one probe (we don't block here)
            return False
        return True


# ── Provider definitions ──────────────────────────────────────────────────────
# Each provider is a dict consumed by _call_provider().
# 'type' controls which API format to use: 'gemini' | 'openai' | 'ollama'

def _build_providers() -> list[dict]:
    gemini_key  = os.environ.get('GOOGLE_AI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
    groq_key    = os.environ.get('GROQ_API_KEY', '')
    openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')

    return [
        {
            'id':    'gemini-flash',
            'type':  'gemini',
            'key':   gemini_key,
            'model': 'gemini-2.0-flash',
            'url':   'https://generativelanguage.googleapis.com/v1beta/models',
        },
        {
            'id':    'groq',
            'type':  'openai',
            'key':   groq_key,
            'model': 'llama-3.3-70b-versatile',
            'url':   'https://api.groq.com/openai/v1/chat/completions',
        },
        {
            'id':    'openrouter',
            'type':  'openai',
            'key':   openrouter_key,
            'model': 'meta-llama/llama-3.3-70b-instruct:free',
            'url':   'https://openrouter.ai/api/v1/chat/completions',
            'extra_headers': {
                'HTTP-Referer': 'https://argos-automotive.pages.dev',
                'X-Title':      'ARGOS Automotive',
            },
        },
        {
            'id':    'gemini-lite',
            'type':  'gemini',
            'key':   gemini_key,
            'model': 'gemini-2.0-flash-lite',
            'url':   'https://generativelanguage.googleapis.com/v1beta/models',
        },
        {
            'id':    'ollama',
            'type':  'ollama',
            'key':   '',
            'model': 'qwen2.5:3b',
            'url':   'http://localhost:11434/api/chat',
        },
    ]


# ── Low-level HTTP callers ────────────────────────────────────────────────────

TIMEOUT = 15       # seconds per cloud request
OLLAMA_TIMEOUT = 120  # seconds for Ollama (Intel iMac cold start is very slow)


def _call_gemini(provider: dict, system_prompt: str, user_message: str,
                 max_tokens: int) -> dict:
    """Call Google Gemini API (not OpenAI-compatible)."""
    if not provider['key']:
        raise ProviderError(provider['id'], 'GOOGLE_AI_API_KEY not set')

    url = f"{provider['url']}/{provider['model']}:generateContent?key={provider['key']}"
    payload = {
        'systemInstruction': {
            'parts': [{'text': system_prompt}]
        },
        'contents': [
            {'role': 'user', 'parts': [{'text': user_message}]}
        ],
        'generationConfig': {
            'maxOutputTokens': max_tokens,
            'temperature': 0.7,
        },
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise ProviderError(provider['id'], f'HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    try:
        text = data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError) as e:
        raise ProviderError(provider['id'], f'Unexpected response shape: {e}')

    usage = data.get('usageMetadata', {})
    tokens = usage.get('totalTokenCount', 0)
    return {'text': text, 'provider': provider['id'], 'tokens_used': tokens}


def _call_openai_compat(provider: dict, system_prompt: str, user_message: str,
                        max_tokens: int) -> dict:
    """Call any OpenAI-compatible endpoint (Groq, OpenRouter, etc.)."""
    if not provider['key']:
        raise ProviderError(provider['id'], f'API key not set ({provider["id"].upper()}_API_KEY)')

    headers = {
        'Authorization': f'Bearer {provider["key"]}',
        'Content-Type':  'application/json',
    }
    headers.update(provider.get('extra_headers', {}))

    payload = {
        'model':       provider['model'],
        'messages':    [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_message},
        ],
        'max_tokens':  max_tokens,
        'temperature': 0.7,
    }
    resp = requests.post(provider['url'], json=payload, headers=headers, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise ProviderError(provider['id'], f'HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    try:
        text = data['choices'][0]['message']['content']
    except (KeyError, IndexError) as e:
        raise ProviderError(provider['id'], f'Unexpected response shape: {e}')

    usage = data.get('usage', {})
    tokens = usage.get('total_tokens', 0)
    return {'text': text, 'provider': provider['id'], 'tokens_used': tokens}


def _call_ollama(provider: dict, system_prompt: str, user_message: str,
                 max_tokens: int) -> dict:
    """Call local Ollama instance."""
    payload = {
        'model':    provider['model'],
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_message},
        ],
        'stream':  False,
        'options': {'num_predict': max_tokens},
    }
    try:
        resp = requests.post(provider['url'], json=payload, timeout=OLLAMA_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise ProviderError(provider['id'], 'Ollama not running on localhost:11434')

    if resp.status_code != 200:
        raise ProviderError(provider['id'], f'HTTP {resp.status_code}: {resp.text[:200]}')

    data = resp.json()
    try:
        text = data['message']['content']
    except (KeyError, TypeError) as e:
        raise ProviderError(provider['id'], f'Unexpected response shape: {e}')

    tokens = data.get('eval_count', 0) + data.get('prompt_eval_count', 0)
    return {'text': text, 'provider': provider['id'], 'tokens_used': tokens}


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _call_provider(provider: dict, system_prompt: str, user_message: str,
                   max_tokens: int) -> dict:
    """Route to the right caller based on provider type."""
    ptype = provider['type']
    if ptype == 'gemini':
        return _call_gemini(provider, system_prompt, user_message, max_tokens)
    elif ptype == 'openai':
        return _call_openai_compat(provider, system_prompt, user_message, max_tokens)
    elif ptype == 'ollama':
        return _call_ollama(provider, system_prompt, user_message, max_tokens)
    else:
        raise ProviderError(provider['id'], f'Unknown provider type: {ptype}')


# ── Main cascade class ────────────────────────────────────────────────────────

class LLMCascade:
    """
    5-level LLM cascade with per-provider circuit breakers.
    Thread-safe. Uses only `requests` (no AI SDKs).
    """

    def __init__(self):
        self._providers = _build_providers()
        self._breakers: dict[str, CircuitBreaker] = {
            p['id']: CircuitBreaker(p['id']) for p in self._providers
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(self, system_prompt: str, user_message: str,
             max_tokens: int = 200) -> dict:
        """
        Try each provider in cascade order.
        Returns: {"text": str, "provider": str, "tokens_used": int}
        Raises: AllProvidersDown if every level fails or is circuit-broken.
        """
        last_error = None
        for provider in self._providers:
            pid = provider['id']
            breaker = self._breakers[pid]

            if breaker.is_open():
                logger.debug(f"[cascade] skipping {pid} — circuit OPEN")
                continue

            try:
                logger.debug(f"[cascade] trying {pid}")
                result = _call_provider(provider, system_prompt, user_message, max_tokens)
                breaker.record_success()
                logger.info(f"[cascade] success via {pid} ({result.get('tokens_used', 0)} tokens)")
                return result

            except ProviderError as e:
                logger.warning(f"[cascade] {e}")
                breaker.record_failure()
                last_error = e

            except requests.exceptions.Timeout:
                t = OLLAMA_TIMEOUT if provider['type'] == 'ollama' else TIMEOUT
                msg = f"timeout after {t}s"
                logger.warning(f"[cascade] [{pid}] {msg}")
                breaker.record_failure()
                last_error = ProviderError(pid, msg)

            except requests.exceptions.RequestException as e:
                msg = f"request error: {e}"
                logger.warning(f"[cascade] [{pid}] {msg}")
                breaker.record_failure()
                last_error = ProviderError(pid, msg)

            except Exception as e:
                msg = f"unexpected error: {e}"
                logger.error(f"[cascade] [{pid}] {msg}", exc_info=True)
                breaker.record_failure()
                last_error = ProviderError(pid, msg)

        raise AllProvidersDown(
            f"All 5 LLM providers failed. Last error: {last_error}"
        )

    def health(self) -> dict:
        """
        Return status dict for all providers.
        Does NOT make API calls — reflects circuit breaker state only.
        """
        result = {}
        for provider in self._providers:
            pid = provider['id']
            has_key = bool(provider['key']) or provider['type'] == 'ollama'
            cb = self._breakers[pid].status()
            result[pid] = {
                'key_configured': has_key,
                'circuit': cb,
            }
        return result

    def test_all(self) -> dict:
        """
        Probe each provider with a minimal request. Returns per-provider results.
        Used for diagnostics / Sprint 1 checks.
        Does NOT short-circuit on failure — tests all 5.
        """
        ping_system = "Rispondi con una sola parola: 'ok'."
        ping_user   = "Rispondi con una sola parola: 'ok'."
        results = {}

        for provider in self._providers:
            pid = provider['id']
            start = time.time()
            try:
                r = _call_provider(provider, ping_system, ping_user, max_tokens=10)
                elapsed = round(time.time() - start, 2)
                results[pid] = {
                    'ok':      True,
                    'latency': elapsed,
                    'text':    r.get('text', '')[:80],
                }
                # Reset breaker on successful probe
                self._breakers[pid].record_success()
            except ProviderError as e:
                elapsed = round(time.time() - start, 2)
                results[pid] = {'ok': False, 'latency': elapsed, 'error': e.reason}
                self._breakers[pid].record_failure()
            except Exception as e:
                elapsed = round(time.time() - start, 2)
                results[pid] = {'ok': False, 'latency': elapsed, 'error': str(e)}
                self._breakers[pid].record_failure()

        return results


# ── Module-level singleton ────────────────────────────────────────────────────
_default_cascade: Optional[LLMCascade] = None
_cascade_lock = threading.Lock()


def get_cascade() -> LLMCascade:
    """Return (or create) the module-level singleton LLMCascade."""
    global _default_cascade
    if _default_cascade is None:
        with _cascade_lock:
            if _default_cascade is None:
                _default_cascade = LLMCascade()
    return _default_cascade


# ── CLI diagnostics ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S',
    )

    parser = argparse.ArgumentParser(description='LLMCascade diagnostics')
    parser.add_argument('--health',    action='store_true', help='Show circuit breaker states')
    parser.add_argument('--test-all',  action='store_true', help='Probe all 5 providers')
    parser.add_argument('--chat',      type=str,            help='Send a quick chat message')
    args = parser.parse_args()

    cascade = LLMCascade()

    if args.health:
        h = cascade.health()
        print(json.dumps(h, indent=2))

    if args.test_all:
        print("Probing all providers (may take up to 50s)...")
        results = cascade.test_all()
        for pid, r in results.items():
            status = 'OK' if r['ok'] else 'FAIL'
            latency = r.get('latency', '?')
            detail  = r.get('text', '') if r['ok'] else r.get('error', '')
            print(f"  {status:4s}  {pid:<20s}  {latency}s  {detail[:60]}")

    if args.chat:
        try:
            result = cascade.chat(
                system_prompt="Sei Luca Ferretti, broker auto premium Italia.",
                user_message=args.chat,
                max_tokens=150,
            )
            print(f"\nProvider: {result['provider']} ({result['tokens_used']} tokens)")
            print(f"Response: {result['text']}")
        except AllProvidersDown as e:
            print(f"ERROR: {e}")
