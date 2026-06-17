# PIANO git filter-repo — bonifica secret in history (S278, da eseguire LUKE)

> Obiettivo C3: rimuovere i secret dalla history e **sbloccare il push** dei 26 commit locali
> S223→S277 (branch `s210/audit-master-plan`, ahead 26 su origin).

## ⚠️ FINDING CRITICO (cambia la natura del lavoro)
I secret **sono GIÀ su GitHub**, non solo in locale:
- `origin/master` contiene `3e97b6a` con `sk-or-v1...` (OpenRouter).
- `origin/s210/audit-master-plan` contiene `82a5881` + `3e97b6a` (sk-or, ghp_, token Telegram).
- Repo: `https://github.com/lukeeterna/europeanautoscout`.

Conseguenza: **i 3 secret vanno trattati come COMPROMESSI** (chiunque abbia clonato/visto il repo
li ha). La rotazione **non è opzionale né "già fatta basta"**: è il primo passo, prima di tutto.
Scrubbare la history senza ruotare = sicurezza solo apparente.

## Secret in history (3 tipi, file noti)
| Secret | Stato dichiarato | Azione |
|--------|------------------|--------|
| OpenRouter `sk-or-v1-...` | "ruotato S221" — **ri-verificare** | conferma su openrouter.ai/keys che la key in history è REVOCATA; se no, revoca ora |
| Telegram bot token (`deploy.sh`, commit `dfa2ff9`) | memoria S220 "morto", MA STATE.md §6 dice **bot tg vivo** → AMBIGUO | **verifica**: se il token in history == `ARGOS_TELEGRAM_TOKEN` attuale (iMac `current/wa-intelligence/.env`), allora è LIVE → `/revoke` via @BotFather + aggiorna .env iMac |
| GitHub PAT `ghp_...` / `github_pat_...` | "morto" | conferma revocato su github.com/settings/tokens; se no, revoca |

File che contengono secret in history (da `git log -S`): `.claude/NEXT_SESSION_PROMPT.manual.md`,
`.planning/SECURITY-AUDIT.md`, `configs/CLAUDE.md`, `deploy.sh`. `git filter-repo --replace-text`
scansiona **tutti** i blob, quindi non serve enumerarli — questa lista serve solo per la VERIFICA finale.

---

## STEP 0 — Rotazione (PRIMA di toccare la history)
1. Revoca/ruota i 3 secret come da tabella (OpenRouter, Telegram bot, GitHub PAT).
2. Aggiorna i posti vivi: `ARGOS_TELEGRAM_TOKEN` su iMac `current/wa-intelligence/.env`,
   eventuale OpenRouter key nel cascade LLM, nuovo PAT/credenziale per il push.
3. Verifica daemon tg ancora vivo dopo rotazione: `ssh imac "curl -s localhost:9191/status"` + `/help` al bot.

## STEP 1 — Backup (Rule 1d)
```
cd ~/Documents
cp -R combaretrovamiauto-enterprise combaretrovamiauto-enterprise.PRE-FILTER-REPO-$(date +%Y%m%d)
# verifica: ls -ld combaretrovamiauto-enterprise.PRE-FILTER-REPO-*  (size>0, mtime ora)
```

## STEP 2 — Clone fresco (filter-repo lo richiede)
```
cd /tmp
git clone ~/Documents/combaretrovamiauto-enterprise argos-scrub
cd argos-scrub
git remote -v   # deve puntare al locale; lo ri-aggancio a GitHub allo STEP 6
```

## STEP 3 — File espressioni di sostituzione
Crea `/tmp/argos-scrub/replace.txt` con i valori LETTERALI dei secret (uno per riga).
Formato `git filter-repo`: `<valore-vecchio>==>***REMOVED***`. Una riga per ciascuno dei 3 secret:
```
<VALORE_COMPLETO_OPENROUTER>==>***REMOVED***
<VALORE_COMPLETO_GITHUB_PAT>==>***REMOVED***
<VALORE_COMPLETO_TOKEN_TELEGRAM>==>***REMOVED***
```
> Estrai i valori esatti da: `git -C /tmp/argos-scrub show dfa2ff9:deploy.sh | grep -i token`
> e `git grep` sui file noti. NON committare `replace.txt`.

## STEP 4 — Rewrite history (tutti i ref)
`git-filter-repo` è installato (`~/Library/Python/3.13/bin/git-filter-repo`).
```
cd /tmp/argos-scrub
git filter-repo --replace-text replace.txt --force
```

## STEP 5 — Verifica scrub (done-condition esterna)
```
# deve restituire VUOTO per ognuno:
git log --all -S 'sk-or-v1'        --oneline
git log --all -S 'ghp_'            --oneline
git log --all -S 'github_pat_'     --oneline
git log --all -p -- deploy.sh | grep -i 'AAH'   # token Telegram
```
Fatto terminale = tutti e 4 vuoti. Se non vuoti → la `replace.txt` non copriva un valore.

## STEP 6 — Re-push forzato (riscrive anche il remoto già contaminato)
```
git remote add origin https://github.com/lukeeterna/europeanautoscout
git push origin --force --all
git push origin --force --tags
```
> ⚠️ Force-push riscrive `master` e `s210/...` su GitHub. Vincolo CC: force-push autorizzato QUI
> perché è esattamente lo scopo (purgare i commit con secret), deciso da Luke.

## STEP 7 — Propagazione locale
Il repo `~/Documents/combaretrovamiauto-enterprise` ha ancora la history vecchia. O:
- ri-clona pulito da GitHub dopo il push, **oppure**
- riallinea: `git fetch origin && git reset --hard origin/s210/audit-master-plan` (DOPO backup STEP 1).
- **OBBLIGATORIO dopo ogni clone**: `git config core.hooksPath .githooks` (riattiva pre-commit + pre-push
  tracciati; la config non si clona — senza, gli hook secret non girano).

## STEP 8 — Igiene residua
- GitHub mantiene in cache i commit vecchi per un po': se il repo è/era pubblico, apri ticket
  GitHub Support per purgare le viste cached + invalidare eventuali fork.
- Verifica `.gitignore` copra già `*.bak`, `.chrome_profile/`, `*.db`, `*.sqlite3` (fix S220) così
  non rientra junk al prossimo commit.

## Esito atteso
History pulita (locale + remoto), 3 secret ruotati, push dei 26 commit S223→S277 sbloccato.
