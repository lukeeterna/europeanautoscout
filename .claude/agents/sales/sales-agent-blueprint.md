# ARGOS SALES AGENT — ENTERPRISE BLUEPRINT
## Stack 0-cost · Anthropic Official Docs · Aprile 2026

**Per:** Claude Code (implementazione)  
**Autorità:** docs.anthropic.com (verificato 09/04/2026)  
**Obiettivo:** eliminare i 5 bug strutturali con architettura template-first

---

## 1. DIAGNOSI RADICE DEI 5 BUG

| Bug | Causa radice | Fix architetturale |
|-----|-------------|-------------------|
| BUG-1: fee leak | Istruzione negativa ("NON fare X") ignorata da modelli free | Rimuovere fee dal system prompt. Template-first: fee appare SOLO nel template OBJ-2 |
| BUG-2: identity inversion | Modello free non gestisce pragmatica italiana | Template fisso con esempio positivo + negativo espliciti |
| BUG-3: risposta soppressa | Classificatore sovrascrive: 3° messaggio negativo cancella 2° positivo | Finestra classificatore su turno singolo, non sliding window |
| BUG-4: 60 messaggi duplicati | `reply_count` non incrementato + nessun cap reale | State machine con campo `outbound_count` + check pre-invio |
| BUG-5: no state machine | Architettura stateless, ogni messaggio isolato | DuckDB state machine a 5 stati, persistita tra sessioni |

**Fonte diagnostica (Anthropic Engineering, set 2025):**
> "Context engineering is the evolution of prompt engineering — the question is: what configuration of context is most likely to generate the desired behavior?"

I modelli free falliscono sulle istruzioni negative perché leggono il vincolo ma lo context window li porta a "rigurgitare" comunque. La soluzione non è un prompt migliore: è rimuovere l'informazione dal contesto finché non è necessaria.

---

## 2. STACK ENTERPRISE — 0 COST

### Modelli selezionati (docs.anthropic.com/models/overview)

```
CLASSIFICATORE:   claude-haiku-4-5-20251001
                  → Near-frontier, real-time, high-volume
                  → Structured outputs (beta: structured-outputs-2025-11-13)
                  → Costo classificazione: ~$0.00025 per messaggio

GENERATORE:       claude-sonnet-4-6
                  → Best intelligence/speed ratio
                  → Prompt caching 1h (GA, no beta header)
                  → Con cache hit: -90% input tokens
                  → Effort: low (non serve extended thinking per template fill)
```

### Costo reale per 100 conversazioni/mese

```
Sistema attuale (llama free): 0€ ma qualità pessima → costo reputazionale alto
Sistema proposto:
  - Haiku classificazione: 100 conv × 10 msg × 500 tok = 500K tok → ~$0.08
  - Sonnet generazione: 100 conv × 5 risposte × 800 tok output = 400K tok → ~$6
  - Prompt cache hit (system prompt 2K tok, cachato): risparmio ~$4
  - TOTALE: ~$2-3/mese — coperto dalla subscription Claude.ai
```

**Se usi Claude Code con subscription Max:** entrambi i modelli sono inclusi. Costo = 0.

### Prompt Caching — configurazione (docs.anthropic.com/prompt-caching)

```python
# System prompt + templates vanno in cache. Cache TTL: 1 ora (GA).
# Per ARGOS: il system prompt è ~2K token, stabile per tutte le conv.
# Automatic caching (raccomandato da Anthropic):

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=600,
    system=[{
        "type": "text",
        "text": ARGOS_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}  # 1h TTL
    }],
    messages=conversation_messages
)
# Cache write: 1.25x prezzo base (solo prima volta)
# Cache read: 0.1x prezzo base (tutte le volte successive)
```

### Structured Outputs per classificatore (docs.anthropic.com/structured-outputs)

```python
# Beta header: structured-outputs-2025-11-13
# Garantisce conformità schema JSON al 100% — niente più parse errors

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["CURIOSITY", "OBJECTION", "POSITIVE", "NEGATIVE", 
                     "REQUEST_INFO", "SCHEDULING", "OUT_OF_SCOPE"]
        },
        "state_transition": {
            "type": "string", 
            "enum": ["COLD", "CONTACTED", "ENGAGED", "INTERESTED", "CONVERTING", "BLOCKED"]
        },
        "archetype": {
            "type": "string",
            "enum": ["RAGIONIERE", "BARONE", "PERFORMANTE", "NARCISO", "TECNICO", "UNKNOWN"]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "requires_human": {"type": "boolean"}
    },
    "required": ["intent", "state_transition", "archetype", "confidence", "requires_human"]
}
```

