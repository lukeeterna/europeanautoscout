#!/usr/bin/env python3
"""
response-analyzer.py — ARGOS™ Response Intelligence
CoVe 2026 | Enterprise Grade | S60 LLM-Powered

S60: Migrato DuckDB→SQLite + integrazione LLM via OpenRouter.
     Keyword classifier resta per routing. LLM genera risposte calibrate.
     Cost tracking integrato.

RESPONSABILITÀ:
  Riceve messaggio dealer → classifica (keyword) → genera risposte LLM
  → salva candidate nel DB → invia a Telegram per approvazione umana.

  ZERO risposte automatiche. Sempre human-in-the-loop.

DIPENDENZE: sqlite3 (stdlib), urllib (stdlib)
"""

import argparse
import sqlite3
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime

# ── Config ─────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get('ARGOS_TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('ARGOS_TELEGRAM_CHAT_ID', '931063621')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL   = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-haiku-4-5')
OPENROUTER_URL     = 'https://openrouter.ai/api/v1/chat/completions'
DB_PATH            = os.environ.get('ARGOS_DB_PATH', '')

# ── ARGOS Business Constants ──────────────────────────────
ARGOS_FEE = '€1.000'
ARGOS_PERSONA = 'Luca Ferretti'
ARGOS_BRAND = 'ARGOS Automotive'


def now_it() -> str:
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo('Europe/Rome')
        return datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
    except Exception:
        return datetime.utcnow().isoformat()


# ── SYSTEM PROMPT per LLM ────────────────────────────────────
SYSTEM_PROMPT = """Sei Luca Ferretti, consulente di ARGOS Automotive. Scrivi risposte WhatsApp per concessionari italiani.

CHI SEI:
- Luca Ferretti, ARGOS Automotive
- Selezioni veicoli premium (BMW, Mercedes, Audi 2018-2023) in Germania, Belgio, Olanda per dealer italiani
- Fee fissa €1.000 a veicolo consegnato, zero anticipi
- Report DAT + ispezione DEKRA inclusi
- Garanzia costruttore UE valida in Italia

REGOLE ASSOLUTE — VIOLAZIONE = RISPOSTA RIFIUTATA:
1. Fee: SEMPRE €1.000. MAI €400, MAI altro importo
2. MAI dire "non possiamo fatturare" → dire "il bonifico è più efficiente per entrambi"
3. MAI dire "CarFax EU" → dire "report DAT" o "DAT Fahrzeughistorie"
4. MAI dire "Händlergarantie" → dire "garanzia costruttore UE"
5. MAI menzionare: CoVe, Claude, AI, Anthropic, RAG, embedding, intelligenza artificiale, algoritmo, machine learning
6. MAI dire "Vincario" → dire "report DAT"
7. Talk track vs trader: "I trader nascondono €7-10.000 nel prezzo. Noi: €1.000 fisso, tu scegli, DAT+DEKRA inclusi."
8. Zero anticipi — il dealer paga SOLO a veicolo consegnato e approvato
9. Se il dealer dice NO → NON insistere. Chiudi con eleganza, porta aperta
10. MAI inventare veicoli specifici, prezzi specifici o disponibilità che non conosci

TONO PER ARCHETIPO:
- RAGIONIERE: numeri precisi, dati concreti, zero fuffa, ROI esplicito
- BARONE: rispetto, "su misura per lei", esclusività, mai pressione
- PERFORMANTE: velocità, "48h", risultati, efficienza
- NARCISO: esclusività, "selezionato", "riservato per la sua area"
- TECNICO: documentazione, specifiche, report DAT dettagliato
- RELAZIONALE: calore, "ci lavoriamo insieme", zero pressione, empatia
- CONSERVATORE: sicurezza, "nessuna sorpresa", garanzie, tutto documentato
- DELEGATORE: semplicità, "gestisco tutto io", zero complicazioni
- OPPORTUNISTA: margine concreto, "i numeri parlano da soli"
- VISIONARIO: modello innovativo, trasparenza come valore differenziante

FORMATO RISPOSTA:
- WhatsApp: breve, diretto, massimo 6-8 righe
- Firma: — Luca (mai "Cordiali saluti" o formalità eccessive)
- Usa il nome del dealer/titolare se lo conosci
- NO emoji eccessive, massimo 0-1 per messaggio
- Tono professionale ma umano, come un collega fidato"""


