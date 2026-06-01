# S78 — Google Business Profile: Automazione Programmatica 2026
**Data ricerca**: 2026-03-23
**Scope**: Upload foto, post, Q&A, descrizione — senza Playwright/browser instabile

---

## EXECUTIVE SUMMARY

Google Business Profile ha una API ufficiale REST (v4) che permette di gestire
post, foto e informazioni profilo **senza browser**. Esiste però un requisito
critico: Google richiede approvazione esplicita per accedere alle API.
Senza approvazione, le chiamate restituiscono 403.

**Situazione 2026**:
- POST localPosts (aggiornamenti): API v4 funzionante, endpoint stabile
- FOTO profilo/copertina: API v4 funzionante, upload da URL o da bytes
- Q&A: RIMOSSA dal 3 novembre 2025 — API discontinuata, feature eliminata da Google
- Descrizione/Info business: API separata (Business Information API v1) — funzionante

---

## 1. STATO API UFFICIALE 2026

### 1.1 Architettura attuale

Google ha suddiviso la vecchia "Google My Business API" in 8 API separate:

| API | Endpoint base | Funzione | Status 2026 |
|-----|---------------|----------|-------------|
| My Business API (v4) | mybusiness.googleapis.com/v4 | Post, foto, reviews | ATTIVO |
| Business Information API | mybusinessbusinessinformation.googleapis.com/v1 | Info, orari, attributi | ATTIVO |
| Account Management API | mybusinessaccountmanagement.googleapis.com/v1 | Account, locations | ATTIVO |
| Business Profile Performance API | businessprofileperformance.googleapis.com/v1 | Analytics/metriche | ATTIVO |
| My Business Q&A API | — | Q&A | DISCONTINUATA nov 2025 |
| My Business Notifications API | — | Notifiche | ATTIVO |
| My Business Verifications API | — | Verifica | ATTIVO |
| My Business Place Actions API | — | Azioni | ATTIVO |

### 1.2 Cosa funziona e cosa no

**FUNZIONA via API:**
- Creare post di tipo "Aggiornamento" (STANDARD), Evento, Offerta
- Upload foto profilo (logo, copertina, galleria)
- Modificare descrizione business
- Modificare orari, contatti, attributi

**NON FUNZIONA via API (limitazioni documentate):**
- Post di tipo "Prodotto" (Product Posts) — non supportati dall'API
- Q&A — API rimossa definitivamente il 3 novembre 2025
- Video upload su post (solo URL immagine per post)
- Creazione nuovo profilo business (solo gestione di profili esistenti)

### 1.3 Problema critico: approvazione richiesta

```
REQUISITO: L'API non e' pubblica.
Ogni sviluppatore/azienda deve richiedere accesso via form ufficiale:
https://support.google.com/business/workflow/16726127

PREREQUISITI:
- Google Business Profile verificato e attivo da 60+ giorni
- Sito web associato al profilo
- Google Cloud Project con numero progetto

TEMPO APPROVAZIONE: indicato "entro 14 giorni" nella FAQ ufficiale
INDICATORE: quota 0 QPM = non approvato, 300 QPM = approvato

NOTA POSITIVA: il profilo di Luca Ferretti soddisfa questi requisiti
appena creato e verificato (richiesta inviabile al momento della creazione).
```

---

## 2. SETUP COMPLETO — PASSO PER PASSO (GRATUITO)

### Step 1 — Google Cloud Console

```
1. Vai a: https://console.cloud.google.com
2. Crea nuovo progetto: "argos-automotive-gbp"
3. Vai a API & Services > Library
4. Abilita TUTTE queste API (obbligatorie):
   - Google My Business API
   - My Business Account Management API
   - My Business Business Information API
   - My Business Place Actions API
   - My Business Notifications API
   - My Business Verifications API
   (Le API si vedono solo dopo approvazione Google — vedi Step 2)
```

### Step 2 — Richiedi accesso API

```
URL form: https://support.google.com/business/workflow/16726127

Compilare:
- Google Cloud Project Number (trovalo in Cloud Console > Project info)
- Email dell'account proprietario del profilo GBP
- Application type: "Application for Basic API Access"
- Use case: gestione profilo personale per attivita' di vehicle sourcing

Attendi email di approvazione (max 14 giorni).
Verifica approvazione: Cloud Console > APIs > Google My Business API > Quotas
  0 QPM = non approvato
  300 QPM = approvato, pronto all'uso
```

