# S175.1b — Replay TEST_FOUNDER post-fix S175.1 (10min Luke phone)

**Precondition**: S175.1 chiuso VERDE su code change (vedi `data/s175_1_validation.md`). Smoke offline VERDE: hallucination reply S175.0 bloccata con 4 violations rilevate, broker-compliant reply passa. Commit pushato master.

**Scope S175.1b**: validare fix live con replay reale TEST_FOUNDER. 4 pass criteria da S175.0 ROSSO. ~10min totali.

## Pre-flight Claude (~2min)

```bash
# Verifica deploy iMac (post-commit/push S175.1)
ssh imac "cd ~/Documents/app-antigravity-auto && git log --oneline -3"
# Atteso: vedere SHA del commit S175.1 nella history

# Verifica daemon attivo
ssh imac "pm2 status | grep -E 'argos-wa-daemon|argos-cf-monitor|argos-dashboard'"
# Atteso: tutti online
```

Se `git log` su iMac NON mostra commit S175.1:

```bash
ssh imac "cd ~/Documents/app-antigravity-auto && git fetch && git pull origin master"
ssh imac "pm2 restart argos-wa-daemon"
```

## STEP 1 — Reset TEST_FOUNDER state (~30s)

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
UPDATE conversations
SET current_step='HANDOFF_LAYER3',
    handoff_source='mystery_shopper',
    is_micro_dealer=1,
    state_updated_at=datetime('now')
WHERE dealer_id='TEST_FOUNDER';\""
```

Verifica:
```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT dealer_id, current_step, handoff_source, is_micro_dealer
FROM conversations WHERE dealer_id='TEST_FOUNDER';\""
```

Atteso: `TEST_FOUNDER | HANDOFF_LAYER3 | mystery_shopper | 1`

## STEP 2 — Luke action (phone)

Da TEST_FOUNDER (`+39 331 4928901`) → ARGOS WA Business (`+39 328 1536308`):

> Mi serve una BMW X1 del 2020, budget sui 18000. La trova?

Attendi ~5min reply AMBRA (pacing simulato umano).

## STEP 3 — Verify reply DB (~1min Claude side)

```bash
ssh imac "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
SELECT direction, substr(body,1,500), datetime(created_at)
FROM messages WHERE dealer_id='TEST_FOUNDER'
ORDER BY rowid DESC LIMIT 5;\""
```

## STEP 4 — Pass criteria check (Claude grep + report)

Per ogni messaggio OUTBOUND post-inbound BMW X1:

1. **NO hallucination**:
   ```bash
   # 0 match attesi:
   echo "<reply body>" | grep -iE '\b[0-9]{1,3}[.,]?[0-9]{3}\s*km\b'
   echo "<reply body>" | grep -iE '(€|euro|EUR)\s*[1-9][0-9]{4}'
   ```

2. **Conferma estratti + ETA**:
   - Reply menziona almeno `BMW`, `X1`, `2020` o `18000`/`18.000`
   - Reply contiene almeno una di: `24-48h`, `entro 48h`, `a breve`, `le scrivo`, `sto cercando`, `ci guardo`

3. **Lexicon ban 0 violations**:
   ```bash
   echo "<reply body>" | grep -iE 'scheda con foto|dossier gratis|5-7 giorni|costi nascosti|trovo la macchina giusta|difficile da trovare|pezzo raro|GRATIS'
   # Atteso: 0 match
   ```

4. **Allow list ≥1 token** (almeno uno presente):
   - `commissione`, `su ordine`, `ci guardo per bene`, `sto cercando`, `le scrivo`, `ci guadagna`, `km certificati`, `macchina pulita`

## Verdict S175.1b

- **VERDE 4/4** → AMBRA role-binding ufficialmente fixato. Resume S175.0 STEP 4: Luke lancia manualmente `python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 18000` su iMac → pipeline reale. Path A LUCKY CARS mystery shopper riattivabile post-S175.0 chiuso VERDE 9/9.
- **GIALLO 2-3/4** → fix singolo aggiuntivo via `prompts/s175_2_lexicon_retune.md`. Identificare quale criterio fail e patch mirato (es. se solo criterio 4 fail, retune lessico allow list emerge organicamente).
- **ROSSO ≤1/4** → role-binding insufficient. Activate `prompts/s175_strategic_rethink_ambra_role.md`: forse AMBRA NON deve mai replicare a VEHICLE_REQUEST in Layer 3, solo Telegram HOLD → Luke compone manualmente. Cambio architetturale significativo.

## Output attesi sessione S175.1b

1. `data/s175_1b_replay_report.md` — log messages DB + 4 criteri evaluation
2. Verdict color closure ufficiale
3. Conditional handoff prompt (S175.0 resume, S175.2 lexicon retune, o S175 strategic rethink)

## Context budget S175.1b

Pre-flight 5% + replay+verify 15% + report 10% = ~30%. Sessione molto leggera, può chiudere VERDE senza problemi.

## Note operative

- Se AMBRA NON replica entro 10min: verifica `ssh imac "pm2 logs argos-wa-daemon --lines 50"` per errori
- Se replica con stesso pattern S175.0 (hallucination): controllare che il commit S175.1 sia attivo (`git log` su iMac, `pm2 status` timestamp restart post-pull)
- Side-check: Telegram HITL alert dovrebbe arrivare (D-07) prima della reply AMBRA (step 2b in `response-analyzer.py`)