def build_user_prompt(dealer: dict, msg_body: str, classification: dict,
                      msg_history: list) -> str:
    """Costruisce il prompt utente con tutto il contesto dealer."""
    cls_type = classification.get('type', 'UNKNOWN')
    obj_code = classification.get('obj_code', '')

    # Storico conversazione
    history_text = ''
    if msg_history:
        history_lines = []
        for m in reversed(msg_history):  # cronologico
            direction = '→ NOI' if m.get('direction') == 'OUTBOUND' else '← DEALER'
            history_lines.append(f'{direction}: {m.get("body", "")[:200]}')
        history_text = '\n'.join(history_lines)

    prompt = f"""CONTESTO DEALER:
- Nome: {dealer.get('dealer_name', 'Sconosciuto')}
- Città: {dealer.get('city', '?')}
- Stock: {dealer.get('stock_size', '?')} veicoli
- Archetipo: {dealer.get('persona_type', 'DEFAULT')}
- Step attuale: {dealer.get('current_step', '?')}
- Score: {dealer.get('score', '?')}/10

CLASSIFICAZIONE MESSAGGIO: {cls_type}{f' ({obj_code})' if obj_code else ''}
"""

    if history_text:
        prompt += f"""
STORICO CONVERSAZIONE:
{history_text}
"""

    prompt += f"""
MESSAGGIO DEL DEALER (a cui devi rispondere):
"{msg_body}"

Genera 2 risposte alternative:
RISPOSTA_A (la migliore per questo archetipo):
RISPOSTA_B (approccio diverso, più breve):

Calibra il tono sull'archetipo {dealer.get('persona_type', 'DEFAULT')}. Rispondi SOLO con le 2 risposte, nient'altro."""

    return prompt


# ── LLM Call via OpenRouter ──────────────────────────────────
def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """Chiama OpenRouter e ritorna le risposte + usage per cost tracking."""
    if not OPENROUTER_API_KEY:
        return {'error': 'OPENROUTER_API_KEY non impostata', 'text': '', 'usage': {}}

    import urllib.request

    payload = json.dumps({
        'model': OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_tokens': 800,
        'temperature': 0.7,
    }).encode()

    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://argosautomotive.it',
        'X-Title': 'ARGOS Response Analyzer',
    }

    req = urllib.request.Request(OPENROUTER_URL, data=payload, headers=headers)

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())

        text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = data.get('usage', {})

        return {'text': text, 'usage': usage, 'model': data.get('model', OPENROUTER_MODEL)}
    except Exception as e:
        print(f'[ERROR] OpenRouter call failed: {e}')
        return {'error': str(e), 'text': '', 'usage': {}}


def parse_llm_responses(text: str) -> list:
    """Parsa le 2 risposte dal testo LLM."""
    responses = []

    # Cerca RISPOSTA_A e RISPOSTA_B
    parts = re.split(r'RISPOSTA_[AB][\s:]*', text, flags=re.IGNORECASE)

    for i, part in enumerate(parts[1:], 1):  # skip parte prima di RISPOSTA_A
        cleaned = part.strip().strip('"').strip()
        if cleaned:
            label = 'LLM_A' if i == 1 else 'LLM_B'
            responses.append({'label': label, 'text': cleaned})

    # Fallback: se il parsing non trova 2 risposte, usa il testo intero
    if len(responses) == 0 and text.strip():
        responses.append({'label': 'LLM_SINGLE', 'text': text.strip()})

    return responses[:2]


