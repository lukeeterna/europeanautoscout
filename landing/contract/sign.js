// ─── ARGOS Contract Sign — frontend logic ──────────────────────────
// Reads token from URL, fetches public contract DTO, renders 10 stylized
// signatures from typed name, submits selected signature to /contract/sign.

(function () {
  'use strict';

  const WORKER_BASE = 'https://argos-proxy.gianlucanewtech.workers.dev';

  // 10 signature font slugs (must match server whitelist in src/lib/types.ts)
  // and CSS family names from Google Fonts <link>.
  const FONTS = [
    { slug: 'allura',          family: 'Allura, cursive',          fallbackBase: 36 },
    { slug: 'great-vibes',     family: '"Great Vibes", cursive',   fallbackBase: 36 },
    { slug: 'pacifico',        family: 'Pacifico, cursive',        fallbackBase: 30 },
    { slug: 'dancing-script',  family: '"Dancing Script", cursive',fallbackBase: 32 },
    { slug: 'sacramento',      family: 'Sacramento, cursive',      fallbackBase: 36 },
    { slug: 'tangerine',       family: 'Tangerine, cursive',       fallbackBase: 44 },
    { slug: 'yellowtail',      family: 'Yellowtail, cursive',      fallbackBase: 32 },
    { slug: 'kaushan-script',  family: '"Kaushan Script", cursive',fallbackBase: 28 },
    { slug: 'satisfy',         family: 'Satisfy, cursive',         fallbackBase: 30 },
    { slug: 'caveat',          family: '"Caveat", cursive',        fallbackBase: 34 },
  ];

  // ── State ──────────────────────────────────────────────────────────
  let contract = null;
  let selectedFont = null;
  let token = null;
  const $ = (id) => document.getElementById(id);

  // ── Init ───────────────────────────────────────────────────────────
  function getTokenFromPath() {
    // /contract/<token>  — token is 32 hex
    const m = location.pathname.match(/^\/contract\/([a-f0-9]{32})\/?$/);
    return m ? m[1] : null;
  }

  function showState(name) {
    for (const id of ['state-loading','state-error','state-signed','state-sign']) {
      const el = $(id);
      if (el) el.classList.toggle('hidden', id !== name);
    }
  }

  function showError(msg) {
    $('error-message').textContent = msg;
    showState('state-error');
  }

  // ── Fetch contract ────────────────────────────────────────────────
  async function loadContract() {
    token = getTokenFromPath();
    if (!token) {
      showError('Link non valido o malformato.');
      return;
    }
    try {
      const res = await fetch(`${WORKER_BASE}/api/v1/contract/${token}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (res.status === 404) {
        showError('Contratto non trovato. Verifichi il link.');
        return;
      }
      if (!res.ok) {
        showError(`Errore caricamento (HTTP ${res.status}).`);
        return;
      }
      contract = await res.json();
      renderRecap(contract);

      // Already-signed branch: status > DRAFT
      if (contract.status !== 'DRAFT') {
        if (contract.pdf_download_url) {
          $('signed-pdf-link').href = contract.pdf_download_url;
        }
        showState('state-signed');
        return;
      }

      buildSignatureGrid();
      attachFormListeners();
      showState('state-sign');
    } catch (err) {
      console.error(err);
      showError('Errore di rete. Riprovi tra poco.');
    }
  }

  // ── Render recap ──────────────────────────────────────────────────
  function renderRecap(c) {
    $('r-dealer').textContent = c.dealer_name || '—';
    const veh = [c.vehicle_year, c.vehicle_make, c.vehicle_model]
      .filter(Boolean).join(' ') || 'Da definire dopo la firma';
    $('r-vehicle').textContent = veh;
    const fee = (c.fee_eur != null) ? `€ ${Number(c.fee_eur).toLocaleString('it-IT', { minimumFractionDigits: 2 })}` : '—';
    $('r-fee').textContent = fee;
  }

  // ── Build 10 signature cards ──────────────────────────────────────
  function buildSignatureGrid() {
    const grid = $('sig-grid');
    grid.innerHTML = '';
    FONTS.forEach((f) => {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'sig-card text-left bg-white border-2 border-slate-200 rounded-md p-4 cursor-pointer';
      card.dataset.slug = f.slug;
      card.setAttribute('aria-label', `Scegli firma ${f.slug}`);
      card.innerHTML = `
        <div class="text-xs text-slate-500 mb-1">Stile: ${f.slug}</div>
        <div class="sig-preview text-3xl text-slate-900 truncate" style="font-family: ${f.family}; font-size: ${f.fallbackBase}px; line-height: 1.2;">
          —
        </div>`;
      card.addEventListener('click', () => selectFont(f.slug, card));
      grid.appendChild(card);
    });
    updatePreviews();
  }

  function selectFont(slug, cardEl) {
    selectedFont = slug;
    document.querySelectorAll('.sig-card').forEach((el) => el.classList.toggle('selected', el === cardEl));
    refreshSubmitState();
  }

  function fullName() {
    const fn = $('firstName').value.trim();
    const ln = $('lastName').value.trim();
    return (fn + ' ' + ln).trim();
  }

  function updatePreviews() {
    const name = fullName() || '—';
    document.querySelectorAll('.sig-preview').forEach((el) => {
      el.textContent = name;
    });
  }

  // ── Form / submit ─────────────────────────────────────────────────
  function attachFormListeners() {
    $('firstName').addEventListener('input', () => { updatePreviews(); refreshSubmitState(); });
    $('lastName').addEventListener('input',  () => { updatePreviews(); refreshSubmitState(); });
    $('consentFes').addEventListener('change', refreshSubmitState);
    $('sign-form').addEventListener('submit', onSubmit);
  }

  function refreshSubmitState() {
    const fn = $('firstName').value.trim();
    const ln = $('lastName').value.trim();
    const consent = $('consentFes').checked;
    const valid = fn.length >= 2 && ln.length >= 2 && selectedFont !== null && consent;
    $('submitBtn').disabled = !valid;
    if (valid) {
      $('submitHint').textContent = 'Pronto. Tocchi "Firma contratto".';
      $('submitHint').className = 'text-xs text-emerald-600 mt-2';
    } else {
      $('submitHint').textContent = 'Compili nome, cognome, scelga firma e accetti il consenso.';
      $('submitHint').className = 'text-xs text-slate-500 mt-2';
    }
  }

  async function onSubmit(ev) {
    ev.preventDefault();
    const btn = $('submitBtn');
    btn.disabled = true;
    btn.textContent = 'Firma in corso…';

    const payload = {
      token,
      signer_name: fullName(),
      signature_font: selectedFont,
      consent_fes: true,
    };

    try {
      const res = await fetch(`${WORKER_BASE}/api/v1/contract/sign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const code = data?.code || `HTTP_${res.status}`;
        throw new Error(`${code}: ${data?.error || 'errore sconosciuto'}`);
      }
      // Success: redirect to thank-you page
      const url = data.post_sign_url
        || `/contract/thank-you.html?id=${encodeURIComponent(data.contract_id || '')}`;
      window.location.href = url;
    } catch (err) {
      console.error(err);
      btn.disabled = false;
      btn.textContent = 'Firma contratto';
      alert('Firma fallita: ' + err.message + '\n\nRiprovi o contatti Luca al 328 153 6308.');
    }
  }

  // ── Boot ───────────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadContract);
  } else {
    loadContract();
  }
})();
