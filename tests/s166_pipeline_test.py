#!/usr/bin/env python3
"""
S166 Pipeline test 5-step (D-11) — auto-eseguibili Step 1 SMOKE + Step 5 EDGE CASE.
Step 2/3/4 richiedono Luke wallclock + TEST_FOUNDER configurato → handoff prompt.

Run:
    cd ~/Documents/combaretrovamiauto-enterprise
    python3 tests/s166_pipeline_test.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wa-intelligence"))

import importlib
ra = importlib.import_module("response-analyzer")
import validator as v

RESULTS = {"session": "S166", "ts": datetime.now(timezone.utc).isoformat(),
           "tests": []}


def record(step, scenario, expected, actual, status):
    RESULTS["tests"].append({
        "step": step, "scenario": scenario, "expected": expected,
        "actual": actual, "status": status,
    })
    icon = "✅" if status == "PASS" else ("⚠️ " if status == "WARN" else "❌")
    print(f"{icon} {step} {scenario}: expected={expected} actual={actual}")


# === STEP 1 SMOKE — Day 1 template validation (dry-run, no real send) ===
def step1_smoke():
    print("\n=== STEP 1 SMOKE — Day 1 template validation ===")
    tpl_path = ROOT / "tools/outreach/day1_templates/stile_car_fg.txt"
    msg = tpl_path.read_text(encoding="utf-8").strip()
    dealer_state = {
        "current_step": "DAY1", "outbound_count": 0,
        "days_on_market": 0, "archetype": "NARCISO",
        "dealer_name": "Stile Car FG",
    }
    result = v.validate(msg, "DAY1_PREMIUM", dealer_state, dealer_id="", mode="shadow")
    status = "PASS" if result["result"] == "PASS" else "FAIL"
    record("Step1", "Day1 stile_car_fg validator",
           expected="PASS", actual=result["result"], status=status)
    if status == "FAIL":
        print(f"   check_failed={result.get('check_failed')} reason={result.get('reason')}")
    return status


# === STEP 5 EDGE CASE — classify_message + validator gates ===
def step5_edge_cases():
    print("\n=== STEP 5 EDGE CASE — validation gates ===")
    cases = [
        # (input, expected_type, description)
        ("ok",                 "POSITIVE",  "5.1 short positive"),
        ("STOP",               "NEGATIVE",  "5.2 opt-out STOP"),
        ("non mi interessa",   "NEGATIVE",  "5.3 negated positive"),
        ("vaffanculo",         "NEGATIVE",  "5.4 profanity → NEGATIVE"),
        ("",                   "UNKNOWN",   "5.5 empty input"),
        ("ma che cazzo è?",    "NEGATIVE",  "5.6 profanity + question → NEGATIVE override"),
        ("Mi spiegate meglio?", "CURIOSITY", "5.7 question mark fallback (no OBJ keyword)"),
    ]
    all_pass = True
    for body, exp, desc in cases:
        cls = ra.classify_message(body)
        actual = cls.get("type", "ERROR")
        ok = actual == exp
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        record("Step5", desc, expected=exp, actual=actual, status=status)

    # Validator edge case: fee leak in DAY1 should BLOCK
    print("\n--- 5.8 validator fee-leak DAY1 ---")
    leaky = "Ciao, fee €1000 a consegna. Buongiorno."
    dealer_state = {"current_step": "DAY1", "outbound_count": 0,
                    "days_on_market": 0, "archetype": "NARCISO"}
    res = v.validate(leaky, "DAY1_PREMIUM", dealer_state, dealer_id="", mode="shadow")
    status = "PASS" if res["result"] == "BLOCK" else "FAIL"
    if res["result"] != "BLOCK":
        all_pass = False
    record("Step5", "5.8 fee leak DAY1 should BLOCK",
           expected="BLOCK", actual=res["result"], status=status)

    return "PASS" if all_pass else "FAIL"


# === STEP 2/3/4 — placeholder handoff (require Luke + TEST_FOUNDER + wallclock) ===
def step234_handoff():
    print("\n=== STEP 2/3/4 — DEFERRED (wallclock + Luke action required) ===")
    deferred = [
        ("Step2", "Response INTEREST positiva",
         "Luke replies 'interessato' on TEST_FOUNDER → classifier=POSITIVE/CURIOSITY → Day 3 follow-up generated"),
        ("Step3", "Response STOP opt-out",
         "Luke replies 'STOP' on TEST_FOUNDER → classifier=NEGATIVE → dealer status=opted_out + soft-delete schedule 90gg"),
        ("Step4", "No-reply Day 7 trigger",
         "TEST_FOUNDER no response 7gg → scheduler trigger Day 7 follow-up → HITL approve gate"),
    ]
    for step, scenario, note in deferred:
        record(step, scenario, expected="WALLCLOCK", actual="DEFERRED", status="WARN")
        print(f"   → {note}")
    return "WARN"


def main():
    print("S166 Pipeline test 5-step (D-11)")
    print(f"Timestamp: {RESULTS['ts']}")

    s1 = step1_smoke()
    s5 = step5_edge_cases()
    s234 = step234_handoff()

    out_path = ROOT.parent / "venture-os/state/s166-results.json"
    if not out_path.parent.exists():
        out_path = ROOT / "state/s166-results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
    RESULTS["summary"] = {"step1_smoke": s1, "step5_edge_case": s5,
                          "step234_handoff": s234}
    out_path.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False))
    print(f"\n💾 Results: {out_path}")

    print("\n=== SUMMARY ===")
    print(f"Step 1 SMOKE:        {s1}")
    print(f"Step 5 EDGE CASE:    {s5}")
    print(f"Step 2/3/4 deferred: {s234} (handoff Luke)")

    exit_code = 0 if (s1 == "PASS" and s5 == "PASS") else 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
