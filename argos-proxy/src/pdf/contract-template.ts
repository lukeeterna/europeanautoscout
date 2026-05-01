// ─── Contract PDF Template — pdf-lib + fontkit ─────────────────────
// 4 pages: header/parts → object/vehicle/fee → clausole+FES consent →
// signature embed + bundle evidence (timestamp, IP, UA truncated).
//
// FONT EMBEDDING: 10 Google Fonts TTF stored in argos-proxy/assets/fonts/,
// imported as ArrayBuffer modules via wrangler "Data" rule (wrangler.toml).
// fontkit handles the static + variable TTF formats Google ships.

import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import fontkit from '@pdf-lib/fontkit';
import type { ContractRow, SignatureFont } from '../lib/types';

// ── Static binary imports — bundled into Worker at build time ──────
import alluraTtf         from '../../assets/fonts/allura.ttf';
import greatVibesTtf     from '../../assets/fonts/great-vibes.ttf';
import pacificoTtf       from '../../assets/fonts/pacifico.ttf';
import dancingScriptTtf  from '../../assets/fonts/dancing-script.ttf';
import sacramentoTtf     from '../../assets/fonts/sacramento.ttf';
import tangerineTtf      from '../../assets/fonts/tangerine.ttf';
import yellowtailTtf     from '../../assets/fonts/yellowtail.ttf';
import kaushanScriptTtf  from '../../assets/fonts/kaushan-script.ttf';
import satisfyTtf        from '../../assets/fonts/satisfy.ttf';
import caveatTtf         from '../../assets/fonts/caveat.ttf';

const FONT_BUFFERS: Record<SignatureFont, ArrayBuffer> = {
  'allura':          alluraTtf,
  'great-vibes':     greatVibesTtf,
  'pacifico':        pacificoTtf,
  'dancing-script':  dancingScriptTtf,
  'sacramento':      sacramentoTtf,
  'tangerine':       tangerineTtf,
  'yellowtail':      yellowtailTtf,
  'kaushan-script':  kaushanScriptTtf,
  'satisfy':         satisfyTtf,
  'caveat':          caveatTtf,
};

export interface RenderParams {
  contract: ContractRow;
  signerName: string;
  font: SignatureFont;
  signedAtIso: string;
  signerIp: string | null;
  signerUa: string | null;
}

