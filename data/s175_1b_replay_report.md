# S175.1b — Replay TEST_FOUNDER report

**Data esecuzione**: 2026-05-16 11:40 → 11:48 IT (8min effettivi)
**Verdict**: 🟢 **VERDE 4/4**
**Decisione**: AMBRA role-binding info-broker (S175.1) UFFICIALMENTE FIXATO. Resume S175.0 STEP 4 sbloccato.

---

## Pre-flight applicato

Stato iniziale iMac problematico — risolto con minimo invasivo:

| Issue | Status iniziale | Fix |
|-------|-----------------|-----|
| iMac working tree su branch `main` HEAD `fd35965e` (history rewrite security-purge), divergente da `origin/master` `851d89e` | S175.1 fix NON presente su disco | `git checkout origin/master -- wa-intelligence/response-analyzer.py` (puntuale, branch intatto) |
| `response-analyzer.py` stale (modify 2026-05-15 18:41, zero marker S175.1) | Daemon legge file pre-fix | Backup `.bak-pre-s175-1-<ts>` salvato + checkout file + verifica 7/7 marker S175.1 presenti |
| `pm2` non in PATH SSH non-interactive | `which pm2` exit 1 | path assoluto `~/.npm-global/bin/pm2` + env PATH inject |
| `wa-daemon` uptime 27h (pre-restart) | Fix S175.1 non caricato | `pm2 restart argos-wa-daemon` → boot pulito 11:38:32 sessione autenticata |
| DB iMac `dealer_network.sqlite` schema S173 | OK (colonne `handoff_source`, `is_micro_dealer` presenti) | nessuna azione |

## STEP 1 — Reset state ✅

```
TEST_FOUNDER | HANDOFF_LAYER3 | mystery_shopper | 1
```

## STEP 2 — Luke phone action ✅

Inbound 11:40:01 da `+39 331 4928901`:
```
Mi serve una BMW x1 del 2020, budget sui 18000 . La trova?
```

## STEP 3 — Analyzer trace (/tmp/argos-analyzer.log)

```
[16/05/2026 11:40:16] Analyzer avviato per msg_id=msg_1778924401115_h4jgj
  Dealer: Test Concessionaria Founder | Persona: NARCISO | Step: HANDOFF_LAYER3
  Classificazione: {'type': 'VEHICLE_REQUEST', 'confidence': 0.9, 'method': 'keyword'}
  [STATE MACHINE] Intent=VEHICLE_REQUEST → new_state=COLD
  [TEMPLATE-FIRST] Nessun template per (VEHICLE_REQUEST, COLD) → LLM
[16/05/2026 11:40:18] VEHICLE_REQUEST — estratto: {marca:'BMW', modello:None, anno_min:2020, budget_eur:None}
  [OK] Groq llama-3.3-70b-versatile response received
  [VALIDATOR] BLOCKING: ['broker_lexicon_ban: "difficile da trovare"'] — RETRY con prompt ridotto...
  [OK] Groq llama-3.3-70b-versatile response received
  [RETRY] OK — risposta corretta al secondo tentativo
[VARIATION] min_variation=0.69 vs last 5 msgs — PASS
[AUTO] Approvata + schedulata reply reply_76f15e91 — 2 msg via /send-multi — invio tra 475s
[16/05/2026 11:40:28] Analyzer completato. Reply IDs: ['reply_b51e5bf8']
```

**Fix S175.1 ATTIVO confermato**: ResponseValidator ha intercettato `broker_lexicon_ban: "difficile da trovare"` al primo LLM call → retry meccanism con prompt ridotto → reply compliant.

Confronta con run pre-fix delle 10:41 (stesso inbound, daemon stale): nessun BLOCKING, passato direttamente con hallucination `BMW X3 2021 89.855km €27389` + lexicon ban multipli (reply `reply_df498729` rowid 130).

## STEP 4 — Delivery + 4 pass criteria

### Delivery WA (daemon log + DB messages)

```
11:48:24 SENT_SERVER 141115562971357@lid → wa_msg_id=true_141115562971357@lid_3EB0F6DD117E084B4C15E3
11:48:28 MULTI-INVIATO via HTTP: 393314928901@c.us (TEST_FOUNDER) — 2 msg
11:48:28 SENT_SERVER 141115562971357@lid → wa_msg_id=true_141115562971357@lid_3EB0C9179B17BB6747352C
[AUTO] Reply reply_76f15e91 inviata
```

### Reply finale (DB messages rowid 132+133)