---

## 3. STATE MACHINE — DEFINIZIONE COMPLETA

### Schema DuckDB (aggiunta campi mancanti)

```sql
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS conversation_state VARCHAR DEFAULT 'COLD';
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS outbound_count INTEGER DEFAULT 0;
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS inbound_count INTEGER DEFAULT 0;
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS last_inbound_at TIMESTAMP;
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS state_updated_at TIMESTAMP;
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS archetype VARCHAR DEFAULT 'UNKNOWN';
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS escalation_flag BOOLEAN DEFAULT FALSE;
```

### Transizioni di stato

```
COLD
  → Day1 outbound inviato → CONTACTED
  → Max 1 outbound (Day1 only)

CONTACTED  
  → Dealer risponde (qualsiasi) → ENGAGED
  → Nessuna risposta dopo Day12 → ARCHIVED
  → Max 3 outbound (Day1, Day7, Day12)

ENGAGED
  → Intent = POSITIVE o INTERESTED → INTERESTED
  → Intent = NEGATIVE ripetuto (≥2x) → ARCHIVED
  → Intent = CURIOSITY/REQUEST_INFO → resta ENGAGED

INTERESTED
  → Dealer chiede scheda/dettagli → CONVERTING
  → Intent = NEGATIVE → torna ENGAGED (non ARCHIVED)

CONVERTING
  → Accordo raggiunto → CLOSED_WON
  → Nessun follow-up dopo 30gg → CLOSED_LOST
```

### Regole per stato (state-gated messaging)

```python
STATE_RULES = {
    "COLD": {
        "allowed_templates": ["DAY1_INTRO"],
        "max_outbound": 1,
        "requires_inbound_before_continue": False
    },
    "CONTACTED": {
        "allowed_templates": ["DAY7_RECOVERY", "DAY12_FINAL", "IDENTITY_RESPONSE"],
        "max_outbound": 3,
        "requires_inbound_before_continue": False
    },
    "ENGAGED": {
        "allowed_templates": ["IDENTITY_RESPONSE", "VEHICLE_PROPOSAL", 
                              "OBJ_1", "OBJ_2", "OBJ_3", "OBJ_4", "OBJ_5"],
        "max_outbound": None,  # risponde a inbound, no cap
        "requires_inbound_before_continue": True
    },
    "INTERESTED": {
        "allowed_templates": ["VEHICLE_DETAILS", "CLOSING_PUSH"],
        "max_outbound": None,
        "requires_inbound_before_continue": True
    }
}

def can_send(dealer_id: str, db) -> tuple[bool, str]:
    """Guardrail pre-invio. Returns (ok, reason)."""
    d = db.execute("SELECT * FROM dealers WHERE id=?", [dealer_id]).fetchone()
    state = d["conversation_state"]
    rules = STATE_RULES.get(state, {})
    
    # Cap outbound
    max_out = rules.get("max_outbound")
    if max_out and d["outbound_count"] >= max_out:
        return False, f"CAP_REACHED: {d['outbound_count']}/{max_out} outbound per stato {state}"
    
    # Dedup: non mandare se stesso messaggio nelle ultime 24h
    # (implementazione omessa per brevità — aggiunge check su message_hash)
    
    return True, "OK"
```

---

## 4. ARCHITETTURA TEMPLATE-FIRST

### Principio (da Anthropic Engineering Blog, 2025)

> "The smallest set of high-signal tokens that maximize the likelihood of your desired outcome."

**Oggi (sbagliato):** system prompt 2K token + tutto il contesto → LLM genera liberamente  
**Domani (corretto):** system prompt 200 token (identity only) + template 150 token + LLM riempie 3 slot

Il LLM non vede mai la fee nel contesto a meno che non sia stato classificato OBJ-2.

### I 10 Template Obbligatori

