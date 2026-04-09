# DEEP_RESEARCH_SKILL.md
## Protocollo di Ricerca Hyperesaustiva per Claude Code
### Fonte: Anthropic Engineering Blog + docs.anthropic.com (verificato 09/04/2026)

---

## QUANDO ATTIVARE QUESTA SKILL

Attivare PRIMA di:
- Pianificare qualsiasi architettura software
- Scegliere uno stack tecnologico
- Scrivere codice che dipende da versioni/API/costi specifici
- Valutare alternative (es. SQLite vs DuckDB, Groq vs Haiku)
- Qualsiasi task dove "dati sbagliati = architettura sbagliata"

NON attivare per:
- Task puramente implementativi con spec già definite
- Refactoring su codebase nota
- Fix di bug già analizzati

---

## ARCHITETTURA DELLA RICERCA (fonte: Anthropic Engineering, giugno 2025)

### Il principio fondamentale

Anthropic ha misurato che nei sistemi multi-agent di ricerca:
- **3 fattori spiegano il 95% della varianza di performance** su BrowseComp
- **Token usage spiega l'80%** della varianza da solo
- Number of tool calls e model choice sono gli altri due fattori
- Un sistema multi-agent con Opus come lead + Sonnet come subagent **supera del 90.2%** un singolo Opus in ricerca complessa

**Implicazione pratica:** la qualità della ricerca è proporzionale ai token spesi. Non c'è shortcut.

### Pattern: Orchestrator + Workers paralleli

```
LeadResearcher (Opus 4.6 o Sonnet 4.6)
  ├── Analizza query
  ├── Salva piano in Memory (prima del context overflow)
  ├── Spawna N subagent in PARALLELO (non seriali)
  │   ├── SubAgent-1: aspetto A (3-10 tool calls)
  │   ├── SubAgent-2: aspetto B (3-10 tool calls)
  │   └── SubAgent-N: aspetto C (3-10 tool calls)
  ├── Sintetizza risultati
  ├── Decide se servono più round
  └── CitationAgent: verifica e cita ogni claim
```

**Attenzione:** Anthropic misura che gli agent usano ~4x più token delle chat normali,
e i sistemi multi-agent usano ~15x più token. È il prezzo della qualità.

---

## PROTOCOLLO IN 6 FASI

### FASE 1 — QUERY DECOMPOSITION (prima di qualsiasi ricerca)

Prima di aprire un browser o chiamare una API, il Lead deve:

```
1. Identificare le dimensioni della domanda:
   - Dimensione TECNICA: come funziona X?
   - Dimensione COSTO: quanto costa X in produzione?
   - Dimensione ALTERNATIVA: cosa esiste invece di X?
   - Dimensione TEMPORALE: X è ancora valido oggi (aprile 2026)?
   - Dimensione TRADE-OFF: X vs Y in questo contesto specifico?

2. Assegnare priorità a ogni dimensione (alta/media/bassa)

3. Definire per ogni subagent:
   - Obiettivo specifico (non vago)
   - Output format atteso
   - Tool da usare (web_search, web_fetch, docs specifici)
   - Task boundary (cosa NON deve cercare per evitare overlap)
```

**Errore da evitare (documentato da Anthropic):**
"research the semiconductor shortage" → troppo vago → subagent duplicano lavoro.
Corretto: "Find data on automotive chip shortage 2021-2023, focus on production numbers and OEM impact. Do NOT cover 2024+ or consumer electronics."

### FASE 2 — SCALING RULES (obbligatorio)

Anthropic ha embeddate queste regole direttamente nei prompt del sistema Research:

| Complessità query | N subagent | Tool calls per subagent |
|-------------------|------------|------------------------|
| Fact semplice | 1 | 3-5 |
| Confronto diretto | 2-4 | 10-15 ciascuno |
| Ricerca complessa | 5-10+ | 15-25 ciascuno, divisi chiaramente |

**Errore da evitare:** spawnare 50 subagent per query semplici (failure mode documentato
nelle prime versioni del sistema Research di Anthropic).

### FASE 3 — SEARCH STRATEGY (start wide, then narrow)

Da Anthropic Engineering:
> "Search strategy should mirror expert human research: explore the landscape before drilling into specifics."

```
Ordine obbligatorio:
1. Query BREVE e LARGA (1-3 parole) → capire il landscape
2. Valutare cosa è disponibile
3. Query progressivamente più specifiche
4. web_fetch sulle pagine più rilevanti (non solo snippet)

SBAGLIATO: "claude haiku 4.5 pricing per million tokens march 2026"
GIUSTO:    "haiku 4.5 pricing" → poi fetch docs.anthropic.com/pricing
```

