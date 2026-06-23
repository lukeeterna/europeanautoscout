# HANDOFF — sessione harness (NON è un mandato; lo stato reale è STATE.md)

**SESSION_ID**: `f428709b-b03f-4c6e-bba5-aa299d0b4ff8`
**HEAD all'apertura**: `195d59e` (auto-close, sopra `b4c5ed6` = S288 reale)
**Branch**: `s210/audit-master-plan` · no push
**Chiusura**: context 63% → vincolo #7 (chiusura ordinata, no nuovo lavoro)

## Done-condition (output grezzo)
```
$ bash -n global_session_end.sh   → SYNTAX OK
$ grep -n 2b global_session_end.sh → :72 commento, :78 git reset -q -- "$PROMPT_FILE"
```

## VERDETTO PARTE A
- **PROPOSTA 1** (handoff 1-file, no dump storico): **CONFERMATO**. Causa dump = `session_reports_combine.sh:36-44` (glob REPORT_*/PROBE_* per mtime + concat :58-65).
- **2a-ARGOS**: **GIÀ A POSTO**. File già breadcrumb declassato; `session_start_wrapper.sh` NON inietta NEXT_SESSION_PROMPT.md; zero reader-mandato (context_gate solo whitelist-Write, post_compact solo suggerisce, gate_e solo commento).
- **2b**: **CONFERMO obiettivo, CORREGGO impl**. Allowlist esplicita B.3 viola il paletto "MAI cosa viene committato" (droppa WIP a nome non previsto). Impl corretta: `git add -A` resta + `git reset` chirurgico del solo prompt.

## FATTO QUESTA SESSIONE
1. **2b IMPLEMENTATO** in `~/.claude/hooks/global_session_end.sh:72-78`. Backup `global_session_end.sh.bak-2b-20260623T213453Z` (NON committato). Sintassi valida. **NON ancora runtime-proven** (done-condition 6-step richiede budget assente).
2. **2a**: nessun codice (già a posto, evidenza sopra).
3. **PROPOSTA 1**: **DEFERRED** (vedi sotto). Backup combine già fatto: `session_reports_combine.sh.bak-P1-20260623T213453Z`.

## PROSSIMA SESSIONE (budget fresco, da root)
### A. Provare 2b (done-condition mandato, step 4)
Simula 2 Stop con STATE.md/rings dirty → `git log --oneline -3` + `git show --stat` ultimo auto-commit:
attesi STATE.md/rings.json NEL commit (persistiti), NEXT_SESSION_PROMPT.md NON nel commit.
NB: la chiusura DI QUESTA sessione è già il 1° run reale del nuovo codice → verifica `git show --stat HEAD` cercando NEXT_SESSION_PROMPT.md assente.

### B. Costruire PROPOSTA 1 (`session_reports_combine.sh`) — DECISIONE APERTA prima di build
Riscrivere l'output: invece di concatenare REPORT_*.md, scrivere `HANDOFF_<SESSION_ID>.md` (estrai `.session_id` da INPUT JSON; SessionEnd lo espone) con header fisso SESSION_ID+HEAD+git-status+done-condition. Stop dump storico.
**INTERAZIONE DA RISOLVERE (perché DEFERRED, non rushato)**: con 2b attivo, `git add -A` committa OGNI file non-prompt → ogni `HANDOFF_<uuid>.md` verrebbe committato → proliferazione 1 file/sessione (lo stesso problema-pattern che PROPOSTA 1 vuole chiudere). Decidere PRIMA del build: (i) gitignore `HANDOFF_*.md` + `NEXT_SESSION_PROMPT.md`, o (ii) escluderli anche dallo staging come il prompt, o (iii) un solo `HANDOFF_CURRENT.md` sovrascritto. Non costruire finché non scelto.

## RISCHIO chiusura
2b gira alla chiusura di QUESTA sessione (hook .sh letto a runtime, non a SessionStart). `set -u` no `-e` → non fallisce la sessione. Sintassi validata. Se l'auto-close fallisse, backup `*.bak-2b-*` ripristina in 1 cp.
