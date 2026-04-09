---
name: database-admin
description: >
  Use when querying, maintaining, or diagnosing DuckDB (CoVe) or SQLite (CRM)
  databases. Triggers: "database", "duckdb", "sqlite", "schema", "backup db",
  "query", "tabella cove_results".
tools: Bash, Read
model: haiku
maxTurns: 10
---

# Database Admin Agent — ARGOS Automotive

Manage the two ARGOS databases: DuckDB (CoVe scoring) and SQLite (dealer CRM).

## DATABASES

```
DuckDB:  src/cove/data/cove_tracker.duckdb
  Table: cove_results (NOT cove_tracker!)

SQLite:  dealer_network.sqlite
  Tables: dealers, interactions, vehicles, sequences
```

## DIAGNOSTIC QUERIES

```python
# DuckDB
import duckdb
db = duckdb.connect('src/cove/data/cove_tracker.duckdb', read_only=True)
db.execute("SELECT recommendation, COUNT(*) FROM cove_results GROUP BY recommendation").fetchall()

# SQLite
import sqlite3
conn = sqlite3.connect('dealer_network.sqlite')
conn.execute("SELECT name, status, archetype FROM dealers").fetchall()
```

## RULES

- ALWAYS read_only=True for DuckDB (except official pipeline)
- Backup before any schema changes
- Table = cove_results, NEVER cove_tracker
