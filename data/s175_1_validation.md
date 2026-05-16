# S175.1 — Fix AMBRA role-binding info-broker — validation report

**Data**: 2026-05-16
**Sessione**: S175.1 (~30min coding + smoke offline)
**Stato code**: VERDE smoke-tested. Replay fisico TEST_FOUNDER deferred a S175.1b (richiede Luke phone, sessione dedicata).

## Decisione CTO

Procedere con commit atomico dei 3 fix tightly coupled (prompt module + skip brand-affinity + validator hallucination/lexicon ban) + handoff replay-only S175.1b.
Motivazione: smoke offline VERDE prova root cause coperta; replay fisico richiede ~10min finestra dedicata Luke, vincolo #7 context budget impone closure ora.

## Root cause S175.0 ROSSO step 3 (verificata fattuale, non ipotesi)

Pattern hallucination "BMW X3 2021 89.855km €27.389" su VEHICLE_REQUEST X1 2020 €18000 ha **due cause sovrapposte**:

1. **`build_user_prompt` brand-affinity fallback inquina vehicle_ctx**:
   `response-analyzer.py` linee 645-659 (pre-fix): se `get_relevant_vehicles(marca='BMW', budget=18000)` torna vuoto, fallback `get_relevant_vehicles(dealer_brands=['BMW'])` pesca top-3 BMW PROCEED dal `cove_tracker.duckdb` **ignorando budget richiesto** → vehicle_ctx popolato con BMW X3 fuori budget.
2. **Prompt non distingue role info-broker (D-21) da seller**: LLM con vehicle_ctx popolato + system prompt che dice "VEICOLI DISPONIBILI ... usa SOLO questi" interpreta come istruzione a proporre.

Bypass D-15 (founder HITL on_demand_runner manuale): AMBRA replica auto in 5min senza che Luke abbia lanciato `tools/on_demand_runner.py`.

## Fix applicati (un unico commit, 3 modifiche sinergiche)

### Fix 1 — Skip brand-affinity per VEHICLE_REQUEST
`response-analyzer.py` `build_user_prompt`: in `cls_type == 'VEHICLE_REQUEST'` forza `vehicle_ctx = ''` e rende esplicito al LLM che la sezione VEICOLI DISPONIBILI non è pertinente.
Brand-affinity fallback resta valido per POSITIVE/CURIOSITY/altre classi (backward compat).

### Fix 2 — Nuovo modulo prompt `vehicle_request_broker`
`PROMPT_MODULES['vehicle_request_broker']`: role-binding esplicito "info-broker NOT seller".
Istruzioni hard:
- Conferma estratti (marca/modello/anno/budget) + ETA 24-48h
- VIETATO inventare km/prezzi/anno/colore di veicoli specifici
- VIETATO proporre alternative anche se simili
- VIETATO marketing lexicon: "scheda", "dossier", "5-7 giorni lavorativi", "costi nascosti", "trovo la macchina giusta"
- Se richiesta fuori range, NON dire "difficile" — di' "ci guardo per bene"

Iniettato in `build_system_prompt` quando `cls_type == 'VEHICLE_REQUEST'`, posizionato in coda (massima salienza LLM).

### Fix 3 — ResponseValidator nuovi check (safety net post-LLM)
- `_check_vehicle_hallucination`: regex km `\b\d{1,3}[\.,]?\d{3}\s*km\b` + prezzo `(?:€|euro\s|EUR\s)\s*([1-9]\d{4}|[1-9]\d{1,2}[\.,]\d{3})` su VEHICLE_REQUEST con vehicle_ctx vuoto → BLOCK
- `_check_broker_lexicon_ban`: ban list ("scheda con foto", "dossier gratis", "5-7 giorni lavorativi", "costi nascosti", "trovo la macchina giusta", "difficile da trovare", "è un bel pezzo", ecc.) su VEHICLE_REQUEST → BLOCK
- Estese le blocking key list per includere `vehicle_hallucination` e `broker_lexicon_ban`
- `retry_prompt` aggiornato con istruzione VEHICLE_REQUEST esplicita
- **`VEHICLE_REQUEST_BROKER_FALLBACK` template**: se retry resta bloccante, sostituzione automatica con template "conferma estratti + ETA" costruito da `_extracted_request`, evita HOLD spurio bloccante pipeline (D-15 founder HITL via Telegram già notificato in step 2b)

