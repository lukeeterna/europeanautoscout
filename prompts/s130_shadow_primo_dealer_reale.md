# S130 — Pre-condizioni live test + transazione E2E completa

## ERRORE S129 — NON RIPETERE

Inviati messaggi WA multipli (10:00, 10:05, 10:31) senza account warming.
Comportamento da spam. Founder: "socializzare prima, senza evidenza di approccio umano niente invii."

**Regola assoluta:** zero invii WA finché le 4 pre-condizioni sotto non sono verificate con evidenze.

---

## Le 4 pre-condizioni (tutte obbligatorie, in ordine)

### 1. WA account warming — verifica stato

```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status | python3 -m json.tool"
```

Verificare che il numero 3281536308 non sia in quality rating basso.
Se il daemon mostra warning su spam/quality → STOP, non procedere con outreach.

Come socializzare il numero prima di outreach:
- Conversazioni normali in entrata/uscita con contatti noti
- Non usare il numero SOLO per cold outreach
- Attendere almeno 24-48h dopo spam burst prima di riprendere

### 2. Image sanitizer — test con output verificabile

```bash
# Prendi un'immagine reale da un listing CoVe
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/src/cove/image_sanitizer.py \
  --listing autoscout24_de_a610dd1c6a97 \
  --output /tmp/test_sanitized/ 2>&1"

# Verifica output
ssh gianlucadistasi@192.168.1.2 "ls -la /tmp/test_sanitized/ && file /tmp/test_sanitized/*"
```

PASS = immagini presenti, dimensioni ragionevoli, nessun errore.
FAIL = blocco, non procedere al PDF.

### 3. PDF dossier con dati CoVe REALI

```bash
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing autoscout24_de_a610dd1c6a97 \
  --dealer 'Test Founder' \
  --output ~/Documents/app-antigravity-auto/dossiers/ 2>&1"
```

Verificare il PDF generato:
- Apri il PDF e controlla che contenga dati reali (non placeholder)
- Verifica che confidence, km, prezzo corrispondano a cove_tracker.duckdb
- Verifica immagini sanitizzate presenti nel PDF

```bash
# Verifica dati nel DB (source of truth)
ssh gianlucadistasi@192.168.1.2 "python3 -c \"
import duckdb
con = duckdb.connect('/Users/gianlucadistasi/Documents/app-antigravity-auto/src/cove/data/cove_tracker.duckdb', read_only=True)
row = con.execute(\\\"SELECT listing_id, make, model, year, mileage, price_eur, confidence, recommendation FROM cove_results WHERE listing_id='autoscout24_de_a610dd1c6a97'\\\").fetchone()
print(row)
con.close()
\""
```

PASS = PDF aperto, dati corrispondono al DB, immagini visibili.
FAIL = blocco, non procedere al live test.

### 4. Transazione E2E live (solo se 1+2+3 sono PASS)

Solo a questo punto:

```bash
# Invia Day 1 V3 (una sola volta — no duplicati)
ssh gianlucadistasi@192.168.1.2 "curl -s -X POST http://localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <API_KEY_DA_ENV>' \
  -d '{
    \"phone\": \"393314928901\",
    \"message\": \"Buongiorno, sono Luca Ferretti — cerco auto premium\nin Germania per concessionari del Sud.\n\nHo visto il suo stock, tratta BMW e premium.\nLe capita di cercare questi modelli all estero?\n\nLuca\",
    \"dealer_id\": \"TEST_FOUNDER\"
  }'"
```

Poi attendere risposta founder (lui risponde dal telefono con l'auto che vuole).

Quando arriva la risposta:
```bash
# Monitora risposte in entrata
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT direction, body, timestamp_it FROM messages \
   WHERE dealer_id=\"TEST_FOUNDER\" AND direction=\"INBOUND\" ORDER BY timestamp_it DESC LIMIT 3'"
```

Analizza con response-analyzer:
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto/wa-intelligence && \
  python3 response-analyzer.py --dealer_id TEST_FOUNDER --body '<testo risposta>'"
```

Genera e invia PDF con l'auto richiesta:
```bash
# Listing disponibili (CoVe PROCEED):
# BMW X3 2021, 48923km, €29950, conf=0.81 → autoscout24_de_a610dd1c6a97
# BMW X3 2021, 89855km, €27389, conf=0.84 → autoscout24_de_6ae63b1c61a5
# BMW X3 2022, 52625km, €37999, conf=0.79 → autoscout24_nl_72d77c5d0594
# BMW X3 2023, 57000km, €36900, conf=0.81 → autoscout24_de_8e9d06ec1145

ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing <listing_id> --dealer 'Test Founder' \
  --output ~/Documents/app-antigravity-auto/dossiers/"

# Invia PDF via WA (verificare endpoint /send-document o simile su daemon)
```

---

## Definition of Done S130

1. [ ] WA account stato OK (no spam flag)
2. [ ] image_sanitizer.py produce output verificabile
3. [ ] PDF con dati CoVe reali (apribile, dati corretti)
4. [ ] Day 1 inviato UNA SOLA VOLTA
5. [ ] Founder risponde con auto specifica
6. [ ] Response-analyzer processa la risposta
7. [ ] PDF dossier generato con il listing corretto
8. [ ] PDF inviato via WA — founder lo riceve

---

## NON fare in S130

- NON inviare WA prima che le pre-condizioni 1+2+3 siano PASS con evidenze
- NON inviare più di 1 messaggio Day 1 (già ne abbiamo mandati 3 oggi)
- NON usare dati mock nel PDF
- NON dichiarare "fatto" senza aprire il PDF e verificare il contenuto
