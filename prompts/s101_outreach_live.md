# S101 — Outreach Live + Prove EU + Follow-up (Agent-First)

## Contesto

S100 ha completato Fase 0 del Piano Operativo:
- Landing deployata su Cloudflare con 15 foto + copy enterprise (argos-automotive.pages.dev)
- 35 dealer scoperti, top 5 in CRM (status NEW), messaggi WA pronti
- 7 materiali formativi/legali pronti (calcolatore, obiezioni, 6 step, glossario, ricevuta, contratto, disclaimer)
- Prove presenza EU preparate (testi LinkedIn/GBP/Europages pronti per copia-incolla)
- Script invio WA: `tools/send_day1_top5_discovery.py`
- Fee = SOLO scouting+verifica (memoria: `feedback_fee_solo_scouting.md`)
- Vertex AI attivo: $299.10 crediti rimanenti
- Test E2E: 10/10 PASS

## Protocollo di avvio
1. SessionStart hook
2. Leggi `memory/MEMORY.md`
3. Verifica WA daemon: `curl -s http://192.168.1.2:9191/status`
4. Verifica landing live: `curl -s -o /dev/null -w "%{http_code}" https://argos-automotive.pages.dev`
5. Procedi con azioni

## PRIORITA' ASSOLUTA — Azioni Lunedi Mattina

### Agente 1 — Invio WA (8:30)
```bash
python3 tools/send_day1_top5_discovery.py
```
- Invia 2 messaggi WA automatici (Az Auto Evolution, WP Cars)
- I 3 dealer con fisso (Autoesse, Expert Auto, Romanazzi) richiedono chiamata manuale
- PRIMA dell'invio: verificare su MobileDE/AutoScout24.de che i veicoli citati ESISTANO
- Se un veicolo non esiste piu': aggiornare il messaggio con uno equivalente reale

### Agente 2 — Pubblicazione Prove EU
Contenuti pronti in `tools/prove_presenza_eu.md` — servono azioni manuali:
1. LinkedIn: aggiornare headline + about + experience (copia-incolla)
2. LinkedIn: pubblicare primo post (BMW X3 DE vs IT)
3. Google Business: aggiornare descrizione + pubblicare primo post
4. Europages: creare profilo (registrazione gratuita)
5. EUROCOC: registrarsi come affiliato (eurococ.eu/affiliate)
6. Firma email: aggiornare in Gmail

### Agente 3 — Monitoraggio Risposte
- Controllare WA per risposte ogni 2-3 ore
- Se risposta ricevuta: analizzare intent (curiosita'/veicolo/obiezione) con response-analyzer
- Preparare risposta calibrata per archetipo
- Se nessuna risposta entro mercoledi: preparare Day 3 (secondo veicolo + foto HD)

### Agente 4 — Espansione Discovery
- Continuare discovery nelle province rimanenti
- Target: Taranto, Lecce, Cosenza, Reggio Calabria
- Obiettivo: altri 20-30 dealer con score 3+
- Cross-reference con AS24 per identificare micro-dealer (pochi annunci)

## KPI Fine S101

| KPI | Target |
|-----|--------|
| Messaggi WA inviati (top 5) | 2 WA + 3 chiamate |
| LinkedIn aggiornato + primo post | SI |
| Google Business aggiornato + primo post | SI |
| Europages profilo creato | SI |
| EUROCOC affiliate registrato | SI |
| Risposte ricevute | monitor (target: 0-1, normale) |
| Discovery espansa | +20 dealer |

## Documenti di riferimento
```
Piano master:       research/s99_PIANO_OPERATIVO_COMPLETO.md
Discovery S100:     research/s100_discovery_dealer_reali.md
Messaggi WA:        tools/messaggi_wa_top5_discovery.md
Script invio:       tools/send_day1_top5_discovery.py
Prove EU:           tools/prove_presenza_eu.md
Materiali:          tools/materiali/ (7 file HTML)
Immagini:           assets/luca_ferretti/ (15 foto)
Fee rule:           memory/feedback_fee_solo_scouting.md
Imagen research:    research/s100_imagen_veo3_best_practices.md
```

## Regole
- OGNI task va delegato a sub-agente specializzato
- MAI outreach senza verificare che il veicolo citato ESISTA
- Fee = solo scouting. MAI dire "mi occupo di tutto"
- Test E2E DEVE rimanere 10/10
- Se dealer risponde: risposta entro 30 minuti in business hours
