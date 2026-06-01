#!/usr/bin/env python3
"""
dealer_crm.py — ARGOS Dealer CRM Unificato
CoVe 2026 | Enterprise Grade

Schema unificato per dealer pipeline:
  - dealers: anagrafica completa (master record)
  - interactions: log touchpoint (WA/TEL/EMAIL/VISIT)
  - vehicles_proposed: storico veicoli proposti per dealer

Bridge con tabella `conversations` del WA daemon (non toccata).

Uso:
  python3 tools/dealer_crm.py init          # Crea tabelle + popola target S73
  python3 tools/dealer_crm.py list          # Lista dealer con stato
  python3 tools/dealer_crm.py show <id>     # Dettaglio dealer
  python3 tools/dealer_crm.py update <id> <campo> <valore>
  python3 tools/dealer_crm.py log <id> <canale> <direzione> <contenuto>
  python3 tools/dealer_crm.py propose <id> <modello> <prezzo_eu> <prezzo_it> [vin]
  python3 tools/dealer_crm.py pipeline      # Vista pipeline per stato
  python3 tools/dealer_crm.py match <marca> # Dealer che trattano marca X
  python3 tools/dealer_crm.py sync          # Sincronizza dealer → conversations
  python3 tools/dealer_crm.py stats         # KPI pipeline
"""

import sqlite3
import os
import sys
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get(
    'ARGOS_DB_PATH',
    os.path.expanduser('~/Documents/app-antigravity-auto/dealer_network.sqlite')
)


def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA foreign_keys=ON')
    return con


# ── Schema ─────────────────────────────────────────────────────

def ensure_tables(con: sqlite3.Connection):
    """Crea tabelle CRM se non esistono. NON tocca le tabelle WA daemon."""
    con.executescript("""
        CREATE TABLE IF NOT EXISTS dealers (
            dealer_id           TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            city                TEXT,
            province            TEXT,
            region              TEXT,
            phone               TEXT,
            wa                  TEXT,
            email               TEXT,
            stock_size          INTEGER,
            brands              TEXT,       -- JSON array: ["BMW","Mercedes","Audi"]
            premium_pct         REAL,       -- % stock premium (0.0-1.0)
            years_active        INTEGER,
            rating              REAL,
            reviews             INTEGER,
            archetype           TEXT,       -- NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE/...
            target_type         TEXT,       -- IMPORTER/GROWTH/LUXURY/MONO_BRAND/VOLUME
            tier                TEXT,       -- TIER0/TIER1/TIER2
            score_fit           REAL,       -- 0-10 fit score
            obj_primary         TEXT,       -- obiezione primaria attesa
            source_url          TEXT,       -- link AS24/Google
            instagram           TEXT,
            facebook            TEXT,
            website             TEXT,
            titolare_name       TEXT,
            titolare_age_est    TEXT,       -- "giovane"/"30-40"/"50+"
            import_signal       TEXT,       -- segnale che gia' importa EU
            pipeline_status     TEXT DEFAULT 'NEW',
            -- Pipeline: NEW/CONTACTED/REPLIED/INTERESTED/NEGOTIATION/DEAL/CLOSED/LOST/DORMANT
            first_contact_at    TEXT,
            last_contact_at     TEXT,
            next_action_at      TEXT,
            next_action_type    TEXT,       -- DAY3/DAY7/DAY10/DAY14/DAY21/DAY30/CUSTOM
            notes               TEXT,
            created_at          TEXT DEFAULT (datetime('now')),
            updated_at          TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id           TEXT NOT NULL,
            timestamp           TEXT DEFAULT (datetime('now')),
            channel             TEXT NOT NULL,   -- WA/TEL/EMAIL/VISIT/TG
            direction           TEXT NOT NULL,   -- OUT/IN
            content             TEXT,
            template_used       TEXT,            -- nome template se usato
            vehicle_proposed    TEXT,            -- modello se proposto veicolo
            outcome             TEXT,            -- SENT/DELIVERED/READ/REPLIED/NO_REPLY/BOUNCED
            notes               TEXT,
            FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id)
        );

        CREATE TABLE IF NOT EXISTS vehicles_proposed (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            dealer_id           TEXT NOT NULL,
            proposed_at         TEXT DEFAULT (datetime('now')),
            model               TEXT NOT NULL,   -- "BMW X3 xDrive20d 2022"
            vin                 TEXT,
            price_eu            REAL,            -- prezzo EU (source)
            price_it            REAL,            -- prezzo mercato IT
            margin_estimated    REAL,            -- margine stimato dealer
            cove_score          REAL,            -- CoVe confidence
            portal_source       TEXT,            -- portale (INTERNO, non dealer-facing)
            country             TEXT,            -- paese source
            pdf_path            TEXT,            -- path dossier generato
            status              TEXT DEFAULT 'PROPOSED',
            -- PROPOSED/INTERESTED/APPROVED/PURCHASED/REJECTED/EXPIRED
            dealer_response     TEXT,
            FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id)
        );

        CREATE INDEX IF NOT EXISTS idx_interactions_dealer ON interactions(dealer_id);
        CREATE INDEX IF NOT EXISTS idx_interactions_ts ON interactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_vehicles_dealer ON vehicles_proposed(dealer_id);
        CREATE INDEX IF NOT EXISTS idx_dealers_status ON dealers(pipeline_status);
        CREATE INDEX IF NOT EXISTS idx_dealers_region ON dealers(region);
        CREATE INDEX IF NOT EXISTS idx_dealers_tier ON dealers(tier);
    """)