### Step 3 — Crea credenziali OAuth 2.0

```
1. Cloud Console > APIs & Services > Credentials
2. Create credentials > OAuth client ID
3. Application type: Desktop App (non Web App — piu' semplice per uso personale)
4. Nome: "ARGOS GBP Manager"
5. Scarica il JSON -> salva come: .env/gbp_credentials.json
6. MAI committare questo file su git
```

### Step 4 — OAuth Consent Screen

```
1. Cloud Console > APIs & Services > OAuth consent screen
2. User Type: External (anche con account personale)
3. App name: "ARGOS Automotive GBP"
4. Support email: ferretti.argosautomotive@gmail.com
5. Developer email: stessa
6. Scopes: aggiungi "https://www.googleapis.com/auth/business.manage"
7. Test users: aggiungi ferretti.argosautomotive@gmail.com
8. Publishing status: lascia "Testing" per uso personale
   NOTA: in modalita' Testing il refresh token scade ogni 7 giorni
   -> Soluzione: metti in "Production" (richiede verifica Google ma gratuita)
```

### Step 5 — Ottieni Refresh Token (una sola volta)

```python
#!/usr/bin/env python3
# Salva come: tools/gbp_auth_setup.py
# Esegui UNA SOLA VOLTA dal MacBook (serve browser per autorizzare)

from google_auth_oauthlib.flow import InstalledAppFlow
import json, os

SCOPES = ['https://www.googleapis.com/auth/business.manage']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '../.env/gbp_credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '../.env/gbp_token.json')

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=8080)

# Salva token (contiene refresh_token persistente)
with open(TOKEN_FILE, 'w') as f:
    f.write(creds.to_json())

print(f"Token salvato in {TOKEN_FILE}")
print(f"Refresh token: {creds.refresh_token}")
```

```bash
# Installazione dipendenze (una volta)
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client requests

# Esecuzione setup auth
python3 tools/gbp_auth_setup.py
# Si apre browser -> accedi con ferretti.argosautomotive@gmail.com -> autorizza
# Il refresh token viene salvato in .env/gbp_token.json
```

### Step 6 — Trova Account ID e Location ID

```python
#!/usr/bin/env python3
# Salva come: tools/gbp_get_ids.py
# Esegui per trovare account_id e location_id

import json, os
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def load_credentials():
    token_file = os.path.join(os.path.dirname(__file__), '../.env/gbp_token.json')
    creds = Credentials.from_authorized_user_file(token_file)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
    return creds.token

token = load_credentials()
headers = {'Authorization': f'Bearer {token}'}

# 1. Trova account ID
resp = requests.get(
    'https://mybusinessaccountmanagement.googleapis.com/v1/accounts',
    headers=headers
)
accounts = resp.json()
print("ACCOUNTS:", json.dumps(accounts, indent=2))

# 2. Trova location ID (usa account_id dall'output sopra)
account_id = accounts['accounts'][0]['name']  # es: "accounts/123456789"
resp2 = requests.get(
    f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}/locations',
    headers=headers
)
print("LOCATIONS:", json.dumps(resp2.json(), indent=2))
# Cerca il campo "name" -> es: "locations/987654321"
# Salva account_id e location_id in .env
```

---

## 3. IMPLEMENTAZIONE — TUTTE LE OPERAZIONI

### 3.1 Script principale GBP Manager