export async function renderContractPdf(
  params: RenderParams,
): Promise<Uint8Array> {
  const { contract, signerName, font, signedAtIso, signerIp, signerUa } = params;

  const pdf = await PDFDocument.create();
  pdf.registerFontkit(fontkit);

  // ── Body fonts (Helvetica standard, no embed) ──────────────────────
  const helvetica     = await pdf.embedFont(StandardFonts.Helvetica);
  const helveticaBold = await pdf.embedFont(StandardFonts.HelveticaBold);

  // ── Signature font: embedded TTF + subset to keep PDF small ────────
  const ttfBuf = FONT_BUFFERS[font];
  if (!ttfBuf) {
    throw new Error(`Font asset missing for slug: ${font}`);
  }
  const signatureFont = await pdf.embedFont(ttfBuf, { subset: true });

  const feeEur = (contract.fee_cents / 100).toFixed(2);
  const vehicleLine = [contract.vehicle_year, contract.vehicle_make, contract.vehicle_model]
    .filter((x) => x)
    .join(' ') || 'Veicolo da definire';

  // ─── Page 1: Header + Parts ────────────────────────────────────────
  const p1 = pdf.addPage([595.28, 841.89]); // A4
  let y = 800;
  p1.drawText('CONTRATTO DI MANDATO PROFESSIONALE', {
    x: 50, y, size: 16, font: helveticaBold, color: rgb(0, 0, 0),
  });
  y -= 24;
  p1.drawText('Servizio scouting veicoli — ARGOS Automotive', {
    x: 50, y, size: 11, font: helvetica, color: rgb(0.3, 0.3, 0.3),
  });
  y -= 40;
  p1.drawText(`Contract ID: ${contract.id}`, { x: 50, y, size: 9, font: helvetica });
  y -= 14;
  p1.drawText(`Data emissione: ${contract.created_at.slice(0, 10)}`, {
    x: 50, y, size: 9, font: helvetica,
  });

  y -= 36;
  p1.drawText('PARTI', { x: 50, y, size: 12, font: helveticaBold });
  y -= 18;
  p1.drawText('Mandante (Dealer):', { x: 50, y, size: 10, font: helveticaBold });
  y -= 14;
  p1.drawText(contract.dealer_name, { x: 60, y, size: 11, font: helvetica });
  y -= 14;
  p1.drawText(`Tel: ${contract.dealer_phone}`, { x: 60, y, size: 10, font: helvetica });
  if (contract.dealer_email) {
    y -= 14;
    p1.drawText(`Email: ${contract.dealer_email}`, { x: 60, y, size: 10, font: helvetica });
  }

  y -= 26;
  p1.drawText('Mandatario (Operatore):', { x: 50, y, size: 10, font: helveticaBold });
  y -= 14;
  p1.drawText('Luca Ferretti — ARGOS Automotive', { x: 60, y, size: 11, font: helvetica });
  y -= 14;
  p1.drawText('Email: ferretti.argosautomotive@gmail.com  ·  Tel: +39 328 153 6308',
    { x: 60, y, size: 9, font: helvetica });

  // ─── Page 2: Object + Vehicle + Fee ───────────────────────────────
  const p2 = pdf.addPage([595.28, 841.89]);
  y = 800;
  p2.drawText('OGGETTO DEL MANDATO', { x: 50, y, size: 14, font: helveticaBold });
  y -= 24;
  const objectText =
    'Il mandatario svolge attivita di scouting di veicoli usati su mercato europeo, ' +
    'consegnando al mandante una shortlist di opportunita verificate. La fee si paga ' +
    'esclusivamente a successo, dopo consegna documenti del veicolo selezionato.';
  drawWrappedText(p2, objectText, 50, y, 495, 11, helvetica);
  y -= 80;

  p2.drawText('VEICOLO TARGET', { x: 50, y, size: 12, font: helveticaBold });
  y -= 18;
  p2.drawText(vehicleLine, { x: 60, y, size: 11, font: helvetica });
  if (contract.vehicle_vin) {
    y -= 14;
    p2.drawText(`VIN: ${contract.vehicle_vin}`, { x: 60, y, size: 10, font: helvetica });
  }
  if (contract.vehicle_price_eu_cents) {
    y -= 14;
    p2.drawText(
      `Prezzo target indicativo: € ${(contract.vehicle_price_eu_cents / 100).toFixed(2)}`,
      { x: 60, y, size: 10, font: helvetica },
    );
  }

  y -= 36;
  p2.drawText('FEE', { x: 50, y, size: 12, font: helveticaBold });
  y -= 18;
  p2.drawText(`Fee fissa: € ${feeEur} (success fee)`,
    { x: 60, y, size: 11, font: helvetica });
  y -= 14;
  p2.drawText('Pagamento: bonifico bancario dopo consegna documenti del veicolo.',
    { x: 60, y, size: 10, font: helvetica });
  y -= 14;
  p2.drawText('Nessun anticipo. Nessun pagamento online.',
    { x: 60, y, size: 10, font: helvetica, color: rgb(0.3, 0.3, 0.3) });

  // ─── Page 3: Clausole + FES Consent ───────────────────────────────
  const p3 = pdf.addPage([595.28, 841.89]);
  y = 800;
  p3.drawText('CLAUSOLE PRINCIPALI', { x: 50, y, size: 14, font: helveticaBold });
  y -= 24;

  const clauses = [
    '1. Mandato non esclusivo — il dealer mantiene liberta di approvigionamento autonomo.',
    '2. Scouting senza esclusiva geografica — fonti EU.',
    '3. Fee maturata solo dopo accettazione del veicolo proposto e consegna documenti.',
    '4. Foro competente: Tribunale di Roma (sede mandatario).',
    '5. Recesso: ognuna delle parti puo recedere con preavviso scritto 7 giorni.',
    '6. Privacy: trattamento dati ex art. 6 lett. b) GDPR (esecuzione contratto).',
  ];
  for (const cl of clauses) {
    drawWrappedText(p3, cl, 50, y, 495, 10, helvetica);
    y -= 28;
  }

  y -= 20;
  p3.drawText('FIRMA ELETTRONICA SEMPLICE (FES) — eIDAS art.3 / CAD art.20',
    { x: 50, y, size: 11, font: helveticaBold });
  y -= 18;
  const fesConsent =
    'Il mandante dichiara di accettare la firma elettronica come equivalente legale ' +
    'della firma autografa per il presente contratto, ai sensi dell\'art. 20 CAD e ' +
    'del Regolamento eIDAS art. 3 (FES). Consenso esplicito reso al momento della firma ' +
    'tramite checkbox dedicata sulla pagina di firma.';
  drawWrappedText(p3, fesConsent, 50, y, 495, 10, helvetica);

  // ─── Page 4: Signature + Evidence Bundle ──────────────────────────
  const p4 = pdf.addPage([595.28, 841.89]);
  y = 800;
  p4.drawText('SOTTOSCRIZIONE', { x: 50, y, size: 14, font: helveticaBold });
  y -= 30;
  p4.drawText(`Per il Mandante — ${contract.dealer_name}`, {
    x: 50, y, size: 11, font: helveticaBold,
  });
  y -= 60;
  // Signature rendering: large size in chosen font
  p4.drawText(signerName, { x: 60, y, size: 36, font: signatureFont });
  y -= 20;
  p4.drawLine({
    start: { x: 50, y }, end: { x: 350, y },
    thickness: 0.5, color: rgb(0.5, 0.5, 0.5),
  });
  y -= 14;
  p4.drawText(`(${signerName} — firma elettronica semplice, font: ${font})`, {
    x: 50, y, size: 9, font: helvetica, color: rgb(0.4, 0.4, 0.4),
  });

  y -= 50;
  p4.drawText('BUNDLE EVIDENZA FES', { x: 50, y, size: 11, font: helveticaBold });
  y -= 16;
  const bundle: Array<[string, string]> = [
    ['Timestamp firma', signedAtIso],
    ['IP firmatario', signerIp ?? 'n/d'],
    ['User-Agent', (signerUa ?? 'n/d').slice(0, 80)],
    ['Token sessione', contract.signature_token],
    ['WhatsApp conv ID', contract.signature_wa_conv_id ?? 'n/d'],
    ['Consenso FES', 'esplicito (checkbox required)'],
    ['SHA256 PDF', '(calcolato post-render, allegato in audit_log)'],
  ];
  for (const [k, v] of bundle) {
    p4.drawText(`${k}: ${v}`, { x: 50, y, size: 9, font: helvetica });
    y -= 14;
  }

  return await pdf.save();
}

// ── Helper: simple word-wrap text drawing ─────────────────────────────
function drawWrappedText(
  page: import('pdf-lib').PDFPage,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  size: number,
  font: import('pdf-lib').PDFFont,
): void {
  const words = text.split(' ');
  let line = '';
  let currentY = y;
  const lineHeight = size + 3;

  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    const width = font.widthOfTextAtSize(test, size);
    if (width > maxWidth && line) {
      page.drawText(line, { x, y: currentY, size, font });
      line = word;
      currentY -= lineHeight;
    } else {
      line = test;
    }
  }
  if (line) {
    page.drawText(line, { x, y: currentY, size, font });
  }
}