# ── Bootstrap: popola dealer target da S73 ─────────────────────

SEED_DEALERS = [
    # TIER 0 — Gia' fanno import EU
    {
        'dealer_id': 'stile_car_fg',
        'name': 'Stile Car.it Srls',
        'city': 'Orta Nova',
        'province': 'FG',
        'region': 'Puglia',
        'phone': '333-4254654',
        'wa': '393334254654',
        'stock_size': 36,
        'brands': '["BMW","Mercedes","Audi","Volvo"]',
        'rating': 4.98,
        'reviews': 860,
        'archetype': 'NARCISO',
        'target_type': 'IMPORTER',
        'tier': 'TIER0',
        'score_fit': 9.5,
        'obj_primary': 'OBJ-3',  # "ti apro portali che non raggiungi"
        'titolare_name': 'Domenico',
        'import_signal': 'Dichiara "importazioni europee dirette" su AS24',
        'notes': '860 reviews 4.98 = business solido. Zona FG = zero competitor ARGOS. Primo target.',
    },
    {
        'dealer_id': 'car_plus_av',
        'name': 'Car Plus',
        'city': 'Grottaminarda',
        'province': 'AV',
        'region': 'Campania',
        'phone': '328-9617180',
        'wa': '393289617180',
        'stock_size': 19,
        'brands': '["BMW","Mercedes","Jaguar","Land Rover"]',
        'rating': 4.85,
        'reviews': 66,
        'archetype': 'RAGIONIERE',
        'target_type': 'IMPORTER',
        'tier': 'TIER0',
        'score_fit': 8.5,
        'obj_primary': 'OBJ-PRICE',  # zero rischio, success fee
        'titolare_name': 'Luca',
        'titolare_age_est': 'giovane',
        'import_signal': 'Dichiara "importazioni dall\'estero" su AS24',
        'notes': 'Giovani, 19 auto, gia\' importano. Pain reale su costi/tempo.',
    },
    {
        'dealer_id': 'samy_auto_cs',
        'name': 'Sa.My. Auto',
        'city': 'Rende',
        'province': 'CS',
        'region': 'Calabria',
        'phone': '349-2587423',
        'wa': '393492587423',
        'stock_size': 99,
        'brands': '["BMW","Mercedes","Porsche","Lamborghini"]',
        'archetype': 'PERFORMANTE',
        'target_type': 'IMPORTER',
        'tier': 'TIER0',
        'score_fit': 8.0,
        'titolare_name': 'Antonio Salerni',
        'titolare_age_est': '30-40',
        'import_signal': 'Titolare ha vissuto in Germania',
        'instagram': 'samyauto',
        'notes': '99 auto, conosce prezzi DE. Approccio peer-to-peer, informale.',
    },
    # TIER 1 — Premium puri
    {
        'dealer_id': 'bd_auto_ce',
        'name': 'BD Auto Srl',
        'city': 'Macerata Campania',
        'province': 'CE',
        'region': 'Campania',
        'phone': '320-8649717',
        'wa': '393208649717',
        'stock_size': 46,
        'brands': '["BMW","Mercedes","Porsche","Ferrari"]',
        'rating': 4.94,
        'reviews': 313,
        'archetype': 'BARONE',
        'target_type': 'LUXURY',
        'tier': 'TIER1',
        'score_fit': 8.0,
        'titolare_name': 'Salvatore Caricchia',
        'titolare_age_est': 'giovane',
        'notes': 'Eredita\' nonno. Stock perfetto. 313 recensioni = gia\' forte.',
    },
    {
        'dealer_id': 'top_cars_cs',
        'name': 'Top Cars Srl',
        'city': 'Rende',
        'province': 'CS',
        'region': 'Calabria',
        'phone': '0984-846248',
        'wa': None,
        'stock_size': 35,
        'brands': '["BMW","Mercedes","Porsche","Lamborghini","Ferrari"]',
        'rating': 5.0,
        'reviews': 3,
        'archetype': 'BARONE',
        'target_type': 'LUXURY',
        'tier': 'TIER1',
        'score_fit': 7.5,
        'notes': 'Unico luxury puro in provincia Cosenza. Solo 3 recensioni = poco visibile.',
    },
    {
        'dealer_id': 'autoquarta_le',
        'name': 'AutoQuarta',
        'city': 'Monteroni di Lecce',
        'province': 'LE',
        'region': 'Puglia',
        'phone': '380-3442964',
        'wa': '393803442964',
        'stock_size': 30,
        'brands': '["BMW","Mercedes","Audi","Volvo"]',
        'rating': 4.97,
        'reviews': 108,
        'archetype': 'RAGIONIERE',
        'target_type': 'GROWTH',
        'tier': 'TIER1',
        'score_fit': 7.5,
        'notes': 'Storico (1980), 30 auto premium. Possibile resistenza cambio.',
    },
    {
        'dealer_id': 'loforese_ta',
        'name': 'Loforese 100',
        'city': 'Taranto',
        'province': 'TA',
        'region': 'Puglia',
        'phone': '349-4957882',
        'wa': '393494957882',
        'stock_size': 54,
        'brands': '["BMW","Mercedes","Audi","MINI"]',
        'reviews': 21,
        'archetype': 'PERFORMANTE',
        'target_type': 'VOLUME',
        'tier': 'TIER1',
        'score_fit': 7.0,
        'titolare_name': 'Michele',
        'titolare_age_est': 'giovane',
        'notes': '"Giovane e dinamica", 54 auto leggermente sopra target.',
    },
    # TIER 2 — Da monitorare
    {
        'dealer_id': 'asm_service_na',
        'name': 'ASM Service',
        'city': 'Marigliano',
        'province': 'NA',
        'region': 'Campania',
        'wa': '393930150576',
        'phone': '393-0150576',
        'stock_size': 38,
        'brands': '["Mercedes"]',
        'archetype': 'TECNICO',
        'target_type': 'MONO_BRAND',
        'tier': 'TIER2',
        'score_fit': 6.5,
        'notes': 'Autorizzato Mercedes.',
    },
    {
        'dealer_id': 'delta_automotive_bn',
        'name': 'Delta Automotive',
        'city': 'Benevento',
        'province': 'BN',
        'region': 'Campania',
        'phone': '392-9117227',
        'wa': '393929117227',
        'stock_size': 10,
        'brands': '["Lamborghini","Ferrari"]',
        'archetype': 'BARONE',
        'target_type': 'LUXURY',
        'tier': 'TIER2',
        'score_fit': 6.0,
        'notes': 'Luxury (Lambo/Ferrari) ma micro.',
    },
    {
        'dealer_id': 'dag_auto_av',
        'name': 'Dag Auto',
        'city': 'Manocalzati',
        'province': 'AV',
        'region': 'Campania',
        'phone': '347-9959258',
        'wa': '393479959258',
        'stock_size': 22,
        'brands': '["Mercedes"]',
        'archetype': 'TECNICO',
        'target_type': 'MONO_BRAND',
        'tier': 'TIER2',
        'score_fit': 6.0,
        'notes': 'Mono Mercedes.',
    },
    # Salerno pipeline (gia' contattati con V1 — da rivalutare)
    {
        'dealer_id': 'autovanny_sa',
        'name': 'Autovanny Group',
        'city': 'Eboli',
        'province': 'SA',
        'region': 'Campania',
        'phone': '335-5250129',
        'wa': '393355250129',
        'stock_size': 58,
        'brands': '["BMW","Mercedes","Audi","Porsche"]',
        'archetype': 'NARCISO',
        'target_type': 'GROWTH',
        'tier': 'TIER1',
        'score_fit': 8.5,
        'pipeline_status': 'CONTACTED',
        'notes': 'DAY1_SENT 18/03 con V1. Troppo forte per primo contatto senza track record.',
    },
    {
        'dealer_id': 'fc_luxury_sa',
        'name': 'FC Luxury Car Center',
        'city': 'Sant\'Egidio del Monte Albino',
        'province': 'SA',
        'region': 'Campania',
        'phone': '342-5036799',
        'wa': '393425036799',
        'stock_size': 27,
        'brands': '["BMW","Mercedes","Porsche"]',
        'archetype': 'BARONE',
        'target_type': 'LUXURY',
        'tier': 'TIER1',
        'score_fit': 8.0,
        'pipeline_status': 'CONTACTED',
        'notes': 'DAY1_SENT 18/03 con V1 — errori nel messaggio.',
    },
]


