# RISPOSTE AUDIT — basate su filesystem + doc più recente
Fonte autorevole più recente: **docs/ROADMAP.md (S286 · 2026-06-26)** — più nuovo di docs/ARCHITETTURA_E2E.md (2026-06-20). Dove disco e ROADMAP divergono, prevale ROADMAP S286.

---

## 1. GATE [E] — TRASPARENZA AZZURRA → **NO (non deployata in produzione)**
- Firma trasparente "Azzurra, l'assistente digitale di Luca Ferretti" + opt-out ('no') → presente SOLO nel REPO: `wa-intelligence/templates.py` (template DAY1_*) e `wa-intelligence/response-analyzer.py:68` (`ARGOS_ASSISTANT='Azzurra'`).
- Daemon LIVE (iMac) = release `20260527_083951`, `templates.py` del 1 Mag → firma vecchia: **"Buongiorno, sono Luca Ferretti."** (impersonificazione, niente Azzurra, niente opt-out).
- Il daemon (`wa-daemon.js`) NON firma da sé: invia testo già composto dalla coda `bridge_outbound`.
- Conferma doc più recente (ROADMAP S286): *"Trasparenza Azzurra chiusa IN-REPO a tutti i layer (S277), NON in produzione (manca sync.sh)."*
- Sblocco = item **[E]**: `bash deploy/sync.sh` (pre-flight symlink wa-sender/, memoria S252), dopo [A] verde.

## 2. RATE-LIMIT WhatsApp (`wa-intelligence/wa-daemon.js`)
- Tetto nominale `DAILY_LIMIT = 30` (riga 46).
- Limite EFFETTIVO = warm-up dinamico `getDailyLimit()` (righe 85-97): settimana ≤1 → **10**, ≤3 → **15**, oltre → **20** (cap 20 hard, API non ufficiale).
- Delay anti-ban tra invii: **30–90s random** (`BRIDGE_ANTI_BAN_DELAY_MS_MIN=30000 / MAX=90000`, righe 201-202) → jitter SÌ.
- Cap risposte per dealer: `MAX_REPLIES_PER_DEALER = 10`/giorno (riga 643).
- Auto-stop: block-rate > 2% → Telegram alert + stop (riga 1937).

## 3. SECOND BRAIN / OBSIDIAN → **NON ESISTE**
- `grep -rni obsidian .` = 0 match. Nessuna cartella `.obsidian`, nessun vault `.md`. Assente, netto.

## 4. FEATURE PIANIFICATO vs REALE (allineato a ROADMAP S286 — 5 fasi)
- **S1 Supply** → IMPLEMENTATO il core: scraper AS24 (`tools/scrapers/autoscout_scraper.py`, E2E ok). Breadth 28 canali + `config/channels.yaml` = **Fase 5, PIANIFICATO** (estende item [C]).
- **S2 Verification** → PARZIALE: CoVe v4 (`src/cove/cove_engine_v4.py`) esiste. `config/argos_standard.yaml` + gap-filling agent = **Fase 5, PIANIFICATO** (mancano su disco).
- **S3 Pricing/Dossier** → motore/dossier onesto **CHIUSO (S271)**: banda p25-p75, margine-intervallo, no-superlativi. **Gate [D]** base-mercato fidata = APERTO (Fase 2 = item [D]): il margine non è ancora credibile davanti a dealer reale.
- **S4 Dealer Profiling** → **ATTIVO ORA** (item corrente dopo [A1], ROADMAP). `data/dealers.db` reale: dealers=1, dealer_profiles=1, dealer_gaps=1, vehicle_observations=28. gap_analysis relativo FATTO (S289, commit 7f10e2a, CLI `gap`, GDPR-clean); raffinamento comparatore di segmento in corso (S290).
- **S5 Azzurra** → PARZIALE: Day-1 generator + AMBRA classifier esistono; trasparenza chiusa in-repo (S277). **Sector wiki `kb/azzurra/` MANCA** = Fase 3 (estende [B]); sequencer multi-touch = PIANIFICATO.
- **S6 Matching dealer↔veicolo** → secondo ROADMAP S286 è **Fase 4 = NUOVO / da costruire** (dipende da S1 supply + S4 profili). Su disco esiste un modulo **legacy/seed** `src/cove/dealer_matcher.py` (331 righe: compute_match_score brand×fascia×gap, match_vehicle_to_dealers, freshness_check) → NON è il matching della nuova architettura. Stato per doc più recente: **PIANIFICATO (Fase 4), con modulo legacy preesistente da riusare/rifare.**
- **S7 Control Plane** → IMPLEMENTATO: VOS, Gate-E (`.harness/gate_e.py`), state machine anelli, scheduler.

### Stato anelli E2E (ROADMAP S286, più recente)
- VERIFIED-smoke: 2 · 9A · 5 — UNVERIFIED: 1 · 9B · 6-7 — BLOCKED (esterno): 8.
- [A1] meccanica d'invio 7a = VERDE chiusa S286 (commit 40a5d1e); ring 6-7 resta UNVERIFIED (consegna WA non re-runnabile in-sessione + breaker 7b deferito ai 3 gate pre-dealer).

