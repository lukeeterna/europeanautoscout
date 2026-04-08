# S101 — PIANO AGENT-FIRST: Sistema Autonomo ARGOS
## Da "demo rotta" a pipeline che genera deal da sola

---

## STATO ATTUALE (cosa funziona e cosa no)

### Funziona
- WA daemon: connesso, invia/riceve messaggi
- CoVe Engine: scrapa 28 portali, scora veicoli, genera PDF
- Response-analyzer: classifica intent (10/10), genera risposte LLM (Groq OK)
- Gate validazione: blocca listing falsi/SKIP
- Security: auth API, anti-ban delay, prompt injection defense
- Discovery engine: scraper Subito.it + commission classifier PRONTI ma mai lanciati

### NON funziona
- **LLM cascade fragile**: Groq unico provider attivo, OpenRouter 402, free models intermittenti
- **auto_approve_and_send**: riscritto 3 volte, subprocess appena deployato — non testato E2E
- **Due DB separati**: CRM MacBook vs dammeno iMac, dealer non sincronizzati
- **Messaggi sbagliati**: approccio "ho trovato un X3" per dealer con stock, NON per target su commissione
- **Discovery non lanciata**: commission_classifier mai usato sui dealer reali
- **Archetipi non validati**: assegnati per portfolio, mai confermati
- **Nessun dealer ha risposto** (tranne Car Plus con una foto — ghostato)

---

## PREREQUISITI (Fase 0 — da completare PRIMA di tutto)

### 0.1 LLM Cascade Stabile
- [ ] Fix Groq User-Agent: deployato, da testare E2E con risposta reale
- [ ] Aggiornare FREE_MODELS con modelli attivi (Gemma 4, Nemotron, GPT-OSS): FATTO
- [ ] Test: inviare messaggio test, ricevere risposta, verificare che il sistema risponda AUTONOMAMENTE entro 3 minuti
- [ ] Criterio PASS: messaggio arriva sul telefono test senza intervento umano

### 0.2 DB Unificato
- [ ] Il daemon iMac DEVE leggere gli stessi dealer del CRM MacBook
- [ ] Opzioni: (a) rsync periodico dealer_network.sqlite, (b) daemon legge da CRM remoto, (c) merge una tantum
- [ ] Criterio PASS: dealer inserito nel CRM MacBook appare nelle conversations del daemon

### 0.3 auto_approve_and_send Testato
- [ ] Inviare messaggio test → ricevere risposta → verificare che la reply parta
- [ ] Verificare sent=1 nel DB SOLO se il messaggio e' effettivamente consegnato
- [ ] Criterio PASS: messaggio di risposta arriva sul telefono test

---

## FASE 1 — DISCOVERY DEALER SU COMMISSIONE (2-3 ore)

### 1.1 Lanciare Discovery Engine
```bash
python3 tools/dealer_discovery/discovery_engine.py --all-priority 1 --dry-un
```
- Province priorita' 1: tutta Italia segmentando regione/provincia7città 
- Il commission_classifier scora ogni dealer: pochi annunci + marche diverse + keyword = su commissione
- Output: lista dealer con commission_score >= 5.0

### 1.2 Verificare i 5 Dealer S100
- Passare Az Auto Evolution, Autoesse, WP Cars, Expert Auto, Romanazzi nel commission_classifier
- Per ognuno: scrappare il profilo Subito.it, contare annunci, analizzare marche
- Domanda: "commission_score >= 5?" — se si', restano nel pipeline; se no, declassati

### 1.3 Integrare con Google Reviews + Facebook e altri canali
- Per ogni dealer con score >= 5: cercare Google Reviews (reputazione), Facebook (come comunicano)
- Output: profilo arricchito con segnali comportamentali reali

### Criterio PASS Fase 1
- Almeno 10 dealer con commission_score >= 5.0
- Per ognuno: nome, citta', telefono, commission_score, segnali, brand mix
- Almeno 3 con WA disponibile (per outreach diretto)

---

## FASE 2 — MESSAGGI PAIN-POINT (2 ore)

### 2.1 Riscrivere i Messaggi Day 1
Il messaggio NON propone un veicolo. Parte dal PAIN POINT.

**Template MECCANICO-COMMERCIANTE (35% del target):**
```
Buongiorno [Nome], le scrivo perche' lavoro con salonisti
di tutta Italia che cercano auto dalla Germania per i loro clienti.
Quanto tempo perde su Mobile.de ogni volta? Io faccio
la ricerca su 73 portali in 19 paesi, verifico km e storico,
e le porto solo quelle pulite. Ha un cliente che cerca qualcosa?
Luca Ferretti
```

**Template SALONISTA PURO (25%):**
```
Buongiorno, una domanda diretta: le capita che un cliente
le chieda una BMW o Mercedes specifica e lei debba cercarla?
Io trovo auto premium in Germania con margini di €3-5.000 netti.
Zero anticipi — paga solo se la compra. Le interessa vedere
come funziona su un caso reale?
Luca
```

