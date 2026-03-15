"""
Merge all batch files into conversations_synthetic_v2.json
Run after all background agents complete.

Usage: python3 tools/merge_batches.py
"""
import json
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent.parent
TRAINING = BASE / "data" / "training"
OUTPUT = TRAINING / "conversations_synthetic_v2.json"

BATCH_FILES = [
    # TIER 1 — RAGIONIERE (already in v2 base)
    # BARONE (3 parts)
    "batch2_barone_p1.json",
    "batch2_barone_p2.json",
    "batch2_barone_p3.json",
    "batch2_barone.json",          # fallback se agent ha scritto file unico
    # PERFORMANTE
    "batch3_performante.json",
    # NARCISO (part1 già esistente + p23)
    "batch4_narciso.json",         # prime 20 già scritte
    "batch4_narciso_p23.json",     # conv 021-060
    # TECNICO
    "batch5_tecnico.json",
    # RELAZIONALE (3 parts)
    "batch6a_rela_p1.json",
    "batch6a_rela_p2.json",
    "batch6a_rela_p3.json",
    "batch6a_relazionale.json",    # fallback
    # CONSERVATORE (3 parts)
    "batch6b_cons_p1.json",
    "batch6b_cons_p2.json",
    "batch6b_cons_p3.json",
    "batch6b_conservatore.json",   # fallback
    # DELEGATORE (20 già + p23)
    "batch6c_delegatore.json",     # prime 20
    "batch6c_dele_p23.json",       # conv 021-060
    # OPPORTUNISTA (3 parts)
    "batch6d_oppo_p1.json",
    "batch6d_oppo_p2.json",
    "batch6d_oppo_p3.json",
    "batch6d_opportunista.json",   # fallback
    # VISIONARIO (3 parts)
    "batch6e_visi_p1.json",
    "batch6e_visi_p2.json",
    "batch6e_visi_p3.json",
    "batch6e_visionario.json",     # fallback
    # GOLD STANDARD (30 conv anchor examples)
    "batch_gold_standard.json",
    # TIER 2 — OVERLAP (7 coppie × 30 conv)
    "overlap_ragicons.json",   # RAGI×CONS
    "overlap_barodel.json",    # BARO×DELE
    "overlap_perfvisi.json",   # PERF×VISI
    "overlap_tecnragi.json",   # TECN×RAGI
    "overlap_narcbaro.json",   # NARC×BARO
    "overlap_relacon.json",    # RELA×CONS
    "overlap_oppodel.json",    # OPPO×DELE
    "batch7_overlap.json",     # fallback file unico
    # TIER 3 — Edge cases
    "batch8_edge_p1.json",
    "batch8_edge_p2.json",
    "batch8_edge_cases.json",  # fallback
    "batch9_regional.json",
    "batch9_regional_campania.json",
    "batch9_regional_puglia.json",
    "batch9_regional_sicilia.json",
    "batch10_multiturn.json",
    # S56 — adversarial + VISIONARIO boost
    "batch_adversarial_s56.json",
    "batch_visionario_s56.json",
]

def load_batch(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [SKIP] {path.name} not found yet")
        return []
    with open(path) as f:
        data = json.load(f)
    convs = data.get("conversations", [])
    print(f"  [OK]   {path.name}: {len(convs)} conversations")
    return convs

def main():
    print("=== ARGOS Dataset Merge ===\n")

    # Start from existing v2 (Batch 1 — RAGIONIERE)
    all_convs = []
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)
        batch1 = existing.get("conversations", [])
        # Only keep if they are RAGIONIERE (batch 1)
        batch1_only = [c for c in batch1 if c.get("primary_archetype") == "RAGIONIERE"]
        print(f"  [BASE] v2.json existing (RAGIONIERE): {len(batch1_only)} conversations")
        all_convs.extend(batch1_only)

    # Load all batch files
    for fname in BATCH_FILES:
        path = TRAINING / fname
        convs = load_batch(path)
        all_convs.extend(convs)

    # Deduplicate by ID
    seen_ids = set()
    deduped = []
    for c in all_convs:
        cid = c.get("id", "")
        if cid not in seen_ids:
            seen_ids.add(cid)
            deduped.append(c)

    print(f"\n  Total (deduped): {len(deduped)} conversations")

    # Distribution report
    dist = Counter(c.get("primary_archetype") for c in deduped)
    print("\n  Distribution:")
    archetypes = ["RAGIONIERE","BARONE","PERFORMANTE","NARCISO","TECNICO",
                  "RELAZIONALE","CONSERVATORE","DELEGATORE","OPPORTUNISTA","VISIONARIO"]
    total_tier1 = 0
    for arch in archetypes:
        n = dist.get(arch, 0)
        total_tier1 += n
        bar = "█" * (n // 5)
        status = "✅" if n >= 60 else f"⚠️  {n}/60"
        print(f"    {arch:<15} {n:>4} {bar}  {status}")

    ctx_dist = Counter(c.get("context") for c in deduped)
    print(f"\n  Context distribution: {dict(ctx_dist)}")

    reg_dist = Counter(c.get("regional_variant") for c in deduped)
    print(f"  Regional distribution: {dict(reg_dist)}")

    obj_dist = Counter(c.get("obj_triggered") for c in deduped)
    print(f"  OBJ distribution: {dict(sorted(obj_dist.items()))}")

    # Validation
    violations = []
    forbidden = ["CarFax", "Händlergarantie", "CoVe", "Anthropic", "non possiamo fatturare"]
    for c in deduped:
        for field in ["dealer_message", "optimal_response", "trap_response", "cot_reasoning"]:
            text = c.get(field, "")
            for f in forbidden:
                if f.lower() in text.lower():
                    violations.append(f"ID {c.get('id','?')}: '{f}' in {field}")

    if violations:
        print(f"\n  ⚠️  VIOLATIONS ({len(violations)}):")
        for v in violations[:10]:
            print(f"    {v}")
    else:
        print(f"\n  ✅ Zero violations in forbidden terms")

    # Write merged output
    output = {
        "version": "2.0-enterprise",
        "generated_by": "Claude Sonnet 4.6",
        "generated_at": "2026-03-15",
        "methodology": "DiaSynth+CoT enterprise grade",
        "total_conversations": len(deduped),
        "conversations": deduped,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\n  [SAVE] → {OUTPUT} ({size_kb:.0f} KB)")
    print(f"\n  Next: python3 src/marketing/train_svm_classifier.py")

if __name__ == "__main__":
    main()
