# Breadcrumb ripartenza — STATE.md è il source-of-truth

**Generato**: `2026-06-21T16:04:09Z` · sessione `4561c97a-f9c0-42cd-99d5-3940e65c8133` · commit auto: cosmetic-skip (only NEXT_SESSION_PROMPT.md dirty, no plan/scope change)

> Questo file NON contiene stato. Lo stato reale (anelli E2E, task corrente,
> prossimi step) è in `STATE.md` — generato da `state/refresh.sh`, unico
> source-of-truth. Non fidarti di status scritto a mano in nessun handoff.

## Come riprendere

1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`  ← **lancia `claude` DA QUI, non da `.claude/`** (vedi nota ambiente)
2. `bash state/refresh.sh <SESSION_ID>`  — ri-deriva lo stato dalla realtà
3. Leggi `STATE.md`: tabella anelli (GENERATA) + task corrente + prossimi step

Se `SESSION_DIRTY.md` esiste in questa cartella, risolvi PRIMA i conflitti.

## ⚠️ NOTA AMBIENTE (bug cwd — S286)
La sessione era partita con cwd = `.../combaretrovamiauto-enterprise/.claude` invece della root.
I PreToolUse hook del progetto (`gate_e.py`, `state_guard.py`) usano path RELATIVI `.harness/…`
→ da `.claude/` non risolvono → exit 2 → **ogni Bash e Write/Edit bloccato**. Workaround usato:
symlink `.claude/.harness → ../.harness` (RIMOSSO a fine sessione). **Fix vero: aprire Claude
Code dalla root del progetto**, non dalla sottocartella `.claude/`.

## ✅ FATTO S286 (regola permanente report)
- Hook `SessionEnd` installato in `~/.claude/settings.json` → script
  `~/.claude/hooks/session_reports_combine.sh`: a fine sessione combina i `REPORT_*.md`/`PROBE_*.md`
  prodotti nella sessione (mtime ≥ birth-time transcript) in `.claude/SESSION_REPORTS_COMBINED.md`
  + apre TextEdit, fail-soft. Testato a vuoto (exit 0, 2 report combinati). Backup settings:
  `~/.claude/settings.json.bak-20260623-211335`.

## Prossimo (S287)
Incorporare il verdetto del giudice esterno (Claude AI) su REPORT_S286 + PROBE_S286_RUN2, poi
build collector pagina-dealer [S4] con le 2 correzioni note (ramo-prezzo `prices.public/dealer.priceRaw`
+ discovery URL dealer). Vedi REPORT_S286.md sez. "Lista minima da costruire in S4".
