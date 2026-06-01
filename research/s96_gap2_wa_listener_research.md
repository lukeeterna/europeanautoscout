# S96 GAP-2: WA Incoming Message Handling & Intent Parsing - Research

**Researched:** 2026-04-01
**Domain:** WhatsApp incoming message processing, intent parsing, LLM-based extraction, human-in-the-loop approval
**Confidence:** HIGH (based on existing codebase analysis + verified sources)

---

## Summary

ARGOS already has a mature WA daemon (`wa-intelligence/wa-daemon.js`) that handles incoming messages via `message_create` event, persists them to SQLite, buffers multi-message inputs with debounce (15s silence / 45s hard cap), and triggers a Python response-analyzer via `spawn()`. The response-analyzer uses keyword-based classification (POSITIVE/NEGATIVE/CURIOSITY/OBJECTION types) followed by LLM generation via OpenRouter (Claude Haiku 4.5) for response drafting. Human-in-the-loop approval happens via Telegram bot (`telegram-handler.py`) with `/approva`, `/modifica`, `/rifiuta` commands.

**What's MISSING is the "request parser" flow**: when a dealer sends a vehicle request ("cerco BMW X3 2022 budget 35k"), the system currently classifies it as POSITIVE/CURIOSITY and generates a conversational reply. It does NOT extract structured search parameters (make, model, year, budget) to feed into the scraper/CoVe pipeline. This is the GAP-2 that needs closing.

**Primary recommendation:** Add a new classification category `VEHICLE_REQUEST` to the existing keyword classifier, then use Claude Haiku via OpenRouter (already integrated, already paid) to extract structured parameters into JSON. Route the structured query to a new `request_handler.py` that triggers the existing scraper pipeline. ZERO new infrastructure needed -- extend what exists.

---

## Existing Architecture (MUST NOT reinvent)

### What Already Works

| Component | File | What It Does |
|-----------|------|--------------|
| WA Daemon | `wa-intelligence/wa-daemon.js` | message_create listener, SQLite persist, debounce buffer, HTTP server :9191 |
| Response Analyzer | `wa-intelligence/response-analyzer.py` | Keyword classifier + LLM response generation via OpenRouter |
| Telegram HITL | `wa-intelligence/telegram-handler.py` | /approva /modifica /rifiuta commands, polling every 3s |
| Knowledge Base | `wa-intelligence/argos_knowledge_base.md` | Sections loaded selectively per classification type |
| CoVe Engine | `src/cove/cove_engine_v4.py` | 842-line scoring engine (DO NOT MODIFY) |
| Scrapers | `tools/scrapers/` | 28 portals, generic_scraper.py + portal_profiles.py |
| Pipeline Orchestrator | `src/cove/pipeline_orchestrator.py` | 7-state pipeline: DISCOVERED -> SCORED -> ... -> DELIVERED |
| CRM | `tools/dealer_crm.py` | Dealer management, pipeline status tracking |
| Fee Calculator | `tools/fee_calculator.py` | Fee calculation ready |
| PDF Generator | `tools/scripts/pdf_generator_enterprise.py` | Dossier generation ready |

### Current Message Flow

```
Dealer sends WA msg
  -> wa-daemon.js: message_create event
  -> lookupDealer(phone) — ONLY processes known dealers in pipeline
  -> persistInboundMessage() — SQLite insert
  -> bufferMessage() — 15s debounce, 45s hard cap
  -> flushBuffer() — aggregates multi-msg
  -> triggerAnalyzer() — spawns python3 response-analyzer.py
    -> classify_message() — keyword matching (POSITIVE/NEGATIVE/CURIOSITY/OBJECTION)
    -> call_llm() — OpenRouter Claude Haiku 4.5 for response generation
    -> save_pending_reply() — stores in pending_replies table
    -> Telegram alert with reply text for human approval
  -> Telegram handler: /approva -> sends via wa-daemon HTTP POST /send-multi
```