```python
#!/usr/bin/env python3
"""
ARGOS GBP Manager — Gestione programmatica Google Business Profile
Percorso: tools/gbp_manager.py
"""

import os, json, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path

# Configurazione (da .env)
TOKEN_FILE = Path(__file__).parent / '../.env/gbp_token.json'
ACCOUNT_ID = os.getenv('GBP_ACCOUNT_ID')   # es: "accounts/123456789"
LOCATION_ID = os.getenv('GBP_LOCATION_ID') # es: "locations/987654321"

BASE_V4 = "https://mybusiness.googleapis.com/v4"
BASE_INFO = "https://mybusinessbusinessinformation.googleapis.com/v1"

def get_token() -> str:
    """Restituisce access token valido, rinnova se scaduto."""
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return creds.token

def headers() -> dict:
    return {
        'Authorization': f'Bearer {get_token()}',
        'Content-Type': 'application/json'
    }

# ─────────────────────────────────────────────
# POST: Crea "Aggiornamento" con testo e immagine
# ─────────────────────────────────────────────
def create_post(text: str, image_url: str = None) -> dict:
    """
    Crea un post di tipo STANDARD (Aggiornamento).
    image_url: URL pubblico dell'immagine (deve essere accessibile da Google)
    """
    payload = {
        "languageCode": "it",
        "summary": text,
        "topicType": "STANDARD"
    }
    if image_url:
        payload["media"] = [{
            "mediaFormat": "PHOTO",
            "sourceUrl": image_url
        }]

    url = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/localPosts"
    resp = requests.post(url, headers=headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────
# POST: Crea Evento
# ─────────────────────────────────────────────
def create_event_post(title: str, description: str,
                      start_date: dict, end_date: dict,
                      image_url: str = None) -> dict:
    """
    Crea un post di tipo EVENTO.
    start_date/end_date: {"year": 2026, "month": 4, "day": 15}
    """
    payload = {
        "languageCode": "it",
        "summary": description,
        "topicType": "EVENT",
        "event": {
            "title": title,
            "schedule": {
                "startDate": start_date,
                "endDate": end_date
            }
        }
    }
    if image_url:
        payload["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": image_url}]

    url = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/localPosts"
    resp = requests.post(url, headers=headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────
# FOTO: Upload foto profilo da URL
# ─────────────────────────────────────────────
def upload_photo_from_url(image_url: str, category: str = "ADDITIONAL") -> dict:
    """
    Carica una foto sul profilo GBP da URL pubblico.

    category options:
    - "COVER"       -> foto di copertina
    - "LOGO"        -> logo/foto profilo
    - "EXTERIOR"    -> esterno locale
    - "INTERIOR"    -> interno locale
    - "AT_WORK"     -> in azione
    - "ADDITIONAL"  -> foto generica galleria
    """
    payload = {
        "mediaFormat": "PHOTO",
        "locationAssociation": {
            "category": category
        },
        "sourceUrl": image_url
    }
    url = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/media"
    resp = requests.post(url, headers=headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────
# FOTO: Upload foto profilo da file locale (bytes)
# ─────────────────────────────────────────────
def upload_photo_from_file(file_path: str, category: str = "ADDITIONAL") -> dict:
    """
    Carica una foto da file locale. 3 step:
    1. Inizia upload (ottieni resourceName)
    2. Carica bytes
    3. Finalizza con Media.Create
    """
    # Step 1: inizia upload
    url_start = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/media:startUpload"
    resp1 = requests.post(url_start, headers=headers(), json={})
    resp1.raise_for_status()
    resource_name = resp1.json()['resourceName']

    # Step 2: carica file bytes
    upload_url = f"https://mybusiness.googleapis.com/upload/v1/media/{resource_name}?upload_type=media"
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    resp2 = requests.post(
        upload_url,
        headers={**headers(), 'Content-Type': 'image/jpeg'},
        data=file_bytes
    )
    resp2.raise_for_status()

    # Step 3: finalizza
    payload = {
        "mediaFormat": "PHOTO",
        "locationAssociation": {"category": category},
        "dataRef": {"resourceName": resource_name}
    }
    url_create = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/media"
    resp3 = requests.post(url_create, headers=headers(), json=payload)
    resp3.raise_for_status()
    return resp3.json()

# ─────────────────────────────────────────────
# DESCRIZIONE: Aggiorna descrizione profilo
# ─────────────────────────────────────────────
def update_description(description: str) -> dict:
    """
    Aggiorna la descrizione del profilo GBP.
    Max 750 caratteri.
    """
    payload = {"profile": {"description": description}}
    url = f"{BASE_INFO}/{LOCATION_ID}?updateMask=profile.description"
    resp = requests.patch(url, headers=headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

# ─────────────────────────────────────────────
# LISTA POST: Mostra post pubblicati
# ─────────────────────────────────────────────
def list_posts() -> list:
    url = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/localPosts"
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json().get('localPosts', [])

# ─────────────────────────────────────────────
# LISTA FOTO: Mostra foto pubblicate
# ─────────────────────────────────────────────
def list_photos() -> list:
    url = f"{BASE_V4}/{ACCOUNT_ID}/{LOCATION_ID}/media"
    resp = requests.get(url, headers=headers())
    resp.raise_for_status()
    return resp.json().get('mediaItems', [])


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "post":
        # python3 tools/gbp_manager.py post "Testo del post" "https://url-immagine.jpg"
        text = sys.argv[2]
        img = sys.argv[3] if len(sys.argv) > 3 else None
        result = create_post(text, img)
        print(json.dumps(result, indent=2))

    elif cmd == "photo":
        # python3 tools/gbp_manager.py photo "https://url-immagine.jpg" COVER
        url = sys.argv[2]
        cat = sys.argv[3] if len(sys.argv) > 3 else "ADDITIONAL"
        result = upload_photo_from_url(url, cat)
        print(json.dumps(result, indent=2))

    elif cmd == "photo-file":
        # python3 tools/gbp_manager.py photo-file /path/to/image.jpg LOGO
        path = sys.argv[2]
        cat = sys.argv[3] if len(sys.argv) > 3 else "ADDITIONAL"
        result = upload_photo_from_file(path, cat)
        print(json.dumps(result, indent=2))

    elif cmd == "list-posts":
        posts = list_posts()
        for p in posts:
            print(f"- {p.get('summary', '')[:80]} [{p.get('state', '')}]")

    elif cmd == "list-photos":
        photos = list_photos()
        for p in photos:
            print(f"- {p.get('name')} [{p.get('locationAssociation', {}).get('category', '')}]")

    elif cmd == "describe":
        desc = sys.argv[2]
        result = update_description(desc)
        print("Descrizione aggiornata:", result.get('profile', {}).get('description', '')[:100])

    else:
        print("""
ARGOS GBP Manager - Comandi:
  post "testo" [url-img]       - Crea post aggiornamento
  photo "url" [COVER|LOGO|...]  - Upload foto da URL
  photo-file /path [categoria]  - Upload foto da file locale
  list-posts                    - Mostra post pubblicati
  list-photos                   - Mostra foto profilo
  describe "testo"              - Aggiorna descrizione
        """)
```

