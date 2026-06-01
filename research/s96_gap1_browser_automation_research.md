# S96 GAP1: Enterprise Browser Automation for Business Profile Management

**Researched:** 2026-04-01
**Domain:** Browser automation, CDP, Google Business Profile, Facebook Pages
**Confidence:** HIGH (multi-source verified)

---

## Summary

This research investigates the best approach for ARGOS to automate business profile management (Google Business Profile, Facebook Pages) from a backend Python system. The key finding is that **neither Google nor Facebook offer public APIs for creating profiles/pages** -- both require manual creation first. Automation value is in **managing existing profiles** (posting, updating, responding to reviews) after manual setup.

For browser automation itself, the ecosystem has shifted significantly in 2025-2026. **browser-use** has moved from Playwright to raw CDP and is production-ready (81K+ GitHub stars). **Playwright MCP** with the Chrome extension bridge is the most practical approach for ARGOS's immediate needs because Claude can directly control an existing logged-in Chrome session.

**Primary recommendation:** Use Playwright MCP with extension mode for interactive tasks (already documented in skill-browser-chrome). For automated backend tasks, use Playwright `connect_over_cdp()` with a dedicated ARGOS Chrome profile. Do NOT invest in browser-use until there is a clear automated/scheduled use case that justifies the LLM cost per action.

---

## 1. Google Business Profile API -- Current State (2026)

### Verdict: NO PUBLIC API for creation. Manual creation required.

| Aspect | Status |
|--------|--------|
| API Type | **Private** -- requires approval |
| Prerequisites | Active, verified GBP for **60+ days minimum** |
| Approval timeline | Undefined ("follow-up email after review") |
| Can create profile via API? | **NO** -- API manages existing profiles only |
| Small business eligible? | Yes, but 60-day wait is mandatory |
| Quota when approved | 300 QPM |

**Source:** [Google GBP API Prerequisites](https://developers.google.com/my-business/content/prereqs) (verified April 2026)

### What the API CAN do (after approval):
- Update business information (hours, description, photos)
- Manage and respond to reviews
- Post updates/offers
- Read insights/analytics
- Manage admins and invitations

### What it CANNOT do:
- Create a new Google Business Profile
- Claim an unclaimed business
- Bypass the 60-day verification wait

### ARGOS Implication
ARGOS (as Luca Ferretti) must create the GBP manually via the Google Business web interface. The founder was already instructed to do this (see `tools/google_business_checklist.md`). API access can be requested AFTER the profile is 60 days old (earliest: ~June 2026 if created now).

**Confidence:** HIGH -- verified against official Google developer docs.

---

## 2. Facebook Pages API -- Current State (2026)

### Verdict: NO API for page creation. Management only.

| Aspect | Status |
|--------|--------|
| Page creation via API? | **NO** -- must create manually |
| Page management via API? | Yes, after App Review |
| Required permissions | pages_manage_posts, pages_manage_engagement, pages_read_engagement |
| App Review required? | Yes, for any permission beyond public_profile |
| Python SDK | facebook-python-business-sdk (official Meta SDK) |

**Source:** [Facebook Pages API Permissions](https://developers.facebook.com/docs/pages/overview/permissions-features/) (verified April 2026)

### What the API CAN do:
- Publish posts, photos, videos to an existing page
- Manage comments and messaging
- Read insights/analytics
- Schedule posts

### What it CANNOT do:
- Create a new Facebook Page
- Claim or transfer page ownership

### ARGOS Implication
Same as GBP: manual creation required first. The API becomes useful later for automated posting (e.g., new vehicle listings, case studies). Meta's App Review adds another gate -- plan 2-4 weeks for approval.

**Confidence:** HIGH -- verified against official Meta developer docs.

---

## 3. Browser Automation Approaches -- Comparative Analysis

### 3.1 Playwright MCP (Extension Mode) -- RECOMMENDED for ARGOS

**What:** Microsoft's MCP server connects Claude to your existing Chrome browser tabs via a Chrome extension bridge.

| Property | Value |
|----------|-------|
| Detection risk | **LOW** -- uses real Chrome with real fingerprint |
| Session persistence | **YES** -- uses your actual logged-in browser |
| Python compatible | N/A (runs via Claude MCP, not Python directly) |
| Setup complexity | LOW -- install extension + MCP config |
| Maintenance | LOW -- Microsoft maintains it |
| Cost | FREE |
| Chrome Web Store | [Playwright MCP Bridge](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm) |

**Best for:** Interactive tasks where Claude assists the founder -- creating GBP, setting up Facebook page, posting content. The founder sees what is happening in their Chrome.

**Configuration:**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--extension"]
    }
  }
}
```

**Security:** Extension generates a unique token per browser profile. Include `PLAYWRIGHT_MCP_EXTENSION_TOKEN` in config for authenticated connection.

### 3.2 Playwright `connect_over_cdp()` -- RECOMMENDED for backend automation

**What:** Python Playwright library connects to an existing Chrome instance via Chrome DevTools Protocol websocket.

| Property | Value |
|----------|-------|
| Detection risk | LOW-MEDIUM -- connects to real Chrome, but CDP connection is detectable |
| Session persistence | YES -- uses dedicated Chrome profile with saved cookies |
| Python compatible | **YES** -- `playwright` 1.58.0 already installed |
| Setup complexity | MEDIUM -- must start Chrome with --remote-debugging-port |
| Maintenance | LOW -- stable API |
| Cost | FREE |

**Pattern:**
```python
from playwright.async_api import async_playwright

