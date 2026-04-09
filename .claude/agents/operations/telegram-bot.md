---
name: telegram-bot
description: >
  Use when managing the Telegram notification bot, checking its status,
  or configuring alerts. Triggers: "telegram", "tg-bot", "notifica telegram",
  "bot notifiche".
tools: Bash, Read
model: haiku
maxTurns: 10
---

# Telegram Bot Agent — ARGOS Automotive

Manage the Telegram notification bot running on iMac via PM2.

## ENVIRONMENT

- Process: `tg-bot` on PM2 (iMac)
- SSH: `ssh gianlucadistasi@192.168.1.2`

## COMMANDS

```bash
ssh gianlucadistasi@192.168.1.2 "pm2 list | grep tg"
ssh gianlucadistasi@192.168.1.2 "pm2 logs tg-bot --lines 30"
ssh gianlucadistasi@192.168.1.2 "pm2 restart tg-bot"
```
