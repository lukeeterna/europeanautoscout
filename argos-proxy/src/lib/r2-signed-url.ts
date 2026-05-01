// ─── R2 Signed URL — HMAC-SHA256, TTL parametrizzabile ─────────────
// Pattern mirror fluxion-proxy/src/routes/lead-magnet.ts
// Worker doesn't expose R2 public bucket → emit signed URL pointing to /r2-fetch route.
//
// URL format:
//   https://argos-proxy.<sub>.workers.dev/r2-fetch?key=<key>&exp=<unix>&sig=<hex>
//
// Where sig = HMAC_SHA256(R2_SIGNING_SECRET, "<key>|<exp>")

const WORKER_BASE_URL = 'https://argos-proxy.gianlucanewtech.workers.dev';

export async function signR2Url(
  signingSecret: string,
  key: string,
  ttlSeconds: number,
): Promise<string> {
  if (!signingSecret) throw new Error('R2_SIGNING_SECRET missing');
  const exp = Math.floor(Date.now() / 1000) + ttlSeconds;
  const message = `${key}|${exp}`;
  const sig = await hmacSha256Hex(signingSecret, message);
  const params = new URLSearchParams({
    key,
    exp: String(exp),
    sig,
  });
  return `${WORKER_BASE_URL}/r2-fetch?${params.toString()}`;
}

export async function verifyR2Signature(
  signingSecret: string,
  key: string,
  exp: number,
  sig: string,
): Promise<boolean> {
  if (!signingSecret) return false;
  if (Number.isNaN(exp) || exp < Math.floor(Date.now() / 1000)) return false;
  const expected = await hmacSha256Hex(signingSecret, `${key}|${exp}`);
  return timingSafeEqualHex(expected, sig);
}

async function hmacSha256Hex(key: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(key),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sig = await crypto.subtle.sign('HMAC', cryptoKey, encoder.encode(message));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function timingSafeEqualHex(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