### Key Architectural Decisions Already Made
- **OpenRouter for LLM** (env: `OPENROUTER_API_KEY`) -- Claude Haiku 4.5 via `anthropic/claude-haiku-4-5`
- **SQLite WAL mode** for all persistence (no Redis, no queues)
- **better-sqlite3** in Node, **sqlite3 stdlib** in Python
- **spawn() pattern** for Node->Python communication (not HTTP webhook between services)
- **PM2** for process management (wa-daemon, dashboard, tg-bot)
- **Telegram** for human approval (not email, not dashboard)
- **Anti-ban**: business hours check, daily limit 30, human-like typing simulation, log-normal delays
- **Message buffer**: debounce multi-input before analysis

---

## 1. WA Daemon Incoming Message Architecture

### Current Pattern: EventEmitter (CORRECT for this scale)

**Confidence: HIGH** -- verified from codebase

The wa-daemon uses `client.on('message_create', ...)` which is the correct event for whatsapp-web.js (more reliable than `message` event since 2025+). The current architecture is:

```
EventEmitter (message_create) -> In-Process Handler -> spawn() Python Analyzer
```

This is the RIGHT pattern for ARGOS scale (50-100 msgs/day max, 12 dealers). Alternatives considered and rejected:

| Pattern | Why NOT for ARGOS |
|---------|-------------------|
| HTTP Webhook (wa-daemon -> Flask/FastAPI) | Adds network hop, new service to manage, PM2 process. Overkill for 50 msg/day |
| Redis Message Queue | New dependency, new infra. ZERO COSTI rule violated if external Redis needed |
| RabbitMQ/Kafka | Enterprise complexity for 12 dealers. Absurd |
| Polling DB | Latency, wasteful, already have real-time events |

**Recommendation: KEEP the current spawn() pattern.** Add the request parsing as a new Python script (`request_handler.py`) called the same way the response-analyzer is called. The wa-daemon already has the perfect architecture.

### Reliability Considerations

The existing wa-daemon handles reconnection well:
- PM2 auto-restart on disconnect (`process.exit(1)` on disconnected event)
- LocalAuth session persistence (no QR re-scan on restart)
- Telegram alerts on connection state changes
- The `@lid` format handling (WA 2025+ new format) is already implemented

**Known issue from whatsapp-web.js**: duplicate messages can occur on reconnection. The daemon uses `INSERT OR IGNORE` with unique message IDs, which provides basic dedup. However, the `wa_msg_id` field should be the primary dedup key.

---

## 2. Intent Parsing for Vehicle Requests

### The Problem

Dealer sends: "cerco BMW X3 2022 budget 35k km sotto 50mila"
Current system classifies as: `CURIOSITY` or `POSITIVE` (keyword match)
What's needed: Extract `{make: "BMW", model: "X3", year: 2022, max_price: 35000, max_km: 50000}`

### Approach: Hybrid Keyword + LLM (RECOMMENDED)

**Confidence: HIGH**

Three-layer approach, from cheapest to most powerful:

#### Layer 1: Keyword Detection (ZERO cost)

Add `VEHICLE_REQUEST` to the existing `PATTERNS` dict in response-analyzer.py:

```python
'VEHICLE_REQUEST': {
    'exact': [
        'cerco', 'cercami', 'mi trovi', 'hai disponibile', 'mi serve',
        'sto cercando', 'avete', 'hai qualcosa', 'budget', 'trovami',
        'mi interessa una', 'mi interessa un', 'voglio', 'vorrei',
        'preventivo', 'proposta per', 'disponibilita',
        # Brand triggers
        'bmw', 'mercedes', 'audi', 'porsche', 'lamborghini',
        'ferrari', 'mclaren', 'range rover', 'land rover',
        # Model triggers
        'x3', 'x5', 'x7', 'serie 3', 'serie 5', 'classe c',
        'classe e', 'gle', 'glc', 'q5', 'q7', 'a4', 'a6',
        'cayenne', 'macan', 'panamera', 'urus', 'huracan',
    ],
    'weight': 1.0,
}
```