# ── Cost Tracking ────────────────────────────────────────────
def track_cost(db_path: str, model: str, usage: dict, dealer_id: str):
    """Salva il costo della chiamata LLM nel DB."""
    # Pricing approssimativo (aggiornare se cambia)
    PRICING = {
        'anthropic/claude-haiku-4-5': {'input': 0.80, 'output': 4.00},  # $/MTok
        'anthropic/claude-3-5-haiku': {'input': 0.80, 'output': 4.00},
        'anthropic/claude-sonnet-4': {'input': 3.00, 'output': 15.00},
        'anthropic/claude-3-5-sonnet': {'input': 3.00, 'output': 15.00},
    }

    # Trova pricing (fallback a haiku)
    price = PRICING.get(model, PRICING.get('anthropic/claude-haiku-4-5'))

    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    total_tokens = input_tokens + output_tokens

    cost_usd = (input_tokens * price['input'] + output_tokens * price['output']) / 1_000_000

    try:
        con = sqlite3.connect(db_path, timeout=10)
        con.execute("""
            CREATE TABLE IF NOT EXISTS llm_costs (
                id TEXT PRIMARY KEY,
                dealer_id TEXT,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        con.execute("""
            INSERT INTO llm_costs (id, dealer_id, model, input_tokens, output_tokens, total_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            f'cost_{uuid.uuid4().hex[:8]}',
            dealer_id, model,
            input_tokens, output_tokens, total_tokens,
            round(cost_usd, 6)
        ])
        con.commit()
        con.close()
        print(f'[COST] {model}: {input_tokens}in + {output_tokens}out = ${cost_usd:.4f}')
    except Exception as e:
        print(f'[ERROR] track_cost: {e}')


# ── DB helpers ───────────────────────────────────────────────
def load_dealer_context(db_path: str, dealer_id: str) -> dict:
    """Carica il profilo completo del dealer dal SQLite."""
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute("""
            SELECT * FROM conversations WHERE dealer_id = ? LIMIT 1
        """, [dealer_id])
        rows = cur.fetchall()
        if not rows:
            return {}
        cols = [d[0] for d in cur.description]
        ctx = dict(zip(cols, rows[0]))

        try:
            cur2 = con.execute("""
                SELECT direction, body, timestamp_it
                FROM messages WHERE dealer_id = ?
                ORDER BY timestamp_it DESC LIMIT 5
            """, [dealer_id])
            ctx['message_history'] = [
                {'direction': r[0], 'body': r[1], 'ts': str(r[2])} for r in cur2.fetchall()
            ]
        except Exception:
            ctx['message_history'] = []
        return ctx
    finally:
        con.close()


