# S130 — Shadow mode primo dealer reale

## Contesto rapido

S129 ha fixato `batch_generator.py` → ora usa framework V3 (CHI+PERCHÉ+DOMANDA).
Il messaggio V3 inviato al founder (393314928901) è ancora in attesa di risposta.

**Source of truth messaggi:** `research/s94_MESSAGGI_DEFINITIVI_V3.md`
**Non toccare nulla finché non l'hai letto.**

---

## Step 0 — Verifica infrastruttura

```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status | python3 -m json.tool"
```

---

## Step 1 — Controlla risposta founder

```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT direction, body, timestamp_it FROM messages \
   WHERE dealer_id=\"TEST_FOUNDER\" ORDER BY timestamp_it DESC LIMIT 5'"
```

### Se ha risposto → gestisci risposta live

Analizza con response-analyzer e segui la sequenza V3:
- Interesse → Day 3 con foto + veicolo reale
- "No" → uscita dignitosa
- Silenzio ancora → attendere Day 7

Listing già disponibili (CoVe PROCEED, cove_tracker.duckdb iMac):
```
BMW X3 2021, 48923km, €29950, conf=0.81 → autoscout24_de_a610dd1c6a97 ← MIGLIOR VALORE
BMW X3 2021, 89855km, €27389, conf=0.84 → autoscout24_de_6ae63b1c61a5 ← PREZZO MINIMO
BMW X3 2022, 52625km, €37999, conf=0.79 → autoscout24_nl_72d77c5d0594
BMW X3 2023, 57000km, €36900, conf=0.81 → autoscout24_de_8e9d06ec1145
```

Se chiede un'auto specifica:
```bash
# Genera PDF
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing autoscout24_de_a610dd1c6a97 --dealer 'Test Founder' \
  --output ~/Documents/app-antigravity-auto/dossiers/"
```

### Se non ha risposto → aspetta Day 7

Non inviare prima del Day 7. Silenzio ≠ rifiuto (regola SEQ-NOEXIT-BEFORE-DAY21-001).

---

## Step 2 — Primo dealer reale in shadow mode

Recupera dealer in coda su iMac:
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  \"SELECT dealer_id, dealer_name, city, persona_type, score FROM conversations \
    WHERE current_step IN ('PENDING','COLD') AND (opt_out IS NULL OR opt_out=0) \
    AND outbound_count=0 AND dealer_id != 'TEST_FOUNDER' \
    ORDER BY score DESC LIMIT 10\""
```

Valuta GATE-ICP-001 su ognuno:
- premium_concentration = (BMW+MB+Audi) / total_stock
- < 0.20 → skip (non ICP-fit)
- ≥ 0.30 → ICP-CORE, procede

Se c'è almeno 1 dealer ICP-CORE con signal S+ (aged inventory >90gg su AutoScout24.it):
1. Genera messaggio V3 archetipo-specifico (già in batch_generator.py)
2. Valida con validator.py in shadow mode
3. Mostra a Luke (Telegram o in chat) PRIMA di qualsiasi invio
4. **Aspetta approvazione esplicita prima dell'invio**

---

## Step 3 — Verifica skill human-first-outreach

```bash
ls -la .claude/skills/human-first-outreach/
```

La skill ha solo scripts/ e assets/. Mancano SKILL.md e references/.
Se hai tempo nella sessione, aggiungere almeno SKILL.md (vedi template nel handoff originale).

---

## Definition of Done S130

1. Founder risponde (o conferma silenzio → wait Day 7)
2. Se risponde: gestione risposta corretta + se chiede auto → PDF inviato
3. Se non risponde: primo dealer reale identificato + messaggio V3 generato + Luke ha approvato
4. Nessun invio a dealer reale senza approvazione esplicita Luke

---

## NON fare in S130

- Non reinventare il framework messaggi (s94 è la source of truth)
- Non inviare a dealer reali senza approvazione esplicita
- Non aggiungere nuova architettura (prima 30 messaggi shadow reali)
- Non toccare signal_event.py, validator.py (funzionano)