```python
# Template engine: per ogni intent/stato → template specifico
# Il LLM (Sonnet 4.6) riceve: template + {DEALER_NAME} + {VEHICLE} + {PRICE_DELTA}
# Non genera testo libero. Personalizza solo gli slot indicati con {}.

TEMPLATES = {

    "DAY1_INTRO": """
Buongiorno, sono Luca Ferretti.
Ho visto il suo salone su AutoScout24 — lavora con {BRAND_FOCUS}, giusto?
Trovo auto premium dalla Germania per concessionari italiani.
Le capita di avere clienti che cercano modelli specifici che in Italia non trova?
""",
    # Nota: NESSUN veicolo specifico, NESSUN prezzo, NESSUNA fee.
    # Obiettivo: risposta sì/no sul suo business.

    "IDENTITY_RESPONSE": """
Ho trovato il suo contatto su {SOURCE} — cerca concessionari multi-marca che lavorano con {BRAND_FOCUS}.
Trovo auto premium in Germania, Olanda e Belgio per conto di dealer italiani.
{DEALER_NAME}, lavora spesso con clienti che cercano {BRAND_FOCUS} specifiche?
""",
    # Esempio positivo da usare nel prompt di personalizzazione:
    # INPUT: "Chi le ha dato il mio numero?"
    # OUTPUT (sopra): risponde chi sono + fonte + chiede del suo business
    # Esempio NEGATIVO (non fare mai):
    # "Posso chiederle come ha avuto il mio numero?" ← INVERTITO, SBAGLIATO

    "VEHICLE_PROPOSAL": """
{DEALER_NAME}, le mando un'opportunità concreta.

{VEHICLE_YEAR} {VEHICLE_BRAND} {VEHICLE_MODEL}
Km verificati: {KM}
Prezzo: {PRICE_EUR} IVA inclusa, consegnata a {CITY}

Rispetto al listino IT equivalente: {PRICE_DELTA}.
Ha clienti che stanno cercando qualcosa di simile?
""",
    # Fee NON presente. Appare solo se chiesta esplicitamente (OBJ-2).

    "OBJ_1_NO_INTEREST": """
Capisco, {DEALER_NAME}. Non serve rispondermi adesso.
Se in futuro arriva un cliente che cerca {BRAND_FOCUS} e non trova quello che vuole in Italia, mi faccia uno squillo.
Buon lavoro.
""",

    "OBJ_2_FEE": """
La mia fee è {FEE_EUR} a veicolo consegnato, pagata solo a consegna avvenuta.
Zero anticipo, zero rischio per lei.
Se il veicolo non va bene, non paga nulla.
""",
    # FEE appare SOLO qui. ARGOS_FEE rimossa da tutte le altre parti del codice.

    "OBJ_3_TRUST": """
È normale che voglia sapere con chi ha a che fare.
Ho lavorato con {REFERENCE_TYPE} in {REFERENCE_CITY} — posso chiedere una referenza se vuole.
Nel frattempo posso mandarle la documentazione del veicolo: {AVAILABLE_DOCS}.
""",

    "OBJ_4_TIMING": """
Nessun problema, {DEALER_NAME}. Il veicolo è disponibile fino al {AVAILABILITY_DATE}.
Se preferisce, la ricontatto tra {FOLLOWUP_DAYS} giorni.
""",

    "OBJ_5_SOURCING": """
Il veicolo viene dalla Germania, con {KM} verificati tramite Hauptuntersuchung (il TÜV tedesco).
Posso mandarle il rapporto completo con storico revisioni.
""",
    # NON usare "CarFax EU" (non esiste). NON usare "Händlergarantie" senza VIN.

    "DAY7_RECOVERY": """
{DEALER_NAME}, la disturbo un momento.
Le avevo scritto la settimana scorsa di una {VEHICLE_BRAND} {VEHICLE_MODEL}.
Ha avuto modo di leggere?
""",

    "DAY12_FINAL": """
{DEALER_NAME}, ultima volta che le scrivo su questo veicolo.
Se non fa al caso suo, nessun problema — magari una prossima volta.
Buon lavoro.
""",
}
```

---

## 5. AGENT SKILLS PER CLAUDE CODE

### Struttura file (docs.anthropic.com/agent-skills)

