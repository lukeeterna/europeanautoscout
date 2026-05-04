// ─── Rate-Limit Middleware ─────────────────────────────────────────
// Anti-abuse layer for public endpoints. Protects R2/D1 from cost-amplifying
// flood (e.g. leaked sign URL hammered → 1M PUT R2 = real spend).
//
// Strategy: in-memory Map per Worker instance + Content-Length body cap.
// Caveat: Workers run multiple isolates → effective limit ≈ N_instances × perIp.
// For ARGOS scale (~100 req/day) this is acceptable. If we ever cross
// 1k req/min, migrate to Durable Objects or KV with atomic INCR.
//
// Layers:
//   1. Per-IP (CF-Connecting-IP header) — caps abuse from single source.
//   2. Global — caps total burst across all IPs.
//   3. Body size — caps POST payload before parsing (Content-Length header).
//
// Admin-authed requests (Bearer ARGOS_ADMIN_SECRET) bypass entirely.

import type { Context, Next } from 'hono';
import type { AppEnv } from '../lib/types';

interface Bucket {
  count: number;
  resetAt: number; // epoch ms
}

interface Options {
  /** Max requests per IP per minute. */
  perIp: number;
  /** Max total requests per minute across all IPs. */
  global: number;
  /** Max body size in bytes (Content-Length check). 0 = no cap. */
  maxBody?: number;
}

const WINDOW_MS = 60_000; // 1 minute fixed window
const GLOBAL_KEY = '__global__';

// Module-level state, persists across requests within a single Worker isolate.
const buckets = new Map<string, Bucket>();

let lastSweepAt = 0;
const SWEEP_INTERVAL_MS = 60_000;

/** Lazy garbage-collection of expired buckets. Called on each invocation; */
/** no-op unless SWEEP_INTERVAL_MS elapsed since last sweep. */
function sweepIfDue(now: number): void {
  if (now - lastSweepAt < SWEEP_INTERVAL_MS) return;
  lastSweepAt = now;
  for (const [key, bucket] of buckets) {
    if (bucket.resetAt <= now) buckets.delete(key);
  }
}

/** Atomically check + increment a bucket. Returns null if allowed, retry-after */
/** seconds if limit exceeded. */
function hit(key: string, limit: number, now: number): number | null {
  let bucket = buckets.get(key);
  if (!bucket || bucket.resetAt <= now) {
    bucket = { count: 0, resetAt: now + WINDOW_MS };
    buckets.set(key, bucket);
  }
  bucket.count += 1;
  if (bucket.count > limit) {
    return Math.max(1, Math.ceil((bucket.resetAt - now) / 1000));
  }
  return null;
}

export function rateLimit(opts: Options) {
  return async (c: Context<AppEnv>, next: Next) => {
    // Admin endpoints bypass — already gated by admin-auth (Bearer token).
    if (c.get('adminAuthed')) {
      return next();
    }

    const now = Date.now();
    sweepIfDue(now);

    // Body size cap (POST/PUT only). Reject before parsing.
    if (opts.maxBody && opts.maxBody > 0) {
      const lenHeader = c.req.header('content-length');
      if (lenHeader) {
        const len = Number.parseInt(lenHeader, 10);
        if (Number.isFinite(len) && len > opts.maxBody) {
          return c.json(
            {
              ok: false,
              error: 'payload_too_large',
              max_bytes: opts.maxBody,
            },
            413,
          );
        }
      }
    }

    // Resolve client IP. CF-Connecting-IP is set by Cloudflare edge; fallback
    // to x-forwarded-for first hop, then a sentinel (treated as one bucket).
    const ip =
      c.req.header('cf-connecting-ip') ||
      c.req.header('x-forwarded-for')?.split(',')[0]?.trim() ||
      'unknown';

    // Per-IP check first (cheaper to fail-fast on noisy single source).
    const ipRetry = hit(`ip:${ip}`, opts.perIp, now);
    if (ipRetry !== null) {
      c.header('Retry-After', String(ipRetry));
      return c.json(
        {
          ok: false,
          error: 'rate_limit_exceeded',
          scope: 'ip',
          retry_after: ipRetry,
        },
        429,
      );
    }

    // Global check.
    const globalRetry = hit(GLOBAL_KEY, opts.global, now);
    if (globalRetry !== null) {
      c.header('Retry-After', String(globalRetry));
      return c.json(
        {
          ok: false,
          error: 'rate_limit_exceeded',
          scope: 'global',
          retry_after: globalRetry,
        },
        429,
      );
    }

    return next();
  };
}
