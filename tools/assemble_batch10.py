#!/usr/bin/env python3
"""Assembles batch10_multiturn.json from part files. Run once then delete."""
import json, os

BASE = "/Users/macbook/Documents/combaretrovamiauto-enterprise/data/training"
parts = [f"{BASE}/batch10_part{i}.json" for i in range(1, 9)]

all_convs = []
for p in parts:
    with open(p, encoding="utf-8") as f:
        all_convs.extend(json.load(f))

# Target distribution: obj_to_int:15, cold_to_open:15, interest_cold:10, test_conv:10
from collections import defaultdict
by_type = defaultdict(list)
for c in all_convs:
    by_type[c["sequence_type"]].append(c)

targets = {
    "objection_to_interest": 15,
    "cold_to_opening": 15,
    "interest_to_cold": 8,   # only 8 exist
    "test_to_converted": 12, # take all 13 minus 1
}

selected = []
for stype, count in targets.items():
    avail = by_type[stype]
    selected.extend(avail[:count])

# If still under 50, take more from largest bucket
if len(selected) < 50:
    used_ids = {c["id"] for c in selected}
    extras = [c for c in all_convs if c["id"] not in used_ids]
    selected.extend(extras[:50 - len(selected)])

assert len(selected) == 50, f"Expected 50, got {len(selected)}"

output = {
    "version": "2.0-enterprise",
    "generated_by": "Claude Sonnet 4.6",
    "generated_at": "2026-03-15",
    "total_conversations": 50,
    "conversations": selected,
}

out_path = f"{BASE}/batch10_multiturn.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Written: {out_path}")
from collections import Counter
print("sequence_type:", dict(Counter(c["sequence_type"] for c in selected)))
print("archetype:    ", dict(Counter(c["primary_archetype"] for c in selected)))
print("regional:     ", dict(Counter(c["regional_variant"] for c in selected)))

# Cleanup parts
for p in parts:
    os.remove(p)
print("Part files removed.")