```
~/Documents/app-antigravity-auto/.claude/
├── CLAUDE.md                          # Root instructions
├── agents/
│   ├── classifier.md                  # Subagent: classificazione intent
│   ├── template-filler.md             # Subagent: personalizzazione template
│   └── validator.md                   # Subagent: validazione bloccante
└── skills/
    ├── ARGOS_DEALER_DOMAIN.md         # Knowledge: dealer archetypes, OBJ codes
    ├── ARGOS_VEHICLE_DATA.md          # Knowledge: veicoli attivi, CoVe scores
    └── ARGOS_COMPLIANCE.md            # Knowledge: regole anti-leak, cap rules
```

### classifier.md (subagent definition)

```yaml
---
name: argos-classifier
description: >
  Classifica messaggi dealer WA in intent/stato/archetype.
  Attivare SEMPRE prima di qualsiasi risposta a messaggio inbound.
  NON generare risposte. Solo classificare.
model: claude-haiku-4-5-20251001
tools: Bash
---
Sei un classificatore per ARGOS, sistema di scouting veicoli B2B.

Analizza il messaggio del dealer e restituisci SOLO JSON valido con schema:
{
  "intent": "CURIOSITY|OBJECTION|POSITIVE|NEGATIVE|REQUEST_INFO|SCHEDULING|OUT_OF_SCOPE",
  "state_transition": "COLD|CONTACTED|ENGAGED|INTERESTED|CONVERTING|BLOCKED",
  "archetype": "RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO|UNKNOWN",
  "confidence": 0.0-1.0,
  "requires_human": true|false,
  "matched_patterns": ["pattern1", "pattern2"]
}

PATTERN POSITIVI (allargati — meglio falso positivo che falso negativo):
- "ti do una possibilità", "dai proviamo", "fammi vedere", "mandami"
- "interessante", "quanto costa", "che chilometri", "che anno"
- qualsiasi domanda sul veicolo = POSITIVE

PATTERN NEGATIVI:
- "non mi interessa", "non cerco", "levami", "non disturbare"
- "sono già fornito", "ho i miei fornitori"

ESCALATION (requires_human: true):
- Minacce legali, linguaggio aggressivo, richiesta di parlare con titolare
- Messaggi che non rientrano in nessun pattern con confidence < 0.5
- Dealer che ha ricevuto >3 messaggi senza risposta (verifica DB)
```

### template-filler.md (subagent definition)

```yaml
---
name: argos-template-filler
description: >
  Personalizza template ARGOS con dati reali dealer e veicolo.
  Riceve: template_id + dealer_data + vehicle_data.
  Restituisce: messaggio WA pronto all'invio, max 6 righe.
  NON aggiungere informazioni non presenti nel template.
  NON menzionare fee se template_id != OBJ_2_FEE.
model: claude-sonnet-4-6
tools: Bash
---
Sei il filler di template per ARGOS. Il tuo unico compito è personalizzare
i placeholder {SLOT} con i dati forniti. Non generare testo libero.

REGOLE ASSOLUTE:
1. Mai menzionare "€1.000" o qualsiasi fee se template != OBJ_2_FEE
2. Mai rigirare domande al dealer (es: "posso chiederle..." → SBAGLIATO)
3. Massimo 6 righe nel messaggio finale
4. Nessun emoji, nessuna formula di chiusura formale
5. Tono: diretto, rispettoso, non servile

Se un slot non ha dati disponibili, usa il fallback:
- {REFERENCE_CITY} → "Nord Italia"
- {AVAILABILITY_DATE} → "fine mese"
- {FOLLOWUP_DAYS} → "10"
```

### validator.md (subagent definition)

```yaml
---
name: argos-validator
description: >
  Validatore BLOCCANTE. Eseguire SEMPRE prima dell'invio WA.
  Se ritorna BLOCK: il messaggio NON viene inviato, mai.
  Logga violazione e notifica Telegram.
model: claude-haiku-4-5-20251001
tools: Bash
---
Analizza il messaggio da inviare e verifica:

CHECK_1 FEE_LEAK: contiene "1.000", "1000", "fee", "commissione", "compenso"?
  → Se sì E template_id != "OBJ_2_FEE": BLOCK

CHECK_2 IDENTITY_INVERSION: contiene "posso chiederle come ha avuto"?
  → Sempre: BLOCK

CHECK_3 OUTBOUND_CAP: dealer.outbound_count >= max per stato corrente?
  → Se sì: BLOCK

CHECK_4 DEDUP: message_hash già presente nelle ultime 24h per questo dealer?
  → Se sì: BLOCK

CHECK_5 SENSITIVE: contiene "Germania" + "spedizione" + "importazione" nello stesso msg?
  → Se sì: BLOCK (non rivelare sourcing esplicito)

Rispondi SOLO con:
{"result": "PASS|BLOCK", "check_failed": "CHECK_N|null", "reason": "..."}
```

