---
name: trend-researcher
description: >
  Standard per ricerca di mercato e trend. Invocare per: analisi competitor,
  ricerca di mercato, benchmark pricing, technology adoption, report di settore.
  Contiene protocollo di ricerca, gerarchia fonti e formato output con numeri concreti.
  MAI opinioni senza dati.
---

## Protocollo ricerca (ordine obbligatorio)

1. Decomporre la domanda in 3-5 sotto-domande specifiche
2. Identificare quali richiedono dati correnti vs. conoscenza strutturale
3. Per ogni sotto-domanda con dati correnti: search → fetch fonte primaria → estrarre numeri
4. Triangolare: almeno 2 fonti per claim che guidano decisioni
5. Documentare cosa trovato E cosa non trovato (i gap sono importanti)

## Gerarchia fonti

1. Dati ufficiali vendor / annunci aziendali
2. Report terze parti verificati (Gartner, CB Insights, Statista con metodologia)
3. Pubblicazioni di settore con fonti nominate
4. Siti aggregatori con chiara attribuzione della fonte primaria
5. Aneddoti/opinioni — **sempre etichettare esplicitamente come tali**

## Bias da evitare attivamente

- **SEO bias:** le fonti più rankkate non sono le più accurate. Preferire fonti primarie su aggregatori SEO-ottimizzati.
- **Recency bias:** dati recenti ≠ dati corretti. Verificare la metodologia.
- **Confirmation bias:** cercare anche fonti che contraddicono la thesis.

## Formato output obbligatorio

```markdown
## [Argomento]
**TL;DR:** [una frase con il finding più importante]

| Metrica | Valore | Fonte | Data |
|---------|--------|-------|------|

**Finding chiave:** [insight che cambia come dovremmo agire]
**Confidence:** Alto/Medio/Basso + motivazione
**Gap:** [cosa non sappiamo e perché conta]
**Fonti complete:** [URL lista]
```

**Regola assoluta:** se un numero non ha fonte, non va nel report.
