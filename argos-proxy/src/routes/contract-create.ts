// ─── Contract Creation — admin endpoint ────────────────────────────
// POST /api/v1/contract/create
// Called by ARGOS analyzer (response-analyzer.py) on INTEREST conf>=0.85
// after Telegram HOLD approval by Luca.

import type { Context } from 'hono';
import type { AppEnv, ContractStatus } from '../lib/types';

interface CreateRequest {
  dealer_id?: string;
  dealer_name?: string;
  dealer_phone?: string;
  dealer_email?: string;
  vehicle?: {
    vin?: string;
    make?: string;
    model?: string;
    year?: number;
    price_eu_cents?: number;
  };
  fee_cents?: number;
  wa_conv_id?: string;
}

const FEE_DEFAULT_CENTS = 80000; // €800.00
const FEE_MIN_CENTS = 50000; // €500
const FEE_MAX_CENTS = 200000; // €2.000

function nanoid16(): string {
  // 16 hex chars (8 bytes) — sufficient namespace for contracts
  const bytes = new Uint8Array(8);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function token32(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function isValidItalianPhone(phone: string): boolean {
  // E.164 italiano (+39...) o nazionale (3xxxxxxxxx)
  const cleaned = phone.replace(/\s+/g, '');
  return /^(\+39)?3\d{8,10}$/.test(cleaned);
}

export async function contractCreate(c: Context<AppEnv>) {
  let body: CreateRequest;
  try {
    body = await c.req.json<CreateRequest>();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_BODY' }, 400);
  }

  // ── Validation ─────────────────────────────────────────────────────
  const dealerId = body.dealer_id?.trim() ?? '';
  const dealerName = body.dealer_name?.trim() ?? '';
  const dealerPhone = body.dealer_phone?.trim() ?? '';
  const dealerEmail = body.dealer_email?.trim().toLowerCase() ?? null;

  if (!dealerId || dealerId.length < 1 || dealerId.length > 64) {
    return c.json({ error: 'dealer_id required', code: 'BAD_DEALER_ID' }, 400);
  }
  if (!dealerName || dealerName.length < 2 || dealerName.length > 200) {
    return c.json({ error: 'dealer_name 2-200 chars', code: 'BAD_DEALER_NAME' }, 400);
  }
  if (!dealerPhone || !isValidItalianPhone(dealerPhone)) {
    return c.json({ error: 'dealer_phone IT format required', code: 'BAD_PHONE' }, 400);
  }

  const feeCents = body.fee_cents ?? FEE_DEFAULT_CENTS;
  if (!Number.isInteger(feeCents) || feeCents < FEE_MIN_CENTS || feeCents > FEE_MAX_CENTS) {
    return c.json(
      { error: `fee_cents must be in [${FEE_MIN_CENTS}, ${FEE_MAX_CENTS}]`, code: 'BAD_FEE' },
      400,
    );
  }

  // ── Generate IDs ────────────────────────────────────────────────────
  const id = nanoid16();
  const signatureToken = token32();
  const now = new Date().toISOString();
  const status: ContractStatus = 'DRAFT';

  // ── INSERT D1 ───────────────────────────────────────────────────────
  try {
    await c.env.DB.prepare(
      `INSERT INTO contracts (
        id, dealer_id, dealer_name, dealer_phone, dealer_email,
        vehicle_vin, vehicle_make, vehicle_model, vehicle_year, vehicle_price_eu_cents,
        fee_cents, status, signature_token,
        signature_wa_conv_id,
        signature_consent_fes,
        created_at, updated_at
      ) VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?, ?, 0, ?,?)`,
    )
      .bind(
        id,
        dealerId,
        dealerName,
        dealerPhone,
        dealerEmail,
        body.vehicle?.vin ?? null,
        body.vehicle?.make ?? null,
        body.vehicle?.model ?? null,
        body.vehicle?.year ?? null,
        body.vehicle?.price_eu_cents ?? null,
        feeCents,
        status,
        signatureToken,
        body.wa_conv_id ?? null,
        now,
        now,
      )
      .run();

    // ── Audit log ─────────────────────────────────────────────────────
    await c.env.DB.prepare(
      `INSERT INTO audit_log (contract_id, action, actor, details, ip, ua, at)
       VALUES (?, 'CREATE', 'analyzer', ?, ?, ?, ?)`,
    )
      .bind(
        id,
        JSON.stringify({ fee_cents: feeCents, vehicle: body.vehicle ?? null }),
        c.req.header('cf-connecting-ip') ?? null,
        c.req.header('user-agent') ?? null,
        now,
      )
      .run();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`contract-create D1 INSERT failed: ${msg}`);
    return c.json({ error: 'D1 insert failed', code: 'DB_ERROR' }, 500);
  }

  const signUrl = `https://argos-automotive.pages.dev/contract/${signatureToken}`;

  return c.json(
    {
      ok: true,
      contract_id: id,
      signature_token: signatureToken,
      sign_url: signUrl,
      status,
      fee_eur: feeCents / 100,
      created_at: now,
    },
    201,
  );
}