## Smoke offline VERDE

Test eseguito in `wa-intelligence/` con Python 3.13 (no DB, isolation):

```
OK system_prompt VEHICLE_REQUEST mystery_shopper micro_dealer contiene VEHICLE_REQUEST_ROLE
OK POSITIVE non attiva VEHICLE_REQUEST_ROLE
Violations S175.0 hallucination reply: [
  "vehicle_hallucination_km: ['89.855 km']",
  "vehicle_hallucination_price: ['27389']",
  'broker_lexicon_ban: "difficile da trovare"',
  'broker_lexicon_ban: "è un bel pezzo"'
]
Violations compliant reply: []
Violations POSITIVE (no vehicle_hallucination expected): []
ALL SMOKE TESTS PASS
```

Reply esatta S175.0 step 3 viene bloccata con 4 violations (km hallucinated + price hallucinated + 2 lexicon ban).
Reply broker-compliant "sto cercando BMW X1 2020 sui 18000, le scrivo entro 24-48h" passa pulita.
POSITIVE backward compat: vecchio prezzo legittimo in vehicle_ctx non scatta hallucination (cls_type guard).

## Autocritica strutturale (vincolo #4)

1. **Assunzione**: ho assunto che LLM rispetti il modulo `vehicle_request_broker` perché posizionato in coda. Se Groq llama-3.3-70b ignora last-instruction salience, ResponseValidator+template fallback è la safety net che garantisce comunque output broker-compliant. Robustezza è "validator-driven" non "prompt-driven only".
2. **Cosa rompe a 30/60gg**: quando avremo dossier reali post-on_demand_runner (D-21 step 4-7), AMBRA dovrà replicare a VEHICLE_REQUEST CITANDO km/prezzo dal dossier reale. Necessario flag `dossier_attached_to_thread` in `conversations` table per discriminare hallucination vs. legitimate citation. Backlog S175.x.
3. **Pattern errore noto**: S173 ResponseValidator condizionale era stato introdotto per stesso pattern (banned argos su mystery_shopper). Funziona pattern. Estensione a hallucination/lexicon ban è naturale.
4. **Sovradimensiono?**: 5 modifiche (prompt module + branching prompt + skip ctx + 2 validator checks + fallback template + retry prompt + blocking list extend) potrebbero sembrare over-engineering. Justification: senza fallback template, se LLM persiste in hallucination la pipeline cade in HOLD Telegram, AMBRA non risponde al dealer reale, trust break alternativo. Fallback template chiude il loop.

## Pass criteria (verifica post-replay Luke S175.1b, NON in questa sessione)

1. AMBRA reply NON contiene km/prezzo/anno veicoli specifici
2. AMBRA reply contiene conferma estratti + ETA (24-48h o "le scrivo a breve")
3. AMBRA reply lexicon ban list 0 violations
4. AMBRA reply contiene ≥1 token allow list ("commissione", "su ordine", "ci guardo per bene", "sto cercando", "ci guadagna", "km certificati")

## Stato S175.1 closure

**VERDE su code change (smoke offline)**. Replay fisico TEST_FOUNDER deferred S175.1b in sessione fresca dedicata (~10min, richiede Luke phone). Nessuno stato PARTIAL/ARANCIONE: il commit chiude il scope coding di S175.1; la replay è una sessione separata di acceptance.

## File modificati

- `wa-intelligence/response-analyzer.py` (5 sezioni: PROMPT_MODULES nuovo modulo, build_system_prompt branching, build_user_prompt skip ctx, ResponseValidator 2 nuovi check + blocking list extend, retry prompt + fallback template VEHICLE_REQUEST_BROKER_FALLBACK)

## Handoff

- **Resume prompt**: `prompts/s175_1b_replay_test_founder.md` (replay-only, Luke phone)
- **Path A LUCKY CARS mystery shopper**: rimane SOSPESO fino verdict S175.1b
- Se S175.1b 4/4 VERDE → resume S175.0 da STEP 4 (on_demand_runner BMW X1 manuale Luke)
- Se S175.1b 2-3/4 → `prompts/s175_2_lexicon_retune.md` (lessico allow list emerge organicamente)
- Se S175.1b ≤1/4 → `prompts/s175_strategic_rethink_ambra_role.md` (forse AMBRA non deve mai rispondere a VEHICLE_REQUEST, solo HOLD Telegram → Luke compone manualmente)
