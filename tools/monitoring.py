#!/usr/bin/env python3
"""
monitoring.py — ARGOS™ System Health Monitor
Runs every 5 minutes via cron on iMac.
Checks: WA daemon, DB integrity, LLM health.
Sends Telegram alert ONLY on failure.

Cron entry (iMac):
  */5 * * * * cd /Users/gianlucadistasi/Documents/combaretrovamiauto-enterprise && \
    /usr/bin/python3 tools/monitoring.py >> /tmp/argos-monitoring.log 2>&1
"""

import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import zoneinfo
from datetime import datetime

# ── Config ────────────────────────────────────────────────────
TIMEZONE         = zoneinfo.ZoneInfo('Europe/Rome')
TELEGRAM_TOKEN   = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
WA_DAEMON_URL    = os.environ.get('WA_DAEMON_URL', 'http://localhost:9191/status')
ARGOS_API_KEY    = os.environ.get('ARGOS_API_KEY', '')
DB_PATH          = os.environ.get('ARGOS_DB_PATH',
    os.path.expanduser(
        '~/Documents/combaretrovamiauto-enterprise/dealer_network.sqlite'
    ))
OPENROUTER_KEY   = os.environ.get('OPENROUTER_API_KEY', '')
GOOGLE_AI_KEY    = os.environ.get('GOOGLE_AI_API_KEY', '')
GROQ_KEY         = os.environ.get('GROQ_API_KEY', '')
CHECK_TIMEOUT    = 5  # seconds


# ── Helpers ───────────────────────────────────────────────────
def now_it() -> str:
    return datetime.now(TIMEZONE).strftime('%d/%m/%Y %H:%M:%S')


def log(msg: str):
    print(f'[{now_it()}] {msg}', flush=True)


def tg_send(text: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    if not TELEGRAM_TOKEN:
        log(f'[TG] No token — would send: {text[:80]}')
        return False
    payload = urllib.parse.urlencode({
        'chat_id':    TELEGRAM_CHAT_ID,
        'text':       text,
        'parse_mode': 'Markdown',
    }).encode()
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    try:
        req  = urllib.request.Request(url, data=payload, method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result.get('ok', False)
    except Exception as e:
        log(f'[TG] Send failed: {e}')
        return False


# ── Check 1: WA Daemon ────────────────────────────────────────
def check_wa_daemon() -> tuple[bool, str]:
    """
    GET /status → check wa_status == 'connected'.
    /status is exempt from API key auth per security.md.
    """
    try:
        req  = urllib.request.Request(WA_DAEMON_URL, method='GET')
        resp = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
        data = json.loads(resp.read())
        wa_status = data.get('wa_status', data.get('status', ''))
        if wa_status == 'connected':
            return True, f'WA connected (daily_sent={data.get("daily_sent", "?")})'
        return False, f'WA status={wa_status!r} (expected "connected")'
    except urllib.error.URLError as e:
        return False, f'WA daemon unreachable: {e.reason}'
    except Exception as e:
        return False, f'WA check error: {e}'


# ── Check 2: DB Integrity ─────────────────────────────────────
def check_db_integrity() -> tuple[bool, str]:
    """
    Run PRAGMA integrity_check and PRAGMA wal_checkpoint(PASSIVE).
    Returns ok only if integrity_check returns 'ok'.
    """
    db_path = os.path.expanduser(DB_PATH)
    if not os.path.exists(db_path):
        return False, f'DB not found: {db_path}'
    try:
        con = sqlite3.connect(db_path, timeout=CHECK_TIMEOUT)
        con.execute('PRAGMA busy_timeout=5000')

        # WAL checkpoint (every run, non-blocking)
        con.execute('PRAGMA wal_checkpoint(PASSIVE)')

        # Integrity check
        rows = con.execute('PRAGMA integrity_check').fetchall()
        con.close()

        result = rows[0][0] if rows else 'no result'
        if result == 'ok':
            return True, 'DB integrity OK + WAL checkpoint done'
        return False, f'DB integrity FAILED: {result}'
    except Exception as e:
        return False, f'DB check error: {e}'


# ── Check 3: LLM Health ───────────────────────────────────────
def _try_openrouter() -> tuple[bool, str]:
    if not OPENROUTER_KEY:
        return False, 'no key'
    payload = json.dumps({
        'model':      'google/gemini-flash-1.5-8b',
        'messages':   [{'role': 'user', 'content': 'ping'}],
        'max_tokens': 1,
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {OPENROUTER_KEY}',
            'Content-Type':  'application/json',
        },
        method='POST',
    )
    resp = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
    data = json.loads(resp.read())
    if 'choices' in data:
        return True, 'OpenRouter OK'
    return False, f'OpenRouter unexpected response: {list(data.keys())}'


def _try_gemini() -> tuple[bool, str]:
    if not GOOGLE_AI_KEY:
        return False, 'no key'
    url     = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'gemini-2.0-flash:generateContent?key={GOOGLE_AI_KEY}'
    )
    payload = json.dumps({
        'contents':         [{'parts': [{'text': 'ping'}]}],
        'generationConfig': {'maxOutputTokens': 1},
    }).encode()
    req  = urllib.request.Request(
        url, data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    resp = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
    data = json.loads(resp.read())
    if 'candidates' in data:
        return True, 'Gemini OK'
    return False, f'Gemini unexpected response: {list(data.keys())}'


def _try_groq() -> tuple[bool, str]:
    if not GROQ_KEY:
        return False, 'no key'
    payload = json.dumps({
        'model':      'llama3-8b-8192',
        'messages':   [{'role': 'user', 'content': 'ping'}],
        'max_tokens': 1,
    }).encode()
    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {GROQ_KEY}',
            'Content-Type':  'application/json',
        },
        method='POST',
    )
    resp = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
    data = json.loads(resp.read())
    if 'choices' in data:
        return True, 'Groq OK'
    return False, f'Groq unexpected response: {list(data.keys())}'


