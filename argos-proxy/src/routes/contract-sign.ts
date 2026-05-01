// ─── Contract Sign — public dealer endpoint ────────────────────────
// POST /api/v1/contract/sign
// Body: { token, signer_name, signature_font, consent_fes }
// 1. Validate token + status=DRAFT + consent_fes=true + font in whitelist
// 2. Render PDF (pdf-lib + fontkit + 10 TTF embedded)
// 3. R2 put + SHA256 + capture FES bundle (IP, UA, timestamp)
// 4. D1 UPDATE status=SIGNED -> AWAITING_DELIVERY (one-step transition)
// 5. Resend email Luca + dealer + Telegram alert

import type { Context } from 'hono';
import type {
  AppEnv,
  ContractRow,
  SignatureFont,
} from '../lib/types';
import { isAllowedFont } from '../lib/types';
import { renderContractPdf } from '../pdf/contract-template';
import { signR2Url } from '../lib/r2-signed-url';
import { sendResendEmail } from '../lib/resend';
import { sendTelegram } from '../lib/telegram';

interface SignRequest {
  token?: string;
  signer_name?: string;
  signature_font?: string;
  consent_fes?: boolean;
}

const SIGNER_MIN = 3;
const SIGNER_MAX = 100;

function sha256Hex(bytes: Uint8Array): Promise<string> {
  return crypto.subtle.digest('SHA-256', bytes).then((buf) =>
    Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join(''),
  );
}