### Risposte ai due punti espliciti
- **Matching serve al primo invio?** No, non come prerequisito. Per doc più recente è Fase 4 (dopo profiling + supply). Per UN dealer il Day-1 si genera già con profilo S4 + veicolo scelto; il matching automatico serve alla SCALA, non al primo invio singolo.
- **Messaggio-due (risposta al "sì") esiste?** SÌ, già presente: template `DAY_INTEREST` (`wa-intelligence/templates.py:149`) → manda link contratto + fee "paghi solo dopo consegna documenti". Non è solo annotato.

---

## 5. FLUSSO POST-ACCETTAZIONE: FEE + DOCUMENTI + IMPORT (esiste in CODICE, assente dal blueprint ARCHITETTURA_E2E.md)
> Layer che il blueprint S286 NON modella (si ferma a "success-fee sulla transazione") ma che è già implementato su disco. Catena: **dealer accetta → paga fee → riceve documenti + posizione veicolo → ARGOS cura import automatizzato per nazione/casistica.**

- **Fee** → `tools/fee_calculator.py` (167 righe) + `src/bot/handlers/fee.py`: fee **€800–1.200 success-only** (paga solo a transazione), a tier sul prezzo veicolo (`fee_min=800`, `fee_max=1200`, default 800).
- **Sequenza post-"sì" (template `wa-intelligence/templates.py`)**:
  - `DAY_INTEREST` → dealer accetta: invia link contratto + fee, "paghi solo dopo consegna documenti auto".
  - `IBAN_SEND` → post-firma, a documenti consegnati (status AWAITING_DELIVERY → IBAN_SENT): saldo.
- **Posizione veicolo** → nel report COMPLETO, **rivelata solo dopo pagamento** (report parziale Day-1 = prezzo visibile come gancio, posizione/venditore/URL nascosti). Coerente con feedback pipeline TEST_FOUNDER.
- **Import automatizzato per nazione/casistica** → `tools/import_checklist.py` (365 righe): `generate_checklist(origin_country, is_b2b, dealer_city)`. Documenti country-specific per DE/NL/BE/AT/FR/SE/DK/NO… (Fahrzeugbrief, Kentekenbewijs+NAP, Car-Pass BE, Carte grise FR…), **reverse charge art.17 DPR 633/72**, ACI immatricolazione, distinzione B2B vs privato.

### STATO IMPLEMENTAZIONE VERIFICATO (wiring sul disco, non solo "il file esiste")
| Pezzo | Stato | Evidenza wiring |
|---|---|---|
| **Calcolo fee** | ✅ IMPLEMENTATO + AGGANCIATO | `fee_calculator.py` referenziato da `pdf_generator_enterprise.py` (la fee finisce nel dossier) |
| **State machine post-accettazione** | ✅ IMPLEMENTATO | `comm-broker/deal_state_machine.py`: `DealStateMachine`, `Deal`, `create_deal()`, stato `payment_confirmed` |
| **Posizione veicolo nascosta finché non paga** | ✅ IMPLEMENTATO + CABLATO | `deal_state_machine.py:235` *"La fonte rimane nascosta finché current_state != 'payment_confirmed'"* |
| **Contratto + IBAN (DAY_INTEREST→IBAN_SEND)** | 🟡 PARZIALE | creazione contratto/`sign_url` via argos-proxy cablata (`response-analyzer.py:115`); **l'INVIO di DAY_INTEREST è delegato al caller/HITL** (response-analyzer.py:151), non automatico |
| **Import automatizzato per nazione/casistica** | 🔴 MODULO PRESENTE, **NON AGGANCIATO** | `import_checklist.py` (365 righe, completo per DE/NL/BE/AT/FR…, reverse charge art.17) — ma `grep generate_checklist` in comm-broker/wa-intelligence/src = **0 chiamanti**. Nessuno lo invoca dopo `payment_confirmed`. È codice scritto ma **scollegato dal flusso**. |

**VERDETTO: NON è tutto implementato E2E.** Cosa manca concretamente:
1. **Aggancio import_checklist → state machine**: dopo `payment_confirmed`, nessun codice chiama `generate_checklist(origin_country, is_b2b, dealer_city)`. Il disbrigo per nazione è una funzione orfana. → serve il wiring nel ramo post-pagamento di `deal_state_machine.py`.
2. **Invio automatico contratto/IBAN**: oggi DAY_INTEREST/IBAN_SEND partono via caller HITL (Telegram), non come transizione automatica della state machine.
3. **Collaudo E2E runtime**: i pezzi 1-3 (fee, state machine, posizione-nascosta) esistono e sono cablati ma NON girati end-to-end in questa sessione (TEST_FOUNDER).

NB: questo intero layer **manca dal doc `ARCHITETTURA_E2E.md`** (si ferma a "success-fee") → gap di documentazione sul progetto + 1 gap reale di codice (l'aggancio import_checklist).

---

## 3 GATE TECNICI A INVIO DEALER REALE (ROADMAP S286)
[A] E2E verde + Luke soddisfatto · **[E] trasparenza live (= NO oggi)** · [D] base-mercato fidata.
