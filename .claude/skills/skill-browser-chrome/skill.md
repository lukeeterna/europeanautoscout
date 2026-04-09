# ARGOS Browser Chrome Skill
## Automazione Chrome con profilo utente loggato via Playwright MCP

---

## STATO INFRASTRUTTURA (2026-03-22)

```
Playwright MCP:  NON installato (mcpServers vuoto in ~/.claude.json)
.playwright-mcp: directory ESISTENTE nel progetto — log browser extension
Metodo corrente: WebFetch/WebSearch (no sessioni autenticate)
```

---

## OPZIONE A — PLAYWRIGHT MCP (Microsoft) — RACCOMANDATO

**Cosa fa**: Apre Chrome controllato da Claude. Naviga, clicca, compila form, screenshot.
**Profilo**: Persistente ma SEPARATO dal profilo Chrome dell'utente.
**Autenticazione**: Login manuale una volta → sessione persiste nel profilo MCP.

### Installazione (terminale, una volta sola)

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

Verifica installazione:
```bash
claude mcp list
# Deve mostrare: playwright
```

### Configurazione con profilo persistente (Chrome reale)

Per usare il tuo Chrome gia' loggato su tutti i siti:

```bash
# Installa con user-data-dir che punta al tuo profilo Chrome
claude mcp add playwright npx @playwright/mcp@latest \
  --  --browser chrome \
  --user-data-dir "$HOME/Library/Application Support/Google/Chrome" \
  --channel chrome
```

ATTENZIONE: Chrome deve essere CHIUSO prima di lanciare Claude con questa config.
Se Chrome e' aperto, il profilo e' locked e Playwright fallisce con errore.

### Configurazione manuale in ~/.claude.json

Se il comando `mcp add` non accetta gli argomenti, edita direttamente:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser", "chrome",
        "--user-data-dir", "/Users/macbook/Library/Application Support/Google/Chrome/Default",
        "--channel", "chrome"
      ]
    }
  }
}
```

### Configurazione SICURA — profilo dedicato ARGOS (non tocca il tuo Chrome)

Crea un profilo Chrome separato solo per ARGOS. Evita conflitti con Chrome aperto.

```bash
# Crea directory profilo ARGOS
mkdir -p ~/.argos-chrome-profile

# Configura MCP
claude mcp add playwright npx @playwright/mcp@latest \
  --  --browser chrome \
  --user-data-dir "$HOME/.argos-chrome-profile"
```

Prima sessione: login manuale ai siti (Google Business, AutoScout24, Facebook, etc.)
Sessioni successive: gia' loggato.

### Uso in conversazione

Dopo installazione, chiedi esplicitamente:

```
"Usa playwright mcp per aprire Google Maps e cerca [nome dealer]"
"Usa playwright per andare su autoscout24.it/concessionari e fare screenshot"
"Apri facebook.com con playwright e cerca la pagina di [dealer]"
```

### Tool disponibili (25 totali)

```
browser_navigate          — naviga a URL
browser_navigate_back     — torna indietro
browser_click             — clicca elemento
browser_type              — digita testo
browser_take_screenshot   — screenshot (PNG base64)
browser_snapshot          — accessibility tree (strutturato, no visione)
browser_scroll            — scrolla pagina
browser_hover             — hover su elemento
browser_drag              — drag-and-drop
browser_wait              — aspetta condizione
browser_pdf_save          — salva pagina come PDF
browser_tab_new           — nuova tab
browser_tab_select        — seleziona tab
browser_tab_close         — chiudi tab
browser_network_requests  — intercetta richieste di rete
browser_console_messages  — leggi console JS
```

---

## OPZIONE B — PLAYWRIGHT MCP BROWSER EXTENSION — PROFILO ESISTENTE

**Cosa fa**: Si collega alle tab Chrome GIA' APERTE. Zero logout, usa sessione attiva.
**Vantaggio**: Nessun conflitto con Chrome aperto. Usa cookie/sessioni reali.
**Limite**: Richiede estensione installata manualmente in Chrome.

### Setup

1. Scarica l'estensione dal repo Microsoft:
   ```
   https://github.com/microsoft/playwright-mcp/blob/main/extension/README.md
   ```

2. Installa in Chrome:
   - Apri `chrome://extensions`
   - Abilita "Modalita' sviluppatore"
   - Clicca "Carica estensione non pacchettizzata"
   - Seleziona la cartella dell'estensione
   - L'estensione "Playwright MCP Bridge" appare in lista

