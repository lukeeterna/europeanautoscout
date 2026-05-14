"""E2E smoke test: full deal lifecycle simulato through pipeline orchestrator.

NO WA reale. Inietta messaggi direttamente in bridge_inbound, run pipeline,
verifica state machine + outbound queue + analyzer calls.

Live Groq calls obbligatori — verifica integration analyzer + Groq in sequence
deal real-world plausible.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wa_bridge import WABridge, InboundMsg
from message_analyzer import MessageAnalyzer
from deal_state_machine import Deal, DealStateMachine
from pipeline import Pipeline


def _load_env() -> None:
    """Load GROQ_API_KEY from ARGOS .env if not in env."""
    if os.environ.get("GROQ_API_KEY"):
        return
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip()


def setup_deal_and_parties(bridge_db: Path, deals_db: Path) -> tuple[WABridge, str]:
    """Crea 1 deal + 2 parties (dealer IT + seller DE) e attach deal."""
    deal = Deal(
        deal_id="DEAL-E2E-001",
        dealer_alias="D-FG-001",
        seller_alias="S-DE-042",
        vehicle_desc="BMW X3 xDrive 30d 2020 45000km",
    )
    DealStateMachine(deal, db_path=deals_db)

    bridge = WABridge(db_path=bridge_db, deals_db_path=deals_db)
    bridge.register_party("393331234567", "dealer", "D-FG-001", country="IT")
    bridge.register_party("4915112345678", "seller", "S-DE-042", country="DE")

    # Attach deal to both parties (so pipeline can resolve deal_id)
    import sqlite3
    conn = sqlite3.connect(bridge_db)
    try:
        conn.execute(
            "UPDATE bridge_parties SET current_deals = ? WHERE phone = ?",
            (json.dumps(["DEAL-E2E-001"]), "393331234567"),
        )
        conn.execute(
            "UPDATE bridge_parties SET current_deals = ? WHERE phone = ?",
            (json.dumps(["DEAL-E2E-001"]), "4915112345678"),
        )
        conn.commit()
    finally:
        conn.close()

    return bridge, "DEAL-E2E-001"


def test_full_deal_lifecycle_live_groq() -> bool:
    """Full 5-step lifecycle simulated: offer → accept → docs → payment → delivery."""
    print("\n=== test_full_deal_lifecycle_live_groq ===")
    _load_env()

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
        "dossier_id": "DEAL-E2E-001",
        "fee_eur": 1000,
        "delivery_days_est": 20,
        "documents_required": ["EUROCOC", "DAT", "DEKRA", "Libretto"],
        "transport_quote_eur": 850,
    }

    with tempfile.TemporaryDirectory() as td:
        bridge_db = Path(td) / "bridge.sqlite"
        deals_db = Path(td) / "deals.sqlite"
        cache_db = Path(td) / "analyzer-cache.sqlite"

        bridge, deal_id = setup_deal_and_parties(bridge_db, deals_db)
        analyzer = MessageAnalyzer(cache_db=cache_db)
        pipeline = Pipeline(bridge, analyzer, default_template_vars=template_vars)

        # Sequence di messaggi simulati real-world plausible
        # Format: (msg_id, role, phone, body, expected_intent_class, expected_state_after)
        sequence = [
            ("MSG-001", "dealer", "393331234567",
             "Mi interessa quella BMW X3, mandami il dossier completo",
             "offer", "accepted"),

            ("MSG-002", "seller", "4915112345678",
             "Yes, the BMW X3 is still available. Can you please send buyer details?",
             None, None),  # seller reply, no specific state transition needed

            ("MSG-003", "dealer", "393331234567",
             "Va bene, procediamo. Quali documenti servono?",
             "docs_request", "docs_shared"),

            ("MSG-004", "dealer", "393331234567",
             "Documenti ricevuti tutti ok. Quando posso pagare i mille euro?",
             "payment", "payment_pending"),

            ("MSG-005", "dealer", "393331234567",
             "Pagato cash a Foggia, possiamo procedere con il ritiro",
             "payment", "payment_confirmed"),

            ("MSG-006", "dealer", "393331234567",
             "Macingo ha confermato il pickup per giovedì, quando arriva?",
             "delivery", "transport_scheduled"),
        ]

        for msg_id, role, phone, body, expected_intent, expected_state in sequence:
            msg = InboundMsg(
                msg_id=msg_id, party_role=role, party_phone=phone,
                body=body, received_ts=1715680000,
            )
            bridge.ingest_inbound(msg)

        # Run pipeline single-pass
        results = pipeline.process_pending(max_iterations=20)

        print(f"\n  Processed {len(results)} messages")
        for r, (mid, role, phone, body, exp_intent, exp_state) in zip(results, sequence):
            transition = r.fsm_transition or "(no transition)"
            print(f"  {r.msg_id} role={role[:6]:6s} intent={r.intent:13s} "
                  f"sentiment={r.sentiment:9s} fsm: {transition:18s} → {r.state_after}")
            if r.error:
                print(f"    ERROR: {r.error}")

        # Final FSM state
        fsm = bridge._open_fsm(deal_id)
        final_state = fsm.current_state.id
        history = fsm.history()
        print(f"\n  Final state: {final_state}")
        print(f"  History: {len(history)} transitions: {[h['to_state'] for h in history]}")

        # Stats
        stats = bridge.stats()
        print(f"  Bridge stats: {stats}")

        # ASSERTS
        assert len(results) == 6, f"expected 6 results, got {len(results)}"
        # State machine should have progressed (at least 3 transitions for non-trivial deal)
        assert len(history) >= 3, f"expected ≥3 FSM transitions, got {len(history)}"
        # No scam detected on legitimate messages
        scam_msgs = [r for r in results if r.scam_flag]
        assert len(scam_msgs) == 0, f"unexpected scam flags: {[r.intent for r in scam_msgs]}"
        # Outbound candidates queued (at least 1 per dealer msg)
        dealer_msgs = sum(1 for _, role, *_ in sequence if role == "dealer")
        assert stats["outbound_total"] >= 3, (
            f"expected ≥3 outbound queued (≥1 per dealer msg), got {stats['outbound_total']}"
        )
        # All messages processed
        assert stats["inbound_pending"] == 0, "all messages should be processed"

        print("  PASS")
        return True


def test_scam_detection_live() -> bool:
    """Scam msg → FSM aborted + outbound NOT queued + alert flag."""
    print("\n=== test_scam_detection_live ===")
    _load_env()

    with tempfile.TemporaryDirectory() as td:
        bridge_db = Path(td) / "b.sqlite"
        deals_db = Path(td) / "d.sqlite"
        cache_db = Path(td) / "c.sqlite"

        bridge, deal_id = setup_deal_and_parties(bridge_db, deals_db)
        analyzer = MessageAnalyzer(cache_db=cache_db)
        pipeline = Pipeline(bridge, analyzer)

        scam_msg = InboundMsg(
            msg_id="SCAM-001", party_role="seller", party_phone="4915112345678",
            body="URGENT! Send €5000 via Western Union to reserve the BMW, "
                 "fiduciary will hold the car for you. Need money TODAY.",
            received_ts=1715680000,
        )
        bridge.ingest_inbound(scam_msg)

        results = pipeline.process_pending()
        assert len(results) == 1
        r = results[0]
        print(f"  intent={r.intent} scam={r.scam_flag} state={r.state_after} error={r.error}")
        assert r.scam_flag is True, f"expected scam_flag=True, got {r.scam_flag}"
        assert r.state_after == "aborted", f"expected aborted, got {r.state_after}"
        assert r.outbound_queued is False, "outbound should NOT be queued on scam"
        print("  PASS")
        return True


def main() -> int:
    tests = [test_full_deal_lifecycle_live_groq, test_scam_detection_live]
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
