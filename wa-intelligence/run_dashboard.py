#!/usr/bin/env python3
"""
run_dashboard.py — ARGOS Dashboard Launcher
Workaround: wa-intelligence ha un trattino, non e' un modulo Python valido.
Questo script aggiunge il path corretto e lancia uvicorn.

PM2: pm2 start run_dashboard.py --name argos-dashboard --interpreter python3
"""

import sys
import os

# Aggiungi wa-intelligence al path cosi' 'dashboard' diventa importabile
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import uvicorn

if __name__ == '__main__':
    uvicorn.run(
        'dashboard.app:app',
        host='0.0.0.0',
        port=8080,
        log_level='info',
    )
