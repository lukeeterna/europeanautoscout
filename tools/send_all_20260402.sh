#!/bin/bash
# ARGOS — Invio completo 2 aprile 2026 ore 8:30
# Lanciato da cron automaticamente

cd /Users/macbook/Documents/combaretrovamiauto-enterprise

echo "$(date) — ARGOS Outreach Start" >> /tmp/argos_outreach.log

# 1. Day 7 TIER0
python3 tools/send_day7_tier0.py 2>&1 | tee -a /tmp/argos_outreach.log
sleep 10

# 2. Day 1 TIER1 (solo Enzo Car, Dream Car esclusa)
python3 tools/send_day1_tier1.py 2>&1 | tee -a /tmp/argos_outreach.log
sleep 10

# 3. Day 1 TIER1 Batch 2 (Autoline + GP Cars)
python3 tools/send_day1_tier1_batch2.py 2>&1 | tee -a /tmp/argos_outreach.log

echo "$(date) — ARGOS Outreach Complete" >> /tmp/argos_outreach.log

# Notifica Telegram se configurato
osascript -e 'display notification "ARGOS: 9 messaggi inviati a 5 dealer" with title "Outreach Completato"' 2>/dev/null