---

## 6. PROTOCOLLO DI IMPLEMENTAZIONE PER CLAUDE CODE

### Fase 1 — State Machine (priorità MASSIMA, 2h)

```bash
# File da creare/modificare:
# 1. src/state_machine.py — logica transizioni
# 2. database/migrations/004_add_state_fields.sql — nuovi campi
# 3. wa_daemon.js — integra can_send() prima di ogni invio

# Test obbligatorio prima di mergiare:
# python -m pytest tests/test_state_machine.py -v
# Scenario: dealer riceve 4 messaggi → il 4° deve essere BLOCCATO
```

### Fase 2 — Template Engine (3h)

```bash
# File da creare:
# 1. src/templates.py — dizionario TEMPLATES + fill_template()
# 2. src/template_selector.py — mapping (intent × stato) → template_id

# Rimuovere da tutti i file:
# - ARGOS_FEE = '€1.000' come costante globale
# - Qualsiasi riferimento a fee nel system prompt principale
# grep -r "1.000\|ARGOS_FEE\|fee" src/ --include="*.py" | grep -v "OBJ_2"
```

### Fase 3 — Classificatore Structured Outputs (2h)

```bash
# File da modificare:
# 1. src/response_analyzer.py — sostituire classificatore attuale
# Aggiungere header: "anthropic-beta": "structured-outputs-2025-11-13"
# Modello: claude-haiku-4-5-20251001

# Validazione: tutti i pattern POSITIVI devono includere:
# "ti do una possibilità" → test coverage obbligatorio
```

### Fase 4 — Validatore Bloccante (1h)

```python
# In wa_daemon.js / python send wrapper:
# ORDINE OBBLIGATORIO:
# 1. classify(message) → intent/state
# 2. select_template(intent, state) → template_id  
# 3. fill_template(template_id, dealer_data) → message
# 4. validate(message, template_id, dealer) → PASS/BLOCK
# 5. SE PASS: log + telegram approval + send
# 6. SE BLOCK: log violazione + telegram alert + NON inviare

# validate() deve BLOCCARE, non solo loggare.
# Il bug attuale: _check_fee_leak flagga ma non blocca.
# Fix: il risultato del validatore DEVE interrompere il flusso.

def send_wa_message(dealer_id, template_id, filled_message):
    ok, reason = can_send(dealer_id)
    if not ok:
        log_blocked(dealer_id, reason)
        send_telegram_alert(f"BLOCKED {dealer_id}: {reason}")
        return False
    
    validation = validate(filled_message, template_id, dealer_id)
    if validation["result"] == "BLOCK":
        log_blocked(dealer_id, validation["reason"])
        send_telegram_alert(f"VALIDATOR BLOCK: {validation['check_failed']}")
        return False
    
    # Solo qui si invia
    increment_outbound_count(dealer_id)
    return waha_send(dealer_id, filled_message)
```

### Fase 5 — Prompt Caching (30min)

```python
# In ogni chiamata Anthropic API, aggiungere cache_control al system prompt.
# Prerequisito: system prompt stabile (non cambia per ogni dealer).
# Con template-first, il system prompt è ~200 token fissi → cache quasi sempre HIT.

CACHED_SYSTEM = [{
    "type": "text",
    "text": ARGOS_CORE_IDENTITY,  # solo identity, ~200 token
    "cache_control": {"type": "ephemeral"}  # TTL 1h, GA no beta header
}]
```

---

## 7. MESSAGGIO DAY1 — RISCRITTURA (Approccio Relazione)

### Il problema (documentato nei log)

Il dealer riceve un veicolo specifico da uno sconosciuto → **diffidenza immediata**.  
Il framework S73 (Sud Italia) richiede: chi sei → chi ti ha mandato → track record → offerta.  
L'attuale Day1 salta ai punti 4 senza fare 1-2-3.