# ── Classificatore keyword (RESTA — per routing + fallback) ───
PATTERNS = {
    'NEGATIVE': {
        'exact': [
            'no grazie', 'non mi interessa', 'non interessa', 'non ho interesse',
            'smettila', 'non scrivere più', 'non scrivermi', 'blocca',
            'stop', 'rimuovi', 'cancella', 'non voglio', 'non contattarmi',
            'ma chi sei', 'ma chi ti conosce', 'vaffanculo', 'vai a cagare',
            'spam', 'segnalo', 'segnalato',
            'non mi convince', 'lascia perdere', 'lasci perdere',
        ],
        'weight': 1.0,
    },
    'POSITIVE': {
        'exact': [
            'sì', 'certo', 'ok', 'perfetto', 'interessante',
            'mi interessa', 'procedi', 'dimmi', 'dimmi di più',
            'manda', 'mandami', 'inviami', 'fammi vedere', 'vediamo',
            'possiamo', 'volentieri', 'ottimo', 'bene', 'va bene',
            'quando possiamo', 'ci sto', 'proviamo', 'facciamo',
            'mi piace', 'buona idea', 'perché no', 'sono curioso',
            'interessato', 'parliamone', 'mi dica', 'avanti',
            'okay', 'okey', 'va benissimo', 'assolutamente',
            'mandi pure', 'mi faccia sapere', 'aspetto',
        ],
        'weight': 0.85,
    },
    'CURIOSITY': {
        'exact': [
            'chi sei', 'chi è lei', 'come hai avuto', 'come ha avuto',
            'da dove', 'sei di', 'è di', 'quale azienda', 'che azienda',
            'come funziona', 'spiegami', 'mi spieghi', 'mi spiega',
            "cos'è", "che cos'è", 'come mai', 'dove hai preso',
            'dove ha preso', 'il mio numero', 'come ha trovato',
            'ma cosa fate', 'che servizio', 'in cosa consiste',
            'che tipo di', 'mi dica di più', 'vorrei capire',
        ],
        'weight': 0.80,
    },
    'OBJ-1': {
        'exact': [
            'ho già', 'uso già', 'lavoro già', 'abbiamo già',
            'ho i miei', 'canali miei', 'faccio già import',
            'importo già', 'ho il mio fornitore', 'sono a posto',
            'non ho bisogno', 'non mi serve', 'non ne ho bisogno',
        ],
        'weight': 0.90,
    },
    'OBJ-2': {
        'exact': [
            'troppo caro', 'il prezzo', 'la fee', 'quanto costa',
            'quanto viene', 'quanto mi costa', 'conviene',
            'non conviene', 'costoso', 'caro', 'economico',
            'risparmio', 'sconto', 'negoziare', 'trattare',
            'margine', 'guadagno', 'ci guadagno', 'costa',
        ],
        'weight': 0.90,
    },
    'OBJ-3': {
        'exact': [
            'non ho tempo', 'occupato', 'richiamo', 'ti richiamo',
            'la richiamo', 'adesso no', 'ora no', 'più tardi',
            'settimana prossima', 'ne parliamo dopo', 'sono fuori',
            'sono in fiera', 'periodo pieno', 'momento sbagliato',
        ],
        'weight': 0.85,
    },
    'OBJ-4': {
        'exact': [
            'garanzie', 'che garanzia', 'come mi tutelo',
            'e se non va bene', 'se non va bene', 'non va bene',
            'e se il veicolo', 'se il veicolo', 'fregatura',
            'sicurezza', 'fidarmi', 'mi fido', 'non mi fido',
            'referenze', 'altri clienti', 'chi ha lavorato',
            'documenti', 'contratto', 'tutela', 'assicurazione',
        ],
        'weight': 0.85,
    },
    'OBJ-5': {
        'exact': [
            'devo sentire', 'devo chiedere', 'mio socio', 'il titolare',
            'il proprietario', 'il capo', 'devo parlare con',
            'non decido io', 'non sono io che', 'aspetta che chiedo',
            'ne parlo con', 'sento il mio', 'devo confrontarmi',
        ],
        'weight': 0.90,
    },
}


