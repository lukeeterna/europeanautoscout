#!/usr/bin/env python3
"""
response-analyzer.py — ARGOS™ Response Intelligence
CoVe 2026 | Enterprise Grade

RESPONSABILITÀ:
  Riceve un messaggio in arrivo da un dealer, carica il contesto completo
  dal DB, classifica la risposta, genera 2 candidate replies calibrate
  sull'archetipo, invia a Telegram per approvazione umana.

  Chiamato in modo asincrono da wa-daemon.js.
  Non blocca mai il daemon.

DIPENDENZE: duckdb, requests (Telegram), subprocess (Ollama locale)
"""

import argparse
import duckdb
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime

# ── Config ─────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
OLLAMA_URL         = 'http://localhost:11434/api/generate'
OLLAMA_MODEL       = 'mistral:7b'
TIMEZONE           = 'Europe/Rome'


def now_it() -> str:
    """Timestamp IT leggibile."""
    import subprocess
    try:
        return subprocess.check_output(
            ['python3', '-c',
             "import datetime; import zoneinfo; "
             "tz=zoneinfo.ZoneInfo('Europe/Rome'); "
             "print(datetime.datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S'))"],
            encoding='utf8'
        ).strip()
    except Exception:
        return datetime.utcnow().isoformat()


def load_dealer_context(db_path: str, dealer_id: str) -> dict:
    """Carica il profilo completo del dealer dal DuckDB."""
    con = duckdb.connect(db_path)
    try:
        rows = con.execute("""
            SELECT *
            FROM conversations
            WHERE dealer_id = ?
            LIMIT 1
        """, [dealer_id]).fetchall()

        if not rows:
            return {}

        cols = [d[0] for d in con.description]
        ctx  = dict(zip(cols, rows[0]))

        # Ultimi 5 messaggi per context history
        msgs = con.execute("""
            SELECT direction, body, timestamp_iso
            FROM messages
            WHERE dealer_id = ?
            ORDER BY created_at DESC
            LIMIT 5
        """, [dealer_id]).fetchall()
        ctx['message_history'] = [
            {'direction': r[0], 'body': r[1], 'ts': str(r[2])} for r in msgs
        ]
        return ctx
    finally:
        con.close()


# ── Classificatore keyword (no LLM per velocità) ──────────────
POSITIVE_KEYWORDS = [
    'sì', 'si', 'certo', 'ok', 'perfetto', 'interessante', 'interessato',
    'mi interessa', 'procedi', 'dimmi', 'dimmi di più', 'manda', 'mandami',
    'quando', 'come funziona', 'scheda', 'info', 'dati', 'vediamo',
    'possiamo', 'volentieri', 'ottimo', 'bene', 'va bene', 'capisco',
]
OBJECTION_KEYWORDS = [
    'ho già', 'uso già', 'lavoro già', 'non ho bisogno', 'troppo caro',
    'il prezzo', 'la fee', 'quanto costa', 'non capisco', 'non mi convince',
    'devo sentire', 'devo chiedere', 'mio socio', 'il titolare', 'aspetta',
    'richiamo', 'ti richiamo', 'non ho tempo', 'occupato',
]
NEGATIVE_KEYWORDS = [
    'non mi interessa', 'non interessa', 'no grazie', 'non grazie',
    'non ho interesse', 'smettila', 'non scrivere', 'blocca', 'stop',
    'rimuovi', 'cancella', 'non voglio',
]
CURIOSITY_KEYWORDS = [
    'chi sei', 'come hai', 'come mi hai', 'da dove', 'sei di',
    'quale azienda', 'che azienda', 'come funziona', 'spiegami',
    'cos\'è', 'che cos\'è', 'come mai', 'dove hai preso',
]


