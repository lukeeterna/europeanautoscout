# GBP + Facebook Page: Creazione Programmatica — Deep Research S96
**Data**: 2026-04-01 | **Obiettivo**: Trovare TUTTI i modi per creare GBP e Facebook Page SENZA compilare form nel browser

---

## VERDETTO RAPIDO

| Metodo | GBP | Facebook Page |
|--------|-----|---------------|
| API ufficiale - crea da zero | **SI** (con approvazione) | **NO** (impossibile) |
| Bulk upload spreadsheet | **SI** (10+ sedi) | N/A |
| Business Manager API | N/A | **NO** (solo claim) |
| Selenium/Playwright | Viola ToS | Viola ToS |
| Tool terze parti gratis | **NO** (tutti a pagamento) | **NO** |

**Conclusione brutale**: GBP si puo' creare via API ma serve approvazione Google (14 giorni). Facebook Page NON si puo' creare via API — punto. L'unica via e' farlo a mano nel browser o con l'app mobile.

---

## PARTE 1: GOOGLE BUSINESS PROFILE

### Approccio 1: Google Business Profile API — accounts.locations.create

**FUNZIONA PER CREARE NUOVI LISTING? SI.**

L'endpoint `accounts.locations.create` crea effettivamente un nuovo business listing su Google.

**Endpoint (API v1 — attuale):**
```
POST https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{accountId}/locations
```

**Endpoint (API v4 — legacy ma ancora funzionante):**
```
POST https://mybusiness.googleapis.com/v4/accounts/{accountId}/locations
```

**OAuth Scope richiesto:**
```
https://www.googleapis.com/auth/business.manage
```

**Request body completo (esempio per ARGOS):**
```json
{
    "title": "ARGOS Automotive",
    "languageCode": "it",
    "storefrontAddress": {
        "addressLines": ["Via Example 1"],
        "locality": "Foggia",
        "postalCode": "71121",
        "administrativeArea": "FG",
        "regionCode": "IT"
    },
    "phoneNumbers": {
        "primaryPhone": "+393281536308"
    },
    "websiteUri": "https://argos-automotive.pages.dev",
    "categories": {
        "primaryCategory": {
            "name": "gcid:auto_broker"
        }
    },
    "regularHours": {
        "periods": [
            {
                "openDay": "MONDAY",
                "closeDay": "FRIDAY",
                "openTime": "09:00",
                "closeTime": "18:00"
            }
        ]
    },
    "profile": {
        "description": "Scouting veicoli premium EU per concessionari italiani. BMW, Mercedes, Audi, Porsche da Germania, Olanda, Belgio."
    }
}
```

**Campi richiesti:**
- `title` — nome business
- `storefrontAddress` — indirizzo fisico completo
- `categories.primaryCategory` — categoria (es. `gcid:auto_broker`)
- `languageCode` — lingua

**Campi opzionali ma consigliati:**
- `phoneNumbers.primaryPhone`
- `websiteUri`
- `regularHours`
- `profile.description`
- `storeCode` — ID interno
- `labels` — tag interni
- `serviceArea` — per business a domicilio
- `serviceItems` — servizi offerti con prezzi

**Python completo per creare un listing:**
```python
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# 1. OAuth flow
flow = Flow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['https://www.googleapis.com/auth/business.manage']
)
authorization_url, _ = flow.authorization_url(prompt='consent')
print(f"Apri questo URL nel browser: {authorization_url}")
code = input("Inserisci il codice di autorizzazione: ")
flow.fetch_token(code=code)
credentials = flow.credentials

# 2. Build service
service = build('mybusinessbusinessinformation', 'v1', credentials=credentials)

# 3. Trova account ID
accounts = service.accounts().list().execute()
account_name = accounts['accounts'][0]['name']  # es. "accounts/123456789"

# 4. Crea location
location_body = {
    "title": "ARGOS Automotive",
    "languageCode": "it",
    "storefrontAddress": {
        "addressLines": ["Via Example 1"],
        "locality": "Foggia",
        "postalCode": "71121",
        "administrativeArea": "FG",
        "regionCode": "IT"
    },
    "phoneNumbers": {
        "primaryPhone": "+393281536308"
    },
    "websiteUri": "https://argos-automotive.pages.dev",
    "categories": {
        "primaryCategory": {
            "name": "gcid:auto_broker"
        }
    }
}

result = service.accounts().locations().create(
    parent=account_name,
    body=location_body,
    validateOnly=False
).execute()

print(f"Location creata: {result['name']}")
print(f"Place ID: {result.get('metadata', {}).get('placeId', 'pending')}")
```

