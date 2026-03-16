#!/usr/bin/env python3
"""
salerno_pipeline_loader.py — ARGOS™ CoVe 2026
Carica 8 dealer Salerno nella pipeline DuckDB + prepara outreach Day 1.

Usage: python3 tools/salerno_pipeline_loader.py
       python3 tools/salerno_pipeline_loader.py --dry-run  (solo preview)
"""

import duckdb
import os
import sys
import json
from datetime import datetime

DB_PATH = os.path.expanduser(
    '~/Documents/app-antigravity-auto/dealer_network.duckdb'
)
DRY_RUN = '--dry-run' in sys.argv

# ── Variante A — messaggio WA Day 1 neutro (approvato S58) ───
MSG_DAY1 = """Buongiorno, sono Luca Ferretti di ARGOS Automotive.

Lavoriamo con concessionari italiani per trovare BMW, Mercedes e Audi 2018-2023 direttamente in Germania, Belgio e Olanda.

La differenza rispetto agli importatori classici: fee fissa €1.000 a veicolo consegnato, zero anticipi. I trader tradizionali nascondono €7-10k nel prezzo — noi mettiamo tutto in chiaro prima.

Verifica storica DAT e ispezione DEKRA inclusi. Si paga solo se il veicolo viene approvato e consegnato.

Le interessa un preventivo su un modello specifico che sta cercando?

Luca Ferretti | ARGOS Automotive""".strip()

# ── Pipeline Salerno S58 ─────────────────────────────────────
DEALERS = [
    {
        "dealer_id": "SALERNO_001",
        "dealer_name": "Autovanny Group Srl",
        "city": "Eboli (SA)",
        "phone_number": "393355250129",
        "stock_size": 58,
        "persona_type": "NARCISO",
        "score": 8.5,
        "source": "autoscout24",
        "notes": "Multi-brand premium, 335-5250129, NARCISO/BARONE ipotesi"
    },
    {
        "dealer_id": "SALERNO_002",
        "dealer_name": "FC Luxury Car Center Srl",
        "city": "S.Egidio del Monte Albino (SA)",
        "phone_number": "393425036799",
        "stock_size": 27,
        "persona_type": "BARONE",
        "score": 8.0,
        "source": "autoscout24",
        "notes": "4.85/5 su 247 recensioni, premium positioning, WA +39 342 5036799"
    },
    {
        "dealer_id": "SALERNO_003",
        "dealer_name": "Ferrauto Srl",
        "city": "San Valentino Torio (SA)",
        "phone_number": "390815187350",
        "stock_size": 68,
        "persona_type": "BARONE",
        "score": 8.0,
        "source": "autoscout24",
        "notes": "Fisso 081-5187350, potrebbe non avere WA su questo numero"
    },
    {
        "dealer_id": "SALERNO_004",
        "dealer_name": "A.B. Motors Srl",
        "city": "Montecorvino Pugliano (SA)",
        "phone_number": "393356418105",
        "stock_size": 49,
        "persona_type": "RELAZIONALE",
        "score": 7.5,
        "source": "autoscout24",
        "notes": "Antonio Buoninfante, 30+ anni, 4.85/5 su 288 recensioni, WA 335-6418105"
    },
    {
        "dealer_id": "SALERNO_005",
        "dealer_name": "Auto Genova Srl",
        "city": "Salerno (SA)",
        "phone_number": "393294357882",
        "stock_size": 117,
        "persona_type": "RAGIONIERE",
        "score": 7.0,
        "source": "autoscout24",
        "notes": "Giovanni venditore, dal 1996, 100+ auto, WA 329-4357882"
    },
    {
        "dealer_id": "SALERNO_006",
        "dealer_name": "Autoluce Srl",
        "city": "Baronissi (SA)",
        "phone_number": "39089953608",
        "stock_size": 26,
        "persona_type": "BARONE",
        "score": 7.0,
        "source": "autoscout24",
        "notes": "Fisso 089-953608, stock piccolo ma target ARGOS"
    },
    {
        "dealer_id": "SALERNO_007",
        "dealer_name": "Tirrenia Auto Srl",
        "city": "Cava de' Tirreni (SA)",
        "phone_number": "390892962937",
        "stock_size": 51,
        "persona_type": "DELEGATORE",
        "score": 7.0,
        "source": "autoscout24",
        "notes": "Lucia Ferrara titolare, 4.5/5 su 128 recensioni, NO WA mobile"
    },
    {
        "dealer_id": "SALERNO_008",
        "dealer_name": "Gruppo Emme Srl",
        "city": "Battipaglia (SA)",
        "phone_number": "393476832587",
        "stock_size": 53,
        "persona_type": "TECNICO",
        "score": 6.5,
        "source": "autoscout24",
        "notes": "Service ufficiale BMW-MINI, 30 anni, WA vendite 347-6832587"
    },
]


