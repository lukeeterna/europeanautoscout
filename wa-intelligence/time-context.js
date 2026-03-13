/**
 * time-context.js — ARGOS™ Time Awareness Module
 * CoVe 2026 | Enterprise Grade
 *
 * RESPONSABILITÀ: ogni componente del sistema che importa questo modulo
 * riceve SEMPRE il contesto temporale completo e aggiornato.
 * Nessun agente può agire senza sapere esattamente dove si trova nel tempo.
 */

'use strict';

const TIMEZONE = 'Europe/Rome';

// ── Ore di business (lun-ven) ─────────────────────────────────
const BUSINESS_HOURS = { start: 9, end: 18 };

// ── Soglie di warning per azioni scadute ─────────────────────
const WARNING_HOURS_BEFORE  = 2;   // allerta 2h prima della scadenza
const CRITICAL_HOURS_BEFORE = 0.5; // allerta 30min prima

/**
 * Ritorna il datetime corrente nel fuso orario IT.
 * Usato da TUTTI i componenti — mai usare `new Date()` direttamente.
 */
function nowIT() {
    return new Date(new Date().toLocaleString('en-US', { timeZone: TIMEZONE }));
}

/**
 * Formatta una data in formato italiano leggibile.
 */
function formatIT(date) {
    if (!date) return 'N/A';
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleString('it-IT', {
        timeZone: TIMEZONE,
        weekday: 'long',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Calcola quanti giorni interi sono trascorsi da una data.
 */
function daysElapsed(fromDate) {
    const from = fromDate instanceof Date ? fromDate : new Date(fromDate);
    const now  = nowIT();
    const diffMs = now.getTime() - from.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Calcola quante ore sono trascorse da una data.
 */
function hoursElapsed(fromDate) {
    const from = fromDate instanceof Date ? fromDate : new Date(fromDate);
    const now  = nowIT();
    return (now.getTime() - from.getTime()) / (1000 * 60 * 60);
}

/**
 * Calcola quanti minuti mancano a una data target.
 * Negativo = scaduto.
 */
function minutesUntil(targetDate) {
    const target = targetDate instanceof Date ? targetDate : new Date(targetDate);
    const now    = nowIT();
    return (target.getTime() - now.getTime()) / (1000 * 60);
}

/**
 * Verifica se l'ora corrente è in orario business.
 */
function isBusinessHours() {
    const now  = nowIT();
    const hour = now.getHours();
    const day  = now.getDay(); // 0=domenica, 6=sabato
    if (day === 0 || day === 6) return false;
    return hour >= BUSINESS_HOURS.start && hour < BUSINESS_HOURS.end;
}

/**
 * Aggiunge N giorni a una data, saltando sabato e domenica
 * e mantenendo l'orario originale.
 */
function addBusinessDays(fromDate, days) {
    const date = new Date(fromDate);
    let added = 0;
    while (added < days) {
        date.setDate(date.getDate() + 1);
        const dow = date.getDay();
        if (dow !== 0 && dow !== 6) added++;
    }
    return date;
}

/**
 * Calcola la scadenza del prossimo step per un dealer.
 *
 * @param {Date}   lastContactAt  - data/ora ultimo contatto
 * @param {string} currentStep    - es. 'WA_DAY1_SENT'
 * @returns {object} { nextStep, deadline, status, urgency }
 */
function calculateNextDeadline(lastContactAt, currentStep) {
    const from = lastContactAt instanceof Date ? lastContactAt : new Date(lastContactAt);
    const now  = nowIT();

    const STEP_MAP = {
        'WA_DAY1_SENT':    { next: 'EMAIL_DAY7',  calDays: 7  },
        'EMAIL_DAY7_SENT': { next: 'WA_DAY12',    calDays: 5  }, // 5 giorni dopo email = day 12 totale
        'WA_DAY12_SENT':   { next: 'CLOSED_TIMEOUT', calDays: 7 },
    };

    const mapping = STEP_MAP[currentStep];
    if (!mapping) return { nextStep: 'MANUAL_CHECK', deadline: null, status: 'UNKNOWN', urgency: 'LOW' };

    // Usa giorni di calendario (non business) per sequenza WA
    const deadline = new Date(from);
    deadline.setDate(deadline.getDate() + mapping.calDays);

    const minsUntil   = minutesUntil(deadline);
    const hoursUntilN = minsUntil / 60;

    let status, urgency;
    if (minsUntil < 0) {
        status  = 'OVERDUE';
        urgency = 'CRITICAL';
    } else if (hoursUntilN <= CRITICAL_HOURS_BEFORE) {
        status  = 'IMMINENT';
        urgency = 'CRITICAL';
    } else if (hoursUntilN <= WARNING_HOURS_BEFORE) {
        status  = 'WARNING';
        urgency = 'HIGH';
    } else {
        status  = 'ON_TRACK';
        urgency = 'LOW';
    }

    return {
        nextStep:      mapping.next,
        deadline,
        deadlineLabel: formatIT(deadline),
        hoursUntil:    Math.round(hoursUntilN * 10) / 10,
        daysUntil:     Math.round(hoursUntilN / 24 * 10) / 10,
        status,
        urgency,
    };
}

/**
 * Genera il "context block" completo da iniettare in ogni prompt agente.
 * Nessun agente deve ignorare questo blocco.
 *
 * @param {object} dealer - riga DuckDB con le info dealer
 */
function buildAgentTimeContext(dealer = {}) {
    const now = nowIT();

    const ctx = {
        // ── Temporale corrente ──────────────────────────────
        now_iso:          now.toISOString(),
        now_it:           formatIT(now),
        day_of_week:      now.toLocaleDateString('it-IT', { weekday: 'long', timeZone: TIMEZONE }),
        is_business_hours: isBusinessHours(),
        hour_it:          now.getHours(),
        week_number:      getWeekNumber(now),

        // ── Dealer-specific (se disponibili) ─────────────────
        dealer_name:      dealer.dealer_name || null,
        persona_type:     dealer.persona_type || null,
        current_step:     dealer.current_step || null,
        days_since_contact: dealer.last_contact_at
            ? daysElapsed(dealer.last_contact_at)
            : null,
        hours_since_contact: dealer.last_contact_at
            ? Math.round(hoursElapsed(dealer.last_contact_at) * 10) / 10
            : null,
    };

    // Aggiungi deadline calcolata se step noto
    if (dealer.current_step && dealer.last_contact_at) {
        const deadline = calculateNextDeadline(dealer.last_contact_at, dealer.current_step);
        ctx.next_step         = deadline.nextStep;
        ctx.deadline_it       = deadline.deadlineLabel;
        ctx.hours_until_next  = deadline.hoursUntil;
        ctx.deadline_status   = deadline.status;
        ctx.deadline_urgency  = deadline.urgency;
    }

    return ctx;
}

/**
 * Ritorna il numero di settimana ISO dell'anno.
 */
function getWeekNumber(date) {
    const d     = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

/**
 * Formatta il time context come stringa leggibile per log/Telegram.
 */
function formatContextForLog(ctx) {
    const bh = ctx.is_business_hours ? '✅ orario business' : '⚠️ fuori orario business';
    let lines = [
        `📅 ${ctx.now_it} [${ctx.day_of_week}] — ${bh}`,
    ];
    if (ctx.dealer_name) {
        lines.push(`👤 ${ctx.dealer_name} (${ctx.persona_type || 'N/A'}) — step: ${ctx.current_step || 'N/A'}`);
        if (ctx.days_since_contact !== null) {
            lines.push(`⏱  ${ctx.days_since_contact} giorni / ${ctx.hours_since_contact}h dall'ultimo contatto`);
        }
        if (ctx.next_step) {
            const emoji = ctx.deadline_urgency === 'CRITICAL' ? '🚨' :
                          ctx.deadline_urgency === 'HIGH'     ? '⚠️' : 'ℹ️';
            lines.push(`${emoji} Prossimo step: ${ctx.next_step} — ${ctx.deadline_it} [${ctx.deadline_status}]`);
        }
    }
    return lines.join('\n');
}

module.exports = {
    nowIT,
    formatIT,
    daysElapsed,
    hoursElapsed,
    minutesUntil,
    isBusinessHours,
    addBusinessDays,
    calculateNextDeadline,
    buildAgentTimeContext,
    formatContextForLog,
    TIMEZONE,
    BUSINESS_HOURS,
};