**curl equivalente:**
```bash
curl -X POST \
  "https://mybusinessbusinessinformation.googleapis.com/v1/accounts/ACCOUNT_ID/locations" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "ARGOS Automotive",
    "languageCode": "it",
    "storefrontAddress": {
        "addressLines": ["Via Example 1"],
        "locality": "Foggia",
        "postalCode": "71121",
        "administrativeArea": "FG",
        "regionCode": "IT"
    },
    "phoneNumbers": {
        "primaryPhone": "+393281536308"
    },
    "websiteUri": "https://argos-automotive.pages.dev",
    "categories": {
        "primaryCategory": {
            "name": "gcid:auto_broker"
        }
    }
  }'
```

### BLOCCO CRITICO: Approvazione API Access

**L'API NON e' pubblica.** Serve approvazione esplicita da Google.

**Requisiti per ottenere accesso:**
1. Account Google con GBP verificato e attivo da 60+ giorni
2. Email owner/manager del GBP esistente
3. Sito web live per il business
4. Progetto Google Cloud Console con Project Number
5. Dimostrare uso legittimo dell'API

**Come richiedere accesso:**
1. Vai su https://support.google.com/business/contact/api_default
2. Seleziona "Application for Basic API Access"
3. Fornisci Project Number da Google Cloud Console
4. Usa email che e' owner/manager sul GBP
5. Attendi revisione (dichiarano 14 giorni)

**Come verificare approvazione:**
- Quota 0 QPM = non approvato
- Quota 300 QPM = approvato

**8 API da abilitare dopo approvazione:**
1. Google My Business API
2. My Business Account Management API
3. My Business Lodging API
4. My Business Place Actions API
5. My Business Notifications API
6. My Business Verifications API
7. My Business Business Information API
8. My Business Q&A API

### PROBLEMA CHICKEN-AND-EGG per ARGOS

L'API richiede un GBP gia' verificato da 60+ giorni. ARGOS non ha ancora un GBP.
Quindi: **il primo GBP DEVE essere creato manualmente**, poi l'API diventa utilizzabile per gestirlo/modificarlo.

### Approccio 2: Bulk Upload Spreadsheet

**FUNZIONA? Solo per 10+ sedi.**

Requisiti:
- Minimo 10 sedi dello stesso business
- Stesso nome e stessa categoria primaria
- File .xls/.xlsx/.ods/.csv
- Service area business NON qualificano

**Procedura:**
1. Vai su Business Profile Manager
2. "Aggiungi profilo" > "Importa profili"
3. Scarica template
4. Compila con 10+ sedi
5. Carica e verifica

**Per ARGOS: NON applicabile** — abbiamo 1 sola sede.

### Approccio 3: Tool terze parti

**Nessuno gratis che crei GBP da zero.**

Tools come Yext, BrightLocal, Semrush gestiscono GBP esistenti. Non ne creano di nuovi. E costano $50-500/mese.

### SOLUZIONE PRATICA PER GBP

**L'unica via realistica per il primo GBP:**
1. Aprire https://business.google.com nel browser (desktop o mobile)
2. Login con l'account Google di Luca Ferretti
3. Compilare i campi (5 minuti)
4. Richiedere verifica (cartolina/telefono/email)
5. DOPO i 60 giorni, richiedere accesso API per automazione futura

---

## PARTE 2: FACEBOOK PAGE

### Approccio 1: Facebook Graph API — /me/accounts

**FUNZIONA PER CREARE NUOVE PAGINE? NO.**

`GET /me/accounts` restituisce le pagine che l'utente gia' gestisce. NON esiste un `POST /me/accounts` per creare nuove pagine.

La documentazione ufficiale Meta e' chiara: "The Pages API enables apps to read and write data for Facebook Pages" — GESTIRE pagine esistenti, non crearne di nuove.

### Approccio 2: pages_manage_metadata

**FUNZIONA PER CREARE PAGINE? NO.**

Questa permission permette:
- Iscriversi a webhook per una pagina
- Aggiornare settings di una pagina

Richiede:
- `pages_show_list` come dipendenza
- App Review (screencast + motivazione)

NON crea pagine. Solo gestisce metadata di pagine esistenti.

### Approccio 3: Facebook Business Suite / Business Management API

**FUNZIONA PER CREARE PAGINE? NO.**

L'endpoint `POST /{business_id}/owned_pages` accetta un parametro `page_id` — cioe' richiede una pagina GIA' ESISTENTE. Serve per "claimare" una pagina nel Business Manager, non per crearla.

Parametri del POST:
- `page_id` (richiesto) — ID della pagina esistente da claimare
- `entry_point` — tipo di claim

Errore 3977: "To claim a Page in Business Manager, you must already be an Admin" — conferma che la pagina deve esistere.

### Approccio 4: Meta Business SDK (Python)