def classify_message(body: str) -> dict:
    """
    Classifica il tipo di risposta con approccio a 2 stadi:
    1. Keyword matching veloce (ms)
    2. Se ambiguo → Ollama per analisi semantica
    """
    b_lower = body.lower().strip()

    # Stage 1: keyword matching deterministico
    for kw in NEGATIVE_KEYWORDS:
        if kw in b_lower:
            return {'type': 'NEGATIVE', 'confidence': 0.95, 'method': 'keyword'}

    for kw in POSITIVE_KEYWORDS:
        if kw in b_lower:
            return {'type': 'POSITIVE', 'confidence': 0.85, 'method': 'keyword'}

    for kw in CURIOSITY_KEYWORDS:
        if kw in b_lower:
            return {'type': 'CURIOSITY', 'confidence': 0.80, 'method': 'keyword'}

    for kw in OBJECTION_KEYWORDS:
        if kw in b_lower:
            # Distingui OBJ-type
            if any(k in b_lower for k in ['ho già', 'uso già', 'lavoro già']):
                return {'type': 'OBJECTION', 'obj_code': 'OBJ-1', 'confidence': 0.90, 'method': 'keyword'}
            if any(k in b_lower for k in ['caro', 'prezzo', 'fee', 'costa']):
                return {'type': 'OBJECTION', 'obj_code': 'OBJ-2', 'confidence': 0.90, 'method': 'keyword'}
            if any(k in b_lower for k in ['tempo', 'occupato', 'richiamo']):
                return {'type': 'OBJECTION', 'obj_code': 'OBJ-3', 'confidence': 0.85, 'method': 'keyword'}
            if any(k in b_lower for k in ['pagamento', 'garanzie', 'sicurezza', 'come funziona']):
                return {'type': 'OBJECTION', 'obj_code': 'OBJ-4', 'confidence': 0.85, 'method': 'keyword'}
            if any(k in b_lower for k in ['titolare', 'socio', 'sentire', 'chiedere']):
                return {'type': 'OBJECTION', 'obj_code': 'OBJ-5', 'confidence': 0.90, 'method': 'keyword'}
            return {'type': 'OBJECTION', 'obj_code': 'OBJ-UNKNOWN', 'confidence': 0.70, 'method': 'keyword'}

    # Stage 2: Ollama per messaggi ambigui (es: risposta breve "Ok" senza contesto)
    return classify_with_ollama(body)


