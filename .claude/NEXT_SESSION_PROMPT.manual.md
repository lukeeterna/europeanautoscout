# S221 — Fix hook auto-close + wording fisco landing + scraper trasporto

## STATO CHIUSO S220 (context 61%)

### ✅ Risolto: secret leak + commit-disastro auto-close
- **Premessa S220 superata**: non era "un secret blocca commit 3". Un **hook di auto-close** aveva già committato in locale `1a132e3` = 3477 file con **3 secret LIVE** + 140MB `.chrome_profile` + DB.
- **Fix applicato** (tutto locale, branch `s210/audit-master-plan` mai pushato):
  1. `git reset --mixed d635e6d` (disfa auto-close). Backup in branch `backup-pre-s220-reset-1a132e3`.
  2. gitignore v2: `*.bak`, `.claude/*.backup_*`, `tools/scrapers/.chrome_profile/`, `*.db`, `*.sqlite3`.
  3. `rm` 4 `.bak` con command-history leakante.
  4. Scrub token nei doc `.planning/CODE-AUDIT.md` + `SECURITY-AUDIT.md` → `<REDACTED-*>`.
  5. ARGOS_API_KEY → `os.environ` in chaos_db_stress.py/chaos_test.sh + placeholder prompt.
  6. **Commit pulito `e1f8aec`** (278 file, zero junk, zero secret, pre-commit passato).

### 🔴 AZIONE LUKE PENDING — revoca 1 secret
Verifica live fatta su tutti e 3:
- GitHub PAT `ghp_zgws…` → **già MORTO** (401). Nulla da fare.
- Telegram bot `8691360619:AAG…` → **già MORTO** (Unauthorized). Nulla da fare.
- **OpenRouter `sk-or-v1-2f13…` → ANCORA VIVA** → revoca su https://openrouter.ai/settings/keys, rigenera, nuova in `.env`.

## PROSSIMI STEP S221 (in ordine)
1. **Fix hook auto-close** (P1 strutturale) — fa `git add -A` cieco bypassando check secret. Renderlo secret-aware o limitarlo a file in-scope. Probabilmente Stop hook in `~/.claude/settings.json`. Vedi memory `s220_autoclose_hook_secret_leak.md`.
2. **`git branch -D backup-pre-s220-reset-1a132e3`** — DOPO che Luke conferma revoca OpenRouter (il branch contiene il commit-disastro con i secret, solo locale).
3. **Pre-commit hook v2** — il check attuale matcha solo il pattern `api_key` assegnato a stringa. Estendere a prefissi `sk-or-`/`sk-`/`ghp_`/`github_pat_` e token Telegram `\d{8,10}:AA`.
4. **Wording fisco landing** (`landing/index.html` Step03:523, FAQ:588, card:476, fee:597) — dice l'opposto del fisco verificato S219. Riconciliare: "resti TU acquirente e soggetto fiscale; coordino agenzie autorizzate; paghi solo a risultato". MAI "gestisco/assolvo io l'IVA".
5. **S220-2 scraper trasporto** DE→IT (Clicktrans/Macingo) — prima validare quali portali espongono preventivi pubblici scrapeable.

## Day 1 Stile Car — blocker invariati
C-SAN-001 (TinEye manuale Luke /tmp/s217_revtest/ pending), C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001.

## NON toccare
image_sanitizer.py / codice produzione. landing/PDF/messaggi finché materiali non riscritti+rivisti.