def bootstrap_dealers(con: sqlite3.Connection):
    """Inserisce dealer seed se non esistono."""
    cols = [
        'dealer_id', 'name', 'city', 'province', 'region', 'phone', 'wa',
        'email', 'stock_size', 'brands', 'premium_pct', 'years_active',
        'rating', 'reviews', 'archetype', 'target_type', 'tier', 'score_fit',
        'obj_primary', 'source_url', 'instagram', 'facebook', 'website',
        'titolare_name', 'titolare_age_est', 'import_signal',
        'pipeline_status', 'notes',
    ]
    placeholders = ', '.join(['?'] * len(cols))
    col_names = ', '.join(cols)

    inserted = 0
    for d in SEED_DEALERS:
        vals = [d.get(c) for c in cols]
        try:
            con.execute(
                f'INSERT OR IGNORE INTO dealers ({col_names}) VALUES ({placeholders})',
                vals
            )
            if con.execute('SELECT changes()').fetchone()[0] > 0:
                inserted += 1
        except Exception as e:
            print(f"  SKIP {d['dealer_id']}: {e}")

    con.commit()
    return inserted


# ── Sync: dealers → conversations (bridge per WA daemon) ───────

def sync_to_conversations(con: sqlite3.Connection):
    """Sincronizza dealer → conversations per il WA daemon.
    Crea record in conversations per dealer non ancora presenti."""
    dealers = con.execute("""
        SELECT d.dealer_id, d.name, d.city, d.wa, d.stock_size,
               d.archetype, d.score_fit, d.notes, d.pipeline_status
        FROM dealers d
        WHERE d.wa IS NOT NULL
          AND d.dealer_id NOT IN (SELECT dealer_id FROM conversations)
    """).fetchall()

    synced = 0
    for d in dealers:
        step = 'PENDING'
        if d['pipeline_status'] == 'CONTACTED':
            step = 'DAY1_SENT'

        con.execute("""
            INSERT OR IGNORE INTO conversations
                (dealer_id, dealer_name, city, phone_number, stock_size,
                 persona_type, score, source, notes, current_step)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'dealer_crm', ?, ?)
        """, (
            d['dealer_id'], d['name'], d['city'],
            d['wa'], d['stock_size'],
            d['archetype'], d['score_fit'], d['notes'], step
        ))
        synced += 1

    con.commit()
    return synced


