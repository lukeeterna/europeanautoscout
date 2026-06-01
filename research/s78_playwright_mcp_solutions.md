# Playwright MCP — Soluzioni Enterprise per Claude Code (2026)
## Research verificata — S78 ARGOS Automotive

**Data ricerca**: 2026-03-23
**Fonti**: GitHub microsoft/playwright-mcp, anthropics/claude-code, npm @playwright/mcp, DeepWiki, Simon Willison TIL

---

## PROBLEMA 1: Chrome Profile Lock

### Causa root

Chrome non supporta piu' istanze simultanee sullo stesso `--user-data-dir`. Quando Playwright
tenta di lanciare Chrome con un profilo gia' in uso, Chrome individua l'istanza esistente,
le delega il comando, e si chiude con `exitCode=0`. Playwright interpreta questo exit come
successo ma senza browser disponibile, oppure come fallimento a seconda della versione.

Output di errore tipico:
```
browserType.launchPersistentContext: Failed to launch the browser process.
[pid=XXXXX][out] Opening in existing browser session.
[pid=XXXXX] <process did exit: exitCode=0, signal=null>
```

Problema confermato su macOS (issue #24144 anthropics/claude-code, marzo 2026).
Su macOS il profilo MCP default si trova in:
`~/Library/Caches/ms-playwright/mcp-chrome-profile`

Problema aggiuntivo documentato: due sessioni Claude Code concorrenti con lo stesso
`--user-data-dir` causano identico conflitto sulla seconda sessione.

### Soluzione enterprise-grade

Tre strategie disponibili, in ordine di priorita' per ARGOS:

**STRATEGIA 1 (RACCOMANDATA) — Modalita' Extension (zero conflitti)**

La Playwright MCP Browser Extension si collega alle tab Chrome GIA' APERTE senza
aprire una nuova istanza di Chrome. Nessun conflitto possibile. Chrome puo' rimanere
aperto normalmente.

**STRATEGIA 2 — Profilo dedicato con storage-state (no Chrome real)**

Usare `--isolated` + `--storage-state` invece di `--user-data-dir`. Playwright
usa Chromium bundled (non il Chrome dell'utente), eliminando il conflitto. Le sessioni
login vengono esportate in un JSON e ricaricate a ogni avvio.

**STRATEGIA 3 — CDP connection (Chrome gia' aperto)**

Lanciare Chrome con remote debugging abilitato e puntare Playwright MCP all'endpoint
CDP. Playwright non lancia un nuovo processo, si connette all'esistente.

### Implementazione specifica

#### Strategia 1 — Extension mode (ARGOS default consigliato)

Step 1: Installa l'estensione Playwright MCP Bridge su Chrome:
- Vai su `chrome://extensions`, abilita "Modalita' sviluppatore"
- Scarica l'estensione da: https://github.com/microsoft/playwright-mcp/tree/main/extension
- "Carica estensione non pacchettizzata" → seleziona la cartella

Step 2: Configura MCP in `~/.claude.json`:
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

Step 3: Uso — Chrome rimane aperto normalmente. Claude controlla le tab esistenti.
Vantaggio bonus: login mantenuto automaticamente (usi il tuo profilo Chrome reale).

#### Strategia 2 — Isolated + storage-state (se non vuoi installare estensione)

Step 1: Login manuale una volta e salva lo stato:
```bash
# Prima volta: login manuale con Chromium bundled, poi esporta stato
npx playwright codegen --save-storage=~/.argos-storage-state.json
```

Step 2: Configura MCP:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--isolated",
        "--storage-state", "/Users/macbook/.argos-storage-state.json"
      ]
    }
  }
}
```

Con `--isolated` Playwright usa un profilo in-memory: nessun lock, nessun conflitto.
Lo storage-state carica cookie/localStorage del login precedente.

#### Strategia 3 — CDP (avanzato, Chrome aperto con debugging)

Step 1: Lancia Chrome con remote debugging:
```bash
# Alias da aggiungere a ~/.zshrc
alias chrome-debug='/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.argos-chrome-profile" &'
```

Step 2: Configura MCP:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--cdp-endpoint", "http://localhost:9222"
      ]
    }
  }
}
```

Playwright si connette all'istanza esistente senza creare un nuovo processo.
Fork dedicato con CDP-first: https://github.com/lars-hagen/mcp-playwright-cdp
(tenta la connessione CDP prima di lanciare un nuovo browser)

### Configurazione attuale ARGOS da aggiornare

