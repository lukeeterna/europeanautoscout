#!/usr/bin/env python3
"""
scheduler.py — ARGOS™ Deadline Monitor
CoVe 2026 | Enterprise Grade | Eseguito ogni 5 min da LaunchAgent

RESPONSABILITÀ:
  - Calcola SEMPRE ora IT corrente, business hours, giorno settimana
  - Monitora scadenze Day 7 / Day 12 per ogni dealer attivo
  - Invia alert proattivi a Telegram PRIMA che una scadenza si avvicini
  - NON invia mai messaggi WA — solo allerte. L'invio richiede approvazione umana.
  - Rileva "silenzio anomalo" (risposta attesa ma non arrivata)

INSTALLAZIONE: vedi deploy.sh → LaunchAgent che lo esegue ogni 5 min
LOG: /tmp/argos-scheduler.log
"""

import duckdb
import json
import os
import sys
import urllib.request
import urllib.parse
import zoneinfo
from datetime import datetime, timedelta

# ── Config ─────────────────────────────────────────────────
TIMEZONE           = zoneinfo.ZoneInfo('Europe/Rome')
DB_PATH            = os.environ.get('ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.duckdb'))
TELEGRAM_TOKEN     = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
LOG_FILE           = '/tmp/argos-scheduler.log'
STATE_FILE         = '/tmp/argos-scheduler-state.json'   # evita alert duplicati

# Soglie alert (ore prima della scadenza)
WARN_HOURS         = 24    # primo avviso: 24h prima
CRITICAL_HOURS     = 2     # avviso critico: 2h prima
OVERDUE_GRACE_HOURS = 1    # tolleranza dopo scadenza prima di "OVERDUE" alert

# Mappa step → giorni al prossimo step (calendario)
SEQUENCE_MAP = {
    'WA_DAY1_SENT':    {'next': 'EMAIL_DAY7',        'days': 7},
    'EMAIL_DAY7_SENT': {'next': 'WA_DAY12',          'days': 5},
    'WA_DAY12_SENT':   {'next': 'CLOSED_TIMEOUT',    'days': 7},
}

BUSINESS_START = 9
BUSINESS_END   = 18


def now_it() -> datetime:
    return datetime.now(TIMEZONE)


def fmt(dt) -> str:
    if dt is None:
        return 'N/A'
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(TIMEZONE).strftime('%a %d/%m %H:%M')


def log(msg: str):
    ts    = now_it().strftime('%d/%m/%Y %H:%M:%S')
    line  = f'[{ts}] {msg}'
    print(line, file=sys.stdout)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def is_business_hours() -> bool:
    now = now_it()
    dow = now.weekday()          # 0=lun, 6=dom
    if dow >= 5:
        return False
    return BUSINESS_START <= now.hour < BUSINESS_END


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception:
        pass


def load_active_dealers():
    """Carica dealer con sequenza in corso da DuckDB."""
    try:
        con = duckdb.connect(DB_PATH)
        rows = con.execute("""
            SELECT dealer_id, dealer_name, persona_type,
                   current_step, last_contact_at, recommendation
            FROM conversations
            WHERE current_step NOT IN (
                'CLOSED_NO', 'CLOSED_YES', 'CLOSED_TIMEOUT', 'HUMAN_NEEDED'
            )
            AND current_step IS NOT NULL
            ORDER BY last_contact_at ASC
        """).fetchall()
        cols = [d[0] for d in con.description]
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        log(f'ERROR load_active_dealers: {e}')
        return []


def calculate_deadline(last_contact_at, current_step) -> dict:
    """Calcola scadenza prossimo step e urgency."""
    if last_contact_at is None or current_step not in SEQUENCE_MAP:
        return None

    if isinstance(last_contact_at, str):
        last_contact_at = datetime.fromisoformat(last_contact_at)
    if last_contact_at.tzinfo is None:
        last_contact_at = last_contact_at.replace(tzinfo=TIMEZONE)

    mapping  = SEQUENCE_MAP[current_step]
    deadline = last_contact_at + timedelta(days=mapping['days'])
    now      = now_it()
    delta_h  = (deadline - now).total_seconds() / 3600

    if delta_h < -OVERDUE_GRACE_HOURS:
        urgency = 'OVERDUE'
    elif delta_h <= CRITICAL_HOURS:
        urgency = 'CRITICAL'
    elif delta_h <= WARN_HOURS:
        urgency = 'WARNING'
    else:
        urgency = 'OK'

    return {
        'next_step':   mapping['next'],
        'deadline':    deadline,
        'deadline_fmt': fmt(deadline),
        'hours_until': round(delta_h, 1),
        'urgency':     urgency,
    }


def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN:
        log(f'[TELEGRAM SKIPPED — no token]\n{text}')
        return False
    try:
        payload = urllib.parse.urlencode({
            'chat_id':    TELEGRAM_CHAT_ID,
            'text':       text,
            'parse_mode': 'Markdown',
        }).encode()
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        req = urllib.request.Request(url, data=payload, method='POST')
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        log(f'Telegram error: {e}')
        return False


