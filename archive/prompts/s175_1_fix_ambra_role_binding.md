# S175.1 ARGOS — Fix AMBRA role-binding info-broker (NOT seller) — gate post-S175.0 ROSSO

**Precondition**: S175.0 chiuso ROSSO (vedi `data/s175_0_e2e_real_report.md`). GAP-3 critico (AMBRA inventa veicolo X3 2021 89.855km €27.389 su inbound VEHICLE_REQUEST BMW X1 2020 €18000) + GAP-2 sistemico (target_lexicon FAIL S174 confermato). Root cause unica: prompt AMBRA non distingue ruolo info-broker da seller.

**Riferimenti vincolanti**:
- D-21 workflow info-broker → communication-broker-garante (broker NON inventa veicoli, propone solo post on_demand_runner reale)
- D-15 founder HITL 100% primi 1-3 dealer (Luke decides manual launch on_demand_runner per ogni VEHICLE_REQUEST)
- D-28 target micro-dealer commissione (lexicon: "commissione", "su ordine", "ci guadagna", NOT "scheda"/"dossier"/"servizio")
- S174 finding target_lexicon FAIL deferred S175

## SCOPE S175.1

Fix unico strutturale (vincolo #3) entrambi gap S175.0 via role-binding esplicito nel prompt AMBRA. Test post-fix replay su TEST_FOUNDER stesso scenario S175.0 (VEHICLE_REQUEST BMW X1 2020 18000). Pass criteria:
1. AMBRA reply NON contiene km/prezzo/anno veicoli specifici (no hallucination)
2. AMBRA reply contiene conferma estratti + ETA (24-48h o "le scrivo a breve")
3. AMBRA reply lexicon ban list 0 violations: "scheda", "dossier", "servizio", "piattaforma", "costi nascosti", "5-7 giorni lavorativi", "GRATIS"
4. AMBRA reply contiene ≥1 token allow list: "commissione", "su ordine", "ci guadagna", "macchina pulita", "km certificati"

## Pre-flight (Claude in-session, ~10min)

```bash
# P1 — Locate prompt AMBRA VEHICLE_REQUEST handler
grep -nE 'VEHICLE_REQUEST|extract_vehicle_request|class.*VehicleRequest|classify_intent' \
  ~/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py | head -20

# P2 — Identify prompt template file (likely in prompts/ subdir)
ls ~/Documents/app-antigravity-auto/wa-intelligence/prompts/ 2>/dev/null
find ~/Documents/app-antigravity-auto/wa-intelligence -name '*.txt' -path '*prompt*' 2>/dev/null | head -10

# P3 — Read S173/S174 modifications history (lexicon retune già provato)
git log --oneline --all -- wa-intelligence/prompts/ 2>/dev/null | head -10
```

## Fix step (Claude, ~1h coding)

1. **Patch prompt VEHICLE_REQUEST** in identified file:
   - Add explicit "ROLE: info-broker, NOT seller" header
   - Add "FORBIDDEN: inventare km/prezzo/anno/colore di veicoli specifici. NON proporre veicoli concreti senza dossier già generato"
   - Add "REQUIRED action: conferma estratti (marca/modello/budget/anno) + 'sto cercando ora, le scrivo entro 24-48h'"
   - Add lexicon section: BAN ["scheda", "dossier", "servizio", "piattaforma", "costi nascosti", "5-7 giorni lavorativi", "GRATIS", "trovo la macchina giusta"] / PREFER ["commissione", "su ordine", "ci guadagna", "macchina pulita", "km certificati", "le sto cercando"]

2. **Add ResponseValidator post-LLM** check (extend S173 pattern):
   - Regex hallucination: match `\d{2,3}[\.,]?\d{3}\s*km` or `\d{4,5}\s*euro|€\s*\d{4,5}` → if VEHICLE_REQUEST class + NO dossier_id set → BLOCK reply, retry o template fallback "le scrivo a breve"
   - Lexicon ban list match → BLOCK reply, regenerate con stricter prompt

## Test post-fix (Luke phone replay, ~5min)

```bash
# Reset TEST_FOUNDER state to HANDOFF_LAYER3 (S175.0 starting state)
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
UPDATE conversations SET current_step='HANDOFF_LAYER3', state_updated_at=datetime('now')
WHERE dealer_id='TEST_FOUNDER';\""
```

**LUKE ACTION (phone TEST_FOUNDER → ARGOS WA 3281536308)**:
> Mi serve una BMW X1 del 2020, budget sui 18000. La trova?

**Gate post-fix**:
- AMBRA reply entro 5min
- NO km/prezzo/anno inventati (regex check)
- Conferma estratti + ETA presente
- Lexicon ban 0 violations, ≥1 allow

```bash
# Verify reply DB
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT direction, substr(body,1,400), datetime(created_at)
FROM messages WHERE dealer_id='TEST_FOUNDER'
ORDER BY rowid DESC LIMIT 3;\""
```

## Verdict S175.1

- VERDE 4/4 pass criteria → resume S175.0 da STEP 4 (on_demand_runner BMW X1)
- GIALLO 2-3/4 pass → fix singolo aggiuntivo prima resume
- ROSSO ≤1/4 → role-binding insufficient, ripensare D-21 workflow tech (forse AMBRA NON deve mai replicare a VEHICLE_REQUEST, solo Telegram HITL → Luke compone manualmente)

## Autocritica strutturale (vincolo #4)

1. **Assunzione**: presumo che prompt AMBRA sia editabile in 1 file. Se split su multiple (intent classifier + response generator + lexicon enforcer), patch frammentato richiede 2x effort.
2. **Cosa rompe a 30/60gg**: ResponseValidator regex su km/prezzo si auto-disabilita su dossier reali (PDF generato → AMBRA può legittimamente citare km/prezzo dal dossier). Necessario flag `dossier_attached_to_thread` in DB per discriminare.
3. **Pattern errore noto**: S173 lexicon retune già fatto (ResponseValidator condizionale) ma S174 ha trovato target_lexicon FAIL → retune incompleto. Rischio S175.1 stessa famiglia: fix copre ban list ma allow list non emerge organicamente da LLM Italian baseline.
4. **Sovradimensiono**: full role-binding rewrite + ResponseValidator + lexicon dual-list potrebbe essere over-engineering per blocker singolo. Fix minimo viable = solo template forzato "conferma + ETA" su VEHICLE_REQUEST class, defer lexicon retune a S175.2 separato.

## Context budget

- Stima: pre-flight 10% + fix 30% + test 20% + report 15% = ~75% gate hard. Split possibile S175.1a (fix VEHICLE_REQUEST template) + S175.1b (lexicon retune) se context >55% post-fix.
- Sessione precedente S175.0 chiusa 67% — partire <35% obbligatorio (vincolo #7).

## Output attesi

1. Patch file in `wa-intelligence/prompts/` o `wa-intelligence/response-analyzer.py` con commit hash
2. `data/s175_1_validation.md` — replay test result + 4 pass criteria evaluation
3. Commit + push
4. Handoff prompt conditional:
   - VERDE → resume S175.0 STEP 4 in nuova sessione
   - GIALLO → `prompts/s175_2_lexicon_retune.md`
   - ROSSO → `prompts/s175_strategic_rethink_ambra_role.md`
