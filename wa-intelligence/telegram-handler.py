#!/usr/bin/env python3
"""
telegram-handler.py — ARGOS™ Human-in-Loop Telegram Bot
CoVe 2026 | Enterprise Grade | PM2 Managed

S60: Migrato da DuckDB a SQLite (WAL mode, multi-processo nativo).

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

import sqlite3
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
import zoneinfo
from datetime import datetime

TIMEZONE         = zoneinfo.ZoneInfo('Europe/Rome')
TELEGRAM_TOKEN   = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
DB_PATH          = os.environ.get('ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite'))
BRIDGE_DB_PATH   = os.environ.get('BRIDGE_DB_PATH', '')
WA_SENDER        = os.path.expanduser(
    '~/Documents/app-antigravity-auto/wa-sender/send_message.js')
WA_CLIENT_ID     = os.environ.get('WA_CLIENT_ID', 'argos-business')
LOG_FILE         = '/tmp/argos-tg-handler.log'
POLL_OFFSET_FILE = '/tmp/argos-tg-offset.txt'

# Anti-ban sleep range (secondi)
SLEEP_MIN, SLEEP_MAX = 90, 720

# S173: stato FORCE — reply_id → True (attende keyword FORCE da Luke)
_PENDING_FORCE: dict[str, dict] = {}

# S173: audit log force=true overrides
FORCE_AUDIT_PATH = os.path.expanduser('~/venture-os/state/argos-force-overrides.jsonl')


def _log_force_override(phone: str, reply_id: str, context: str = 'telegram_approve'):
    """Scrive audit entry per force=true override (compliance trail)."""
    entry = json.dumps({
        'ts': int(time.time()),
        'phone': phone,
        'reply_id': reply_id,
        'founder': 'luke',
        'context': context,
    })
    try:
        os.makedirs(os.path.dirname(FORCE_AUDIT_PATH), exist_ok=True)
        with open(FORCE_AUDIT_PATH, 'a') as _f:
            _f.write(entry + '\n')
        log(f'[force-override] audit logged: phone={phone} reply_id={reply_id}')
    except Exception as _e:
        log(f'[force-override] audit log FAILED: {_e} — entry: {entry}')


def _bridge_precheck_24h(phone: str) -> tuple[bool, int]:
    """Verifica se phone ha ricevuto msg nelle ultime 24h via bridge_outbound.
    Returns: (recent: bool, minutes_ago: int)
    """
    if not BRIDGE_DB_PATH:
        return False, -1
    try:
        con = sqlite3.connect(BRIDGE_DB_PATH, timeout=5)
        cutoff = int(time.time()) - 24 * 3600
        row = con.execute(
            'SELECT sent_ts FROM bridge_outbound WHERE target_phone = ? AND sent_ts IS NOT NULL AND sent_ts > ? ORDER BY sent_ts DESC LIMIT 1',
            (phone, cutoff)
        ).fetchone()
        con.close()
        if not row:
            return False, -1
        minutes_ago = round((int(time.time()) - row[0]) / 60)
        return True, minutes_ago
    except Exception as _e:
        log(f'[bridge_precheck_24h] error: {_e}')
        return False, -1


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
        resp = urllib.request.urlopen(req, timeout=40)
        return json.loads(resp.read())
    except Exception as e:
        log(f'TG error [{method}]: {e}')
        return {}


def send(text: str, chat_id: str = TELEGRAM_CHAT_ID, reply_markup: str = None):
    payload = {
        'chat_id':    chat_id,
        'text':       text,
        'parse_mode': 'Markdown',
    }
    if reply_markup is not None:
        payload['reply_markup'] = reply_markup
    return tg_post('sendMessage', payload)


def make_inline_keyboard(reply_id: str) -> str | None:
    """Ritorna JSON reply_markup con bottoni Accetta/Rifiuta, o None se reply_id troppo lungo."""
    cb_approva = f'approva:{reply_id}'
    cb_rifiuta = f'rifiuta:{reply_id}'
    if len(cb_approva) > 64 or len(cb_rifiuta) > 64:
        return None
    return json.dumps({
        'inline_keyboard': [[
            {'text': '✅ Accetta', 'callback_data': cb_approva},
            {'text': '🚫 Rifiuta', 'callback_data': cb_rifiuta},
        ]]
    })


def db_query(sql: str, params: list = None) -> list:
    try:
        from db_utils import get_connection
        con = get_connection()
        con.row_factory = sqlite3.Row
        cur = con.execute(sql, params or [])
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        log(f'db_query error: {e}')
        return []


def db_exec(sql: str, params: list = None):
    for attempt in range(3):
        try:
            from db_utils import get_connection
            con = get_connection()
            con.execute(sql, params or [])
            con.commit()
            con.close()
            return True
        except Exception as e:
            log(f'db_exec error (attempt {attempt+1}): {e}')
            time.sleep(1)
    return False


# ── Comandi ──────────────────────────────────────────────────
def cmd_approva(reply_id: str, force: bool = False) -> str:
    """Approva e schedula invio reply.

    S173: precheck 24h su bridge_outbound prima di inviare.
    Se phone ha ricevuto msg nelle ultime 24h e force=False:
      → risponde con warning + istruzione 'FORCE <reply_id>' per override.
    Se force=True: procede + scrive audit log.
    """
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', reply_id):
        return f'❌ Formato reply_id non valido: `{reply_id}`'

    rows = db_query('SELECT * FROM pending_replies WHERE id = ?', [reply_id])
    if not rows:
        return f'❌ Reply ID non trovato: `{reply_id}`'

    r = rows[0]
    if r.get('approved') == 1:
        return f'⚠️ Reply `{reply_id}` già approvata.'
    if r.get('sent') == 1:
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

    # S173: precheck 24h via bridge_outbound
    recent, minutes_ago = _bridge_precheck_24h(phone)
    if recent and not force:
        # Salva stato pending FORCE per questo reply_id
        _PENDING_FORCE[reply_id] = {'phone': phone, 'wa_id': wa_id, 'r': r}
        return (
            f'⚠️ *Precheck 24h BLOCKED*\n'
            f'📱 {phone} ha ricevuto un messaggio *{minutes_ago} minuti fa* (< 24h).\n\n'
            f'Per inviare ugualmente, rispondi con:\n'
            f'`FORCE {reply_id}`\n\n'
            f'_Audit log obbligatorio — registra override per compliance._'
        )

    if recent and force:
        # Force override — audit log obbligatorio
        _log_force_override(phone=phone, reply_id=reply_id, context='telegram_approve')
        log(f'[force-override] APPROVED: reply={reply_id} phone={phone} minutes_ago={minutes_ago}')

    # Schedula invio con anti-ban sleep
    sleep_s = random.randint(SLEEP_MIN, SLEEP_MAX)
    log(f'Approvata reply {reply_id} — sleep {sleep_s}s prima dell\'invio (force={force})')

    db_exec(
        'UPDATE pending_replies SET approved = 1 WHERE id = ?',
        [reply_id]
    )

    # Cleanup stato FORCE pendente se presente
    _PENDING_FORCE.pop(reply_id, None)

    # S224 #9: orchestrazione invio via temp-file Python (NO bash-quoting pitfalls).
    # Ri-controlla `approved` DOPO lo sleep e PRIMA di node sender → reject durante
    # sleep = NESSUN invio. Stesso pattern provato di response-analyzer.send_script.
    task = {
        'db_path':    DB_PATH,
        'reply_id':   reply_id,
        'phone':      phone,
        'reply_text': r["reply_text"],
        'sleep_s':    sleep_s,
        'daemon_url': os.environ.get('ARGOS_DAEMON_URL', 'http://127.0.0.1:9191/send'),
        'api_key':    os.environ.get('ARGOS_API_KEY', ''),
        'force':      bool(force),
    }
    with tempfile.NamedTemporaryFile('w', suffix='.json', prefix='argos_tg_send_',
                                     delete=False, dir='/tmp') as _f:
        json.dump(task, _f)
        task_file = _f.name

    send_script = (
        "import time, json, sqlite3, sys, os, urllib.request, urllib.error\n"
        "t = json.load(open(sys.argv[1]))\n"
        "os.unlink(sys.argv[1])\n"
        "time.sleep(t['sleep_s'])\n"
        # re-check approval — reject durante sleep deve abortire PRIMA dell'invio
        "ck = sqlite3.connect(t['db_path'], timeout=10)\n"
        "ck.execute('PRAGMA busy_timeout=10000')\n"
        "ap = ck.execute('SELECT approved FROM pending_replies WHERE id=?', [t['reply_id']]).fetchone()\n"
        "ck.close()\n"
        "if not ap or ap[0] != 1:\n"
        "    print(f'[ABORT] Reply {t[\"reply_id\"]} non piu approvata (rifiutata durante sleep) — invio annullato')\n"
        "    sys.exit(0)\n"
        # S230: branch multi/mono — envelope JSON AMBRA vs testo semplice
        "try:\n"
        "    envelope = json.loads(t['reply_text'])\n"
        "    msgs = envelope.get('messages', []) if isinstance(envelope, dict) else []\n"
        "except Exception:\n"
        "    msgs = []\n"
        "if msgs:\n"
        "    # MULTI: POST /send-multi — NON include 'force' (non supportato da /send-multi)\n"
        "    send_url = t['daemon_url'].rsplit('/', 1)[0] + '/send-multi'\n"
        "    payload = json.dumps({'phone': t['phone'], 'messages': msgs}).encode()\n"
        "    endpoint_label = '/send-multi'\n"
        "else:\n"
        "    # MONO: POST /send — comportamento originale, include 'force'\n"
        "    send_url = t['daemon_url']\n"
        "    payload = json.dumps({'phone': t['phone'], 'message': t['reply_text'], 'force': t['force']}).encode()\n"
        "    endpoint_label = '/send'\n"
        "req = urllib.request.Request(send_url, data=payload, method='POST', headers={'Content-Type': 'application/json', 'X-API-Key': t['api_key']})\n"
        "try:\n"
        "    resp = urllib.request.urlopen(req, timeout=60)\n"
        "    rbody = json.loads(resp.read())\n"
        "except urllib.error.HTTPError as e:\n"
        "    print(f'[ERROR] Reply {t[\"reply_id\"]} daemon {endpoint_label} HTTP {e.code}: {e.read().decode()[:200]} — sent NON marcato')\n"
        "    sys.exit(1)\n"
        "except Exception as e:\n"
        "    print(f'[ERROR] Reply {t[\"reply_id\"]} daemon {endpoint_label} fallito: {e} — sent NON marcato')\n"
        "    sys.exit(1)\n"
        "if rbody.get('status') != 'sent':\n"
        "    print(f'[ERROR] Reply {t[\"reply_id\"]} daemon {endpoint_label} risposta inattesa: {rbody} — sent NON marcato')\n"
        "    sys.exit(1)\n"
        "c = sqlite3.connect(t['db_path'], timeout=10)\n"
        "c.execute('PRAGMA busy_timeout=10000')\n"
        "cur = c.execute('UPDATE pending_replies SET sent=1 WHERE id=? AND approved=1', [t['reply_id']])\n"
        "rc = cur.rowcount\n"
        "c.commit(); c.close()\n"
        "if rc == 0:\n"
        "    print(f'[ERROR] Reply {t[\"reply_id\"]} inviata ma sent NON aggiornato (approved!=1 race) — verifica manuale')\n"
        "else:\n"
        "    sent_ref = rbody.get('msg_ids', rbody.get('msg_id', '?'))\n"
        "    print(f'[SENT] Reply {t[\"reply_id\"]} inviata via daemon {endpoint_label} ref={sent_ref}')\n"
    )
    _log_fd = open('/tmp/argos-tg-send.log', 'a')
    subprocess.Popen(
        [sys.executable, '-c', send_script, task_file],
        close_fds=True, stdout=_log_fd, stderr=_log_fd,
    )
    _log_fd.close()

    force_note = ' *(force=true, audit logged)*' if force else ''
    return (
        f'✅ *Reply approvata{force_note}* — invio tra ~{sleep_s//60}min\n'
        f'👤 A: {r["dealer_name"]}\n'
        f'💬 _{r["reply_text"][:200]}_'
    )


def cmd_modifica(reply_id: str, new_text: str) -> str:
    rows = db_query('SELECT * FROM pending_replies WHERE id = ?', [reply_id])
    if not rows:
        return f'❌ Reply ID non trovato: `{reply_id}`'

    r = rows[0]
    original_text = r.get('reply_text', '')

    # Salva coppia originale→corretto per training dataset
    db_exec("""
        CREATE TABLE IF NOT EXISTS training_corrections (
            id TEXT PRIMARY KEY,
            reply_id TEXT,
            dealer_id TEXT,
            original_label TEXT,
            original_text TEXT,
            corrected_text TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    import uuid
    db_exec("""
        INSERT INTO training_corrections (id, reply_id, dealer_id, original_label, original_text, corrected_text)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        f'tc_{uuid.uuid4().hex[:8]}', reply_id,
        r.get('dealer_id', ''), r.get('reply_label', ''),
        original_text, new_text
    ])

    db_exec(
        'UPDATE pending_replies SET reply_text = ?, reply_label = ? WHERE id = ?',
        [new_text, 'MANUAL_EDIT', reply_id]
    )
    return (
        f'✏️ *Testo aggiornato* per reply `{reply_id}`\n'
        f'📊 _Correzione salvata per training_\n'
        f'Ora usa `/approva {reply_id}` per inviare.'
    )


def cmd_rifiuta(reply_id: str) -> str:
    rows = db_query('SELECT sent FROM pending_replies WHERE id = ?', [reply_id])
    if not rows:
        return f'❌ Reply ID non trovato: `{reply_id}`'
    if rows[0].get('sent') == 1:
        return f'⚠️ Reply `{reply_id}` già inviata — impossibile revocare.'
    # S224 #9: revoca consentita finché non spedito (sent=0), anche se già approvato
    # (finestra di sleep anti-ban). Il send subprocess ri-controlla approved prima dell'invio.
    db_exec(
        'UPDATE pending_replies SET approved = 0 WHERE id = ? AND sent = 0',
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
        WHERE approved IS NULL AND sent = 0
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
        SET last_contact_at = datetime(last_contact_at, '+' || ? || ' days')
        WHERE dealer_id = ?
    """, [str(days_int), dealer_id])

    return f'⏰ Scadenza *posticipata di {days_int} giorno/i* per dealer `{dealer_id}`'


def cmd_close(dealer_id: str) -> str:
    db_exec("""
        UPDATE conversations
        SET current_step = 'CLOSED_NO',
            analyzed_at  = datetime('now')
        WHERE dealer_id = ?
    """, [dealer_id])
    return f'🔒 Dealer `{dealer_id}` chiuso con stato `CLOSED_NO`.'


def cmd_human(dealer_id: str) -> str:
    db_exec("""
        UPDATE conversations
        SET current_step = 'HUMAN_NEEDED',
            analyzed_at  = datetime('now')
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
        SET current_step = 'DAY1_SENT', last_contact_at = datetime('now')
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
        WHERE approved IS NULL AND sent = 0
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


def cmd_costi() -> str:
    """Report costi LLM OpenRouter."""
    rows = db_query("""
        SELECT
            COUNT(*) as calls,
            COALESCE(SUM(input_tokens), 0) as tot_in,
            COALESCE(SUM(output_tokens), 0) as tot_out,
            COALESCE(SUM(cost_usd), 0) as tot_usd
        FROM llm_costs
    """)
    if not rows or rows[0]['calls'] == 0:
        return '💰 *Nessuna chiamata LLM registrata.*'

    r = rows[0]
    cost_eur = r['tot_usd'] * 0.92  # approx USD→EUR

    # Ultimi 5 costi
    recent = db_query("""
        SELECT dealer_id, model, input_tokens, output_tokens, cost_usd, created_at
        FROM llm_costs ORDER BY created_at DESC LIMIT 5
    """)

    today = db_query("""
        SELECT COALESCE(SUM(cost_usd), 0) as today_usd, COUNT(*) as today_calls
        FROM llm_costs WHERE date(created_at) = date('now')
    """)
    t = today[0] if today else {'today_usd': 0, 'today_calls': 0}

    lines = [
        f'💰 *ARGOS™ LLM Cost Tracker*',
        f'',
        f'📊 *Totale*: ${r["tot_usd"]:.4f} (~€{cost_eur:.4f})',
        f'🔢 Chiamate: {r["calls"]}',
        f'📥 Token in: {r["tot_in"]:,} | 📤 Token out: {r["tot_out"]:,}',
        f'',
        f'📅 *Oggi*: ${t["today_usd"]:.4f} | {t["today_calls"]} chiamate',
        f'',
        f'*Ultime 5 chiamate:*',
    ]
    for c in recent:
        lines.append(
            f'• `{c["dealer_id"]}` {c["input_tokens"]}+{c["output_tokens"]}tok '
            f'${c["cost_usd"]:.4f} _{str(c["created_at"])[:16]}_'
        )

    return '\n'.join(lines)


def cmd_pause():
    """Pause the WA agent — no messages will be sent."""
    import urllib.request as _ureq
    api_key = os.environ.get('ARGOS_API_KEY', '')
    try:
        req = _ureq.Request(
            'http://127.0.0.1:9191/pause',
            method='POST',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=b'{}',
        )
        resp = _ureq.urlopen(req, timeout=10)
        return '⏸ *Agent PAUSED* — nessun messaggio verrà inviato.\nUsa `/resume` per riprendere.'
    except Exception as e:
        return f'❌ Errore pause: {e}'


def cmd_resume():
    """Resume the WA agent."""
    import urllib.request as _ureq
    api_key = os.environ.get('ARGOS_API_KEY', '')
    try:
        req = _ureq.Request(
            'http://127.0.0.1:9191/resume',
            method='POST',
            headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
            data=b'{}',
        )
        resp = _ureq.urlopen(req, timeout=10)
        return '▶️ *Agent RESUMED* — operatività ripristinata.'
    except Exception as e:
        return f'❌ Errore resume: {e}'


def cmd_metrics():
    """Show today's health metrics."""
    import urllib.request as _ureq
    import json as _json
    api_key = os.environ.get('ARGOS_API_KEY', '')
    try:
        req = _ureq.Request(
            'http://127.0.0.1:9191/health-metrics',
            headers={'X-API-Key': api_key},
        )
        resp = _ureq.urlopen(req, timeout=10)
        d = _json.loads(resp.read())
        risk = d.get('risk_level', 'N/A')
        emoji = {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(risk, '⚪')
        return (
            f"📊 *Health Metrics* — {d.get('date', '?')}\n\n"
            f"Inviati: {d.get('sent', 0)} | Consegnati: {d.get('delivered', 0)}\n"
            f"Letti: {d.get('read_count', 0)} | Risposte: {d.get('replied', 0)}\n"
            f"Bloccati: {d.get('blocked', 0)} | Falliti: {d.get('failed', 0)}\n\n"
            f"Delivery rate: {d.get('delivery_rate', 'N/A')}\n"
            f"Block rate: {d.get('block_rate', 'N/A')}\n"
            f"Reply rate: {d.get('reply_rate', 'N/A')}\n\n"
            f"{emoji} Risk: *{risk}*"
        )
    except Exception as e:
        return f'❌ Errore metrics: {e}'


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

💰 *Costi*
`/costi` — report costi LLM OpenRouter

⏸ *Controllo Agent*
`/pause` — pausa agent, blocca tutti gli invii
`/resume` — riprendi operativita'
`/metrics` — metriche salute e rischio ban

ℹ️ *Info*
`/help` — questo messaggio
"""

BUSINESS_START = 9
BUSINESS_END   = 18


def dispatch(text: str, chat_id: str):
    parts = text.strip().split(None, 2)
    cmd   = parts[0].lower() if parts else ''
    args  = parts[1:]

    # S173: FORCE <reply_id> — override precheck 24h dopo avviso da cmd_approva
    if cmd == 'force' and args:
        force_reply_id = args[0]
        if force_reply_id in _PENDING_FORCE:
            reply = cmd_approva(force_reply_id, force=True)
        else:
            reply = (
                f'⚠️ Nessun precheck pending per `{force_reply_id}`.\n'
                f'Usa prima `/approva {force_reply_id}` — se bloccato da precheck 24h, il sistema chiederà conferma.'
            )
        send(reply, chat_id)
        return

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
    elif cmd == '/costi':
        reply = cmd_costi()
    elif cmd == '/pause':
        reply = cmd_pause()
    elif cmd == '/resume':
        reply = cmd_resume()
    elif cmd == '/metrics':
        reply = cmd_metrics()
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
                'allowed_updates': json.dumps(['message', 'callback_query']),
            })
            updates = result.get('result', [])
            for upd in updates:
                offset = upd['update_id'] + 1
                save_offset(offset)

                # ── branch callback_query (bottoni inline) ──────────
                cq = upd.get('callback_query')
                if cq:
                    cq_id   = cq['id']
                    data    = cq.get('data', '')
                    chat_id = str(cq.get('message', {}).get('chat', {}).get('id', TELEGRAM_CHAT_ID))
                    if chat_id != TELEGRAM_CHAT_ID:
                        log(f'WARN: callback da chat non autorizzato {chat_id}')
                        tg_post('answerCallbackQuery', {'callback_query_id': cq_id})
                        continue
                    log(f'Callback ricevuto: {data}')
                    parts  = data.split(':', 1)
                    action = parts[0] if parts else ''
                    rid    = parts[1] if len(parts) > 1 else ''
                    if action == 'approva' and rid:
                        reply = cmd_approva(rid)
                    elif action == 'rifiuta' and rid:
                        reply = cmd_rifiuta(rid)
                    else:
                        reply = f'❌ Callback non riconosciuto: `{data}`'
                    tg_post('answerCallbackQuery', {'callback_query_id': cq_id, 'text': action.capitalize()})
                    send(reply, chat_id)
                    continue

                # ── branch message (path testo esistente) ───────────
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
