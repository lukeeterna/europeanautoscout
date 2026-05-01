// ─── WhatsApp Daemon Client ────────────────────────────────────────
// HTTP client to ARGOS daemon on iMac (LAN). Used for IBAN_SEND and
// PAYMENT_RECEIVED templates.
//
// Env: WA_DAEMON_URL = http://192.168.1.2:9191 (LAN)
//      WA_DAEMON_API_KEY = X-API-Key header (per .claude/rules/security.md)
//
// NOTE production: daemon NOT publicly reachable. For prod path the Worker
// would need Tailscale binding or daemon would publish via Cloudflare Tunnel.
// In S152 (test mode) this is invoked manually from dashboard while Luke is
// on home LAN, OR via Tailscale ingress. Documented in HANDOFF.

import type { Env } from './types';

export interface SendWaParams {
  phone: string; // 393314928901 format (no +, no spaces)
  body: string;
}

export async function sendWa(
  env: Env,
  params: SendWaParams,
): Promise<{ ok: boolean; error?: string }> {
  if (!env.WA_DAEMON_URL) {
    return { ok: false, error: 'WA_DAEMON_URL missing' };
  }
  if (!params.phone || !/^\d{11,13}$/.test(params.phone)) {
    return { ok: false, error: 'invalid phone format' };
  }
  if (!params.body || params.body.length === 0 || params.body.length > 4096) {
    return { ok: false, error: 'invalid body length' };
  }

  try {
    const res = await fetch(`${env.WA_DAEMON_URL}/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(env.WA_DAEMON_API_KEY ? { 'X-API-Key': env.WA_DAEMON_API_KEY } : {}),
      },
      body: JSON.stringify({
        phone: params.phone,
        message: params.body,
      }),
      // Cloudflare Workers fetch has no built-in timeout — rely on platform
    });

    if (!res.ok) {
      const errBody = await res.text().catch(() => '');
      console.error(`WA daemon HTTP ${res.status}: ${errBody.slice(0, 200)}`);
      return { ok: false, error: `HTTP ${res.status}` };
    }
    return { ok: true };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`WA daemon error: ${msg}`);
    return { ok: false, error: msg };
  }
}
