# S205 — Codice-first recovery: chiudere i 4 gap per Day 1 Stile Car

> Generato 2026-05-28 18:00. Sessione S204 ha eseguito audit codice-first (NON doc).
> Risultato: 5 fatti verificati, 5 gap reali. Vedi memory `s204_verita_codice_audit_2026-05-28.md`.
> Deadline Day 1 Stile Car: **2026-06-03 (T-6gg)**.

## REGOLA #0 sessione

**Ignorare PLAN.md, HANDOFF-*, .planning/, ROADMAP, DECISIONS storiche.**
Fonte di verità = codice + DB reali + comandi eseguiti. Se un doc contraddice il codice, vince il codice.

## STEP 0 — Verifica fattuale pre-flight (15min)

```bash
# CoVe smoke (deve restituire PROCEED 0.77+)
python3 -c "
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'src/cove')
from cove_engine_v4 import CoVeEngine, Listing
from datetime import datetime
r = CoVeEngine().analyze(Listing('SMK','BMW','Serie 3',2021,45000,24500,None,'autoscout24',datetime.now().isoformat()))
print(r.recommendation, r.confidence)
"

# AMBRA classifier (5/5 PASS)
python3 tools/test_ambra_5scenarios.py | tail -10

# iMac PM2 + wa-daemon status
ssh imac "~/.npm-global/bin/pm2 list; curl -s localhost:9191/status"
```

Se uno dei tre fallisce → STOP, recovery del componente prima di proseguire.

## STEP 1 — Gap #2: verificare TEST_FOUNDER contract end-to-end (30min)

Ultimo INBOUND `39<TEST_FOUNDER_NUM>` 2026-05-16: "Va bene, mi mandi il contratto".
Domanda: la pipeline reactive CONTRACT_REQUEST ha creato il contract su D1? Mark-paid eseguito?

```bash
# Query D1 argos-contracts via wrangler (cwd argos-proxy/)
cd argos-proxy && wrangler d1 execute argos-contracts --remote \
  --command "SELECT id, status, dealer_phone, created_at, signed_at, paid_at FROM contracts WHERE dealer_phone='+39<TEST_FOUNDER_NUM>' ORDER BY created_at DESC LIMIT 5"

# Query iMac dossiers/messages per token
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  \"SELECT body FROM messages WHERE phone_number='39<TEST_FOUNDER_NUM>@c.us' AND direction='OUTBOUND' AND body LIKE '%contract%' ORDER BY timestamp_iso DESC LIMIT 3;\""
```

**PASS criteria**: sappiamo se quel "Va bene" ha prodotto un contract reale o se è caduto. Se caduto → identificare callsite mancante (probabile gap classifier o handler).

## STEP 2 — Gap #4: tabella `dealers` mancante su iMac DB (15min)

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite '.tables'"
# Conferma: nessuna tabella `dealers`.

# Cerca dove batch_runner legge la lista dealer:
grep -rn "FROM dealers\|SELECT.*dealers\|dealer_network" tools/ src/ wa-intelligence/ --include="*.py" | grep -v __pycache__ | head -20
```

**PASS criteria**: identificare quale DB / file / tabella alimenta davvero l'outreach. Se è il `dealer_network.sqlite` locale (MacBook 204KB), spiegare a Luke: l'outreach va lanciato da MacBook, non da iMac.

## STEP 3 — Gap #1: sanitizer UAT rivalidazione (30-45min)

Smoke 5 sample reali T7 con sanitizer attuale, confronto visivo Luke:

```bash
# Pick 5 listing recenti da AutoScout / mobile.de via on_demand_runner --modello "Serie 3"
# Genera PDF dossier, apri sanitized images
python3 tools/on_demand_runner.py --marca BMW --modello "Serie 3" --budget 35000 --dealer "S205_UAT"
ls -la dossiers/safe_images/ | tail -10
```

**PASS criteria**: 5/5 sample senza over-mask visibile. Se ≥1 over-mask → BACKLOG #S205-SANIT, NON committare Day 1 finché risolto.

## STEP 4 — Gap #3: micro-patch NEGATIVE → opt_out=1 (15min)

```bash
grep -n "NEGATIVE\|opt_out" wa-intelligence/response-analyzer.py | head -20
# Localizza handler NEGATIVE, aggiunge UPDATE conversations SET opt_out=1 prima/dopo CLOSED_NO.
# Re-run python3 tools/test_ambra_5scenarios.py — scenario 4 deve mostrare opt_out=1.
```

## STEP 5 — Decisione Luke (Day 1 reale vs replay TEST_FOUNDER)

Riportare a Luke i risultati Step 1-4. Luke decide:
- (A) replay completo TEST_FOUNDER end-to-end con micro-patch applicate
- (B) Day 1 reale Stile Car se replay già verde retroattivamente

**MAI auto-lanciare Day 1 reale.** Vedi memory `feedback_no_live_without_test.md` + `feedback_e2e_full_test_founder_before_day1.md`.

## Closure S205

- Update `MEMORY.md` con esito 5 step (verde/giallo/rosso per ognuno).
- Aggiorna `HANDOFF-ARGOS-FIX-2026-05-28.md` (o sostituisci con `HANDOFF-S205-*.md`).
- Commit: `prompts/s205_*.md` + `HANDOFF-*` + eventuale patch micro-Step 4.

## Vincoli sessione

- Context budget gate **60%** (cwd ARGOS, no skill pesanti).
- Domenica 2026-05-31 OFF — non pianificare Luke fisico domenica.
- Sanitizer over-mask BLOCKER strutturale Day 1 (recidiva S179b/S183-bis/S187/S188).
