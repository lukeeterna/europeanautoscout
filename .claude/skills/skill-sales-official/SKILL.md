---
name: skill-sales-official
description: >
  Plugin ufficiale Anthropic Sales adattato per ARGOS Automotive.
  Capacità: account-research (intel dealer), draft-outreach (base per skill-argos),
  competitive-intelligence (battlecard import EU), pipeline-review (salute pipeline),
  call-prep (prep visita dealer), forecast (proiezioni revenue).
  TRIGGER su: "ricerca intel dealer", "analisi competitor import", "pipeline review",
  "forecast revenue", "prep visita", "battlecard", "account research".
  IMPORTANTE: Per outreach italiano con archetipi → usa skill-argos (Layer 3) DOPO questo.
version: 1.0.0
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
---

# ARGOS Sales Intelligence — Official Plugin Layer

> **Fonte**: github.com/anthropics/knowledge-work-plugins/sales (Apache 2.0)
> **Adattamento**: ARGOS Automotive B2B Vehicle Scouting EU→IT
> **Posizione architettura**: Layer 2 — Foundation per skill-argos (Layer 3)

---

## CONTESTO ARGOS (settings)

```json
{
  "name": "Luca Ferretti",
  "title": "Vehicle Sourcing Specialist EU",
  "company": "ARGOS Automotive",
  "quota": { "monthly_deals": 5, "value_per_deal": 1000 },
  "product": {
    "name": "EU Vehicle Scouting B2B",
    "value_props": [
      "BMW/Mercedes/Audi 2018-2023 EU a prezzi di mercato",
      "€800-1200 success-fee, zero upfront",
      "ROI medio dealer 200-300%",
      "Perizia + documentale incluso tier 2-3"
    ],
    "competitors": [
      "AutoScout24 privati (no garanzie, no supporto)",
      "Import fai-da-te (rischio legale + burocrazia)",
      "Dealer Germania diretti (barriera linguistica + logistica)",
      "Aste EU (no pre-selezione qualità, deposito richiesto)"
    ]
  },
  "target_market": "Concessionari family-business Sud Italia 30-80 auto"
}
```

---

## WORKFLOW DECISIONALE

```
TASK RICEVUTO
     │
     ├─ Intel su dealer target ─────────────→ [A] ACCOUNT-RESEARCH
     ├─ Prima bozza messaggio ──────────────→ [B] DRAFT-OUTREACH → poi skill-argos
     ├─ Analisi competitor ─────────────────→ [C] COMPETITIVE-INTELLIGENCE
     ├─ Salute pipeline ────────────────────→ [D] PIPELINE-REVIEW
     ├─ Prep visita/chiamata ───────────────→ [E] CALL-PREP
     └─ Proiezioni revenue ─────────────────→ [F] FORECAST
```

---

## [A] ACCOUNT-RESEARCH — Intel Dealer Target

**Trigger**: "ricerca intel [nome dealer]", "analisi [concessionaria]", "chi è [dealer]"

**Workflow**:
1. Web search: "[nome dealer] [città] concessionario auto"
2. Cerca: dimensione stock, marchi, anni attività, titolare, social media
3. Cerca segnali: post LinkedIn, annunci assunzione, news, espansioni
4. Stima personalità ARGOS (RAGIONIERE/BARONE/PERFORMANTE/NARCISO/TECNICO) in base a:
   - Stile comunicazione online
   - Dimensione azienda
   - Marchi trattati
   - Area geografica (Nord/Centro/Sud)

**Output strutturato**:
```
SCHEDA DEALER — [Nome] | [Città] | [Data ricerca]
─────────────────────────────────────────────
ANAGRAFICA:
  Ragione sociale: ...
  Titolare: ...
  Stock stimato: ... auto
  Marchi: ...
  Anni attività: ...

CONTATTI TROVATI:
  Tel: ...
  WhatsApp: (verifica)
  Email: ...

SEGNALI RILEVANTI:
  - ...

STIMA PERSONALITÀ ARGOS: [ARCHETIPO]
Motivazione: ...

OBJ PROBABILE: OBJ-[N] — [descrizione]

RACCOMANDAZIONE APPROCCIO:
  Primo contatto: [WA/Email/Tel]
  Template: [nome template skill-argos]
  Timing: [orario/giorno ottimale]
```

---

## [B] DRAFT-OUTREACH — Prima Bozza (Foundation Layer)

**IMPORTANTE**: Questo genera la struttura base. Per versione finale italiana con
archetipi e OBJ handler → passa sempre a **skill-argos [C] SEQUENCE PROTOCOL**.

**Workflow**:
1. Research dealer (vedi [A])
2. Identifica value prop più rilevante per questo dealer
3. Bozza messaggio: opening + value prop + CTA
4. → Passa a skill-argos per personalizzazione archetipo