export async function contractSign(c: Context<AppEnv>) {
  let body: SignRequest;
  try {
    body = await c.req.json<SignRequest>();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_BODY' }, 400);
  }

  // ── Validation ─────────────────────────────────────────────────────
  const token = body.token?.trim() ?? '';
  const signerName = body.signer_name?.trim() ?? '';
  const fontRaw = body.signature_font?.trim() ?? '';
  const consent = Boolean(body.consent_fes);

  if (!token || !/^[a-f0-9]{32}$/.test(token)) {
    return c.json({ error: 'Invalid token', code: 'BAD_TOKEN' }, 400);
  }
  if (signerName.length < SIGNER_MIN || signerName.length > SIGNER_MAX) {
    return c.json({ error: 'signer_name 3-100 chars', code: 'BAD_NAME' }, 400);
  }
  if (!isAllowedFont(fontRaw)) {
    return c.json({ error: 'Invalid font', code: 'BAD_FONT' }, 400);
  }
  const font: SignatureFont = fontRaw;
  if (!consent) {
    return c.json(
      { error: 'FES consent required', code: 'NO_CONSENT' },
      400,
    );
  }

  // ── Lookup contract ────────────────────────────────────────────────
  const row = await c.env.DB.prepare(
    `SELECT * FROM contracts WHERE signature_token = ?`,
  )
    .bind(token)
    .first<ContractRow>();

  if (!row) {
    return c.json({ error: 'Contract not found', code: 'NOT_FOUND' }, 404);
  }
  if (row.status !== 'DRAFT') {
    return c.json(
      { error: `Contract already ${row.status}`, code: 'BAD_STATUS', status: row.status },
      409,
    );
  }

  // ── Capture FES evidence bundle ────────────────────────────────────
  const ip = c.req.header('cf-connecting-ip') ?? null;
  const ua = c.req.header('user-agent')?.slice(0, 500) ?? null;
  const now = new Date().toISOString();

  // ── Render PDF ─────────────────────────────────────────────────────
  let pdfBytes: Uint8Array;
  let sha256: string;
  try {
    pdfBytes = await renderContractPdf({
      contract: row,
      signerName,
      font,
      signedAtIso: now,
      signerIp: ip,
      signerUa: ua,
    });
    sha256 = await sha256Hex(pdfBytes);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`contract-sign PDF render failed: ${msg}`);
    return c.json({ error: 'PDF render failed', code: 'PDF_ERROR' }, 500);
  }

  // ── R2 put ─────────────────────────────────────────────────────────
  const r2Key = `contracts/${row.id}.pdf`;
  try {
    await c.env.CONTRACTS.put(r2Key, pdfBytes, {
      httpMetadata: {
        contentType: 'application/pdf',
        contentDisposition: `attachment; filename="ARGOS-contratto-${row.id}.pdf"`,
      },
      customMetadata: {
        contract_id: row.id,
        signed_at: now,
        sha256,
      },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`contract-sign R2 put failed: ${msg}`);
    return c.json({ error: 'Storage failed', code: 'R2_ERROR' }, 500);
  }

  // ── D1 UPDATE: DRAFT -> SIGNED then transition to AWAITING_DELIVERY ─
  // Conditional update guards against double-submit race
  try {
    const update = await c.env.DB.prepare(
      `UPDATE contracts
       SET status = 'AWAITING_DELIVERY',
           signature_font = ?,
           signature_signer_name = ?,
           signature_ip = ?,
           signature_ua = ?,
           signature_at = ?,
           signature_consent_fes = 1,
           pdf_r2_key = ?,
           pdf_sha256 = ?,
           updated_at = ?
       WHERE id = ? AND status = 'DRAFT'`,
    )
      .bind(font, signerName, ip, ua, now, r2Key, sha256, now, row.id)
      .run();

    if (!update.success || (update.meta?.changes ?? 0) === 0) {
      return c.json(
        { error: 'Race condition: contract no longer DRAFT', code: 'RACE_LOST' },
        409,
      );
    }

    await c.env.DB.prepare(
      `INSERT INTO audit_log (contract_id, action, actor, details, ip, ua, at)
       VALUES (?, 'SIGN', 'dealer', ?, ?, ?, ?)`,
    )
      .bind(
        row.id,
        JSON.stringify({
          signer_name: signerName,
          font,
          consent_fes: true,
          pdf_sha256: sha256,
          fes_bundle: {
            ip,
            ua,
            signed_at: now,
            wa_conv_id: row.signature_wa_conv_id,
          },
        }),
        ip,
        ua,
        now,
      )
      .run();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`contract-sign D1 UPDATE failed: ${msg}`);
    return c.json({ error: 'DB update failed', code: 'DB_ERROR' }, 500);
  }

  // ── Best-effort side effects (don't fail the sign on these) ────────
  let pdfUrl: string | null = null;
  try {
    pdfUrl = await signR2Url(c.env.R2_SIGNING_SECRET, r2Key, 7 * 86400);
  } catch (err) {
    console.warn(`contract-sign: signed URL failed: ${(err as Error).message}`);
  }

  const feeEur = row.fee_cents / 100;
  const vehicleLine = [row.vehicle_year, row.vehicle_make, row.vehicle_model]
    .filter((x) => x)
    .join(' ') || 'veicolo da definire';

  // Email to Luca
  if (c.env.RESEND_API_KEY) {
    try {
      await sendResendEmail(c.env, {
        to: 'gianlucadistasi81@gmail.com',
        subject: `[ARGOS] Contratto FIRMATO ${row.dealer_name} - €${feeEur}`,
        html: buildLucaSignedEmail(row, signerName, font, vehicleLine, pdfUrl, sha256),
      });
    } catch (err) {
      console.warn(`Resend Luca failed: ${(err as Error).message}`);
    }

    // Email to dealer (if email known)
    if (row.dealer_email) {
      try {
        await sendResendEmail(c.env, {
          to: row.dealer_email,
          subject: `Conferma firma contratto ARGOS — ${vehicleLine}`,
          html: buildDealerSignedEmail(row, signerName, vehicleLine, pdfUrl),
        });
      } catch (err) {
        console.warn(`Resend dealer failed: ${(err as Error).message}`);
      }
    }
  }

  // Telegram alert
  try {
    await sendTelegram(
      c.env,
      `📝 *Contratto FIRMATO*\n` +
        `Dealer: ${escapeMd(row.dealer_name)}\n` +
        `Veicolo: ${escapeMd(vehicleLine)}\n` +
        `Fee: €${feeEur}\n` +
        `Firmatario: ${escapeMd(signerName)}\n` +
        `Status: AWAITING\\_DELIVERY\n` +
        `ID: \`${row.id}\``,
    );
  } catch (err) {
    console.warn(`Telegram alert failed: ${(err as Error).message}`);
  }

  return c.json(
    {
      ok: true,
      contract_id: row.id,
      status: 'AWAITING_DELIVERY',
      signed_at: now,
      pdf_sha256: sha256,
      post_sign_url: `https://argos-automotive.pages.dev/contract/thank-you.html?id=${row.id}`,
    },
    200,
  );
}