When `VEHICLE_REQUEST` is detected AND at least one brand/model keyword is present, route to LLM extraction.

#### Layer 2: LLM Structured Extraction (via existing OpenRouter)

Use Claude Haiku 4.5 (already configured) with a focused extraction prompt:

```python
EXTRACTION_PROMPT = """Estrai i parametri di ricerca veicolo dal messaggio del dealer.
Rispondi SOLO con JSON valido. Se un campo non e' specificato, usa null.

{
  "make": "marca (BMW/Mercedes/Audi/Porsche/etc)",
  "model": "modello (X3/GLC/Q5/etc) o null",
  "year_min": numero o null,
  "year_max": numero o null,
  "max_price_eur": numero intero o null,
  "max_km": numero intero o null,
  "fuel": "benzina/diesel/ibrido/elettrico o null",
  "color": "colore o null",
  "features": ["lista features specifiche"] o [],
  "notes": "altri dettagli rilevanti o null",
  "confidence": 0.0-1.0
}

Messaggio dealer: "{msg}"
"""
```

**Why LLM beats regex for Italian dealer messages:**
- Dealers write in dialect/informal: "mi servirebbe na x3 del 22 sotto i 35 mila"
- Abbreviations: "merc classe c", "bm x5", "audi a6 avant 2.0 tdi"
- Implicit info: "stessa cosa ma diesel" (refers to previous context)
- Price formats: "35k", "35mila", "35.000", "trentacinque", "budget 35"
- Mixed Italian/dialect: "cercami na machina tedesca buona, budget 40"

Regex would need 200+ patterns for Italian informal. Haiku handles all of these natively.

#### Layer 3: Human Validation via Telegram

After LLM extraction, send structured result to Telegram for confirmation:

```
RICHIESTA VEICOLO da Stile Car (Domenico)

BMW X3 | 2022+ | Budget: 35.000 | Max KM: 50.000
Fuel: diesel | Color: qualsiasi

[CONFERMA] [MODIFICA] [IGNORA]
```

Only after human confirmation, trigger the search pipeline.

### Why NOT pure regex

| Scenario | Regex | LLM |
|----------|-------|-----|
| "BMW X3 2022 35k" | Works | Works |
| "na macchina tedesca budget 40" | Fails | Works |
| "stessa cosa ma in diesel" | Fails | Works (with history) |
| "hai qualcosa sotto i 30 mila tipo suv?" | Partial | Works |
| Cost per extraction | FREE | ~$0.003 |

### Why NOT dedicated NLP model

- No Italian automotive NLP model exists that we could use for free
- Training a custom model requires labeled data we don't have
- spaCy NER for Italian doesn't know car models
- Haiku at $0.003/msg is effectively free at 50-100 msgs/day

---

## 3. Cost Analysis: Claude Haiku via OpenRouter

**Confidence: HIGH** -- verified from OpenRouter pricing page and existing code

### Pricing (verified April 2026)

| Model | Input ($/MTok) | Output ($/MTok) | Via |
|-------|----------------|------------------|-----|
| Claude Haiku 4.5 | $1.00 | $5.00 | OpenRouter |

### Per-Message Cost Estimate

For vehicle request extraction:
- System prompt: ~300 tokens
- User message + dealer context: ~200 tokens
- JSON output: ~150 tokens
- **Total per extraction: ~$0.001 input + $0.00075 output = ~$0.002**

For response generation (current usage):
- System prompt: ~800 tokens (SYSTEM_PROMPT is large)
- User prompt + KB section + history: ~1500 tokens
- Output: ~300 tokens
- **Total per response: ~$0.0023 input + $0.0015 output = ~$0.004**

### Monthly Cost at Scale

| Messages/day | Extractions/day | Monthly Cost |
|-------------|-----------------|--------------|
| 10 | 3 | $0.18 |
| 50 | 15 | $0.90 |
| 100 | 30 | $1.80 |