**Regole ARGOS (immutabili)**:
- MAX 6 righe WhatsApp
- MAI: CoVe, RAG, Claude, Anthropic, Ollama, tech jargon
- MAI: buzzword ("Neural", "Enterprise", "AI-powered")
- Relationship-first, formale, automotive competence focus
- Sempre proposta multipla (Tier 1/2/3)

---

## [C] COMPETITIVE-INTELLIGENCE — Battlecard Import EU

**Trigger**: "analisi competitor", "battlecard", "obiezione [competitor]", "competitor import"

**Competitor principali ARGOS**:

| Competitor | Tipo | Vantaggio vs ARGOS | Contro-argomento |
|-----------|------|-------------------|-----------------|
| AutoScout24 privati | DIY | Nessuna fee | No garanzie, no supporto, rischio fregatura |
| Import fai-da-te | DIY | Controllo totale | Burocrazia DE/IT, rischio legale, tempo |
| Dealer Germania diretti | Professionale | Rapporto diretto | Barriera linguistica, no selezione pre-qualità |
| Aste EU (BCA, ADESA) | Professionale | Prezzi bassi | Deposito richiesto, no pre-ispezione, logistica |
| Altri scout | Concorrenza | Esperienza locale | Nessun sistema CoVe™, no cultural matching |

**Workflow battlecard**:
1. Identifica competitor menzionato dal dealer
2. Recupera differenziatori ARGOS vs quel competitor
3. Genera talk track specifico
4. Integra con OBJ handler skill-argos

---

## [D] PIPELINE-REVIEW — Salute Pipeline Dealer

**Trigger**: "review pipeline", "stato dealer attivi", "analisi pipeline"

**Query DuckDB** (auto-generate con skill-data-official):
```sql
-- Pipeline attiva per archetipo
SELECT
  persona_type,
  COUNT(*) as count,
  AVG(confidence) as avg_confidence,
  STRING_AGG(dealer_name, ', ') as dealers
FROM cove_tracker
WHERE recommendation = 'PROCEED'
  AND analyzed_at > NOW() - INTERVAL '30 days'
GROUP BY persona_type
ORDER BY avg_confidence DESC;
```

**Output**:
- Dealer per archetipo + confidence
- Flag: dealer senza follow-up da >7 giorni
- Opportunità: dealer PROCEED mai contattati
- Action plan settimanale prioritizzato

---

## [E] CALL-PREP — Preparazione Visita/Chiamata Dealer

**Trigger**: "prep visita [dealer]", "prepara chiamata", "meeting [nome]"

**Workflow**:
1. Account research aggiornato (vedi [A])
2. Storico interazioni da DuckDB
3. Personalità + OBJ stimato
4. Agenda suggerita: apertura → valore → obiezioni → CTA
5. Domande discovery specifiche per archetipo

**Discovery questions per archetipo**:
- RAGIONIERE: "Che margini mediamente fa su import diretti oggi?"
- BARONE: "Quanti anni ha questo mercato per lei? Come è cambiato?"
- PERFORMANTE: "Quali sono i modelli che ruotano più velocemente nel suo stock?"
- NARCISO: "Come si posiziona rispetto agli altri concessionari in zona?"
- TECNICO: "Che documentazione richiede tipicamente per un veicolo EU?"

---

## [F] FORECAST — Proiezioni Revenue

**Trigger**: "forecast mese", "proiezione revenue", "pipeline projection"

**Input richiesto**:
- Pipeline DuckDB attiva (PROCEED dealers)
- Tasso conversione storico (target: 30-40%)
- Avg deal value: €1.000 (mix tier 1-2-3)

**Formula**:
```
Revenue stimata = dealer_proceed × conversion_rate × avg_deal_value
Pipeline minima per €3k/mese = 10 dealer PROCEED attivi
```

**Output**:
- Revenue base / ottimistica / pessimistica
- Gap vs quota mensile
- Azioni per chiudere gap

---

## INTEGRAZIONE CON LAYER 3 (skill-argos)

```
Flusso completo dealer →:

1. skill-sales-official [A]  → Account Research (intel)
   ↓
2. skill-sales-official [B]  → Draft Outreach (struttura base)
   ↓
3. skill-argos [E]           → PersonaDetect → OBJ pre-load
   ↓
4. skill-argos [C]           → Template WA/Email × archetipo
   ↓
5. skill-argos [A]           → WA Send via daemon iMac
   ↓
6. skill-sales-official [D]  → Pipeline tracking DuckDB
```

---

## NOTE DI AGGIORNAMENTO

**v1.0.0** (S51 — 2026-03-14):
- Creazione iniziale da knowledge-work-plugins/sales (Apache 2.0)
- Adattamento contesto ARGOS Automotive
- Integrazione workflow con skill-argos Layer 3
- Competitor analysis EU import specifico
- Discovery questions per 5 archetipi italiani