function escapeMd(s: string): string {
  return s.replace(/[_*[\]()~`>#+=|{}.!-]/g, (c) => `\\${c}`);
}

function buildLucaSignedEmail(
  row: ContractRow,
  signer: string,
  font: string,
  vehicle: string,
  pdfUrl: string | null,
  sha256: string,
): string {
  const link = pdfUrl
    ? `<p><a href="${pdfUrl}" style="background:#0066cc;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;">⬇ Scarica PDF firmato</a></p>`
    : '<p><em>(PDF in R2 — link signed URL non disponibile)</em></p>';
  return `<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:auto;padding:20px;">
    <h2>📝 Contratto FIRMATO — ${escapeHtml(row.dealer_name)}</h2>
    <p><strong>Status:</strong> AWAITING_DELIVERY (consegna documenti auto in corso, poi invia IBAN)</p>
    <table style="border-collapse:collapse;width:100%;margin:16px 0;">
      <tr><td style="padding:6px 0;"><b>Dealer:</b></td><td>${escapeHtml(row.dealer_name)} (${escapeHtml(row.dealer_phone)})</td></tr>
      <tr><td style="padding:6px 0;"><b>Veicolo:</b></td><td>${escapeHtml(vehicle)}</td></tr>
      <tr><td style="padding:6px 0;"><b>Fee:</b></td><td>€${row.fee_cents / 100}</td></tr>
      <tr><td style="padding:6px 0;"><b>Firmatario:</b></td><td>${escapeHtml(signer)} (font: ${font})</td></tr>
      <tr><td style="padding:6px 0;"><b>SHA256:</b></td><td><code style="font-size:11px;">${sha256}</code></td></tr>
      <tr><td style="padding:6px 0;"><b>Contract ID:</b></td><td><code>${row.id}</code></td></tr>
    </table>
    ${link}
    <p style="color:#666;font-size:13px;">Prossimo step: consegna documenti auto al dealer → dashboard "📨 Invia IBAN".</p>
  </body></html>`;
}

function buildDealerSignedEmail(
  row: ContractRow,
  signer: string,
  vehicle: string,
  pdfUrl: string | null,
): string {
  const link = pdfUrl
    ? `<p><a href="${pdfUrl}" style="background:#0066cc;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;">⬇ Scarica copia contratto</a> <em>(link valido 7 giorni)</em></p>`
    : '';
  return `<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:auto;padding:20px;">
    <h2>Grazie ${escapeHtml(signer)}, contratto ricevuto</h2>
    <p>Conferma firma contratto ARGOS per <strong>${escapeHtml(vehicle)}</strong>.</p>
    <p><strong>Fee:</strong> €${row.fee_cents / 100} — pagamento <em>solo dopo consegna documenti del veicolo</em>.</p>
    <p>Le invieremo l'IBAN per il bonifico via WhatsApp ed email appena consegnati i documenti dell'auto.</p>
    ${link}
    <p style="color:#666;font-size:13px;margin-top:24px;">A presto,<br>Luca Ferretti — ARGOS</p>
  </body></html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