def alert_key(dealer_id: str, urgency: str, step: str) -> str:
    """Chiave univoca per evitare alert duplicati nello stesso giorno."""
    day = now_it().strftime('%Y-%m-%d')
    return f'{dealer_id}_{step}_{urgency}_{day}'


def run():
    now  = now_it()
    log('━━━ Scheduler run ━━━')
    log(f'Ora IT: {now.strftime("%a %d/%m/%Y %H:%M")} | '
        f'Business hours: {"SÌ" if is_business_hours() else "NO"}')

    state   = load_state()
    dealers = load_active_dealers()
    log(f'Dealer attivi in pipeline: {len(dealers)}')

    alerts_sent = 0

    for d in dealers:
        dealer_id   = d['dealer_id']
        dealer_name = d['dealer_name']
        persona     = d.get('persona_type', '?')
        step        = d.get('current_step', '')
        last        = d.get('last_contact_at')

        info = calculate_deadline(last, step)
        if info is None:
            continue

        urgency = info['urgency']
        key     = alert_key(dealer_id, urgency, step)

        if urgency == 'OK':
            log(f'  {dealer_name}: {step} → {info["next_step"]} '
                f'tra {info["hours_until"]}h [{info["deadline_fmt"]}] ✓')
            continue

        # Evita alert duplicati nella stessa finestra
        if state.get(key):
            log(f'  {dealer_name}: alert già inviato [{urgency}] — skip')
            continue

        # Costruisci messaggio alert
        emoji = {'OVERDUE': '🚨', 'CRITICAL': '⚠️', 'WARNING': '🔔'}.get(urgency, 'ℹ️')
        bh_note = '' if is_business_hours() else '\n⚠️ _Fuori orario business — considera se inviare ora_'

        if urgency == 'OVERDUE':
            headline = f'{emoji} *SCADUTO* — azione richiesta ADESSO'
            detail   = f'Step `{step}` scaduto {abs(info["hours_until"]):.0f}h fa'
        elif urgency == 'CRITICAL':
            headline = f'{emoji} *CRITICO* — scade tra {info["hours_until"]}h'
            detail   = f'Step `{step}` → `{info["next_step"]}` entro {info["deadline_fmt"]}'
        else:
            headline = f'{emoji} *AVVISO* — scade tra {info["hours_until"]:.0f}h'
            detail   = f'Step `{step}` → `{info["next_step"]}` entro {info["deadline_fmt"]}'

        text = '\n'.join([
            f'📅 {now.strftime("%a %d/%m/%Y %H:%M")}',
            '',
            headline,
            '',
            f'👤 *{dealer_name}* (archetipo: {persona})',
            detail,
            f'Ultimo contatto: {fmt(last)}',
            bh_note,
            '',
            '→ Approva invio: `/fire {dealer_id} {info["next_step"]}`',
            '→ Posticipa 1g: `/delay {dealer_id} 1`',
            '→ Chiudi: `/close {dealer_id}`',
        ])

        if send_telegram(text):
            state[key] = now.isoformat()
            log(f'  ✅ Alert inviato: {dealer_name} [{urgency}]')
            alerts_sent += 1
        else:
            log(f'  ❌ Alert fallito: {dealer_name}')

    save_state(state)
    log(f'Fine run. Alert inviati: {alerts_sent}')

    # Daily digest in orario business (solo alle 9:00 ±10min)
    if is_business_hours() and now.hour == 9 and now.minute < 10:
        send_daily_digest(dealers, now)


def send_daily_digest(dealers: list, now: datetime):
    """Digest mattutino con il quadro completo del pipeline."""
    digest_key = f'digest_{now.strftime("%Y-%m-%d")}'
    state = load_state()
    if state.get(digest_key):
        return

    lines = [
        f'☀️ *ARGOS™ MORNING DIGEST — {now.strftime("%a %d/%m/%Y")}*',
        f'📊 Pipeline attivo: {len(dealers)} dealer',
        '',
    ]

    for d in dealers:
        info = calculate_deadline(d.get('last_contact_at'), d.get('current_step', ''))
        emoji = {'OVERDUE': '🚨', 'CRITICAL': '⚠️', 'WARNING': '🔔', 'OK': '✅'}.get(
            info['urgency'] if info else 'OK', 'ℹ️')
        next_info = f'→ {info["next_step"]} tra {info["hours_until"]}h' if info else '→ check manuale'
        lines.append(f'{emoji} *{d["dealer_name"]}* ({d.get("persona_type","?")}) | '
                     f'{d.get("current_step","?")} {next_info}')

    lines += ['', f'Business hours IT: {BUSINESS_START}:00-{BUSINESS_END}:00']

    state[digest_key] = now.isoformat()
    save_state(state)
    send_telegram('\n'.join(lines))
    log('Daily digest inviato')


if __name__ == '__main__':
    run()
