# S108 — Settimana 0: Esecuzione Piano Validato V2

## Contesto

S107 ha validato il piano operativo con 5 agenti paralleli.
Risultato: piano corretto al 60%, ricalibrato in `prompts/s107_piano_validato_v2.md`.
Solo 4/30 dealer VALIDATI — serve verifica + enrichment prima di qualsiasi outreach.

## Obiettivo S108

ESEGUIRE la Settimana 0 del piano V2. Tutto fattibile senza iMac.
Approccio: Agent-First — ogni task delegato all'agent/skill corretto.

---

## BLOCCO 1 — Verifica AS24 dei 10 dealer DUBBIO (BLOCCANTE)

**Skill:** `/skill-argos-intel-territoriale`
**Agent:** `agent-research` (subagent_type)

Per ognuno dei 10 dealer DUBBIO Sud Italia:
1. Cercare su AutoScout24.it il dealer per nome + citta'
2. Contare annunci attivi (soglia: >= 20 per VALIDATO)
3. Verificare brand in stock (premium vs utilitarie)
4. Google Maps: stelle, n. recensioni, anno apertura

Dealer DUBBIO da verificare:
- Grandinetti Auto (CZ, Soveria Mannelli)
- Davids Auto (ME, San Filippo del Mela)
- 2F MOTORS LAMEZIA (CZ, Lamezia Terme)
- MACCHITELLA SRL (BR, San Vito dei Normanni)
- GP Auto (LE, Gallipoli)
- PUNTO AUTO SRL (IS, Isernia)
- Stefano Auto (FG, Cerignola)
- SAINAUTO (SA, Sala Consilina)
- 3D Automotive (TA, Manduria)
- CUOMO CARS (SA, Sant'Egidio del Monte Albino)

**Output:** Tabella con verdetto VALIDATO/NON TARGET per ognuno. Target: portare totale a 7-8 validati.

**Azione parallela — Recupero dealer S78/S79:**
Leggere `research/s78_*.json` e `research/s79_*.json` per recuperare:
- Stile Car (FG) — gia' con dossier
- Top Cars (CS)
- BD Auto (CE), Delta Automotive (BN), Car Plus (AV), ASM Service (NA)
Cross-reference con `research/s104_dealer_enriched_wa.json` per WA numbers.

---

## BLOCCO 2 — Enrichment manuale top 10 (BLOCCANTE)

**Skill:** `/skill-argos-intel-territoriale`
**Agent:** `agent-research` (subagent_type)

Per i 7-8 dealer VALIDATI (4 confermati + nuovi da BLOCCO 1):
1. Email (da sito web o Google Maps)
2. Website URL
3. Pagina Facebook (link diretto)
4. N. annunci AS24 (gia' fatto in BLOCCO 1)
5. Note specifiche (orari, specializzazione)

**Output:** Aggiornare `research/s108_dealer_enriched_final.json` con tutti i campi.

---

## BLOCCO 3 — Contratto anti-bypass (BLOCCANTE)

**Skill:** `/legal-compliance-checker`

Leggere `tools/materiali/contratto_incarico_scouting.html` e aggiungere:

**Art. 5-bis — Clausola di protezione (anti-bypass)**
- Penale pari al 100% della fee concordata se il Committente acquista il veicolo
  segnalato senza corrispondere il compenso
- Definizione "veicolo segnalato" = qualsiasi veicolo incluso in un dossier inviato
  o comunicato per iscritto (incluso WA) dall'Incaricato al Committente
- La protezione e' valida per 90 giorni dalla data di segnalazione,
  anche dopo la scadenza naturale del contratto
- Art. 1382 c.c. come base giuridica

**Output:** Contratto HTML aggiornato, pronto per generazione PDF.

---

## BLOCCO 4 — Requirements.txt + fix anomalie

**Skill:** `/backend-architect`

### 4.1 Creare requirements.txt
```
# wa-intelligence/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
itsdangerous==2.1.2
```

### 4.2 Fix DAY1_MIXED (6 righe → 5)
Leggere `wa-intelligence/templates.py`, accorciare DAY1_MIXED a max 5 righe
senza perdere contenuto critico.

### 4.3 Valutare scheduler.py DuckDB
`wa-intelligence/scheduler.py` importa duckdb ma tutto S106 usa sqlite3.
Decisione: deprecare o migrare? (solo analisi, non eseguire migrazione)

---

## BLOCCO 5 — Template case study + packaging formazione

**Skill:** `/content-creator` + `/brand-guardian`

### 5.1 Template case study (1 pagina)
Creare `tools/materiali/case_study_template.html` con struttura:
- Header ARGOS (logo + "Case Study #001")
- Veicolo: [marca] [modello] [anno] [km]
- Prezzo EU: €[X] | Prezzo IT: €[Y] | Delta: €[Z]
- Tempo: dalla richiesta alla consegna [N] giorni
- Margine dealer netto: €[M]
- Citazione dealer (opzionale)
- Footer con contatti Luca Ferretti

### 5.2 Package formazione
Verificare che esistano e siano completi:
- `tools/materiali/import_eu_6_step.html`
- `tools/materiali/guida_vendita_premium_import.html`
Se ok, creare `tools/materiali/formazione_dealer_kit.md` con indice dei materiali.

---

## BLOCCO 6 — Prompt S109 (se tutti i blocchi completati)

Se Settimana 0 completata:
- S109 = Settimana 1: Deploy iMac + Test E2E live
- Richiede iMac ONLINE

Se Settimana 0 parziale:
- S109 = completare blocchi mancanti + primi deploy appena iMac online

---

## Ordine di esecuzione consigliato

```
PARALLELO 1 (ricerca):
  - BLOCCO 1: Verifica AS24 dealer DUBBIO
  - BLOCCO 1b: Recupero dealer S78/S79

PARALLELO 2 (dopo BLOCCO 1):
  - BLOCCO 2: Enrichment top 10
  - BLOCCO 3: Contratto anti-bypass
  - BLOCCO 4: Requirements + fix

PARALLELO 3 (indipendente):
  - BLOCCO 5: Case study template + formazione

SEQUENZIALE (fine sessione):
  - BLOCCO 6: Prompt S109
```

## File chiave

```
Piano V2:          prompts/s107_piano_validato_v2.md
Lead 30:           research/s106_dealer_profiled_30.json
Lead enriched:     research/s104_dealer_enriched_wa.json
Lead S78/S79:      research/s78_*.json, research/s79_*.json
Contratto:         tools/materiali/contratto_incarico_scouting.html
Templates:         wa-intelligence/templates.py
Validator:         wa-intelligence/validator.py
Materiali:         tools/materiali/
Memory:            ~/.claude/projects/.../memory/MEMORY.md
```

## Regole S108

- OGNI blocco deve produrre un output verificabile (file, tabella, diff)
- Se un blocco fallisce, documentare PERCHE' e proporre alternativa
- NON fare outreach — questa e' ancora preparazione
- Commit incrementali per ogni blocco completato
- Aggiornare memory a fine sessione
