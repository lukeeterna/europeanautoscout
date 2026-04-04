---
name: skill-handover
description: "Genera handover a fine sessione: aggiorna memory, crea prompt S(N+1), documenta stato"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep
---

# Handover Protocol — Fine Sessione ARGOS

Esegui questo protocollo ALLA FINE di ogni sessione significativa.

## Step 1: Determina il numero sessione
Leggi `memory/MEMORY.md` per trovare l'ultimo numero di sessione (S97, S98, etc.).
La prossima sessione e' S(N+1).

## Step 2: Aggiorna Memory
Aggiorna `memory/MEMORY.md`:
- Sezione "STATO CORRENTE" con: cosa funziona, cosa no, decisioni prese
- Se ci sono nuovi feedback permanenti, crea file in `memory/feedback_*.md`
- Se ci sono nuovi fatti progetto, crea/aggiorna `memory/project_s{N}_*.md`

## Step 3: Crea Prompt Prossima Sessione
Crea `prompts/s{N+1}_*.md` con:
- Contesto (cosa e' stato fatto)
- Prerequisiti (cosa leggere prima)
- Tasks ordinati per priorita'
- Verifiche finali
- Decisioni aperte per il founder

## Step 4: Output al Founder
Riassumi in 5-10 righe:
- Cosa e' stato completato
- Cosa resta da fare
- Decisioni che servono dal founder
- Path del prompt prossima sessione
