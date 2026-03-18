# PROMPT: Build ARGOS Command Center — Enterprise Grade

## MISSIONE

Implementa e deploya l'ARGOS Command Center, la dashboard enterprise per il sistema ARGOS Automotive CoVe 2026. Il boilerplate esiste gia' in `wa-intelligence/dashboard/`. Il tuo compito e' renderlo FUNZIONANTE, BELLO, DEPLOYATO.

---

## CONTESTO SISTEMA

ARGOS e' un sistema B2B di vehicle scouting EU→IT per concessionari italiani del Sud Italia.

**Infra esistente (iMac 2012, 8GB RAM):**
- SQLite WAL: `~/Documents/app-antigravity-auto/dealer_network.sqlite`
- DuckDB: `dealer_network.duckdb` (CoVe engine, READ-ONLY, NON TOCCARE)
- PM2: `argos-tg-bot` (Python), `argos-wa-daemon` (Node.js)
- SSH: `ssh gianlucadistasi@192.168.1.2`
- Cloudflare Pages: `argos-automotive.pages.dev` (landing, gia' live)
- OpenRouter: Haiku 4.5 per generazione risposte
- Brand: nero #0D0D0D + oro #B8960C

**Tabelle SQLite (dealer_network.sqlite):**
```
conversations    — dealer_id, dealer_name, city, phone_number, stock_size, persona_type, score, source, notes, current_step, day1_message, recommendation, created_at, last_contact_at, analyzed_at
messages         — id, dealer_id, dealer_name, phone_number, direction (INBOUND/OUTBOUND), body, timestamp_it, timestamp_iso, wa_msg_id, processed, created_at
pending_replies  — id, dealer_id, dealer_name, inbound_msg_id, reply_text, reply_label, cialdini_trigger, approved, sent, scheduled_at, created_at
scheduled_actions — id, dealer_id, dealer_name, action_type, due_at, status, fired_at, created_at
audit_log        — id, event_type, dealer_id, payload, timestamp_it, created_at
llm_costs        — (tabella costi LLM con cost_usd, tokens, model, created_at)
```

---

## STACK TECNOLOGICO (GIA' DECISO)

| Layer | Tecnologia | Note |
|-------|-----------|------|
| Backend | FastAPI + Uvicorn | Async, lightweight |
| Templating | Jinja2 | Server-side rendering |
| Interattivita' | HTMX 2.0 (CDN 14KB) | Partial page updates, zero JS custom |
| Reattivita' client | Alpine.js 3.x (CDN 15KB) | Filtri, toggle, dropdown |
| UI Framework | Tabler 1.0 (Bootstrap 5, CDN) | Dark theme nativo |
| Charts | ECharts 5.x (CDN) | Dark theme built-in |
| CSS Custom | `argos-theme.css` | Override Tabler: nero + oro |
| Auth | itsdangerous + cookie firmato | Session 7gg, single user |
| HTTPS | Cloudflare Tunnel | Zero port-forward |
| Process mgmt | PM2 | Quarto processo: argos-dashboard |

**Dipendenze Python:** `fastapi uvicorn jinja2 python-multipart itsdangerous`

---

## BOILERPLATE GIA' CREATO

Tutti questi file esistono gia' in `wa-intelligence/dashboard/`:

```
dashboard/
  __init__.py            # Package init
  app.py                 # FastAPI app — 6 route + 2 HTMX partials + 2 JSON API
  auth.py                # Cookie session firmato, timing-safe
  db.py                  # 12 query read-only su SQLite WAL
  static/css/
    argos-theme.css      # Theme completo nero+oro, glassmorphism, badge archetipi
  templates/
    base.html            # Layout Tabler dark + sidebar collapsabile + HTMX/Alpine/ECharts CDN
    login.html           # Login page glassmorphism
    dashboard.html       # Overview: KPI auto-refresh + funnel ECharts + donut archetipi + feed messaggi
    pipeline.html        # Tabella dealer con filtro archetipo Alpine.js
    conversations.html   # Split view dealer list + chat area
    conversation_detail.html  # Chat timeline per dealer
    finance.html         # Costi LLM + pipeline revenue + ROI projection
    system.html          # PM2 status + DB stats + sessioni
    partials/
      _kpi_cards.html    # KPI partial (HTMX refresh 30s)
      _message_feed.html # Feed messaggi partial (HTMX refresh 30s)
      _dealer_table.html # Tabella dealer partial
```

---

## FASI DI IMPLEMENTAZIONE

### FASE 1 — FOUNDATION (Backend Validation + Fix)

**Obiettivo**: Far partire `uvicorn dashboard.app:app` senza errori.

1. Leggi TUTTI i file in `wa-intelligence/dashboard/` per capire lo stato attuale
2. Installa dipendenze su iMac: `pip3 install fastapi uvicorn jinja2 python-multipart itsdangerous`
3. Fix eventuali import/path issues
4. Verifica che `db.py` si connetta correttamente al DB iMac (`~/Documents/app-antigravity-auto/dealer_network.sqlite`)
5. Testa: `cd ~/Documents/app-antigravity-auto && python3 -m uvicorn wa-intelligence.dashboard.app:app --host 127.0.0.1 --port 8080`
6. Verifica che la pagina login si carichi
7. Verifica auth con password default `argos2026`
8. Verifica che la dashboard mostri dati reali dai 8 dealer Salerno

**Criteri di successo F1:**
- Server parte senza errori
- Login funziona
- Dashboard mostra KPI reali (8 dealer, 0 messaggi)
- Nessun errore 500 navigando tutte le pagine

### FASE 2 — VISUAL POLISH (Enterprise Look)

**Obiettivo**: La dashboard deve sembrare un prodotto SaaS premium da $200/mese.

1. Verifica che il CSS glassmorphism funzioni (backdrop-filter)
2. Verifica chart ECharts: funnel + donut archetipi
3. Aggiungi transizioni CSS smooth sulle card (hover glow oro)
4. Verifica responsiveness mobile (sidebar collapsabile)
5. Verifica che i badge archetipi abbiano i colori giusti
6. Aggiungi favicon ARGOS (usa un emoji placeholder se non disponibile)
7. Verifica scrollbar custom su WebKit

**Design principles:**
- Dark background PURO #0D0D0D (non grigio)
- Oro #B8960C solo per: titoli sezione, KPI values, bordi attivi, CTA
- Testo body: #E0E0E0 | Testo secondario: #888888
- Card border: #2A2A2A | Card hover border: #8B7209 (oro dim)
- Zero decorazioni inutili — clean, minimal, enterprise

### FASE 3 — LIVE DATA + HTMX

**Obiettivo**: Auto-refresh funzionante, dati live dal DB.

1. Verifica HTMX auto-refresh KPI ogni 30s
2. Verifica HTMX auto-refresh message feed ogni 30s
3. Verifica che cliccando un dealer nella pipeline si apra la conversazione
4. Verifica che la chat timeline mostri messaggi in/out con stile WhatsApp
5. Verifica filtro archetipi Alpine.js nella pipeline
6. System page: verifica che PM2 status sia live (subprocess `pm2 jlist`)

### FASE 4 — DEPLOY SU IMAC + PM2

**Obiettivo**: Dashboard accessibile in produzione.

1. Copia i file su iMac via SCP
2. Installa dipendenze Python su iMac
3. Aggiungi a PM2:
   ```bash
   pm2 start "python3 -m uvicorn wa_intelligence.dashboard.app:app --host 0.0.0.0 --port 8080" \
     --name argos-dashboard --cwd ~/Documents/app-antigravity-auto
   pm2 save
   ```
4. Verifica health: `curl http://127.0.0.1:8080/login`
5. (Opzionale) Setup Cloudflare Tunnel per accesso remoto HTTPS

### FASE 5 — AZIONI DASHBOARD (Nice-to-have)

**Obiettivo**: Azioni dirette dalla dashboard (non solo visualizzazione).

1. Bottone "Invia Day 1" per dealer PENDING → POST al wa-daemon HTTP /send
2. Bottone "Approva Risposta" per pending_replies → UPDATE approved=1 + trigger invio
3. Bottone "Skip" per pending_replies → UPDATE approved=0
4. Form "Aggiungi Nota" per dealer → UPDATE conversations.notes

---

## REGOLE IMMUTABILI

- La dashboard e' **READ-ONLY** sul database (tranne per azioni esplicite F5)
- **MAI** toccare `cove_engine_v4.py` o `dealer_network.duckdb`
- **MAI** esporre credenziali, API key, token nel frontend
- **MAI** menzionare CoVe, Claude, AI, Anthropic, embedding nella UI visibile
- Password dashboard nel `.env`, MAI hardcoded in produzione
- Il CSS deve funzionare su Safari macOS 11 (iMac 2012) e Safari iOS (telefono founder)
- Tutto via CDN — ZERO npm install, ZERO build step, ZERO webpack/vite
- Brand: **ARGOS Automotive** | Persona: **Luca Ferretti**

---

## AGENT DELEGATION

Se il task richiede competenze specifiche, delega ai subagent:
- **agent-ops**: per deploy iMac, PM2, SSH, health check
- **agent-cove**: per query DuckDB/CoVe scoring (READ-ONLY)
- **agent-finance**: per calcoli ROI, fee, report P&L
- **agent-marketing**: per contenuti brand, tone of voice

NON delegare il codice dashboard stesso — quello e' core e va fatto direttamente.

---

## COME VERIFICARE IL RISULTATO

Alla fine di ogni fase, esegui:
```bash
# Test locale
curl -s http://127.0.0.1:8080/login | grep "ARGOS" && echo "LOGIN OK"
curl -s -c /tmp/cookies -d "password=argos2026" -L http://127.0.0.1:8080/login
curl -s -b /tmp/cookies http://127.0.0.1:8080/ | grep "kpi-card" && echo "DASHBOARD OK"
curl -s -b /tmp/cookies http://127.0.0.1:8080/pipeline | grep "dealer" && echo "PIPELINE OK"
curl -s -b /tmp/cookies http://127.0.0.1:8080/api/stats && echo "API OK"
```

---

## INIZIO

Parti dalla FASE 1. Leggi il boilerplate, fixa, testa, e procedi fase per fase. Report su Telegram dopo ogni fase completata.
