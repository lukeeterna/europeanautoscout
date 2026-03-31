# S96 — Invio Outreach Live + Profiling TIER2

## Contesto

S95 ha preparato tutto per l'outreach ma è bloccata su 2 fronti:
1. **GBP + Facebook**: Google e Facebook bloccano Playwright → il founder deve crearli manualmente
2. **WA daily limit**: raggiunto il 31/03, reset automatico a mezzanotte

## PRIMA DI TUTTO — Verificare prerequisiti

### Check 1: Google Business Profile
```bash
# Cerca su Google se il profilo esiste
# Se NON esiste → il founder DEVE crearlo PRIMA di qualsiasi invio
# Istruzioni complete in: tools/google_business_checklist.md
```

### Check 2: Facebook Page
```
# Verifica se la pagina esiste su facebook.com
# Se NON esiste → istruzioni in S95 session log
```

### Check 3: WA Daemon
```bash
curl http://192.168.1.2:9191/status
# Verificare: wa_status=connected, daily_remaining > 0
```

## Se prerequisiti OK → ESEGUIRE

### 1. Day 7 ai TIER0 (URGENTE — scade 3 aprile)
```bash
python3 tools/send_day7_tier0.py
# Invia messaggio + PDF dossier BMW X3 a:
# - Stile Car (Domenico) 393334254654
# - Car Plus (Luca) 393289617180
# - Sa.My. Auto (Antonio) 393492587423
```

### 2. Day 1 ai TIER1 (dopo TIER0)
```bash
python3 tools/send_day1_tier1.py
# Invia messaggio V3 CHI-PERCHE'-CHIEDI a:
# - Enzo Car (Enzo Cordisco, NARCISO) 393398835656
# - Dream Car (Michele Cannone, BARONE) 393494530357
# CRM aggiornato automaticamente (CONTACTED + Day 3 schedulato)
```

### 3. Verificare veicoli per Day 3
```
# I Day 3 di Enzo Car e Dream Car citano veicoli specifici:
# - Mercedes GLC 220d 2022, ~44.000 km, Monaco ~€33.800
# - Audi A6 Avant 40 TDI 2022, ~39.000 km, Monaco ~€31.400
# VERIFICARE che esistano su autoscout24.de PRIMA del Day 3
```

### 4. Profilare TIER2 con intel territoriale
```
# 7 dealer nel CRM da profilare:
# Auto Carfora (CE), Crimarcar (CE), 2F Motors (CS), De Cicco (CS)
# Autoline (AV), GP Cars (TA), Sull'Auto (CZ)
# Usare skill: argos-intel-territoriale per raccogliere dati reali
```

### 5. Request parser per flusso on-demand
```
# Il messaggio bridge Day 7 dice: "mi scriva marca e budget"
# Serve un parser che intercetta i messaggi in arrivo e li trasforma
# in richieste di scouting strutturate
# Input: WA message "BMW X3 2022 budget 35k"
# Output: search query per scrapers
```

## CRM attuale (12 dealer)
```
TIER0 (3): Stile Car, Car Plus, Sa.My. Auto — CONTACTED, DAY7_FOLLOWUP
TIER1 (2): Enzo Car, Dream Car — NEW, pronti per Day 1
TIER2 (7): Auto Carfora, Crimarcar, 2F Motors, De Cicco, Autoline, GP Cars, Sull'Auto — NEW
```

## Script pronti
```
tools/send_day7_tier0.py      ← Day 7 + PDF (--dry-run per test)
tools/send_day1_tier1.py      ← Day 1 V3 (--dry-run per test)
tools/outreach_scheduler.py   ← Fixato S95 (rispetta RESPONDED status)
```

## Orari invio ottimali
```
Martedì/Mercoledì 8:30-9:00
Sabato 8:30-10:00
```
