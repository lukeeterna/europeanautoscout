# S110 — Soft Launch Outreach (Agent-First)

## Contesto

S108-S109 ha completato: Settimana 0 (6 blocchi), deploy iMac, 12 security fix,
14 chaos test PASS, 20/20 validator adversarial PASS, repo PRIVATE, GDPR fix.
Sistema SECURE e READY per soft launch.

**Unico test mancante:** invio WA reale via daemon durante business hours.

## Prerequisiti

- iMac ONLINE, WA CONNECTED
- PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`
- API KEY: in .env su iMac (ARGOS_API_KEY)
- Numeri WA dealer: nel DB iMac (conversations) e nel file locale non sanitizzato

---

## FASE 0 — Test WA reale (9:00, agent-ops)

**Skill:** `/api-tester`
**Agent:** `agent-ops`

Task: Reset TEST_FOUNDER a COLD, inviare messaggio DAY1_PREMIUM reale via daemon /send,
verificare: messaggio arrivato su WA, DB aggiornato (CONTACTED, outbound_count=1),
log daemon senza errori, Telegram alert ricevuto.

**Go/No-Go:** Se il messaggio NON arriva o il daemon crasha → STOP. Debug con agent-ops.

---

## FASE 1 — Recovery Car Plus (9:10, MANUALE)

**NON usare il daemon.** Inviare dal telefono personale di Luca.

Car Plus (AV) ha risposto il 07-04 con una foto. 2+ giorni di silenzio.
Archetipo RAGIONIERE — tollerante sul tempo, intollerante su risposte vuote.

**Messaggio da telefono:**
```
scusa il ritardo, ero impegnato con una consegna.
ho ricevuto la foto — grazie. mi dice cosa mi sta mostrando?
e' un'auto che ha in stock o qualcosa che sta cercando?

Luca
```

Dopo invio, aggiornare DB:
```sql
UPDATE conversations SET
  outbound_count = outbound_count + 1,
  last_contact_at = datetime('now'),
  current_step = 'RECOVERY_MANUAL'
WHERE dealer_id = 'TIER0_AV_001';
```

---

## FASE 2 — Import 13 dealer enriched (agent-first)

**Skill:** `/backend-architect`
**Agent:** `gsd-executor`

I 13 dealer validati devono essere inseriti nella tabella `conversations` su iMac.
Sorgente: file locale `research/s108_enrichment_13_dealer_validati.json` (numeri sanitizzati nel repo,
numeri reali nel file `research/s106_dealer_profiled_30.json` locale pre-sanitizzazione o nel DB).

ATTENZIONE: I numeri WA reali sono stati sanitizzati nei file committati.
Usare i numeri dal DB iMac o dal backup pre-sanitizzazione.

Controllare che i dealer gia' in DB (Stile Car TIER0_FG_001, Car Plus TIER0_AV_001) non vengano duplicati.

Script: `tools/import_profiled_dealers.py` (gia' pronto, testato dry-run in S106).

---

## FASE 3 — Soft Launch: 1 dealer (se FASE 0 PASS)

**Skill:** `/skill-argos`
**Agent:** `agent-sales`

**Dealer:** Stefano Auto — Cerignola (FG)
- 29 annunci AS24, 4.98/5, 100% raccomandazioni
- Archetipo: RELAZIONALE (famiglia Stefano + figlio Cosimo)
- NON gia' in DB — primo contatto pulito
- Zona FG vicina a Stile Car

**Messaggio (da s108_day1_messages_top5.md):**
```
Buongiorno, sono Luca Ferretti.
Ho visto il suo salone su AutoScout24 — 4.98 su 5, lavora con BMW e Land Rover, giusto?
Seleziono auto premium in tutta Europa per concessionari italiani: tagliandi certificati digitalmente, km tracciati dalla revisione TUV, garanzia costruttore europea valida in Italia.
Auto con allestimenti che qui non arrivano — e margine netto di 3-5.000 euro per lei.
Ha 2 minuti per capire come funziona?
```

**Procedura:**
1. Inserire Stefano Auto nel DB conversations (FASE 2)
2. Validare messaggio col guard CLI
3. Approvazione founder
4. Invio via daemon
5. Monitoring 48h

**Go/No-Go per FASE 4:** Nessun errore tecnico. Se silenzio = OK.

---

## FASE 4 — Outreach scaglionato (1/giorno, giorni successivi)

Solo se FASE 3 OK. Ordine:

| Giorno | Dealer | Template |
|--------|--------|----------|
| +1 | BD Auto (CE) | DAY1_PREMIUM |
| +2 | CUOMO CARS (SA) | DAY1_PREMIUM |
| +3 | AZ Auto Evolution (AV) | DAY1_PREMIUM |
| +4 | Stile Car (FG) | DAY7_RECOVERY (gia' CONTACTED dal 26/03) |

**Regole anti-ban:**
- Max 1 dealer nuovo/giorno, orario 9:00-10:00
- Min 24h tra invii a dealer diversi
- Approvazione umana per ogni risposta ricevuta

---

## Agent Routing per S110

```
FASE 0: agent-ops (test WA reale)
FASE 1: MANUALE (telefono founder)
FASE 2: gsd-executor (import dealer) + backend-architect (schema check)
FASE 3: agent-sales (messaggio + invio) + agent-ops (monitoring)
FASE 4: agent-sales (outreach) + agent-recovery (se Car Plus non risponde)
```

## Security Checklist (gia' completata S109)

- [x] 12 security fix deployati
- [x] 14 chaos test PASS
- [x] 20/20 validator adversarial PASS
- [x] Repo PRIVATE
- [x] Zero PII nei file tracked
- [x] Guard: auth→guard→biz hours→send (ordine verificato)
- [ ] Test WA reale durante business hours (FASE 0)

## File chiave

```
Messaggi DAY1:      research/s108_day1_messages_top5.md
Dealer enriched:    research/s108_enrichment_13_dealer_validati.json
Verifica AS24:      research/s108_dealer_as24_verification.md
Chaos report:       research/s108_chaos_test_report.md
Contratto:          tools/materiali/contratto_incarico_scouting.html
Case study:         tools/materiali/case_study_template.html
Formazione:         tools/materiali/formazione_dealer_kit.md
Import script:      tools/import_profiled_dealers.py
```
