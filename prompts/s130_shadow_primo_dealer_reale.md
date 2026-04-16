# S130 — Live test E2E completo

## Leggi questo prima di fare qualsiasi cosa

Nelle sessioni precedenti abbiamo mandato 3 messaggi WA a raffica senza warming.
Comportamento da spam. Numero a rischio ban.

**Ordine obbligatorio. Zero deroghe.**

---

## STEP 1 — image_sanitizer funziona?

```bash
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/src/cove/image_sanitizer.py \
  --listing autoscout24_de_a610dd1c6a97 \
  --output /tmp/test_sanitized/ 2>&1"

ssh gianlucadistasi@192.168.1.2 "ls -lh /tmp/test_sanitized/"
```

PASS = file presenti, dimensioni > 0, nessun errore.
FAIL = debugga fino a PASS. Non andare avanti.

---

## STEP 2 — PDF con dati reali funziona?

```bash
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing autoscout24_de_a610dd1c6a97 \
  --dealer 'Test Founder' \
  --output ~/Documents/app-antigravity-auto/dossiers/ 2>&1"
```

Poi aprilo e verifica con i tuoi occhi:
- Dati reali (km, prezzo, confidence) corrispondono al DB
- Immagini sanitizzate visibili
- Zero placeholder

Dati attesi da cove_tracker.duckdb:
```
listing_id: autoscout24_de_a610dd1c6a97
BMW X3 2021 | 48.923 km | €29.950 | confidence 0.81 | PROCEED
```

PASS = PDF aperto, dati corretti, immagini dentro.
FAIL = debugga fino a PASS. Non andare avanti.

---

## STEP 3 — Account warming OK?

```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status | python3 -m json.tool"
```

Verificare che non ci siano warning su quality rating o spam.
Se ci sono → attendere 24h prima di inviare qualsiasi messaggio.

---

## STEP 4 — Invia Day 1 (UNO SOLO)

Solo se STEP 1 + 2 + 3 sono PASS.

```bash
API_KEY=$(ssh gianlucadistasi@192.168.1.2 "grep ARGOS_API_KEY ~/Documents/app-antigravity-auto/.env | cut -d= -f2")

ssh gianlucadistasi@192.168.1.2 "curl -s -X POST http://localhost:9191/send \
  -H 'Content-Type: application/json' \
  -H \"X-API-Key: $API_KEY\" \
  -d '{
    \"phone\": \"393314928901\",
    \"message\": \"Buongiorno, sono Luca Ferretti — cerco auto premium\nin Germania per concessionari del Sud.\n\nHo visto il suo stock, tratta BMW e premium.\nLe capita di cercare questi modelli all estero?\n\nLuca\",
    \"dealer_id\": \"TEST_FOUNDER\"
  }'"
```

Aspetta. Il founder risponde dal telefono con l'auto che vuole.

---

## STEP 5 — Risposta arrivata → gestisci

```bash
# Polling risposta
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT direction, body, timestamp_it FROM messages \
   WHERE dealer_id=\"TEST_FOUNDER\" AND direction=\"INBOUND\" \
   ORDER BY timestamp_it DESC LIMIT 3'"
```

Quando arriva:
```bash
ssh gianlucadistasi@192.168.1.2 "cd ~/Documents/app-antigravity-auto/wa-intelligence && \
  python3 response-analyzer.py --dealer_id TEST_FOUNDER --body '<testo risposta>'"
```

---

## STEP 6 — Genera PDF con l'auto richiesta e invia

Listing disponibili (CoVe PROCEED, pronti):
```
BMW X3 2021 | 48.923 km | €29.950 | conf 0.81 → autoscout24_de_a610dd1c6a97  ← miglior valore
BMW X3 2021 | 89.855 km | €27.389 | conf 0.84 → autoscout24_de_6ae63b1c61a5  ← prezzo minimo
BMW X3 2022 | 52.625 km | €37.999 | conf 0.79 → autoscout24_nl_72d77c5d0594
BMW X3 2023 | 57.000 km | €36.900 | conf 0.81 → autoscout24_de_8e9d06ec1145
```

```bash
ssh gianlucadistasi@192.168.1.2 "python3 ~/Documents/app-antigravity-auto/tools/scripts/pdf_generator_enterprise.py \
  --listing <listing_id_scelto> \
  --dealer 'Test Founder' \
  --output ~/Documents/app-antigravity-auto/dossiers/"

# Poi invia PDF — verifica endpoint /send del daemon (attachment o link)
```

---

## Done quando

- [ ] image_sanitizer → output verificato
- [ ] PDF aperto con dati reali
- [ ] Day 1 inviato (uno)
- [ ] Founder risponde
- [ ] PDF dossier inviato via WA
- [ ] Founder lo riceve e lo apre