---

## 4. SOLUZIONE IMMAGINI — PROBLEMA SOURCEURL

L'API v4 per i post richiede che le immagini siano su URL pubblico accessibile da Google.
Per le foto di profilo (logo/copertina) si possono caricare da file locale (bytes).

**Opzioni per hosting immagini gratis (per post):**

```
Opzione A — Cloudflare Pages (gia' in uso per landing ARGOS)
  - Metti le immagini in landing/assets/
  - Deploy: npx wrangler pages deploy landing
  - URL risultante: https://argos-automotive.pages.dev/assets/nomefile.jpg
  - GRATIS illimitato, CDN globale, HTTPS nativo

Opzione B — GitHub raw content
  - Commit le immagini su un repo pubblico
  - URL: https://raw.githubusercontent.com/[user]/[repo]/main/[file].jpg
  - GRATIS, nessun hosting da gestire

Opzione C — Google Drive (pubblico)
  - Carica su Drive, rendi pubblico, usa link diretto
  - URL: https://drive.google.com/uc?id=FILE_ID
  - GRATIS ma meno affidabile (Google cambia URLs)

RACCOMANDAZIONE ARGOS: Opzione A (Cloudflare Pages gia' configurato)
```

---

## 5. GESTIONE Q&A — API RIMOSSA (ALTERNATIVA)

La Q&A API e' stata **discontinuata il 3 novembre 2025**. Google ha rimosso
interamente la feature Q&A dai profili GBP, sostituendola con "Ask Maps"
(risposte AI generate da Gemini).

**Cosa fare invece della Q&A:**
- Non c'e' equivalente API programmatico per Ask Maps
- Le "risposte AI" si alimentano automaticamente da: descrizione, foto, orari, attributi
- Azione ARGOS: ottimizzare la descrizione e gli attributi del profilo
  (questo e' gia' automatizzabile via API Business Information)

---

## 6. ALTERNATIVE SENZA APPROVAZIONE API (BACKUP)

Se l'approvazione API tarda o viene rifiutata:

### Opzione B — Playwright con Chrome stabile