# ── CLI Commands ───────────────────────────────────────────────

def cmd_init():
    """Crea tabelle e popola con dealer target."""
    con = connect()
    ensure_tables(con)
    inserted = bootstrap_dealers(con)
    synced = sync_to_conversations(con)
    total = con.execute('SELECT COUNT(*) FROM dealers').fetchone()[0]
    conv = con.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
    con.close()
    print(f"\n{'='*50}")
    print(f"ARGOS CRM INIZIALIZZATO")
    print(f"{'='*50}")
    print(f"  Dealer inseriti:     {inserted}")
    print(f"  Totale dealer:       {total}")
    print(f"  Synced → conversations: {synced}")
    print(f"  Totale conversations:   {conv}")
    print(f"  DB: {DB_PATH}")
    print(f"{'='*50}")


def cmd_list():
    """Lista dealer con stato pipeline."""
    con = connect()
    ensure_tables(con)
    dealers = con.execute("""
        SELECT dealer_id, name, city, province, tier, archetype,
               target_type, score_fit, pipeline_status, stock_size,
               last_contact_at
        FROM dealers
        ORDER BY
            CASE tier WHEN 'TIER0' THEN 0 WHEN 'TIER1' THEN 1 ELSE 2 END,
            score_fit DESC
    """).fetchall()

    print(f"\n{'ID':<22} {'Nome':<25} {'Citta':<20} {'Tier':<6} {'Arche':<12} "
          f"{'Stato':<12} {'Score':<6} {'Stock':<6}")
    print('─' * 115)
    for d in dealers:
        print(f"{d['dealer_id']:<22} {(d['name'] or '')[:24]:<25} "
              f"{(d['city'] or '')[:19]:<20} {d['tier'] or '':<6} "
              f"{d['archetype'] or '':<12} {d['pipeline_status'] or 'NEW':<12} "
              f"{d['score_fit'] or 0:<6.1f} {d['stock_size'] or 0:<6}")
    print(f"\nTotale: {len(dealers)} dealer")
    con.close()


