# Response Agent v2 — Architettura Definitiva

## Problema
Il response-analyzer attuale ha un system prompt monolitico di ~250 righe che:
- Confonde l'LLM mescolando identita', regole, formato, tono
- Non passa veicoli reali dal DB → l'LLM inventa prezzi
- Non gestisce lo storico conversazione → risposte ripetitive
- Valida solo banned words → fee e prezzi inventati passano

## Architettura Target

```
Dealer WA msg
  │
  ▼
[1] CLASSIFIER (keyword, locale, ~0ms)
  │  ─ POSITIVE/NEGATIVE/CURIOSITY/OBJECTION/VEHICLE_REQUEST/UNKNOWN
  │
  ▼
[2] CONTEXT BUILDER (locale, ~50ms)
  │  ─ Carica dealer profile da SQLite
  │  ─ Sliding window 6 messaggi (3 scambi) + summary precedenti
  │  ─ Se VEHICLE_REQUEST → query DuckDB top 3 veicoli PROCEED
  │  ─ Assembla system prompt MODULARE (solo moduli necessari)
  │
  ▼
[3] LLM GENERATE (Groq, ~1-2s)
  │  ─ System prompt: ~800-1000 token (non 2000+)
  │  ─ User prompt: contesto dealer + storico + veicoli reali
  │  ─ Output: JSON {"messages": ["msg1", "msg2"]}
  │
  ▼
[4] VALIDATOR (rule-based, locale, ~0ms)
  │  ─ Formato JSON valido
  │  ─ Fee leak (menzionata senza richiesta)
  │  ─ Prezzi inventati (non nel contesto veicolo)
  │  ─ Ripetizioni (frasi gia' inviate)
  │  ─ Banned words
  │  ─ Se FAIL: 1 retry con prompt ridotto, poi template fallback
  │
  ▼
[5] SEND (daemon WA, ~30-60s delay anti-ban)
```

**Principio: 1 sola chiamata LLM. Tutto il resto e' locale e deterministico.**

---

## Modulo 1: System Prompt Modulare

Spezzare il prompt monolitico in 6 moduli con tag XML (funzionano bene con llama-3.3-70b):

```python
PROMPT_MODULES = {
    'identity': """<IDENTITY>
Sei Luca Ferretti. Trovi auto premium in Europa per concessionari italiani.
SEI TU che hai contattato il dealer PER PRIMO.
Se chiedono "chi sei" → spiega che li hai trovati online e proponi opportunita'.
</IDENTITY>""",

    'hard_rules': """<RULES priority="critical">
1. Fee €1.000 fissa — NON menzionarla finche' il dealer non chiede
2. MAI inventare veicoli/prezzi non presenti nel contesto
3. MAI menzionare: CoVe, Claude, AI, bot, piattaforma, algoritmo
4. Se dice NO → chiudi con eleganza, porta aperta
5. Dossier GRATIS. Fee sblocca la POSIZIONE.
</RULES>""",

    'format': """<OUTPUT_FORMAT>
JSON: {"messages": ["msg1", "msg2"]}
2-3 messaggi. Ogni messaggio max 4-5 righe.
</OUTPUT_FORMAT>""",

    'tone': """<TONE>
WhatsApp umano: "ciao" minuscolo, "guarda/senti/dai" come intercalari.
"macchina" MAI "veicolo". Numeri in EUR netti. Firma: "Luca".
</TONE>""",

    'register': """<REGISTER>
Primo contatto: "lei". Se dealer usa "tu": passa al "tu".
MAI mischiare tu/lei nello stesso messaggio.
</REGISTER>""",

    # Selezionato dinamicamente per archetipo
    'archetype_narciso': '<ARCHETYPE>Esclusivita': "questa me la sono tenuta per lei"</ARCHETYPE>',
    'archetype_ragioniere': '<ARCHETYPE>Numeri precisi: "a conti fatti il margine netto..."</ARCHETYPE>',
    'archetype_tecnico': '<ARCHETYPE>Dettagli: "M Sport, full LED, Vernasca, HUD"</ARCHETYPE>',
    'archetype_relazionale': '<ARCHETYPE>Rapporto: "quando ha un momento, le faccio vedere"</ARCHETYPE>',
    'archetype_default': '<ARCHETYPE>Professionale e diretto.</ARCHETYPE>',
}

def build_system_prompt(archetype: str, cls_type: str) -> str:
    """Assembla solo i moduli necessari. Target: <1000 token."""
    parts = [
        PROMPT_MODULES['identity'],
        PROMPT_MODULES['hard_rules'],
        PROMPT_MODULES['format'],
        PROMPT_MODULES['tone'],
        PROMPT_MODULES['register'],
    ]
    # Archetipo specifico
    arch_key = f'archetype_{archetype.lower()}'
    parts.append(PROMPT_MODULES.get(arch_key, PROMPT_MODULES['archetype_default']))
    return '\n\n'.join(parts)
```