def classify_message(body: str) -> dict:
    b_lower = body.lower().strip()
    words = b_lower.split()
    if len(words) <= 1:
        if b_lower in ('ok', 'sì', 'si', 'certo', 'perfetto', 'ottimo', 'bene'):
            return {'type': 'POSITIVE', 'confidence': 0.90, 'method': 'short_match'}
        if b_lower in ('no', 'stop'):
            return {'type': 'NEGATIVE', 'confidence': 0.95, 'method': 'short_match'}
        if '?' in body:
            return {'type': 'CURIOSITY', 'confidence': 0.75, 'method': 'question_mark'}

    negated_positives = [
        'non va bene', 'non mi piace', 'non mi interessa',
        'non ho interesse', 'non voglio', 'non mi convince',
    ]
    has_negated = any(np in b_lower for np in negated_positives)

    scores = {}
    for category, config in PATTERNS.items():
        score = 0
        matched = []
        for kw in config['exact']:
            if kw not in b_lower:
                continue
            if category == 'POSITIVE' and has_negated:
                if any(kw in np and np in b_lower for np in negated_positives):
                    continue
            score += config['weight']
            matched.append(kw)
        if score > 0:
            scores[category] = {'score': score, 'matched': matched}

    if not scores:
        if '?' in body:
            return {'type': 'CURIOSITY', 'confidence': 0.60, 'method': 'question_fallback'}
        return {'type': 'UNKNOWN', 'confidence': 0.0, 'method': 'no_match'}

    if 'NEGATIVE' in scores:
        return {'type': 'NEGATIVE', 'confidence': 0.95, 'method': 'keyword',
                'matched': scores['NEGATIVE']['matched']}

    best = max(scores.items(), key=lambda x: x[1]['score'])
    category = best[0]
    matched = best[1]['matched']

    if category.startswith('OBJ-'):
        return {'type': 'OBJECTION', 'obj_code': category,
                'confidence': 0.85, 'method': 'keyword', 'matched': matched}

    return {'type': category, 'confidence': 0.85, 'method': 'keyword',
            'matched': matched}


# ── Salva pending reply ──────────────────────────────────────
def save_pending_reply(db_path: str, dealer_id: str, dealer_name: str,
                       inbound_msg_id: str, reply: dict):
    reply_id = f"reply_{uuid.uuid4().hex[:8]}"
    con = sqlite3.connect(db_path, timeout=10)
    try:
        con.execute("""
            INSERT INTO pending_replies
                (id, dealer_id, dealer_name, reply_text, reply_label, approved, sent)
            VALUES (?, ?, ?, ?, ?, NULL, 0)
        """, [reply_id, dealer_id, dealer_name, reply['text'], reply['label']])
        con.commit()
        return reply_id
    except Exception as e:
        print(f'[ERROR] save_pending_reply: {e}')
        return reply_id
    finally:
        con.close()


# ── Validazione di sicurezza ─────────────────────────────────
FORBIDDEN_TERMS = [
    'carfax', 'cove engine', 'claude', 'anthropic', 'openai', 'chatgpt',
    'intelligenza artificiale', 'machine learning', 'algoritmo',
    'embedding', 'vincario', 'händlergarantie',
    'non possiamo fatturare',
]

# Termini che vanno matchati come parola intera (no substring)
FORBIDDEN_WORDS_EXACT = ['cove', 'gpt', 'rag', 'bot', 'ai']

def validate_response(text: str) -> dict:
    """Valida la risposta prima dell'auto-invio. Ritorna {safe, reason}."""
    import re
    t_lower = text.lower()

    # Check termini vietati (substring)
    for term in FORBIDDEN_TERMS:
        if term in t_lower:
            return {'safe': False, 'reason': f'Termine vietato: "{term}"'}

    # Check parole esatte (word boundary)
    for word in FORBIDDEN_WORDS_EXACT:
        if re.search(r'\b' + re.escape(word) + r'\b', t_lower):
            return {'safe': False, 'reason': f'Parola vietata: "{word}"'}

    # Check fee corretta
    if '€' in text and '1.000' not in text and '1000' not in text:
        # Menziona un importo ma non è €1.000
        import re
        fees = re.findall(r'€\s*[\d.]+', text)
        for f in fees:
            if '1.000' not in f and '1000' not in f:
                return {'safe': False, 'reason': f'Fee sospetta: {f}'}

    # Check lunghezza
    if len(text) > 1200:
        return {'safe': False, 'reason': f'Troppo lungo: {len(text)} chars'}

    if len(text) < 20:
        return {'safe': False, 'reason': f'Troppo corto: {len(text)} chars'}

    return {'safe': True, 'reason': 'OK'}


