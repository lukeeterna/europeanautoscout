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

const fs      = require('fs');
const path    = require('path');
const HOME    = process.env.HOME || '/Users/gianlucadistasi';
const BASE    = path.join(HOME, 'Documents/app-antigravity-auto');
const INTEL   = path.join(BASE, 'wa-intelligence');

// Carica .env da wa-intelligence/ (mai hardcoded nel codice)
const dotEnvPath = path.join(INTEL, '.env');
const dotEnv = {};
if (fs.existsSync(dotEnvPath)) {
    fs.readFileSync(dotEnvPath, 'utf8').split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
            const eqIdx = trimmed.indexOf('=');
            dotEnv[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
        }
    });
}

// Variabili d'ambiente condivise
const SHARED_ENV = {
    NODE_ENV:               'production',
    TZ:                     'Europe/Rome',
    ARGOS_DB_PATH:          path.join(BASE, 'dealer_network.sqlite'),
    ARGOS_TELEGRAM_CHAT_ID: dotEnv.ARGOS_TELEGRAM_CHAT_ID || '931063621',
    ARGOS_TELEGRAM_TOKEN:   dotEnv.ARGOS_TELEGRAM_TOKEN   || '',
    WA_CLIENT_ID:           dotEnv.WA_CLIENT_ID           || 'argos-business',
    OPENROUTER_API_KEY:     dotEnv.OPENROUTER_API_KEY     || '',
    OPENROUTER_MODEL:       dotEnv.OPENROUTER_MODEL       || 'anthropic/claude-haiku-4-5',
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
