# S86 — Replicare AMBRA: Agente WA Autonomo per ARGOS

## Contesto critico — LEGGI PRIMA DI FARE QUALSIASI COSA

Il founder ha analizzato AMBRA (Martes AI) — un agente WA che genera €20.000/mese.
Video: https://www.youtube.com/watch?v=EsZi5Chlub4
Trascrizione completa salvata in: `memory/project_s84_ambra_agent_analysis.md`

**REGOLA ZERO**: wa-daemon.js + response-analyzer.py (802 righe) + OpenRouter/Haiku 4.5 ESISTONO GIA'.
Il 70% del sistema e' costruito. NON reinventare. Leggere PRIMA di proporre.

## Trascrizione AMBRA — I dettagli che contano

Rileggere ATTENTAMENTE `memory/project_s84_ambra_agent_analysis.md` PRIMA di scrivere codice.

I 10 comportamenti da replicare:
1. **Multi-messaggio**: 2-3 msg separati con 3-5s delay (MAI 1 blocco)
2. **Imperfezioni volontarie**: "ciao" minuscolo, spazio prima "?", "??" doppio, maiuscole casuali
3. **Intercalari**: "cavolo", "guarda", "senti", "dai", "niente"
4. **Analisi vocali**: Whisper locale per trascrivere audio WA
5. **Buffer multi-input**: aspettare 10-15s dopo ultimo msg del lead prima di rispondere
6. **Obiezioni contestuali**: non risposte generiche, soluzioni al problema specifico
7. **Pipeline autonoma**: l'agente sposta i lead negli stati automaticamente
8. **Takeover umano**: dalla dashboard, l'operatore subentra in qualsiasi momento
9. **Contesto profondo**: storico, preferenze, ultimo contatto, veicolo proposto
10. **90-95% non si accorge che e' AI** — questo e' il benchmark

## File da leggere PRIMA di iniziare

```bash
# OBBLIGATORIO — leggere questi file:
cat wa-intelligence/wa-daemon.js          # Come riceve messaggi, come chiama analyzer
cat wa-intelligence/response-analyzer.py  # 802 righe, Haiku 4.5 via OpenRouter GIA' configurato
cat wa-intelligence/telegram-handler.py   # Alert Telegram
cat wa-intelligence/time-context.js       # Business hours

# Contesto dealer + veicoli:
cat research/s73_messaging_v2.md          # Template per archetipo (NARCISO/RAGIONIERE/TECNICO)
cat tools/backstory_luca_ferretti.md      # Persona Luca Ferretti
```

## Cosa manca (30%) — da costruire

### 1. Multi-messaggio con delay
wa-daemon.js ha `/send` che manda 1 messaggio. Serve:
- Nuovo endpoint `/send-multi` che accetta array di messaggi
- Delay 3-5 secondi tra ogni messaggio (simula digitazione)
- Typing indicator attivo durante il delay (`client.sendPresenceUpdate('composing')`)

### 2. Prompt Haiku con imperfezioni umane
response-analyzer.py ha il prompt per generare risposte. Aggiornare il prompt con:
- Istruzioni ESPLICITE sulle imperfezioni (minuscole, spazi, intercalari)
- Formato output: JSON array di 2-3 messaggi separati
- Contesto veicolo proposto al dealer
- Contesto archetipo (NARCISO = esclusivita, RAGIONIERE = numeri)
- Knowledge base ARGOS (FAQ import, costi, tempi)

### 3. Invio automatico
Oggi response-analyzer genera candidate replies ma NON le invia.
Aggiungere flag `--auto-send` che invia automaticamente SE:
- Il dealer e' in stati avanzati (REPLIED, INTERESTED)
- Il messaggio non contiene richieste di prezzo/fee (queste vanno a human review)
- Business hours attive

### 4. Buffer multi-input
Se il dealer manda 3 messaggi in 30 secondi, NON rispondere a ognuno.
Aspettare 15 secondi dopo l'ultimo messaggio, poi rispondere a TUTTI insieme.
Implementare con debounce nel wa-daemon.js.

### 5. Whisper per vocali
Quando arriva un audio WA:
- Scaricarlo (`msg.downloadMedia()`)
- Trascriverlo con Whisper (locale, zero costi: `pip install openai-whisper`)
- Passare la trascrizione al response-analyzer come msg-body

### 6. Knowledge base ARGOS
Creare `wa-intelligence/argos_knowledge_base.md` con:
- Come funziona il servizio (scouting → verifica → dossier → consegna)
- Costi: success fee €800-1.200, SOLO a consegna (MAI upfront)
- Tempi: 5-7 giorni dal ok alla consegna
- Trasporto: ritiro personale o trasportatore singolo
- Garanzia: costruttore residua, NO garanzia ARGOS
- Documenti: COC, Kaufvertrag, F24, tutto gestito da ARGOS
- Obiezioni comuni: "non mi fido", "quanto costa", "come funziona", "ho gia un fornitore"

### 7. Takeover umano dalla dashboard
In /vehicles aggiungere per ogni conversazione attiva:
- Bottone "Subentra" che stoppa l'agente e apre input manuale
- Bottone "Riattiva agente" per ridare il controllo all'AI

## COMPLIANCE META — NON NEGOZIABILE

Il wa-daemon usa whatsapp-web.js (NON ufficiale). Se Meta blocca, il sistema muore.
Opzioni da ricercare:
1. **WhatsApp Business API ufficiale** (Meta Cloud API) — gratis fino a 1.000 conversazioni/mese. Conforme al 100%.
2. **Se WA non e' possibile** → email + SMS come fallback
3. **Il sistema deve funzionare INDIPENDENTEMENTE dal canale** — WA e' un transport, non il cervello.

Deep research necessarie PRIMA dell'implementazione:
1. **WhatsApp Business Cloud API**: costi reali, limiti, come migrare da whatsapp-web.js
2. **Whisper locale su iMac**: quale modello, quanto RAM, velocita' trascrizione
3. **Rate limiting WA ufficiale**: quanti messaggi/giorno, template messages vs session messages
4. **Typing indicator**: disponibile su Cloud API?

## Target dealer ARGOS (reminder)
Piccolo autosalone 10-30 auto, compra 1 alla volta su commissione del cliente.
NON concessionario strutturato con bisarche e reparto vendite.
Linguaggio: "macchina", "margine", "ci guadagna €X", MAI "ROI", "pipeline", "algoritmo".

## Infra esistente
```
iMac: ssh gianlucadistasi@192.168.1.2
WA daemon: :9191 (whatsapp-web.js + better-sqlite3)
Response analyzer: OpenRouter + Haiku 4.5
Dashboard: :8080 (FastAPI + HTMX + Tabler)
DB: dealer_network.sqlite (CRM) + cove_tracker.duckdb (veicoli)
```
