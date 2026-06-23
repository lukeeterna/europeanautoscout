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

## CHIUSURA HARNESS (sessione successiva, post-compact) — 2b PROVATO + P1 COSTRUITO
- **2b VERDE (runtime-proven)**: commit `a0938d9` (1° auto-close POST-edit 2b, 21:44:51Z > edit 21:34:53Z) contiene SOLO `STATE.md`+`state/rings.json`; `NEXT_SESSION_PROMPT.md` ASSENTE (grep -c 0) e resta dirty by-design. Confronto col PRE-2b `195d59e` che lo committava. Nessun rollback.
- **PROPOSTA 1 COSTRUITA** in `~/.claude/hooks/session_reports_combine.sh` (riscritto): emette `.claude/HANDOFF_<SESSION_ID>.md` (header fisso SESSION_ID+branch+HEAD+git-status+done-condition; report di sessione ELENCATI non concatenati → stop dump storico). `.session_id` da INPUT JSON. Runtime-proven (809 byte, 4 report listati). Backup `session_reports_combine.sh.bak-P1build-20260623T214920Z`.
- **Anti-proliferazione applicata** in `global_session_end.sh`: trigger esclude `HANDOFF_.*\.md$` (:60) + reset glob `git reset -- .claude/HANDOFF_*.md` (:83). De-stage runtime-proven (staged→reset→vuoto). HANDOFF resta su disco, MAI auto-committato; commit manuale se serve. Backup `global_session_end.sh.bak-P1build-20260623T214920Z`.
- Entrambi `bash -n` OK. Hook in `~/.claude/` (fuori repo): vivono su disco+backup.

## PROSSIMA SESSIONE (budget fresco, da root)
### A. Provare 2b (done-condition mandato, step 4)
Simula 2 Stop con STATE.md/rings dirty → `git log --oneline -3` + `git show --stat` ultimo auto-commit:
attesi STATE.md/rings.json NEL commit (persistiti), NEXT_SESSION_PROMPT.md NON nel commit.
NB: la chiusura DI QUESTA sessione è già il 1° run reale del nuovo codice → verifica `git show --stat HEAD` cercando NEXT_SESSION_PROMPT.md assente.

### B. Costruire PROPOSTA 1 (`session_reports_combine.sh`) — DECISIONE APERTA prima di build
Riscrivere l'output: invece di concatenare REPORT_*.md, scrivere `HANDOFF_<SESSION_ID>.md` (estrai `.session_id` da INPUT JSON; SessionEnd lo espone) con header fisso SESSION_ID+HEAD+git-status+done-condition. Stop dump storico.
**INTERAZIONE DA RISOLVERE (perché DEFERRED, non rushato)**: con 2b attivo, `git add -A` committa OGNI file non-prompt → ogni `HANDOFF_<uuid>.md` verrebbe committato → proliferazione 1 file/sessione (lo stesso problema-pattern che PROPOSTA 1 vuole chiudere).
**RACCOMANDAZIONE (singola)**: estendere il `git reset` di 2b per de-stagiare anche `.claude/HANDOFF_*.md`, stesso meccanismo del prompt. È già il pattern provato per "artefatto di sessione generato che non va committato": un solo concetto, zero codice nuovo, mantiene il file taggato `HANDOFF_<SESSION_ID>.md` su disco (commit manuale se il founder ne vuole tenere uno). Scartate perché perdono dati: gitignore toglie il file da `git status` e blocca il commit intenzionale; `HANDOFF_CURRENT.md` sovrascritto butta storia per-sessione + naming SESSION_ID (CC-ADD).

## RISCHIO chiusura
2b gira alla chiusura di QUESTA sessione (hook .sh letto a runtime, non a SessionStart). `set -u` no `-e` → non fallisce la sessione. Sintassi validata. Se l'auto-close fallisse, backup `*.bak-2b-*` ripristina in 1 cp.