**Regola sulle fonti (Anthropic, testato in produzione):**
Gli agent tendono a preferire contenuti SEO-ottimizzati su fonti autorevoli ma meno rankkate.
Inserire esplicitamente nel prompt: "prefer primary sources (official docs, academic PDFs,
official announcements) over secondary aggregators."

### FASE 4 — INTERLEAVED THINKING (per ogni tool result)

Anthropic: "Subagents use interleaved thinking after tool results to evaluate quality,
identify gaps, and refine their next query."

Dopo ogni tool call, il subagent deve pensare:
```
- Questo risultato risponde alla mia domanda? (qualità)
- Ci sono gap? Cosa manca? (completezza)
- La fonte è primaria o secondaria? (affidabilità)
- Devo fare un'altra query o ho abbastanza? (efficienza)
- Questo contraddice qualcosa trovato prima? (conflitto)
```

Su Sonnet 4.6 e Opus 4.6: `thinking: {type: "adaptive"}` — il modello calibra
automaticamente quanto pensare. Non usare `budget_tokens` (deprecato).

### FASE 5 — SOURCE TRIANGULATION (confronto fonti)

Per ogni claim che finirà nel report finale:

```python
# Regola di triangolazione:
# Claim CRITICO (influenza architettura): minimo 3 fonti indipendenti
# Claim IMPORTANTE (influenza scelta tool): minimo 2 fonti
# Claim DI CONTESTO: 1 fonte primaria sufficiente

# Gerarchia fonti (ordine decrescente affidabilità):
1. docs.anthropic.com / ufficiale vendor
2. Engineering blog ufficiale (anthropic.com/engineering)
3. Release notes ufficiali
4. Paper peer-reviewed / benchmark pubblici con metodologia
5. Report aziendali con numeri verificabili
6. Blog tecnici con prove misurabili
7. Opinioni / comparazioni senza dati
```

**Conflitto tra fonti:** se due fonti affidabili si contraddicono, il report deve
documentare il conflitto, non scegliere arbitrariamente una versione.

### FASE 6 — CITATION AGENT (obbligatorio, non saltare)

Da Anthropic Engineering:
> "The CitationAgent processes the documents and research report to identify specific
> locations for citations. This ensures all claims are properly attributed."

Il Citation Agent verifica:
- Ogni claim numerico ha una fonte citabile con URL + data
- Nessun "secondo alcune fonti" o "si dice che" senza link
- I numeri nel report corrispondono esattamente ai numeri nelle fonti
- Le date delle fonti sono recenti rispetto alla domanda

---

## OUTPUT FORMAT OBBLIGATORIO

Ogni ricerca deve produrre un report con questa struttura:

```markdown
# [TITOLO RICERCA]
**Data:** [data esecuzione]  
**Query originale:** [testo esatto]  
**Fonti consultate:** N  
**Confidence score:** [0.0-1.0]

---

## EXECUTIVE SUMMARY (max 5 righe)
[Risposta diretta alla domanda con i numeri più importanti]

---

## DATI VERIFICATI

### [Dimensione 1: es. Costi]
| Metrica | Valore | Fonte | Data fonte |
|---------|--------|-------|-----------|
| ... | ... | [URL] | ... |

### [Dimensione 2: es. Performance]
[dati con fonte inline per ogni numero]

### [Dimensione N]
...

---

## CONFLITTI TRA FONTI
[Se trovati: documenta la discrepanza, non scegliere]

---

## GAP DI CONOSCENZA
[Cosa non è stato trovato o non è verificabile]

---

## RACCOMANDAZIONE BASATA SU DATI
[Solo dopo aver presentato i dati. Mai raccomandazione prima dei dati.]

---

## FONTI COMPLETE
1. [URL] — [titolo] — [data accesso] — [tipo: primaria/secondaria]
2. ...
```

**Regola critica:** se un numero non ha fonte, non va nel report.
"Circa €2-3/mese" senza fonte = da rimuovere o marcare come stima non verificata.

---

## EVALUTAZIONE DELLA RICERCA (LLM-as-judge)

Anthropic usa questo rubric per valutare i propri output di ricerca:

```
1. ACCURATEZZA FATTUALE (0-1): i claim matchano le fonti?
2. ACCURATEZZA CITAZIONI (0-1): le fonti citate supportano i claim?
3. COMPLETEZZA (0-1): tutti gli aspetti richiesti sono coperti?
4. QUALITÀ FONTI (0-1): fonti primarie usate vs aggregatori?
5. EFFICIENZA TOOL (0-1): tool usati un numero ragionevole di volte?

Score minimo per pubblicare il report: media ≥ 0.7
Score sotto 0.5 su qualsiasi dimensione: rifai quella parte
```

