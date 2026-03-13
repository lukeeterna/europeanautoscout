/**
 * ecosystem.config.js — ARGOS™ PM2 Process Manager
 * CoVe 2026 | Enterprise Grade
 *
 * AVVIO:   pm2 start ecosystem.config.js
 * STOP:    pm2 stop all
 * STATUS:  pm2 list
 * LOG:     pm2 logs
 * RELOAD:  pm2 reload all   (zero-downtime)
 * PERSIST: pm2 save && pm2 startup launchd
 *
 * Processi gestiti:
 *   1. argos-wa-daemon    — WA listener persistente (Node.js)
 *   2. argos-tg-bot       — Telegram human-in-loop (Python)
 */

'use strict';

const path    = require('path');
const HOME    = process.env.HOME || '/Users/gianlucadistasi';
const BASE    = path.join(HOME, 'Documents/app-antigravity-auto');
const INTEL   = path.join(BASE, 'wa-intelligence');

// Variabili d'ambiente condivise (SENZA credenziali — quelle vanno in .env)
const SHARED_ENV = {
    NODE_ENV:             'production',
    TZ:                   'Europe/Rome',
    ARGOS_DB_PATH:        path.join(BASE, 'dealer_network.duckdb'),
    ARGOS_TELEGRAM_CHAT_ID: '931063621',   // Chat ID Telegram Luke
    // ARGOS_TELEGRAM_TOKEN: letto da .env — mai hardcoded
};

module.exports = {
    apps: [
        // ── 1. WA Intelligence Daemon ────────────────────────
        {
            name:             'argos-wa-daemon',
            script:           path.join(INTEL, 'wa-daemon.js'),
            cwd:              INTEL,
            interpreter:      'node',

            // Restart policy
            autorestart:      true,
            watch:            false,         // no hot-reload in prod
            max_restarts:     10,
            min_uptime:       '30s',         // < 30s = crash loop
            restart_delay:    5000,          // 5s tra restart

            // Risorse iMac 2012 (8GB RAM disponibile)
            max_memory_restart: '512M',

            // Log
            log_file:         '/tmp/argos-wa-daemon-combined.log',
            out_file:         '/tmp/argos-wa-daemon-out.log',
            error_file:       '/tmp/argos-wa-daemon-err.log',
            log_date_format:  'DD/MM/YYYY HH:mm:ss',
            merge_logs:       true,

            env: {
                ...SHARED_ENV,
            },

            // Graceful shutdown: aspetta max 10s prima di SIGKILL
            kill_timeout:     10000,
            wait_ready:       false,
            listen_timeout:   8000,
        },

        // ── 2. Telegram Bot Human-in-Loop ────────────────────
        {
            name:             'argos-tg-bot',
            script:           path.join(INTEL, 'telegram-handler.py'),
            cwd:              INTEL,
            interpreter:      'python3',

            autorestart:      true,
            watch:            false,
            max_restarts:     20,
            min_uptime:       '10s',
            restart_delay:    3000,

            max_memory_restart: '128M',

            log_file:         '/tmp/argos-tg-bot-combined.log',
            out_file:         '/tmp/argos-tg-bot-out.log',
            error_file:       '/tmp/argos-tg-bot-err.log',
            log_date_format:  'DD/MM/YYYY HH:mm:ss',
            merge_logs:       true,

            env: {
                ...SHARED_ENV,
            },
        },
    ],
};
