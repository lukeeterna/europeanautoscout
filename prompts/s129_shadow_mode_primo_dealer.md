# S129 — Live Test + Fix batch_generator V3

## Contesto rapido

S128 ha implementato Phase 2 tecnica (OK) ma ha inviato il messaggio Day 1 SBAGLIATO al founder.
Il messaggio "hypothesis framing" non funziona. Il founder ha detto "solito approccio del cazzo".

È stato inviato il messaggio V3 CORRETTO (s94) — il founder non ha ancora risposto.

**Source of truth messaggi: `research/s94_MESSAGGI_DEFINITIVI_V3.md`**
**Non toccare nulla finché non l'hai letto.**

---

## Step 0 — Verifica infrastruttura

```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"
```

---

## Step 1 — Controlla risposta founder

```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT direction, body, timestamp_it FROM messages \
   WHERE dealer_id=\"TEST_FOUNDER\" ORDER BY timestamp_it DESC LIMIT 10'"
```

### Se ha risposto:
Analizza il testo con response-analyzer:
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto/wa-intelligence && \
  python3 response-analyzer.py --dealer_id TEST_FOUNDER --body '<testo risposta>'"
```

Poi rispondi seguendo la sequenza V3 (Day 3 se mostra interesse, uscita dignitosa se "no").

### Se chiede un'auto specifica:
```bash
# Scraper on-demand
python3 tools/on_demand_runner.py --marca BMW --budget 40000

# Poi genera PDF con listing reale
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing autoscout24_de_a610dd1c6a97 --dealer 'Test Founder' --output ~/Documents/app-antigravity-auto/dossiers/"

# Poi invia PDF via WA (controlla come fa wa-daemon /send con attachment)
```

### Listing già disponibili (CoVe PROCEED):
```
BMW X3 2022, 52625km, €37999, conf=0.79  → autoscout24_nl_72d77c5d0594
BMW X3 2021, 48923km, €29950, conf=0.81  → autoscout24_de_a610dd1c6a97  ← MIGLIOR VALORE
BMW X3 2023, 57000km, €36900, conf=0.81  → autoscout24_de_8e9d06ec1145
BMW X3 2021, 89855km, €27389, conf=0.84  → autoscout24_de_6ae63b1c61a5  ← PREZZO MINIMO
```

---

## Step 2 — Fix batch_generator

`batch_generator.py:generate_day1_message()` usa ancora hypothesis framing → va sostituita con V3.

Template V3 corretto:
```python
def generate_day1_message_v3(dealer: dict, signal: SignalEvent) -> str:
    """
    Framework V3 (s94_MESSAGGI_DEFINITIVI_V3):
    RIGA 1: CHI SEI + COSA FAI
    RIGA 2: PERCHÉ LUI (1 dato specifico sul suo stock)
    RIGA 3: DOMANDA no-oriented
    RIGA 4: Nome
    """
    nome = dealer.get("dealer_name", "")
    persona = dealer.get("persona_type", "NEUTRO")
    city = dealer.get("city", "")

    # RIGA 2: personalizzata per archetipo
    perche_lui = {
        "NARCISO":    f"Ho visto il suo stock, tratta BMW e premium.",
        "BARONE":     f"Ho visto le sue recensioni — i clienti parlano di serietà.",
        "RAGIONIERE": f"Ho notato che tratta BMW e Mercedes — capisce i numeri.",
        "TECNICO":    f"Ho visto il suo stock, tratta marchi tedeschi.",
        "RELAZIONALE":f"Ho visto il suo lavoro nella zona di {city}.",
    }.get(persona, f"Ho visto che tratta BMW e auto premium.")

    return (
        f"Buongiorno, sono Luca Ferretti — cerco auto premium\n"
        f"in Germania per concessionari del Sud.\n\n"
        f"{perche_lui}\n"
        f"Le capita di cercare questi modelli all'estero?\n\n"
        f"Luca"
    )
```

---

## Step 3 — Validator check su template V3

Verifica che il messaggio V3 non venga bloccato da CRED-SEQUENCE o NO-OFFER:
```bash
python3 wa-intelligence/validator.py
# Aggiungere test per template V3 se mancante
```

---

## Definition of Done S129

1. Founder ha risposto al V3 message (o ha chiesto un'auto)
2. Sistema ha risposto correttamente (Day 3 con veicolo reale O uscita dignitosa)
3. Se ha chiesto auto → PDF generato e inviato via WA
4. batch_generator usa V3 (non hypothesis framing)

**La transazione €0 è completata quando:**
- Founder riceve PDF con listing reale
- Founder "approva" il dossier (anche informalmente)
- validation_log ha tutto registrato

---

## NON fare in S129
- Nessuna nuova architettura
- Non toccare signal_event.py, GATE-ICP-001, SIGNAL-FRESH-001 (funzionano)
- Non re-inventare il framework messaggi — s94 è già validato