**Perche' tag XML**: llama-3.3-70b li tratta come sezioni strutturate. Hard rules nei primi 500 token = massima aderenza.

---

## Modulo 2: Conversazione Stateful

Sliding window di 6 messaggi + summary rule-based per i precedenti:

```python
MAX_RECENT = 6  # 3 scambi completi

def build_conversation_context(msg_history: list) -> str:
    if not msg_history:
        return ''
    messages = list(reversed(msg_history))  # cronologico
    recent = messages[-MAX_RECENT:]
    older = messages[:-MAX_RECENT]

    parts = []
    if older:
        dealer_count = sum(1 for m in older if m.get('direction') != 'OUTBOUND')
        our_count = len(older) - dealer_count
        topics = _extract_topics(older)  # rule-based keyword extraction
        parts.append(f'[Precedenti: {dealer_count} dealer + {our_count} nostri. Temi: {topics}]')

    for m in recent:
        who = 'LUCA' if m.get('direction') == 'OUTBOUND' else 'DEALER'
        parts.append(f'{who}: {m.get("body", "")[:300]}')

    return '\n'.join(parts)[:1500]
```

**Perche' 6 messaggi**: conversazione WA B2B tipica ha 3-5 scambi. 6 = 3 scambi completi (dealer+risposta). Budget token ottimale per llama-3.3-70b.

**SCOPERTA**: il daemon GIA' salva messaggi OUTBOUND nella tabella messages (via /send e /send-multi).
La query `load_dealer_context()` GIA' carica ultimi 5 messaggi (INBOUND + OUTBOUND mescolati).
Il problema delle ripetizioni NON e' mancanza di contesto — e' il prompt monolitico che confonde l'LLM.
Fix: prompt modulare (modulo 1) + check ripetizioni nel validator (modulo 4) risolvono entrambi.

---

## Modulo 3: Pipeline Dati Reali (CoVe → LLM)

Il campo `_vehicle_context` ESISTE gia' in `build_user_prompt()` ma nessuno lo popola.

```python
def get_relevant_vehicles(marca: str, budget: int = None) -> str:
    """Query DuckDB per top 3 veicoli PROCEED."""
    import duckdb
    con = duckdb.connect('cove_tracker.duckdb', read_only=True)
    query = """
        SELECT make, model, year, km, price, confidence
        FROM cove_results
        WHERE recommendation = 'PROCEED'
          AND fraud_overall = 'CLEAN'
          AND make ILIKE ?
    """
    params = [f'%{marca}%']
    if budget:
        query += " AND price <= ?"
        params.append(budget)
    query += " ORDER BY confidence DESC LIMIT 3"

    rows = con.execute(query, params).fetchall()
    con.close()

    if not rows:
        return ''
    lines = []
    for i, (make, model, year, km, price, conf) in enumerate(rows, 1):
        lines.append(f"{i}. {make} {model} {year} | {km:,} km | EUR {price:,.0f} | Conf: {conf:.0%}")
    return '\n'.join(lines)
```

**Quando popolare**: 
- VEHICLE_REQUEST → estrai marca/budget → query DuckDB → passa a LLM
- Primo contatto (Day 1) → pre-carica 2-3 veicoli basati su brand affinity del dealer
- Conversazione in corso → mantieni ultimi veicoli proposti nel contesto