def cmd_show(dealer_id: str):
    """Dettaglio dealer."""
    con = connect()
    ensure_tables(con)
    d = con.execute('SELECT * FROM dealers WHERE dealer_id = ?', (dealer_id,)).fetchone()
    if not d:
        print(f"Dealer '{dealer_id}' non trovato.")
        con.close()
        return

    print(f"\n{'='*50}")
    print(f"  {d['name']} ({d['dealer_id']})")
    print(f"{'='*50}")
    for key in d.keys():
        val = d[key]
        if val is not None:
            print(f"  {key:<22} {val}")

    # Interazioni recenti
    interactions = con.execute("""
        SELECT * FROM interactions WHERE dealer_id = ?
        ORDER BY timestamp DESC LIMIT 10
    """, (dealer_id,)).fetchall()
    if interactions:
        print(f"\n  --- Interazioni recenti ---")
        for i in interactions:
            print(f"  {i['timestamp']} {i['channel']:<5} {i['direction']:<4} "
                  f"{(i['content'] or '')[:60]}")

    # Veicoli proposti
    vehicles = con.execute("""
        SELECT * FROM vehicles_proposed WHERE dealer_id = ?
        ORDER BY proposed_at DESC LIMIT 5
    """, (dealer_id,)).fetchall()
    if vehicles:
        print(f"\n  --- Veicoli proposti ---")
        for v in vehicles:
            margin = f"+EUR {v['margin_estimated']:,.0f}" if v['margin_estimated'] else '—'
            print(f"  {v['proposed_at']} {v['model']:<30} {margin:<15} {v['status']}")

    con.close()


