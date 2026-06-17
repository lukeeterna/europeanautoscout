# ARGOS — Security Gates

## Credenziali — ZERO DEROGA
- MAI credenziali hardcoded → solo .env
- MAI chiavi API in chat/commit
- .env NON su GitHub (.gitignore)
- chmod 600 su .env e *.sqlite

## REGOLA SECRET (S278) — la sicurezza dei secret è di Claude, non di Luke
> Luke NON deve ruotare token ogni sessione. Se succede, è un bug del meccanismo, non sua responsabilità.

1. **Chi committa/pusha possiede il rischio**: prima di OGNI commit e di OGNI push lo eseguo io →
   è MIA la responsabilità che nessun secret entri nella history.
2. **Enforcement tracciato e portabile** (non parole): hook in **`.githooks/`** (versionati), attivati
   con `git config core.hooksPath .githooks`. Due livelli con la stessa `TOKEN_PATTERN`:
   - `pre-commit` → blocca un secret in un commit NUOVO.
   - `pre-push` → blocca il push se UN QUALSIASI commit in arrivo contiene un secret (chiude il buco
     S49-S51/S220: la history vecchia passava su origin perché nulla scansionava al push).
3. **MAI bypassare**: vietato `--no-verify`, vietato `git add -A` su commit massivi (solo file nominati).
4. **Dopo ogni clone** (incl. il clone fresco del filter-repo): ri-eseguire `git config core.hooksPath .githooks`
   — la config non si clona. È l'unico passo manuale; senza, gli hook tracciati non si attivano.
5. **La rotazione ricorrente NON è prevenzione**: si rotea/scrubba UNA-TANTUM (filter-repo + revoca dei 3
   token: OpenRouter (key `sk-or-v1-…` che termina con 2f13), GitHub PAT (`ghp_zgws…`), bot Telegram @Argosautomotivebot). Poi basta.

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