**Problema riportato**: instabilita' Playwright. Causa probabile: caricamento lento
dell'UI Google Business (usa React con lazy loading). Soluzione:

```python
# Aggiungi questi parametri al browser Playwright
await page.goto('https://business.google.com', wait_until='networkidle')
await page.wait_for_timeout(3000)  # extra wait dopo networkidle

# Per navigazione post
await page.goto('https://business.google.com/u/0/posts/create')
await page.wait_for_selector('[data-testid="post-text-area"]', timeout=15000)
```

URL diretti per le azioni principali (piu' stabili del menu di navigazione):
```
Post nuovo:   https://business.google.com/u/0/posts/create
Foto:         https://business.google.com/u/0/media/photos
Informazioni: https://business.google.com/u/0/profile
```

### Opzione C — n8n self-hosted (gratuito)

n8n ha un nodo nativo "Google Business Profile" che gestisce OAuth internamente.
Vantaggio: n8n si occupa del token refresh automaticamente.

```bash
# Installa n8n (gia' Node disponibile su iMac)
npm install -g n8n
n8n start  # apre su localhost:5678

# Workflow: trigger cron -> Google Business Profile node -> crea post
# Non richiede approvazione API separata se usi OAuth personale
```

**Limitazione**: n8n usa comunque la stessa API GBP internamente,
quindi se l'account non e' approvato, fallisce ugualmente.

---

## 7. RIEPILOGO DECISIONALE

```
SITUAZIONE ARGOS (marzo 2026):
- Profilo GBP da creare/verificare -> serve 60 giorni prima di richiedere API
- Alternativa immediata: Playwright (browser) per i primi 60 giorni
- Dopo 60 giorni: invia richiesta API -> 14 giorni approvazione
- Da giorno 75-80: gestione completamente programmatica via API

TIMELINE CONSIGLIATA:
Giorno 0:   Crea profilo GBP e verifica identita'
Giorno 1:   Crea Cloud Project, configura OAuth consent screen
Giorno 60:  Invia richiesta API access (form ufficiale)
Giorno 60-74: Usa Playwright per post/foto (stabile con URL diretti)
Giorno 74:  Ricevi approvazione API (o followup se non arriva)
Giorno 75+: python3 tools/gbp_manager.py post "testo" "url-img"
```

---

## 8. FILE DA CREARE PER OPERATIVITA'

```
.env/gbp_credentials.json    <- Scarica da Google Cloud Console (NON su git)
.env/gbp_token.json          <- Generato da gbp_auth_setup.py (NON su git)
.env (aggiungere):
  GBP_ACCOUNT_ID=accounts/123456789
  GBP_LOCATION_ID=locations/987654321

tools/gbp_auth_setup.py      <- Script one-time per auth (da creare)
tools/gbp_manager.py         <- Manager principale (codice in sezione 3.1)
tools/gbp_post_argos.py      <- Script specializzato per post ARGOS (da creare)
```

**Aggiungere a .gitignore:**
```
.env/gbp_credentials.json
.env/gbp_token.json
```

---

## 9. COSTO TOTALE

| Componente | Costo |
|-----------|-------|
| Google Business Profile API | GRATIS (quota 300 QPM gratuiti) |
| Google Cloud Project | GRATIS (nessuna API a pagamento usata) |
| OAuth 2.0 | GRATIS |
| Hosting immagini (Cloudflare Pages) | GRATIS |
| Librerie Python (google-auth-oauthlib) | GRATIS |
| **TOTALE** | **€0/mese** |

---

## FONTI

- [Google Business Profile APIs — Overview](https://developers.google.com/my-business/content/overview) (aggiornato agosto 2025)
- [Upload Media — API Reference](https://developers.google.com/my-business/content/upload-photos)
- [Create Posts — API Reference](https://developers.google.com/my-business/content/posts-data)
- [Prerequisites — API Access](https://developers.google.com/my-business/content/prereqs)
- [Implement OAuth — Python Guide](https://developers.google.com/my-business/content/implement-oauth)
- [Q&A API Discontinued Nov 2025](https://ppc.land/google-discontinues-business-profile-q-a-api-effective-november-3/)
- [n8n GBP Integration Issues — GitHub](https://github.com/n8n-io/n8n/issues/18703)
- [GBP API FAQ](https://developers.google.com/my-business/content/faq)