async def connect_to_chrome():
    async with async_playwright() as p:
        # Chrome must be started with:
        # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        #   --remote-debugging-port=9222 \
        #   --user-data-dir=$HOME/.argos-chrome-profile
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]  # Reuse existing context with cookies
        page = context.pages[0]  # Or context.new_page()
        # Now interact with logged-in session
```

**Critical limitation:** Cannot use the default Chrome user data directory if Chrome is already running. Must use a separate `--user-data-dir` for automation.

**Best for:** Scheduled tasks -- posting to GBP, updating Facebook page, taking screenshots of dealer profiles.

### 3.3 browser-use (AI Browser Agent)

**What:** Open-source Python library (81K+ GitHub stars) that gives an LLM full browser control. Moved from Playwright to raw CDP in August 2025.

| Property | Value |
|----------|-------|
| Detection risk | LOW -- uses raw CDP, no WebDriver flag |
| Session persistence | YES -- supports user_data_dir + storage_state |
| Python compatible | YES -- Python 3.11+, pip install browser-use |
| Setup complexity | MEDIUM -- needs LLM API key |
| Maintenance | MEDIUM -- fast-moving project, breaking changes possible |
| Cost | **LLM cost per action** (2-5 seconds per action, token cost varies) |
| Performance | 89% on WebVoyager benchmark |

**Architecture (post CDP migration):**
```
browser-use
    |-- Direct CDP connection (no Playwright/Puppeteer)
    |-- LLM decides next action (click, type, navigate)
    |-- Human-like interaction patterns
    |-- Real Chrome profile reuse via user_data_dir
```

**Why they left Playwright:** Playwright abstracts away CDP details that AI agents need (iframe handling, precise timing, network interception). Raw CDP gives 3-5x faster element extraction and screenshot capture.

**Cost concern for ARGOS:** Every browser action requires an LLM call. For a simple "post to GBP" task that takes 8-12 actions, that is 8-12 LLM API calls. With Claude/GPT-4, this could cost $0.10-0.50 per task. ARGOS has a ZERO COST constraint -- browser-use only makes sense with free local models (Ollama), but those are less reliable for complex form-filling.

**Verdict:** Impressive technology but **overkill for ARGOS's current needs**. Revisit when there are 50+ automated tasks/day that justify the complexity.

### 3.4 Pydoll (Direct CDP, Python-native)

**What:** Modern Python library for Chrome automation via CDP. No WebDriver, no Playwright dependency.

| Property | Value |
|----------|-------|
| Detection risk | **VERY LOW** -- no WebDriver flag, no automation markers |
| Session persistence | YES -- connects to existing Chrome via CDP |
| Python compatible | YES -- async Python, Pydantic models |
| Setup complexity | LOW -- pip install pydoll |
| Maintenance | MEDIUM -- newer project, smaller community |
| Cost | FREE |

**Best for:** Stealth scraping, bot-resistant sites. Good Playwright alternative when detection is the primary concern.

**ARGOS relevance:** Could replace Playwright for scraper work on protected portals. Not needed for GBP/Facebook (those detect based on account behavior, not browser fingerprint).

### 3.5 Selenium (Legacy)

**Verdict: Skip.** Slower, more detectable, no advantages over Playwright or CDP-direct for any ARGOS use case.

### 3.6 BrowserMCP.io (Stealth MCP)

**What:** MCP server that controls your actual running Chrome instance (not a new one).

| Property | Value |
|----------|-------|
| Detection risk | **LOWEST** -- your actual Chrome with real fingerprint |
| Session persistence | YES -- your real profile |
| Setup | Requires Chrome extension + npm package |
| Cost | FREE |

**vs Playwright MCP Extension mode:** Similar concept but BrowserMCP provides more stealth features. Playwright MCP Extension is better supported (Microsoft-backed).

---

## 4. Production CDP Patterns

### 4.1 Session Management

```
Browser Session (WebSocket)
    |-- Target.attachToTarget() → sessionId
    |-- Child sessions close when parent closes
    |-- Multiple clients can connect to same target (but creates concurrency issues)