# ── Auto-approvazione + invio schedulato ─────────────────────
def auto_approve_and_send(db_path, reply_id, dealer, reply_text):
    """Auto-approva e schedula invio con anti-ban sleep."""
    import random, subprocess

    phone = (dealer.get('phone_number', '') or '').replace('+', '').replace(' ', '')
    if not phone:
        print(f'[WARN] No phone for auto-send {reply_id}')
        return False

    wa_id = f'{phone}@c.us'
    sleep_s = random.randint(90, 720)

    # Approva nel DB
    con = sqlite3.connect(db_path, timeout=10)
    con.execute('UPDATE pending_replies SET approved = 1 WHERE id = ?', [reply_id])
    con.commit()
    con.close()

    # Schedula invio in background
    wa_sender = os.path.expanduser(
        '~/Documents/app-antigravity-auto/wa-sender/send_message.js')
    client_id = os.environ.get('WA_CLIENT_ID', 'argos-business')

    env = os.environ.copy()
    env['CLIENT_ID'] = client_id

    safe_text = reply_text.replace('"', "'")
    subprocess.Popen(
        ['bash', '-c',
         f'sleep {sleep_s} && node {wa_sender} "{wa_id}" "{safe_text}" '
         f'&& python3 -c "import sqlite3; c=sqlite3.connect(\'{db_path}\'); '
         f'c.execute(\'UPDATE pending_replies SET sent=1 WHERE id=\\\'{reply_id}\\\'\'); '
         f'c.commit(); c.close()"'],
        env=env, close_fds=True
    )

    print(f'[AUTO] Approvata + schedulata reply {reply_id} — invio tra {sleep_s}s')
    return True


# ── Telegram notification ────────────────────────────────────
def send_telegram_notification(dealer, msg_body, classification,
                               best_reply, reply_id, llm_cost_info='',
                               auto_status='', sleep_s=0):
    """Notifica Telegram — informativa (il sistema ha già approvato)."""
    if not TELEGRAM_BOT_TOKEN:
        print('[WARN] ARGOS_TELEGRAM_TOKEN non impostato')
        return

    import urllib.request, urllib.parse

    name     = dealer.get('dealer_name', 'Sconosciuto') if dealer else 'Sconosciuto'
    persona  = dealer.get('persona_type', '?') if dealer else '?'
    step     = dealer.get('current_step', '?') if dealer else '?'
    cls_type = classification.get('type', 'UNKNOWN')
    cls_conf = int(classification.get('confidence', 0) * 100)
    obj_code = classification.get('obj_code', '')

    lines = [
        f"🧠 *RISPOSTA DEALER — {now_it()}*",
        f"",
        f"👤 *{name}* | 🎭 {persona} | Step: {step}",
        f"📊 `{cls_type}` {f'({obj_code})' if obj_code else ''} — {cls_conf}%",
        f"",
        f"💬 *Messaggio ricevuto:*",
        f"_{msg_body[:400]}_",
        f"",
        f"━━━ RISPOSTA AUTO-APPROVATA ━━━",
        f"{best_reply['text'][:500]}",
        f"",
        f"{auto_status}",
        f"`/rifiuta {reply_id}` per bloccare invio",
        f"",
    ]

    if llm_cost_info:
        lines.append(f"💰 _{llm_cost_info}_")

    text = '\n'.join(lines)

    # Fallback: se Markdown fallisce, invia senza parse_mode
    import urllib.request, urllib.parse as uparse
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    for parse_mode in ['Markdown', '']:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        data = uparse.urlencode(payload).encode()
        try:
            req = urllib.request.Request(url, data=data, method='POST')
            resp = urllib.request.urlopen(req, timeout=15)
            print(f'[INFO] Telegram notification inviata: {resp.status}')
            return
        except Exception as e:
            if 'Bad Request' in str(e) and parse_mode == 'Markdown':
                print(f'[WARN] Markdown failed, retrying plain text')
                continue
            print(f'[ERROR] Telegram send failed: {e}')
            return