**This is NEGLIGIBLE.** The existing response-analyzer already uses Haiku via OpenRouter. Adding extraction costs less than $2/month at peak projected volume.

### ZERO COSTI Compliance

The OpenRouter API key is already active and being used (`OPENROUTER_API_KEY` in .env). This is NOT a new cost -- it's incremental usage of an existing service. At $2/month peak, this falls under "gia' pagato" territory.

---

## 4. Extending wa-daemon.js Architecture

### How to Add Request Parsing (CORRECT approach)

**DO NOT add HTTP webhooks or new services.** Extend the existing pattern:

```
wa-daemon.js
  -> message_create
  -> handleInboundMessage()
  -> bufferMessage() + flushBuffer()
  -> triggerAnalyzer()  <-- EXISTING: generates responses
  -> triggerRequestParser()  <-- NEW: extracts vehicle requests
```

**Option A: Single Python script (RECOMMENDED)**

Extend `response-analyzer.py` to also detect and extract vehicle requests. When `classify_message()` returns `VEHICLE_REQUEST`, run the extraction prompt instead of the response prompt. This keeps one script, one LLM call pattern, one DB access pattern.

**Option B: Separate request_handler.py**

New script `wa-intelligence/request_handler.py` called by wa-daemon when analyzer detects `VEHICLE_REQUEST`. Better separation of concerns but adds another script to maintain.

**Recommendation: Option A** -- extend response-analyzer.py. The classification already routes to different behavior based on type. Adding `VEHICLE_REQUEST` routing is natural.

### Integration Flow

```
1. classify_message() detects VEHICLE_REQUEST
2. call_llm() with EXTRACTION_PROMPT -> structured JSON
3. validate extraction (make/model present, price reasonable)
4. save_vehicle_request() -> new table `vehicle_requests` in SQLite
5. Send Telegram alert with extracted params + [CONFERMA] [MODIFICA] [IGNORA]
6. On /conferma -> trigger search:
   a. Run scrapers for matching vehicles
   b. Run CoVe scoring
   c. Select top 3-5 opportunities
   d. Generate mini-dossier
   e. Send to Telegram for final review before WA delivery
```

### New SQLite Table

```sql
CREATE TABLE IF NOT EXISTS vehicle_requests (
    id              TEXT PRIMARY KEY,
    dealer_id       TEXT NOT NULL,
    dealer_name     TEXT,
    raw_message     TEXT,
    make            TEXT,
    model           TEXT,
    year_min        INTEGER,
    year_max        INTEGER,
    max_price_eur   INTEGER,
    max_km          INTEGER,
    fuel            TEXT,
    color           TEXT,
    features        TEXT,  -- JSON array
    notes           TEXT,
    confidence      REAL,
    status          TEXT DEFAULT 'PENDING',  -- PENDING/CONFIRMED/SEARCHING/RESULTS_READY/DELIVERED/CANCELLED
    results_count   INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    confirmed_at    TEXT,
    delivered_at    TEXT
);
```

---

## 5. Human-in-the-Loop Patterns

### Current HITL (Already Excellent)

**Confidence: HIGH** -- verified from codebase

The existing system has a solid HITL flow:

1. **wa-daemon** detects message, runs analyzer
2. **response-analyzer** generates 2-3 candidate replies
3. **pending_replies** table stores candidates (approved=NULL)
4. **telegram-handler** sends alert with reply text
5. **Human** reviews and uses `/approva`, `/modifica`, or `/rifiuta`
6. **telegram-handler** updates DB and triggers send via wa-daemon HTTP

### Enhancement for Vehicle Requests

Add Telegram inline keyboard buttons (the telegram-handler already supports `reply_markup`):

```python
# In Telegram alert for vehicle request
reply_markup = {
    "inline_keyboard": [[
        {"text": "CONFERMA", "callback_data": f"vreq_confirm_{request_id}"},
        {"text": "MODIFICA", "callback_data": f"vreq_edit_{request_id}"},
        {"text": "IGNORA", "callback_data": f"vreq_ignore_{request_id}"},
    ]]
}
```

