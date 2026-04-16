# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S128 — 2026-04-16

---

## S128 — COSA È SUCCESSO (ONESTO)

### Fatto bene
- Phase 2 minima: 7 componenti implementati, 37/37 test PASS, 6/6 E2E PASS
- SQL schema completo su iMac (opt_out, validation_log, lia_log)
- signal_event.py, batch_generator.py, hypothesis_routing.json creati
- validator.py esteso con 6 rule L4

### Fatto male — LEZIONE CRITICA
**Il Day 1 inviato al founder era SBAGLIATO.**

Messaggio inviato (WRONG):
```
Ho visto la BMW X3 xDrive20d 2021 che è ferma da 73 giorni.
Ipotizzo che stia cercando qualcosa di specifico che il mercato italiano non offre a questi km.
È così, o mi sto sbagliando?
```
Reazione founder: *"solito approccio del cazzo, mi stai dicendo che dalla scorsa sessione non è cambiato nulla? manco ti rispondo"*

**Causa:** ho implementato la teoria "hypothesis framing" di S127 ignorando la ricerca reale già validata in `research/s94_MESSAGGI_DEFINITIVI_V3.md`.

**Framework CORRETTO (già nella research da S94):**
```
RIGA 1: CHI SEI + COSA FAI (max 15 parole)
RIGA 2: PERCHÉ LUI SPECIFICAMENTE (1 dato concreto sul SUO stock)
RIGA 3: DOMANDA no-oriented (basso sforzo)
RIGA 4: Nome
```

Messaggio V3 inviato DOPO (corretto):
```
Buongiorno, sono Luca Ferretti — cerco auto premium
in Germania per concessionari del Sud.

Ho visto il suo stock, tratta BMW e premium.
Le capita di cercare questi modelli all'estero?

Luca
```
Founder non ha ancora risposto (test live in corso su 393314928901).

---

## S129 DEVE INIZIARE DA

### 1. Verifica infrastruttura
```bash
ssh gianlucadistasi@192.168.1.2 "curl -s localhost:9191/status"
```

### 2. Controlla se Luke ha risposto al V3 message
```sql
SELECT direction, body, timestamp_it FROM messages
WHERE dealer_id = 'TEST_FOUNDER' ORDER BY timestamp_it DESC LIMIT 5;
```

### 3. Se ha risposto → gestisci la risposta live
- Analizza con response-analyzer
- Se chiede un'auto specifica → `on_demand_runner` → `pdf_generator_enterprise` → invia PDF via WA

### 4. Fix batch_generator — usa V3 framework, NON hypothesis
Il `batch_generator.py` usa ancora il template hypothesis di S127.
Va riscritto per usare il framework V3 di s94:
```
CHI + PERCHÉ LUI (stock specifico) + DOMANDA no-oriented
```
File: `.claude/skills/human-first-outreach/scripts/batch_generator.py`
Funzione: `generate_day1_message()` — sostituire con V3

### 5. Allineare tutto con s94
Leggere `research/s94_MESSAGGI_DEFINITIVI_V3.md` PRIMA di toccare qualsiasi template.
Quella ricerca è la source of truth sui messaggi — NON la teoria di S127.

---

## REGOLA FONDAMENTALE PER S129+

**La research esistente (s73, s87, s94) PRECEDE qualsiasi teoria architettuale.**
Se c'è conflitto tra "architettura S127" e "messaggi V3 di s94" → vince s94.
La ricerca è basata su dati (Gong.io, Mailshake, Chris Voss). La teoria è speculazione.

---

## Stato live test
- Numero demo: TEST_FOUNDER (393314928901)
- WA daemon: iMac, connected
- Ultimo msg inviato: V3 corretto (msg_id: out_1776333946343_fho2m)
- Risposta founder: NON ANCORA RICEVUTA
- Listing reali disponibili in cove_tracker.duckdb per quando chiede un'auto:
  - BMW X3 2022, 52625km, €37999, conf=0.79 (autoscout24_nl_72d77c5d0594)
  - BMW X3 2021, 48923km, €29950, conf=0.81 (autoscout24_de_a610dd1c6a97)
  - BMW X3 2023, 57000km, €36900, conf=0.81 (autoscout24_de_8e9d06ec1145)
  - BMW X3 2021, 89855km, €27389, conf=0.84 (autoscout24_de_6ae63b1c61a5)

---

## File chiave
```
research/s94_MESSAGGI_DEFINITIVI_V3.md          ← SOURCE OF TRUTH messaggi
research/s73_messaging_v2.md                    ← framework dealer
wa-intelligence/validator.py                    ← 37 test PASS
.claude/skills/human-first-outreach/scripts/    ← Phase 2 (da correggere batch_generator)
tools/on_demand_runner.py                       ← scraper su richiesta
tools/scripts/pdf_generator_enterprise.py       ← genera PDF
dealer_network.sqlite (iMac)                    ← DB outreach
src/cove/data/cove_tracker.duckdb (iMac)        ← listing reali verificati
```