def send_telegram_hold(dealer, msg_body, classification,
                       candidates, reply_ids, hold_reason, llm_cost_info=''):
    """Notifica Telegram — HOLD, richiede intervento manuale."""
    if not TELEGRAM_BOT_TOKEN:
        return

    import urllib.request, urllib.parse

    name     = dealer.get('dealer_name', 'Sconosciuto') if dealer else 'Sconosciuto'
    persona  = dealer.get('persona_type', '?') if dealer else '?'
    cls_type = classification.get('type', 'UNKNOWN')
    obj_code = classification.get('obj_code', '')

    lines = [
        f"⚠️ *HOLD — INTERVENTO RICHIESTO*",
        f"",
        f"👤 *{name}* | 🎭 {persona}",
        f"📊 `{cls_type}` {f'({obj_code})' if obj_code else ''}",
        f"🔒 Motivo hold: _{hold_reason}_",
        f"",
        f"💬 *Messaggio dealer:*",
        f"_{msg_body[:400]}_",
        f"",
    ]

    for i, (reply, rid) in enumerate(zip(candidates, reply_ids), 1):
        lines += [
            f"━━━ SUGGERIMENTO #{i} — `{reply['label']}` ━━━",
            f"{reply['text'][:500]}",
            f"`/approva {rid}` | `/modifica {rid} testo`",
            f"",
        ]

    if llm_cost_info:
        lines.append(f"💰 _{llm_cost_info}_")

    text = '\n'.join(lines)

    import urllib.request, urllib.parse as uparse
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    for parse_mode in ['Markdown', '']:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
        if parse_mode:
            payload['parse_mode'] = parse_mode
        data = uparse.urlencode(payload).encode()
        try:
            req = urllib.request.Request(url, data=data, method='POST')
            urllib.request.urlopen(req, timeout=15)
            print(f'[INFO] Telegram hold inviata')
            return
        except Exception as e:
            if 'Bad Request' in str(e) and parse_mode == 'Markdown':
                continue
            print(f'[ERROR] Telegram hold failed: {e}')
            return


# ── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msg-id',     required=True)
    parser.add_argument('--msg-body',   required=True)
    parser.add_argument('--dealer-id',  required=True)
    parser.add_argument('--dealer-name', default='Sconosciuto')
    parser.add_argument('--persona',    default='DEFAULT')
    parser.add_argument('--step',       default='UNKNOWN')
    parser.add_argument('--db-path',    required=True)
    parser.add_argument('--time-ctx',   default='{}')
    args = parser.parse_args()

    print(f'[{now_it()}] Analyzer avviato per msg_id={args.msg_id}')
    print(f'  Dealer: {args.dealer_name} | Persona: {args.persona} | Step: {args.step}')
    print(f'  Messaggio: {args.msg_body[:100]}...')

    # 1. Carica contesto dealer
    dealer = load_dealer_context(args.db_path, args.dealer_id)
    if not dealer:
        dealer = {
            'dealer_id':    args.dealer_id,
            'dealer_name':  args.dealer_name,
            'persona_type': args.persona,
            'current_step': args.step,
        }

    # 2. Classifica messaggio
    classification = classify_message(args.msg_body)
    print(f'  Classificazione: {classification}')

    # 3. Genera risposte via LLM
    candidates = []
    llm_cost_info = ''
    cls_type = classification.get('type', 'UNKNOWN')

    if cls_type == 'NEGATIVE':
        # NEGATIVE → NON rispondere, chiudi dealer
        con = sqlite3.connect(args.db_path, timeout=10)
        con.execute("""
            UPDATE conversations SET current_step = 'CLOSED_NO', analyzed_at = datetime('now')
            WHERE dealer_id = ?
        """, [args.dealer_id])
        con.commit()
        con.close()

        # Solo notifica, nessuna risposta
        if TELEGRAM_BOT_TOKEN:
            import urllib.request, urllib.parse
            text = (
                f"🚫 *DEALER CHIUSO — NEGATIVE*\n\n"
                f"👤 *{dealer.get('dealer_name', '?')}*\n"
                f"💬 _{args.msg_body[:300]}_\n\n"
                f"_Nessuna risposta inviata. Dealer chiuso con CLOSED\\_NO._"
            )
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
            data = urllib.parse.urlencode(payload).encode()
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
            try:
                req = urllib.request.Request(url, data=data, method='POST')
                urllib.request.urlopen(req, timeout=15)
            except Exception:
                pass

        print(f'[{now_it()}] NEGATIVE — dealer chiuso, nessuna risposta.')
        return

    if OPENROUTER_API_KEY:
        msg_history = dealer.get('message_history', [])
        user_prompt = build_user_prompt(dealer, args.msg_body, classification, msg_history)

        print(f'  Chiamata LLM: {OPENROUTER_MODEL}...')
        result = call_llm(SYSTEM_PROMPT, user_prompt)

        if result.get('text'):
            candidates = parse_llm_responses(result['text'])
            usage = result.get('usage', {})
            model = result.get('model', OPENROUTER_MODEL)

            if usage:
                track_cost(args.db_path, model, usage, args.dealer_id)
                in_tok = usage.get('prompt_tokens', 0)
                out_tok = usage.get('completion_tokens', 0)
                llm_cost_info = f'{model}: {in_tok}+{out_tok} tok'

            print(f'  LLM OK: {len(candidates)} risposte generate')
        else:
            print(f'  LLM FALLBACK: {result.get("error", "unknown")}')

    # Fallback template
    if not candidates:
        candidates = [{
            'label': 'TEMPLATE_FALLBACK',
            'text': "Grazie per il riscontro.\n"
                    "Le mando i dettagli completi entro 48h — "
                    "report DAT e ispezione DEKRA inclusi.\n"
                    "Zero anticipi, paga solo a veicolo approvato.\n— Luca"
        }]
        llm_cost_info = 'fallback template'

    # 4. Salva nel DB
    reply_ids = [
        save_pending_reply(args.db_path, args.dealer_id, args.dealer_name,
                           args.msg_id, r)
        for r in candidates
    ]

    # 5. AUTO-APPROVAZIONE con validazione di sicurezza
    best = candidates[0]  # Prende RISPOSTA_A (la migliore)
    best_id = reply_ids[0]

    validation = validate_response(best['text'])

    if cls_type == 'UNKNOWN':
        # UNKNOWN → HOLD, serve intervento umano
        send_telegram_hold(dealer, args.msg_body, classification,
                           candidates, reply_ids,
                           'Messaggio non classificato — richiede review',
                           llm_cost_info)
        print(f'[HOLD] UNKNOWN — attesa intervento manuale')

    elif not validation['safe']:
        # Validazione fallita → HOLD
        send_telegram_hold(dealer, args.msg_body, classification,
                           candidates, reply_ids,
                           f'Validazione fallita: {validation["reason"]}',
                           llm_cost_info)
        print(f'[HOLD] Validazione fallita: {validation["reason"]}')

    else:
        # SAFE → auto-approva e invia
        import random
        sleep_s = random.randint(90, 720)
        success = auto_approve_and_send(
            args.db_path, best_id, dealer, best['text'])

        status = (f"✅ *AUTO-APPROVATA* — invio tra ~{sleep_s // 60}min\n"
                  f"_Usa `/rifiuta {best_id}` entro {sleep_s // 60}min per bloccare_"
                  if success else "❌ Auto-invio fallito — approva manualmente")

        send_telegram_notification(
            dealer, args.msg_body, classification,
            best, best_id, llm_cost_info, status, sleep_s)

        print(f'[AUTO] Risposta auto-approvata, invio tra {sleep_s}s')

    print(f'[{now_it()}] Analyzer completato. Reply IDs: {reply_ids}')


if __name__ == '__main__':
    main()
