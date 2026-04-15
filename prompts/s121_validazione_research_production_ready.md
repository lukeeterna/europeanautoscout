# S121 — Validazione Research + Pianificazione Production-Ready
**Data**: 2026-04-15 (prossima sessione dopo S120)
**Contesto**: CoVe E2E PASS 3/3, DB dealer resettato, research autosalon su commissione completata ma da validare.

---

## Obiettivo sessione

Validare i dati della research su autosalon su commissione, adattare il pitch, pianificare E2E production-ready con gate chiari, e ottenere autorizzazione founder per go-live.

---

## Agenda (ordine obbligatorio per framework)

### 1. Leggi HANDOFF.md e MEMORY.md
```
Read HANDOFF.md → stato S120
Read ~/.claude/projects/.../memory/MEMORY.md → contesto completo
```

### 2. Validazione research autosalon su commissione
La research iCRIBIS/UNRAE è da fonti secondarie. Validare con dati primari:
- Cercare su AutoScout24 i profili dei dealer target (Stile Car, Sa.My., Car Plus, Autoline, GP Cars)
- Verificare se sono autosalon su commissione o dealer classici
- Contare stock effettivo visibile, tipologia veicoli, prezzi
- Aggiornare pitch se necessario

### 3. Adattare template Day 1 per autosalon su commissione
Se validazione conferma segmento, riscrivere template Day 1 con:
- Leva: rotazione <30gg + zero anticipo (non "margine di acquisto")
- Veicolo concreto con prezzo EU + stima commissione dealer
- Domanda chiusa sulla rotazione ("quanto ti mette solitamente un BMW X3 a girare?")

### 4. Pianificazione E2E production-ready
Definire gate di qualità obbligatori:
```
CoVe score ≥ 0.75 (PROCEED)
→ Dossier PDF generato + watermark
→ Pitch validato per archetipo dealer
→ Test Day 1 su TEST_FOUNDER: PASS
→ Founder authorization esplicita
→ Go-live
```

### 5. Test WA su TEST_FOUNDER (OBBLIGATORIO prima di go-live)
```
python3 tools/test_e2e_full.py --fast
```
Verificare: Day 1 → risposta simulata → auto-reply → PASS

### 6. Go-live (solo con tutti i gate verdi + autorizzazione)
- Day 1 a Stile Car, Sa.My. Auto, Car Plus
- Se founder autorizza: Autoline, GP Cars

---

## Stato sistema all'apertura S121
- WA daemon: connected, porta 9191 (iMac app-antigravity-auto)
- CoVe E2E: PASS 3/3
- Dealer pronti: Stile Car (TIER0_FG_001), Sa.My. Auto (TIER0_CS_001), Car Plus (TIER0_AV_001)
- DB corretto: `sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite`

## Path critici
- Daemon: `/Users/gianlucadistasi/Documents/app-antigravity-auto/wa-intelligence/wa-daemon.js`
- DB messages: `app-antigravity-auto/dealer_network.sqlite` (conversations + messages tables)
- CoVe test: `app-antigravity-auto/python/tests/test_e2e_integration_v3.py`
- Response analyzer: `app-antigravity-auto/wa-intelligence/response-analyzer.py` (o path enterprise)
