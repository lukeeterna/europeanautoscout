# S101 — Stress Test E2E Report
## 2026-04-07

### Test eseguiti: 11 | Bug trovati: 7 | Gap: 3

---

## BUG CRITICI (bloccanti)

### BUG-1: Auth mancante nel response-analyzer — FIXATO
- `/send` e `/send-multi` chiamati senza X-API-Key
- Impatto: TUTTE le risposte auto-generate dal 2 aprile NON sono mai state inviate
- 10 pending_replies con sent=0 (TEST_FOUNDER)
- Fix: aggiunto header X-API-Key

### BUG-2: Flag `sent=1` inaffidabile — FIXATO
- curl senza `--fail` ritorna exit 0 anche con `{"error":"unauthorized"}`
- Il DB segna sent=1 quando il messaggio NON e' stato consegnato
- Fix: riscritto auto_approve_and_send in Python puro (no bash/curl)

### BUG-3: CAR PLUS HA RISPOSTO E NON HA RICEVUTO RISPOSTA
- Car Plus (TIER0_AV_001, Grottaminarda) ha inviato una FOTO alle 08:32 del 7/4
- L'analyzer ha generato risposta, auto-approvato, ma invio fallito (BUG-1 + BUG-2)
- Il dealer e' stato ghostato per 12+ ore
- La risposta generata menzionava la fee al primo contatto (viola regole comunicazione)

### BUG-4: Classificatore tratta immagini come testo — FIXATO
- Car Plus ha mandato una FOTO (JPEG base64)
- Il classifier ha matchato "ok" nel raw base64 -> classificato POSITIVE
- Fix: aggiunta _is_media_message() per rilevare JPEG/PNG/PDF/audio

---

## BUG MEDIO

### BUG-5: Classificatore mixed intent — FIXATO
- "BMW X3 non mi interessa, avete Mercedes GLC?" -> NEGATIVE
- L'intent reale e' VEHICLE_REQUEST
- Fix: se NEGATIVE + VEHICLE_REQUEST + "?" -> VEHICLE_REQUEST vince

### BUG-6: "Chi siete?" bassa confidence — FIXATO
- "Ma chi siete? Non vi conosco" -> CURIOSITY conf=0.6 (question_fallback)
- Fix: "chi siete", "chi e'", "non vi conosco" aggiunti a keywords

### BUG-7: OpenRouter 402 — crediti esauriti
- Il provider primario non funziona
- Groq aggiunto alla cascade ma 403 dall'iMac
- Cascade free models funziona (Qwen) ma fragile (429 intermittenti)

---

## GAP STRUTTURALI

### GAP-1: Due database separati non sincronizzati
- MacBook: dealer_network.sqlite (CRM - 15 dealer, top 5 discovery)
- iMac: dealer_network.sqlite (daemon - conversations, messages, pending_replies)
- I dealer discovery non sono nel daemon

### GAP-2: Risposta LLM include fee al primo contatto — FIXATO
- Il system prompt diceva "Fee fissa 1.000"
- L'LLM la menzionava nella prima risposta
- Fix: "NON menzionare la fee FINCHE' il dealer non chiede"

### GAP-3: Nessun rilevamento immagini/media — FIXATO
- Fix: _is_media_message() + handler MEDIA nel flusso principale

---

## TEST SUPERATI

| Test | Risultato |
|------|-----------|
| Outbound burst dry-run (3 msg) | 3/3 OK |
| Security: no API key | Bloccato |
| Security: payload vuoto | Bloccato |
| Security: API key falsa | Bloccato |
| Gate validazione: listing falso | Bloccato |
| Gate validazione: listing reale | Passato |
| Gate validazione: no listing_id | Passato |
| Data integrity CRM | Zero duplicati |
| Data integrity DuckDB | 3/3 listing validi |
| Classifier: 10/10 scenari | Tutti corretti |
| LLM cascade (Qwen free) | Funzionante |

---

## CODE REVIEW (2 pipeline, 25 finding, 12 fixati)

### Response-analyzer (15 finding)
- CRITICAL #1+#2: Shell injection in auto_approve_and_send -> riscritto in Python puro
- HIGH #4: SQLite no timeout -> aggiunto WAL+timeout
- HIGH #6: LLM prompt injection in extract_vehicle_request -> sanitize
- HIGH #8: Empty API key fallthrough -> check aggiunto
- HIGH #12: LLM guard solo OpenRouter -> ora include Groq+Gemini
- MEDIUM #14: Ternary operator bug Telegram -> fixato
- MEDIUM #7: Marca non sanitizzata nel comando Telegram -> sanitizzata
- LOW #15: .env parser non gestisce quote -> fixato

### Outreach pipeline (10 finding)
- HIGH #2: Gate validazione fails-open su eccezione -> fails-closed
- MEDIUM #5: Anti-ban delay skip tra tel_first -> basato su ultimo invio reale
- MEDIUM #9: SKIP vehicles nel fallback -> smart fallback (CoVe error vs SKIP)

---

## BUG POST-FIX (trovato 8/4)

### Thread daemon muore con il processo
- auto_approve_and_send riscritto con threading.Thread(daemon=True)
- Ma response-analyzer.py esce prima che il thread finisca il sleep
- Il thread muore -> risposta mai inviata
- Fix: sostituito con subprocess.Popen(python3 -c ...)
