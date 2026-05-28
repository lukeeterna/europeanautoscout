# Prompt idempotente per Claude AI web (Opus 4.x) — Design AMBRA-NEXT autonomous sales agent

> **Istruzione a Luke**: copia il blocco `=== INIZIO PROMPT ===` fino a `=== FINE PROMPT ===` in claude.ai web (Opus 4.x con WebSearch attiva). Salva output integrale in `prompts/s199_claude_ai_output_v2_<data>.md`. La sessione S200 di Claude Code lo aspetta per decisione finale.
>
> **Idempotenza**: prompt autocontenuto. Niente richiede contesto previo. Puoi rieseguirlo n volte ottenendo stesso scope (output può variare per creatività).

---

=== INIZIO PROMPT ===

# Design AMBRA-NEXT — Autonomous Sales Agent B2B WhatsApp italiano (zero training fine-tuning)

## Ruolo che ti chiedo
Sei senior agentic AI engineer + sales engineer B2B Italia. Devi progettare l'evoluzione di un sistema sales agent esistente (AMBRA, reactive single-turn) verso architettura autonoma multi-turn agent loop, **mantenendo HITL gate immutato** per azioni irreversibili.

## Constraint duri (non negoziabili)
1. **Zero costi infrastruttura**. €30/mese hard cap LLM tracciato. Free-tier first (Gemini Flash, Groq, OpenRouter free). Self-hosted Ollama solo per fallback.
2. **macOS 11 Big Sur** MacBook + **iMac 2012** server (no AVX2). Python 3.13. Node v20. SQLite + DuckDB. PM2 process manager.
3. **HITL gate immutato** per: invio Day 1, modifica prezzo, creazione contratto, mark-paid. Telegram approve/reject flow.
4. **WhatsApp Business** unico canale outbound oggi (email/voice come futuro condizionato).
5. **Brand guard**: nei messaggi dealer MAI menzionare "ARGOS / CoVe / Claude / GPT / bot / LLM / automatico / Anthropic / embedding".
6. **Persona Luca Ferretti** mantenuta come front-stage (dealer vede umano).
7. **Stack-stitch first**: preferisci comporre repo GitHub esistenti (production-grade, licenza permissiva, attiva ultimo anno) invece di scrivere from-scratch. Se mancano DATI vertical (B2B auto Sud Italia), proponi proxy verticali simili (B2B SMB Italia, real estate IT, fintech IT outbound) con caveat esplicito.
8. **Output strutturato JSON-parseable** in coda al design (sezione 9).

## Stato funnel target (requisito Luke, immutabile)

```
[ARGOS scopera dealer]
  → Cold contact PROATTIVO efficace (Day 1 con esca che innesca dealer a chiedere modello)
  → Dealer chiede modello/specifica (intent VEHICLE_REQUEST captured)
  → AMBRA-NEXT lavora full funnel:
     comprensione → memoria → pianificazione → generazione →
     tool use (CoVe search, dossier PDF, contract) →
     guardrail (HITL su irreversibili) →
     apprendimento outcome →
     osservabilità (escalation Telegram)
  → CLOSED_WON (PAID) o CLOSED_LOST (motivo tracciato)
```

Il salto strategico è il primo step: Day 1 oggi chiede "2 minuti per capire come funziona?" — il nuovo Day 1 deve **innescare richiesta veicolo dal dealer** (hook proattivo). Disegna i 3 pattern di esca testabili.

## Inventario AMBRA esistente (NON re-inventare, USA cosa c'è)