def classify_with_ollama(body: str) -> dict:
    """Usa Ollama locale per classificazione semantica."""
    prompt = f"""Classifica il seguente messaggio WhatsApp di un dealer automobilistico italiano
che ha ricevuto un messaggio da uno scout veicoli EU.

Messaggio: "{body}"

Rispondi SOLO con un oggetto JSON in questo formato:
{{"type": "POSITIVE|NEGATIVE|OBJECTION|CURIOSITY|UNKNOWN", "obj_code": "OBJ-1|OBJ-2|OBJ-3|OBJ-4|OBJ-5|OBJ-UNKNOWN|null", "confidence": 0.0-1.0, "reasoning": "breve spiegazione"}}

Type:
- POSITIVE = disponibile, interessato, vuole saperne di più
- NEGATIVE = rifiuto chiaro, non vuole più contatti
- OBJECTION = ha dubbi, obiezioni specifiche
- CURIOSITY = vuole capire chi sei e cosa fai
- UNKNOWN = impossibile classificare"""

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', OLLAMA_URL,
             '-H', 'Content-Type: application/json',
             '-d', json.dumps({'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False})],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        raw  = data.get('response', '{}')
        # Estrai JSON dalla risposta
        import re
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            parsed['method'] = 'ollama'
            return parsed
    except Exception as e:
        pass

    return {'type': 'UNKNOWN', 'confidence': 0.0, 'method': 'fallback'}


# ── Generatore risposte calibrate per archetipo ──────────────
REPLY_TEMPLATES = {
    'POSITIVE': {
        'RAGIONIERE': [
            ("ACK_DOC",
             "Buongiorno Mario, grazie per il riscontro.\n"
             "Le mando la scheda tecnica completa: km certificati, "
             "report Vincario e analisi mercato IT.\nLa contatto al più presto."),
            ("ACK_PROCESS",
             "Perfetto Mario.\nProcedo con la verifica documentale completa "
             "— entro 48h ha tutto il necessario per valutare."),
        ],
        'BARONE': [
            ("ACK_RESPECT",
             "La ringrazio, [Nome].\nLe preparo un'analisi su misura "
             "per il suo segmento — niente dati generici."),
            ("ACK_SHORT",
             "Ottimo [Nome]. Procedo e la richiamo "
             "appena ho qualcosa di concreto da mostrarle."),
        ],
        'PERFORMANTE': [
            ("ACK_FAST",
             "Perfetto.\n48h: scheda tecnica + breakdown margini nel suo inbox.\n"
             "Tutto verificato. Pronti."),
        ],
        'NARCISO': [
            ("ACK_EXCLUSIVE",
             "[Nome], ottimo.\nLe mando un'anteprima — "
             "questa opportunità va ad un dealer per area, massimo.\n"
             "La ricontatto subito."),
        ],
        'DEFAULT': [
            ("ACK_GENERIC",
             "Grazie per il riscontro.\n"
             "Le mando i dettagli completi entro 48h.\nA presto,\nLuca"),
        ],
    },
    'CURIOSITY': {
        'DEFAULT': [
            ("ID_FULL",
             "Certo [Nome].\nSono Luca Ferretti — scouto veicoli premium "
             "verificati in Germania, Austria, Olanda e altri mercati EU "
             "per dealer italiani.\nOgni veicolo ha report Vincario, km certificati, "
             "storico tagliandi. Nessun anticipo — pago solo a veicolo consegnato e approvato.\n"
             "Vuole che le mando un esempio concreto?"),
            ("ID_SHORT",
             "Mi chiamo Luca Ferretti.\nIdentificare veicoli premium EU verificati "
             "per dealer italiani che vogliono margini certi.\n"
             "Come funziona: [Nome] indica modello/segmento → in 48h "
             "verifico se c'è qualcosa di concreto in giro.\nZero anticipi."),
        ],
    },
    'OBJECTION': {
        'OBJ-1': {
            'RAGIONIERE': [
                ("OBJ1_DATA",
                 "Capisco perfettamente — e non voglio sostituire i suoi fornitori.\n"
                 "La differenza concreta: ogni veicolo che propongo ha km verificati "
                 "con report Vincario, non 'circa X.000'.\n"
                 "Quella differenza vale €1.500-2.000 sul valore di rivendita.\n"
                 "Posso mandarle un esempio reale per confronto?"),
            ],
            'DEFAULT': [
                ("OBJ1_GENERIC",
                 "Capisco — e non le chiedo di cambiare fornitori.\n"
                 "Le offro solo veicoli con verifica documentale che i canali "
                 "standard non offrono. Vale valutare?"),
            ],
        },
        'OBJ-2': {
            'DEFAULT': [
                ("OBJ2_CALC",
                 "Le faccio i numeri precisi:\n"
                 "• Veicolo EU: franco partenza\n"
                 "• Trasporto + targhe IT: incluso nel mio costo\n"
                 "• Mercato IT stesso veicolo: verificabile su AutoScout24\n"
                 "• La mia fee pilot: €400 — solo a consegna avvenuta\n"
                 "Vuole che glieli faccia su un veicolo specifico?"),
            ],
        },
        'OBJ-3': {
            'DEFAULT': [
                ("OBJ3_ASYNC",
                 "Rispetto il suo tempo — ho già fatto tutto il lavoro.\n"
                 "Le basta 1 minuto: le mando un PDF di 1 pagina con i dati.\n"
                 "Non ho fretta — mi faccia sapere quando può dare un'occhiata."),
            ],
        },
        'OBJ-4': {
            'DEFAULT': [
                ("OBJ4_RISK",
                 "Funziona a successo totale: non paga nulla fino alla "
                 "consegna fisica del veicolo.\nFee €400 — addebitata solo "
                 "quando il veicolo è da lei, verificato e approvato.\n"
                 "Se non corrisponde alle specifiche certificate: non deve nulla."),
            ],
        },
        'OBJ-5': {
            'DEFAULT': [
                ("OBJ5_ESCALATE",
                 "Naturalmente — è la cosa giusta da fare.\n"
                 "Le mando una scheda di 1 pagina da girare direttamente: "
                 "margine netto documentato, verifica km, condizioni pilot.\n"
                 "Posso mandarla a lei o direttamente al titolare?"),
            ],
        },
        'OBJ-UNKNOWN': {
            'DEFAULT': [
                ("OBJ_UNKNOWN",
                 "⚠️ OBIEZIONE NON CATALOGATA — RICHIEDE INTERVENTO UMANO\n"
                 "Messaggio dealer: [MSG_BODY]\n"
                 "NON rispondere automaticamente. Analizza e rispondi manualmente."),
            ],
        },
    },
    'NEGATIVE': {
        'DEFAULT': [
            ("CLOSE_GRACEFUL",
             "[internalmente: CHIUDI CONTATTO — non rispondere, log CLOSED_NO]"),
        ],
    },
}


def get_candidate_replies(
    classification: dict,
    persona: str,
    msg_body: str,
    dealer: dict,
    time_ctx: dict,
) -> list[dict]:
    """
    Restituisce 1-2 candidate replies basate su archetipo + classificazione.
    """
    msg_type = classification.get('type', 'UNKNOWN')
    obj_code = classification.get('obj_code')

    # Naviga il template tree
    if msg_type == 'NEGATIVE':
        templates = REPLY_TEMPLATES['NEGATIVE']['DEFAULT']
    elif msg_type == 'CURIOSITY':
        personas  = REPLY_TEMPLATES.get('CURIOSITY', {})
        templates = personas.get(persona, personas.get('DEFAULT', []))
    elif msg_type == 'POSITIVE':
        personas  = REPLY_TEMPLATES.get('POSITIVE', {})
        templates = personas.get(persona, personas.get('DEFAULT', []))
    elif msg_type == 'OBJECTION':
        obj_tree  = REPLY_TEMPLATES.get('OBJECTION', {})
        obj_node  = obj_tree.get(obj_code or 'OBJ-UNKNOWN', {})
        templates = obj_node.get(persona, obj_node.get('DEFAULT', []))
    else:
        templates = [('UNKNOWN_FALLBACK',
                      '⚠️ Messaggio non classificabile. Analisi manuale richiesta.')]

    # Personalizza con nome dealer e corpo messaggio
    name = dealer.get('dealer_name', '[Nome]').split()[0] if dealer else '[Nome]'
    results = []
    for label, text in templates:
        personalized = (
            text
            .replace('[Nome]', name)
            .replace('[MSG_BODY]', msg_body[:200])
        )
        results.append({
            'label':          label,
            'text':           personalized,
            'cialdini_note':  get_cialdini_note(msg_type, obj_code, persona),
        })

    return results


def get_cialdini_note(msg_type: str, obj_code: str, persona: str) -> str:
    """Nota Cialdini per la risposta — aiuta il reviewer umano."""
    notes = {
        ('POSITIVE', None, 'RAGIONIERE'): 'Commitment progressivo → dai dati, aspetta conferma',
        ('POSITIVE', None, 'BARONE'):     'Authority → rispetta il suo tempo e status',
        ('POSITIVE', None, 'PERFORMANTE'): 'Scarcity + velocità → consegna rapida',
        ('OBJECTION', 'OBJ-1', '*'):      'Reciprocità → dai insight competitivo gratuito',
        ('OBJECTION', 'OBJ-2', '*'):      'Commitment → micro-sì su calcolo specifico',
        ('OBJECTION', 'OBJ-5', '*'):      'Authority procedurale → facilitare al titolare',
        ('CURIOSITY', None, '*'):         'Liking + Reciprocità → racconta chi sei con valore',
        ('NEGATIVE', None, '*'):          'STOP. Porta aperta implicita per il futuro.',
    }
    for (t, o, p), note in notes.items():
        if t == msg_type and (o is None or o == obj_code) and (p == '*' or p == persona):
            return note
    return 'Rispondere con calibrazione archetipo standard'


def save_pending_reply(db_path: str, dealer_id: str, dealer_name: str,
                       inbound_msg_id: str, reply: dict, time_ctx: dict):
    """Salva reply candidata nel DB per tracking approvazione."""
    reply_id = f"reply_{uuid.uuid4().hex[:8]}"
    con = duckdb.connect(db_path)
    try:
        con.execute("""
            INSERT OR IGNORE INTO pending_replies
                (id, dealer_id, dealer_name, inbound_msg_id,
                 reply_text, reply_label, cialdini_trigger,
                 approved, sent, scheduled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, FALSE, CURRENT_TIMESTAMP)
        """, [
            reply_id, dealer_id, dealer_name, inbound_msg_id,
            reply['text'], reply['label'], reply.get('cialdini_note', ''),
        ])
        con.commit()
        return reply_id
    finally:
        con.close()


def send_telegram_for_approval(
    dealer: dict,
    msg_body: str,
    classification: dict,
    candidates: list[dict],
    reply_ids: list[str],
    time_ctx: dict,
):
    """
    Invia al Telegram human-in-loop le candidate replies con bottoni
    APPROVA / MODIFICA / RIFIUTA per ogni candidata.
    """
    if not TELEGRAM_BOT_TOKEN:
        print('[WARN] ARGOS_TELEGRAM_TOKEN non impostato — alert solo su console')
        print('--- CANDIDATE REPLIES ---')
        for i, r in enumerate(candidates):
            print(f'\n[{i+1}] {r["label"]}: {r["text"][:200]}')
        return

    import urllib.request, urllib.parse

    name     = dealer.get('dealer_name', 'Sconosciuto') if dealer else 'Sconosciuto'
    persona  = dealer.get('persona_type', '?') if dealer else '?'
    step     = dealer.get('current_step', '?') if dealer else '?'
    cls_type = classification.get('type', 'UNKNOWN')
    cls_conf = int(classification.get('confidence', 0) * 100)
    obj_code = classification.get('obj_code', '')

    lines = [
        f"🧠 *ANALISI RISPOSTA — {time_ctx.get('now_it', '')}*",
        f"",
        f"👤 *{name}* | Archetipo: {persona} | Step: {step}",
        f"📊 Classificazione: `{cls_type}` {f'({obj_code})' if obj_code else ''} — {cls_conf}% confidence",
        f"",
        f"💬 Messaggio ricevuto:",
        f"_{msg_body[:400]}_",
        f"",
    ]

    for i, (reply, rid) in enumerate(zip(candidates, reply_ids), 1):
        lines += [
            f"━━━ RISPOSTA #{i} — `{reply['label']}` ━━━",
            f"{reply['text'][:500]}",
            f"_💡 {reply.get('cialdini_note', '')}_",
            f"Reply ID: `{rid}`",
            f"",
        ]

    lines += [
        f"*Azione richiesta:*",
        f"→ Approva: `/approva <reply_id>`",
        f"→ Modifica: `/modifica <reply_id> <testo>`",
        f"→ Rifiuta: `/rifiuta <reply_id>`",
        f"→ Escalation umana: `/human`",
    ]

    text = '\n'.join(lines)

    payload = {
        'chat_id':    TELEGRAM_CHAT_ID,
        'text':       text,
        'parse_mode': 'Markdown',
    }
    data = urllib.parse.urlencode({k: v for k, v in payload.items()}).encode()
    url  = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        req  = urllib.request.Request(url, data=data, method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        print(f'[INFO] Telegram approval request inviata: {resp.status}')
    except Exception as e:
        print(f'[ERROR] Telegram send failed: {e}')


# ── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msg-id',     required=True)
    parser.add_argument('--msg-body',   required=True)
    parser.add_argument('--dealer-id',  required=True)
    parser.add_argument('--dealer-name', default='Sconosciuto')
    parser.add_argument('--persona',    default='RAGIONIERE')
    parser.add_argument('--step',       default='UNKNOWN')
    parser.add_argument('--db-path',    required=True)
    parser.add_argument('--time-ctx',   default='{}')
    args = parser.parse_args()

    time_ctx = json.loads(args.time_ctx) if args.time_ctx else {}

    print(f'[{now_it()}] Analyzer avviato per msg_id={args.msg_id}')
    print(f'  Dealer: {args.dealer_name} | Persona: {args.persona} | Step: {args.step}')
    print(f'  Messaggio: {args.msg_body[:100]}...')

    # 1. Carica contesto dealer
    dealer = load_dealer_context(args.db_path, args.dealer_id)
    if not dealer:
        dealer = {
            'dealer_id':   args.dealer_id,
            'dealer_name': args.dealer_name,
            'persona_type': args.persona,
            'current_step': args.step,
        }

    # 2. Classifica messaggio
    classification = classify_message(args.msg_body)
    print(f'  Classificazione: {classification}')

    # 3. Genera candidate replies
    candidates = get_candidate_replies(
        classification,
        args.persona.upper(),
        args.msg_body,
        dealer,
        time_ctx,
    )

    # 4. Salva nel DB
    reply_ids = [
        save_pending_reply(
            args.db_path, args.dealer_id, args.dealer_name,
            args.msg_id, r, time_ctx
        )
        for r in candidates
    ]

    # 5. Invia a Telegram per approvazione
    send_telegram_for_approval(
        dealer, args.msg_body, classification,
        candidates, reply_ids, time_ctx
    )

    print(f'[{now_it()}] Analyzer completato. Reply IDs: {reply_ids}')


if __name__ == '__main__':
    main()
