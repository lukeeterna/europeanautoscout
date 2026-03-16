#!/usr/bin/env python3
"""
response-analyzer.py — ARGOS™ Response Intelligence
CoVe 2026 | Enterprise Grade | S58 Rewrite

RESPONSABILITÀ:
  Riceve un messaggio in arrivo da un dealer, carica il contesto completo
  dal DB, classifica la risposta, genera 2 candidate replies calibrate
  sull'archetipo, invia a Telegram per approvazione umana.

  Chiamato in modo asincrono da wa-daemon.js.
  Non blocca mai il daemon.
  ZERO dipendenze LLM — classificazione keyword + template.

DIPENDENZE: duckdb, urllib (stdlib)
"""

import argparse
import duckdb
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
TIMEZONE           = 'Europe/Rome'

# ── ARGOS Business Constants ──────────────────────────────
ARGOS_FEE = '€1.000'
ARGOS_FEE_RANGE = '€800-1.200'
ARGOS_PERSONA = 'Luca Ferretti'
ARGOS_BRAND = 'ARGOS Automotive'


def now_it() -> str:
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo('Europe/Rome')
        return datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
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
        try:
            msgs = con.execute("""
                SELECT direction, body, timestamp_it
                FROM messages
                WHERE dealer_id = ?
                ORDER BY timestamp_it DESC
                LIMIT 5
            """, [dealer_id]).fetchall()
            ctx['message_history'] = [
                {'direction': r[0], 'body': r[1], 'ts': str(r[2])} for r in msgs
            ]
        except Exception:
            ctx['message_history'] = []
        return ctx
    finally:
        con.close()


