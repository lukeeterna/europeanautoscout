# S110 — Soft Launch Outreach (Domani 9:00)

## Prerequisito
iMac ONLINE, WA CONNECTED, daemon stabile.
PM2 SSH: `export PATH=$HOME/.npm-global/bin:/usr/local/bin:$PATH`
API KEY: h_65WFGPMtlgROInLfZtU5TM8hFlVLfYLrn8vSV6kko

## Stato pre-sessione (da S108-S109)

**Completato:**
- Deploy S106 su iMac + fix state_machine + fix templates + fix voice templates
- E2E guard test 6/6 PASS (clean OK, fee BLOCK, tech BLOCK, state BLOCK, post_send OK, DB OK)
- DB contatori resync, stati corretti, test data puliti
- 13 dealer enriched pronti, 5 messaggi DAY1 pronti
- Business hours enforcement confermato (blocca fuori 9-18)

**DA FARE in ordine:**

---

## FASE 0 — Test daemon WA reale (9:00, 5 min)

L'unico test mancante. Serve business hours (9-18).

```bash
# Reset TEST_FOUNDER a COLD
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"UPDATE conversations SET conversation_state='COLD', outbound_count=0 WHERE dealer_id='TEST_FOUNDER';\""

# Invio WA reale al founder
curl -s -X POST http://192.168.1.2:9191/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: h_65WFGPMtlgROInLfZtU5TM8hFlVLfYLrn8vSV6kko" \
  -d '{
    "phone": "393314928901",
    "message": "Test S110 — guard attivo, post_send attivo.\n\nBuongiorno sono Luca Ferretti.\nHo visto il suo salone su AutoScout24.\nHa 2 minuti?",
    "dealer_id": "TEST_FOUNDER",
    "template_id": "DAY1_PREMIUM"
  }'
```

**Checklist PASS:**
- [ ] Messaggio arrivato su WA del founder
- [ ] Newline formattati correttamente
- [ ] DB: TEST_FOUNDER conversation_state = CONTACTED, outbound_count = 1
- [ ] Log daemon senza errori
- [ ] Telegram alert ricevuto (se configurato)

**Se FAIL:** Non procedere. Debug con agent-ops.

---

## FASE 1 — Recovery Car Plus (9:10, manuale)

Car Plus ha risposto il 07-04 con una foto. 2+ giorni di silenzio. Recovery MANUALE dal telefono di Luca (NON dal daemon).

**Messaggio da telefono:**
```
scusa il ritardo, ero impegnato con una consegna.
ho ricevuto la foto — grazie. mi dice cosa mi sta mostrando?
e' un'auto che ha in stock o qualcosa che sta cercando?

Luca
```

**Dopo invio manuale, aggiornare DB:**
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"
UPDATE conversations SET 
  outbound_count = outbound_count + 1,
  last_contact_at = datetime('now'),
  current_step = 'RECOVERY_MANUAL'
WHERE dealer_id = 'TIER0_AV_001';
\""
```

---

## FASE 2 — Import 13 dealer enriched nel DB

**Skill:** `/backend-architect`

I 13 dealer validati e enriched devono essere inseriti nella tabella conversations per poter usare il daemon.
File sorgente: `research/s108_enrichment_13_dealer_validati.json` (gia' su iMac)

Script da creare o usare `tools/import_profiled_dealers.py` adattato per i 13 enriched.

Verificare che i dealer gia' in DB (Stile Car TIER0_FG_001) non vengano duplicati.

---

## FASE 3 — Soft Launch: 1 dealer (se FASE 0 PASS)

**Dealer scelto: Stefano Auto — Cerignola (FG)**
- 29 annunci AS24, 4.98/5, 100% raccomandazioni
- Archetipo: RELAZIONALE (famiglia Stefano + figlio Cosimo)
- WA: +39 338 819 9414
- NON gia' in DB (dealer nuovo)
- Zona FG vicina a Stile Car — se funziona, rafforza la presenza territoriale
- RELAZIONALE = piu' aperto al primo contatto, meno diffidente

**Perche' Stefano Auto e non Stile Car:**
Stile Car e' gia' in DB come CONTACTED (Day1 inviato 26/03, no risposta). Inviargli un secondo messaggio richiede DAY7_RECOVERY. Stefano Auto e' vergine — primo contatto pulito.

**Messaggio (da s108_day1_messages_top5.md):**
```
Buongiorno, sono Luca Ferretti.
Ho visto il suo salone su AutoScout24 — 4.98 su 5, lavora con BMW e Land Rover, giusto?
Seleziono auto premium in tutta Europa per concessionari italiani: tagliandi certificati digitalmente, km tracciati dalla revisione TUV, garanzia costruttore europea valida in Italia.
Auto con allestimenti che qui non arrivano — e margine netto di 3-5.000 euro per lei.
Ha 2 minuti per capire come funziona?
```

**Procedura:**
1. Inserire Stefano Auto nel DB conversations
2. Validare messaggio col guard (CLI)
3. Preview su Telegram per approvazione founder
4. Invio via daemon
5. Monitoring 48h

**Criteri GO per FASE 4:**
- Nessun errore tecnico
- Messaggio arrivato correttamente
- Se risponde: classificazione corretta
- Se silenzio: OK (normale)

---

## FASE 4 — Outreach scaglionato (1/giorno, giorni successivi)

Solo se FASE 3 OK. Ordine:

| Giorno | Dealer | WA | Template |
|--------|--------|-----|----------|
| +1 | BD Auto (CE) | 320 864 9717 | DAY1_PREMIUM |
| +2 | CUOMO CARS (SA) | 351 567 2993 | DAY1_PREMIUM |
| +3 | AZ Auto Evolution (AV) | 345 414 6671 | DAY1_PREMIUM |
| +4 | Stile Car (FG) | 333 425 4654 | DAY7_RECOVERY (gia' CONTACTED) |

**Regole anti-ban:**
- Max 1 dealer nuovo/giorno
- Orario: 9:00-10:00 (inizio business)
- Min 24h tra invii a dealer diversi
- Approvazione umana per ogni risposta ricevuta

---

## File chiave

```
Messaggi DAY1:      research/s108_day1_messages_top5.md
Dealer enriched:    research/s108_enrichment_13_dealer_validati.json
Verifica AS24:      research/s108_dealer_as24_verification.md
Contratto:          tools/materiali/contratto_incarico_scouting.html (con Art.5-bis)
Case study:         tools/materiali/case_study_template.html
Formazione:         tools/materiali/formazione_dealer_kit.md
```
