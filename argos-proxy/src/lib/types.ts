// ─── ARGOS Proxy Worker — Environment Bindings ─────────────────────
// Stack v2 (post-S151 pivot): bonifico bancario manuale, NO Stripe.

export interface Env {
  // Cloudflare bindings
  DB: D1Database;
  CONTRACTS: R2Bucket;

  // Secrets
  RESEND_API_KEY: string;
  ARGOS_ADMIN_SECRET: string;
  R2_SIGNING_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_CHAT_ID: string;
  ARGOS_IBAN: string;
  ARGOS_INTESTATARIO: string;
  WA_DAEMON_URL: string;
  WA_DAEMON_API_KEY: string;

  // Vars
  ENVIRONMENT: 'test' | 'production';
}

// ─── Hono Context Variables ────────────────────────────────────────
export interface Variables {
  // populated by admin-auth middleware
  adminAuthed?: true;
}

export interface AppEnv {
  Bindings: Env;
  Variables: Variables;
}

// ─── Domain types ──────────────────────────────────────────────────

export type ContractStatus =
  | 'DRAFT'
  | 'SIGNED'
  | 'AWAITING_DELIVERY'
  | 'IBAN_SENT'
  | 'PAID'
  | 'CANCELLED'
  | 'REFUNDED';

export interface ContractRow {
  id: string;
  dealer_id: string;
  dealer_name: string;
  dealer_phone: string;
  dealer_email: string | null;
  vehicle_vin: string | null;
  vehicle_make: string | null;
  vehicle_model: string | null;
  vehicle_year: number | null;
  vehicle_price_eu_cents: number | null;
  fee_cents: number;
  status: ContractStatus;
  signature_token: string;
  signature_font: string | null;
  signature_signer_name: string | null;
  signature_ip: string | null;
  signature_ua: string | null;
  signature_at: string | null;
  signature_wa_conv_id: string | null;
  signature_email_match: string | null;
  signature_consent_fes: number; // SQLite boolean (0/1)
  pdf_r2_key: string | null;
  pdf_sha256: string | null;
  iban_sent_at: string | null;
  iban_sent_iban: string | null;
  paid_at: string | null;
  payment_amount_cents: number | null;
  payment_bank: string | null;
  payment_reference: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Allowed signature fonts (whitelist server-side) ───────────────
// Mirrors assets/fonts/*.ttf filenames (lowercase-kebab).
export const ALLOWED_SIGNATURE_FONTS = [
  'allura',
  'great-vibes',
  'pacifico',
  'dancing-script',
  'sacramento',
  'tangerine',
  'yellowtail',
  'kaushan-script',
  'satisfy',
  'caveat',
] as const;

export type SignatureFont = (typeof ALLOWED_SIGNATURE_FONTS)[number];

export function isAllowedFont(value: string): value is SignatureFont {
  return (ALLOWED_SIGNATURE_FONTS as readonly string[]).includes(value);
}

// ─── Public contract DTO (returned to anonymous viewer of sign page) ─
// Strips internal fields (audit, IPs, R2 keys) — only what the dealer needs.
export interface ContractPublicDto {
  id: string;
  status: ContractStatus;
  dealer_name: string;
  vehicle_make: string | null;
  vehicle_model: string | null;
  vehicle_year: number | null;
  fee_eur: number;
  created_at: string;
  signed_at: string | null;
  pdf_download_url: string | null; // populated only when SIGNED+, signed URL TTL 7d
}
