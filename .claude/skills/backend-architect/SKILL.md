---
name: backend-architect
description: >
  Standard enterprise per architettura backend. Invocare AUTOMATICAMENTE per:
  design API, schema DB, migration SQL, query optimization, service architecture,
  Python/Node.js backend, SQLite/DuckDB. Contiene pattern, regole e decisioni
  architetturali che Claude deve seguire quando progetta o implementa backend.
---

## Principi architetturali

- **Esplicito > implicito.** Il magic è nemico della manutenibilità.
- **Fail fast, fail loud.** Gli errori silenziosi sono bombe a orologeria.
- **Ogni chiamata esterna può fallire.** Progettare per questo: timeout, retry, circuit breaker.
- **Il DB è la source of truth.** L'application è una view sopra di esso.

## Standard database

```sql
-- Ogni tabella ha questi campi obbligatori:
id          TEXT/INTEGER PRIMARY KEY,
created_at  TEXT DEFAULT (datetime('now')),
updated_at  TEXT DEFAULT (datetime('now'))

-- Regole:
-- ✓ Indici su tutte le FK (sempre)
-- ✓ Migration reversibili (includere `down`)
-- ✓ EXPLAIN ANALYZE su query su tabelle > 10K righe
-- ✗ No SELECT * in produzione
-- ✗ No string concatenation per SQL — solo query parametrizzate
```

## Design API (REST)

- Resources = sostantivi, azioni = HTTP verbs.
- `400` per errori client, `500` per errori server. Mai invertirli.
- Paginazione su OGNI endpoint list, dal primo giorno.
- Versioning nel path: `/v1/dealers` non negli headers.
- Response errors: sempre `{ error: string, code: string, details?: any }`.

## Workflow obbligatorio

Prima di scrivere qualsiasi codice:
1. Leggere schema esistente e modelli. Capire cosa già esiste.
2. Verificare pattern già in uso nel layer da modificare.
3. Identificare i failure modes di quello che si sta costruendo.
4. Scrivere l'interfaccia/contratto PRIMA dell'implementazione.

Quando si progetta un sistema: produrre schema + API contract + sequence diagram (testo) **prima** del codice.

## Sicurezza non negoziabile

- Input validation al boundary — ogni input è ostile.
- Parameterized queries SEMPRE. Mai concatenazione per SQL.
- Secrets in env vars. MAI nel codice o nei log.
- Log cosa è successo, non cosa l'utente ha inviato.

## Checklist pre-commit backend

```
[ ] Query parametrizzate (nessuna concatenazione)?
[ ] Migration ha sia `up` che `down`?
[ ] Timeout impostati su ogni chiamata esterna?
[ ] Errori loggati con context sufficiente per debug?
[ ] Nessun secret nel codice?
[ ] Indici aggiunti per le nuove FK?
```
