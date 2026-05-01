// ─── Resend Email Client — clone pattern fluxion-proxy/lead-magnet ─
// Free tier: 3000/month. From: onboarding@resend.dev (no custom domain).

import type { Env } from './types';

export interface ResendMessage {
  to: string;
  subject: string;
  html: string;
  from?: string;
}

const DEFAULT_FROM = 'ARGOS <onboarding@resend.dev>';

export async function sendResendEmail(
  env: Env,
  msg: ResendMessage,
): Promise<{ ok: boolean; id?: string; error?: string }> {
  if (!env.RESEND_API_KEY) {
    return { ok: false, error: 'RESEND_API_KEY missing' };
  }

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: msg.from ?? DEFAULT_FROM,
        to: [msg.to],
        subject: msg.subject,
        html: msg.html,
      }),
    });

    if (!res.ok) {
      const errBody = await res.text().catch(() => '');
      const trunc = errBody.slice(0, 200);
      console.error(`Resend HTTP ${res.status}: ${trunc}`);
      return { ok: false, error: `HTTP ${res.status}: ${trunc}` };
    }
    const data = (await res.json()) as { id?: string };
    return { ok: true, id: data.id };
  } catch (err) {
    const msgErr = err instanceof Error ? err.message : String(err);
    console.error(`Resend error: ${msgErr}`);
    return { ok: false, error: msgErr };
  }
}
