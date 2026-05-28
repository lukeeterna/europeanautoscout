# Prompt Claude AI (web) — Design autonomous sales agent ARGOS (codename TBD, sostituirà AMBRA)

> **Uso**: incolla il blocco "PROMPT DA INVIARE" qui sotto in claude.ai web (modello Opus 4 o superiore, NO Code).
> **Output atteso**: design completo + DATI quantitativi verificati + bibliografia.
> **Prossima sessione ARGOS**: incrocio output Claude AI ↔ research mia basata su DATI (WebSearch attuale + benchmark verificati).
> **Domanda Luke alla AI**: chiedere DATI espliciti per ogni claim. Rifiutare risposte "verosimili senza fonte".

---

## PROMPT DA INVIARE A CLAUDE AI (copia-incolla integrale tra le linee `===`)

```
===

Sei un senior architect di sistemi conversazionali B2B autonomi. Devo progettare il successore di AMBRA, il sales agent reactive di ARGOS Automotive, trasformandolo in un sales agent COMPLETAMENTE AUTONOMO che possa operare con human-in-the-loop solo su scelte irreversibili (es. firma contratto, escalation legale), NON su ogni messaggio.

## CONTESTO BUSINESS

**ARGOS Automotive** = scouting B2B vehicle import EU→IT. Trovo BMW/Mercedes/Audi/Porsche/Range Rover su 28 portali EU (DE/NL/BE/AT/FR/SE), confronto prezzo netto vs prezzo IT, propongo ai dealer family-business Sud Italia (30-80 auto stock) opportunità con margine €3-8k. Success-fee €800-1200 per veicolo importato (zero upfront, pago io upfront i costi).

**Persona pubblica**: "Luca Ferretti", reale, volto trovabile su Google. Brand: ARGOS™.

**Target dealer**: 5 archetipi mappati (NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE). Cultura Sud Italia: prima fiducia personale, poi business. Tasso di risposta atteso B2B Sud Italia cold WhatsApp = ?

**Competitor diretti**:
- Bolidem (B2C, 219 recensioni 4.8/5, fee upfront €1270)
- Autotedesche.it (B2C, 162 recensioni 4.9/5, 1 persona, fee upfront)
- Importami.com (B2C, fee 4% min €750+IVA upfront)
- Nessun competitor fa B2B Sud Italia con scouting proattivo + success-fee = white space confermato

**Gap critico ARGOS**: zero recensioni, zero track record visibile. Primo dealer = atto di fede + vale 3-5 dealer referral.

**Stack tecnico esistente**: SQLite (dealer_network.sqlite + bridge.sqlite), Python 3.13 backend, Node.js WA daemon (whatsapp-web.js su iMac 2012 sempre acceso, no AVX2), Cloudflare Workers per contract sign-flow, dashboard Flask:8080 con login auth.

**Stack LLM attuale** (cascade fallback):
1. Gemini 2.5 Flash (free tier 1500 req/min)
2. Groq llama-3.3-70b-versatile
3. OpenRouter Anthropic Haiku 4.5 (paid)
4. Gemini Lite
5. Ollama locale (fallback offline)

**Vincoli hard**:
- Budget LLM €30/mese tracked
- macOS 11 Big Sur su dev MacBook (no AVX2, no librerie ML moderne)
- iMac 2012 server: no GPU, no AVX2, Python 3.13 ok
- ZERO costi extra (no SaaS paid, no subscription, no nuovo hardware)
- Italiano nativo (no traduzioni meccaniche)
- GDPR-compliant (no PII fuori UE non motivata)

## STATO AMBRA OGGI (cosa GIÀ funziona — da preservare nel nuovo design)

File principale: `wa-intelligence/response-analyzer.py` (2420 righe). Architettura reactive: dealer scrive → daemon Node forwarda → Python classifier → LLM cascade → ResponseValidator → save pending_reply → HITL approve dashboard → bridge_outbound → daemon invia WA.

**Features già implementate:**

1. **Intent classifier keyword-based** (12 classi)
   - NEGATIVE, POSITIVE, CURIOSITY, OBJ-1..5, VEHICLE_REQUEST, CONTRACT_REQUEST, NEUTRAL/UNKNOWN
   - Pattern italiano informale + dialetto Sud (es. "ci sto", "mandi pure", "fatti sentire")
   - CONTRACT_REQUEST gated da state (DOSSIER_SENT/DAY3_SENT) per evitare falsi positivi
   - **GAP S198 noto**: manca "bonifico/pagamento" in CONTRACT_REQUEST; manca "non mi scrivere/contattare più" con pronome clitico in NEGATIVE

2. **State machine dealer**
   - PENDING → DAY1_SENT → DAY3_SENT → DOSSIER_SENT → CONTRACT_DRAFT → CONTRACT_SIGNED → PAID → CLOSED_OK
   - Branch: → CLOSED_NO / CLOSED_NO_RESPONSE / OBJECTION_HANDLED / VEHICLE_REQUESTED

3. **LLM cascade con cost tracking**
   - Switching automatico al primo errore/rate-limit
   - Token usage loggato per dealer in `cove_tracker.duckdb`
   - Circuit breaker per provider (3 fail in 5 min → skip)

4. **ResponseValidator (5 check pre-send)**
   - `_check_json_format` — output LLM strutturato valido
   - `_check_banned_words` — no menzioni AI/algoritmo/CoVe/Claude/Anthropic/embedding/RAG/bot/automatico/LLM
   - `_check_fee_leak` — no fee €800 in primo contatto
   - `_check_invented_prices` — no prezzi inventati da LLM
   - `_check_repetitions` — no overlap con ultimi 3 outbound
   - `_check_vehicle_hallucination` — VEHICLE_REQUEST → no veicolo specifico inventato (modulo `vehicle_request_broker`, role info-broker NOT seller)
   - `_check_broker_lexicon_ban` — VEHICLE_REQUEST → no lessico marketing/vendita

5. **Template-first architecture**
   - 47 template (`templates.py`) tested per intent×state
   - Template SCELTO prima di LLM. LLM solo se nessun template matcha (cost saving + consistency)
   - Validator blocca template fill incompleti

6. **Prompt injection defense**
   - Sanitize input dealer (12 pattern: "ignora istruzioni", "you are now", "dimentica precedenti", etc.)
   - Cap length 2000 char

7. **Anti-spam cooldown intelligente**
   - 24h cooldown dopo ultimo outbound SOLO se dealer non ha risposto
   - Bypass se conversazione attiva (last inbound > last outbound)
   - NEGATIVE bypassa sempre cooldown (segnale chiusura)

8. **HITL gate dashboard (post-S190)**
   - Tutte le pending_replies → dashboard:8080 con login auth
   - Luke approve/reject/edit prima di invio
   - audit_log completo: REPLY_APPROVED, BRIDGE_INSERTED, etc.
   - Gate immutabile per scelte irreversibili (contract create + send sign_url)

9. **Bridge_outbound single-writer canonical queue**
   - Solo `bridge_outbound` insert → daemon WA polla → invia → marca sent
   - UNIQUE constraint anti-duplicati: (deal_id, target_phone, template_phase) WHERE sent IS NULL
   - Eccezioni documentate (Day7 voice diretto, /send force=true)

10. **Workflow contratto eBay-style (CONTRACT_REQUEST)**
    - Dealer post-DOSSIER scrive intent acquisto
    - System crea contract draft via Cloudflare Worker → genera sign_url
    - HITL approve → invia sign_url WA
    - Dealer firma form web → status AWAITING_DELIVERY → IBAN_SENT → PAID

11. **Persona system prompt per archetype**
    - 5 versioni system prompt (NARCISO/BARONE/RAGIONIERE/TECNICO/RELAZIONALE + DEFAULT)
    - Lessico calibrato per archetipo (es. RAGIONIERE = numeri + ROI, NARCISO = ego + esclusività)

12. **Knowledge base statica**
    - `argos_knowledge_base.md` (markdown chunked, retrieved per cls_type + obj_code)
    - Veicoli reali in stock (`get_relevant_vehicles` query DuckDB filtrata)

13. **Telegram HOLD notification**
    - Su CONTRACT_REQUEST + qualsiasi pending → notifica Telegram a Luke con preview
    - Link diretto a dashboard:8080 approve

14. **Audit log strutturato**
    - Ogni decisione (classify, approve, reject, send, fail) → audit_log tabella SQLite
    - Cost tracking LLM per dealer + per session

## GAP DA COLMARE (cosa il nuovo agente DEVE fare in più)

L'agente deve diventare **autonomo** = decide e agisce, HITL solo per scelte irreversibili. Servono questi salti qualitativi:

A. **Proattività multi-touchpoint** — oggi AMBRA è reactive (risponde se dealer scrive). Nuovo: orchestrazione sequenza Day 1/3/7/10/14/21/30 autonoma, decidendo timing + canale + contenuto basato su signal dealer (silenzio = trigger Day7 voice + Day14 referral; primo segnale interesse = accelera DOSSIER).

B. **Persona detection adattiva real-time** — oggi persona_type è settato manualmente. Nuovo: inferenza archetipo dai PRIMI 2-3 messaggi dealer (lessico, ritmo, formalità, focus prezzo vs garanzia vs esclusività) + ri-calibrazione continua se signal cambia.

C. **Empathy & sentiment modeling** — oggi LLM genera reply ma non c'è modello sentiment esplicito. Nuovo: detection emozione dealer (frustrato, entusiasta, scettico, distratto) + adattamento tono response (es. dealer frustrato → no pitch, solo ascolto + domanda aperta).

D. **Negoziazione autonoma con limiti hard** — oggi CONTRACT_REQUEST → human approve. Nuovo: agente può negoziare prezzo entro range pre-approvato (es. ±€500 dal listino, fee fissa €800), escalation a HITL solo fuori range o controproposta strutturale.

E. **Memoria long-term cross-conversation** — oggi load_dealer_context legge per dealer corrente. Nuovo: pattern recognition cross-dealer (es. "i dealer NARCISO Catania chiudono a 14gg con vocale + foto interni", "i RAGIONIERE Bari rispondono a numeri tabellari").

F. **Scaltrezza tattica = strategia mossa successiva** — oggi è 1-shot reply. Nuovo: pianificazione 3-5 mosse avanti (chess-like) con considerazione dello stato dealer + opportunity inventory. Es. "se dealer non risponde a Day3 ma ha aperto sign_url Day1, invia caso studio simile Day5 con domanda chiusa".

G. **Human-like timing & jitter** — oggi invio immediato post-approve. Nuovo: timing realistico (no risposta in 2 secondi alle 3 di notte, no 7 messaggi consecutivi, jitter umano 30s-15min basato su context conversation).

H. **Conoscenza estesa settore auto (verticale, non generica)**:
   - Prezzi listino IT vs EU per modello/anno/km (price index aggiornato)
   - Trade-in dynamics regione (es. Puglia preferisce diesel, Campania ibrido)
   - Documenti import (CoC, fattura TD17/18/19 reverse charge, blocco TARGA EU, ANTS Francia)
   - Tempi realistici (10-15gg consegna DE→IT, +5gg pratiche immatricolazione)
   - Garanzie costruttore residue (no Handlergarantie, solo costruttore UE)
   - Anomalie comuni (km scalati, sale, riverniciature, incidente non dichiarato)

I. **Continuous learning da outcomes**
   - Ogni conversazione finita (CLOSED_OK / CLOSED_NO) → feedback loop
   - Re-train (o re-prompt) su pattern winning vs losing
   - A/B test automatico su variazioni messaggio Day 1 (entro vincolo HITL approve)

J. **Multi-channel orchestration**
   - WA primario, ma fallback email per dealer non rispondenti dopo Day 14
   - Telefono diretto Day 30 (script preparato per Luke fisico)
   - LinkedIn DM Day 21 se WA muto + profilo dealer attivo

K. **Calibrazione fiducia (trust calibration)**
   - Track signal trust dealer per dealer: ha aperto sign_url? ha visto dossier PDF? ha chiesto referenze?
   - Se trust < soglia → propone case study + recensioni prima del pitch veicolo
   - Se trust > soglia → salta credibility-building, va dritto al closing

L. **Self-monitoring + safety guardrails**
   - Detection drift performance (es. response rate crolla 50% → alert)
   - Kill switch se invia > 10 messaggi/h senza response umana (segnale loop)
   - GDPR opt-out persistente (no recontatto dopo opt_out flag)

## DELIVERABLE RICHIESTI DA TE (Claude AI)

Output strutturato in 6 sezioni. Per ogni claim quantitativo, **cita la fonte** (paper, benchmark, vendor whitepaper, GitHub repo, articolo industria). NO numeri "verosimili senza fonte". Se non hai DATI, dichiara esplicitamente "[DATI MANCANTI]".

### Sezione 1 — Naming & positioning
- Codename agente (4 proposte con motivazione semantica). Vincolo: italiano riconoscibile, no inglese, no acronimi tecnici.
- One-liner posizionamento interno team (max 12 parole).
- Tagline conversazionale per dealer (max 7 parole, se serve menzionarlo).

### Sezione 2 — Architettura tecnica
- Diagramma componenti (testuale, ASCII art ok)
- Choice giustificata: agent loop pattern (ReAct? Reflexion? CoT? Multi-agent orchestration?)
- Memory architecture: short-term (conversation buffer), medium-term (dealer profile), long-term (cross-dealer patterns). Tecnologie zero-cost compatibili con SQLite + macOS 11.
- Decision engine: state machine vs planner LLM vs hybrid. Trade-off con DATI.
- Tool use: quali tool il LLM può chiamare (query DuckDB, send WA, create contract, schedule follow-up).
- HITL integration: dove l'agente deve fermarsi e chiedere approve (lista esaustiva di scelte irreversibili).

### Sezione 3 — Stack LLM con DATI
- Modello primary raccomandato per ogni task (intent classify, response gen, planning, validation). Cita benchmark MT-Bench/AlpacaEval/Arena Hard se disponibili.
- Costo stimato per conversazione completa Day 1→PAID (tokens in/out × prezzo per provider). Confronta 3 setup: Gemini Flash only, Groq mix, Claude Haiku 4.5.
- Latency target per response (B2B WA aspettativa = ?). Cita ricerca UX conversational.
- Fallback offline plan (Ollama models compatibili Big Sur senza AVX2 — verifica disponibilità wheel).

### Sezione 4 — Conversation design
- Sequenza Day 1/3/7/10/14/21/30 dettagliata con:
  - Trigger (condizione entry)
  - Goal mossa
  - Template fallback se LLM gen ko
  - Branch decision tree (cosa fare se dealer risponde X, Y, Z, silenzio)
- 5 dialoghi simulati END-to-END (input dealer reale → reply agent → next step), uno per archetipo
- Pattern empathy: 8-10 mini-pattern con esempi (dealer frustrato, dealer occupato, dealer scettico, dealer entusiasta, dealer evasivo, dealer aggressivo, dealer curioso, dealer indeciso)
- Negoziazione: 3 scenari (sconto richiesto, fee challenge, condizioni pagamento) con strategy + esempio dialogo

### Sezione 5 — DATI quantitativi (cita SEMPRE fonte)
- Conversion rate benchmark sales agent autonomi B2B (case study real, NON paper teorici): cita 5+ studi con anno, vertical, % conversion baseline vs agent
- Cost-per-conversation industry benchmark conversational AI 2025-2026
- Response time aspettativa B2B WhatsApp Italia (research recente)
- Sentiment detection accuracy SoTA italiano (modelli open-source compatibili Big Sur)
- ROI calcolato: costo agente (LLM + dev time + maintenance) vs revenue addizionale stimato 12mesi su 30 dealer attivi

### Sezione 6 — Roadmap implementazione (timeline + dipendenze)
- 4 fasi sequenziali (MVP autonomous core / Multi-touchpoint orchestration / Adaptive empathy / Continuous learning)
- Per fase: feature delta, test criteria, gate decisione GO/NO-GO
- Risk register: 8-10 rischi (technical, business, ethical, GDPR) con mitigation
- Dipendenze esterne (API stability, model availability, regulatory changes)

## ANTI-PATTERN DA EVITARE (vincoli founder)

1. **Mai liste A/B/C/D su decisioni tecniche** — una raccomandazione singola motivata con DATI per ogni choice point. Solo eccezione: opzioni di SCOPE business (cosa Luke vuole), non tecniche.
2. **Mai capex hardware** — no "compra GPU/Mac nuovo". Solo free-tier + esistente.
3. **Mai claim production-ready senza test reali** — se design non testato, marca "[POC, da validare]".
4. **Mai citare API/standard inesistenti** — verifica con WebSearch se modello/library/feature esiste DAVVERO oggi (2026-05-27).
5. **Mai "best practice" generiche** — concretezza > buzzword. "Use RAG with vector DB" è inutile se non specifichi DB, embedding model, costo, integrazione codebase esistente.
6. **Mai stati PARTIAL/INTERMEDIO** — ogni gate decisione GO o NO-GO secco.
7. **Output verificato > output verosimile** — meglio 500 righe corrette che 1500 vaghe.
8. **Critica strutturale obbligatoria** — dopo ogni proposta sezione, autocritica in 4 punti (assunzioni nascoste, cosa rompe a 30/60/90gg, pattern errore noti su sistemi simili, dove sovradimensioni).

## FORMATO OUTPUT

Markdown strutturato. Sezioni numerate 1-6. Sotto-sezioni con heading H2/H3. Tabelle dove appropriato (cost comparison, conversion benchmark). Codice ASCII per diagrammi architettura.

Max output: 8000 parole. Sii esaustivo ma chirurgico. NO filler.

Inizia con: "DATI VERIFICATI AL: [data verifica fonti]"

Termina con: "DATI MANCANTI / RICERCA RICHIESTA: [lista esplicita claim non supportati da fonte verificabile, perché Luke incrocerà con la propria research]"

===
```

