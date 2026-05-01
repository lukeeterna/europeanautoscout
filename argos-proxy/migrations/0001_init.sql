-- ─── ARGOS contracts schema v2 (post-S151 pivot, no Stripe) ──────────
-- Apply locally:  wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --local
-- Apply remote:   wrangler d1 execute argos-contracts --file=migrations/0001_init.sql --remote
--
-- Status state machine (v2 — bonifico bancario manuale):
--   DRAFT
--    ↓ (dealer signs sign-page)
--   SIGNED  ──┐
--             ↓ (auto-transition in contract-sign.ts after PDF render)
--   AWAITING_DELIVERY
--    ↓ (Luca delivers vehicle docs offline → dashboard "Send IBAN")
--   IBAN_SENT
--    ↓ (Luca verifies wire arrival in MyTu/evolu app → dashboard "Mark Paid")
--   PAID
--
-- Terminal exits: CANCELLED (any state pre-PAID), REFUNDED (post-PAID).

CREATE TABLE IF NOT EXISTS contracts (
  -- Identity
  id                       TEXT    PRIMARY KEY,                  -- nanoid 16 hex
  dealer_id                TEXT    NOT NULL,
  dealer_name              TEXT    NOT NULL,
  dealer_phone             TEXT    NOT NULL,                     -- 393xxxxxxxxx
  dealer_email             TEXT,                                 -- optional, for Resend cc

  -- Vehicle (optional at create-time; CoVe data may arrive later)
  vehicle_vin              TEXT,
  vehicle_make             TEXT,
  vehicle_model            TEXT,
  vehicle_year             INTEGER,
  vehicle_price_eu_cents   INTEGER,                              -- price in EU before delta

  -- Commercial
  fee_cents                INTEGER NOT NULL,                     -- success fee in EUR cents
  status                   TEXT    NOT NULL DEFAULT 'DRAFT'
                                     CHECK (status IN (
                                       'DRAFT','SIGNED','AWAITING_DELIVERY',
                                       'IBAN_SENT','PAID','CANCELLED','REFUNDED')),

  -- Signature token (32 hex) — unique per contract, used in sign URL
  signature_token          TEXT    NOT NULL UNIQUE,

  -- FES (Firma Elettronica Semplice) bundle — eIDAS art.3 / CAD art.20
  signature_font           TEXT,                                 -- whitelist enum (10 values)
  signature_signer_name    TEXT,                                 -- as typed by dealer
  signature_ip             TEXT,                                 -- CF-Connecting-IP at sign
  signature_ua             TEXT,                                 -- User-Agent (truncated 500 chars)
  signature_at             TEXT,                                 -- ISO 8601 UTC
  signature_wa_conv_id     TEXT,                                 -- correlate to WA message (audit)
  signature_email_match    TEXT,                                 -- (reserved future: email magic-link match)
  signature_consent_fes    INTEGER NOT NULL DEFAULT 0
                                     CHECK (signature_consent_fes IN (0,1)),

  -- PDF artefact
  pdf_r2_key               TEXT,                                 -- contracts/<id>.pdf
  pdf_sha256               TEXT,                                 -- 64 hex chars

  -- IBAN sent step (Phase B-7)
  iban_sent_at             TEXT,
  iban_sent_iban           TEXT,                                 -- snapshot which IBAN was sent
                                                                 -- (Luke may rotate MyTu↔evolu)

  -- Payment (manual reconciliation)
  paid_at                  TEXT,
  payment_amount_cents     INTEGER,                              -- amount actually received
  payment_bank             TEXT,                                 -- "MyTu" / "evolu" / etc
  payment_reference        TEXT,                                 -- causale / reference

  -- Bookkeeping
  created_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_contracts_status     ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_dealer     ON contracts(dealer_id);
CREATE INDEX IF NOT EXISTS idx_contracts_token      ON contracts(signature_token);
CREATE INDEX IF NOT EXISTS idx_contracts_created    ON contracts(created_at DESC);

-- ─── Audit log (append-only, FES evidence persistence) ──────────────
-- One row per state transition + per arbitrary event we want forensically pinned.
-- Keep PII minimal in details; full IP/UA columns are dedicated for indexability.

CREATE TABLE IF NOT EXISTS audit_log (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_id  TEXT    NOT NULL,
  action       TEXT    NOT NULL,                                 -- CREATE | SIGN | SEND_IBAN |
                                                                 -- MARK_PAID | CANCEL | REFUND |
                                                                 -- VIEW | OTHER
  actor        TEXT    NOT NULL,                                 -- 'analyzer' | 'dealer' | 'admin'
  details      TEXT,                                             -- JSON blob
  ip           TEXT,
  ua           TEXT,
  at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_contract ON audit_log(contract_id);
CREATE INDEX IF NOT EXISTS idx_audit_action   ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_at       ON audit_log(at DESC);
