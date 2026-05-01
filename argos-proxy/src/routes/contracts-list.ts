// ─── Contracts List — admin endpoint for dashboard ─────────────────
// GET /api/v1/admin/contracts?status=...&limit=...
// Returns recent contracts (newest first). Used by Luca dashboard.

import type { Context } from 'hono';
import type { AppEnv, ContractRow, ContractStatus } from '../lib/types';

const VALID_STATUSES: ContractStatus[] = [
  'DRAFT', 'SIGNED', 'AWAITING_DELIVERY', 'IBAN_SENT', 'PAID', 'CANCELLED', 'REFUNDED',
];

export async function contractsList(c: Context<AppEnv>) {
  const statusParam = c.req.query('status')?.trim() ?? '';
  const limitParam = parseInt(c.req.query('limit') ?? '50', 10);
  const limit = Math.min(Math.max(Number.isFinite(limitParam) ? limitParam : 50, 1), 200);

  let rows: ContractRow[];
  try {
    if (statusParam && (VALID_STATUSES as string[]).includes(statusParam)) {
      const result = await c.env.DB.prepare(
        `SELECT * FROM contracts WHERE status = ? ORDER BY created_at DESC LIMIT ?`,
      )
        .bind(statusParam, limit)
        .all<ContractRow>();
      rows = result.results ?? [];
    } else {
      const result = await c.env.DB.prepare(
        `SELECT * FROM contracts ORDER BY created_at DESC LIMIT ?`,
      )
        .bind(limit)
        .all<ContractRow>();
      rows = result.results ?? [];
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`contracts-list D1 error: ${msg}`);
    return c.json({ error: 'DB error', code: 'DB_ERROR' }, 500);
  }

  // Strip nothing — admin already authed. Return full rows for dashboard.
  return c.json({ ok: true, count: rows.length, contracts: rows }, 200);
}
