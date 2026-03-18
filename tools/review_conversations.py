#!/usr/bin/env python3
"""
review_conversations.py — ARGOS™ Conversation Review & Dealer Profiling
CoVe 2026 | S60

Eseguito da Claude Code durante le sessioni di review.
Legge TUTTE le conversazioni dal DB, analizza:
  1. Archetipo confermato vs ipotizzato
  2. Qualità risposte LLM (approvate vs modificate vs rifiutate)
  3. Pattern di risposta per tipo di dealer
  4. Genera report + suggerimenti per migliorare system prompt

Usage:
  python3 tools/review_conversations.py                    # report completo
  python3 tools/review_conversations.py --dealer SALERNO_001  # singolo dealer
  python3 tools/review_conversations.py --export-training     # esporta training data
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

DB_PATH = os.environ.get('ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite'))


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def review_pipeline():
    """Report completo della pipeline."""
    con = get_db()

    # Dealer status
    dealers = con.execute("""
        SELECT dealer_id, dealer_name, city, persona_type, current_step,
               score, last_contact_at, analyzed_at
        FROM conversations ORDER BY score DESC
    """).fetchall()

    print("=" * 70)
    print("ARGOS™ — REVIEW CONVERSAZIONI")
    print(f"DB: {DB_PATH}")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)

    print(f"\n📊 DEALER PIPELINE ({len(dealers)} totali)")
    print("-" * 70)
    for d in dealers:
        print(f"  {d['dealer_id']:15s} | {d['dealer_name']:30s} | "
              f"{d['persona_type']:12s} | {d['current_step']}")

    # Messaggi per dealer
    print(f"\n💬 MESSAGGI PER DEALER")
    print("-" * 70)
    for d in dealers:
        msgs = con.execute("""
            SELECT direction, body, timestamp_it
            FROM messages WHERE dealer_id = ?
            ORDER BY timestamp_it ASC
        """, [d['dealer_id']]).fetchall()

        if msgs:
            print(f"\n  [{d['dealer_id']}] {d['dealer_name']} ({d['persona_type']})")
            for m in msgs:
                direction = "→ NOI" if m['direction'] == 'OUTBOUND' else "← DEALER"
                print(f"    {direction}: {m['body'][:120]}...")

    # Risposte LLM: approvate vs modificate vs rifiutate
    print(f"\n🤖 PERFORMANCE RISPOSTE LLM")
    print("-" * 70)

    stats = con.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN approved = 1 AND reply_label != 'MANUAL_EDIT' THEN 1 ELSE 0 END) as approved_as_is,
            SUM(CASE WHEN reply_label = 'MANUAL_EDIT' THEN 1 ELSE 0 END) as modified,
            SUM(CASE WHEN approved = 0 THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN approved IS NULL AND sent = 0 THEN 1 ELSE 0 END) as pending
        FROM pending_replies
    """).fetchone()

    if stats['total'] > 0:
        print(f"  Totale risposte generate: {stats['total']}")
        print(f"  ✅ Approvate senza modifica: {stats['approved_as_is']}")
        print(f"  ✏️  Modificate: {stats['modified']}")
        print(f"  ❌ Rifiutate: {stats['rejected']}")
        print(f"  ⏳ In attesa: {stats['pending']}")

        if stats['approved_as_is'] and stats['total'] > 0:
            accuracy = stats['approved_as_is'] / max(1, stats['total'] - stats['pending']) * 100
            print(f"\n  📈 Accuracy LLM (approvate/gestite): {accuracy:.0f}%")
    else:
        print("  Nessuna risposta LLM ancora generata.")

    # Training corrections
    corrections = con.execute("""
        SELECT tc.*, pr.dealer_id
        FROM training_corrections tc
        LEFT JOIN pending_replies pr ON tc.reply_id = pr.id
        ORDER BY tc.created_at DESC
    """).fetchall() if table_exists(con, 'training_corrections') else []

    if corrections:
        print(f"\n📝 CORREZIONI TRAINING ({len(corrections)})")
        print("-" * 70)
        for c in corrections:
            print(f"  [{c['dealer_id'] or '?'}] {c['original_label']}")
            print(f"    ORIGINALE: {c['original_text'][:100]}...")
            print(f"    CORRETTO:  {c['corrected_text'][:100]}...")
            print()

    # Costi LLM
    if table_exists(con, 'llm_costs'):
        costs = con.execute("""
            SELECT SUM(cost_usd) as total, COUNT(*) as calls,
                   SUM(input_tokens) as in_tok, SUM(output_tokens) as out_tok
            FROM llm_costs
        """).fetchone()
        if costs['total']:
            print(f"\n💰 COSTI LLM")
            print(f"  Totale: ${costs['total']:.4f} ({costs['calls']} chiamate)")
            print(f"  Token: {costs['in_tok']:,} in + {costs['out_tok']:,} out")

    con.close()