---

## GUARDRAILS ANTI-FAILURE

Failure modes documentati da Anthropic nel sistema Research:

| Failure mode | Sintomo | Fix |
|-------------|---------|-----|
| Endless search | Agent cerca fonti non esistenti | Limite tool calls esplicito nel prompt |
| Subagent overlap | 2+ agent fanno le stesse query | Task boundary obbligatori nella decomposizione |
| SEO bias | Preferisce content farm su fonti autorevoli | "prefer primary sources" nel prompt |
| Effort misalignment | 50 subagent per domanda semplice | Scaling rules embedded nel prompt |
| Context overflow | Lead agent perde il piano | Salvare piano in Memory prima di iterazioni |
| Stale data | Risposta basata su informazioni di 12 mesi fa | Ogni fonte deve avere data, filtrare per recency |

---

## IMPLEMENTAZIONE PER CLAUDE CODE

### Subagent file: deep-researcher.md

```yaml
---
name: deep-researcher
description: >
  Ricerca hyperesaustiva multi-source con triangolazione fonti.
  Attivare PRIMA di pianificare architetture o scegliere stack.
  Restituisce report con numeri concreti e fonti verificate.
  NON fare assunzioni senza dati. NON stimare senza fonte.
model: claude-sonnet-4-6
tools: WebSearch, WebFetch, Bash
memory: project
---

Sei un ricercatore sistematico. Per ogni task:

1. Decomposizione: dividi la domanda in 3-5 sotto-domande specifiche
2. Scaling: applica le scaling rules (1/2-4/5+ subquery per complessità)
3. Search strategy: inizia largo, poi restringi
4. Source triangulation: claim critici = 3 fonti, importanti = 2
5. Output: solo numeri con fonte. Mai stime non attributite.

FONTI PRIMARIE OBBLIGATORIE per task tecnici Anthropic:
- docs.anthropic.com (API, modelli, pricing)
- anthropic.com/engineering (architetture, benchmarks)
- anthropic.com/news (release ufficiali)

Formato output: tabelle con colonne Metrica | Valore | Fonte | Data.
```

### Integrazione CLAUDE.md

```markdown
## Prima di pianificare o scrivere codice

Attiva il subagent `deep-researcher` per qualsiasi domanda dove
dati sbagliati potrebbero portare a scelte architetturali sbagliate.

Esempi obbligatori:
- "qual è il costo reale di X in produzione?"
- "X è ancora supportato/disponibile?"
- "confronto tra A e B per questo use case"
- "quale versione di X è compatibile con Y?"

Il researcher restituisce un report. Usa SOLO i numeri del report,
mai quelli del training data che potrebbe essere stale.
```

---

## NUMERI CHIAVE DAI DOCS (riferimento rapido, verificato 09/04/2026)

| Metrica | Valore | Fonte |
|---------|--------|-------|
| Multi-agent vs single-agent research | +90.2% performance | anthropic.com/engineering/multi-agent-research-system |
| Token usage: chat vs agent | ~4x | idem |
| Token usage: chat vs multi-agent | ~15x | idem |
| BrowseComp variance spiegata da token usage | 80% | idem |
| Taglio ricerca con tool calls paralleli | fino a 90% tempo | idem |
| Prompt caching TTL | 1h (GA, no beta header) | docs.anthropic.com/prompt-caching |
| Sonnet 4.6 pricing | $3/M input, $15/M output | docs.anthropic.com/pricing |
| Opus 4.6 pricing | $15/M input, $75/M output | idem |
| Haiku 4.5 pricing | $0.80/M input, $4/M output | idem |
| Context window Sonnet 4.6 / Opus 4.6 | 1M token (standard) | docs.anthropic.com/models |
| Max output Opus 4.6 (Batch API) | 300K token (beta header: output-300k-2026-03-24) | release-notes |
| Adaptive thinking | GA, nessun beta header | docs.anthropic.com/extended-thinking |
| `budget_tokens` | DEPRECATO su 4.6 | idem |
| Structured outputs | beta: structured-outputs-2025-11-13 | release-notes |
| Web fetch dynamic filtering | richiede code execution tool | docs.anthropic.com/web-fetch-tool |
| Citations su web fetch | opzionale: `"citations": {"enabled": true}` | idem |
| Citations su web search | sempre abilitate | idem |