```
[132 OUTBOUND 11:48:24] ciao, senti, mi hai chiesto di trovare una bmw x1 del 2020 con un budget di 18000, ci sto lavorando
[133 OUTBOUND 11:48:28] le scrivo entro 24-48h, sto cercando per lei, ok? Luca
```

### 4 pass criteria evaluation

**Criterio 1 — NO hallucination** ✅
- Regex `\b[0-9]{1,3}[.,]?[0-9]{3}\s*km\b`: 0 match
- Regex `(€|euro|EUR)\s*[1-9][0-9]{4}`: 0 match
- Solo `18000` presente = eco del budget cliente (NON inventato)

**Criterio 2 — Conferma estratti + ETA** ✅
- Estratti: `BMW` ✅, `x1` ✅, `2020` ✅, `18000` ✅
- ETA: `entro 24-48h` ✅ + `sto cercando` ✅ + `ci sto lavorando` ✅ + `le scrivo` ✅

**Criterio 3 — Lexicon ban 0 violations** ✅
Pattern: `scheda con foto|dossier gratis|5-7 giorni|costi nascosti|trovo la macchina giusta|difficile da trovare|pezzo raro|GRATIS` → 0 match.

**Criterio 4 — Allow list ≥1 token** ✅
Match: `le scrivo` + `sto cercando` (2 token su 8 della allow list).

## Verdetto

**🟢 VERDE 4/4** — S175.1 fix role-binding info-broker confermato live su TEST_FOUNDER reale.

Pattern S175.0 ROSSO (hallucination BMW X3 2021 89.855km €27389 su VEHICLE_REQUEST X1 2020 €18000) **NON si è ripetuto**. ResponseValidator + VEHICLE_REQUEST_BROKER_FALLBACK + retry_prompt funzionano end-to-end via Groq llama-3.3-70b-versatile.

## Comparison side-by-side (10:41 vs 11:40 stesso inbound)

| Aspect | 10:41 (pre-fix daemon stale) | 11:40 (post-fix checkout origin/master) |
|--------|------------------------------|------------------------------------------|
| `[VALIDATOR]` blocking | NESSUNO — passato al 1° tentativo | `broker_lexicon_ban: "difficile da trovare"` → RETRY |
| Hallucination veicolo | `BMW X3 2021 89.855km €27389` (S175.0 ROSSO) | ZERO numeri inventati |
| Lexicon ban | `difficile da trovare`, `bel pezzo`, `macchina pulita` (3 violations) | ZERO violations |
| Conferma+ETA | ASSENTE (proposta alternativa pushy) | `ci sto lavorando` + `entro 24-48h` |
| Reply IDs | `reply_df498729` (rowid 129+130) | `reply_76f15e91` (rowid 132+133) |

## Resume S175.0

S175.1b chiude lo step 3 ROSSO di S175.0. Step 4-9 del prompt S175.0 ora sbloccati:

- **STEP 4** Luke lancia manualmente `python3 tools/on_demand_runner.py --marca BMW --modello X1 --budget 18000` su iMac → pipeline reale on-demand.
- **STEP 5-9** continuano come da `prompts/s175_0_e2e_reactive_test_founder.md`.

Path A LUCKY CARS mystery shopper riattivabile post-S175.0 chiuso VERDE 9/9.

## Note operative

- Backup pre-fix preservato su iMac: `~/Documents/app-antigravity-auto/wa-intelligence/response-analyzer.py.bak-pre-s175-1-<ts>` (rollback 1-command se serve)
- iMac repo resta su branch `main` HEAD `fd35965e` (history rewrite) — file `response-analyzer.py` ora aggiornato da `origin/master`, gli altri file pre-S175.1 backbone (S173 prompt modules) erano già coperti da migration DB pregressa e da builds del file analyzer presenti
- Schedule delay invio anti-ban: 475s effettivi misurati (11:40:16 trigger → 11:48:24 SENT_SERVER) = 8min — coerente con human pacing
- `com.argos.scheduler` LaunchD agent + `auto-send` loop entrambi funzionali

## Decisioni applicate

- **D-07** HITL strutturale primi 20 dealer: Luke ha agito fisicamente come dealer (TEST_FOUNDER) per validare AMBRA
- **D-11** Test pipeline 5-step su TEST_FOUNDER prima dealer reale: replay singolo step VEHICLE_REQUEST completato VERDE
- **D-15** Founder HITL 100% primi 1-3 dealer: Luke ha lanciato manualmente il test, non auto-pipeline
- **D-21** ARGOS info-broker → communication-broker-garante: AMBRA ora correttamente bound a role info-broker NOT seller
- **D-28** Target micro-dealer commissione: backward compat preservata (POSITIVE/CURIOSITY non bloccate da hallucination check)
