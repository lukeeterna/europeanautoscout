# S175 ARGOS — Mystery shopper Layer 2 pilot fisico (3 dealer HIGH ranking)

**Precondition**: S174 chiuso GIALLO 2.5/3 — migration iMac VERDE, hash sync VERDE post-rsync, LLM path verificato con identity_post_handoff PASS e ban argos PASS. Caveat aperto: `target_lexicon` D-28 module presente nel system prompt ma LLM lo ignora in favore di `hard_rules` cost-deflect. Calibration target_lexicon = output S175 stesso (mystery shopper raccoglie ground-truth lessico commissione).

**Riferimenti**:
- `data/s173_cciaa_target_d28.csv` — 33 micro-dealer Sud Italia harvested S173
- `wiki/projects/ARGOS/DECISIONS.md` D-27 (3-layer mystery shopper) + D-28 (target micro-dealer commissione)
- `s174_verify_s173_yellow.md` — caveat e findings
- AMBRA-AUDIT.md sez 6 + sez 8.4 (critica strutturale FSM)

---

## SCOPE S175

**3 dealer HIGH ranking** selezionati da `data/s173_cciaa_target_d28.csv` (filtro: stock_size_estimate ≤ 10, regione Calabria/Sicilia/Puglia, digitalmente silenti — no sito o solo Facebook page).

**Layer 2 mystery shopper = Luke fisico** che impersona cliente finale che ha bisogno di auto specifica. NON ARGOS messaging. Goal: seed curiosità organicamente cosicché Layer 3 AMBRA (post-handoff) abbia base reale per riprendere il filo.

### Step operativi

**S175.1 — Selection dealer HIGH (~30min)**
```bash
sqlite3 :memory: <<SQL
.mode csv
.import data/s173_cciaa_target_d28.csv dealers_d28
SELECT * FROM dealers_d28 WHERE ranking='HIGH' LIMIT 5;
SQL
```
Luke sceglie 3 dealer fisicamente raggiungibili o telefonicamente contattabili.

**S175.2 — Script mystery shopper Layer 2 (Luke writes)**
Per ogni dealer scelto, Luke prepara:
- Auto specifica: marca/modello/anno/budget plausibile per zona (es. BMW Serie 1 2020 €18-22k per Calabria)
- Persona cliente: età, lavoro, perché vuole quel modello
- Frase seed Argos: "ho visto online che Argos cerca auto in Germania, conosce?"
- Goal: registrare risposta dealer (audio/video se possibile, txt diary se no)

**S175.3 — Esecuzione fisica/telefonica (Luke, fuori sessione Claude)**
3 conversazioni Layer 2 mystery shopper. Luke registra:
- Reazione dealer alla frase Argos
- Lessico spontaneo dealer (commissione/margine/cliente-cerca/su-ordine)
- Apertura/chiusura conversazione
- Disponibilità futura ("se trovo qualcosa la richiamo?")

**S175.4 — Sync ground-truth → repo**
File `data/s175_mystery_shopper_outputs.md`:
- Dealer ID + ranking + zona
- Auto fittizia richiesta
- Trascrizione/sintesi conversazione
- Tag lessico spontaneo dealer (es. "commissione: 5", "margine: 2", "su ordine: 3")
- Status: SEEDED (curiosità accesa) | NEUTRAL | REJECTED

**S175.5 — Calibration target_lexicon module (Claude in sessione)**
Da `s175_mystery_shopper_outputs.md`, estrai:
- Top 5 termini commissione effettivamente usati da micro-dealer Sud
- Top 5 termini margine premium NON usati (banditi)
- Reformulate `PROMPT_MODULES['target_lexicon']` in `response-analyzer.py` con utterances reali
- Rerun G2 S174 per confermare LLM ora usa target lexicon su cost-related question
- Update `tests/test_ambra_layer3.py` con 1 test reale ground-truth (non mock)

**S175.6 — Handoff Layer 3 AMBRA (per dealer SEEDED only)**
Per ogni dealer SEEDED:
```sql
UPDATE conversations
SET handoff_source='mystery_shopper', is_micro_dealer=1
WHERE dealer_id IN (<S175 SEEDED dealer ids>);
```
Day 1 AMBRA template post-handoff applicato (D-27 reactive tone).

---

## CRITERI VERDE/GIALLO/ROSSO

- **VERDE** = ≥2/3 dealer SEEDED + target_lexicon calibrato + ≥1 test integration reale passing
- **GIALLO** = 1/3 SEEDED + lexicon parziale + caveat aperto S176
- **ROSSO** = 0/3 SEEDED → D-27 strategy invalidata, ripensare 3-layer model

---

## VINCOLI S175

- **Luke fisico richiesto** — questa sessione NO Claude esegue mystery shopper. Claude prepara script + analizza output.
- **#1 verifica fattuale** — claim "dealer SEEDED" richiede evidence reale (audio/diary), non assumption
- **#3 raccomandazione singola** — script mystery shopper = 1 versione raffinata, no A/B/C/D options a Luke
- **#9 mai diplomatico** — se 0/3 SEEDED, dichiarare D-27 invalidata, no soft language
- **#11 pattern recognition** — S173 mock-only → S174 finding integration → S175 ground-truth. Ogni step preserva learning, non re-mocka.
- **NO Day 1 dealer reale outside SEEDED set** finché S175 chiusa.

---

## OUTPUT ATTESI S175

1. `data/s175_mystery_shopper_outputs.md` — ground-truth 3 conversazioni
2. Diff `wa-intelligence/response-analyzer.py` PROMPT_MODULES['target_lexicon'] calibrato
3. 1 test integration reale in `tests/test_ambra_layer3.py` (non mock, no fabricated response)
4. SQL update handoff_source per dealer SEEDED
5. Verdict VERDE/GIALLO/ROSSO + commit

---

## CHIUSURA S175

- VERDE 2-3 SEEDED → handoff S176 (primo Day 1 AMBRA reale post-handoff su 1 dealer SEEDED)
- GIALLO 1 SEEDED → handoff S176-bis (espandi mystery shopper a 5-10 dealer ranking MEDIUM)
- ROSSO 0 SEEDED → handoff S176-strat (rivedi D-27 model, possibile D-29 alternative path)