def cmd_update(dealer_id: str, field: str, value: str):
    """Aggiorna campo dealer."""
    con = connect()
    ensure_tables(con)

    # Whitelist campi modificabili
    allowed = {
        'pipeline_status', 'archetype', 'target_type', 'tier',
        'score_fit', 'obj_primary', 'notes', 'phone', 'wa', 'email',
        'stock_size', 'brands', 'titolare_name', 'titolare_age_est',
        'import_signal', 'instagram', 'facebook', 'website',
        'next_action_at', 'next_action_type',
    }
    if field not in allowed:
        print(f"Campo '{field}' non modificabile. Campi consentiti: {sorted(allowed)}")
        con.close()
        return

    con.execute(
        f"UPDATE dealers SET {field} = ?, updated_at = datetime('now') WHERE dealer_id = ?",
        (value, dealer_id)
    )
    con.commit()
    print(f"OK: {dealer_id}.{field} = {value}")
    con.close()


def cmd_log_interaction(dealer_id: str, channel: str, direction: str, content: str):
    """Logga interazione touchpoint."""
    con = connect()
    ensure_tables(con)
    con.execute("""
        INSERT INTO interactions (dealer_id, channel, direction, content)
        VALUES (?, ?, ?, ?)
    """, (dealer_id, channel.upper(), direction.upper(), content))

    # Aggiorna last_contact_at nel dealer
    con.execute("""
        UPDATE dealers SET last_contact_at = datetime('now'), updated_at = datetime('now')
        WHERE dealer_id = ?
    """, (dealer_id,))
    con.commit()
    print(f"OK: interazione loggata per {dealer_id} ({channel} {direction})")
    con.close()


