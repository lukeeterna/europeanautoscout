# HANDOFF — S297 (chiusura bypass git add -A) — 2026-07-07 UTC
> Render dello stato su disco. Autorità = git/disco, NON questo testo. Rigenerabile con chiudi-ordinatamente.

### SESSIONE
- Tipo: FIX-HARNESS (1 edit su hook GLOBALE `~/.claude/hooks/global_session_end.sh`, fuori repo)
- Mandato: (A) chiudere bypass `git add -A` auto-close hook con lettura S286 2b · (B) riconciliare riga stale gate base-mercato in STATE.md §3 via generatore
- Esito: **A VERDE** · **B NON iniziata** (context 60%, deferita a prossima sessione per decisione Luke)

### VERITÀ GIT
- branch s210/audit-master-plan · HEAD `5c74cfa` (auto-close di prova UNITÀ A) · working-tree: solo `.claude/NEXT_SESSION_PROMPT.md` rigenerato
- L'hook modificato vive in `~/.claude/` (vincolo #12, fuori dal repo ARGOS): NON versionato qui, persiste su disco. Backup 1d: `~/.claude/hooks/global_session_end.sh.bak-S297-20260707T203657Z`

### UNITÀ A — FATTA (verde)
- S286 2b trovata VERBATIM = blocco-commento DENTRO l'hook (`:72-78`), non un report. Intento reale = de-stage del solo prompt; `git add -A` "resta" per minimal-change, NON come scelta pro-mass-add. Regola founder scritta (S278/S286): "mai git add -A, solo file nominati". → ramo 1 (auto-commit artefatti di stato). Il handoff S296 riga 37 ("decisione esplicita git add -A resta") era FALSO — disco lo smentisce.
- Fix: `git add -A` → whitelist NOMINATA (`STATE.md state/rings.json HANDOFF_CURRENT.md .claude/NEXT_SESSION_PROMPT.md`) **condizionata a `[ -f STATE.md ]`** (risolve vincolo #12: FLUXION/Guardian mantengono `git add -A` generico — era il blocco che aveva deferito S296).
- Prova: commit `5c74cfa` committa solo whitelist; file-esca `ESCA_S297_bypass_test.txt` rimasto UNTRACKED, NON committato. Bypass chiuso.

### PROSSIMO PASSO — UNITÀ B (singolo, falsificabile)
Riconciliare la riga stale del gate base-mercato in STATE.md §3 **VIA GENERATORE, mai a mano**:
1. STATE.md §3 (righe ~20-32) dice ancora "base-mercato NON chiuso (cap-truncated)" = finding S273 **SUPERSEDED**. Gate [3]/[D] è CHIUSO S295-C (330i attraverso `validate_band` su fixture 323, commit `ebe422e`/`d586f03`).
2. Aggiornare la DEFINIZIONE del gate in `state/rings.json` (check_cmd: es. fixture s273cont4 esiste + `gate_it_band` emette verdict) così che `state/refresh.py` (o `refresh.sh`) rigeneri lo stato corretto.
3. Done-B: output di `state/refresh.py` + la riga rigenerata di STATE.md §3 incollate.
- VIETATO editare STATE.md direttamente (blocco GENERATED · Rule 1b · serve `ARGOS_HARNESS_UNLOCK=1` per guard/generatori).
- Verificare prima: commit `ebe422e`/`d586f03` esistono e `validate_band`/fixture 323 sono sul disco (le ref S295-C vengono dal mandato, non ancora verificate contro git in questa sessione).

### BLOCKED-ON (invariati, fatti esterni)
- E2E TEST_FOUNDER (anelli 1/6-7/9B) — Luke fisico su WA/HITL.
- Anello 8 (sign_url firmato dal dealer reale) — freeze fisico.
- Parità gate/runtime `/send` `approved_ts` (STATE.md §3 item 2) — gated su autonomia-invio.

### CATENA DI AUTORITÀ
codice/git > STATE.md > docs/ROADMAP.md > docs/briefs/ > REPORT/handoff (SUPERSEDED)
