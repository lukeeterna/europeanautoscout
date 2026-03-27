---
status: complete
started: 2026-03-27
completed: 2026-03-27
---

# Summary: 06-05 Anti-ban layer

## What was built
- HumanLike module with 6 methods:
  - logNormalDelay: realistic random delays (Box-Muller transform)
  - simulateTyping: composing indicator proportional to message length
  - simulateRecording: recording indicator before voice notes
  - checkOnWhatsApp: isRegisteredUser check before first contact
  - clearPresence: clear typing/recording state after send
  - isAllowedToSend: business hours enforcement
- Integrated in /send, /send-multi, /send-voice, scheduler Day3, scheduler Day7
- onWhatsApp check blocks sending to non-WA numbers
- Business hours enforcement returns 403 on all endpoints
- Scheduler uses log-normal delay between dealers (mean 5min) instead of fixed random
- response-analyzer uses differentiated delays: 20-60s for active conversation, log-normal for outreach

## Key files
- `wa-intelligence/wa-daemon.js` — HumanLike object, integrated in all endpoints + scheduler
- `wa-intelligence/response-analyzer.py` — differentiated sleep in auto_approve_and_send

## Deviations
None.
