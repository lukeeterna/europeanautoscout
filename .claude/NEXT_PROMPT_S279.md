> SUPERSEDED da docs/ROADMAP.md — vedi STATE.md regola di precedenza.

# PROMPT RIPARTENZA — S279

## ⚠️ CORREZIONE URGENZA SECRET (precede tutto — fatto verificato S278)
Rotazione e scrub-history sono DUE cose diverse, NON bundlarle:
- **Rotazione 3 token = azione Luke, disaccoppiata dal filter-repo/unlock.** NON è lo STEP 0 di
  un piano gated sul push.
- **Repo VERIFICATO PRIVATE** (`gh repo view lukeeterna/europeanautoscout` → `isPrivate:true`, S278).
  Quindi NON è l'emergenza "scanner pubblici in minuti" (quella premessa assumeva repo pubblico, falsa).
  Esposizione reale su privato: collaboratori, cloni/fork già fatti, e il caso "se diventa pubblico".
  → Importante e presto, NON panico. Stato onesto: **secret in history di repo PRIVATO = da ruotare,
    rischio contenuto ma reale.**
- Dei 3, **2 erano già dati per morti** (OpenRouter ruotato S221; GitHub PAT morto). Il vivo ambiguo
  è il **bot Telegram** (STATE.md §6 dice il bot vivo). Quindi la rotazione concreta = (a) CONFERMARE
  morti i 2, (b) RUOTARE Telegram via @BotFather se il token in history == quello attuale su iMac.
  Ordine se vivi: GitHub PAT `ghp_zgws…` > OpenRouter `sk-or-v1-…2f13` > bot @Argosautomotivebot.
  NON pastare i secret interi da nessuna parte — i parziali bastano per identificarli.
- **Scrub (filter-repo) = SEPARATO, quando comodo.** NON sostituisce la rotazione (fork/cache/cloni
  conservano i vecchi). Serve solo a non ri-committarli + sbloccare il push. Push resta bloccato dal
  pre-push finché scrub fatto, ma il push bloccato NON è il rischio.

## Esegui IN ORDINE
[1] RELAUNCH unlocked — PRIORITA' 0 (correttezza, richiede unlock, Gate-E `overwrite_sot`):
    `ARGOS_HARNESS_UNLOCK=1 claude`
    a) backup Rule 1d di MEMORY.md → aggiorna riga-indice 11 (riga pronta in `.claude/REPORT_S277.md`).
    b) aggiorna STATE.md (commit ee0694f firma Azzurra + 6a01884 enforcement secret + c0f6ed1 report).

[2] COPY DAY-1 (C1): OK Luke sui 3 nodi in `.claude/COPY_DAY1_S278_PROPOSAL.md`
    (provenienza dichiarata, archetipo, condizioni wiring). NON wirare prima dell'OK.

[3] FILTER-REPO (quando Luke vuole sbloccare il push) — `.claude/PLAN_FILTER_REPO_S278.md`.
    Disaccoppiato dalla rotazione (che è già fatta sopra, indipendente).

[4] Verso E2E: anelli 6-7 (gate HITL iMac + invio PDF a TEST_FOUNDER 39<TEST_FOUNDER_NUM>).
    Prima azione che innesca Gate-E classe `outreach_real`.

## Stato E2E (INVARIATO — S278 = control-plane + sicurezza)
2/9A/5 VERIFIED(smoke) · 1/9B/6-7 UNVERIFIED · 8 BLOCKED(esterno).

## Enforcement secret attivo (S278)
`.githooks/` tracciati (pre-commit + pre-push) via `core.hooksPath=.githooks`. pre-push blocca push
con commit-secret. Dopo OGNI clone: `git config core.hooksPath .githooks`. MAI `--no-verify`/`git add -A`.

## Gate tecnici a invio dealer REALE (nessuno legale: WA cold = DECISO-FINALE, rischio accettato non inesistente)
(1) E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto"; (2) trasparenza in PRODUZIONE (Azzurra→sync.sh);
(3) base-mercato fidata (DEEP_PAGES≥80 + geo==IT + experiment-OFF).
