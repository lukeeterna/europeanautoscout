// ─── Admin Auth Middleware ─────────────────────────────────────────
// Bearer token validation against ARGOS_ADMIN_SECRET.
// Used for routes invoked by ARGOS analyzer + Luca dashboard.

import type { Context, Next } from 'hono';
import type { AppEnv } from '../lib/types';

export async function adminAuth(c: Context<AppEnv>, next: Next) {
  if (!c.env.ARGOS_ADMIN_SECRET) {
    console.error('ARGOS_ADMIN_SECRET not configured');
    return c.json({ error: 'Server misconfigured', code: 'NO_ADMIN_SECRET' }, 500);
  }

  const auth = c.req.header('Authorization') ?? '';
  const expected = `Bearer ${c.env.ARGOS_ADMIN_SECRET}`;

  // Constant-time comparison
  if (auth.length !== expected.length || !timingSafeEqual(auth, expected)) {
    return c.json({ error: 'Unauthorized', code: 'INVALID_TOKEN' }, 401);
  }

  c.set('adminAuthed', true);
  await next();
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
