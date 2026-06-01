# S78 — Platform Automation Solutions
## Setup piattaforme ARGOS: soluzioni verificate 2026
### Ricerca: 2026-03-23 | Skill: deep-research

---

## SOMMARIO ESECUTIVO

7 task S78 analizzati. Risultato:

| Task | Metodo ottimale | Browser richiesto | Rischio captcha | Effort |
|------|----------------|-------------------|-----------------|--------|
| Trustpilot Business | Browser manuale (1 volta) | SI | BASSO | 15 min |
| ProvenExpert | Browser manuale (1 volta) | SI | BASSO | 20 min |
| LinkedIn profilo | Browser manuale (1 volta) | SI | ALTO con bot | 30 min |
| Facebook Business Page | Browser manuale (1 volta) | SI | MEDIO | 20 min |
| Europages | Browser manuale (1 volta) | SI | BASSO | 10 min |
| Gmail firma | Gmail API Python (CLI) | NO | NESSUNO | 5 min |
| Cloudflare Pages deploy | Wrangler CLI (CI-ready) | NO | NESSUNO | 3 min |

**Regola generale verificata**: Le piattaforme social (LinkedIn, Facebook, Trustpilot) non hanno
API gratuite per la creazione account da zero. Il browser e' obbligatorio per il primo setup.
Post-setup, alcune operazioni sono automatizzabili via API.

---

## 1. TRUSTPILOT BUSINESS

### Piano Free — funzionalita' verificate

- 50 inviti recensione/mese (sufficienti per fase startup)
- Risposta a tutte le recensioni
- 1 dominio, 1 utente
- NO widget TrustBox
- NO integrazioni automatiche invito
- NO analytics avanzate
- Gratis, no carta di credito

**PROBLEMA DOMINIO**: Trustpilot preferisce email con dominio corrispondente al sito
(es. luca@argos-automotive.it). Con Gmail gratuito il claim funziona ma puo' essere
piu' lento (verifica manuale). Soluzione: usare ferretti.argosautomotive@gmail.com
e verificare con la pagina del sito argos-automotive.pages.dev.

### Setup via Browser (metodo corretto)

```
URL: https://business.trustpilot.com
Account: ferretti.argosautomotive@gmail.com

Passaggi:
1. Click "Create free account"
2. Inserisci URL sito: https://argos-automotive.pages.dev
3. Trustpilot cerca il profilo esistente — se non trovato, crealo
4. Verifica via email (controlla spam)
5. Completa profilo: nome, categoria, descrizione
6. Vai a sezione "Get Reviews" → copia il link unico
   (formato: https://it.trustpilot.com/review/argos-automotive.pages.dev)
```

**GENERAZIONE LINK INVITO**:
Il link di invito si trova in: Business Dashboard > Get Reviews > Share Link.
Questo link va nei template WA per raccogliere recensioni.

Formato link diretto per scrivere una recensione:
```
https://www.trustpilot.com/evaluate/argos-automotive.pages.dev
```

### Playwright MCP — fattibilita'

