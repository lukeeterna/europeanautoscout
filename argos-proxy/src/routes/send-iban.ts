// ─── Send IBAN — admin endpoint (B-7) ─────────────────────────────
// POST /api/v1/contract/:id/send-iban
//
// Pre: status === 'AWAITING_DELIVERY' (Luca delivered car docs offline).
// Action:
//   1. UPDATE status='IBAN_SENT', iban_sent_at, iban_sent_iban (snapshot)
//   2. Audit log row
//   3. Best-effort: WA template + Resend email + Telegram alert
// Side effects are best-effort (do not fail the response on side-effect failure).

import type { Context } from 'hono';
import type { AppEnv, ContractRow } from '../lib/types';
import { sendWa } from '../lib/wa-daemon';
import { sendResendEmail } from '../lib/resend';
import { sendTelegram } from '../lib/telegram';

export async function sendIban(c: Context<AppEnv>) {
  const id = c.req.param('id')?.trim() ?? '';
  if (!id || !/^[a-f0-9]{16}$/.test(id)) {
    return c.json({ error: 'Invalid contract id', code: 'BAD_ID' }, 400);
  }

  if (!c.env.ARGOS_IBAN || !c.env.ARGOS_INTESTATARIO) {
    console.error('ARGOS_IBAN or ARGOS_INTESTATARIO not configured');
    return c.json(
      { error: 'Server misconfigured: IBAN secrets missing', code: 'NO_IBAN' },
      500,
    );
  }

  // ── Lookup ─────────────────────────────────────────────────────────
  const row = await c.env.DB.prepare(`SELECT * FROM contracts WHERE id = ?`)
    .bind(id)
    .first<ContractRow>();

  if (!row) {
    return c.json({ error: 'Contract not found', code: 'NOT_FOUND' }, 404);
  }
  if (row.status !== 'AWAITING_DELIVERY') {
    return c.json(
      {
        error: `Cannot send IBAN: status is ${row.status}, expected AWAITING_DELIVERY`,
        code: 'BAD_STATUS',
        current_status: row.status,
      },
      409,
    );
  }

  // ── D1 UPDATE (conditional, guards against double-trigger) ─────────
  const now = new Date().toISOString();
  const ibanSnapshot = c.env.ARGOS_IBAN;
  try {
    const update = await c.env.DB.prepare(
      `UPDATE contracts
       SET status = 'IBAN_SENT',
           iban_sent_at = ?,
           iban_sent_iban = ?,
           updated_at = ?
       WHERE id = ? AND status = 'AWAITING_DELIVERY'`,
    )
      .bind(now, ibanSnapshot, now, id)
      .run();

    if (!update.success || (update.meta?.changes ?? 0) === 0) {
      return c.json(
        { error: 'Race: status changed concurrently', code: 'RACE_LOST' },
        409,
      );
    }

    const ibanLast4 = ibanSnapshot.slice(-4);
    await c.env.DB.prepare(
      `INSERT INTO audit_log (contract_id, action, actor, details, ip, ua, at)
       VALUES (?, 'SEND_IBAN', 'admin', ?, ?, ?, ?)`,
    )
      .bind(
        id,
        JSON.stringify({ iban_last4: ibanLast4 }),
        c.req.header('cf-connecting-ip') ?? null,
        c.req.header('user-agent') ?? null,
        now,
      )
      .run();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`send-iban D1 UPDATE failed: ${msg}`);
    return c.json({ error: 'DB update failed', code: 'DB_ERROR' }, 500);
  }

  const feeEur = row.fee_cents / 100;

  // ── Build WA template (IBAN_SEND) ──────────────────────────────────
  const waBody = buildIbanWaTemplate({
    dealerName: row.dealer_name,
    iban: ibanSnapshot,
    intestatario: c.env.ARGOS_INTESTATARIO,
    feeEur,
    contractId: row.id,
  });

  // ── Side effects (best-effort) ─────────────────────────────────────
  let waSent = false;
  let emailSent = false;

  const waResult = await sendWa(c.env, {
    phone: row.dealer_phone,
    body: waBody,
  });
  if (waResult.ok) {
    waSent = true;
  } else {
    console.warn(`send-iban WA failed: ${waResult.error}`);
  }

  if (row.dealer_email && c.env.RESEND_API_KEY) {
    try {
      const emailRes = await sendResendEmail(c.env, {
        to: row.dealer_email,
        subject: `IBAN per bonifico ARGOS — ${row.dealer_name}`,
        html: buildIbanEmail({
          dealerName: row.dealer_name,
          iban: ibanSnapshot,
          intestatario: c.env.ARGOS_INTESTATARIO,
          feeEur,
          contractId: row.id,
        }),
      });
      emailSent = emailRes.ok;
      if (!emailRes.ok) {
        console.warn(`send-iban Resend failed: ${emailRes.error}`);
      }
    } catch (err) {
      console.warn(`send-iban Resend exception: ${(err as Error).message}`);
    }
  }

  try {
    await sendTelegram(
      c.env,
      `📨 *IBAN inviato*\n` +
        `Dealer: ${escapeMd(row.dealer_name)}\n` +
        `Importo: €${feeEur}\n` +
        `Causale: ARGOS\\-${row.id}\n` +
        `WA: ${waSent ? '✅' : '⚠️'}  Email: ${emailSent ? '✅' : '➖'}\n` +
        `Status: IBAN\\_SENT`,
    );
  } catch (err) {
    console.warn(`send-iban Telegram failed: ${(err as Error).message}`);
  }

  return c.json(
    {
      ok: true,
      contract_id: id,
      status: 'IBAN_SENT',
      iban_sent_at: now,
      wa_sent: waSent,
      email_sent: emailSent,
    },
    200,
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────

interface IbanCtx {
  dealerName: string;
  iban: string;
  intestatario: string;
  feeEur: number;
  contractId: string;
}

function buildIbanWaTemplate(ctx: IbanCtx): string {
  // Nota narrativa: titolare conto è nome reale del founder, non persona
  // commerciale Luca Ferretti. SEPA VoP (live dal 9 ottobre 2025) farebbe
  // mismatch in caso contrario — disclosure necessario.
  return [
    `Pronto per il bonifico ${ctx.dealerName}.`,
    ``,
    `IBAN: ${ctx.iban}`,
    `Intestatario: ${ctx.intestatario}`,
    `Importo: €${ctx.feeEur}`,
    `Causale: ARGOS-${ctx.contractId}`,
    ``,
    `Per il bonifico la banca verifica il nome del titolare del conto: ${ctx.intestatario}. ARGOS è il brand, Luca Ferretti il referente.`,
    ``,
    `Mi invii ricevuta quando fatto. Grazie.`,
  ].join('\n');
}

function buildIbanEmail(ctx: IbanCtx): string {
  return `<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:auto;padding:20px;">
    <h2>Pronto per il bonifico — ${escapeHtml(ctx.dealerName)}</h2>
    <p>Le confermo i dati per il bonifico ARGOS:</p>
    <table style="border-collapse:collapse;width:100%;margin:16px 0;border:1px solid #ddd;">
      <tr><td style="padding:10px;background:#f7f7f7;"><b>IBAN</b></td><td style="padding:10px;font-family:monospace;">${escapeHtml(ctx.iban)}</td></tr>
      <tr><td style="padding:10px;background:#f7f7f7;"><b>Intestatario</b></td><td style="padding:10px;">${escapeHtml(ctx.intestatario)}</td></tr>
      <tr><td style="padding:10px;background:#f7f7f7;"><b>Importo</b></td><td style="padding:10px;">€${ctx.feeEur}</td></tr>
      <tr><td style="padding:10px;background:#f7f7f7;"><b>Causale</b></td><td style="padding:10px;font-family:monospace;">ARGOS-${escapeHtml(ctx.contractId)}</td></tr>
    </table>
    <p style="background:#fff8e1;border-left:4px solid #f9a825;padding:12px;margin:16px 0;">
      <strong>Nota:</strong> dal 9 ottobre 2025 le banche EU verificano il nome del titolare del conto (SEPA Verification of Payee). La banca farà controllo automatico sul nome <em>${escapeHtml(ctx.intestatario)}</em>: ARGOS è il brand commerciale, l'intestatario del conto è il titolare reale.
    </p>
    <p>Mi invii la ricevuta del bonifico via WhatsApp o email quando completato. Grazie.</p>
    <p style="color:#666;font-size:13px;margin-top:24px;">A presto,<br>Luca Ferretti — ARGOS</p>
  </body></html>`;
}

function escapeMd(s: string): string {
  return s.replace(/[_*[\]()~`>#+=|{}.!-]/g, (c) => `\\${c}`);
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