# ── Classificatore keyword robusto (ZERO LLM) ────────────────
# Ordine: NEGATIVE > OBJECTION > POSITIVE > CURIOSITY > UNKNOWN
# Ogni pattern ha peso. Il tipo con score più alto vince.

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
    'OBJ-1': {  # Ho già fornitori
        'exact': [
            'ho già', 'uso già', 'lavoro già', 'abbiamo già',
            'ho i miei', 'canali miei', 'faccio già import',
            'importo già', 'ho il mio fornitore', 'sono a posto',
            'non ho bisogno', 'non mi serve', 'non ne ho bisogno',
        ],
        'weight': 0.90,
    },
    'OBJ-2': {  # Prezzo/fee
        'exact': [
            'troppo caro', 'il prezzo', 'la fee', 'quanto costa',
            'quanto viene', 'quanto mi costa', 'conviene',
            'non conviene', 'costoso', 'caro', 'economico',
            'risparmio', 'sconto', 'negoziare', 'trattare',
            'margine', 'guadagno', 'ci guadagno', 'costa',
        ],
        'weight': 0.90,
    },
    'OBJ-3': {  # Tempo
        'exact': [
            'non ho tempo', 'occupato', 'richiamo', 'ti richiamo',
            'la richiamo', 'adesso no', 'ora no', 'più tardi',
            'settimana prossima', 'ne parliamo dopo', 'sono fuori',
            'sono in fiera', 'periodo pieno', 'momento sbagliato',
        ],
        'weight': 0.85,
    },
    'OBJ-4': {  # Garanzie/fiducia/rischio
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
    'OBJ-5': {  # Devo sentire socio/titolare
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
    """
    Classifica il tipo di risposta con keyword matching robusto.
    Zero dipendenze LLM. Fallback a UNKNOWN con flag human-needed.
    """
    b_lower = body.lower().strip()

    # Messaggi di 1 parola — check speciale
    words = b_lower.split()
    if len(words) <= 1:
        if b_lower in ('ok', 'sì', 'si', 'va bene', 'certo', 'perfetto', 'ottimo', 'bene',
                       'si grazie', 'sì grazie', 'ok grazie', 'certo grazie'):
            return {'type': 'POSITIVE', 'confidence': 0.90, 'method': 'short_match'}
        if b_lower in ('no', 'no grazie', 'stop'):
            return {'type': 'NEGATIVE', 'confidence': 0.95, 'method': 'short_match'}
        if '?' in body:
            return {'type': 'CURIOSITY', 'confidence': 0.75, 'method': 'question_mark'}

    # Negation check: "non va bene" != "va bene"
    negated_positives = [
        'non va bene', 'non mi piace', 'non mi interessa',
        'non ho interesse', 'non voglio', 'non mi convince',
    ]
    has_negated_positive = any(np in b_lower for np in negated_positives)

    # Score-based matching
    scores = {}
    for category, config in PATTERNS.items():
        score = 0
        matched = []
        for kw in config['exact']:
            if kw not in b_lower:
                continue
            # Skip positive matches if negation detected
            if category == 'POSITIVE' and has_negated_positive:
                negated = False
                for np in negated_positives:
                    if kw in np and np in b_lower:
                        negated = True
                        break
                if negated:
                    continue
            score += config['weight']
            matched.append(kw)
        if score > 0:
            scores[category] = {'score': score, 'matched': matched}

    if not scores:
        # Nessun match — check se contiene domanda
        if '?' in body:
            return {'type': 'CURIOSITY', 'confidence': 0.60, 'method': 'question_fallback'}
        return {'type': 'UNKNOWN', 'confidence': 0.0, 'method': 'no_match',
                'note': 'HUMAN_NEEDED — nessun pattern riconosciuto'}

    # NEGATIVE ha sempre priorità assoluta
    if 'NEGATIVE' in scores:
        return {'type': 'NEGATIVE', 'confidence': 0.95, 'method': 'keyword',
                'matched': scores['NEGATIVE']['matched']}

    # Tra i rimanenti, prendi il più alto
    best = max(scores.items(), key=lambda x: x[1]['score'])
    category = best[0]
    matched = best[1]['matched']

    # Map OBJ-X → OBJECTION type
    if category.startswith('OBJ-'):
        return {'type': 'OBJECTION', 'obj_code': category,
                'confidence': 0.85, 'method': 'keyword', 'matched': matched}

    return {'type': category, 'confidence': 0.85, 'method': 'keyword',
            'matched': matched}


# ── Template risposte per archetipo ──────────────────────────
# REGOLE IMMUTABILI:
#   - Fee: €1.000 (MAI €400, MAI "non possiamo fatturare")
#   - MAI "CarFax EU" → "report DAT" / "DAT Fahrzeughistorie"
#   - MAI "Händlergarantie" → "garanzia costruttore UE"
#   - MAI "Vincario" → "report DAT"
#   - Talk track: "€1.000 fisso vs €7-10k margine nascosto dei trader"
#   - MAI menzionare: CoVe, Claude, AI, Anthropic, RAG, embedding

REPLY_TEMPLATES = {
    'POSITIVE': {
        'RAGIONIERE': [
            ("ACK_DATA",
             "Grazie per il riscontro.\n"
             "Le preparo i numeri concreti: veicolo EU franco partenza, "
             "costi trasporto e immatricolazione, confronto prezzo IT.\n"
             "Entro 48h ha tutto documentato.\n— Luca"),
            ("ACK_SPECIFIC",
             "Perfetto.\nHa un modello specifico che sta cercando? "
             "Così le faccio i conti precisi: prezzo EU, margine netto, "
             "report DAT incluso.\n— Luca"),
        ],
        'BARONE': [
            ("ACK_RESPECT",
             "La ringrazio, [Nome].\nLe preparo un'analisi su misura "
             "per il suo segmento — niente proposte generiche.\n"
             "La ricontatto appena ho qualcosa di concreto.\n— Luca"),
            ("ACK_EXCLUSIVE",
             "Ottimo, [Nome].\nProcedo con una selezione riservata "
             "e la aggiorno personalmente.\n— Luca"),
        ],
        'PERFORMANTE': [
            ("ACK_FAST",
             "Perfetto.\n48h: scheda tecnica completa + breakdown margini.\n"
             "Report DAT e ispezione DEKRA inclusi. Pronti.\n— Luca"),
            ("ACK_ACTION",
             "Ricevuto. Mi dica modello e fascia prezzo — "
             "le mando le opzioni disponibili entro domani.\n— Luca"),
        ],
        'NARCISO': [
            ("ACK_PREMIUM",
             "[Nome], ottimo.\nLe invio un'anteprima riservata — "
             "lavoriamo con un dealer selezionato per area.\n"
             "La ricontatto subito.\n— Luca"),
        ],
        'TECNICO': [
            ("ACK_TECH",
             "Grazie.\nLe mando la documentazione completa: "
             "report DAT con storico tagliandi verificato, "
             "ispezione DEKRA, km certificati.\n"
             "Ha un modello o motorizzazione specifica in mente?\n— Luca"),
        ],
        'RELAZIONALE': [
            ("ACK_WARM",
             "Grazie, [Nome], fa piacere.\n"
             "Mi dica pure con calma cosa sta cercando — "
             "ci lavoriamo insieme senza fretta.\n— Luca"),
        ],
        'CONSERVATORE': [
            ("ACK_SAFE",
             "Grazie per la fiducia.\nLe mando tutto documentato: "
             "nessuna sorpresa, verifica DAT e DEKRA incluse.\n"
             "Zero anticipi — paga solo se il veicolo la convince.\n— Luca"),
        ],
        'DELEGATORE': [
            ("ACK_EASY",
             "Perfetto, [Nome].\nGestisco tutto io — lei mi dice "
             "modello e budget, io le porto il veicolo verificato.\n"
             "La aggiorno passo per passo.\n— Luca"),
        ],
        'OPPORTUNISTA': [
            ("ACK_DEAL",
             "Ottimo.\nLe mostro subito dove sta il margine: "
             "prezzo EU vs prezzo IT dello stesso veicolo.\n"
             "I numeri parlano da soli.\n— Luca"),
        ],
        'VISIONARIO': [
            ("ACK_MODEL",
             "Interessante che ci stia pensando.\n"
             "Il nostro modello è diverso: fee fissa trasparente, "
             "zero margini nascosti, verifica indipendente.\n"
             "Le mando un caso studio concreto.\n— Luca"),
        ],
        'DEFAULT': [
            ("ACK_GENERIC",
             "Grazie per il riscontro.\n"
             "Le mando i dettagli completi entro 48h — "
             "report DAT e ispezione DEKRA inclusi.\n"
             "Zero anticipi, paga solo a veicolo approvato.\n— Luca"),
        ],
    },

    'CURIOSITY': {
        'DEFAULT': [
            ("ID_FULL",
             "Certo, [Nome].\n"
             "Sono Luca Ferretti di ARGOS Automotive — seleziono veicoli premium "
             "verificati in Germania, Belgio e Olanda per concessionari italiani.\n\n"
             "Come funziona:\n"
             "• Lei mi dice modello e fascia — io cerco nei mercati EU\n"
             "• Ogni veicolo ha report DAT + ispezione DEKRA\n"
             "• Fee fissa {fee} a veicolo consegnato — zero anticipi\n"
             "• Se il veicolo non la convince: non paga nulla\n\n"
             "La differenza rispetto ai trader? Loro nascondono €7-10.000 "
             "nel prezzo. Noi mettiamo tutto in chiaro.\n"
             "Vuole che le faccia un esempio su un modello specifico?\n— Luca".format(fee=ARGOS_FEE)),
            ("ID_SHORT",
             "Luca Ferretti, ARGOS Automotive.\n"
             "Trovo veicoli premium EU verificati per dealer italiani.\n"
             "Fee fissa {fee} — paga solo a veicolo consegnato e approvato.\n"
             "Report DAT + DEKRA inclusi.\n"
             "Posso mostrarle un esempio concreto?\n— Luca".format(fee=ARGOS_FEE)),
        ],
    },

    'OBJECTION': {
        'OBJ-1': {  # Ho già fornitori
            'RAGIONIERE': [
                ("OBJ1_DATA",
                 "Non le chiedo di cambiare fornitori — capisco perfettamente.\n\n"
                 "Una cosa concreta: i trader tradizionali incorporano €7-10.000 "
                 "di margine nel prezzo senza dichiararlo.\n"
                 "Con noi la fee è {fee} fissa e trasparente — "
                 "il risparmio netto va tutto a lei.\n\n"
                 "Le faccio un confronto su un modello che tratta? "
                 "Prezzo EU vs prezzo del suo fornitore attuale.\n— Luca".format(fee=ARGOS_FEE)),
            ],
            'DEFAULT': [
                ("OBJ1_GENERIC",
                 "Capisco — e non le chiedo di cambiare nulla.\n"
                 "Le offro un'opzione in più: veicoli con report DAT verificato "
                 "e fee fissa {fee} dichiarata.\n"
                 "Vale confrontare? Un esempio su un modello specifico "
                 "non costa nulla.\n— Luca".format(fee=ARGOS_FEE)),
            ],
        },
        'OBJ-2': {  # Prezzo/fee
            'RAGIONIERE': [
                ("OBJ2_CALC",
                 "I numeri concreti:\n"
                 "• Un trader prende €7-10.000 di margine nascosto per auto\n"
                 "• La nostra fee: {fee} fissa, dichiarata prima\n"
                 "• Differenza netta per lei: €6-9.000 in più di margine per veicolo\n\n"
                 "Su un lotto di 5 auto sono €30-45.000 di differenza.\n"
                 "Vuole che le faccia i conti su un modello preciso?\n— Luca".format(fee=ARGOS_FEE)),
            ],
            'DEFAULT': [
                ("OBJ2_TRANSPARENT",
                 "La nostra fee è {fee} a veicolo, tutto incluso.\n"
                 "Nessun anticipo — paga solo quando il veicolo è da lei, "
                 "verificato e approvato.\n\n"
                 "Per confronto: i trader nascondono €7-10.000 nel prezzo.\n"
                 "Con noi risparmia e sa esattamente quanto spende.\n"
                 "Posso mostrarle un esempio reale?\n— Luca".format(fee=ARGOS_FEE)),
            ],
        },
        'OBJ-3': {  # Tempo
            'DEFAULT': [
                ("OBJ3_ASYNC",
                 "Nessun problema — rispetto il suo tempo.\n"
                 "Le mando un riepilogo di 1 pagina via WhatsApp: "
                 "lo guarda quando ha 2 minuti.\n"
                 "Non c'è urgenza — mi faccia sapere lei.\n— Luca"),
            ],
        },
        'OBJ-4': {  # Garanzie/fiducia
            'DEFAULT': [
                ("OBJ4_RISK",
                 "Funziona a rischio zero per lei:\n"
                 "• Non paga nulla fino alla consegna fisica\n"
                 "• Report DAT (storico veicolo) + ispezione DEKRA prima dell'acquisto\n"
                 "• Garanzia costruttore UE valida in Italia\n"
                 "• Fee {fee} solo a veicolo approvato da lei\n"
                 "• Se non corrisponde alle specifiche: non deve nulla\n\n"
                 "Posso mandarle un esempio di report DAT?\n— Luca".format(fee=ARGOS_FEE)),
            ],
        },
        'OBJ-5': {  # Socio/titolare
            'DEFAULT': [
                ("OBJ5_ESCALATE",
                 "Naturalmente — è la cosa giusta da fare.\n"
                 "Le preparo un riepilogo di 1 pagina da girare direttamente: "
                 "come funziona, fee {fee}, report DAT + DEKRA, zero anticipi.\n"
                 "Lo mando a lei o preferisce che lo invii al titolare?\n— Luca".format(fee=ARGOS_FEE)),
            ],
        },
        'OBJ-UNKNOWN': {
            'DEFAULT': [
                ("OBJ_UNKNOWN",
                 "⚠️ OBIEZIONE NON CATALOGATA — RICHIEDE APPROVAZIONE MANUALE\n\n"
                 "Messaggio dealer:\n«[MSG_BODY]»\n\n"
                 "Suggerimento: rispondi con empatia, riporta al valore concreto "
                 "(fee {fee} fissa vs €7-10k nascosti).".format(fee=ARGOS_FEE)),
            ],
        },
    },

    'NEGATIVE': {
        'DEFAULT': [
            ("CLOSE_GRACEFUL",
             "— AZIONE: Non rispondere. Dealer chiuso con CLOSED_NO.\n"
             "Porta aperta: il dealer potrebbe tornare in futuro."),
        ],
    },

    'UNKNOWN': {
        'DEFAULT': [
            ("UNKNOWN_HUMAN",
             "⚠️ MESSAGGIO NON CLASSIFICATO — APPROVAZIONE MANUALE RICHIESTA\n\n"
             "Messaggio dealer:\n«[MSG_BODY]»\n\n"
             "Il sistema non ha riconosciuto il pattern. "
             "Scrivi la risposta manualmente con /modifica."),
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
    elif msg_type == 'UNKNOWN':
        templates = REPLY_TEMPLATES['UNKNOWN']['DEFAULT']
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
        templates = REPLY_TEMPLATES['UNKNOWN']['DEFAULT']

    # Personalizza con nome dealer e corpo messaggio
    name = '[Nome]'
    if dealer:
        full_name = dealer.get('dealer_name', '')
        if full_name:
            # Usa il nome dell'azienda (primo token significativo)
            parts = full_name.replace('Srl', '').replace('S.r.l.', '').replace('srl', '').strip().split()
            name = parts[0] if parts else full_name

    results = []
    for label, text in templates:
        personalized = (
            text
            .replace('[Nome]', name)
            .replace('[MSG_BODY]', msg_body[:300])
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
        ('POSITIVE', None):    'Commitment progressivo → micro-sì verso azione concreta',
        ('CURIOSITY', None):   'Reciprocità → dai valore (info concreta) prima di chiedere',
        ('NEGATIVE', None):    'STOP — porta aperta implicita, zero insistenza',
        ('UNKNOWN', None):     'HUMAN NEEDED — analizza il contesto e rispondi manualmente',
        ('OBJECTION', 'OBJ-1'): 'Social proof + reciprocità → "non sostituisco, aggiungo"',
        ('OBJECTION', 'OBJ-2'): 'Ancoraggio numerico → €1.000 vs €7-10k nascosti',
        ('OBJECTION', 'OBJ-3'): 'Coerenza + rispetto → "quando ha tempo, zero urgenza"',
        ('OBJECTION', 'OBJ-4'): 'Authority → DAT + DEKRA + garanzia costruttore UE',
        ('OBJECTION', 'OBJ-5'): 'Facilitazione → prepara materiale per il decisore',
    }
    for (t, o), note in notes.items():
        if t == msg_type and (o is None or o == obj_code):
            return note

    # Nota specifica per archetipo
    persona_notes = {
        'RAGIONIERE':    'Dati concreti, numeri precisi, zero fuffa',
        'BARONE':        'Rispetto, esclusività, "su misura per lei"',
        'PERFORMANTE':   'Velocità, risultati, "48h"',
        'NARCISO':       'Esclusività, "selezionato", "riservato"',
        'TECNICO':       'Documentazione, specifiche, report DAT',
        'RELAZIONALE':   'Calore, "ci lavoriamo insieme", zero pressione',
        'CONSERVATORE':  'Sicurezza, "nessuna sorpresa", garanzie',
        'DELEGATORE':    'Semplicità, "gestisco tutto io"',
        'OPPORTUNISTA':  'Margine concreto, "i numeri parlano"',
        'VISIONARIO':    'Modello innovativo, trasparenza come valore',
    }
    return persona_notes.get(persona, 'Calibrazione archetipo standard')


def save_pending_reply(db_path: str, dealer_id: str, dealer_name: str,
                       inbound_msg_id: str, reply: dict, time_ctx: dict):
    """Salva reply candidata nel DB per tracking approvazione."""
    reply_id = f"reply_{uuid.uuid4().hex[:8]}"
    con = duckdb.connect(db_path)
    try:
        con.execute("""
            INSERT INTO pending_replies
                (id, dealer_id, dealer_name,
                 reply_text, reply_label,
                 approved, sent)
            VALUES (?, ?, ?, ?, ?, NULL, FALSE)
        """, [
            reply_id, dealer_id, dealer_name,
            reply['text'], reply['label'],
        ])
        con.commit()
        return reply_id
    except Exception as e:
        print(f'[ERROR] save_pending_reply: {e}')
        return reply_id
    finally:
        con.close()


def send_telegram_for_approval(
    dealer: dict,
    msg_body: str,
    classification: dict,
    candidates: list,
    reply_ids: list,
    time_ctx: dict,
):
    """Invia al Telegram human-in-loop le candidate replies."""
    if not TELEGRAM_BOT_TOKEN:
        print('[WARN] ARGOS_TELEGRAM_TOKEN non impostato — alert solo su console')
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
        f"🧠 *RISPOSTA DEALER — {now_it()}*",
        f"",
        f"👤 *{name}* | 🎭 {persona} | Step: {step}",
        f"📊 `{cls_type}` {f'({obj_code})' if obj_code else ''} — {cls_conf}%",
        f"",
        f"💬 *Messaggio ricevuto:*",
        f"_{msg_body[:400]}_",
        f"",
    ]

    for i, (reply, rid) in enumerate(zip(candidates, reply_ids), 1):
        lines += [
            f"━━━ RISPOSTA #{i} — `{reply['label']}` ━━━",
            f"{reply['text'][:500]}",
            f"_💡 {reply.get('cialdini_note', '')}_",
            f"`/approva {rid}` | `/modifica {rid} testo` | `/rifiuta {rid}`",
            f"",
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
    parser.add_argument('--persona',    default='DEFAULT')
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
