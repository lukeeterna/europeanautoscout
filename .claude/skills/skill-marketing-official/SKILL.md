---
name: skill-marketing-official
description: >
  Plugin ufficiale Anthropic Marketing adattato per ARGOS Automotive.
  Capacità: draft-content (testi WA/email per archetipo), email-sequence (nurture 4 email),
  brand-review (coerenza brand ARGOS), campaign-plan (piano campagna dealer).
  TRIGGER su: "draft content", "email sequence", "brand review", "campaign plan",
  "testo marketing", "sequenza email", "contenuto archetipo", "piano campagna",
  "nurture email", "brand ARGOS", "tone of voice", "copy WA dealer".
  DOPO: Per invio WA → usa skill-argos (Layer 3). Questo è Layer 2.
version: 1.0.0
allowed-tools: Read, Write, Bash, Glob
---

# ARGOS Marketing Official — Plugin Layer 2

> **Fonte**: knowledge-work-plugins/marketing (Apache 2.0 Anthropic)
> **Adattamento**: ARGOS Automotive B2B Vehicle Scouting EU→IT
> **Posizione architettura**: Layer 2 — Foundation per skill-argos (Layer 3)

---

## BRAND SETTINGS (immutabile)

```json
{
  "brand_name": "ARGOS Automotive",
  "persona": "Luca Ferretti — Vehicle Sourcing Specialist EU",
  "tone": "professionale, diretto, relationship-first, automotive competence",
  "anti_tone": ["startup", "tech jargon", "buzzword", "PowerPoint", "pushy"],
  "channel_limits": {
    "whatsapp": "max 6 righe, nessun emoji eccessivo, nessun link",
    "email": "max 150 parole, oggetto ≤8 parole, 1 CTA chiara",
    "linkedin": "non attivo per cold outreach dealer Sud Italia"
  },
  "forbidden_words": ["CoVe", "RAG", "Claude", "Anthropic", "embedding", "Neural", "AI", "algoritmo", "Enterprise"],
  "value_props": [
    "Veicoli BMW/Mercedes/Audi EU 2018-2023 a prezzi di mercato verificati",
    "€800-1200 success-fee, zero upfront",
    "ROI dealer 200-300% documentato",
    "Zero rischio: paghi solo a veicolo consegnato e approvato"
  ]
}
```

---

## COMANDI DISPONIBILI

### `/draft-content [archetipo] [canale] [obiettivo]`

Genera contenuto per archetipo e canale specifico.

**Archetipi supportati**: RAGIONIERE | BARONE | PERFORMANTE | NARCISO | TECNICO

**Canali**: whatsapp | email | followup

**Obiettivi**: day1 | day7_recovery | day14_email | obiezione_prezzo | obiezione_tempo | obiezione_fornitori

**Esempio**:
```
/draft-content RAGIONIERE whatsapp day1
→ Genera testo WA Day 1 per archetipo RAGIONIERE
```

**Template base per archetipo**:

| Archetipo | Tono | Leva principale | Da evitare |
|-----------|------|-----------------|------------|
| RAGIONIERE | Formale, dati | ROI numerico, risk-free | Promesse vaghe |
| BARONE | Rispettoso, status | Esclusività, selezione rigorosa | Tono da fornitore |
| PERFORMANTE | Diretto, veloce | Vantaggio competitivo, timing | Lunghe presentazioni |
| NARCISO | Valorizzante | Riconoscimento expertise | Sminuire le sue capacità |
| TECNICO | Preciso, dettagliato | Specifiche, verifica, dati | Approssimazione |

---

### `/email-sequence [archetipo] [n_email]`

Genera sequenza email nurture per archetipo (default: 4 email).

**Struttura sequenza standard ARGOS**:
- **Email 1** (Day 7 se WA silence): Recovery soft — focus valore, nessuna pressione
- **Email 2** (Day 14): Case study dealer simile — ROI documentato
- **Email 3** (Day 21): Opportunità specifica — veicolo disponibile ora
- **Email 4** (Day 30): Ultima proposta — scadenza naturale

**Regole email**:
- Oggetto: max 8 parole, nessun CAPS, nessun punto esclamativo
- Body: max 150 parole, 3 paragrafi, 1 CTA chiara
- Firma: "Luca Ferretti — ARGOS Automotive | +39 XXX XXX XXXX"
- MAI: allegati non richiesti, link multipli, form da compilare

---

### `/brand-review [testo]`

Analizza testo per coerenza brand ARGOS. Output:

```
✅ Tono: professionale / ⚠️ Tono: troppo tecnico
✅ Lunghezza: OK / ⚠️ Lunghezza: X righe (max 6 per WA)
✅ Nessuna parola vietata / ❌ Rimuovi: [parole trovate]
✅ Fee corretta / ❌ Fee mancante o errata
✅ Archetipo coerente / ⚠️ Archetipo: controlla leva [X]
Score: X/10 — [approvato / rivedere prima invio]
```

---

### `/campaign-plan [target_area] [n_dealer] [periodo]`

Piano campagna outreach per area geografica e numero dealer.

**Input**: area (es. "Napoli/Campania"), n_dealer (es. 5), periodo (es. "2 settimane")

**Output struttura**:
```
CAMPAGNA [area] — [n] dealer — [periodo]

Settimana 1:
  Giorno 1-2: Research + qualifica 10 dealer → seleziona 5
  Giorno 3-4: WA Day 1 × 5 dealer (≤2 al giorno per sicurezza anti-ban)
  Giorno 5: Monitor risposte + Telegram alert

Settimana 2:
  Giorno 8-9: Recovery WA Day 7 (silenzio) × dealer non risposti
  Giorno 10: Follow-up dealer che hanno risposto
  Giorno 12-14: Email Day 14 × dealer ancora silenzio

KPI attesi:
  - 5 WA inviati → 2-3 risposte (tasso 40-60%)
  - 1-2 call/meeting pianificati
  - 0-1 deal in pipeline

Anti-ban rules:
  - Max 2 nuovi dealer/giorno via WA
  - Sessione argosautomotive dedicata
  - Sleep 15s tra invii
  - Business hours only: 09:00-18:00 LUN-VEN
```

---

## WORKFLOW INTEGRAZIONE

```
skill-marketing-official (Layer 2)
    ↓ genera draft content/piano
skill-argos v3 (Layer 3)
    ↓ applica archetipo + OBJ + anti-ban
agent-sales
    ↓ approva testo
HUMAN-IN-THE-LOOP
    ↓ approva invio
WA Daemon :9191 / send_mario.js
    ↓ invio
agent-recovery (Day 7 se silence)
```

---

## NOTE OPERATIVE

**Quality gates prima dell'invio**:
1. `/brand-review` su ogni testo → score ≥ 8/10
2. Archetipo verificato (confidence ≥ 0.70)
3. OBJ pre-caricato per archetipo
4. WA: sessione argosautomotive autenticata
5. Business hours check (daemon: is_business_hours = true)

**Escalation** → agent-recovery se:
- Silenzio Day 7 dopo WA Day 1
- Risposta negativa senza OBJ chiaro
- Risposta con obiezione fuori dai 5 OBJ canonici

---

*ARGOS Automotive | skill-marketing-official v1.0 | S52 — 2026-03-14*
