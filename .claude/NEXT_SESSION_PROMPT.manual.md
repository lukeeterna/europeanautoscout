# S249 — ARGOS · resume

SessionStart: lascia partire `bash state/refresh.sh S249`. Se il fix NON e' ancora
landato verra' bloccato da Gate E come FP `disable_hook-dca8f6243f` — NON ritentare,
vai al land qui sotto. Poi leggi `STATE.md`. NON riscrivere handoff.

## Stato lasciato da S248 (Gate E refinement — work-item #1, verify-DONE / land-PENDING)

**Fatto + validato (verify):** `.harness/gate_e.py.new` (staging, NON landato) =
refinement completo, **`selftest PASS 19/19`** (ri-eseguibile: `python3 .harness/gate_e.py.new selftest`).
Cosa cambia vs `gate_e.py` attuale:
1. **FP fix (causa #1)**: disable_hook/overwrite_sot scattano SOLO sugli OPERANDI reali di
   un'op lossy (target di `>`/`>>` su file; arg di mv/cp/rm/sed -i/tee/truncate/chmod col verbo
   in posizione di comando), MAI su testo incidentale → niente piu' FP su `bash refresh.sh ... 2>&1`
   (ha bloccato l'avvio S248), su nome-script eseguito, su body di `git commit -m "..."`
   (ha bloccato 2x il commit S247). Impl: `lossy_operands()` + riuso `classify_write_edit`.
2. **SoT-DB ristretto**: non piu' "qualunque .db sotto ROOT" (beccava DB-spazzatura profilo
   Chrome, argos.db, nhtsa_wmi) → `SOT_DB_REALPATHS` = {dealer_network.sqlite,
   comm-broker/bridge.sqlite, src/cove/data/cove_tracker.duckdb}.
3. **Escape manutenzione**: `ARGOS_HARNESS_UNLOCK=1` → allow in `run_hook` (come state_guard.gate_c).
   NB bootstrap: il gate_e ATTUALE (vecchio) NON onora l'env → il PRIMO land NON puo' usarlo.

**Da LANDARE (gated — e' il punto giusto):** sovrascrivere `gate_e.py` con lo staging.
Comando: `cp .harness/gate_e.py.new .harness/gate_e.py`.
Il gate_e ATTUALE lo blocca con slug **`disable_hook-d312c497fe`** (gia' calcolato).
Sequenza:
  1. CC (S249) attempt `cp .harness/gate_e.py.new .harness/gate_e.py` → BLOCK + packet.
  2. Luke incolla verdetto esterno (Claude AI) nel packet + `! python3 .harness/gate_e.py approve disable_hook-d312c497fe --verdict "..."`.
  3. CC ritenta lo STESSO cp UNA volta → token consumato → land.
  4. Subito dopo: `python3 .harness/gate_e.py selftest` (atteso 19/19) + verifica live
     (`bash state/refresh.sh S249` ora deve passare) + `rm .harness/gate_e.py.new`. Poi commit+push.

**Verdetto esterno richiesto (vincolo #4 — modifica strutturale a un guardrail):** prima del land
serve l'OK di Claude AI sul diff. Far validare: (a) l'operand-matching e' difesa sufficiente per il
threat-model "sbadataggine CC" (Rule 1d: euristica best-effort OK)? (b) il restringimento SoT-DB
introduce un falso-NEGATIVO accettabile? (c) l'escape unlock coerente con state_guard. Residuo noto
onesto: un `git commit` con HEREDOC che contenga LETTERALMENTE `> STATE.md` nel body resta FP teorico
(raro, accettato).

**NON ancora fatto (budget S248 esaurito):**
- `gate_e.py` in `PROTECTED_FILES` di `state_guard.py` (defense-in-depth secondario: gate_e gia' si
  auto-protegge via disable_hook). Editare state_guard.py e' doppio-gated.

## Prossimi step (STATE.md sez.3, DOPO il land)
- **#2 COVERAGE-CHECK** (production-blocking classe `outreach_real`): confermare che Gate E intercetti
  il path-tool REALE con cui AMBRA invia (se MCP/Python bypassa il matcher-shell → breaker decorativo
  → flip a REJECT). Non urgente (autonomia gia' gated da regola >=10 CLOSED_WON).
- **#3 6-7 E2E**: gate HITL iMac (fastapi) + invio PDF su TEST_FOUNDER 393314928901 (mai dealer reale).
  Prima azione che innesca Gate E classe `outreach_real`. Fare DOPO #2.

## Note
- Packet FP avvio S248: `.harness/pending_review/disable_hook-dca8f6243f.md` (refresh.sh `2>&1`).
  NON approvarlo — e' l'FP che il fix elimina. Dopo il land si puo' rimuovere il packet.
- S248 chiusa al ~62-65% durante validazione. Tutto il lavoro e' in staging + questo handoff.
