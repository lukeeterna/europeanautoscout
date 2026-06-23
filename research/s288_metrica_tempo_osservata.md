# S288 BUILD — Metrica-tempo OSSERVATA + rinomina onesta

**Data**: 2026-06-23 · **Esecuzione**: CC-MAIN diretto (no delega, per incidente subagent S288)
**File toccati**: `tools/dealer_collector.py`, `tests/test_s288_vehicle_observations.py`

## Cosa è stato costruito (3 parti)

### PARTE 1 — Rinomina onesta
`avg_listing_age_days` → `avg_vehicle_age_days`. È **età-veicolo** (da
`firstRegistrationDate`), NON anzianità-annuncio. Migrazione idempotente
`migrate_schema()`: guarda `PRAGMA table_info` e fa `ALTER TABLE … RENAME COLUMN`
solo se serve. Restore-point pre-ALTER via SQLite backup API (vincolo 1d).

### PARTE 2 — vehicle_observations (cuore S288)
Tabella `vehicle_observations(dealer_id, vehicle_key, first_observed_at,
last_observed_at, status)`, PK composta. `snapshot_observations()`:
- **CORR #1**: `vehicle_key = listing.id` (UUID v4 nativo, stabile) — NON hash di
  contenuto (cambierebbe a ogni ribasso → falso "venduto").
- nuovo → insert `first=last=now` PRESENT; già visto → `last=now` (first INVARIATO).
- **CORR #2**: diff-GONE (assenti ORA → GONE, **mai delete**) gira SOLO se
  `run_complete` (no errori fetch AND `len(items) >= numberOfResults`). Fetch
  parziale → niente GONE (evita valanga di falsi-GONE).

### PARTE 3 — Prova diff senza doctorare il DB
- **CORR #3**: test unitario su sqlite `:memory:` — NON muta `data/dealers.db`.

## Evidenza DONE-CONDITION

1. **.schema** — `avg_vehicle_age_days` presente; `vehicle_observations` creata. ✓
2. **Collector ×2 live rossettomotors-srl** (28 listing reali, run_complete=true):
   - RUN1: `inserted=28, updated=0, gone=0` (first==last, tutti PRESENT)
   - RUN2: `inserted=0, updated=28, gone=0` — first INVARIATO, last avanzato, 0 dup
   - campione: `ec02cde1-…` first `20:31:09.88` < last `20:31:23.20` ✓
3. **Test GONE** `tests/test_s288_vehicle_observations.py`: **4/4 PASS**
   (gone-no-delete, first-stabile, guardia-run-parziale, idempotenza). ✓
4. **Idempotenza S287**: dealers=1, profiles=1. ✓
5. **GDPR**: 0 colonne personali (vehicle_key = UUID, nessun contatto/telefono/email). ✓
6. Commit file nominati, no push.

Restore-point creato: `data/dealers.backup-20260623T203100Z.db` (non committato).

## SPEC S289 (annotata, NON costruita)
Gap-Analysis su metrica osservata: "stock fermo" = `days_observed` alto;
velocity = conteggio GONE/tempo. Estendi `generate_cold_day1` (`templates.py:273`)
con dato OSSERVATO ("questa BMW è ferma da ~X settimane"). ICP micro-dealer <20
da sorgente discovery diversa.
