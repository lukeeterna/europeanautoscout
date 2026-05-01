// ─── Mark Paid — admin endpoint (B-8) ──────────────────────────────
// POST /api/v1/contract/:id/mark-paid
// Body: { paid_amount_cents, paid_at_iso?, payment_bank, payment_reference }
//
// Pre: status in ('IBAN_SENT', 'AWAITING_DELIVERY')  — IBAN_SENT is the
//      normal path; AWAITING_DELIVERY allows reconciling early bonifici
//      (dealer paid before IBAN was formally sent — happens with relational
//      dealers).
// Tolerance ±€1 vs fee_cents (rounding/bank fees).

import type { Context } from 'hono';
import type { AppEnv, ContractRow } from '../lib/types';
import { sendWa } from '../lib/wa-daemon';
import { sendResendEmail } from '../lib/resend';
import { sendTelegram } from '../lib/telegram';

interface MarkPaidRequest {
  paid_amount_cents?: number;
  paid_at_iso?: string;
  payment_bank?: string;
  payment_reference?: string;
}

const TOLERANCE_CENTS = 100; // ±€1

export async function markPaid(c: Context<AppEnv>) {
  const id = c.req.param('id')?.trim() ?? '';
  if (!id || !/^[a-f0-9]{16}$/.test(id)) {
    return c.json({ error: 'Invalid contract id', code: 'BAD_ID' }, 400);
  }

  let body: MarkPaidRequest;
  try {
    body = await c.req.json<MarkPaidRequest>();
  } catch {
    return c.json({ error: 'Invalid JSON', code: 'BAD_BODY' }, 400);
  }

  const paidAmount = body.paid_amount_cents;
  const paymentBank = body.payment_bank?.trim() ?? '';
  const paymentReference = body.payment_reference?.trim() ?? '';
  const paidAtIso = body.paid_at_iso?.trim() || new Date().toISOString();

  if (!Number.isInteger(paidAmount) || (paidAmount as number) <= 0) {
    return c.json(
      { error: 'paid_amount_cents must be positive integer', code: 'BAD_AMOUNT' },
      400,
    );
  }
  if (!paymentBank || paymentBank.length < 2 || paymentBank.length > 50) {
    return c.json(
      { error: 'payment_bank required (2-50 chars)', code: 'BAD_BANK' },
      400,
    );
  }
  if (!paymentReference || paymentReference.length < 2 || paymentReference.length > 200) {
    return c.json(
      { error: 'payment_reference required (2-200 chars)', code: 'BAD_REF' },
      400,
    );
  }
  if (Number.isNaN(Date.parse(paidAtIso))) {
    return c.json(
      { error: 'paid_at_iso must be ISO 8601', code: 'BAD_DATE' },
      400,
    );
  }

  // ── Lookup ─────────────────────────────────────────────────────────
  const row = await c.env.DB.prepare(`SELECT * FROM contracts WHERE id = ?`)
    .bind(id)
    .first<ContractRow>();

  if (!row) {
    return c.json({ error: 'Contract not found', code: 'NOT_FOUND' }, 404);
  }
  if (row.status !== 'IBAN_SENT' && row.status !== 'AWAITING_DELIVERY') {
    return c.json(
      {
        error: `Cannot mark paid: status is ${row.status}`,
        code: 'BAD_STATUS',
        current_status: row.status,
      },
      409,
    );
  }

  if ((paidAmount as number) < row.fee_cents - TOLERANCE_CENTS) {
    return c.json(
      {
        error: `Amount short: received ${paidAmount} cents, expected >= ${row.fee_cents - TOLERANCE_CENTS}`,
        code: 'AMOUNT_SHORT',
        expected_cents: row.fee_cents,
        received_cents: paidAmount,
      },
      400,
    );
  }

  // ── D1 UPDATE ──────────────────────────────────────────────────────
  const nowUpdated = new Date().toISOString();
  try {
    const update = await c.env.DB.prepare(
      `UPDATE contracts
       SET status = 'PAID',
           paid_at = ?,
           payment_amount_cents = ?,
           payment_bank = ?,
           payment_reference = ?,
           updated_at = ?
       WHERE id = ? AND status IN ('IBAN_SENT', 'AWAITING_DELIVERY')`,
    )
      .bind(paidAtIso, paidAmount, paymentBank, paymentReference, nowUpdated, id)
      .run();

    if (!update.success || (update.meta?.changes ?? 0) === 0) {
      return c.json(
        { error: 'Race: status changed concurrently', code: 'RACE_LOST' },
        409,
      );
    }

    await c.env.DB.prepare(
      `INSERT INTO audit_log (contract_id, action, actor, details, ip, ua, at)
       VALUES (?, 'MARK_PAID', 'admin', ?, ?, ?, ?)`,
    )
      .bind(
        id,
        JSON.stringify({
          amount_cents: paidAmount,
          bank: paymentBank,
          reference: paymentReference,
          paid_at_iso: paidAtIso,
          previous_status: row.status,
        }),
        c.req.header('cf-connecting-ip') ?? null,
        c.req.header('user-agent') ?? null,
        nowUpdated,
      )
      .run();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`mark-paid D1 UPDATE failed: ${msg}`);
    return c.json({ error: 'DB update failed', code: 'DB_ERROR' }, 500);
  }

  const feeEur = row.fee_cents / 100;
  const paidEur = (paidAmount as number) / 100;

  // ── Side effects (best-effort) ─────────────────────────────────────
  const waBody = buildPaymentWaTemplate({ dealerName: row.dealer_name });

  let waSent = false;
  let emailSent = false;

  const waResult = await sendWa(c.env, {
    phone: row.dealer_phone,
    body: waBody,
  });
  if (waResult.ok) {
    waSent = true;
  } else {
    console.warn(`mark-paid WA failed: ${waResult.error}`);
  }

  if (c.env.RESEND_API_KEY) {
    try {
      await sendResendEmail(c.env, {
        to: 'gianlucadistasi81@gmail.com',
        subject: `[ARGOS] PAGATO €${paidEur} — ${row.dealer_name}`,
        html: buildLucaPaidEmail({
          dealerName: row.dealer_name,
          paidEur,
          feeEur,
          paymentBank,
          paymentReference,
          paidAtIso,
          contractId: row.id,
        }),
      });
    } catch (err) {
      console.warn(`mark-paid Resend Luca failed: ${(err as Error).message}`);
    }

    if (row.dealer_email) {
      try {
        const emailRes = await sendResendEmail(c.env, {
          to: row.dealer_email,
          subject: `Pagamento ricevuto — ARGOS ${row.dealer_name}`,
          html: buildDealerPaidEmail({ dealerName: row.dealer_name, paidEur }),
        });
        emailSent = emailRes.ok;
      } catch (err) {
        console.warn(`mark-paid Resend dealer failed: ${(err as Error).message}`);
      }
    }
  }

  try {
    await sendTelegram(
      c.env,
      `✅ *PAGATO* €${paidEur}\n` +
        `Dealer: ${escapeMd(row.dealer_name)}\n` +
        `Banca: ${escapeMd(paymentBank)}\n` +
        `Causale: ${escapeMd(paymentReference)}\n` +
        `WA: ${waSent ? '✅' : '⚠️'}  Email: ${emailSent ? '✅' : '➖'}\n` +
        `Contratto chiuso: \`${row.id}\``,
    );
  } catch (err) {
    console.warn(`mark-paid Telegram failed: ${(err as Error).message}`);
  }

  return c.json(
    {
      ok: true,
      contract_id: id,
      status: 'PAID',
      paid_at: paidAtIso,
      payment_amount_cents: paidAmount,
      wa_sent: waSent,
      email_sent: emailSent,
    },
    200,
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────

function buildPaymentWaTemplate(ctx: { dealerName: string }): string {
  return [
    `Bonifico ricevuto ${ctx.dealerName}, grazie. Operazione conclusa.`,
    ``,
    `A presto per il prossimo veicolo.`,
  ].join('\n');
}

function buildLucaPaidEmail(ctx: {
  dealerName: string;
  paidEur: number;
  feeEur: number;
  paymentBank: string;
  paymentReference: string;
  paidAtIso: string;
  contractId: string;
}): string {
  return `<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:auto;padding:20px;">
    <h2>✅ PAGATO €${ctx.paidEur} — ${escapeHtml(ctx.dealerName)}</h2>
    <table style="border-collapse:collapse;width:100%;margin:16px 0;">
      <tr><td style="padding:6px 0;"><b>Importo ricevuto:</b></td><td>€${ctx.paidEur}</td></tr>
      <tr><td style="padding:6px 0;"><b>Importo atteso:</b></td><td>€${ctx.feeEur}</td></tr>
      <tr><td style="padding:6px 0;"><b>Banca:</b></td><td>${escapeHtml(ctx.paymentBank)}</td></tr>
      <tr><td style="padding:6px 0;"><b>Causale:</b></td><td><code>${escapeHtml(ctx.paymentReference)}</code></td></tr>
      <tr><td style="padding:6px 0;"><b>Data:</b></td><td>${escapeHtml(ctx.paidAtIso)}</td></tr>
      <tr><td style="padding:6px 0;"><b>Contract ID:</b></td><td><code>${escapeHtml(ctx.contractId)}</code></td></tr>
    </table>
    <p style="color:#666;font-size:13px;">Contratto chiuso. Stato: PAID.</p>
  </body></html>`;
}

function buildDealerPaidEmail(ctx: { dealerName: string; paidEur: number }): string {
  return `<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:auto;padding:20px;">
    <h2>Pagamento ricevuto — ${escapeHtml(ctx.dealerName)}</h2>
    <p>Bonifico di <strong>€${ctx.paidEur}</strong> ricevuto correttamente. Operazione conclusa.</p>
    <p>A presto per il prossimo veicolo.</p>
    <p style="color:#666;font-size:13px;margin-top:24px;">Luca Ferretti — ARGOS</p>
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
