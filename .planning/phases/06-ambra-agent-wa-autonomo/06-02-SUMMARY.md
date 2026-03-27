---
status: complete
started: 2026-03-27
completed: 2026-03-27
---

# Summary: 06-02 Prompt Haiku con imperfezioni umane

## What was built
- Complete rewrite of SYSTEM_PROMPT with human imperfection instructions (lowercase, double ??, intercalari)
- JSON output format: `{"messages": ["msg1", "msg2"]}` instead of RISPOSTA_A/B
- Updated build_user_prompt with vehicle context and KB injection
- New parse_llm_responses with multi-fallback JSON parser (direct, markdown block, regex, legacy)
- Updated auto_approve_and_send to detect multi-msg and route to /send-multi
- Fallback template converted to multi-msg format

## Key files
- `wa-intelligence/response-analyzer.py` — SYSTEM_PROMPT, build_user_prompt, parse_llm_responses, auto_approve_and_send

## Deviations
None.
