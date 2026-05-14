"""Test WA bridge — E2E flow simulato dealer + seller per deal completo.

Smoke test:
  1. Setup deal + parties
  2. Ingest inbound msg dealer
  3. State machine transitions
  4. Generate outbound candidate dealer (IT) e seller (EN) per ogni fase
  5. Approve + mark sent simulato
  6. Stats finale
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deal_state_machine import Deal, DealStateMachine
from wa_bridge import WABridge, InboundMsg


def test_e2e_deal_flow() -> bool:
    print("\n=== test_e2e_deal_flow ===")
    with tempfile.TemporaryDirectory() as td:
        bridge_db = Path(td) / "bridge.sqlite"
        deals_db = Path(td) / "deals.sqlite"

        # 1. Setup: Deal + Parties
        deal = Deal(
            deal_id="DEAL-FG-001",
            dealer_alias="D-FG-001",
            seller_alias="S-DE-042",
            vehicle_desc="BMW X3 xDrive 30d 2020 45000km",
        )
        DealStateMachine(deal, db_path=deals_db)
        print("  deal created")

        bridge = WABridge(db_path=bridge_db, deals_db_path=deals_db)
        bridge.register_party("393331234567", "dealer", "D-FG-001", country="IT")
        bridge.register_party("4915112345678", "seller", "S-DE-042", country="DE")
        print("  2 parties registered")

        # 2. Ingest inbound da dealer (interesse)
        bridge.ingest_inbound(InboundMsg(
            msg_id="MSG-001",
            party_role="dealer",
            party_phone="393331234567",
            body="Mi interessa, mi mandi dossier completo",
            received_ts=1715680000,
        ))
        pending = list(bridge.pending_inbound())
        assert len(pending) == 1, f"expected 1 pending inbound, got {len(pending)}"
        print(f"  inbound msg ingested: {pending[0].msg_id}")

        # 3. Process inbound (mock NLU result), mark processed
        bridge.mark_processed("MSG-001", deal_id="DEAL-FG-001",
                              intent="offer_request", sentiment="positive")

        # 4. Generate outbound candidates per ogni fase del workflow
        template_vars = {
            "dealer_alias": "D-FG-001",
            "seller_alias": "S-DE-042",
            "auto_make": "BMW",
            "auto_model": "X3 xDrive 30d",
            "auto_year": 2020,
            "auto_km": 45000,
            "price_eu_eur": 32000,
            "price_it_market_eur": 38500,
            "margin_estimate_eur": 4500,
            "country": "DE",
            "dossier_id": "ARGOS-2026-001",
            "fee_eur": 1000,
            "delivery_days_est": 20,
            "documents_required": ["EUROCOC", "DAT", "DEKRA", "Libretto"],
            "transport_quote_eur": 850,
        }

        fsm = DealStateMachine(deal, db_path=deals_db)

        # Stato offer_sent → generate offer.it per dealer + offer.en per seller
        cand_dealer = bridge.generate_response("DEAL-FG-001", "dealer", template_vars)
        cand_seller = bridge.generate_response("DEAL-FG-001", "seller", template_vars)
        assert cand_dealer.template_phase == "offer"
        assert cand_dealer.template_lang == "it"
        assert cand_dealer.target_phone == "393331234567"
        assert cand_seller.template_lang == "en"
        assert cand_seller.target_phone == "4915112345678"
        assert "ARGOS-2026-001" in cand_dealer.body
        assert "BMW X3 xDrive 30d" in cand_dealer.body
        bridge.queue_outbound(cand_dealer)
        bridge.queue_outbound(cand_seller)
        print(f"  offer phase: 2 candidates queued (dealer IT + seller EN)")

        # Advance state: offer_sent → accepted → docs_shared → payment_pending → ...
        fsm.accept()
        cand = bridge.generate_response("DEAL-FG-001", "dealer", template_vars)
        assert cand.template_phase == "negotiation"
        bridge.queue_outbound(cand)
        print(f"  accepted → negotiation phase outbound queued")

        fsm.share_docs()
        cand = bridge.generate_response("DEAL-FG-001", "seller", template_vars)
        assert cand.template_phase == "documents"
        bridge.queue_outbound(cand)
        print(f"  docs_shared → documents phase outbound queued")

        fsm.request_payment()
        cand = bridge.generate_response("DEAL-FG-001", "dealer", template_vars)
        assert cand.template_phase == "payment"
        bridge.queue_outbound(cand)

        fsm.confirm_payment()
        cand = bridge.generate_response("DEAL-FG-001", "seller", template_vars)
        assert cand.template_phase == "payment"  # payment_confirmed maps still to payment phase
        bridge.queue_outbound(cand)

        fsm.schedule_transport()
        cand = bridge.generate_response("DEAL-FG-001", "dealer", template_vars)
        assert cand.template_phase == "delivery"
        bridge.queue_outbound(cand)

        # 5. Approve + mark sent simulato (HITL flow)
        pending_out = bridge.pending_outbound()
        assert len(pending_out) >= 6, f"expected ≥6 outbound, got {len(pending_out)}"
        for o in pending_out[:3]:
            bridge.approve_outbound(o["id"])
        approved = bridge.pending_outbound(only_approved=True)
        assert len(approved) == 3
        for o in approved:
            bridge.mark_sent(o["id"], "ok")

        # 6. Stats finale
        stats = bridge.stats()
        print(f"  stats: {stats}")
        assert stats["parties_registered"] == 2
        assert stats["inbound_total"] == 1
        assert stats["inbound_pending"] == 0
        assert stats["outbound_total"] >= 6
        assert stats["outbound_pending"] == stats["outbound_total"] - 3
        print("  PASS")
        return True


def test_party_alias_lookup() -> bool:
    print("\n=== test_party_alias_lookup ===")
    with tempfile.TemporaryDirectory() as td:
        bridge_db = Path(td) / "b.sqlite"
        deals_db = Path(td) / "d.sqlite"
        # Init deals DB schema
        DealStateMachine(Deal(deal_id="X", dealer_alias="A", seller_alias="B"), db_path=deals_db)
        bridge = WABridge(bridge_db, deals_db)
        bridge.register_party("393001234567", "dealer", "D-TEST-001", "IT")
        bridge.register_party("491701234567", "seller", "S-DE-099", "DE")
        assert bridge.get_party_alias("393001234567") == "dealer:D-TEST-001"
        assert bridge.get_party_alias("491701234567") == "seller:S-DE-099"
        assert bridge.get_party_alias("000000000") is None
        print("  PASS")
        return True


def main() -> int:
    tests = [test_e2e_deal_flow, test_party_alias_lookup]
    results = []
    for t in tests:
        try:
            ok = t()
            results.append((t.__name__, ok))
        except AssertionError as e:
            print(f"  FAIL: {e}")
            results.append((t.__name__, False))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  ERROR: {type(e).__name__}: {e}")
            results.append((t.__name__, False))

    print("\n=== SUMMARY ===")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
