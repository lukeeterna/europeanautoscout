// ─── ARGOS Proxy — Cloudflare Worker ───────────────────────────────
// Contract signing + bonifico bancario manuale (S152 v2, no Stripe).
//
// Endpoints:
//   GET  /health                                    — health check (no auth)
//   GET  /api/v1/contract/:token                    — public, dealer view
//   POST /api/v1/contract/sign                      — public, dealer signs
//   POST /api/v1/contract/create                    — admin, ARGOS analyzer trigger
//   POST /api/v1/contract/:id/send-iban             — admin, send IBAN via WA
//   POST /api/v1/contract/:id/mark-paid             — admin, reconcile bonifico
//   GET  /api/v1/admin/contracts                    — admin, list for dashboard
//
// Stack: Hono + D1 + R2 + pdf-lib + Resend + Telegram. Zero subscription.

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { AppEnv } from './lib/types';
import { adminAuth } from './middleware/admin-auth';
import { contractCreate } from './routes/contract-create';
import { contractGet } from './routes/contract-get';
import { contractSign } from './routes/contract-sign';
import { sendIban } from './routes/send-iban';
import { markPaid } from './routes/mark-paid';
import { contractsList } from './routes/contracts-list';

const app = new Hono<AppEnv>();

// ── CORS — allow contract sign page on Pages domain ────────────────
app.use(
  '/api/*',
  cors({
    origin: [
      'https://argos-automotive.pages.dev',
      'http://localhost:8788', // wrangler pages dev
      'http://localhost:8080', // dashboard local
    ],
    allowMethods: ['GET', 'POST', 'OPTIONS'],
    allowHeaders: ['Authorization', 'Content-Type'],
    maxAge: 86400,
  }),
);

// ── Health (no auth) ───────────────────────────────────────────────
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    service: 'argos-proxy',
    version: '1.0.0',
    environment: c.env.ENVIRONMENT,
    timestamp: new Date().toISOString(),
  });
});

// ── Public dealer routes ───────────────────────────────────────────
// GET /api/v1/contract/:token — view (recap + status)
// POST /api/v1/contract/sign  — submit signature
app.get('/api/v1/contract/:token', contractGet);
app.post('/api/v1/contract/sign', contractSign);

// ── Admin routes — Bearer ARGOS_ADMIN_SECRET ───────────────────────
app.use('/api/v1/contract/create', adminAuth);
app.use('/api/v1/contract/:id/send-iban', adminAuth);
app.use('/api/v1/contract/:id/mark-paid', adminAuth);
app.use('/api/v1/admin/*', adminAuth);

app.post('/api/v1/contract/create', contractCreate);
app.post('/api/v1/contract/:id/send-iban', sendIban);
app.post('/api/v1/contract/:id/mark-paid', markPaid);
app.get('/api/v1/admin/contracts', contractsList);

// ── 404 ────────────────────────────────────────────────────────────
app.notFound((c) => c.json({ error: 'Not found', code: 'NOT_FOUND' }, 404));

// ── Error handler ──────────────────────────────────────────────────
app.onError((err, c) => {
  console.error('Worker error:', err.message, err.stack);
  return c.json(
    { error: 'Internal server error', code: 'INTERNAL_ERROR' },
    500,
  );
});

export default app;