def ensure_tables(con):
    """Crea tabella conversations se non esiste."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            dealer_id       VARCHAR PRIMARY KEY,
            dealer_name     VARCHAR,
            city            VARCHAR,
            phone_number    VARCHAR,
            stock_size      INTEGER,
            persona_type    VARCHAR,
            score           DOUBLE,
            source          VARCHAR,
            notes           VARCHAR,
            current_step    VARCHAR DEFAULT 'PENDING',
            day1_message    VARCHAR,
            recommendation  VARCHAR DEFAULT 'PENDING',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contact_at TIMESTAMP,
            analyzed_at     TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS pending_replies (
            id           VARCHAR PRIMARY KEY,
            dealer_id    VARCHAR,
            dealer_name  VARCHAR,
            reply_text   VARCHAR,
            reply_label  VARCHAR,
            approved     BOOLEAN,
            sent         BOOLEAN DEFAULT FALSE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id           INTEGER PRIMARY KEY,
            dealer_id    VARCHAR,
            direction    VARCHAR,
            body         VARCHAR,
            timestamp_it TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def load_dealers(con):
    """Inserisce dealer nella pipeline. Skip se già esistono."""
    loaded = 0
    skipped = 0
    for d in DEALERS:
        existing = con.execute(
            "SELECT 1 FROM conversations WHERE dealer_id = ?",
            [d['dealer_id']]
        ).fetchall()
        if existing:
            print(f"  ⏭️  {d['dealer_name']} — già presente, skip")
            skipped += 1
            continue

        con.execute("""
            INSERT INTO conversations
            (dealer_id, dealer_name, city, phone_number, stock_size,
             persona_type, score, source, notes, current_step, day1_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
        """, [
            d['dealer_id'], d['dealer_name'], d['city'],
            d['phone_number'], d['stock_size'], d['persona_type'],
            d['score'], d['source'], d['notes'], MSG_DAY1
        ])
        loaded += 1
        print(f"  ✅ {d['dealer_name']} ({d['city']}) — caricato")

    return loaded, skipped


def main():
    print("=" * 60)
    print("ARGOS™ — Salerno Pipeline Loader (S58)")
    print("=" * 60)
    print(f"DB: {DB_PATH}")
    print(f"Dealer da caricare: {len(DEALERS)}")
    print(f"Dry run: {'SÌ' if DRY_RUN else 'NO'}")
    print()

    if DRY_RUN:
        print("📋 PREVIEW — nessuna modifica al DB\n")
        for d in DEALERS:
            wa = "✅ WA" if d['phone_number'].startswith('393') and len(d['phone_number']) == 12 else "📞 Fisso"
            print(f"  {d['dealer_id']} | {d['dealer_name']:30s} | {d['city']:25s} | {wa} | {d['persona_type']:12s} | {d['score']}/10")
        print(f"\n📝 Messaggio Day 1 ({len(MSG_DAY1)} chars):")
        print(MSG_DAY1[:200] + "...")
        return

    con = duckdb.connect(DB_PATH)
    ensure_tables(con)
    loaded, skipped = load_dealers(con)
    con.commit()
    con.close()

    print(f"\n{'=' * 60}")
    print(f"✅ Caricati: {loaded} | ⏭️ Skippati: {skipped}")
    print(f"Prossimo step: attivare WA Business → auth_business.js → invio Day 1")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
