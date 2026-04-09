# S107 — Validazione Agent-First del Piano Operativo ARGOS

## Contesto

S106 ha prodotto:
- BLOCCO 1: Integrazione daemon ←→ moduli Python (36/36 test PASS)
- BLOCCO 2: Profilazione 30 dealer (MA: archetipi assegnati senza intel reale)
- CLAUDE.md aggiornato: 347 righe, 50 skills, sistema due livelli
- AUDIT COMPLETO: 5 agenti paralleli hanno mappato stato di ogni componente
- PIANO 4 BLOCCHI (A/B/C/D) — da validare con skill/agent prima di eseguire

## Obiettivo S107

VALIDARE il piano operativo completo usando le skill/agent corrette.
NON eseguire — PRIMA validare, POI eseguire.

Approccio: **Agent-First** — ogni blocco viene analizzato dall'agent specializzato
che poi dice SE il piano e' corretto, COSA manca, COSA cambiare.

## FASE 1 — Validazione A2: I 30 lead sono il target giusto?

**Agent:** `/deep-researcher` + `/trend-researcher`
**Domanda:** I dealer in research/s106_dealer_profiled_30.json sono salonisti
multimarca (30-80 auto) che ricevono richieste specifiche dai clienti e comprano
su commissione? Oppure sono altro?

**Come validare:**
1. Per i top 5 dealer (fit >= 8.5, Sud): cercare stock reale su Subito.it/AS24
2. Contare quante auto hanno EFFETTIVAMENTE in vetrina
3. Verificare se hanno brand premium E generalisti (= modello misto)
4. Cercare recensioni Google Maps → indizi su "mi hanno trovato l'auto che cercavo"

**Output atteso:** Per ognuno dei 5: VALIDATO / NON TARGET / DUBBIO con evidenza.

## FASE 2 — Validazione Piano Blocco A (pre-lancio)

### A1: Deploy S106 su iMac
**Agent:** `/devops-automator`
**Validare:** sync.sh e' pronto per i file nuovi? outbound_guard.py e post_send_update.py
sono inclusi nel rsync? wa-daemon.js modificato — PM2 restart necessario?
Dipendenze Python nuove? (state_machine, templates, validator gia' deployati in S105)

### A3: Test E2E su iMac
**Agent:** `/api-tester`
**Validare:** test_e2e_full.py copre il flusso S106? (outbound_guard, post_send_update,
template-first nel response-analyzer). Se no, cosa aggiungere?

### A4: requirements.txt
**Agent:** `/backend-architect`
**Validare:** Quali import usa wa-intelligence/*.py che NON sono stdlib?
Generare requirements.txt minimo. Verificare che iMac ha tutto installato.

## FASE 3 — Validazione Piano Blocco B (primo dealer)

### B1: 5 lead validati
**Agent:** `/deep-researcher`
**Validare:** Dopo FASE 1, selezionare i 5 migliori candidati per primo contatto.
Criteri: fit_score >= 7.5 + SUD + stock verificato + brand premium + WA confermato.

### B2: Primo invio DAY1
**Agent:** `/skill-argos` (wa-compliance check)
**Validare:** I template DAY1 in templates.py sono pronti? Il flusso
fill_template → validate → /send funziona E2E? dry_run test su numero demo?

### B3: Pitch deck
**Agent:** `/content-creator` + `/brand-guardian`
**Validare:** Quali materiali esistono gia'? (one-pager, landing, dossier PDF).
Cosa serve DAVVERO per il primo dealer? Pitch deck o basta il dossier?

### B4: Contratto/T&C
**Agent:** `/legal-compliance-checker`
**Validare:** Serve un contratto formale per le prime 1-2 operazioni
(prestazione occasionale) o basta un accordo email? Art. 1382 c.c.
clausola penale — serve redazione legale?

## FASE 4 — Validazione Piano Blocco C (robustezza)

### C1-C5
**Agent:** `/devops-automator` + `/workflow-optimizer` + `/infrastructure-maintainer`
**Validare:** Prioritizzare i 5 item. Quali sono REALMENTE bloccanti per operare
con 5-10 dealer? Quali possono aspettare il mese 2?

## FASE 5 — Validazione Piano Blocco D (scala)

**Agent:** `/project-shipper` + `/growth-hacker`
**Validare:** Timeline realistica per D1-D5. Cosa triggera ogni fase?
(es: D1 si fa DOPO il primo deal chiuso, non prima)

## Regole S107

- OGNI validazione deve produrre: CONFERMATO / DA MODIFICARE / DA ELIMINARE
- Se un blocco e' DA MODIFICARE: l'agent propone la modifica
- Se un blocco e' DA ELIMINARE: l'agent spiega perche'
- Output finale: PIANO OPERATIVO VALIDATO V2 con timeline
- NON eseguire nulla — solo validare e riscrivere il piano

## File chiave

```
Piano corrente:     memory/MEMORY.md (sezione PIANO OPERATIVO POST-AUDIT)
Lead da validare:   research/s106_dealer_profiled_30.json
Dealer enriched:    research/s104_dealer_enriched_wa.json
Discovery pipeline: tools/dealer_discovery/
Template DAY1:      wa-intelligence/templates.py
Daemon:             wa-intelligence/wa-daemon.js
Test E2E:           wa-intelligence/test_pipeline_s106.py
Deploy:             deploy/sync.sh
CLAUDE.md:          CLAUDE.md (347 righe, 50 skills, routing table)
Ricerca S105:       .planning/research/s105_dealer_commissione_italia.md
```

## Stato iMac

Al momento della stesura: WA Daemon UNREACHABLE.
Se iMac e' online in S107: partire da A1 (deploy) + A3 (test E2E live).
Se iMac e' offline: fare FASE 1-5 (validazione pura, zero deploy).
