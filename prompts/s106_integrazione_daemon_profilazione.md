# S106 — Integrazione Daemon + Profilazione Dealer + Primo Outreach Live

## Contesto

S105 ha prodotto:
- Architettura template-first completa: state_machine.py, templates.py, validator.py
- 3 varianti DAY1 (PREMIUM/MIXED/GENERALIST) con leve reali testate
- Brand map 22 brand con priorita' CORE/HIGH/MEDIO/EVITARE
- CLAUDE.md integrato con Agent Routing Table (17 agent)
- 7 deep research con dati verificati
- Servizio definito: Scenario A (scouting puro, success-fee)

MA: i moduli Python sono pronti ma il daemon wa-daemon.js NON li chiama ancora.
Il DB ha 30 dealer con WA ma SENZA archetipo/brand classificati.

## REGOLA ZERO — Usa la Agent Routing Table in CLAUDE.md

Per ogni task, consulta la tabella in CLAUDE.md e spawna l'agent corretto:
- DB/API/daemon → `backend-architect`
- LLM/classificatore → `ai-engineer`
- Copy/contenuti → `content-creator`
- Ricerca mercato → `deep-researcher` + `trend-researcher`
- Test API → `api-tester`
- Deploy → `agent-ops`

## 3 Blocchi di Lavoro (in ordine)

### BLOCCO 1: Integrazione daemon wa-daemon.js (BLOCCANTE, 3h)

Agent: `backend-architect` + `ai-engineer`

Il daemon Node.js deve chiamare i moduli Python PRIMA di ogni invio/risposta:

```
FLUSSO INBOUND (dealer risponde):
  1. Daemon riceve messaggio → salva in messages
  2. Chiama Python: classify(msg) → intent + state_transition
  3. Chiama Python: process_inbound(db, dealer_id, intent) → aggiorna stato
  4. Chiama Python: select_template(intent, state) → template_id
  5. Chiama Python: fill_template(template_id, dealer_data) → messaggio
  6. Chiama Python: validate(messaggio, template_id, dealer) → PASS/BLOCK
  7. Se PASS: invia + increment_outbound(). Se BLOCK: telegram alert

FLUSSO OUTBOUND (noi contattiamo):
  1. Chiama Python: can_send(db, dealer_id, template_id) → ok/reason
  2. Se ok: fill_template → validate → send → increment_outbound → update_state
  3. Se no: log + skip
```

File da modificare: `wa-intelligence/wa-daemon.js` (funzione che gestisce messaggi inbound + endpoint /send)
Approccio: subprocess Python chiamato dal Node.js (come gia' fa per response-analyzer.py)

Test obbligatorio: `api-tester` sul daemon — invio + ricezione + classificazione + template + validazione

### BLOCCO 2: Profilazione 30 dealer target (2h)

Agent: `agent-research` + `trend-researcher`

Per ogni dealer in `research/s104_dealer_enriched_wa.json`:
1. Cercare su Google Maps: rating, recensioni, specializzazione
2. Verificare stock attuale su Subito.it/AS24
3. Classificare brand mix (PREMIUM_BRANDS_CORE/HIGH/MEDIO)
4. Assegnare variante DAY1 con select_day1_variant()
5. Classificare archetipo (NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE)

Output: `research/s106_dealer_profiled_30.json` con campi:
```json
{
  "dealer_id": "...",
  "name": "...",
  "phone_wa": "...",
  "province": "...",
  "brands": ["BMW", "Fiat"],
  "premium_pct": 0.25,
  "day1_variant": "DAY1_MIXED",
  "brand_focus": "BMW",
  "archetype": "RAGIONIERE",
  "google_rating": 4.2,
  "reviews_count": 47,
  "source_found": "AutoScout24"
}
```

### BLOCCO 3: Primo outreach LIVE a 5 dealer reali (1h)

Agent: `agent-sales` + `project-shipper`

Pre-requisiti: BLOCCO 1 e 2 completati.

1. Selezionare top 5 dealer profilati (fit >= 8, archetipo assegnato, WA confermato)
2. Per ognuno: fill_template(day1_variant, dealer_data) → validate → can_send → invio
3. Monitorare risposte su Telegram
4. Se risposta: verificare che il flusso template-first funziona (non il vecchio LLM)

## Regole

- Usare SEMPRE Agent Routing Table per ogni sub-task
- Test E2E PRIMA di invio a dealer reali
- Se validate() ritorna BLOCK: NON inviare, MAI
- Se can_send() ritorna False: NON inviare, MAI
- Aggiornare memory/MEMORY.md durante la sessione, non solo alla fine

## File chiave

```
Daemon:          wa-intelligence/wa-daemon.js
State machine:   wa-intelligence/state_machine.py
Templates:       wa-intelligence/templates.py
Validator:       wa-intelligence/validator.py
Analyzer:        wa-intelligence/response-analyzer.py
Dealer target:   research/s104_dealer_enriched_wa.json
Brand map:       .planning/research/s105_brand_premium_completi.md
CLAUDE.md:       CLAUDE.md (con Agent Routing Table)
```
