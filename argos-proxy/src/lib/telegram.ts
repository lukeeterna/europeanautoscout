// ─── Telegram Alert ────────────────────────────────────────────────
// Used for ARGOS Luca alerts: contract signed, IBAN sent, payment received.
// Reuses existing TG bot from ARGOS infra.

import type { Env } from './types';

export async function sendTelegram(
  env: Env,
  text: string,
): Promise<{ ok: boolean; error?: string }> {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) {
    return { ok: false, error: 'Telegram secrets missing' };
  }
  try {
    const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: env.TELEGRAM_CHAT_ID,
        text,
        parse_mode: 'MarkdownV2',
        disable_web_page_preview: true,
      }),
    });
    if (!res.ok) {
      const errBody = await res.text().catch(() => '');
      console.error(`Telegram HTTP ${res.status}: ${errBody.slice(0, 200)}`);
      return { ok: false, error: `HTTP ${res.status}` };
    }
    return { ok: true };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`Telegram error: ${msg}`);
    return { ok: false, error: msg };
  }
}