### 2.2 Adattare per Archetipo
- Ogni archetipo (Meccanico, Salonista, Giovane, Ragioniere, Weekend Warrior) ha il SUO messaggio
- L'archetipo si assegna dal commission_classifier + segnali comportamentali
- Il messaggio si valida DOPO la prima risposta (Day 3-7)

### 2.3 Posizionamento Luxury
- Inserire nel messaggio il concetto: "auto premium = margini alti con meno lavoro"
- NON dire "luxury" — dire "BMW, Mercedes, Porsche dalla Germania"
- Il dealer deve capire: 3 auto premium/mese > 10 auto da €8k

### Criterio PASS Fase 2
- 5 messaggi Day 1 diversi per 5 archetipi
- Ogni messaggio parte dal pain point, NON dal veicolo
- Ogni messaggio verificato contro regole comunicazione (max 5 righe, domanda chiusa, no fee)

---

## FASE 3 — PIPELINE AUTONOMA (3-4 ore)

### 3.1 Flusso Agent-First Completo
```
Discovery Engine (trova dealer su commissione)
  → Commission Classifier (scora)
  → CRM insert (con archetipo + commission_score)
  → Messaggio Day 1 pain-point (personalizzato per archetipo)
  → WA daemon invia
  → Dealer risponde
  → Response-analyzer classifica intent
  → LLM genera risposta (Groq/free models)
  → auto_approve_and_send invia reply
  → Telegram notifica founder
  → Day 3/7 follow-up automatico
```

### 3.2 Cosa Manca nel Flusso
- [ ] **Collegamento CRM → daemon**: i dealer scoperti devono finire nel DB del daemon
- [ ] **Messaggio Day 1 automatico**: oggi e' manuale (script), deve essere schedulato
- [ ] **Follow-up Day 3/7**: non esiste — serve uno scheduler che rilancia
- [ ] **Monitoraggio risposte**: il founder deve vedere su Telegram cosa succede senza aprire il terminale
- [ ] **Escalation**: se il dealer chiede qualcosa che l'LLM non sa gestire → alert Telegram con "AZIONE UMANA RICHIESTA"

### 3.3 Test E2E Completo
1. Inserire dealer test nel CRM
2. Discovery engine lo classifica (commission_score)
3. Messaggio Day 1 parte automaticamente
4. Risposta simulata dal telefono test
5. Sistema risponde autonomamente
6. Verificare: messaggio arrivato, intent corretto, risposta coerente, no fee, tono giusto
7. Day 3: sistema invia follow-up automatico

### Criterio PASS Fase 3
- Il ciclo completo gira SENZA intervento umano
- Il founder vede tutto su Telegram
- La risposta e' personalizzata per archetipo
- Zero parole bannate, zero fee al primo contatto

---

## FASE 4 — GO LIVE (1 ora)

### 4.1 Primo Batch
- 3-5 dealer su commissione verificati
- Messaggi pain-point personalizzati
- Sistema autonomo pronto a rispondere
- Founder monitora su Telegram

### 4.2 Metriche
- Reply rate atteso: 4-5% su WA freddo (1-2 risposte su 30-50 contatti)
- Target primo deal: entro 90 giorni (benchmark SaaS partner programs)
- KPI giornaliero: messaggi inviati, risposte ricevute, intent classificato

### 4.3 Car Plus
- Rispondere SUBITO (ghostato da 24h+)
- Messaggio manuale, pain-point approach
- Se risponde positivamente: primo candidato per operazione guidata

---

## ORDINE DI ESECUZIONE

| Step | Cosa | Blocca | Tempo |
|------|------|--------|-------|
| 0.1 | Test E2E auto-send (Groq) | Tutto | 30 min |
| 0.2 | Sync DB CRM ↔ daemon | Fase 3 | 1 ora |
| 0.3 | Rispondere | Niente (parallelo) | 15 min |
| 1 | Discovery + commission scoring | Fase 2 | 2-3 ore |
| 2 | Riscrivere messaggi Day 1 | Fase 3 | 2 ore |
| 3 | Collegare pipeline E2E | Fase 4 | 3-4 ore |
| 4 | Go live primo batch | — | 1 ora |

**Tempo totale stimato: 2-3 sessioni di lavoro**

---

## PRINCIPI

1. **Agent-first**: il sistema fa, il founder supervisiona su Telegram
2. **Pain-point first**: il messaggio parte dal problema del dealer, non dal veicolo
3. **Commission-first**: il target e' chi cerca auto per i clienti, non chi ha stock
4. **Luxury-first**: auto premium = margini alti con meno operazioni
5. **Zero fake**: ogni dato nei messaggi viene dalla pipeline CoVe, mai scritto a mano
6. **Test before live**: ogni componente testato E2E prima dell'outreach reale
7. **Aiutiamo i dealer con un programma e contenuti a loro riservati che li aiutano vendere auto di segmento alto in sezione dedicata della landing con accesso dedicato