FATTIBILE per il setup iniziale. Trustpilot non usa captcha aggressivi nella registrazione.
Rischio ban: BASSO (e' un processo legittimo, non scraping).

Comando per Playwright MCP:
```
"Usa playwright per andare su business.trustpilot.com,
creare un account con ferretti.argosautomotive@gmail.com
e il sito argos-automotive.pages.dev"
```

### API Trustpilot (post-setup)

Trustpilot ha una API per il piano free con funzionalita' limitate.
Base URL: `https://api.trustpilot.com/v1/`
Per il piano free: solo lettura profilo e recensioni pubbliche.
Invito via API: solo piano a pagamento.
Conclusione: non serve API — link diretto e' sufficiente.

---

## 2. PROVENEXPERT

### Piano Free — funzionalita' verificate

- Profilo pubblico con raccolta recensioni
- Survey template per oltre 40 settori (incluso automotive)
- Listato su ExpertCompass (directory DACH)
- 30 giorni trial completo, poi free con limiti
- NO analytics avanzate nel free
- Ideale per credibilita' su mercato DE/AT

**VALORE ARGOS**: ProvenExpert e' molto conosciuto in Germania. Un profilo con
10-15 recensioni DE aumenta credibilita' con dealer che verificano online.

### Setup via Browser

```
URL: https://www.provenexpert.com/it/ (o /de/ per interfaccia tedesca)
Account: ferretti.argosautomotive@gmail.com

Passaggi:
1. Click "Registrati gratis" o "Kostenlos registrieren"
2. Scegli "Libero professionista" o "Azienda"
3. Categoria: Automotive > Mediazione auto / Fahrzeughandel
4. Nome profilo: "Luca Ferretti – Vehicle Sourcing EU"
5. Completa con sito, descrizione, foto
6. Genera link raccolta recensioni dalla dashboard
```

### Playwright MCP — fattibilita'

FATTIBILE. ProvenExpert non usa protezioni anti-bot aggressive.
Rischio ban: MOLTO BASSO.

### Testo profilo in tedesco (pronto per copy-paste)

```
Ich finde BMW, Mercedes, Audi und Porsche auf europäischen Märkten für
italienische Autohändler. 10+ Jahre Erfahrung, direkter Zugang zum deutschen
Markt. Success-Fee-Modell: Sie zahlen nur bei erfolgreich geliefertem Fahrzeug.
Einsatzgebiet: Kampanien, Apulien, Kalabrien, Basilikata, Sizilien.
WhatsApp: +39 328 153 6308
```

---

## 3. LINKEDIN PROFILO PROFESSIONALE

### Rischi automazione — CRITICO

LinkedIn e' la piattaforma con anti-bot PIU' AGGRESSIVA in 2026.
- Sezione 8.2 ToS vieta esplicitamente bot e scraping
- Rilevamento: fingerprinting browser, pattern comportamentale, IP reputation
- Sanzioni: Tier 1 (blocco 1-24h) → Tier 2 (lock 3-14 gg) → Tier 3 (ban permanente)
- Browser extension hanno 60% detection rate PIU' ALTO vs accesso normale

**VERDETTO PER ARGOS**: La creazione del profilo va fatta MANUALMENTE dal founder.
Non usare Playwright MCP per LinkedIn — rischio ban dell'account appena creato
prima ancora di usarlo.

### Setup Manuale (unica opzione sicura)

```
URL: https://www.linkedin.com/signup

Passaggi:
1. Crea account con ferretti.argosautomotive@gmail.com
2. Nome: Luca Ferretti
3. Headline: Vehicle Sourcing EU per Concessionari | BMW · Mercedes · Audi
4. Location: Italia
5. Industry: Automotive
6. Aggiungi foto da assets/profile_placeholder_v2.png
7. Aggiungi banner da assets/cover_google_business_v2.png (ritagliare 1584x396)
8. Copia About da tools/platform_setup_playbook.md (sezione 3)
9. Aggiungi esperienza: "Vehicle Sourcing Specialist – 2016 a oggi"
10. Skills: Vehicle Sourcing, Automotive Sales, Import/Export, B2B Sales
```

### Uso di Playwright per LinkedIn (solo post-login sicuro)

Se gia' loggato nel profilo Chrome dedicato (~/.argos-chrome-profile),
Playwright puo' essere usato SOLO per leggere il profilo pubblico, non per
creare contenuti o interagire in modo automatico.

---

## 4. FACEBOOK BUSINESS PAGE

### Struttura corretta (non confondere con profilo personale)

```
URL creazione pagina: https://www.facebook.com/pages/creation/

Tipo: Business o brand
Categoria: "Consulente Automobilistico" o "Importazione auto"
Nome pagina: "Luca Ferretti – Vehicle Sourcing EU"
```

### Setup CTA WhatsApp

Facebook supporta bottone WhatsApp nativo sulle pagine:
```
Pagina creata > Edit Page Info > Add a Button > Contact > Send WhatsApp Message
Inserisci: +393281536308
Verifica via codice SMS nel telefono con WhatsApp Business
```

Questo crea il bottone "Invia messaggio su WhatsApp" direttamente sulla pagina
Facebook — i dealer cliccano e arrivano su WA senza friction.

### Playwright MCP — fattibilita'

PARZIALMENTE FATTIBILE. Facebook usa captcha durante registrazione account.
La creazione PAGINA su un account gia' loggato e' piu' semplice.

Strategia consigliata:
1. Login manuale nell'account Facebook personale del founder
2. Playwright MCP (con profilo persistente) per creare la pagina business
3. Playwright compila i form, il founder risolve eventuali captcha manualmente

```
"Usa playwright con profilo ~/.argos-chrome-profile per andare su
facebook.com/pages/creation e creare una pagina business per
'Luca Ferretti - Vehicle Sourcing EU', categoria automotive"
```

### Upload immagini Facebook via Playwright

Facebook usa input type="file" standard. Il metodo corretto con Playwright MCP:
```
browser_click (sul bottone upload foto)
→ questo apre il file chooser
→ Playwright intercetta con expect_file_chooser()
→ imposta il path assoluto del file

Path copertina: /Users/macbook/Documents/combaretrovamiauto-enterprise/assets/cover_google_business_v2.png
Path profilo: /Users/macbook/Documents/combaretrovamiauto-enterprise/assets/profile_placeholder_v2.png
```

**NOTA**: Il metodo `setInputFiles()` diretto su elementi nascosti puo' fallire.
Il workaround affidabile e' cliccare il bottone upload PRIMA di intercettare il dialog.

---

## 5. EUROPAGES B2B

### Piano Free — confermato

```
URL: https://www.europages.co.uk/en/supplier-registration
URL alternativo: https://ols.europages.com/EN/free-listing-registration.html

Piano Basic = GRATUITO
Funzionalita': listing directory, profilo base, contatto da acquirenti
Visibilita': limitata vs piano Business (€399/mese) e Premium (€899/mese)
```

**VALUTAZIONE PER ARGOS**: Europages ha traffico B2B europeo ma bassa
rilevanza per dealer Sud Italia. Priorita' BASSA rispetto a Google Business e Trustpilot.
Fare il listing richiede 10 minuti e non costa nulla — vale fatto.

### Dati da inserire

```
Ragione sociale: Luca Ferretti – Vehicle Sourcing EU
Settore: Automotive > Import/Export veicoli
Paesi serviti: Italia (Campania, Puglia, Calabria, Basilicata, Sicilia)
Sito: https://argos-automotive.pages.dev
Telefono: +390972536918
```

### Playwright MCP — fattibilita'

FATTIBILE. Europages usa form standard, rischio captcha basso.

---

## 6. GMAIL FIRMA — VIA API (SENZA BROWSER)

### Soluzione ottimale: Gmail API Python

La firma HTML e' gia' pronta in `copy/email_signature.html`.
Gmail API permette di impostarla via script senza aprire il browser.

**Endpoint**:
```
PATCH https://gmail.googleapis.com/gmail/v1/users/me/settings/sendAs/{emailAddress}
```

**OAuth scope richiesto**:
```
https://www.googleapis.com/auth/gmail.settings.basic
```

**Script Python completo** (zero costo, Google Cloud Console richiesto):

```python
#!/usr/bin/env python3
"""
Script: set_gmail_signature.py
Imposta la firma HTML su ferretti.argosautomotive@gmail.com
Requisiti: google-auth google-auth-oauthlib google-api-python-client
"""
import os
import html
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.settings.basic']
SIGNATURE_FILE = '/Users/macbook/Documents/combaretrovamiauto-enterprise/copy/email_signature.html'
TARGET_EMAIL = 'ferretti.argosautomotive@gmail.com'

def load_signature(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Rimuove commenti HTML prima di inserire nella firma
    import re
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    return content.strip()

def get_credentials():
    """OAuth flow — richiede credentials.json da Google Cloud Console"""
    flow = InstalledAppFlow.from_client_secrets_file(
        os.path.expanduser('~/.argos-gmail-credentials.json'),
        SCOPES
    )
    creds = flow.run_local_server(port=0)
    return creds

def set_signature(service, email: str, signature_html: str):
    """Aggiorna la firma per l'alias primario"""
    # Lista alias per trovare quello primario
    aliases = service.users().settings().sendAs().list(userId='me').execute()

    primary = None
    for alias in aliases.get('sendAs', []):
        if alias.get('isPrimary', False):
            primary = alias['sendAsEmail']
            break

    if not primary:
        primary = email

    result = service.users().settings().sendAs().patch(
        userId='me',
        sendAsEmail=primary,
        body={'signature': signature_html}
    ).execute()

    print(f"Firma aggiornata per: {result['sendAsEmail']}")
    return result

if __name__ == '__main__':
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    sig = load_signature(SIGNATURE_FILE)
    set_signature(service, TARGET_EMAIL, sig)
    print("Done.")
```

### Setup Google Cloud Console (una volta sola)

```
1. Vai su: https://console.cloud.google.com
2. Crea nuovo progetto: "argos-gmail-setup"
3. APIs & Services > Enable APIs > cerca "Gmail API" > Enable
4. APIs & Services > Credentials > Create Credentials > OAuth client ID
5. Application type: Desktop app
6. Scarica il JSON → salvalo in ~/.argos-gmail-credentials.json
7. In OAuth consent screen: User Type = External, aggiungi ferretti.argosautomotive@gmail.com come Test user
```

### Installazione dipendenze

```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

### Esecuzione

```bash
python3 /Users/macbook/Documents/combaretrovamiauto-enterprise/tools/set_gmail_signature.py
# Si apre browser per OAuth → autorizza l'app → firma impostata
```

**Nota**: La prima esecuzione apre il browser per l'autorizzazione OAuth.
Le successive usano il token cached (nessuna interazione richiesta).

### Alternativa rapida: metodo manuale

Se preferisci fare manualmente (5 min):
```
1. Gmail > Impostazioni (ingranaggio) > Visualizza tutte le impostazioni
2. Scheda "Generale" > sezione "Firma" > "Crea nuova firma"
3. Nome: "Luca Ferretti ARGOS"
4. Nell'editor, clicca su "Altro formato" (icona <>) per accedere HTML
   OPPURE: incolla direttamente il testo — Gmail accetta HTML nel campo firma
5. Incolla il contenuto del file copy/email_signature.html
   (solo il blocco <table>...</table>, senza i commenti iniziali)
6. Salva in fondo alla pagina
```

**IMPORTANTE**: Gmail sanitizza l'HTML prima di salvarlo — elementi come
`<script>`, `<style>` esterni vengono rimossi. La firma attuale usa
solo inline styles e table layout: compatibile al 100%.

---

## 7. CLOUDFLARE PAGES DEPLOY

### Deploy non-interattivo (CI-ready)

```bash
# Setup una-tantum: crea token da Cloudflare Dashboard
# dashboard.cloudflare.com > My Profile > API Tokens > Create Token
# Template: Edit Cloudflare Workers (include Pages)
# Permessi minimi per Pages: Account > Cloudflare Pages > Edit

# Salva in .env (mai committare)
export CLOUDFLARE_API_TOKEN="tuo_token_qui"
export CLOUDFLARE_ACCOUNT_ID="tuo_account_id"

# Deploy (dalla directory landing/)
cd /Users/macbook/Documents/combaretrovamiauto-enterprise/landing
npx wrangler pages deploy . \
  --project-name=argos-automotive \
  --branch=production
```

### Come trovare Account ID

```
Cloudflare Dashboard > Workers & Pages > Overview
Account ID visibile nella sidebar destra
OPPURE: dashboard.cloudflare.com/[account_id]/workers/overview
```

### Configurazione .env locale

Aggiungere al file .env esistente:
```
CLOUDFLARE_API_TOKEN=xxx
CLOUDFLARE_ACCOUNT_ID=xxx
```

### Script deploy completo

```bash
#!/bin/bash
# deploy_landing.sh — deploy Cloudflare Pages da Claude Code

set -e
source /Users/macbook/Documents/combaretrovamiauto-enterprise/.env

cd /Users/macbook/Documents/combaretrovamiauto-enterprise/landing

echo "Deploy landing page ARGOS..."
npx wrangler pages deploy . \
  --project-name=argos-automotive \
  --branch=production

echo "Deploy completato."
echo "URL: https://argos-automotive.pages.dev"
```

### Verifica deploy

```bash
# Controlla ultimo deployment
npx wrangler pages deployment list --project-name=argos-automotive
```

**Non richiede browser. Non richiede interazione manuale. Zero rischio captcha.**

---

## PLAYWRIGHT MCP — REFERENCE TECNICO

### Problemi comuni e soluzioni verificate

#### Problema 1: File upload che crasha

```
CAUSA: Playwright clicca il bottone ma non intercetta il dialog a tempo
SOLUZIONE CORRETTA:
  1. Non usare setInputFiles() direttamente su elementi nascosti
  2. Usare la sequenza: click bottone > intercetta file chooser > imposta file

In una sessione Playwright MCP:
  browser_click "[bottone upload foto]"
  # Playwright intercetta automaticamente il dialog del sistema operativo
  # e inietta il file PRIMA che il dialog si apra
  # Se crasha, alternativa: trovare il <input type="file"> nascosto via snapshot
  # e usare browser_snapshot() per trovare il selector esatto
```

#### Problema 2: Dropdown fuori viewport

```
CAUSA: Il dropdown apre elementi che escono dalla viewport
SOLUZIONE: Playwright scrolla automaticamente prima delle azioni.
  Se non funziona:
  browser_scroll [direzione: down] [per portare l'elemento in viewport]
  poi cliccare l'opzione
```

#### Problema 3: Dialog di conferma (alert/confirm)

```
CAUSA: Alert nativi del browser bloccano l'automazione
SOLUZIONE: Playwright li gestisce automaticamente.
  Se il dialog persiste, usare:
  browser_snapshot() per vedere lo stato corrente
  browser_click "[tasto OK/Conferma nel dialog]"
```

#### Problema 4: Scroll in elementi specifici (non pagina intera)

```
CAUSA: Alcune liste/dropdown hanno scroll interno, non la pagina
SOLUZIONE:
  browser_scroll con il selector specifico del container
  Esempio: browser_scroll "#lista-categorie" direction:down pixels:200
```

#### Problema 5: Sessioni lunghe multi-sito (token scaduto)

```
CAUSA: Cookie di sessione scadono durante sessione lunga
PREVENZIONE:
  - Usare profilo persistente ~/.argos-chrome-profile
  - Non chiudere browser tra task dello stesso sito
  - Se sessione scade: browser_navigate al login → riautenticarsi
```

### Captcha — gestione 2026

```
APPROCCIO CORRETTO per registrazione piattaforme:
  Non tentare bypass captcha. E' contro i ToS e inaffidabile.

PATTERN "PAUSE AND ATTACH" (Playwright MCP nativo):
  Quando appare un captcha:
  1. Playwright MCP mostra il browser
  2. Il founder risolve il captcha manualmente
  3. Claude riprende l'automazione dopo la risoluzione

Questo e' il metodo raccomandato per il 2026 per task one-time
come creazione profili (non scraping continuativo).
```

### Priorita' piattaforme per Playwright MCP

| Piattaforma | Playwright OK | Note |
|------------|--------------|-------|
| Trustpilot | SI | Rischio basso, form semplici |
| ProvenExpert | SI | Rischio molto basso |
| Facebook (pagina su account esistente) | SI con monitoraggio | Possibili captcha |
| Europages | SI | Form standard |
| LinkedIn | NO | Rischio ban alto — solo manuale |
| Gmail firma | NO — usare API | Piu' veloce e affidabile |
| Cloudflare Pages | NO — usare CLI | wrangler e' la soluzione corretta |

---

## SEQUENZA DI ESECUZIONE RACCOMANDATA S78

```
Ordine ottimale (durata totale stimata: 2-3 ore):

SESSIONE 1 — CLI (nessun browser):
  [ ] 1. Configura .env con CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID
  [ ] 2. Run: npx wrangler pages deploy . (da /landing)
  [ ] 3. Setup Gmail API credentials in Google Cloud Console
  [ ] 4. Run: python3 tools/set_gmail_signature.py

SESSIONE 2 — Browser manuale (founder al computer):
  [ ] 5. LinkedIn: crea profilo manualmente (no automazione)
  [ ] 6. Trustpilot: registrazione con Playwright MCP o manuale
  [ ] 7. ProvenExpert: registrazione con Playwright MCP o manuale
  [ ] 8. Facebook: login con account personale > crea pagina > CTA WhatsApp
  [ ] 9. Europages: form di registrazione base

POST-SETUP:
  [ ] 10. Copia link recensione Trustpilot da dashboard
  [ ] 11. Copia link recensione ProvenExpert da dashboard
  [ ] 12. Aggiorna template WA con i link (copy/template_recensione_wa.txt)
  [ ] 13. Avvia piano recensioni (tools/recensioni_estere_strategy.md)
```

---

## FONTI

- [Trustpilot Free Plan features](https://business.trustpilot.com/pricing/free)
- [Trustpilot claim profile guide](https://support.trustpilot.com/hc/en-us/articles/115015561467)
- [Gmail API signature endpoint](https://developers.google.com/workspace/gmail/api/guides/alias_and_signature_settings)
- [Gmail API sendAs reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.sendAs)
- [Cloudflare Pages Direct Upload CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)
- [Cloudflare Wrangler auth docs](https://developers.cloudflare.com/workers/wrangler/migration/v1-to-v2/wrangler-legacy/authentication/)
- [Playwright MCP GitHub](https://github.com/microsoft/playwright-mcp)
- [Playwright file upload guide](https://www.browserstack.com/guide/playwright-upload-file)
- [Playwright captcha 2026](https://www.browserstack.com/guide/playwright-captcha)
- [LinkedIn automation ban risk 2026](https://growleads.io/blog/linkedin-automation-ban-risk-2026-safe-use/)
- [ProvenExpert free plan](https://help.provenexpert.com/en/provenexpert-free-plan)
- [Europages free listing](https://ols.europages.com/EN/free-listing-registration.html)
- [Facebook CTA WhatsApp button](https://roihacks.com/facebook-call-to-action-buttons/)
