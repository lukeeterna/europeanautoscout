# LinkedIn Automation Research 2026 — ARGOS

## Verdetto: Profilo manuale, zero automazione

### 5 Layer Anti-Bot LinkedIn (tutti simultanei)
1. **TLS Fingerprinting (JA3)** — Playwright ha firma diversa da Chrome reale
2. **CDP Leak Detection** — Chrome DevTools Protocol visibile da JS
3. **Behavioral AI ("360Brew")** — analisi real-time timing/scroll/click
4. **DOM Injection Detection** — estensioni browser rilevate in ore
5. **IP Reputation** — datacenter bloccati, residenziali 31% ban risk

### Tool Analizzati
| Tool | Bypassa | Non bypassa | Verdetto |
|------|---------|-------------|----------|
| Patchright | CDP, webdriver flag | TLS, behavioral, IP | Insufficiente per LinkedIn |
| Camoufox | Canvas, WebGL, screen | TLS (Firefox), behavioral, IP | Non production-ready |
| playwright-stealth | Test base | LinkedIn — zero successi documentati | Non fare |
| browser-use | Timing variabile | TLS, CDP, IP | Riduce rischio ma non elimina |
| AgentQL | Parsing elements | Nessun layer anti-detection | Non pertinente |

### Stack Massima Stealth (se vuoi rischiare)
- Patchright + mobile proxy 4G (€200-500/mese) + behavioral jitter
- Ban risk residuo: 15-25% entro 90 giorni per profilo nuovo
- Viola guardrail ZERO COSTI

### Decisione ARGOS
- **Profilo**: creazione MANUALE (45 min, zero rischio)
- **Outreach dealer**: WhatsApp (non LinkedIn — dealer Sud Italia non usano LI)
- **Intel dealer**: Google Maps, AutoScout24, Facebook (non LinkedIn)
- Dati per creazione manuale: `tools/platform_setup_playbook.md` sezione 3

Fonte: deep research multi-source marzo 2026 (Growleads, Dux-Soup, Patchright GitHub, ZenRows, Bright Data, PROXIES.SX)