def cmd_propose(dealer_id: str, model: str, price_eu: str, price_it: str,
                vin: Optional[str] = None):
    """Registra veicolo proposto a dealer."""
    con = connect()
    ensure_tables(con)
    eu = float(price_eu)
    it = float(price_it)
    margin = it - eu

    con.execute("""
        INSERT INTO vehicles_proposed (dealer_id, model, vin, price_eu, price_it, margin_estimated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (dealer_id, model, vin, eu, it, margin))
    con.commit()
    print(f"OK: {model} proposto a {dealer_id} (margine: +EUR {margin:,.0f})")
    con.close()


def cmd_pipeline():
    """Vista pipeline per stato."""
    con = connect()
    ensure_tables(con)
    statuses = con.execute("""
        SELECT pipeline_status, COUNT(*) as cnt
        FROM dealers
        GROUP BY pipeline_status
        ORDER BY
            CASE pipeline_status
                WHEN 'NEW' THEN 0 WHEN 'CONTACTED' THEN 1 WHEN 'REPLIED' THEN 2
                WHEN 'INTERESTED' THEN 3 WHEN 'NEGOTIATION' THEN 4
                WHEN 'DEAL' THEN 5 WHEN 'CLOSED' THEN 6
                WHEN 'LOST' THEN 7 WHEN 'DORMANT' THEN 8 ELSE 9
            END
    """).fetchall()

    total = sum(s['cnt'] for s in statuses)
    print(f"\n{'='*40}")
    print(f"  PIPELINE ARGOS ({total} dealer)")
    print(f"{'='*40}")

    bar_width = 25
    for s in statuses:
        pct = s['cnt'] / total if total > 0 else 0
        bar = '#' * int(pct * bar_width)
        status = s['pipeline_status'] or 'NEW'
        print(f"  {status:<14} {bar:<25} {s['cnt']}")

    print(f"{'='*40}")
    con.close()


def cmd_match(brand: str):
    """Trova dealer che trattano una marca specifica."""
    con = connect()
    ensure_tables(con)
    brand_upper = brand.upper()

    dealers = con.execute("""
        SELECT dealer_id, name, city, province, tier, score_fit,
               pipeline_status, brands
        FROM dealers
        WHERE UPPER(brands) LIKE ?
        ORDER BY score_fit DESC
    """, (f'%{brand_upper}%',)).fetchall()

    print(f"\nDealer che trattano {brand.upper()}:")
    print('─' * 80)
    for d in dealers:
        print(f"  {d['dealer_id']:<22} {d['name']:<25} {(d['city'] or ''):<15} "
              f"{d['tier'] or '':<6} {d['pipeline_status'] or 'NEW':<12}")
    print(f"\nTotale: {len(dealers)}")
    con.close()


def cmd_sync():
    """Sincronizza dealer → conversations."""
    con = connect()
    ensure_tables(con)
    synced = sync_to_conversations(con)
    print(f"Synced {synced} dealer → conversations")
    con.close()


def cmd_stats():
    """KPI pipeline."""
    con = connect()
    ensure_tables(con)

    total = con.execute('SELECT COUNT(*) FROM dealers').fetchone()[0]
    by_tier = con.execute("""
        SELECT tier, COUNT(*) as cnt FROM dealers GROUP BY tier ORDER BY tier
    """).fetchall()
    by_region = con.execute("""
        SELECT region, COUNT(*) as cnt FROM dealers GROUP BY region ORDER BY cnt DESC
    """).fetchall()
    contacted = con.execute(
        "SELECT COUNT(*) FROM dealers WHERE pipeline_status != 'NEW'"
    ).fetchone()[0]
    interactions_count = con.execute('SELECT COUNT(*) FROM interactions').fetchone()[0]
    vehicles_count = con.execute('SELECT COUNT(*) FROM vehicles_proposed').fetchone()[0]

    print(f"\n{'='*40}")
    print(f"  ARGOS CRM STATS")
    print(f"{'='*40}")
    print(f"  Dealer totali:      {total}")
    print(f"  Contattati:         {contacted}")
    print(f"  Interazioni:        {interactions_count}")
    print(f"  Veicoli proposti:   {vehicles_count}")
    print(f"\n  Per tier:")
    for t in by_tier:
        print(f"    {t['tier'] or 'N/A':<8} {t['cnt']}")
    print(f"\n  Per regione:")
    for r in by_region:
        print(f"    {r['region'] or 'N/A':<15} {r['cnt']}")
    print(f"{'='*40}")
    con.close()


# ── Main ───────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == 'init':
        cmd_init()
    elif cmd == 'list':
        cmd_list()
    elif cmd == 'show' and len(sys.argv) >= 3:
        cmd_show(sys.argv[2])
    elif cmd == 'update' and len(sys.argv) >= 5:
        cmd_update(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'log' and len(sys.argv) >= 6:
        cmd_log_interaction(sys.argv[2], sys.argv[3], sys.argv[4],
                            ' '.join(sys.argv[5:]))
    elif cmd == 'propose' and len(sys.argv) >= 6:
        cmd_propose(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
                    sys.argv[6] if len(sys.argv) > 6 else None)
    elif cmd == 'pipeline':
        cmd_pipeline()
    elif cmd == 'match' and len(sys.argv) >= 3:
        cmd_match(sys.argv[2])
    elif cmd == 'sync':
        cmd_sync()
    elif cmd == 'stats':
        cmd_stats()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
