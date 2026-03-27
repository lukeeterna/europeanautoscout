---
status: complete
started: 2026-03-27
completed: 2026-03-27
---

# Summary: 06-04 Knowledge base ARGOS

## What was built
- argos_knowledge_base.md with 7 sections: service, costs, timing, documents, warranty, transport, objections
- 8 common objection responses calibrated for dealer tone
- KB loaded at analyzer startup, parsed into sections
- Selective KB injection in LLM prompt based on classification type
- CURIOSITY → service + costs, OBJ-2 → costs + transport, OBJ-4 → warranty + documents, etc.
- Max 1500 chars injected to avoid bloating prompt token budget

## Key files
- `wa-intelligence/argos_knowledge_base.md` — new file
- `wa-intelligence/response-analyzer.py` — _load_knowledge_base, _get_relevant_kb

## Deviations
None.
