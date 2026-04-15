-- ARGOS Plan 04-02 — reset artefatti seeding (2026-04-15)
-- PRECONDIZIONE: messages table deve avere 0 righe per i 3 dealer_id qui sotto.
-- Eseguire su: /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite
-- TIER1_FG_002 (Enzo Car) NON incluso — resta CLOSED_NO.

-- SAFETY NOTE: RAISE(ABORT) non supportato fuori da trigger in SQLite 3.x.
-- Il pre-check (zero messages) va eseguito PRIMA di questo script via:
--   sqlite3 DB "SELECT COUNT(*) FROM messages WHERE dealer_id IN ('TIER0_FG_001','TIER0_CS_001','TIER0_AV_001');"
-- Se COUNT > 0 → NON eseguire questo script.

BEGIN TRANSACTION;

UPDATE conversations
SET current_step = 'PENDING',
    outbound_count = 0,
    inbound_count = 0,
    last_contact_at = NULL
WHERE dealer_id IN ('TIER0_FG_001','TIER0_CS_001','TIER0_AV_001');

COMMIT;

-- Post-check
SELECT dealer_id, current_step, outbound_count, inbound_count, last_contact_at
FROM conversations
WHERE dealer_id IN ('TIER0_FG_001','TIER0_CS_001','TIER0_AV_001')
ORDER BY dealer_id;
