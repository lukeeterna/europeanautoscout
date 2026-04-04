---
name: skill-loader
description: "Determina quali skill ARGOS caricare per il task corrente. Invoca PRIMA di task non banali."
user-invocable: true
allowed-tools: Read, Glob
---

# Skill Loader — Meta-Skill ARGOS

Quando ricevi un task, determina quali skill servono e suggerisci di invocarle.
NON caricare tutte le skill — solo quelle necessarie.

## Mapping Task → Skill

| Il task contiene... | Skill da invocare |
|---------------------|-------------------|
| outreach, contatta, day 1/3/7, wa, messaggio dealer | `/skill-argos` + `/skill-argos-orchestrator` |
| cove, score, veicolo, scoring, dossier, pdf | `/skill-cove` |
| debug, non funziona, errore, daemon, crash | `/skill-argos-debug` |
| dealer, discovery, territorio, scouting | `/skill-argos-intel-territoriale` |
| valida, verifica, controlla dati | `/skill-argos-validator` |
| browser, landing, screenshot, pagina | `/skill-browser-chrome` |
| ricerca, research, deep research | `/skill-deep-research` |
| marketing, copy, contenuto, brand | `/skill-marketing-official` |
| sales, account research, competitive intel | `/skill-sales-official` |
| deploy, infra, daemon, pm2, ssh | `/skill-argos-debug` |
| api, claude api, anthropic sdk | `/claude-api` |
| handover, fine sessione, chiudi | `/skill-handover` |

## Se il task non corrisponde a nessuna skill

Rispondi: "Nessuna skill specifica necessaria — procedo direttamente."

## Se servono piu' skill

Lista le skill nell'ordine in cui vanno invocate:
1. Prima la skill di validazione (se c'e' invio dealer)
2. Poi la skill operativa
3. Infine la skill di debug (se qualcosa fallisce)
