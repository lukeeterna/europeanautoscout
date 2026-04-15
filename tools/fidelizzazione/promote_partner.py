"""
ARGOS — Promuovi dealer a Partner Attivo dopo la prima transazione.

CLI:
  python3 promote_partner.py --dealer TIER0_FG_001 --transactions 1 --revenue 2800
  python3 promote_partner.py --list   # mostra tutti i partner attivi
"""

import argparse
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get(
    "ARGOS_DB_PATH",
    "/Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite"
)


def promote(dealer_id: str, transactions: int, revenue: float):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    row = con.execute(
        "SELECT dealer_name, city, is_active_partner FROM conversations WHERE dealer_id = ?",
        (dealer_id,)
    ).fetchone()
    if not row:
        con.close()
        raise ValueError(f"Dealer non trovato: {dealer_id}")

    now = datetime.utcnow().isoformat()
    con.execute(
        """UPDATE conversations SET
             is_active_partner    = 1,
             partner_since        = COALESCE(partner_since, ?),
             total_transactions   = total_transactions + ?,
             total_revenue_dealer = total_revenue_dealer + ?,
             state_updated_at     = ?
           WHERE dealer_id = ?""",
        (now, transactions, revenue, now, dealer_id)
    )
    con.commit()

    updated = con.execute(
        "SELECT dealer_name, city, is_active_partner, partner_since, "
        "total_transactions, total_revenue_dealer FROM conversations WHERE dealer_id = ?",
        (dealer_id,)
    ).fetchone()
    con.close()

    print(f"\n✓ {updated['dealer_name']} ({updated['city']}) → PARTNER ATTIVO")
    print(f"  Transazioni totali: {updated['total_transactions']}")
    print(f"  Revenue dealer:     € {updated['total_revenue_dealer']:,.0f}")
    print(f"  Partner dal:        {updated['partner_since'][:10]}")
    print(f"\nProssimi step:")
    print(f"  1. Genera lettera:  python3 trusted_partner_letter.py --dealer {dealer_id} --mark-sent")
    if updated["total_transactions"] >= 2:
        print(f"  2. Genera analytics: python3 analytics_dossier.py --dealer {dealer_id}")


def list_partners():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT dealer_id, dealer_name, city, total_transactions, total_revenue_dealer, "
        "partner_since, trusted_partner_sent, last_analytics_sent "
        "FROM conversations WHERE is_active_partner = 1"
    ).fetchall()
    con.close()

    if not rows:
        print("Nessun partner attivo ancora.")
        return

    print(f"\n{'DEALER':<20} {'CITTÀ':<15} {'TX':>4} {'REVENUE':>10} {'PARTNER DAL':<12} {'LETTERA':>8} {'ANALYTICS':>10}")
    print("-" * 90)
    for r in rows:
        lettera  = "✓" if r["trusted_partner_sent"] else "—"
        analytics = r["last_analytics_sent"][:10] if r["last_analytics_sent"] else "—"
        since    = r["partner_since"][:10] if r["partner_since"] else "—"
        print(
            f"{r['dealer_name']:<20} {r['city']:<15} {r['total_transactions']:>4} "
            f"€ {r['total_revenue_dealer']:>8,.0f} {since:<12} {lettera:>8} {analytics:>10}"
        )


def main():
    parser = argparse.ArgumentParser(description="ARGOS Partner Promotion")
    parser.add_argument("--dealer",       help="dealer_id da promuovere")
    parser.add_argument("--transactions", type=int, default=1, help="n. transazioni da aggiungere")
    parser.add_argument("--revenue",      type=float, default=0.0, help="revenue dealer da aggiungere (€)")
    parser.add_argument("--list",         action="store_true", help="lista partner attivi")
    args = parser.parse_args()

    if args.list:
        list_partners()
    elif args.dealer:
        promote(args.dealer, args.transactions, args.revenue)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