### Escalation Rules

| Scenario | Action |
|----------|--------|
| VEHICLE_REQUEST with confidence >= 0.8 | Auto-extract, send to Telegram for confirm |
| VEHICLE_REQUEST with confidence < 0.8 | Flag as AMBIGUOUS, ask human to clarify |
| NEGATIVE | Auto-close, notify Telegram |
| CURIOSITY about service | LLM response -> Telegram approval (existing) |
| OBJECTION | LLM response -> Telegram approval (existing) |
| UNKNOWN classification | Flag HUMAN_NEEDED, full message to Telegram |

### Best Practices from Production Systems

From n8n workflow patterns and Telegram bot implementations:
- **Timeout**: If no human response within 2 hours during business hours, send auto-acknowledgment to dealer ("sto verificando, ti aggiorno a breve")
- **Double-click prevention**: Disable inline buttons after first click (mark request as CONFIRMED in DB)
- **Audit trail**: Log every human decision with timestamp in `audit_log` table (already exists)
- **Feedback loop**: Track which extractions were modified vs confirmed to improve prompts over time

---

## 6. Message Deduplication and Idempotency

### Current State

**Confidence: HIGH** -- verified from codebase

The wa-daemon already has basic dedup:
- `INSERT OR IGNORE INTO messages` with unique `id` (generated: `msg_{timestamp}_{random}`)
- `wa_msg_id` field stores the WhatsApp message ID

### Problem

The `id` field is generated per-receipt, not based on the actual WhatsApp message ID. If the same message is received twice (reconnection scenario), a new `id` is generated, but `wa_msg_id` is the same. However, `INSERT OR IGNORE` only checks the `id` PRIMARY KEY, not `wa_msg_id`.

### Fix (SIMPLE)

Add a UNIQUE constraint on `wa_msg_id`:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_wa_msg_id
ON messages(wa_msg_id) WHERE wa_msg_id IS NOT NULL;
```

And use `INSERT OR IGNORE` which will now catch duplicates on BOTH `id` and `wa_msg_id`.

### Additional Dedup Layer for Request Processing

For vehicle requests, use a processing lock:

```python
# Before processing a request
def is_already_processing(db_path, dealer_id, raw_message_hash):
    """Check if we already have a pending request with same content."""
    con = sqlite3.connect(db_path)
    exists = con.execute("""
        SELECT COUNT(*) FROM vehicle_requests
        WHERE dealer_id = ? AND status IN ('PENDING', 'CONFIRMED', 'SEARCHING')
        AND created_at > datetime('now', '-1 hour')
    """, [dealer_id]).fetchone()[0]
    con.close()
    return exists > 0
```

### Reconnection Handling

The wa-daemon already handles this well with PM2 + `process.exit(1)` on disconnect. The `message_create` event with `msg.id.id` provides the canonical dedup key. Enhancement:

```javascript
// Add to handleInboundMessage
const seenSet = new Set();  // in-memory LRU
const SEEN_TTL = 300000;  // 5 minutes

