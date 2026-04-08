# S103 — Discovery Target + Build Response Agent + Stress Test Autonomo

## Contesto

S102 ha prodotto:
- Step 0.1 PASS: pipeline E2E auto-send funzionante (daemon→classifier→Groq→send→Telegram)
- Architettura response agent v2: `research/s102_RESPONSE_AGENT_ARCHITECTURE.md`
- Validazione architettura su fonti: `research/s102_architecture_validation.md` (se completata)
- 4 bug identificati e 3 fix deployati (system prompt "chi ha scritto per primo", classifier POSITIVE, no prezzi inventati)
- Feedback founder: proporre redesign architetturale, non fix incrementali

## 3 Blocchi di Lavoro (in ordine)

---

### BLOCCO 1: Discovery e Profiling Dealer Target (2-3h)
**Obiettivo: trovare i dealer GIUSTI, non tutti i dealer**

#### 1.1 Deep Research Pre-Discovery
- Leggere `tools/dealer_discovery/` — capire come funziona il discovery engine
- Leggere `tools/dealer_discovery/commission_classifier.py` — come scora i dealer
- Leggere `research/s94_dealer_su_commissione_sud_italia.md` — intelligence esistente
- Leggere `research/s100_discovery_dealer_reali.md` — 35 dealer gia' trovati
- Verificare che lo scraper Subito.it funzioni (test 1 provincia)

#### 1.2 Definire il Profilo Target Ideale
Il dealer ideale per ARGOS:
- **Su commissione** (cerca auto per i clienti, non ha stock fisso)
- **Family business** (30-80 auto, non catena)
- **Premium mix** (BMW/Mercedes/Audi nel portfolio)
- **Tutta Italia** segmentata per regione/provincia/citta' (modifica founder)

Creare un **scoring model** che pesi:
- Commission score (da Subito.it: pochi annunci, marche diverse)
- Premium affinity (% annunci premium nel portfolio)
- Digital presence (Google Reviews, Facebook, sito web)
- Accessibility (WA disponibile vs solo fisso)
- Geography (coprire tutto il territorio, non solo Sud)

#### 1.3 Lanciare Discovery
```bash
# Test su 1 provincia
python3 tools/dealer_discovery/discovery_engine.py --province foggia --dry-run

# Se OK, lanciare tutto
python3 tools/dealer_discovery/discovery_engine.py --all-priority 1
```

#### 1.4 Verificare i 5 Dealer S100
Passare nel commission_classifier: Az Auto Evolution, Autoesse, WP Cars, Expert Auto, Romanazzi.
Declassare quelli con score < 5.

#### Criterio PASS Blocco 1
- Almeno 20 dealer profilati con commission_score >= 5
- Per ognuno: nome, citta', telefono, WA, score, brand mix, archetipo
- Almeno 5 con WA disponibile (per outreach diretto)
- Copertura: almeno 3 regioni diverse

---

### BLOCCO 2: Build Response Agent v2 (3-4h)
**Obiettivo: implementare l'architettura da research/s102_RESPONSE_AGENT_ARCHITECTURE.md**

#### 2.1 Prompt Modulare (1h)
- Spezzare SYSTEM_PROMPT in 6 moduli XML in `response-analyzer.py`
- Creare `build_system_prompt(archetype, cls_type)` che assembla dinamicamente
- Target: <1000 token system prompt (da 2000+ attuali)
- Test: stessi 5 messaggi del test S102, confrontare output vecchio vs nuovo