3. Configura MCP con flag `--extension`:
   ```bash
   claude mcp add playwright npx @playwright/mcp@latest -- --extension
   ```

   Oppure in ~/.claude.json:
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

4. Uso:
   - Apri Chrome con la pagina gia' loggata
   - Chiedi a Claude di usare playwright
   - Seleziona la tab da controllare quando richiesto

---

## OPZIONE C — BROWSER MCP (BrowserMCP.io) — STEALTH MODE

**Cosa fa**: Controlla il tuo Chrome reale (non una nuova istanza).
**Vantaggio**: Usa fingerprint reale, evita anti-bot. Gia' loggato su tutto.
**Architettura**: Estensione Chrome + server MCP locale.

### Setup

```bash
npm install -g @browsermcp/mcp
```

Aggiungi a ~/.claude.json:
```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["@browsermcp/mcp@latest"]
    }
  }
}
```

Installa estensione Chrome da: https://docs.browsermcp.io

### Differenza chiave vs Playwright MCP

| Aspetto | Playwright MCP | Browser MCP |
|---------|---------------|-------------|
| Browser | Nuova istanza | Chrome esistente |
| Profilo | Separato/persistente | Il tuo profilo reale |
| Anti-bot | Rilevabile | Stealth (fingerprint reale) |
| Setup | Piu' semplice | Richiede estensione |
| Costo | Gratis | Gratis |

---

## WORKFLOW DEALER RESEARCH CON BROWSER

### Task 1: Google Business / Maps

```
"Usa playwright mcp per:
1. Navigare a maps.google.it
2. Cercare '[nome dealer] [citta]'
3. Fare screenshot della scheda Google Business
4. Estrarre: stelle, n. recensioni, orari, telefono, sito web"
```

### Task 2: AutoScout24 Dealer Profile

```
"Usa playwright mcp per:
1. Andare su autoscout24.it
2. Cercare il concessionario '[nome]'
3. Aprire la pagina dealer
4. Estrarre: n. annunci, modelli pubblicati, prezzi, anni attivita'"
```

### Task 3: Facebook Business Page

```
"Usa playwright mcp per:
1. Aprire facebook.com/[nome-pagina]
2. Screenshot della pagina profilo
3. Estrarre: follower, ultimo post, tipo contenuti"
```

### Task 4: Screenshot per memory/dossier

```
"Usa playwright mcp per fare screenshot di [URL]
e salvarlo in assets/dealers/[nome_dealer]_google.png"
```

---

## LIMITI E WORKAROUND

### Chrome lockato (gia' aperto)
- **Problema**: Profilo Chrome locked se Chrome e' aperto
- **Fix**: Usa profilo ARGOS dedicato (~/.argos-chrome-profile) OPPURE Opzione B (extension)

### Siti anti-bot (AutoScout24, Mobile.de)
- **Problema**: Playwright rilevabile da WAF
- **Fix**: Usa Browser MCP (Opzione C) con fingerprint reale
- **Alternativa**: I nostri scraper esistenti in tools/scrapers/ sono gia' ottimizzati per questo

### Login richiesto (Facebook, Google Business)
- **Fix Playwright**: Usa profilo persistente (~/.argos-chrome-profile) con login manuale iniziale
- **Fix Extension**: Sei gia' loggato nel tuo Chrome

---

## INTEGRAZIONE CON PIPELINE ARGOS

```
Browser MCP/Playwright MCP
         |
         v
Screenshot dealer (Google, AS24, FB)
         |
         v
Estrazione dati strutturati
         |
         v
Scheda Dealer ARGOS (formato standard)
         |
         v
tools/dealer_crm.py (insert dealer)
         |
         v
CoVe score (src/cove/cove_engine_v4.py)
```

---

## INSTALLAZIONE RAPIDA (comando unico)

```bash
# Opzione A — profilo dedicato ARGOS (raccomandato, nessun conflitto)
mkdir -p ~/.argos-chrome-profile && \
claude mcp add playwright npx @playwright/mcp@latest

# Poi modifica ~/.claude.json per aggiungere --user-data-dir ~/.argos-chrome-profile
```

Verifica:
```bash
claude mcp list
# Output atteso: playwright   npx @playwright/mcp@latest
```
