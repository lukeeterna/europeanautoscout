/**
 * ecosystem.config.js — ARGOS S292 production process manager.
 *
 * Transport remains single-writer: runtime_entrypoint.py performs only the
 * first-boot PAUSED invariant and then execs wa-daemon.js. No second transport
 * process exists. The scheduler is queue-only and defaults to disabled until
 * the production rollout explicitly sets ARGOS_AUTOMATION_ENABLED=1.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const INTEL = __dirname;
const BASE = path.dirname(INTEL);
const PYTHON_313 = '/usr/local/bin/python3.13';

const dotEnvPath = path.join(INTEL, '.env');
const dotEnv = {};
if (fs.existsSync(dotEnvPath)) {
    fs.readFileSync(dotEnvPath, 'utf8').split('\n').forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) return;
        const eqIdx = trimmed.indexOf('=');
        let value = trimmed.slice(eqIdx + 1).trim();
        if ((value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
        }
        dotEnv[trimmed.slice(0, eqIdx).trim()] = value;
    });
}

const SHARED_ENV = {
    NODE_ENV: 'production',
    TZ: 'Europe/Rome',
    // A release tree must point to the canonical external state DB rather than
    // silently creating/using a DB next to the release checkout.
    ARGOS_DB_PATH: dotEnv.ARGOS_DB_PATH || path.join(BASE, 'dealer_network.sqlite'),
    BRIDGE_DB_PATH: dotEnv.BRIDGE_DB_PATH || '',

    // Transport mode is non-secret and may be visible to observability processes.
    ARGOS_WA_TRANSPORT: dotEnv.ARGOS_WA_TRANSPORT || 'wwebjs',

    // Preserve the existing LocalAuth identity/path for legacy rollback.
    ARGOS_WA_CLIENT_ID: dotEnv.ARGOS_WA_CLIENT_ID || dotEnv.WA_CLIENT_ID || 'argos-business',
    ARGOS_WA_SESSION_DIR: dotEnv.ARGOS_WA_SESSION_DIR || path.join(BASE, 'wa-sender'),
    CHROME_EXECUTABLE_PATH: dotEnv.CHROME_EXECUTABLE_PATH || '',
    ARGOS_WA_PORT: dotEnv.ARGOS_WA_PORT || '9191',
    ARGOS_BIND_HOST: dotEnv.ARGOS_BIND_HOST || '127.0.0.1',
    ARGOS_API_KEY: dotEnv.ARGOS_API_KEY || dotEnv.WA_API_KEY || '',
    ARGOS_PYTHON: dotEnv.ARGOS_PYTHON || PYTHON_313,
    ARGOS_BRIDGE_POLL_MS: dotEnv.ARGOS_BRIDGE_POLL_MS || dotEnv.BRIDGE_POLL_INTERVAL_MS || '15000',
    ARGOS_GLOBAL_DAILY_LIMIT: dotEnv.ARGOS_GLOBAL_DAILY_LIMIT || '40',
    ARGOS_DEALER_DAILY_LIMIT: dotEnv.ARGOS_DEALER_DAILY_LIMIT || '3',
    ARGOS_BUSINESS_START_HOUR: dotEnv.ARGOS_BUSINESS_START_HOUR || '9',
    ARGOS_BUSINESS_END_HOUR: dotEnv.ARGOS_BUSINESS_END_HOUR || '18',
    ARGOS_BUSINESS_DAYS: dotEnv.ARGOS_BUSINESS_DAYS || '1,2,3,4,5',

    // Non-secret approved template names are shared with the queue-only scheduler
    // so it can persist the exact Meta template payload before the single writer
    // claims a proactive row. Secrets stay daemon-only below.
    META_WA_TEMPLATE_LANGUAGE: dotEnv.META_WA_TEMPLATE_LANGUAGE || 'it',
    META_WA_TEMPLATE_DAY1_NAME: dotEnv.META_WA_TEMPLATE_DAY1_NAME || '',
    META_WA_TEMPLATE_DAY7_NAME: dotEnv.META_WA_TEMPLATE_DAY7_NAME || '',
    META_WA_TEMPLATE_DAY12_NAME: dotEnv.META_WA_TEMPLATE_DAY12_NAME || '',

    // Queue-only zero-founder loop. Intentionally OFF until rollout gate C10.
    ARGOS_AUTOMATION_ENABLED: dotEnv.ARGOS_AUTOMATION_ENABLED || '0',
    ARGOS_SCHEDULER_INTERVAL_SECONDS: dotEnv.ARGOS_SCHEDULER_INTERVAL_SECONDS || '900',

    // Existing observability/admin processes retain their current secrets.
    ARGOS_TELEGRAM_CHAT_ID: dotEnv.ARGOS_TELEGRAM_CHAT_ID || '931063621',
    ARGOS_TELEGRAM_TOKEN: dotEnv.ARGOS_TELEGRAM_TOKEN || '',
    GMAIL_FERRETTI_EMAIL: dotEnv.GMAIL_FERRETTI_EMAIL || '',
    GMAIL_FERRETTI_APP_PASSWORD: dotEnv.GMAIL_FERRETTI_APP_PASSWORD || '',
    ARGOS_PROXY_URL: dotEnv.ARGOS_PROXY_URL || '',
    ARGOS_ADMIN_SECRET: dotEnv.ARGOS_ADMIN_SECRET || '',
};

// Official WhatsApp Cloud API credentials are least-privilege daemon-only.
// Empty values fail closed when ARGOS_WA_TRANSPORT=cloud.
const WA_DAEMON_ENV = {
    ...SHARED_ENV,
    META_GRAPH_API_VERSION: dotEnv.META_GRAPH_API_VERSION || 'v25.0',
    META_WA_ACCESS_TOKEN: dotEnv.META_WA_ACCESS_TOKEN || '',
    META_WA_PHONE_NUMBER_ID: dotEnv.META_WA_PHONE_NUMBER_ID || '',
    META_WA_WABA_ID: dotEnv.META_WA_WABA_ID || '',
    META_WA_WEBHOOK_VERIFY_TOKEN: dotEnv.META_WA_WEBHOOK_VERIFY_TOKEN || '',
    META_APP_SECRET: dotEnv.META_APP_SECRET || '',
};

const common = {
    autorestart: true,
    watch: false,
    merge_logs: true,
};

module.exports = {
    apps: [
        {
            name: 'argos-wa-daemon',
            script: path.join(INTEL, 'runtime_entrypoint.py'),
            cwd: INTEL,
            interpreter: PYTHON_313,
            ...common,
            max_restarts: 10,
            min_uptime: '30s',
            restart_delay: 5000,
            max_memory_restart: '512M',
            log_file: '/tmp/argos-wa-daemon-combined.log',
            out_file: '/tmp/argos-wa-daemon-out.log',
            error_file: '/tmp/argos-wa-daemon-err.log',
            log_date_format: 'DD/MM/YYYY HH:mm:ss',
            env: { ...WA_DAEMON_ENV },
            kill_timeout: 10000,
            wait_ready: false,
            listen_timeout: 8000,
        },
        {
            name: 'argos-outreach-scheduler',
            script: path.join(INTEL, 'outreach_scheduler.py'),
            cwd: INTEL,
            interpreter: PYTHON_313,
            ...common,
            max_restarts: 10,
            min_uptime: '30s',
            restart_delay: 5000,
            max_memory_restart: '96M',
            log_file: '/tmp/argos-outreach-scheduler-combined.log',
            out_file: '/tmp/argos-outreach-scheduler-out.log',
            error_file: '/tmp/argos-outreach-scheduler-err.log',
            log_date_format: 'DD/MM/YYYY HH:mm:ss',
            env: { ...SHARED_ENV },
            kill_timeout: 5000,
        },
        {
            name: 'argos-tg-bot',
            script: path.join(INTEL, 'telegram-handler.py'),
            cwd: INTEL,
            interpreter: PYTHON_313,
            ...common,
            max_restarts: 20,
            min_uptime: '10s',
            restart_delay: 3000,
            max_memory_restart: '128M',
            log_file: '/tmp/argos-tg-bot-combined.log',
            out_file: '/tmp/argos-tg-bot-out.log',
            error_file: '/tmp/argos-tg-bot-err.log',
            log_date_format: 'DD/MM/YYYY HH:mm:ss',
            env: { ...SHARED_ENV },
        },
        {
            name: 'argos-cf-monitor',
            script: path.join(INTEL, 'cf_alert_monitor.py'),
            cwd: INTEL,
            interpreter: PYTHON_313,
            ...common,
            max_restarts: 20,
            min_uptime: '30s',
            restart_delay: 10000,
            max_memory_restart: '128M',
            log_file: '/tmp/argos-cf-monitor-combined.log',
            out_file: '/tmp/argos-cf-monitor-out.log',
            error_file: '/tmp/argos-cf-monitor-err.log',
            log_date_format: 'DD/MM/YYYY HH:mm:ss',
            env: { ...SHARED_ENV },
        },
        {
            name: 'argos-dashboard',
            script: path.join(INTEL, 'run_dashboard.py'),
            cwd: INTEL,
            interpreter: PYTHON_313,
            ...common,
            max_restarts: 20,
            min_uptime: '30s',
            restart_delay: 5000,
            max_memory_restart: '256M',
            log_file: '/tmp/argos-dashboard-combined.log',
            out_file: '/tmp/argos-dashboard-out.log',
            error_file: '/tmp/argos-dashboard-err.log',
            log_date_format: 'DD/MM/YYYY HH:mm:ss',
            env: {
                ...SHARED_ENV,
                ARGOS_DASHBOARD_PASSWORD: dotEnv.ARGOS_DASHBOARD_PASSWORD || '',
            },
        },
    ],
};