```

### 4.2 Best Practices for ARGOS

| Practice | Details |
|----------|---------|
| **Dedicated Chrome profile** | `~/.argos-chrome-profile` -- never use the main Chrome profile |
| **One session at a time** | Don't connect multiple automation scripts to same Chrome |
| **Stable CDP only** | Avoid experimental CDP domains -- they break across Chrome versions |
| **Error recovery** | If CDP WebSocket disconnects, restart Chrome and reconnect |
| **Tab isolation** | One task = one tab. Close tabs after use. |
| **Version matching** | CDP methods change per Chrome version -- pin Chrome version or use stable subset |

### 4.3 Connection Pooling (NOT recommended for ARGOS)

Connection pooling is for high-throughput systems (100+ concurrent browsers). ARGOS has 1 user, 1 Chrome, sequential tasks. Keep it simple: one Chrome instance, one connection.

---

## 5. Recommended Architecture for ARGOS

### Phase 1: NOW (manual setup assisted by Claude)

```
Founder's Chrome (logged in to Google/Facebook)
    |
    v
Playwright MCP Extension Mode
    |
    v
Claude assists with:
  - Creating GBP (manual, Claude guides through steps)
  - Creating Facebook Page (manual, Claude guides)
  - Initial profile setup (photos, description, hours)
```

**This is what skill-browser-chrome already documents. Use it.**

### Phase 2: AFTER profiles exist (automated management)

```
Dedicated ARGOS Chrome (--remote-debugging-port=9222)
    |
    v
Playwright connect_over_cdp() from Python
    |
    v
Scheduled tasks:
  - Post new vehicle listings to GBP
  - Post to Facebook Page
  - Screenshot dealer profiles for intel
  - Monitor reviews
```

**Implementation pattern:**
```python
# tools/profile_manager.py
import asyncio
from playwright.async_api import async_playwright

ARGOS_CDP_URL = "http://localhost:9222"

async def post_to_gbp(business_name: str, post_text: str, image_path: str = None):
    """Post an update to Google Business Profile."""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ARGOS_CDP_URL)
        context = browser.contexts[0]
        page = await context.new_page()

        await page.goto("https://business.google.com")
        # Navigate to posts section
        # Fill in post content
        # Upload image if provided
        # Submit

        await page.close()

async def post_to_facebook(page_id: str, post_text: str, image_path: str = None):
    """Post to Facebook Business Page."""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ARGOS_CDP_URL)
        context = browser.contexts[0]
        page = await context.new_page()

        await page.goto(f"https://www.facebook.com/{page_id}")
        # Create post flow

        await page.close()
```

### Phase 3: FUTURE (if scale demands it)

```
browser-use with local LLM (Ollama)
    |
    v
Autonomous agent handles:
  - Complex multi-step workflows
  - Form filling with judgment
  - Error recovery without human intervention
