# Diagnosi auto-accept (acceptEdits) — v1

**Data**: 2026-07-18 14:39 · **Repo canonico**: `/Users/macbook/Documents/europeanautoscout`
**Mandato**: DIAGNOSI-AUTOACCEPT v1 + coda igiene R0. Sola lettura config (nessun fix applicato).
**Vincoli rispettati**: zero fetch web · archivio `combaretrovamiauto-enterprise` intoccato ·
`git -C` esplicito su ogni comando.

---

## Esito in una riga

Il flag **acceptEdits si ri-arma a ogni sessione** perché Claude Code **persiste la modalità
permessi interattiva** (toggle Shift+Tab) in `~/.claude.json` → chiave `tengu_quill_harbor`,
valore corrente **`"acceptEdits"`** (riga 695). Nessun file `settings.json` (né globale né di
progetto) definisce `permissions.defaultMode`, quindi **non esiste un override dichiarativo**:
al SessionStart vince il valore runtime persistito. Non è causato da hook (D2 pulito).

---

## R0 — coda igiene `state/rings.json`

**Premessa del mandato NON più valida** (verificata su disco/git):

- `state/rings.json` è **tracciato e identico a HEAD** — `git -C … diff --stat HEAD -- state/rings.json`
  è **vuoto**. Nessuna modifica in working-tree da mettere in stage.