if (seenSet.has(msg.id?.id)) {
    log('INFO', `Dedup: skipping already-seen msg ${msg.id?.id}`);
    return;
}
seenSet.add(msg.id?.id);
setTimeout(() => seenSet.delete(msg.id?.id), SEEN_TTL);
```

---

## 7. Framework Choice: Response to Webhook/API Needs

### Current Stack

- **wa-daemon.js**: Node.js raw HTTP (http.createServer) on port 9191
- **dashboard**: FastAPI (already chosen, already running on port 8080)
- **scripts**: Python CLI tools called via spawn()

### Recommendation: DO NOT add another framework

**Confidence: HIGH**

The question "Flask vs FastAPI vs raw HTTP for webhook listener" is the WRONG question for ARGOS. Here's why:

1. The wa-daemon's HTTP server on :9191 already handles `/send`, `/send-multi`, `/send-voice`, `/qr`
2. The dashboard is already FastAPI on :8080
3. Adding a THIRD HTTP service for "webhook listening" is unnecessary complexity

The incoming messages come via whatsapp-web.js EventEmitter, NOT via HTTP webhook. There's no external service calling an HTTP endpoint. The entire flow is in-process.

**If you ever need a Python HTTP endpoint** (e.g., for the dashboard to trigger a search), the FastAPI dashboard at :8080 is the right place. It already has auth, templates, and DB access.

### When You Would Need a New Service

Only if:
- An external system needs to push data to ARGOS (not the case)
- You move to WhatsApp Cloud API (which uses HTTP webhooks from Meta)
- You add a web-based interface for request submission (beyond Telegram)

None of these apply now. The spawn() pattern from Node->Python is the correct architecture for the current scale.

---

## Architecture Pattern: Request Handler Integration

### Recommended Project Structure

```
wa-intelligence/
  wa-daemon.js                    # EXISTING - no changes needed to message flow
  response-analyzer.py            # EXTEND - add VEHICLE_REQUEST classification + extraction
  request_handler.py              # NEW - handles confirmed vehicle requests
  telegram-handler.py             # EXTEND - add /conferma /modifica_req commands
  argos_knowledge_base.md         # EXISTING
  time-context.js                 # EXISTING

tools/
  scrapers/                       # EXISTING - invoked by request_handler
  dealer_crm.py                   # EXISTING - dealer context

src/cove/
  cove_engine_v4.py               # EXISTING - DO NOT MODIFY, invoked by request_handler
  pipeline_orchestrator.py        # EXISTING - can feed results
```

### Data Flow: Dealer Request to Vehicle Delivery

```
[1] Dealer WA: "cerco BMW X3 2022 budget 35k diesel"
    |
[2] wa-daemon.js -> bufferMessage() -> flushBuffer()
    |
[3] response-analyzer.py:
    classify_message() -> VEHICLE_REQUEST (keyword: "cerco" + "bmw" + "x3")
    |
[4] call_llm(EXTRACTION_PROMPT) -> {make: "BMW", model: "X3", year_min: 2022, ...}
    |
[5] save_vehicle_request() -> SQLite vehicle_requests table
    |
[6] Telegram: "RICHIESTA: BMW X3 2022+ diesel <35k [CONFERMA] [MODIFICA] [IGNORA]"
    |
[7] Human: clicks [CONFERMA]
    |
[8] telegram-handler.py: updates status='CONFIRMED'
    triggers: python3 request_handler.py --request-id REQ_xxxx
    |
[9] request_handler.py:
    a. Reads request params from DB
    b. Configures SearchProfile for relevant portals (DE/NL/BE/AT)
    c. Runs scrapers (mobile.de, autoscout24.de, etc.)
    d. Runs CoVe scoring on results
    e. Selects top 3-5 opportunities
    f. Generates mini-dossier text
    g. Saves results to DB, updates status='RESULTS_READY'
    h. Sends results to Telegram for review
    |
[10] Human reviews, approves top picks
    |
[11] telegram-handler: triggers WA send with vehicle proposals
    wa-daemon HTTP POST /send-multi with formatted vehicle cards