def check_llm_health() -> tuple[bool, str]:
    """
    Try LLM providers in cascade order: Gemini → OpenRouter → Groq.
    Returns ok if at least one responds successfully.
    """
    providers = [
        ('Gemini',      _try_gemini),
        ('OpenRouter',  _try_openrouter),
        ('Groq',        _try_groq),
    ]
    errors = []
    for name, fn in providers:
        try:
            ok, detail = fn()
            if ok:
                return True, detail
            errors.append(f'{name}: {detail}')
        except Exception as e:
            errors.append(f'{name}: {e}')

    return False, 'All LLM providers failed — ' + ' | '.join(errors)


# ── Main ──────────────────────────────────────────────────────
def run_checks() -> list[dict]:
    checks = [
        ('WA Daemon',     check_wa_daemon),
        ('DB Integrity',  check_db_integrity),
        ('LLM Health',    check_llm_health),
    ]
    results = []
    for name, fn in checks:
        t0 = time.monotonic()
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f'Unexpected error: {e}'
        elapsed = time.monotonic() - t0
        status  = 'OK' if ok else 'FAIL'
        log(f'[{status}] {name}: {detail} ({elapsed:.1f}s)')
        results.append({'name': name, 'ok': ok, 'detail': detail})
    return results


def build_alert(failures: list[dict]) -> str:
    ts    = now_it()
    lines = [f'*ARGOS ALERT* — {ts}', '']
    for f in failures:
        lines.append(f'FAIL {f["name"]}')
        lines.append(f'  `{f["detail"]}`')
    lines.append('')
    lines.append('_Check /tmp/argos-monitoring.log per dettagli._')
    return '\n'.join(lines)


def main():
    test_mode = '--test' in sys.argv

    if test_mode:
        msg = f'*ARGOS Monitoring TEST* — {now_it()}\nSistema di monitoring attivo.'
        log(f'[TEST] Sending test alert to Telegram...')
        ok = tg_send(msg)
        log(f'[TEST] Telegram send: {"OK" if ok else "FAILED"}')
        sys.exit(0 if ok else 1)

    log('--- ARGOS monitoring run start ---')
    results  = run_checks()
    failures = [r for r in results if not r['ok']]

    if failures:
        alert = build_alert(failures)
        log(f'[ALERT] {len(failures)} check(s) failed — sending Telegram alert')
        sent = tg_send(alert)
        log(f'[ALERT] Telegram: {"sent" if sent else "FAILED to send"}')
    else:
        log('[OK] All checks passed — no alert sent')

    log('--- ARGOS monitoring run end ---')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
