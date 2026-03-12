#!/bin/bash
# start_bot.sh — Avvia @CombaRetrovamiautoNotifierbot
# Uso: ./scripts/start_bot.sh [--daemon]

WORKSPACE=~/Documents/app-antigravity-auto
VENV=$WORKSPACE/venv
BOT_DIR=$WORKSPACE/python/bot
LOG_FILE=$WORKSPACE/logs/bot.log
PID_FILE=$WORKSPACE/logs/bot.pid

# Ensure log directory exists
mkdir -p $WORKSPACE/logs

# Check if virtual environment exists
if [ ! -d "$VENV" ]; then
    echo "Errore: Virtual environment non trovato in $VENV"
    echo "Crea l'ambiente virtuale con: python3 -m venv $VENV"
    exit 1
fi

# Activate virtual environment
source $VENV/bin/activate

# Change to bot directory
cd $BOT_DIR

# Install dependencies if needed
pip install -q python-telegram-bot>=21.0 pydantic-settings python-dotenv duckdb 2>/dev/null

if [ "$1" == "--daemon" ]; then
    # Check if already running
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Bot già in esecuzione (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    # Start in background
    nohup python bot_main.py >> $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    echo "Bot avviato in background. PID: $!"
    echo "Log: $LOG_FILE"
    echo "Per fermare: kill $(cat $PID_FILE)"
elif [ "$1" == "--stop" ]; then
    if [ -f "$PID_FILE" ]; then
        kill $(cat $PID_FILE) 2>/dev/null
        rm -f $PID_FILE
        echo "Bot fermato."
    else
        echo "Nessun PID file trovato."
    fi
elif [ "$1" == "--status" ]; then
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Bot in esecuzione (PID: $(cat $PID_FILE))"
        echo "Ultimo log:"
        tail -n 5 $LOG_FILE
    else
        echo "Bot non in esecuzione."
    fi
else
    # Start in foreground
    echo "Avvio bot in foreground... (Ctrl+C per fermare)"
    python bot_main.py
fi