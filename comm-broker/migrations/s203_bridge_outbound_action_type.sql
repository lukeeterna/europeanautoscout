-- S203 Migration: aggiunge action_type a bridge_outbound per HITL routing
-- Idempotente: applicare solo se colonna non esiste (vedere apply_s203_migration.py)
--
-- Whitelist auto-approve:
--   day1_send, day3_followup, day7_followup, objection_reply, partial_report
--
-- HITL required (approved_ts = NULL → dashboard popola):
--   contract_create, mark_paid, price_override

ALTER TABLE bridge_outbound ADD COLUMN action_type TEXT DEFAULT 'agent_auto';
