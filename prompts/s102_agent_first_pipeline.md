# S102 — Agent-First Pipeline: Test E2E + Discovery + Messaggi Pain-Point

## Contesto

S101 ha prodotto:
- Piano Agent-First completo: `research/s101_PIANO_AGENT_FIRST.md` (modificato dal founder)
- Response-analyzer riscritto production-ready (12 fix, 2 code review)
- Groq LLM funzionante (User-Agent fix), cascade aggiornata (Gemma 4, Nemotron, GPT-OSS)
- auto_approve_and_send riscritto con subprocess (fix thread daemon)
- Commission classifier + discovery engine PRONTI ma mai lanciati
- Stress test report: `research/s101_stress_test_report.md`

## Modifiche Founder al Piano (CRITICHE)
- Target: TUTTA ITALIA, non solo Sud — segmentare regione/provincia/citta'
- Principio 7: programma contenuti riservati per dealer + sezione dedicata landing con accesso dedicato
- Messaggi: "quanto tempo perdi su Mobile.de?" NON "ho trovato un X3"

## Protocollo Sessione
1. Leggi `memory/MEMORY.md`
2. Leggi `research/s101_PIANO_AGENT_FIRST.md` (piano master)
3. Esegui in ordine le fasi del piano

## STEP 0.1 — Test E2E Auto-Send (BLOCCANTE)

### Obiettivo
Il sistema DEVE rispondere autonomamente a un messaggio WA senza intervento umano.

### Azioni
1. Verificare WA daemon: `curl -s http://192.168.1.2:9191/status`
2. Inviare Day 1 al dealer test (393314928901)
3. Il founder risponde dal telefono test
4. Monitorare `/tmp/argos-analyzer.log` sull'iMac
5. Verificare:
   - Messaggio ricevuto dal daemon
   - Classificato correttamente (CURIOSITY/POSITIVE/OBJECTION)
   - LLM genera risposta (Groq o free model, NON template fallback)
   - auto_approve_and_send invia la reply (subprocess)
   - `pending_replies.sent = 1` nel DB daemon
   - Messaggio arriva sul telefono test
   - Telegram notification al founder

### Criterio PASS
- Risposta arriva sul telefono test SENZA intervento umano
- Risposta coerente, no fee al primo contatto, no parole bannate
- Tutto loggato e visibile su Telegram

### Se FAIL
- Debug: leggere `/tmp/argos-analyzer.log` + `/tmp/argos-auto-send.log`
- Fix e re-test prima di procedere

## STEP 0.2 — Sync DB CRM <-> Daemon

### Problema
MacBook ha `dealer_network.sqlite` (CRM — 15 dealer)
iMac ha `dealer_network.sqlite` (daemon — conversations, messages, pending_replies)
I dealer del CRM NON sono nel daemon e viceversa.

### Soluzione
Rsync one-way MacBook → iMac per la tabella `dealers`, oppure merge script.
Il daemon deve riconoscere i dealer del CRM quando riceve messaggi.

## STEP 1 — Discovery Dealer Su Commissione

### Deep Research Obbligatoria PRIMA del Discovery
- Analizzare come funziona il discovery_engine (leggere tutto tools/dealer_discovery/)
- Verificare che lo scraper Subito.it funzioni (test con 1 provincia)
- Capire i limiti: rate limiting, coverage, accuratezza commission_classifier

### Esecuzione
```bash
# Test su 1 provincia prima
python3 tools/dealer_discovery/discovery_engine.py --province foggia --dry-run

# Se OK, lanciare priorita' 1
python3 tools/dealer_discovery/discovery_engine.py --all-priority 1

# Poi estendere a tutta Italia (modificare config.py per aggiungere province)
```

### Output Atteso
- Lista dealer con commission_score >= 5.0
- Per ognuno: nome, citta', telefono, WA, commission_score, segnali, brand mix
- Classificazione archetipo (Meccanico-Commerciante / Salonista / Giovane / etc.)

## STEP 2 — Messaggi Pain-Point

### Deep Research Obbligatoria PRIMA della Scrittura
- Leggere: `research/s94_dealer_commissione_pain_points_comunicazione.md`
- Leggere: `research/s99_micro_dealer_archetipo.md`
- Leggere: `research/s99_formazione_integrata_operazione.md`
- Capire i 5 archetipi micro-dealer (Meccanico, Salonista, Giovane, Ragioniere, Weekend Warrior)
- Capire i pain points reali (tempo su Mobile.de, barriera linguistica, km scalati, burocrazia)

### Scrittura
- 5 messaggi Day 1 diversi per archetipo
- Pain-point first, domanda chiusa
- Luxury positioning integrato
- Validare contro regole comunicazione (.claude/rules/communication.md)

## STEP 3 — Pipeline E2E

### Skill/Agent da Implementare
- **agent-discovery**: orchestra discovery_engine + commission_classifier + CRM insert
- **agent-outreach**: seleziona dealer dal CRM, assegna messaggio per archetipo, invia Day 1
- **agent-responder**: response-analyzer evoluto — risponde autonomamente, gestisce Day 3/7
- **agent-monitor**: monitora pipeline su Telegram, alerta per escalation

### Collegamento
- Discovery → CRM → Outreach → Response → Follow-up → Monitor
- Tutto agent-first: il founder vede su Telegram, interviene solo se necessario

## STEP 4 — Sezione Dealer Landing

### Principio 7 (founder)
- Sezione dedicata nella landing (argos-automotive.pages.dev)
- Accesso riservato per dealer registrati
- Contenuti formativi: come vendere auto premium, margini, processo import
- Obiettivo: fidelizzare dealer con valore PRIMA della prima operazione

## Regole Sessione
- OGNI step richiede deep research PRIMA dell'implementazione (mai codice prima di research)
- OGNI componente va testato E2E prima di dichiararlo completato
- Agent-first: delegare a sub-agenti specializzati
- I test E2E dello step 0.1 sono BLOCCANTI — niente procede senza auto-send funzionante
- Skill e agent specifici vanno identificati, scritti, testati — enterprise level

## Documenti di Riferimento
```
Piano master:              research/s101_PIANO_AGENT_FIRST.md
Stress test report:        research/s101_stress_test_report.md
Pain points commissione:   research/s94_dealer_commissione_pain_points_comunicazione.md
Archetipi micro-dealer:    research/s99_micro_dealer_archetipo.md
Formazione integrata:      research/s99_formazione_integrata_operazione.md
Dealer su commissione:     research/s94_dealer_su_commissione_sud_italia.md
Discovery engine:          tools/dealer_discovery/
Response-analyzer:         wa-intelligence/response-analyzer.py
WA daemon:                 wa-intelligence/wa-daemon.js (iMac)
Commission classifier:     tools/dealer_discovery/commission_classifier.py
Regole comunicazione:      .claude/rules/communication.md
Memory:                    memory/MEMORY.md
```
