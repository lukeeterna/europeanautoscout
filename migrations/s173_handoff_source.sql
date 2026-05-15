-- S173 D-27 / D-28 — handoff_source + is_micro_dealer flags
-- Additive migration: aggiunge 2 colonne a `conversations` per supportare
-- Layer 3 AMBRA post mystery shopper handoff (D-27) e targeting
-- micro-dealer commissione P.IVA forfettaria (D-28).
--
-- Backfill: tutte le righe esistenti pre-S173 → handoff_source='cold' (default),
--           is_micro_dealer=0 (default). Zero impatto su pipeline current.
--
-- Riferimenti:
--   - DECISIONS.md D-27 PROPOSED (3-layer mystery shopper)
--   - DECISIONS.md D-28 DECIDED (micro-dealer commissione target)
--   - AMBRA-AUDIT.md sez 4 (gap-to-D27) + sez 5 (gap-to-D28) + sez 8.4 (critica blast radius FSM)
--
-- Idempotenza: idempotent via ALTER TABLE ADD COLUMN — SQLite rifiuta col duplicate.
-- Per re-run safe usare ensure_state_columns() in state_machine.py (try/except wrap).

-- Vincolo enum applicato lato applicazione (state_machine.VALID_HANDOFF_SOURCES)
-- perche' SQLite CHECK constraint su ALTER TABLE richiede ricostruzione tabella
-- (sqlite docs: "Some restrictions apply to ALTER TABLE ADD COLUMN").
ALTER TABLE conversations ADD COLUMN handoff_source TEXT DEFAULT 'cold';
ALTER TABLE conversations ADD COLUMN is_micro_dealer INTEGER DEFAULT 0;

-- Backfill esplicito (defensive — SQLite default si applica solo a INSERT,
-- non a righe pre-esistenti per ADD COLUMN; in pratica per ADD COLUMN il
-- valore DEFAULT viene materializzato, ma esplicitiamo per chiarezza).
UPDATE conversations SET handoff_source = 'cold' WHERE handoff_source IS NULL;
UPDATE conversations SET is_micro_dealer = 0 WHERE is_micro_dealer IS NULL;
