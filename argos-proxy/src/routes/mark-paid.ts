// ─── Mark Paid — admin endpoint (B-8 stub) ─────────────────────────
// Implemented in Phase B-8 (Chunk B / S152b).

import type { Context } from 'hono';
import type { AppEnv } from '../lib/types';

export async function markPaid(c: Context<AppEnv>) {
  return c.json(
    { error: 'Not implemented — Phase B-8 (S152b)', code: 'NOT_IMPLEMENTED' },
    501,
  );
}
