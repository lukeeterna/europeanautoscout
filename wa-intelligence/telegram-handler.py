#!/usr/bin/env python3
"""
telegram-handler.py — ARGOS™ Human-in-Loop Telegram Bot
CoVe 2026 | Enterprise Grade | PM2 Managed

RESPONSABILITÀ:
  - Riceve comandi da Luke via Telegram
  - /approva <reply_id>       → schedula invio WA (anti-ban sleep)
  - /modifica <reply_id> testo → sostituisce testo e schedula
  - /rifiuta <reply_id>       → chiude senza inviare, log
  - /fire <dealer_id> <step>  → forza invio prossimo step
  - /delay <dealer_id> <gg>   → posticipa scadenza
  - /close <dealer_id>        → chiude dealer (CLOSED_NO)
  - /status                   → quadro pipeline completo
  - /human                    → flag HUMAN_NEEDED sul dealer
  - alert <text> <markup>     → modalità CLI (chiamata da wa-daemon)

  In modalità DAEMON: polling Telegram ogni 3 secondi.
  In modalità CLI: invia alert singolo e termina.

AVVIO daemon: pm2 start telegram-handler.py --name argos-tg-bot --interpreter python3
"""

import duckdb
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import zoneinfo
from datetime import datetime

TIMEZONE         = zoneinfo.ZoneInfo('Europe/Rome')
TELEGRAM_TOKEN   = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
DB_PATH          = os.environ.get('ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.duckdb'))
WA_SENDER        = os.path.expanduser(
    '~/Documents/app-antigravity-auto/wa-sender/send_message.js')
WA_CLIENT_ID     = os.environ.get('WA_CLIENT_ID', 'argos-business')
LOG_FILE         = '/tmp/argos-tg-handler.log'
POLL_OFFSET_FILE = '/tmp/argos-tg-offset.txt'

# Anti-ban sleep range (secondi)
SLEEP_MIN, SLEEP_MAX = 90, 720


# ── Utility ──────────────────────────────────────────────────
def now_it() -> str:
    return datetime.now(TIMEZONE).strftime('%d/%m/%Y %H:%M:%S')