- Il placeholder è **già committato** in `66d143f` ("igiene pubblica: numero test → placeholder +
  rimozione .bak tracciati"), chiuso da `9d7c3f7` ("docs/judge: chiusura igiene pubblica v1").
  Il campo `note` dell'anello 6-7 (riga 72) porta già `TEST_FOUNDER 39<TEST_FOUNDER_NUM>`.
- **Sorgente del campo `note`**: è **testo scritto a mano** dentro `rings.json`, NON generato.
  `state/refresh.py` (unico generatore) riscrive solo `last_status` / `last_run_ts` /
  `last_run_session` e **preserva** `note`. Quindi non c'è sorgente da patchare (nessun fix ≤5 righe).

**Conclusione R0**: niente da stage/commit su `rings.json` (un commit sarebbe vuoto → non creato).
L'unico file nuovo committato da questo mandato è **questo report**.

> Nota fuori-scope (solo segnalazione, R0 autorizza il solo `rings.json`): il pattern placeholder
> compare anche in `state/s244_resume.md` e `state/s246_resume.md`, ma **già come `TEST_FOUNDER_NUM`**
> (placeholder, non numero reale). Nessuna azione richiesta.

---

## D1 — Censimento config (sola lettura)

Grep chiavi: `accept|autoAccept|acceptEdits|permission|defaultMode|bypassPermissions|mode`.

| File | Riga | Chiave / valore | Rilevanza auto-accept |
|------|------|-----------------|------------------------|
| `~/.claude/settings.json` | — | **nessuna** chiave `permissions`/`defaultMode`/`acceptEdits` | — |
| `~/.claude/settings.json` | 58 | `permissionDecision` / `permissionDecisionReason` | ❌ output hook PreToolUse (deny), non è config di modalità |
| `~/.claude/settings.json` | 8 | `"model": "sonnet"` | ❌ modello, non permessi |
| `~/.claude.json` | **695** | **`"tengu_quill_harbor": "acceptEdits"`** | ✅ **modalità permessi persistita (runtime)** |
| `~/.claude.json` | 42-43 | `"default-permission-mode-config": 774`, `"permissions": 774` | ❌ tracker versione-tips (interi), non config reale |
| `<canonico>/.claude/settings.json` | 3-26 | blocco `permissions` (`allow`/`deny`) — **NO `defaultMode`** | ⚠️ definisce allow/deny ma **non** la modalità di default |
| `<canonico>/.claude/settings.local.json` | — | **file assente** | — |

`tengu_quill_harbor` è l'**unica** occorrenza di una stringa-modalità (`acceptEdits`/`bypassPermissions`)
in tutto `~/.claude.json`; non esiste `projects[cwd].permissionMode` né `defaultMode`. È il singolo
"vettore" che trasporta il flag tra le sessioni.

### Confronto storico (D1)

`git -C … show 932796d:docs/backups/pre_S134_setup/settings.json.bak` → il blocco `permissions`
(allow/deny) del backup **pre-S134 è byte-identico** a quello attuale in `<canonico>/.claude/settings.json`.
`defaultMode` **assente in entrambi**. Diff concettuale del blocco permessi: **zero cambiamenti**.
(Le uniche differenze del file sono altrove: aggiunta di `"model"` e degli hook `state_guard.py`/`gate_e.py`;
i permessi non sono mai stati toccati.) → la regressione **non nasce da una modifica del blocco permessi**.

---

## D2 — Hook / harness

Grep ricorsivo su `~/.claude/hooks/`, `<canonico>/.harness/`, `<canonico>/.claude/` per:
`claude … --permission-mode` · `--dangerously-skip-permissions` · scrittura di `settings.json` /
`~/.claude.json` / `tengu_quill_harbor`.

- **Nessun hook lancia `claude`** con `--permission-mode` o `--dangerously-skip-permissions`.
- **Nessun hook riscrive** `settings.json` o `~/.claude.json` a runtime. Gli unici match sono:
  - commenti/docstring che *citano* `settings.json` (auto_code_review, pre-tool-safety, ecc.);
  - `diag_session_start.sh:44` fa `json.load(...settings.json)` → **sola lettura**;
  - `.claude/skills/skill-browser-chrome/skill.md` → *documentazione* su come editare `~/.claude.json`
    a mano per Playwright (non eseguibile, non un hook).
- `global_session_end.sh` (auto-close): fa commit/push git, **non** rilancia `claude` né tocca i permessi.

**D2 = pulito**: il ri-arm non è prodotto dagli hook.

---

## D3 — Doc locale CLI (nessun web)

`claude --help`:
- `--permission-mode <mode>` — choices: **`acceptEdits`**, `auto`, `bypassPermissions`, `default`,
  `dontAsk`, `plan`. → `acceptEdits` è una modalità valida, coerente col valore persistito.
- `--dangerously-skip-permissions` / `--allow-dangerously-skip-permissions` esistono ma **non usati**
  da nessun hook (vedi D2).
- La modalità è governata da `permissions.defaultMode` in `settings.json` **quando presente**; qui è assente.

---

## D4 — Causa più probabile, fix proposto, rischi

### Causa più probabile
Claude Code **serializza la modalità permessi interattiva** (Shift+Tab) nella cache di stato globale
`~/.claude.json` sotto `tengu_quill_harbor`. Attualmente vale `"acceptEdits"`. A ogni nuova sessione
CC **ripristina** quel valore. Poiché **nessun `settings.json` impone `defaultMode`**, non c'è nulla
che riporti la sessione a `default`: il valore persistito "ri-arma" acceptEdits. Confermato che la
regressione **non** viene da hook (D2) né da una modifica del blocco permessi (D1 storico = identico).

### Fix proposto (UNA riga — NON applicato, in attesa di Luke)
**Primario (dichiarativo, durevole, in-repo)** — aggiungere dentro l'oggetto `permissions` di
`<canonico>/.claude/settings.json`:

```json
"defaultMode": "default"
```

Forza `default` a ogni SessionStart, indipendentemente dal toggle persistito.

**Precedenza da verificare** `[non-verificato-senza-doc-upstream]`: se `defaultMode` in settings.json
NON dovesse avere precedenza sul valore runtime persistito, il fix deterministico one-shot è riportare
in `~/.claude.json` la chiave `tengu_quill_harbor` da `"acceptEdits"` a `"default"`. Sconsigliato come
fix **durevole** perché si ri-scrive appena Luke ri-preme Shift+Tab; utile solo come reset immediato.
Raccomandazione: applicare il primario (`defaultMode`) e, se al test successivo la sessione parte ancora
in acceptEdits, aggiungere il reset della chiave persistita.

### Rischi
- `defaultMode: "default"` → ogni sessione riparte chiedendo conferma sugli edit: se qualche flusso
  autonomo (auto-close, `/loop`) contava sull'acceptEdits implicito, cambia UX. Ma è esattamente il
  comportamento richiesto (stop al ri-arm non voluto).
- Editare `~/.claude.json` a mano è più rischioso: file runtime grande, CC può riscriverlo alla chiusura
  → preferire la via `settings.json`.

### Cosa NON è stato toccato
- Nessuna config modificata (D1-D4 sola lettura); il fix lo autorizza Luke dopo verdetto.
- `state/rings.json` non ri-committato (già pulito a HEAD).
- Archivio `combaretrovamiauto-enterprise`: intoccato.
- Zero fetch web. `git -C` esplicito su ogni comando.