---

## NOTE PER LUKE (post-output Claude AI)

### Prossima sessione ARGOS (S200) — valutazione output
1. Apri output Claude AI
2. Per ogni claim quantitativo, verifica fonte (WebSearch attuale)
3. Cross-check tecnico:
   - Modelli LLM citati esistono oggi? Pricing aggiornato 2026-05?
   - Library/tool compatibili macOS 11 Big Sur senza AVX2?
   - Benchmark conversion rate reali o ipotizzati?
4. Costruisci matrix VERIFIED / DISPUTED / UNVERIFIABLE per ogni sezione
5. Decisione architettura: adottare A) intero design B) ibrido (preservare AMBRA core + aggiungere layer agentic) C) scartare e tenere AMBRA fixed

### Vincolo S199 ancora aperto
**Day 1 Stile Car 2026-06-03 deadline T-7gg** dipende da fix P1+P2 classifier (memory `s198_step7_rosso_3_5_classifier_gaps.md`). Design autonomous agent è strategy a 30-90gg, NON risolve gate Day 1 immediato. Quindi sequenza S199:
- **Track A urgente (1-2h)**: fix P1+P2 classifier + re-test 5/5 → sblocco STEP 8 E2E Luke fisico → Day 1 Stile Car
- **Track B strategy (parallel)**: valutazione output Claude AI design autonomous, decisione architettura

I due track NON si bloccano a vicenda.