def log(msg: str):
    line = f'[{now_it()}] {msg}'
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def tg_post(method: str, payload: dict) -> dict:
    if not TELEGRAM_TOKEN:
        log(f'[NO TOKEN] {method}: {payload}')
        return {}
    data = urllib.parse.urlencode(payload).encode()
    url  = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}'
    try:
        req  = urllib.request.Request(url, data=data, method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        log(f'TG error [{method}]: {e}')
        return {}


def send(text: str, chat_id: str = TELEGRAM_CHAT_ID):
    return tg_post('sendMessage', {
        'chat_id':    chat_id,
        'text':       text,
        'parse_mode': 'Markdown',
    })


def db_query(sql: str, params: list = None) -> list:
    try:
        con  = duckdb.connect(DB_PATH)
        rows = con.execute(sql, params or []).fetchall()
        cols = [d[0] for d in con.description] if con.description else []
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        log(f'db_query error: {e}')
        return []


def db_exec(sql: str, params: list = None):
    try:
        con = duckdb.connect(DB_PATH)
        con.execute(sql, params or [])
        con.commit()
        con.close()
        return True
    except Exception as e:
        log(f'db_exec error: {e}')
        return False


# ── Comandi ──────────────────────────────────────────────────
def cmd_approva(reply_id: str) -> str:
    rows = db_query('SELECT * FROM pending_replies WHERE id = ?', [reply_id])
    if not rows:
        return f'❌ Reply ID non trovato: `{reply_id}`'

    r = rows[0]
    if r.get('approved') is True:
        return f'⚠️ Reply `{reply_id}` già approvata.'
    if r.get('sent') is True:
        return f'⚠️ Reply `{reply_id}` già inviata.'

    # Carica numero telefono dal dealer
    dealers = db_query(
        'SELECT phone_number FROM conversations WHERE dealer_id = ?',
        [r['dealer_id']]
    )
    if not dealers or not dealers[0].get('phone_number'):
        return f'❌ Numero telefono non trovato per dealer `{r["dealer_id"]}`'

    phone = dealers[0]['phone_number'].replace('@c.us', '').replace('+', '').replace(' ', '')
    wa_id = f'{phone}@c.us'

    # Schedula invio con anti-ban sleep
    sleep_s = random.randint(SLEEP_MIN, SLEEP_MAX)
    log(f'Approvata reply {reply_id} — sleep {sleep_s}s prima dell\'invio')

    db_exec(
        'UPDATE pending_replies SET approved = TRUE WHERE id = ?',
        [reply_id]
    )

    # Avvia invio in background (non blocca)
    env = os.environ.copy()
    env['CLIENT_ID'] = WA_CLIENT_ID
    subprocess.Popen(
        ['bash', '-c',
         f'sleep {sleep_s} && node {WA_SENDER} "{wa_id}" "{r["reply_text"].replace(chr(34), chr(39))}" '
         f'&& python3 -c "import duckdb; con=duckdb.connect(\'{DB_PATH}\'); '
         f'con.execute(\'UPDATE pending_replies SET sent=TRUE WHERE id=\\\'\\\'\\\'%s\\\'\\\'\\\'\'); '
         f'con.commit()"' % reply_id],
        env=env, close_fds=True
    )

    return (
        f'✅ *Reply approvata* — invio tra ~{sleep_s//60}min\n'
        f'👤 A: {r["dealer_name"]}\n'
        f'💬 _{r["reply_text"][:200]}_'
    )


def cmd_modifica(reply_id: str, new_text: str) -> str:
    rows = db_query('SELECT * FROM pending_replies WHERE id = ?', [reply_id])
    if not rows:
        return f'❌ Reply ID non trovato: `{reply_id}`'

    db_exec(
        'UPDATE pending_replies SET reply_text = ?, reply_label = ? WHERE id = ?',
        [new_text, 'MANUAL_EDIT', reply_id]
    )
    return (
        f'✏️ *Testo aggiornato* per reply `{reply_id}`\n'
        f'Ora usa `/approva {reply_id}` per inviare.'
    )


def cmd_rifiuta(reply_id: str) -> str:
    db_exec(
        'UPDATE pending_replies SET approved = FALSE WHERE id = ?',
        [reply_id]
    )
    return f'🚫 Reply `{reply_id}` rifiutata. Nessun messaggio inviato.'


def cmd_status() -> str:
    dealers = db_query("""
        SELECT dealer_name, persona_type, current_step,
               last_contact_at, recommendation
        FROM conversations
        WHERE current_step NOT IN ('CLOSED_NO','CLOSED_YES','CLOSED_TIMEOUT')
        ORDER BY last_contact_at ASC
    """)

    pending = db_query("""
        SELECT COUNT(*) as cnt FROM pending_replies
        WHERE approved IS NULL AND sent = FALSE
    """)
    p_count = pending[0]['cnt'] if pending else 0

    now = datetime.now(TIMEZONE)
    bh  = BUSINESS_START <= now.hour < BUSINESS_END and now.weekday() < 5

    lines = [
        f'📊 *ARGOS™ PIPELINE STATUS*',
        f'📅 {now.strftime("%a %d/%m/%Y %H:%M")} IT',
        f'🕐 Business hours: {"✅ SÌ" if bh else "❌ NO"}',
        f'⏳ Risposte in attesa approvazione: {p_count}',
        '',
        f'*Dealer attivi: {len(dealers)}*',
    ]

    for d in dealers:
        lines.append(
            f'• *{d["dealer_name"]}* ({d.get("persona_type","?")}) — '
            f'`{d.get("current_step","?")}` | '
            f'Ultimo: {str(d.get("last_contact_at","?"))[:16]}'
        )

    return '\n'.join(lines)


def cmd_fire(dealer_id: str, step: str) -> str:
    """Notifica che occorre preparare il prossimo step — NON invia da solo."""
    dealers = db_query(
        'SELECT * FROM conversations WHERE dealer_id = ?',
        [dealer_id]
    )
    if not dealers:
        return f'❌ Dealer ID non trovato: `{dealer_id}`'
    d = dealers[0]
    return (
        f'🔔 *Fire richiesto*\n'
        f'👤 {d["dealer_name"]} (archetipo: {d.get("persona_type","?")})\n'
        f'Step da eseguire: `{step}`\n\n'
        f'→ Genera testo con Claude Code\n'
        f'→ Usa `/modifica` per caricare il testo\n'
        f'→ Usa `/approva` per inviare\n'
        f'_Nessun invio automatico — approvazione richiesta._'
    )


def cmd_delay(dealer_id: str, days: str) -> str:
    try:
        days_int = int(days)
    except ValueError:
        return '❌ Giorni non valido. Es: `/delay MARIO_001 1`'

    db_exec("""
        UPDATE conversations
        SET last_contact_at = TIMESTAMPADD('day', ?, last_contact_at)
        WHERE dealer_id = ?
    """, [days_int, dealer_id])

    return f'⏰ Scadenza *posticipata di {days_int} giorno/i* per dealer `{dealer_id}`'


def cmd_close(dealer_id: str) -> str:
    db_exec("""
        UPDATE conversations
        SET current_step = 'CLOSED_NO',
            analyzed_at  = CURRENT_TIMESTAMP
        WHERE dealer_id = ?
    """, [dealer_id])
    return f'🔒 Dealer `{dealer_id}` chiuso con stato `CLOSED_NO`.'


def cmd_human(dealer_id: str) -> str:
    db_exec("""
        UPDATE conversations
        SET current_step = 'HUMAN_NEEDED',
            analyzed_at  = CURRENT_TIMESTAMP
        WHERE dealer_id = ?
    """, [dealer_id])
    return (
        f'🧑 Dealer `{dealer_id}` flaggato come *HUMAN_NEEDED*.\n'
        f'Automatismo sospeso — gestione manuale richiesta.'
    )


def cmd_outreach(dealer_id: str = '') -> str:
    """Mostra dealer PENDING pronti per Day 1, o schedula invio per uno specifico."""
    if not dealer_id:
        # Lista dealer pronti
        rows = db_query("""
            SELECT dealer_id, dealer_name, city, phone_number, persona_type, score
            FROM conversations
            WHERE current_step = 'PENDING'
            ORDER BY score DESC
        """)
        if not rows:
            return '✅ Nessun dealer in stato PENDING.'
        lines = ['*Dealer pronti per Day 1:*', '']
        for r in rows:
            phone = r.get('phone_number', '')
            wa = '✅ WA' if phone.startswith('393') and len(phone) == 12 else '📞'
            lines.append(
                f'• `{r["dealer_id"]}` — *{r["dealer_name"]}* ({r["city"]})\n'
                f'  {wa} | {r["persona_type"]} | {r["score"]}/10\n'
                f'  `/outreach {r["dealer_id"]}`'
            )
        return '\n'.join(lines)

    # Schedula invio Day 1 per dealer specifico
    rows = db_query(
        'SELECT * FROM conversations WHERE dealer_id = ?', [dealer_id]
    )
    if not rows:
        return f'❌ Dealer `{dealer_id}` non trovato'
    d = rows[0]
    if d.get('current_step') != 'PENDING':
        return f'⚠️ Dealer `{dealer_id}` non in stato PENDING (stato: `{d["current_step"]}`)'

    phone = d.get('phone_number', '').replace('+', '').replace(' ', '')
    if not phone.startswith('393') or len(phone) != 12:
        return f'❌ Numero `{phone}` non è WA valido (serve 393XXXXXXXXX)'

    wa_id = f'{phone}@c.us'
    msg = d.get('day1_message', '')
    if not msg:
        return f'❌ Nessun messaggio Day 1 per `{dealer_id}`'

    sleep_s = random.randint(SLEEP_MIN, SLEEP_MAX)

    # Aggiorna stato
    db_exec("""
        UPDATE conversations
        SET current_step = 'DAY1_SENT', last_contact_at = CURRENT_TIMESTAMP
        WHERE dealer_id = ?
    """, [dealer_id])

    # Avvia invio in background
    env = os.environ.copy()
    env['CLIENT_ID'] = WA_CLIENT_ID
    subprocess.Popen(
        ['bash', '-c',
         f'sleep {sleep_s} && node {WA_SENDER} "{wa_id}" '
         f'"{msg.replace(chr(34), chr(39))}"'],
        env=env, close_fds=True
    )

    return (
        f'🚀 *Day 1 schedulato* — invio tra ~{sleep_s // 60}min\n'
        f'👤 {d["dealer_name"]} ({d["city"]})\n'
        f'📱 {phone}\n'
        f'🎭 Archetipo: {d.get("persona_type", "?")}\n'
        f'💬 Variante A (neutro)\n'
        f'_Anti-ban sleep attivo_'
    )


def cmd_pending() -> str:
    rows = db_query("""
        SELECT id, dealer_name, reply_label, reply_text, created_at
        FROM pending_replies
        WHERE approved IS NULL AND sent = FALSE
        ORDER BY created_at ASC
        LIMIT 10
    """)
    if not rows:
        return '✅ Nessuna reply in attesa di approvazione.'
    lines = ['*Reply in attesa:*', '']
    for r in rows:
        lines.append(
            f'• `{r["id"]}` — *{r["dealer_name"]}* `{r["reply_label"]}`\n'
            f'  _{r["reply_text"][:120]}..._\n'
            f'  `/approva {r["id"]}` | `/rifiuta {r["id"]}`'
        )
    return '\n'.join(lines)


# ── Router comandi ───────────────────────────────────────────
HELP_TEXT = """*ARGOS™ Bot — Comandi disponibili*

🚀 *Outreach*
`/outreach` — lista dealer pronti per Day 1
`/outreach <dealer_id>` — invia Day 1 a dealer

📩 *Gestione risposte*
`/pending` — lista risposte in attesa
`/approva <id>` — approva e schedula invio
`/modifica <id> <testo>` — modifica testo risposta
`/rifiuta <id>` — scarta risposta

📊 *Pipeline*
`/status` — quadro pipeline completo
`/fire <dealer_id> <step>` — prepara prossimo step
`/delay <dealer_id> <gg>` — posticipa scadenza
`/close <dealer_id>` — chiudi dealer
`/human <dealer_id>` — flag intervento umano

ℹ️ *Info*
`/help` — questo messaggio
"""

BUSINESS_START = 9
BUSINESS_END   = 18


def dispatch(text: str, chat_id: str):
    parts = text.strip().split(None, 2)
    cmd   = parts[0].lower() if parts else ''
    args  = parts[1:]

    if cmd == '/approva':
        reply = cmd_approva(args[0]) if args else '❌ Usage: `/approva <reply_id>`'
    elif cmd == '/modifica':
        reply = cmd_modifica(args[0], ' '.join(args[1:])) if len(args) >= 2 else '❌ Usage: `/modifica <id> <testo>`'
    elif cmd == '/rifiuta':
        reply = cmd_rifiuta(args[0]) if args else '❌ Usage: `/rifiuta <reply_id>`'
    elif cmd == '/status':
        reply = cmd_status()
    elif cmd == '/fire':
        reply = cmd_fire(args[0], args[1]) if len(args) >= 2 else '❌ Usage: `/fire <dealer_id> <step>`'
    elif cmd == '/delay':
        reply = cmd_delay(args[0], args[1]) if len(args) >= 2 else '❌ Usage: `/delay <dealer_id> <gg>`'
    elif cmd == '/close':
        reply = cmd_close(args[0]) if args else '❌ Usage: `/close <dealer_id>`'
    elif cmd == '/human':
        reply = cmd_human(args[0]) if args else '❌ Usage: `/human <dealer_id>`'
    elif cmd == '/outreach':
        reply = cmd_outreach(args[0] if args else '')
    elif cmd == '/pending':
        reply = cmd_pending()
    elif cmd in ('/help', '/start'):
        reply = HELP_TEXT
    else:
        reply = f'❓ Comando non riconosciuto: `{cmd}`\nUsa `/help` per la lista.'

    send(reply, chat_id)


# ── Polling loop (daemon mode) ───────────────────────────────
def load_offset() -> int:
    try:
        return int(open(POLL_OFFSET_FILE).read().strip())
    except Exception:
        return 0


def save_offset(offset: int):
    try:
        with open(POLL_OFFSET_FILE, 'w') as f:
            f.write(str(offset))
    except Exception:
        pass


def run_daemon():
    log('ARGOS™ Telegram Bot DAEMON avviato')
    send(f'🤖 *ARGOS™ Telegram Bot online*\n📅 {now_it()}\nUsa `/help` per i comandi.')

    offset = load_offset()
    while True:
        try:
            result = tg_post('getUpdates', {
                'offset':          offset,
                'timeout':         30,
                'allowed_updates': 'message',
            })
            updates = result.get('result', [])
            for upd in updates:
                offset = upd['update_id'] + 1
                save_offset(offset)
                msg = upd.get('message', {})
                if not msg:
                    continue
                chat_id = str(msg.get('chat', {}).get('id', TELEGRAM_CHAT_ID))
                text    = msg.get('text', '')
                if not text:
                    continue
                # Sicurezza: accetta solo comandi dal chat_id autorizzato
                if chat_id != TELEGRAM_CHAT_ID:
                    log(f'WARN: messaggio da chat non autorizzato {chat_id}')
                    continue
                log(f'Comando ricevuto: {text[:80]}')
                dispatch(text, chat_id)
        except Exception as e:
            log(f'Polling error: {e}')
            time.sleep(5)


# ── CLI mode (alert singolo) ─────────────────────────────────
def run_cli_alert(text: str, markup_json: str = '{}'):
    """Invia un alert singolo e termina. Chiamato da wa-daemon."""
    send(text)
    sys.exit(0)


# ── Entry point ──────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'alert':
        text    = sys.argv[2] if len(sys.argv) > 2 else 'ARGOS alert'
        markup  = sys.argv[3] if len(sys.argv) > 3 else '{}'
        run_cli_alert(text, markup)
    else:
        run_daemon()