---

## Modulo 4: Validatore Output Multi-Layer

```python
class ResponseValidator:
    def validate(self, text, cls_type, prev_msgs, vehicle_ctx) -> list[str]:
        violations = []
        violations += self._check_json_format(text)
        violations += self._check_banned_words(text)
        violations += self._check_fee_leak(text, cls_type)
        violations += self._check_invented_prices(text, vehicle_ctx)
        violations += self._check_repetitions(text, prev_msgs)
        return violations

    def _check_invented_prices(self, text, vehicle_ctx):
        """Ogni prezzo EUR nel testo DEVE esistere nel contesto veicolo."""
        import re
        prices_in_text = re.findall(r'EUR?\s*([\d\.]+)', text)
        prices_in_ctx = set(re.findall(r'EUR?\s*([\d\.]+)', vehicle_ctx or ''))
        prices_in_ctx.add('1.000')  # fee sempre lecita
        return [f'prezzo_inventato: EUR {p}' for p in prices_in_text if p not in prices_in_ctx]

    def _check_repetitions(self, text, prev_msgs):
        """Rileva frasi >15 char gia' inviate da Luca."""
        import re
        our_phrases = set()
        for m in (prev_msgs or []):
            if m.get('direction') == 'OUTBOUND':
                for s in re.split(r'[.!?\n]', m.get('body', '')):
                    if len(s.strip()) > 15:
                        our_phrases.add(s.strip().lower())
        return [f'ripetizione: "{p[:50]}"' for p in our_phrases if p in text.lower()]
```

**Strategia fallimento**:
1. `formato` → 1 retry con prompt "Rispondi SOLO JSON"
2. `fee_leak` / `banned` → HOLD, Telegram alert
3. `prezzo_inventato` → BLOCCO, template senza prezzi
4. `ripetizione` → WARNING su Telegram, invio comunque

---

## Ordine Implementazione

| # | Cosa | Impatto | Effort |
|---|------|---------|--------|
| 1 | Prompt modulare (spezzare SYSTEM_PROMPT) | Alto — LLM rispetta meglio le regole | 1h |
| 2 | Validator multi-layer | Alto — blocca fee/prezzi inventati | 1h |
| 3 | Storico conversazione stateful | Alto — elimina ripetizioni | 1-2h |
| 4 | Pipeline veicoli reali CoVe→LLM | Critico — elimina dati inventati | 2-3h |
| 5 | Test E2E conversazione completa | Bloccante — prima del go-live | 1h |

**Tempo totale stimato: 1 sessione di lavoro (6-8h)**

---

## Cosa NON cambiare

- Classifier keyword-based → funziona (10/10 dopo fix S102)
- LLM cascade (OpenRouter→Groq→free→Gemini) → funziona
- WA daemon (wa-daemon.js) → funziona
- Anti-ban delay → funziona
- Telegram notification → funziona
- auto_approve_and_send → funziona (subprocess.Popen)

---

## Correzioni da Validazione (fonti: research/s102_architecture_validation.md)

1. **Prompt caching Groq**: mantenere system prompt stabile tra chiamate — token cached non contano verso TPM (6,000 TPM free tier)
2. **Vincolo TPM**: max 2-3 richieste/minuto con ~2100 tok/req. Se 2+ dealer simultanei → cascade verso free models essenziale
3. **Sliding window parametrica**: k=6 come default, non hardcodato. Tuning dopo primi 20 scambi reali
4. **Tono check LLM**: aggiungere SOLO se emerge problema in produzione. Primi 20 scambi tutti in Telegram per review manuale

## Principi

1. **1 sola chiamata LLM** — classify e validate sono locali (confermato: LangChain, Databricks)
2. **Dati reali o niente** — MAI lasciare l'LLM inventare
3. **Prompt corto** — <1000 token system, regole critiche nei primi 500 (confermato: "Lost in the Middle", Liu et al. 2023)
4. **Stateful** — l'LLM vede gli ultimi 3 scambi + summary
5. **Fail-safe** — se validazione fallisce, template > risposta sbagliata