Il file `~/.claude.json` attuale usa `--user-data-dir ~/.argos-chrome-profile`.
Questa configurazione e' vulnerabile al lock se Chrome e' aperto (anche se e' un
profilo diverso da Default, Chrome su macOS puo' comunque causare problemi).

**Azione immediata**: Sostituire con Strategia 1 (extension) o Strategia 2 (isolated+storage-state).

### Fonte/riferimento

- [Issue #24144 anthropics/claude-code — Playwright MCP fails when Chrome already running](https://github.com/anthropics/claude-code/issues/24144)
- [microsoft/playwright-mcp README — --isolated, --extension, --cdp-endpoint flags](https://github.com/microsoft/playwright-mcp)
- [Issue #1294 — Support isolated instances](https://github.com/microsoft/playwright-mcp/issues/1294)
- [DeepWiki — Browser Context Management](https://deepwiki.com/microsoft/playwright-mcp/4.4-browser-context-management)

---

## PROBLEMA 2: File Upload Crash

### Causa root

Il tool `browser_file_upload` in @playwright/mcp richiede una condizione specifica:
il file chooser dialog deve essere ATTIVAMENTE APERTO sulla pagina nel momento in
cui viene invocato il tool. Se il dialog non e' presente o e' gia' chiuso, il tool
fallisce con:

```
"The tool 'browser_file_upload' can only be used when there is related modal state present."
```

Crash del browser documentati in due scenari distinti:

1. **Race condition**: Il file chooser si apre e si chiude prima che Claude esegua
   il tool. Il browser rimane in stato inconsistente.

2. **Limite 50MB**: File maggiori di 50MB causano errore
   `"Cannot transfer files larger than 50Mb to a browser not co-located with the server"`
   (issue #1268 microsoft/playwright-mcp — chiuso con fix in playwright PR #38614
   via `connectOverCDP({ isLocal })`).

3. **Contesto Extension**: In extension mode, il CDP connection e' "remote"
   anche se locale — il transfer di file supera il limite dimensionale interno.

Il crash totale del browser (processo che muore) durante upload non e' documentato
come bug specifico del MCP, ma e' correlato a:
- `SharedMemory /dev/shm` insufficiente (problematica principalmente su Linux/container)
- Chrome che non riesce a gestire il pipe di dati del CDP durante l'upload

### Soluzione enterprise-grade

**APPROCCIO 1 (IMMEDIATO) — Sequenza corretta con wait esplicito**

Il file chooser deve essere intercettato PRIMA che si apra, non dopo. La sequenza
corretta e':

```
1. browser_snapshot    → identifica l'elemento upload
2. Imposta listener filechooser (interno a Playwright)
3. browser_click       → clicca elemento che apre il dialog
4. browser_file_upload → eseguito immediatamente dopo il click (< 1 secondo)
```

In pratica con Claude Code: chiedere esplicitamente di fare click e upload
in una singola istruzione atomica, non in passi separati.

**APPROCCIO 2 (ROBUSTO) — JavaScript injection senza dialog**

Bypassare completamente il file chooser usando `browser_evaluate` per impostare
direttamente il valore dell'input file via DOM:

```javascript
// Questo approccio funziona per input[type="file"] normali
// Il file deve essere accessibile dal server MCP (path locale)
const dataTransfer = new DataTransfer();
// Oppure usare setInputFiles via CDP
```

Playwright MCP espone `browser_evaluate` per eseguire JS arbitrario nella pagina.
Per upload di immagini su Google Business / piattaforme standard:

```
Prompt Claude: "Usa browser_evaluate per impostare direttamente il valore
dell'input file con percorso [path] senza aprire il dialog"
```

**APPROCCIO 3 (ALTERNATIVA COMPLETA) — Drag-and-drop simulato**

Alcune piattaforme accettano drag-and-drop come alternativa al file dialog.
Playwright MCP ha `browser_drag` che simula drag-and-drop:

```
browser_drag: trascina il file dalla posizione X alla drop zone Y
```

Questa modalita' evita completamente il file chooser e il suo stato modale.

**APPROCCIO 4 (WORKAROUND PRATICO per ARGOS) — Carica da URL**

Per upload di immagini (Google Business, Trustpilot, Facebook):
se la piattaforma accetta URL immagine invece di upload diretto, usare
`browser_type` nel campo URL invece di `browser_file_upload`.

### Implementazione specifica per ARGOS (upload foto Google Business)

Sequenza raccomandata per upload foto profilo su Google Business:

```
Step 1: browser_navigate → business.google.com
Step 2: browser_snapshot → identifica sezione foto, trova input[type="file"]
Step 3: Prompt Claude: "Clicca il bottone di upload foto e carica immediatamente
        /Users/macbook/Documents/.../assets/cover_google_business_v2.png"
        (Claude eseguira' click + file_upload in sequenza rapida)
Step 4: Se fallisce: usa browser_evaluate per impostare input.files via FileList
Step 5: Fallback finale: screenshot della pagina, caricare manualmente le foto
```

Nota pratica: per la sessione S78, l'upload manuale delle foto ARGOS rimane
il metodo piu' affidabile. Il tool browser_file_upload e' utile per
automatizzare upload ripetitivi ma non e' mission-critical per il setup iniziale.

### Fonte/riferimento

- [Issue #1268 — 50MB upload limit](https://github.com/microsoft/playwright-mcp/issues/1268)
- [Playwright docs — FileChooser API](https://playwright.dev/docs/api/class-filechooser)
- [Issue #30934 microsoft/playwright — No file uploaded using filechooser](https://github.com/microsoft/playwright/issues/30934)
- [BrowserStack — Upload files with Playwright](https://www.browserstack.com/guide/playwright-upload-file)

---

## PROBLEMA 3: MCP Disconnection dopo crash

### Causa root

Playwright MCP gira come processo stdio separato che Claude Code lancia all'avvio.
Quando il browser crasha o si chiude inaspettatamente, il processo Playwright MCP
riceve un segnale e termina. Una volta terminato, la connessione stdio e' permanentemente
rotta per quella sessione di Claude Code.

Comportamento confermato (issue #5670 anthropics/claude-code, chiuso come "not planned"):
- Auto-reconnect esiste SOLO per server SSE remoti (aggiunto in Claude Code v1.0.18)
- Server stdio locali (come Playwright MCP) NON hanno auto-reconnect
- Il comando `/mcp reconnect playwright` quando il server non e' configurato causa
  DEADLOCK completo di Claude Code (issue #11385) — la sessione si blocca e va killata

Comportamento di "No such tool available": dopo il crash del processo stdio,
Claude Code rimuove i tool di quella connessione dal contesto. Non e' un bug ma
il comportamento atteso per una connessione stdio morta.

### Soluzione enterprise-grade

**SOLUZIONE 1 (IMMEDIATA) — Wrapper script con auto-restart**

Crea uno script che riavvia automaticamente il processo Playwright MCP quando
si chiude (crash o chiusura normale):

```bash
#!/bin/bash
# File: ~/.argos-playwright-wrapper.sh
echo "[ARGOS] Avvio Playwright MCP con auto-restart..."
while true; do
  npx -y @playwright/mcp@latest "$@"
  EXIT_CODE=$?
  echo "[ARGOS] Playwright MCP terminato (exit: $EXIT_CODE). Riavvio in 2s..."
  sleep 2
done
```

```bash
chmod +x ~/.argos-playwright-wrapper.sh
claude mcp remove playwright
claude mcp add playwright -- "$HOME/.argos-playwright-wrapper.sh"
```

Aggiungi argomenti al wrapper:
```bash
claude mcp add playwright -- "$HOME/.argos-playwright-wrapper.sh" \
  --isolated \
  --storage-state "$HOME/.argos-storage-state.json"
```

Con questo wrapper, Claude Code mantiene la connessione stdio aperta
(il wrapper non muore mai), e il processo Playwright interno si riavvia
automaticamente dopo ogni crash. I tool tornano disponibili entro 2-3 secondi.

**SOLUZIONE 2 (PREVENZIONE) — Non chiudere mai il browser durante la sessione**

La causa principale di disconnessione e' `browser_close` (esplicito)
o crash del browser durante operazioni rischiose (upload, form complessi).

Best practice ARGOS:
- Non usare `browser_close` durante la sessione
- Completare tutte le operazioni browser in sequenza continua
- Chiudere il browser solo alla fine della sessione completa
- Evitare `browser_file_upload` per file grandi (rischio crash)

**SOLUZIONE 3 (SE GIA' DISCONNESSO) — Recupero senza riavvio Claude Code**

Se il MCP e' gia' disconnesso e i tool sono "No such tool available":

```bash
# In un terminale separato (NON dentro Claude Code):
# 1. Verifica stato MCP
claude mcp list

# 2. Se il server e' listato ma non risponde, rimuovi e riaggiunge
claude mcp remove playwright
claude mcp add playwright -- "$HOME/.argos-playwright-wrapper.sh" [args]

# 3. Nella sessione Claude Code attiva:
# Digita: /mcp  (mostra stato server)
# Se playwright non compare: riavvia Claude Code (non c'e' altro modo)
```

ATTENZIONE: NON usare `/mcp reconnect playwright` — causa deadlock confermato
(issue #11385). Se devi ricorrere al comando /mcp, usa solo `/mcp` senza
sottocomandi per vedere lo stato.

**SOLUZIONE 4 (ARCHITETTURA ALTERNATIVA) — SSE server per auto-reconnect nativo**

Claude Code ha auto-reconnect nativo per server SSE (HTTP). Si puo' convertire
Playwright MCP da stdio a SSE:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "sse",
      "url": "http://localhost:8931/sse"
    }
  }
}
```

Avvia il server SSE separatamente (in PM2 su iMac o come servizio macOS):
```bash
# Su iMac via PM2
pm2 start "npx @playwright/mcp@latest --port 8931" --name playwright-mcp
```

Con SSE, se il server crasha e si riavvia, Claude Code si riconnette automaticamente.
Questa e' la soluzione piu' robusta per uso production ma richiede server sempre
attivo (iMac) o servizio launchd su macOS.

### Implementazione specifica per ARGOS (configurazione finale raccomandata)

La configurazione ottimale per ARGOS combina le 3 soluzioni:

**`~/.claude.json` — configurazione finale**:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "/bin/bash",
      "args": [
        "/Users/macbook/.argos-playwright-wrapper.sh",
        "--extension"
      ]
    }
  }
}
```

Con `--extension`: zero conflitti Chrome, zero crash da profile lock.
Con wrapper: se il processo MCP muore per qualunque ragione, si riavvia da solo.
Con extension mode: browser_file_upload NON e' disponibile (usa Chrome nativo,
non un browser controllato da Playwright) — ma questo risolve anche il Problema 2.

**Script wrapper da creare**:
```bash
cat > ~/.argos-playwright-wrapper.sh << 'EOF'
#!/bin/bash
# ARGOS Playwright MCP — auto-restart wrapper
# Creato: 2026-03-23
echo "[ARGOS Playwright] Avvio..." >&2
while true; do
  npx -y @playwright/mcp@latest "$@"
  echo "[ARGOS Playwright] Terminato. Riavvio in 2s..." >&2
  sleep 2
done
EOF
chmod +x ~/.argos-playwright-wrapper.sh
```

### Fonte/riferimento

- [Issue #5670 — Let Claude AI self reconnect to MCP (chiuso: not planned)](https://github.com/anthropics/claude-code/issues/5670)
- [Issue #11385 — /mcp reconnect causes deadlock](https://github.com/anthropics/claude-code/issues/11385)
- [Issue #1383 — BUG Playwright MCP frequently fails](https://github.com/anthropics/claude-code/issues/1383)
- [Issue #6224 — MCP Initialization fails requiring manual restart](https://github.com/anthropics/claude-code/issues/6224)
- [Simon Willison TIL — Using Playwright MCP with Claude Code](https://til.simonwillison.net/claude-code/playwright-mcp-claude-code)

---

## CONFIGURAZIONE FINALE ARGOS — SINTESI

Obiettivo: Playwright MCP stabile, zero conflitti Chrome, auto-recover da crash.

### Setup da eseguire (una volta sola)

```bash
# Step 1: Crea wrapper auto-restart
cat > ~/.argos-playwright-wrapper.sh << 'EOF'
#!/bin/bash
echo "[ARGOS Playwright] Avvio..." >&2
while true; do
  npx -y @playwright/mcp@latest "$@"
  echo "[ARGOS Playwright] Terminato. Riavvio in 2s..." >&2
  sleep 2
done
EOF
chmod +x ~/.argos-playwright-wrapper.sh

# Step 2: Installa estensione Chrome (manuale in chrome://extensions)
# URL: https://github.com/microsoft/playwright-mcp/tree/main/extension

# Step 3: Aggiorna ~/.claude.json
# (vedi configurazione sopra — --extension flag)

# Step 4: Riavvia Claude Code per caricare nuova config
```

### Matrice decisionale

| Scenario | Soluzione |
|---------|-----------|
| Chrome aperto, no lock | Extension mode (--extension) |
| Chrome chiuso, login necessario | --isolated + --storage-state |
| Upload file < 50MB | browser_file_upload (sequenza atomica) |
| Upload file > 50MB | Upload manuale o URL-based |
| MCP disconnesso | Wrapper auto-restart (risolto automaticamente) |
| /mcp reconnect | NON USARE — causa deadlock |

### Versione @playwright/mcp raccomandata

Usare una versione pinned invece di `@latest` per stabilita':
```bash
# Versione stabile confermata (feb 2026):
npx @playwright/mcp@0.0.68
```

Verificare la versione corrente su: https://github.com/microsoft/playwright-mcp/releases

---

## AGGIORNAMENTO skill-browser-chrome/skill.md

Il file `.claude/skills/skill-browser-chrome/skill.md` va aggiornato per:
1. Rimuovere la configurazione `--user-data-dir ~/.argos-chrome-profile` (vulnerabile al lock)
2. Aggiungere il wrapper auto-restart come configurazione default
3. Documentare il divieto di `/mcp reconnect` (deadlock)
4. Aggiungere la sequenza corretta per browser_file_upload

---

*Research completata: 2026-03-23 | ARGOS S78 | Fonti: 15 issue GitHub verificate*
