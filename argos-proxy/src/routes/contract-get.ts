// ─── Contract View — public dealer endpoint ────────────────────────
// GET /api/v1/contract/:token
// Returns ContractPublicDto (no PII beyond dealer_name + vehicle/fee).
// If status >= SIGNED, includes signed R2 download URL (TTL 7d).

import type { Context } from 'hono';
import type { AppEnv, ContractRow, ContractPublicDto } from '../lib/types';
import { signR2Url } from '../lib/r2-signed-url';

export async function contractGet(c: Context<AppEnv>) {
  const token = c.req.param('token')?.trim() ?? '';

  if (!token || !/^[a-f0-9]{32}$/.test(token)) {
    return c.json({ error: 'Invalid token format', code: 'BAD_TOKEN' }, 400);
  }

  const row = await c.env.DB.prepare(
    `SELECT * FROM contracts WHERE signature_token = ?`,
  )
    .bind(token)
    .first<ContractRow>();

  if (!row) {
    return c.json({ error: 'Contract not found', code: 'NOT_FOUND' }, 404);
  }

  let pdfDownloadUrl: string | null = null;
  if (row.pdf_r2_key && c.env.R2_SIGNING_SECRET) {
    try {
      pdfDownloadUrl = await signR2Url(
        c.env.R2_SIGNING_SECRET,
        row.pdf_r2_key,
        7 * 86400, // 7d
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`contract-get: signed URL failed for ${row.id}: ${msg}`);
    }
  }

  const dto: ContractPublicDto = {
    id: row.id,
    status: row.status,
    dealer_name: row.dealer_name,
    vehicle_make: row.vehicle_make,
    vehicle_model: row.vehicle_model,
    vehicle_year: row.vehicle_year,
    fee_eur: row.fee_cents / 100,
    created_at: row.created_at,
    signed_at: row.signature_at,
    pdf_download_url: pdfDownloadUrl,
  };

  return c.json(dto, 200);
}