#### 2.2 Validator Multi-Layer (1h)
- Implementare classe `ResponseValidator` con 5 check:
  - Formato JSON valido
  - Fee leak (menzionata senza richiesta)
  - Prezzi inventati (non nel contesto veicolo)
  - Ripetizioni (frasi gia' inviate)
  - Banned words
- Integrare nel flusso: dopo call_llm(), prima di save_pending_reply()
- Strategia: 1 retry poi template fallback

#### 2.3 Pipeline CoVe → LLM (2h)
- Popolare `_vehicle_context` con veicoli reali da DuckDB
- Per VEHICLE_REQUEST: query top 3 PROCEED per marca/budget
- Per primo contatto: pre-caricare veicoli basati su brand affinity dealer
- Formattare come testo strutturato nel prompt

#### 2.4 Sliding Window (30min)
- Ampliare da LIMIT 5 a LIMIT 7 (sliding window 6 + messaggio corrente)
- Aggiungere summary rule-based per messaggi precedenti alla window
- Test: verificare che l'LLM non ripeta frasi gia' inviate

#### Criterio PASS Blocco 2
- Prompt modulare assemblato dinamicamente per archetipo
- Validator blocca: fee leak, prezzi inventati, ripetizioni
- LLM risponde con dati reali CoVe (non inventati)
- Deploy su iMac con rsync atomico

---

### BLOCCO 3: Stress Test Autonomo "Cattivo" (1-2h)
**Obiettivo: simulare i 10 scenari piu' difficili che un dealer puo' mandare**

#### 3.1 Scenari da Testare
Inviare al sistema (via daemon test) questi messaggi simulando dealer diversi:

| # | Messaggio | Expected | Cosa verifica |
|---|-----------|----------|---------------|
| 1 | "Ma chi cazzo sei?" | NEGATIVE, chiusura elegante | Gestione insulto |
| 2 | "Quanto costa il servizio?" | CURIOSITY, risposta fee | Fee al momento giusto |
| 3 | "Ho un cliente che cerca una BMW X3 2022 budget 35k" | VEHICLE_REQUEST, dati reali CoVe | Pipeline veicoli |
| 4 | "Non mi fido, come faccio a sapere che non e' una truffa?" | OBJECTION, credibilita' | Trust building |
| 5 | "Ci penso e ti faccio sapere" | SOFT_NO, porta aperta | Non insistere |
| 6 | "Gia' importo dalla Germania da solo" | OBJECTION, differenziale | Competitive handling |
| 7 | "Mandami un esempio concreto" | POSITIVE, veicolo reale | Dati reali non inventati |
| 8 | [foto di un annuncio] | MEDIA, riconoscimento | Gestione immagini |
| 9 | "ok" (dopo 3 scambi) | POSITIVE, next step | Conversazione stateful |
| 10 | "Sei un bot?" | CURIOSITY, risposta naturale | Anti-bot detection |

#### 3.2 Automazione Test
Creare script `tools/stress_test_autonomous.py`:
- Invia messaggio test via daemon API
- Attende risposta (polling pending_replies)
- Verifica: classificazione corretta, no violazioni validator, tono coerente
- Output: report con PASS/FAIL per ogni scenario + testo risposta

#### 3.3 Scoring Qualita'
Per ogni risposta, valutare (manualmente o con regole):
- Classificazione corretta? (PASS/FAIL)
- Dati inventati? (PASS/FAIL)
- Fee menzionata quando non richiesta? (PASS/FAIL)
- Tono coerente con archetipo? (1-5)
- Risposte ripetitive? (PASS/FAIL)
- Risposta naturale (non da bot)? (1-5)

#### Criterio PASS Blocco 3
- 10/10 scenari testati
- 0 prezzi inventati
- 0 fee leak
- 0 banned words
- Classificazione corretta >= 8/10
- Score tono >= 3.5/5 medio

---

## Documenti di Riferimento
```
Architettura response agent:   research/s102_RESPONSE_AGENT_ARCHITECTURE.md
Validazione architettura:      research/s102_architecture_validation.md
Piano master:                  research/s101_PIANO_AGENT_FIRST.md
Discovery engine:              tools/dealer_discovery/
Commission classifier:         tools/dealer_discovery/commission_classifier.py
Response-analyzer:             wa-intelligence/response-analyzer.py
Dealer su commissione:         research/s94_dealer_su_commissione_sud_italia.md
Discovery S100:                research/s100_discovery_dealer_reali.md
Archetipi micro-dealer:        research/s99_micro_dealer_archetipo.md
Pain points:                   research/s94_dealer_commissione_pain_points_comunicazione.md
Regole comunicazione:          .claude/rules/communication.md
Memory:                        memory/MEMORY.md
```

## Regole Sessione
- OGNI blocco richiede deep research PRIMA dell'implementazione
- Discovery PRIMA di build — servono dealer reali per testare
- Build PRIMA di stress test — serve l'agent v2 per testare
- Stress test "cattivo" — simulare il dealer piu' difficile possibile
- Se un blocco fallisce, NON procedere al successivo
- Agent-first: il founder vede su Telegram, interviene solo se necessario
- Proporre redesign architetturale quando servono 3+ fix (feedback S102)
