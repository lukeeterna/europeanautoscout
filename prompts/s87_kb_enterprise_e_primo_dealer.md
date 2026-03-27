# S87 — KB Enterprise + Primo Outreach Dealer Reale

## Contesto — LEGGI PRIMA DI FARE QUALSIASI COSA

L'agente Luca Ferretti e' LIVE e testato E2E (S86).
Pipeline completa: messaggio dealer → debounce 15s → classificazione → Haiku 4.5 + KB → multi-msg con typing.
Costo: $0.002/risposta. Sessione WA persistente. Anti-ban attivo.

## Cosa funziona (NON toccare)

```
wa-intelligence/wa-daemon.js         ← message_create + LID + HumanLike + buffer 15s
wa-intelligence/response-analyzer.py ← SYSTEM_PROMPT imperfezioni + JSON multi-msg + KB injection
wa-intelligence/argos_knowledge_base.md ← FAQ 7 sezioni + 8 obiezioni
```

## Priorita' S87 — in ordine

### 1. Arricchire Knowledge Base (ridurre carico Haiku)
La KB attuale ha 7 sezioni base. Servono contenuti enterprise:
- Case study reali (anche fittizi ma realistici): "BMW X3 2022, margine €5.200 per dealer Foggia"
- FAQ avanzate fiscalita': TD17, reverse charge, regime margine, F24
- Dettagli trasporto per tratta: Monaco→Foggia, Bruxelles→Napoli, Amsterdam→Cosenza
- Obiezioni specifiche per zona: "nel mio paese non si vendono tedesche"
- Risposte calibrate per ogni archetipo (NARCISO/RAGIONIERE/TECNICO/RELAZIONALE)
- Piu' contenuto in KB = meno token Haiku = meno costi

### 2. Fix edge-tts su iMac
I vocali Day 7 falliscono: `edge-tts: command not found`
```bash
ssh gianlucadistasi@192.168.1.2
pip3 install edge-tts  # o pip3.9 install edge-tts
```

### 3. Primo outreach REALE — Domenico (Stile Car)
Phase 4 del roadmap. Serve:
- Veicolo REALE con margine > €2.500 (il BMW X3 aveva margine €699 — insufficiente)
- Fresh scrape per trovare veicoli con margine adeguato
- Dossier PDF completo
- Day 1 message NARCISO calibrato

### 4. Preparare WA Cloud API (background)
- Creare Meta Business Manager (gratis, 3-14 gg verifica)
- Preparare 2-3 template messages per approvazione
- L'architettura e' gia' transport-agnostic

## Infra

```
iMac: ssh gianlucadistasi@192.168.1.2
PM2 start: export $(grep -v '^#' wa-intelligence/.env | xargs) && pm2 start wa-intelligence/wa-daemon.js --name argos-wa-daemon
Dashboard: Python 3.9 (path lungo) -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8080 --app-dir wa-intelligence
QR Auth: http://192.168.1.2:9191/qr (dal daemon, zero processi separati)
OpenRouter: chiave in wa-intelligence/.env — credito ricaricato 2026-03-27
```

## Regole

- L'agente si chiama LUCA FERRETTI, mai "AMBRA"
- Ordine: capire cosa hai → ricercare → poi definire implementazione (B→A→C)
- TUTTO e' possibile, basta cercare bene
- cove_engine_v4.py NON MODIFICARE