23 capability già operative:
1. Intent classification 8 classi (NEGATIVE/POSITIVE/CURIOSITY/OBJ-1..5/VEHICLE_REQUEST/CONTRACT_REQUEST/MEDIA/UNKNOWN) — `response-analyzer.py:1378`
2. Pattern weighted + mixed-intent solver — `PATTERNS:1162`
3. Profanity override + negated positives
4. Entity extraction veicolo (marca/modello/budget/anno/km) — Haiku + regex
5. State machine 7 stati COLD→CONTACTED→ENGAGED→INTERESTED→CONVERTING→CLOSED_*/ARCHIVED — `state_machine.py`
6. Conversation history retrieval — `load_dealer_context()`
7. 9 archetype prompt modules (narciso/ragioniere/barone/tecnico/relazionale/conservatore/delegatore/performante/opportunista)
8. System prompt assembler modulare con branching handoff_source + cls_type
9. Template engine 10 fixed templates
10. Day 1 sender operativo (`send_day1_stile_car.py`)
11. Sequence Day 1/3/7/10/14/21/30 codificata
12. Vehicle request broker role-binding anti-hallucination
13. Target lexicon micro-dealer (commissione vocabolario)
14. Dossier PDF on-demand (CoVe + sanitizer S183-bis)
15. Contract create + sign URL workflow
16. HITL gate `auto_approve_and_send` + Telegram HOLD
17. Anti-ban: bridge_outbound single-writer + business hours
18. ResponseValidator 7 check (json/banned_words/fee_leak/invented_prices/vehicle_hallucination/broker_lexicon_ban/repetitions)
19. Brand guard FORBIDDEN_WORDS
20. LLM cost tracking per dealer + model
21. Cascade LLM 5 livelli (Gemini→Groq→OpenRouter free→Gemini Lite→Ollama)
22. Audit + replay (analyzed_at + messages table preservata)
23. Mystery-shopper handoff mode (Layer 2 cliente fittizio → Layer 3 dealer warm)

## 17 Gap target da coprire (output deve mappare ognuno)

G1 Persona detection automatica da segnali (sito web, social, stock, language style) — oggi archetype = parametro esterno
G2 Sentiment continuo turn-by-turn (raffreddamento detection)
G3 Language style mirror (formale/dialettale, brevità)
G4 Long-term episodic memory cross-dealer
G5 Multi-step planning agent loop (3-5 mosse avanti)
G6 Goal hierarchy + next-best-action policy
G7 Channel orchestration (WA + email + voice futuro)
G8 Price negotiation bounded handler (range pre-approvati)
G9 Close trigger automatico
G10 Calendar/follow-up scheduler dinamico (adattivo, non fisso)
G11 Outcome tracking + A/B in-the-loop
G12 Pattern mining cross-dealer (chiusi vs persi)
G13 Confidence-based escalation dinamica (HITL non binario)
G14 **Cold contact hook proattivo** che innesca "dealer chiede modello" (requisito Luke)
G15 Opt-out persistence (P3 BLOCKER S199 fix imminente)
G16 CONTRACT_REQUEST pattern "bonifico/pagamento" (P1 BLOCKER S199 fix imminente)
G17 NEGATIVE clitici "non mi scrivere più" (P2 BLOCKER S199 fix imminente)

## Cosa devi produrre (ordine fisso, idempotente)

### Sezione 1 — Architettura agent loop (≤800 parole)
- Pattern (ReAct / Plan-and-Execute / LangGraph state machine / autonomous loop con tool use)
- Diagramma testuale step-by-step ciclo agent
- Dove gli stati AMBRA esistenti (COLD→ARCHIVED) si innestano nel loop
- Dove HITL gate si inserisce senza spezzare l'autonomia

### Sezione 2 — Stack-stitch repo GitHub (≤600 parole, ≥6 repo)
Per ogni repo: nome, link, licenza, ultima commit, ⭐ star, ruolo nell'architettura, integrazione concreta con AMBRA esistente. Almeno 6 repo distinti coprendo: agent loop, memoria episodica, persona detection, conversation routing, A/B testing, observability. **No repo abbandonati** (>12 mesi senza commit = scartati).

