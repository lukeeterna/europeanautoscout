# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S129 — 2026-04-16

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

## S129 — COSA È SUCCESSO

- iMac ONLINE (WA daemon connected, status OK)
- Founder non ha risposto al V3 message inviato ieri (0 INBOUND da TEST_FOUNDER)
- **Fix completato**: `batch_generator.py` ora usa framework V3 (commit ba00842)
  - `generate_day1_message()` → CHI+PERCHÉ+DOMANDA, tutti 8 archetipi, 0 veicolo/prezzo
  - `load_hypothesis()` mantenuto per Day 7+ (Reframe/Rational Drowning)
  - Validato: 8 archetipi × constraints V3 = tutti PASS (≤5 righe, ≤60 parole)
- Context strategy: integrata sessione Claude.ai con deep research 2026 (psicologia, compliance, trust)
  - Key finding: hypothesis framing = fallback per Day 7+, NON per Day 1
  - V3 CHI+PERCHÉ+DOMANDA è validated (Gong.io 2.1x, Mailshake +142%, Voss +22%)
  - Architecture decisions aggiuntive già in MEMORY.md (GATE-ICP, SIGNAL-FRESH, batch, etc.)

---

## S130 DEVE INIZIARE DA

### 1. Verifica che il founder abbia risposto
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  'SELECT direction, body, timestamp_it FROM messages \
   WHERE dealer_id=\"TEST_FOUNDER\" ORDER BY timestamp_it DESC LIMIT 5'"
```

### 2. Se ha risposto → gestisci la risposta live
- Analizza con response-analyzer
- Se chiede un'auto specifica → `on_demand_runner` → `pdf_generator_enterprise` → invia PDF via WA
- Listing disponibili (già verificati CoVe PROCEED):
  - BMW X3 2021, 48923km, €29950 → autoscout24_de_a610dd1c6a97 (MIGLIOR VALORE)
  - BMW X3 2021, 89855km, €27389 → autoscout24_de_6ae63b1c61a5 (PREZZO MINIMO)

### 3. Se non ha risposto → attendere (silenzio ≠ rifiuto fino a Day 7)
NON inviare altro al founder prima di Day 7 (regola SEQ-NOEXIT-BEFORE-DAY21-001).

### 4. Primo dealer reale in shadow mode
Se il founder approva anche informalmente il V3, si può passare al primo dealer reale.
Verificare lista dealer in coda su iMac:
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \
  \"SELECT dealer_id, dealer_name, city, persona_type FROM conversations \
    WHERE current_step IN ('PENDING','COLD') AND (opt_out IS NULL OR opt_out=0) \
    AND outbound_count=0 AND dealer_id != 'TEST_FOUNDER' LIMIT 10\""
```

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
