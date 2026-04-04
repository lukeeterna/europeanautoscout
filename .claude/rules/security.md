# ARGOS — Security Gates

## Credenziali — ZERO DEROGA
- MAI credenziali hardcoded → solo .env
- MAI chiavi API in chat/commit
- .env NON su GitHub (.gitignore)
- chmod 600 su .env e *.sqlite

## API Security
- Porta 9191 (WA daemon): DEVE avere API key auth (X-API-Key header)
- Input validation su /send: telefono italiano valido, messaggio <4096 char
- Dashboard :8080: password NON default, rate limit login

## Deploy
- rsync atomico con symlink swap (MAI scp singoli file)
- Healthcheck post-deploy obbligatorio
- Rollback in 1 secondo (symlink a release precedente)

## Database
- Backup ogni 6h con `sqlite3 .backup` (MAI `cp` su SQLite)
- MAI cancellare -wal/-shm con processi aperti
- PRAGMA integrity_check ogni 5 min via monitoring
- WAL mode + busy_timeout=10000 su ENTRAMBI Node e Python

## LLM
- Cascade 5 livelli: Gemini → Groq → OpenRouter free → Gemini Lite → Ollama locale
- Circuit breaker per provider (3 fail in 5 min → skip)
- MAI template fallback senza alert Telegram
- Prompt injection defense: sanitizzare input dealer, validare output LLM
- Minimizzare PII nelle chiamate LLM (no telefoni, solo nome + citta')

## Monitoring
- Ogni 5 min: WA connected, DB integrity, LLM health
- Se fallisce → Telegram alert immediato
- Heartbeat iMac ogni 30 min

## Guardrails business
- ZERO COSTI — tutto gratuito o gia' pagato
- Test E2E DEVE passare prima di ogni outreach dealer
- Nessun deploy senza healthcheck