### Sezione 3 — Cold contact hook proattivo Day 1 (≤500 parole)
3 pattern testabili di esca Day 1 che innescano dealer a chiedere modello. Per ognuno: messaggio italiano <5 righe, archetipo target (NARCISO/RAGIONIERE/BARONE), psicologia trigger, metrica successo (reply rate, VEHICLE_REQUEST intent rate, time-to-vehicle-ask), come misurarla con AMBRA esistente. **Rispetta brand guard** (no ARGOS/automatico/algoritmo).

### Sezione 4 — Mappatura 17 Gap → soluzione (tabella)
Per ogni G1-G17:
- Componente nuovo o estensione di componente AMBRA esistente
- Repo GitHub coinvolto (se applicabile)
- Effort stima (S/M/L)
- Dipendenze
- Priorità (P0/P1/P2)

### Sezione 5 — DATI quantitativi
Se ammetti onestamente "[DATI MANCANTI per vertical B2B auto Sud Italia]" su uno specifico KPI, PROPONI proxy: vertical simile + numero + fonte + caveat. Esempi accettabili: B2B SMB Italia outbound, real estate IT cold contact, fintech B2B Italia, automotive remarketing B2B EU. Almeno 5 metriche con almeno 1 fonte verificabile (URL) ciascuna o caveat esplicito. **No "McKinsey 2024" senza link.**

### Sezione 6 — Conversation design Day 1-30 (≤700 parole)
Flow concreto messaggio per messaggio per 3 archetipi (NARCISO, RAGIONIERE, RELAZIONALE), 30 giorni. Include: trigger transizione stato AMBRA, tool calls (CoVe search, dossier, contract), HITL gate trigger, fallback NEGATIVE/OBJ.

### Sezione 7 — Rischi + mitigazioni (≤300 parole, 5+ rischi)
Pattern-detection da letteratura agent autonomi (hallucination loop, reward hacking, escalation failure, cost explosion). Mitigazione concreta per ognuno.

### Sezione 8 — Roadmap 4 sprint (≤200 parole)
Sprint 1 = MVP cold contact hook + persona detection auto. Sprint 2-4 = resto. Definition of Done per sprint. **Sprint 1 NON deve includere refactor S199 P1+P2+P3** (in corso parallelo).

### Sezione 9 — Output JSON-parseable (obbligatorio)
```json
{
  "version": "v2",
  "date": "<YYYY-MM-DD>",
  "agent_loop_pattern": "<ReAct|PlanExecute|LangGraph|Custom>",
  "repos_stitched": [
    {"name":"","url":"","license":"","last_commit":"","stars":0,"role":""}
  ],
  "cold_contact_hooks": [
    {"id":"H1","archetype":"","msg":"","trigger_psychology":"","metric":""}
  ],
  "gap_coverage": [
    {"gap":"G1","solution":"","repo":"","effort":"S|M|L","priority":"P0|P1|P2"}
  ],
  "metrics": [
    {"kpi":"","value":"","source_url":"","caveat":""}
  ],
  "risks": [
    {"risk":"","mitigation":""}
  ],
  "roadmap": [
    {"sprint":1,"scope":"","DoD":""}
  ],
  "open_questions_for_luke": ["..."]
}
```

## Anti-pattern da NON ripetere (storico ARGOS)
- "Production ready" senza test reali su TEST_FOUNDER fisico
- API/standard/repo inventati senza link verificabile
- Comandi che rompono Big Sur (es. npm major upgrade)
- Liste A/B/C/D senza raccomandazione singola motivata
- Design >2500 parole sezione 5 = 70% "[DATI MANCANTI]"
- Re-inventare componenti AMBRA esistenti (vedi inventario 23 capability)

## Vincoli stilistici output
- Italiano. Numero parole rispettato per sezione.
- Sezione 9 JSON sempre presente in coda, validabile.
- Citazioni repo: nome + URL GitHub + licenza + ultima commit + ⭐.
- DATI senza URL verificabile = caveat esplicito "[DATI MANCANTI proxy=X]".

=== FINE PROMPT ===
