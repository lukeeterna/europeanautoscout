---
name: argos-orchestrator
description: >
  Skill di orchestrazione ARGOS: gestisce il flusso completo
  discovery → profiling → messaggio → invio → tracking.
  TRIGGER su: "orchestrator", "flusso completo", "discover dealer",
  "profile dealer", "prepara dossier", "status pipeline", "send day",
  "cerca veicolo", "shortlist", "pipeline status", "next actions".
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Agent
---

# ARGOS™ Orchestrator — Flusso Completo CoVe 2026

## RIFERIMENTI CRITICI

```
MASTER REF:     research/S94_MASTER_REFERENCE.md
MESSAGGI V3:    research/s94_MESSAGGI_DEFINITIVI_V3.md
DISCOVERY:      tools/dealer_discovery/discovery_engine.py
CRM:            tools/dealer_crm.py
OUTREACH:       tools/outreach_scheduler.py
PIPELINE:       src/cove/pipeline_orchestrator.py
PROFILI:        research/s94_top6_dealer_profiles.md
INTEL:          research/s94_intel_reale_enzo_dream.md
BACKSTORY:      tools/backstory_luca_ferretti.md
COPY:           copy/ (bio, descrizioni, template)
ASSETS:         assets/ (foto, loghi, cover)
```

## COMANDI

### `discover <provincia>`
Lancia dealer discovery su Subito.it per la provincia indicata.

```bash
python3 tools/dealer_discovery/discovery_engine.py --province <provincia> --pages 3 --dry-run
```

Output: lista dealer con commission_score e fit_score.
Se --insert-crm: inserisce i dealer fit nel CRM.

### `profile <dealer_name>`
Profila un dealer specifico. Usa gli agenti:
1. `persona-classifier` — archetipo + verifica stock
2. `agent-research` — intel da AutoScout24, Google Maps, Facebook, Instagram, Subito

Output atteso: profilo strutturato con archetipo, stock reale, recensioni reali, tono, segnali import.

### `prepare <dealer_name>`
Prepara tutto per il primo contatto:
1. Leggi il profilo del dealer (da profiling precedente)
2. Cerca un veicolo REALE su AS24.de coerente col suo stock (per Day 3)
3. Genera messaggio Day 1 con framework V3 CHI-PERCHE'-CHIEDI
4. Genera Day 3 e Day 7
5. Presenta tutto al founder per approvazione

**FRAMEWORK V3 — Day 1:**
```
RIGA 1: CHI SEI + COSA FAI (max 15 parole)
RIGA 2: PERCHE' LUI SPECIFICAMENTE (1 dato concreto sul SUO stock/recensioni)
RIGA 3: DOMANDA no-oriented a basso sforzo
RIGA 4: Nome
```

**REGOLE:**
- ZERO veicolo nel Day 1
- ZERO numeri/prezzi nel Day 1
- ZERO fee nel Day 1
- ZERO link/allegati nel Day 1
- Max 4 righe, 40-60 parole
- Il veicolo arriva nel Day 3 (quando il dealer sa chi sei)

### `status`
Mostra stato pipeline completo:

```bash
python3 tools/dealer_crm.py pipeline
python3 tools/dealer_crm.py stats
```

Integra con:
- Dealer discovery recente (quanti trovati, quanti profilati)
- Messaggi inviati e risposte
- Next actions con date

### `send <dealer_name> <day>`
Prepara il messaggio per il day indicato (day1, day3, day7, day10, day14, day21, day30).

**MAI inviare senza approvazione esplicita del founder.**

Steps:
1. Leggi profilo dealer dal CRM
2. Genera messaggio basato su framework V3 + archetipo
3. Se day3+: allega veicolo reale verificato su AS24.de
4. Se day7+: allega PDF dossier
5. Se day10: genera vocale con edge-tts (it-IT-DiegoNeural)
6. Presenta al founder → attendi "OK" → solo allora invoca wa-daemon

### `vehicle <marca> <modello> <anno> <budget>`
Cerca veicolo reale su AS24.de per shortlist on-demand.

```bash
python3 src/cove/scraper_cove_pipeline.py --make <marca> --model <modello> --year <anno> --max-price <budget>
```

Poi CoVe scoring → top 3 → formato shortlist WA.

## BLOCCHI PRE-CONTATTO

Prima di usare `send` su QUALSIASI dealer, verificare:

1. **Google Business Profile** — Luca Ferretti / ARGOS deve essere trovabile su Google
2. **Landing page** — argos-automotive.pages.dev deve essere online e funzionante
3. **WA Business bio** — deve essere impostata su 3281536308
4. **Veicolo Day 3** — deve ESISTERE su AS24.de al prezzo indicato

Se uno di questi blocchi non e' risolto, il messaggio NON va inviato.

## COMPLIANCE

- GDPR B2B: max 5 nuovi dealer/giorno, contatto personalizzato, opt-out immediato
- MAI menzionare: CoVe, Claude, AI, algoritmo, piattaforma, scoring bayesiano
- MAI inviare senza approvazione founder
- MAI inventare dati — se un veicolo non esiste, non proporlo
- Linguaggio: "macchina/auto", "tedesca", "margine", "ci guadagna €X"