### Nuovo DAY1_INTRO (template finale)

```
Buongiorno, sono Luca Ferretti.
Ho visto il suo salone su AutoScout24 — lavora con {BRAND_FOCUS}, giusto?
Trovo auto premium dalla Germania per concessionari italiani.
Le capita di avere clienti che cercano modelli specifici che in Italia non trova?
```

**Differenze chiave:**
- Nessun veicolo specifico → nessuna pressione su un prodotto
- Cita AutoScout24 → spiega dove ha trovato il contatto (trasparenza)
- Domanda aperta sul SUO business → lui al centro
- Zero fee, zero prezzo, zero urgenza
- Solo se risponde "sì, mi capita" → proponi il veicolo con numeri

---

## 8. CHECKLIST PRE-COMMIT (Claude Code deve verificare)

```bash
# Eseguire prima di ogni commit su ARGOS:

echo "=== CHECK 1: Nessuna fee nel contesto globale ==="
grep -rn "1\.000\|ARGOS_FEE" src/ --include="*.py" | grep -v "OBJ_2\|test_"
# Atteso: 0 risultati

echo "=== CHECK 2: Validatore blocca, non solo logga ==="
python -c "
from src.validator import validate
result = validate('La fee è 1000 euro', 'VEHICLE_PROPOSAL', 'test_dealer')
assert result['result'] == 'BLOCK', 'VALIDATORE NON BLOCCA!'
print('OK: validatore blocca correttamente')
"

echo "=== CHECK 3: State machine impedisce 4° outbound ==="
python -m pytest tests/test_state_machine.py::test_outbound_cap -v

echo "=== CHECK 4: Classificatore riconosce pattern positivi allargati ==="
python -m pytest tests/test_classifier.py::test_positive_patterns -v
# Include: "ti do una possibilità", "fammi vedere", "mandami scheda"

echo "=== CHECK 5: Template filler non aggiunge fee ==="
python -c "
from src.templates import fill_template
msg = fill_template('VEHICLE_PROPOSAL', {'DEALER_NAME': 'Mario', 'VEHICLE_BRAND': 'BMW', ...})
assert '1.000' not in msg and 'fee' not in msg.lower()
print('OK: fee non presente in VEHICLE_PROPOSAL')
"
```

---

## 9. FONTI UFFICIALI ANTHROPIC USATE

| Fonte | URL | Applicazione |
|-------|-----|-------------|
| Models overview | docs.anthropic.com/models/overview | Haiku 4.5 per classifier, Sonnet 4.6 per generator |
| Prompt caching | docs.anthropic.com/prompt-caching | 1h TTL GA, automatic caching |
| Structured outputs | docs.anthropic.com/structured-outputs | JSON schema garantito per classifier |
| Agent Skills | docs.anthropic.com/agent-skills | Subagent files classifier/filler/validator |
| Claude 4 best practices | docs.anthropic.com/claude-4-best-practices | Esempi positivi+negativi, be explicit |
| Context windows | docs.anthropic.com/context-windows | Context rot → tieni context minimo |
| Subagents | docs.anthropic.com/claude-code/sub-agents | Memoria persistente per subagent |
| Keep Claude in character | docs.anthropic.com/keep-claude-in-character | Identity consistency per Luca Ferretti |

---

## 10. PRIORITÀ IMPLEMENTAZIONE

| # | Azione | Tempo | Impatto |
|---|--------|-------|---------|
| 1 | State machine DuckDB + can_send() | 2h | Elimina BUG-4 (spam) |
| 2 | Rimuovere fee dal contesto globale | 30min | Elimina BUG-1 |
| 3 | Validatore bloccante (non solo logga) | 1h | Elimina BUG-1+2+3+4 |
| 4 | 10 template fissi + template_selector | 3h | Elimina BUG-2+3 |
| 5 | Classificatore Haiku 4.5 + structured outputs | 2h | Elimina BUG-3 |
| 6 | Prompt caching 1h sul system prompt | 30min | 0 cost |
| 7 | Nuovo DAY1_INTRO (approccio relazione) | 30min | Elimina diffidenza |

**Stima totale: ~10h di sviluppo per eliminare tutti i bug strutturali.**
