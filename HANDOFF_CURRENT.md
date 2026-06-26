# HANDOFF — S4 — Compositore Day-1 VEICOLO-FIRST (primo messaggio reale)

**DEALER = de_cicco_cs (De Cicco S.r.l., Casali del Manco CS) — micro, profilo completo (fb 504 / ig 1011, 4 anchor)**
**VEICOLO REALE = BMW X1 sDrive18i, 2025, 8.900 km, EUR 40.890 (Germania) — listing `autoscout24_de_9f222b8d5e8a`**

## DAY-1 GENERATO (incollato integrale)
```
BMW X1 sDrive18i, 2025, 8.900 km — Germania, EUR 40.890 consegnata.
Km tracciati TUV, tagliandi certificati, garanzia costruttore valida in Italia.
Un SUV premium tedesco in piu' per la sua vetrina: le interesserebbe?
Sono Azzurra, assistente digitale di Luca Ferretti; ho preso il suo contatto da AutoScout24. Se preferisce non ricevere messaggi mi scriva 'no'.
```

---

## FASE 0 — re-ground (riportato)
- `pwd`=root, HEAD=334b69c, status=solo rumore-hook NEXT_SESSION_PROMPT → OK.
- Candidati piccoli con profilo completo: **de_cicco_cs** (fb 504 / ig 1011, segmento mainstream + Land Rover SUV) e 2f_motors_cs (fb 1922 / ig 4230, gia' premium-tedesco). Esclusi gp_cars/carfora/samy (strutturati).
- Firma esistente: `generate_cold_day1(dealer_brands, source, dealer_name="")` in templates.py:273.
- Veicoli reali gia' raccolti: `dealer_network.sqlite.market_listings` = 67 (BMW Serie3 ×47, BMW X1 ×20). Nessun fetch live necessario.
- Regola primo-messaggio cablata nel validator `wa-intelligence/validator.py` (CRED-SEQUENCE-001, NO-OFFER-DAY1-001, LEX-SCARCITY, BRAND-SELFPROMO, BANNED_WORD...).

## Scelta dealer + veicolo (e perche')
- **de_cicco_cs** scelto come da default: profilo+handle COMPLETI → non scatta la clausola di switch. Calza l'ICP "crescita nel premium": De Cicco tratta mainstream (Kia/Suzuki/Dacia) + **Land Rover (SUV premium)** → e' un dealer che ARGOS *gradua* verso il premium tedesco, NON un gia-strutturato.
- 2f_motors scartato: gia' Audi/BMW/Porsche/Mercedes = "rifornimento a un gia-strutturato", ICP sbagliato.
- **BMW X1** (SUV premium compatto) scelto perche' coerente col segmento **SUV** che De Cicco gia' tratta (Land Rover): pertinenza implicita = un SUV premium tedesco per la sua vetrina, MAI "ho visto il tuo Instagram". Veicolo REALE da market_listings (km/anno/prezzo reali), nessun placeholder.

## BUILD (additivo, retro-compatibile)
- `wa-intelligence/templates.py`:
  - nuovo template **`DAY1_VEHICLE_FIRST`** (apre col veicolo + numeri + 1 domanda chiusa; firma Azzurra + provenienza + opt-out in coda).
  - `generate_cold_day1(...)` esteso con `vehicle=None, profile=None`. **Retro-compatibile**: senza `vehicle` resta identico (legacy DAY1_PREMIUM/MIXED/GENERALIST).
  - SLOT_DEFAULTS: aggiunti `vehicle_variant`, `country`, `segmento`.

## DONE-CONDITION (evidenza)
1. Dealer+perche' + veicolo reale → sopra. OK
2. Day-1 incollato → apre con veicolo+numeri+domanda chiusa, NESSUNA presentazione iniziale, NON cita profilo/Instagram/social. OK
3. **Superlativi sul Day-1 = 0** (grep su 12 pattern: miglior/unico/imbattibil/leader/eccezional/...). OK
4. **Validator esistente: PASS 13/13** (`validate(msg,"DAY1_VEHICLE_FIRST",{current_step:COLD,outbound_count:0})` → All checks passed). Passato ONESTAMENTE: il template NON e' nell'exempt-list; CRED-SEQUENCE-001 soddisfatto via anchor legittimo "la sua vetrina" (pertinenza, non sorveglianza), nessun pattern NO-OFFER-DAY1. OK
5. **Idempotenza**: re-run → messaggio identico, funzione pura, 0 effetti collaterali (nessun write DB). OK
6. **0 dati personali del titolare**. Firma Azzurra + opt-out 'no' + provenienza presenti. OK

## Tensione architetturale (flag onesto, non episodio)
Il validator codifica la filosofia OPPOSTA al mandato: CRED-SEQUENCE-001 + NO-OFFER-DAY1-001 = "Day-1 e' solo hypothesis framing, offerta dopo". communication.md ha entrambe le regole in contraddizione ("PRIMO CONTENUTO = veicolo reale" vs "credibilita' sequenziale, offerta = step 4"). Il mandato S4 sceglie deliberatamente veicolo-first; passato senza toccare il validator. **Da decidere a monte se la sequenza-credibilita' va rivista o se veicolo-first e' l'eccezione cablata.**

## APERTO (pre-invio, non bloccante per Gate-E)
- **Provenienza**: `de_cicco_cs.source_url = NULL`. Ho usato "AutoScout24" (portale-inventario). La vera fonte-contatto e' social/CRM → **correggere la stringa-provenienza al valore reale prima di QUALSIASI invio**. Gate-E intatto, nessun invio in questa sessione.

## File nominati (commit locale, no push)
- `wa-intelligence/templates.py`
- `HANDOFF_CURRENT.md`
