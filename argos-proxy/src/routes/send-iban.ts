// ─── Send IBAN — admin endpoint (B-7 stub) ─────────────────────────
// Implemented in Phase B-7 (Chunk B / S152b).

import type { Context } from 'hono';
import type { AppEnv } from '../lib/types';

export async function sendIban(c: Context<AppEnv>) {
  return c.json(
    { error: 'Not implemented — Phase B-7 (S152b)', code: 'NOT_IMPLEMENTED' },
    501,
  );
}
