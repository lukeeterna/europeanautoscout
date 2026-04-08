# Validazione Architettura Response Agent v2 — Fonti Affidabili

## Riepilogo: 6/6 punti CONFERMATI (con sfumature)

| # | Claim | Verdetto | Fonte |
|---|-------|----------|-------|
| 1 | XML tags per llama-3.3-70b | OK (empirico, non ufficiale Meta) | meta-llama/llama-recipes#450, Promptfoo test |
| 2 | Regole nei primi 500 token | CONFERMATO | Liu et al. 2023 "Lost in the Middle" (TACL 2024) |
| 3 | Sliding window 6 messaggi | RAGIONEVOLE | LangChain ConversationBufferWindowMemory |
| 4 | 1 sola chiamata LLM | CONFERMATO ottimale | LangChain agent speed, Databricks design patterns |
| 5 | Validazione rule-based | SUFFICIENTE | Guardrails AI vs NeMo comparison |
| 6 | Groq ~1-2s latenza | CONFERMATO (1.9s) | Groq docs, Artificial Analysis benchmark |

## Correzioni da Applicare all'Architettura

1. **Prompt caching Groq**: system prompt identico tra chiamate = token cached non contano verso TPM. Sfruttare attivamente mantenendo il system prompt stabile.

2. **Vincolo 6,000 TPM**: con ~2100 token/richiesta, max 2-3 richieste/minuto. Se 2+ dealer rispondono nello stesso minuto, la cascade verso free models e' essenziale. Monitorare.

3. **Sliding window k=6**: parametrizzare, non hardcodare. Tuning empirico dopo primi 20 scambi reali.

4. **Tono check**: il validator rule-based NON copre tono incoerente con archetipo. Aggiungere controllo LLM solo se emerge problema in produzione (primi 20 scambi tutti in Telegram review).

## Fonti Complete

- Liu et al. 2023: https://arxiv.org/abs/2307.03172
- Groq rate limits: https://console.groq.com/docs/rate-limits
- Groq llama-3.3-70b: https://console.groq.com/docs/model/llama-3.3-70b-versatile
- Artificial Analysis benchmark: https://artificialanalysis.ai/models/llama-3-3-instruct-70b/providers
- LangChain memory: https://python.langchain.com/docs/modules/memory/types/buffer/
- Databricks agent patterns: https://docs.databricks.com/gcp/en/generative-ai/guide/agent-system-design-patterns
- Guardrails comparison: https://aicoolies.com/comparisons/guardrails-ai-vs-nemo-guardrails
- meta-llama XML discussion: https://github.com/meta-llama/llama-recipes/issues/450