```python
# pip install facebook_business
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

# Questo SDK permette di:
# - Leggere pagine
# - Pubblicare post
# - Gestire ads
# - Gestire Business Manager
# NON permette di: CREARE pagine
```

### Approccio 5: curl con access token

```bash
# Questo FUNZIONA per pubblicare su una pagina ESISTENTE:
curl -X POST "https://graph.facebook.com/v25.0/{page_id}/feed" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test post", "access_token": "PAGE_ACCESS_TOKEN"}'

# Ma NON esiste un endpoint per CREARE una pagina.
# Non c'e' nessun:
# POST /me/pages (non esiste)
# POST /v25.0/pages (non esiste)
# POST /{user_id}/pages (non esiste)
```

### Approccio 6: Automazione browser (Selenium/Playwright)

**Tecnicamente possibile ma:**
- Viola i Terms of Service di Facebook
- Facebook ha rilevamento bot aggressivo
- Account puo' essere bannato/bloccato
- Gia' testato nella sessione S95 — Facebook ha bloccato il flusso

### SOLUZIONE PRATICA PER FACEBOOK PAGE

**L'unica via funzionante:**
1. Aprire https://www.facebook.com/pages/create nel browser
2. O dall'app mobile Facebook > Menu > Pagine > Crea
3. Compilare: nome, categoria, bio (3 minuti)
4. DOPO la creazione, usare l'API per gestire la pagina (post, rispondere messaggi, ecc.)

---

## PARTE 3: DOPO LA CREAZIONE — Cosa si puo' automatizzare

### GBP (dopo creazione manuale + 60 giorni):
- Aggiornare orari, descrizione, foto via API
- Rispondere alle recensioni via API
- Pubblicare post/offerte via API
- Monitorare insights via API

### Facebook Page (dopo creazione manuale):
- Pubblicare post via `POST /{page_id}/feed`
- Rispondere a messaggi via Messenger API
- Gestire commenti via `POST /{comment_id}/comments`
- Leggere insights via `GET /{page_id}/insights`
- Webhook per notifiche real-time

**Permessi necessari post-creazione Facebook:**
```
pages_manage_posts        — pubblicare post
pages_manage_engagement   — rispondere commenti
pages_messaging           — rispondere messaggi
pages_read_engagement     — leggere engagement
pages_read_user_content   — leggere contenuti utente
pages_manage_metadata     — gestire settings + webhook
```

---

## PARTE 4: PIANO D'AZIONE ARGOS

### Immediato (oggi, 5 minuti per ciascuno):

**GBP — Creazione manuale:**
1. Vai su https://business.google.com
2. Login con account Google Luca Ferretti
3. "Aggiungi attivita'"
4. Nome: "ARGOS Automotive"
5. Categoria: "Intermediario auto" o "Auto broker"
6. Indirizzo: (indirizzo reale o service area)
7. Telefono: +39 328 153 6308
8. Sito web: https://argos-automotive.pages.dev
9. Completa e richiedi verifica

**Facebook Page — Creazione manuale:**
1. Vai su https://www.facebook.com/pages/create
2. Login con account personale
3. Nome pagina: "ARGOS Automotive"
4. Categoria: "Concessionario auto" o "Servizio auto"
5. Bio: "Scouting veicoli premium EU per concessionari italiani"
6. Aggiungi foto profilo e copertina (da assets/)
7. Pubblica

### Medio termine (dopo 60 giorni GBP verificato):
1. Richiedere accesso GBP API
2. Automatizzare post, risposte recensioni, aggiornamenti
3. Creare script Python per gestione automatica

### Post-creazione Facebook (immediato):
1. Generare Page Access Token via Graph API Explorer
2. Automatizzare pubblicazione post con cron
3. Setup webhook per notifiche messaggi

---

## FONTI

- Google: https://developers.google.com/my-business/reference/businessinformation/rest/v1/accounts.locations/create
- Google prerequisites: https://developers.google.com/my-business/content/prereqs
- Google basic setup: https://developers.google.com/my-business/content/basic-setup
- Google FAQ: https://developers.google.com/my-business/content/faq
- Google API apply: https://support.google.com/business/contact/api_default
- Google bulk upload: https://support.google.com/business/answer/3370250
- Facebook Pages API: https://developers.facebook.com/docs/pages-api/overview
- Facebook Page node: https://developers.facebook.com/docs/graph-api/reference/page/
- Facebook pages_manage_metadata: https://developers.facebook.com/docs/permissions/reference/pages_manage_metadata
- Facebook owned_pages: https://developers.facebook.com/docs/marketing-api/reference/business/owned_pages/
- Facebook Business Asset Management: https://developers.facebook.com/docs/marketing-api/business-asset-management/guides/pages/
