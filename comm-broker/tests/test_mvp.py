"""ARGOS comm-broker MVP smoke test.

Verifica:
  1. image_shield.protect() pipeline funzionante su synthetic image
  2. DealStateMachine 7-step transitions + SQLite persistence
  3. Round-trip: state machine restore from DB
"""
from __future__ import annotations

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
import image_shield
import deal_state_machine
from deal_state_machine import Deal, DealStateMachine


def make_synthetic_image(path: str, size=(1200, 800)) -> None:
    """Genera immagine sintetica colorata per test (no dipendenza da Mobile.de)."""
    img = Image.new("RGB", size, color=(180, 200, 220))
    # Aggiungi qualche feature visiva per phash discrimination
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 400, 300], fill=(200, 150, 100))
    draw.ellipse([500, 200, 800, 500], fill=(100, 150, 200))
    draw.polygon([(900, 100), (1100, 300), (950, 600)], fill=(150, 100, 150))
    img.save(path, "JPEG", quality=95)


def test_image_shield() -> bool:
    print("\n=== test_image_shield ===")
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.jpg"
        out = Path(td) / "out.jpg"
        make_synthetic_image(str(src))
        result = image_shield.protect(
            str(src), str(out), dossier_id="TEST-001"
        )
        assert out.exists(), "output missing"
        assert result["orig_size"] != result["final_size"], "size unchanged (crop failed)"
        # Verify final size is ~65% area of orig (D-25 spec)
        ow, oh = result["orig_size"]
        fw, fh = result["final_size"]
        area_ratio = (fw * fh) / (ow * oh)
        assert 0.60 <= area_ratio <= 0.70, f"area ratio {area_ratio:.3f} out of D-25 spec ~0.65"
        # Verify phash hamming distance ≥10 (D-25 target ≥20 con anche reverse-search test,
        # qui solo synthetic differential)
        hd = result["hamming_distance"]
        assert hd >= 10, f"phash hamming distance {hd} too low (target ≥10 for synthetic)"
        print(f"  orig {result['orig_size']} → final {result['final_size']}")
        print(f"  area ratio: {area_ratio:.3f} (D-25 spec 0.65)")
        print(f"  phash hamming: {hd} (target ≥10 synthetic, ≥20 reverse-search reale)")
        print("  PASS")
        return True


def test_state_machine() -> bool:
    print("\n=== test_state_machine ===")
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "deals.sqlite"
        deal = Deal(
            deal_id="DEAL-SMOKE-001",
            dealer_alias="D-FG-001",
            seller_alias="S-DE-042",
            vehicle_desc="BMW X3 2020 45000km",
        )
        fsm = DealStateMachine(deal, db_path=db)
        assert fsm.current_state.id == "offer_sent"

        # Forward path complete
        fsm.accept()
        assert fsm.current_state.id == "accepted"
        fsm.share_docs()
        assert fsm.current_state.id == "docs_shared"
        fsm.request_payment()
        fsm.confirm_payment()
        fsm.schedule_transport()
        fsm.start_transit()
        fsm.deliver()
        assert fsm.current_state.id == "delivered"

        # History should have 7 transitions
        hist = fsm.history()
        assert len(hist) == 7, f"expected 7 transitions, got {len(hist)}"
        events = [t["event"] for t in hist]
        expected = [
            "accept", "share_docs", "request_payment", "confirm_payment",
            "schedule_transport", "start_transit", "deliver",
        ]
        assert events == expected, f"transition order wrong: {events}"
        print(f"  7 transitions: {' → '.join(t['to_state'] for t in hist)}")
        print("  PASS")
        return True


def test_state_machine_restore() -> bool:
    """Restore stato da SQLite (caso restart processo)."""
    print("\n=== test_state_machine_restore ===")
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "deals.sqlite"
        # Sessione 1: portala a accepted
        deal = Deal(
            deal_id="DEAL-RESTORE-001",
            dealer_alias="D-001",
            seller_alias="S-001",
        )
        fsm1 = DealStateMachine(deal, db_path=db)
        fsm1.accept()
        fsm1.share_docs()
        assert fsm1.current_state.id == "docs_shared"

        # Sessione 2: stesso deal_id, nuovo istanza FSM
        deal2 = Deal(
            deal_id="DEAL-RESTORE-001",
            dealer_alias="D-001",
            seller_alias="S-001",
        )
        fsm2 = DealStateMachine(deal2, db_path=db)
        assert fsm2.current_state.id == "docs_shared", (
            f"restore failed: expected docs_shared, got {fsm2.current_state.id}"
        )
        # Continua flow
        fsm2.request_payment()
        assert fsm2.current_state.id == "payment_pending"
        print(f"  restored at: docs_shared → request_payment → {fsm2.current_state.id}")
        print("  PASS")
        return True


def test_state_machine_abort() -> bool:
    print("\n=== test_state_machine_abort ===")
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "deals.sqlite"
        deal = Deal(deal_id="DEAL-ABORT-001", dealer_alias="D", seller_alias="S")
        fsm = DealStateMachine(deal, db_path=db)
        fsm.accept()
        fsm.share_docs()
        fsm.abort()
        assert fsm.current_state.id == "aborted"
        print("  PASS")
        return True


def main() -> int:
    tests = [
        test_image_shield,
        test_state_machine,
        test_state_machine_restore,
        test_state_machine_abort,
    ]
    results = []
    for t in tests:
        try:
            ok = t()
            results.append((t.__name__, ok))
        except AssertionError as e:
            print(f"  FAIL: {e}")
            results.append((t.__name__, False))
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            results.append((t.__name__, False))

    print("\n=== SUMMARY ===")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