```

---

## Common Pitfalls

### Pitfall 1: Over-engineering the Message Bus
**What goes wrong:** Adding Redis/RabbitMQ for 50 messages/day
**Why it happens:** Tutorial-driven development, "production-grade" cargo cult
**How to avoid:** SQLite + spawn() handles 1000x the current volume. Add queues at 10k msg/day, not 50.

### Pitfall 2: Auto-sending Without Human Review
**What goes wrong:** LLM generates wrong vehicle params, system searches and sends irrelevant results
**Why it happens:** Rushing to "full automation"
**How to avoid:** ALWAYS require human confirmation for vehicle requests. The existing HITL pattern is the right one.

### Pitfall 3: Ignoring Message Context
**What goes wrong:** Dealer says "stessa cosa ma diesel" and system can't parse without history
**Why it happens:** Treating each message independently
**How to avoid:** Include last 3-5 messages in LLM context (response-analyzer already does this via `msg_history`)

### Pitfall 4: Not Handling Partial Requests
**What goes wrong:** Dealer says "hai qualcosa di tedesco?" -- no specific make/model/budget
**Why it happens:** Expecting fully specified requests
**How to avoid:** LLM extracts what's available, flags missing fields, HITL asks if should request more info from dealer

### Pitfall 5: Duplicate Search Triggers
**What goes wrong:** Same request triggers multiple searches (reconnection, double-tap)
**Why it happens:** No idempotency on request processing
**How to avoid:** Check `vehicle_requests` table for recent pending/searching entries for same dealer before creating new request

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM structured extraction | Custom regex parser for Italian car requests | Claude Haiku via OpenRouter (already integrated) | Italian informal language is unpredictable, Haiku handles it at $0.002/msg |
| Message queue | Redis/RabbitMQ infrastructure | SQLite tables + spawn() (existing pattern) | 50 msg/day doesn't need distributed systems |
| NLP entity extraction | spaCy/BERT Italian model | Claude Haiku prompt | No free Italian automotive NER model exists |
| Webhook framework | New Flask/FastAPI service | Extend wa-daemon HTTP or dashboard FastAPI | Don't add a 4th service to PM2 |
| Session management | Custom reconnection logic | PM2 auto-restart + LocalAuth (existing) | Already production-tested |

---

## Code Examples

### Vehicle Request Classification (extend existing PATTERNS)

```python
# Add to response-analyzer.py PATTERNS dict
'VEHICLE_REQUEST': {
    'exact': [
        'cerco', 'cercami', 'mi trovi', 'trovami', 'hai disponibile',
        'mi serve', 'sto cercando', 'avete', 'hai qualcosa',
        'budget', 'preventivo', 'proposta per', 'disponibilita',
        'voglio', 'vorrei', 'mi interessa una', 'mi interessa un',
        # Brands (triggers high confidence when combined with request verbs)
        'bmw', 'mercedes', 'audi', 'porsche', 'lamborghini',
        'ferrari', 'mclaren', 'range rover',
        # Common models
        'x3', 'x5', 'x7', 'serie 3', 'serie 5',
        'classe c', 'classe e', 'gle', 'glc',
        'q5', 'q7', 'a4', 'a6', 'cayenne', 'macan',
    ],
    'weight': 1.2,  # Higher weight to win over POSITIVE/CURIOSITY
}
```

### LLM Extraction Prompt

```python
VEHICLE_EXTRACTION_SYSTEM = """Sei un parser di richieste veicoli. Estrai i parametri dal messaggio del dealer.
Rispondi ESCLUSIVAMENTE con JSON valido. Nessun testo fuori dal JSON.
Se un campo non e' specificato, usa null. Deduci il ragionevole (es. "del 22" = year_min: 2022).

Marche supportate: BMW, Mercedes-Benz, Audi, Porsche, Lamborghini, Ferrari, McLaren, Land Rover
Mercati: DE, NL, BE, AT, FR, SE (tutti EU)
Budget: in EUR. "35k" = 35000, "35mila" = 35000
KM: "50mila km" = 50000, "sotto i 50" (nel contesto km) = 50000"""

