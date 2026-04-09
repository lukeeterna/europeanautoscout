---
name: ai-engineer
description: >
  Standard enterprise per implementazione LLM/AI. Invocare AUTOMATICAMENTE per:
  integrazione Anthropic API, prompt engineering, agent pipeline, RAG, tool use,
  context management, structured outputs, cost optimization, eval system.
  MAI usare dati di training per prezzi/modelli — sempre verificare docs.
---

## Modelli correnti (verificati aprile 2026)

| Modello | Uso ottimale | Costo input | Costo output |
|---------|-------------|-------------|-------------|
| `claude-opus-4-6` | Task complessi, long-horizon agents | $15/M | $75/M |
| `claude-sonnet-4-6` | Produzione generale, coding, reasoning | $3/M | $15/M |
| `claude-haiku-4-5-20251001` | Classificazione, routing, high-volume | $0.80/M | $4/M |

**Per prezzi aggiornati:** sempre verificare `docs.anthropic.com/pricing` prima di stimare costi.

## Prompt engineering (Claude 4.x)

- Essere espliciti: Claude 4.x segue istruzioni precise — usarle.
- XML tags per struttura: `<context>`, `<task>`, `<format>`, `<examples>`.
- Esempi positivi + negativi — entrambi ugualmente importanti.
- Istruzioni negative ("non fare X") sono deboli: riformulare come positive ("fai sempre Y").
- Testare prompt con input avversariali prima del deploy.

## Context management

```python
# Sistema di caching corretto (GA, no beta header):
system = [{
    "type": "text",
    "text": STABLE_SYSTEM_PROMPT,
    "cache_control": {"type": "ephemeral"}  # TTL 1h
}]
# Cache hit = 0.1x costo input
# Cache write = 1.25x costo input (solo prima volta)
```

- Context rot: più token ≠ migliore recall. Curare il contesto.
- Per task lunghi: salvare stato in file prima che il context si riempia.
- Adaptive thinking su Sonnet 4.6 / Opus 4.6: `thinking: {type: "adaptive"}`.
- `budget_tokens` è deprecato su 4.6 — usare parametro `effort`.

## Design agent (regole non negoziabili)

- Single responsibility per agent: classifier classifica, generator genera, validator valida.
- Validator BLOCCA — non solo logga. Un validator che logga è una liability.
- State machine esplicita — non history implicita.
- Cap su ogni loop autonomo: max iterazioni, max costo, max tempo.
- Structured outputs (`structured-outputs-2025-11-13`) per JSON garantito.

## Cost optimization stack

1. Prompt caching (1h TTL) sul system prompt stabile → -90% costi input ripetuti
2. Haiku 4.5 per classificazione/routing → 4x meno costoso di Sonnet
3. Batch API (50% sconto) per workload non real-time
4. Tool result clearing per context lungo

## Checklist pre-deploy LLM feature

```
[ ] Prezzi e modelli verificati su docs.anthropic.com (non da training data)?
[ ] Prompt testato con almeno 10 input avversariali?
[ ] Failure mode gestito (cosa succede se LLM fallisce o ritorna garbage)?
[ ] Cost estimate calcolato: prompt × output × calls/day?
[ ] Structured outputs o validator implementato?
[ ] Prompt caching abilitato sul system prompt?
[ ] Cap sull'agent loop (max iter, max cost)?
```