def review_dealer(dealer_id):
    """Review approfondito di un singolo dealer."""
    con = get_db()

    d = con.execute("SELECT * FROM conversations WHERE dealer_id = ?",
                    [dealer_id]).fetchone()
    if not d:
        print(f"Dealer {dealer_id} non trovato.")
        return

    print(f"\n{'=' * 60}")
    print(f"REVIEW: {d['dealer_name']} ({d['dealer_id']})")
    print(f"{'=' * 60}")
    print(f"  Città: {d['city']}")
    print(f"  Archetipo ipotizzato: {d['persona_type']}")
    print(f"  Score: {d['score']}/10")
    print(f"  Step: {d['current_step']}")
    print(f"  Ultimo contatto: {d['last_contact_at']}")

    # Tutti i messaggi
    msgs = con.execute("""
        SELECT * FROM messages WHERE dealer_id = ? ORDER BY timestamp_it ASC
    """, [dealer_id]).fetchall()

    print(f"\n  📨 Messaggi ({len(msgs)}):")
    for m in msgs:
        direction = "→ NOI" if m['direction'] == 'OUTBOUND' else "← DEALER"
        print(f"    [{m['timestamp_it']}] {direction}")
        print(f"    {m['body'][:300]}")
        print()

    # Risposte generate
    replies = con.execute("""
        SELECT * FROM pending_replies WHERE dealer_id = ? ORDER BY created_at ASC
    """, [dealer_id]).fetchall()

    print(f"  🤖 Risposte generate ({len(replies)}):")
    for r in replies:
        status = "✅" if r['approved'] == 1 else "❌" if r['approved'] == 0 else "⏳"
        sent = " [INVIATA]" if r['sent'] == 1 else ""
        print(f"    {status} {r['reply_label']}{sent}: {r['reply_text'][:150]}...")

    con.close()


def export_training():
    """Esporta dati per training: conversazioni complete + correzioni."""
    con = get_db()

    training_data = []

    # 1. Conversazioni con risposte approvate (positive examples)
    approved = con.execute("""
        SELECT pr.*, c.persona_type, c.city, c.dealer_name,
               m.body as inbound_message
        FROM pending_replies pr
        JOIN conversations c ON pr.dealer_id = c.dealer_id
        LEFT JOIN messages m ON m.dealer_id = pr.dealer_id AND m.direction = 'INBOUND'
        WHERE pr.sent = 1
        ORDER BY pr.created_at ASC
    """).fetchall()

    for r in approved:
        training_data.append({
            'type': 'approved_response',
            'dealer_id': r['dealer_id'],
            'dealer_name': r['dealer_name'],
            'persona_type': r['persona_type'],
            'city': r['city'],
            'inbound_message': r['inbound_message'] or '',
            'response': r['reply_text'],
            'label': r['reply_label'],
            'was_modified': r['reply_label'] == 'MANUAL_EDIT',
        })

    # 2. Correzioni (gold standard)
    if table_exists(con, 'training_corrections'):
        corrections = con.execute("SELECT * FROM training_corrections").fetchall()
        for c in corrections:
            training_data.append({
                'type': 'correction',
                'dealer_id': c['dealer_id'],
                'original_label': c['original_label'],
                'original_text': c['original_text'],
                'corrected_text': c['corrected_text'],
            })

    output_path = 'data/training/conversations_real_v1.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Esportati {len(training_data)} record in {output_path}")
    con.close()


def table_exists(con, name):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", [name]
    ).fetchone() is not None


if __name__ == '__main__':
    if '--dealer' in sys.argv:
        idx = sys.argv.index('--dealer')
        review_dealer(sys.argv[idx + 1])
    elif '--export-training' in sys.argv:
        export_training()
    else:
        review_pipeline()