VEHICLE_EXTRACTION_USER = """Messaggio dealer: "{msg}"

Rispondi con:
{{"make": "...", "model": "...", "year_min": ..., "year_max": ..., "max_price_eur": ..., "max_km": ..., "fuel": "...", "color": "...", "features": [...], "notes": "...", "confidence": 0.0-1.0}}"""
```

### Telegram Inline Keyboard for Request Confirmation

```python
def send_request_confirmation(request_id, dealer_name, params):
    """Send vehicle request to Telegram with inline buttons."""
    make = params.get('make', '?')
    model = params.get('model', '')
    year = params.get('year_min', '?')
    budget = params.get('max_price_eur', '?')
    km = params.get('max_km', '?')
    fuel = params.get('fuel', 'qualsiasi')

    text = (
        f"RICHIESTA VEICOLO\n"
        f"Da: {dealer_name}\n\n"
        f"{make} {model} | {year}+\n"
        f"Budget: {budget} | Max KM: {km}\n"
        f"Fuel: {fuel}\n\n"
        f"Confidence: {params.get('confidence', '?')}"
    )

    markup = json.dumps({
        "inline_keyboard": [[
            {"text": "CONFERMA", "callback_data": f"vreq_ok_{request_id}"},
            {"text": "MODIFICA", "callback_data": f"vreq_edit_{request_id}"},
            {"text": "IGNORA", "callback_data": f"vreq_no_{request_id}"},
        ]]
    })

    tg_post('sendMessage', {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown',
        'reply_markup': markup,
    })
```

### In-Memory Dedup for wa-daemon.js

```javascript
// Add near top of wa-daemon.js, after MESSAGE_BUFFER
const SEEN_MSGS = new Map();  // wa_msg_id -> timestamp
const SEEN_TTL = 5 * 60 * 1000;  // 5 min

function isDuplicate(msgId) {
    if (!msgId) return false;
    if (SEEN_MSGS.has(msgId)) return true;
    SEEN_MSGS.set(msgId, Date.now());
    // Cleanup old entries periodically
    if (SEEN_MSGS.size > 1000) {
        const cutoff = Date.now() - SEEN_TTL;
        for (const [k, v] of SEEN_MSGS) {
            if (v < cutoff) SEEN_MSGS.delete(k);
        }
    }
    return false;
}

// In message_create handler, add early:
if (isDuplicate(msg.id?.id)) {
    log('INFO', `Dedup: skipping duplicate ${msg.id?.id}`);
    return;
}
```

---

## Open Questions

1. **Portal search speed**: How long does a multi-portal search take? If >5 minutes, need async notification to dealer ("sto cercando, ti aggiorno tra poco"). Check with existing scraper timings.

2. **Callback query handling**: The telegram-handler.py currently uses text commands (`/approva`), not inline button callbacks. Adding callback_query support requires extending the polling handler to process `callback_query` updates from Telegram API.

3. **Concurrent requests**: What if the same dealer sends two vehicle requests within minutes? Need request dedup or merge logic.

4. **Result formatting**: How to present search results in WA (5-line limit)? Mini-dossier format needs design.

---

## Sources

### Primary (HIGH confidence)
- **Codebase analysis**: wa-daemon.js (950+ lines), response-analyzer.py (600+ lines), telegram-handler.py, dealer_crm.py -- all read and verified
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing) -- Haiku 4.5: $1/$5 per MTok
- [OpenRouter Claude Haiku 4.5](https://openrouter.ai/anthropic/claude-haiku-4.5) -- $1/$5 per MTok confirmed

### Secondary (MEDIUM confidence)
- [whatsapp-web.js GitHub Issues](https://github.com/pedroslopez/whatsapp-web.js/issues/1898) -- duplicate message patterns
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) -- verified FastAPI is already used
- [Telegram Bot API](https://core.telegram.org/bots/api) -- inline keyboard callback_query support
- [n8n HITL Telegram patterns](https://n8n.io/workflows/9039-create-secure-human-in-the-loop-approval-flows-with-postgres-and-telegram/) -- approval flow architecture

### Tertiary (LOW confidence -- needs validation)
- whatsapp-web.js reconnection reliability claims -- based on community reports, not official benchmarks

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed, everything already in codebase
- Architecture: HIGH -- extending existing patterns, not introducing new ones
- Intent parsing: HIGH -- LLM extraction is well-documented, Haiku pricing verified
- Pitfalls: HIGH -- based on real issues found in codebase (dedup gap, no request parsing)
- Cost analysis: HIGH -- verified against OpenRouter pricing page

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable stack, no fast-moving dependencies)