```

**Only when:** 50+ automated tasks/day AND local LLM is reliable enough.

---

## 6. Common Pitfalls

### Pitfall 1: Trying to automate GBP/Facebook creation
**What goes wrong:** Both platforms detect automation during account/page creation and block or ban the account.
**Why it happens:** Creation flows have the strongest anti-bot measures. Management flows are more lenient.
**How to avoid:** Create profiles manually. Automate management AFTER creation.
**Warning signs:** CAPTCHA loops, account suspension, "unusual activity" warnings.

### Pitfall 2: Using the main Chrome profile for automation
**What goes wrong:** Chrome profile is locked when Chrome is open. Playwright fails with "profile in use" error.
**Why it happens:** Chrome's profile lock prevents concurrent access.
**How to avoid:** Always use a dedicated `~/.argos-chrome-profile` directory.
**Warning signs:** "Failed to create new context" errors.

### Pitfall 3: Forgetting to start Chrome with debugging port
**What goes wrong:** `connect_over_cdp()` fails with connection refused.
**Why it happens:** Chrome must be explicitly started with `--remote-debugging-port=9222`.
**How to avoid:** Create a shell alias or PM2 process for the ARGOS Chrome instance.

### Pitfall 4: Over-engineering with browser-use too early
**What goes wrong:** Spending days setting up LLM-driven browser automation for tasks that take 2 minutes manually.
**Why it happens:** browser-use is exciting technology. But each action costs LLM tokens and takes 2-5 seconds.
**How to avoid:** Start with Playwright MCP (Claude-assisted) and Playwright CDP (scripted). Graduate to browser-use only when task volume justifies it.

### Pitfall 5: Assuming CDP is stable across Chrome versions
**What goes wrong:** Automation scripts break after Chrome auto-update.
**Why it happens:** Experimental CDP domains change without notice.
**How to avoid:** Use only stable CDP commands. Pin Chrome version if possible. Use Playwright as CDP abstraction layer (it handles version differences).

---

## 7. Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CDP connection management | Custom WebSocket client | Playwright `connect_over_cdp()` | Handles reconnection, version diffs, session management |
| Browser fingerprint evasion | Custom header spoofing | Real Chrome profile (--user-data-dir) | Real fingerprint > fake fingerprint always |
| Form automation with judgment | Regex-based form detection | browser-use (when needed) | AI handles dynamic forms, CAPTCHAs, layout changes |
| Screenshot comparison | Pixel-diff library | Playwright screenshot + visual review | Playwright handles DPI, viewport, timing |
| GBP/Facebook posting API | Custom HTTP API client | Playwright page automation | No public creation API exists |

---

## 8. Decision Matrix: Which Tool When

| Task | Tool | Reason |
|------|------|--------|
| Create GBP (one-time) | **Founder manually** | Anti-bot detection too strong |
| Create Facebook Page (one-time) | **Founder manually** | Same |
| Claude helps founder set up profiles | **Playwright MCP Extension** | Claude sees/controls real Chrome |
| Automated daily GBP post | **Playwright connect_over_cdp()** | Scripted, no LLM cost |
| Automated Facebook post | **Playwright connect_over_cdp()** | Same |
| Scraping bot-protected portals | **Pydoll or existing scrapers** | Stealth is priority |
| Complex multi-site workflows | **browser-use** (future) | AI handles unpredictable flows |

---

## 9. Environment Notes

| Dependency | Status | Notes |
|------------|--------|-------|
| Playwright (Python) | Installed | v1.58.0, `/usr/local/lib/python3.13/site-packages` |
| browser-use | NOT installed | `pip install browser-use` if needed |
| Pydoll | NOT installed | `pip install pydoll` if needed |
| Chrome | Assumed available | MacBook + iMac both have Chrome |
| Node.js | v22 | For Playwright MCP npx commands |
| Python | 3.13 | Compatible with all tools (browser-use needs 3.11+) |

---

## 10. ARGOS-Specific Constraints (from CLAUDE.md)

1. **ZERO COST** -- No paid APIs. browser-use with paid LLMs violates this. Use Playwright (free) or browser-use with Ollama (free but less reliable).
2. **Enterprise grade** -- No shortcuts on reliability. Playwright connect_over_cdp is battle-tested.
3. **Use existing assets** -- Playwright 1.58.0 is already installed. skill-browser-chrome already documents MCP setup. Don't reinvent.
4. **End-to-end value chain** -- Browser automation must connect to the dealer pipeline: scrape -> CoVe -> dossier -> post to GBP/Facebook.

---

## Sources

### Primary (HIGH confidence)
- [Google GBP API Prerequisites](https://developers.google.com/my-business/content/prereqs) -- verified API is private, 60-day wait required
- [Google GBP API FAQ](https://developers.google.com/my-business/content/faq) -- confirmed no public creation endpoint
- [Facebook Pages API Permissions](https://developers.facebook.com/docs/pages/overview/permissions-features/) -- confirmed no page creation via API
- [Playwright Python BrowserType docs](https://playwright.dev/python/docs/api/class-browsertype) -- connect_over_cdp() API reference
- [Playwright MCP Extension README](https://github.com/microsoft/playwright-mcp/blob/main/extension/README.md) -- extension mode setup

### Secondary (MEDIUM confidence)
- [browser-use CDP migration blog](https://browser-use.com/posts/playwright-to-cdp) -- architectural rationale verified by multiple sources
- [browser-use GitHub](https://github.com/browser-use/browser-use) -- 81K+ stars, active development
- [Pydoll GitHub](https://github.com/autoscrape-labs/pydoll) -- CDP-native Python alternative
- [Playwright MCP Bridge Chrome Web Store](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm)

### Tertiary (LOW confidence)
- browser-use Cloud API pricing -- not verified, referenced only for awareness
- Pydoll production maturity -- newer project, limited production case studies
