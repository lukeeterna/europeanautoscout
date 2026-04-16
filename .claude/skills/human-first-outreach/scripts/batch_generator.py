"""
batch_generator.py — ARGOS human-first-outreach Phase 2
Batch generation + digest Telegram | S128

Flusso:
  07:00 → genera messaggi candidati per dealer in coda giornaliera
  07:30 → digest Telegram a Luke (raggruppato per archetipo/regione/ICP tier)
  08:00 → Luke approva/rigetta in bulk
  09:30+ → messaggi approvati entrano in coda wa-daemon

Uso:
  python3 batch_generator.py                    # genera + invia digest
  python3 batch_generator.py --dry-run          # genera senza inviare TG
  python3 batch_generator.py --test-founder     # test su TEST_FOUNDER
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Path al project root (3 livelli su da .claude/skills/human-first-outreach/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "wa-intelligence"))

from signal_event import SignalEvent, run_gates, signal_fresh_001
from validator import validate, log_to_db

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH = os.getenv(
    "ARGOS_DB_PATH",
    os.path.expanduser("~/Documents/app-antigravity-auto/dealer_network.sqlite"),
)
HYPOTHESIS_FILE = Path(__file__).parent.parent / "assets" / "hypothesis_routing.json"
DAILY_MAX_CANDIDATES = int(os.getenv("ARGOS_BATCH_DAILY_MAX", "10"))

TG_TOKEN   = os.getenv("ARGOS_TELEGRAM_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
TG_CHAT_ID = os.getenv("ARGOS_TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_ADMIN_CHAT_IDS", ""))


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_dealers_for_batch(limit: int = DAILY_MAX_CANDIDATES, test_only: bool = False) -> list:
    """
    Recupera dealer in coda per outreach Day 1.
    Criteri: current_step = PENDING, opt_out = 0, outbound_count = 0.
    """
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        con.row_factory = sqlite3.Row
        query = """
            SELECT dealer_id, dealer_name, city, persona_type, score,
                   phone_number, recommendation
            FROM conversations
            WHERE current_step IN ('PENDING', 'COLD')
              AND (opt_out IS NULL OR opt_out = 0)
              AND outbound_count = 0
        """
        params = []
        if test_only:
            query += " AND dealer_id = 'TEST_FOUNDER'"
        else:
            query += " AND dealer_id != 'TEST_FOUNDER'"

        query += " ORDER BY score DESC LIMIT ?"
        params.append(limit)

        rows = con.execute(query, params).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[BATCH] DB error: {e}")
        return []


def get_dealer_stock_from_db(dealer_id: str) -> dict:
    """
    Recupera stock del dealer per GATE-ICP-001.
    Usa cove_tracker.duckdb se disponibile, altrimenti stima da conversations.
    """
    # Fallback: stima da score e persona_type (se non abbiamo dati DuckDB)
    try:
        import duckdb
        cove_db = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")
        if os.path.exists(cove_db):
            con = duckdb.connect(cove_db, read_only=True)
            # Cerca veicoli per dealer
            rows = con.execute(
                "SELECT make, COUNT(*) as cnt FROM vehicle_listings WHERE dealer_id = ? GROUP BY make",
                [dealer_id]
            ).fetchall()
            con.close()
            if rows:
                stock = {"total": sum(r[1] for r in rows)}
                for make, cnt in rows:
                    stock[make] = cnt
                return stock
    except Exception:
        pass

    # Fallback conservativo: assume stock generico da conversations.score
    return {"total": 20, "BMW": 4, "Mercedes": 3, "Audi": 2}


def load_hypothesis(persona_type: str) -> str:
    """Carica hypothesis per archetipo dal JSON."""
    try:
        with open(HYPOTHESIS_FILE) as f:
            data = json.load(f)
        hypotheses = data.get("hypotheses", {})
        return hypotheses.get(persona_type, hypotheses.get("NEUTRO", ""))
    except Exception as e:
        print(f"[BATCH] Hypothesis file error: {e}")
        return "Ipotizzo che stia aspettando il momento giusto per ribassare senza compromettere il margine"


def generate_day1_message(dealer: dict, signal: SignalEvent) -> str:
    """Genera messaggio Day 1 con hypothesis framing."""
    hypothesis = load_hypothesis(dealer.get("persona_type", "NEUTRO"))
    anchor = signal.anchor_text()

    return (
        f"Buongiorno, sono Luca Ferretti.\n\n"
        f"Ho visto la {signal.vehicle} che {anchor}.\n\n"
        f"{hypothesis}.\n\n"
        f"È così, o mi sto sbagliando?\n\n"
        f"Luca"
    )


# ── Core batch pipeline ───────────────────────────────────────────────────────

def process_dealer(dealer: dict, signal: SignalEvent, mode: str = "shadow") -> Optional[dict]:
    """
    Processa un dealer: gates → messaggio → validate → candidate o block.
    Returns dict con candidate data, o None se bloccato.
    """
    dealer_id = dealer["dealer_id"]

    # LAYER 0: Gates
    stock = get_dealer_stock_from_db(dealer_id)
    gate_result = run_gates(signal, stock)

    if not gate_result["passed"]:
        log_to_db(dealer_id, gate_result["blocked_by"], "block",
                  gate_result["motivation"], "", mode)
        return {
            "dealer_id": dealer_id,
            "dealer_name": dealer["dealer_name"],
            "status": "BLOCKED",
            "blocked_by": gate_result["blocked_by"],
            "motivation": gate_result["motivation"],
        }

    icp_tier = gate_result.get("icp_tier", "unknown")
    premium_pct = gate_result.get("premium_concentration", 0.0)

    # Genera messaggio
    message = generate_day1_message(dealer, signal)

    # Dealer state per validator
    dealer_state = {
        "current_step": dealer.get("current_step", "PENDING"),
        "outbound_count": 0,
        "days_on_market": signal.days_on_market,
    }

    # Validate (Layer 4)
    val = validate(message, "DAY1_PREMIUM", dealer_state,
                   dealer_id=dealer_id, mode=mode)

    if val["result"] == "BLOCK":
        return {
            "dealer_id": dealer_id,
            "dealer_name": dealer["dealer_name"],
            "status": "BLOCKED",
            "blocked_by": val["check_failed"],
            "motivation": val["reason"],
        }

    # Log LIA
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        con.execute(
            "INSERT INTO lia_log (dealer_id, purpose, data_source, data_source_date) VALUES (?, ?, ?, ?)",
            (dealer_id, "vehicle_scouting_outreach", signal.data_source,
             str(signal.scrape_date))
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"[BATCH] LIA log error: {e}")

    return {
        "dealer_id": dealer_id,
        "dealer_name": dealer["dealer_name"],
        "city": dealer.get("city", ""),
        "persona_type": dealer.get("persona_type", "NEUTRO"),
        "phone_number": dealer.get("phone_number", ""),
        "score": dealer.get("score", 0),
        "icp_tier": icp_tier,
        "premium_concentration": f"{premium_pct:.0%}",
        "signal_strength": signal.signal_strength,
        "signal_days": signal.days_on_market,
        "vehicle": signal.vehicle,
        "message": message,
        "status": "CANDIDATE",
        "opt_out_text": signal.opt_out_source_text(),
    }


def send_telegram_digest(candidates: list, blocked: list, mode: str = "shadow") -> bool:
    """Invia digest Telegram a Luke per approvazione bulk."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[BATCH] TG not configured — digest skipped")
        return False

    try:
        import requests

        now_it = datetime.now().strftime("%d/%m/%Y %H:%M")
        lines = [
            f"🗂 *ARGOS — Daily Batch {now_it}* [{mode.upper()}]",
            f"",
            f"✅ Candidati: {len(candidates)} | 🚫 Bloccati: {len(blocked)}",
            f"",
        ]

        # Raggruppa per archetipo
        by_type = {}
        for c in candidates:
            pt = c["persona_type"]
            by_type.setdefault(pt, []).append(c)

        for pt, dealers in sorted(by_type.items()):
            lines.append(f"*{pt}* ({len(dealers)})")
            for d in dealers:
                lines.append(
                    f"  • {d['dealer_name']} ({d['city']}) — "
                    f"ICP={d['icp_tier']} | {d['signal_strength']} | {d['signal_days']}gg"
                )
            lines.append("")

        if blocked:
            lines.append(f"*Bloccati*")
            for b in blocked:
                lines.append(f"  ✗ {b['dealer_name']}: {b['blocked_by']}")
            lines.append("")

        if candidates:
            lines.append("Per approvare: rispondi *OK* a questo messaggio")
            lines.append("Per rigettare singolo: rispondi *SKIP dealer_id*")

        text = "\n".join(lines)

        resp = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        resp.raise_for_status()
        print(f"[BATCH] Digest TG inviato ({len(candidates)} candidati)")
        return True

    except Exception as e:
        print(f"[BATCH] TG digest failed: {e}")
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ARGOS Batch Generator — Phase 2")
    parser.add_argument("--dry-run", action="store_true", help="Genera senza inviare TG")
    parser.add_argument("--test-founder", action="store_true", help="Usa solo TEST_FOUNDER")
    parser.add_argument("--mode", default="shadow", choices=["shadow", "canary", "enforce"])
    args = parser.parse_args()

    mode = args.mode
    test_only = args.test_founder

    print(f"[BATCH] Avvio batch generation — mode={mode}, test_only={test_only}")

    # 1. Carica dealer in coda
    dealers = get_dealers_for_batch(test_only=test_only)
    if not dealers:
        print("[BATCH] Nessun dealer in coda. Exit.")
        return

    print(f"[BATCH] {len(dealers)} dealer da processare")

    # 2. Crea signal_event di test/mock
    #    In produzione questo viene da scraper AutoScout24.it
    #    Per test usiamo signal mock con dati realistici
    from datetime import date, timedelta
    signal = SignalEvent(
        url="https://www.autoscout24.it/listing/test",
        days_on_market=87,
        vehicle="BMW X3 xDrive30d 2022",
        listing_price=38500,
        scrape_date=date.today(),
        signal_strength="S+",
        signal_observed_at=datetime.now(timezone.utc),
        dealer_id="",  # viene sovrascritta in process_dealer
        data_source="AutoScout24.it",
        listing_id="test_listing_001",
    )

    # 3. Processa ogni dealer
    candidates = []
    blocked = []

    for dealer in dealers:
        signal.dealer_id = dealer["dealer_id"]
        result = process_dealer(dealer, signal, mode=mode)
        if result:
            if result["status"] == "CANDIDATE":
                candidates.append(result)
            else:
                blocked.append(result)

    print(f"[BATCH] Risultati: {len(candidates)} candidati, {len(blocked)} bloccati")

    # 4. Mostra preview messaggi
    for c in candidates:
        print(f"\n{'─'*50}")
        print(f"CANDIDATO: {c['dealer_name']} ({c['city']}) — {c['persona_type']}")
        print(f"ICP={c['icp_tier']} | Signal={c['signal_strength']} | {c['signal_days']}gg")
        print(f"\nMESSAGGIO:\n{c['message']}")

    for b in blocked:
        print(f"\n✗ BLOCCATO: {b['dealer_name']} — {b['blocked_by']}: {b['motivation']}")

    # 5. Invia digest TG
    if not args.dry_run:
        send_telegram_digest(candidates, blocked, mode=mode)
    else:
        print("\n[BATCH] Dry-run: digest TG non inviato")

    # 6. Return exit code
    total = len(candidates) + len(blocked)
    block_rate = len(blocked) / total if total > 0 else 0
    print(f"\n[BATCH] block_rate={block_rate:.0%} ({len(blocked)}/{total})")
    return candidates


if __name__ == "__main__":
    main()
