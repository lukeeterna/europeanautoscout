# S148 — Response handling Day 1 Stile Car (watch 48h + albero risposte)

**Sessione**: S148
**Trigger**: monitoraggio post-invio Day 1 a Stile Car (inviato 2026-04-30 16:44 CEST, msg_id `out_1777560285710_7i2id`)
**Finestra critica**: 48h dall'invio = entro 2026-05-02 16:44 CEST

---

## 0. Letture obbligatorie all'avvio

1. `~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/MEMORY.md`
   → entry "2026-04-30 16:44 — S147 DAY 1 INVIATO A STILE CAR"
   → entry "S147 pre-flight Day 1 Stile Car + iMac IP regress"
2. `HANDOFF.md` sezione "S147 OUTCOME"
3. `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` sezione "Risposte pronte" (5 risposte calibrate)
4. `.claude/rules/communication.md` (sequenza touchpoint Day 1/3/7/10/14/21/30)

---

## 1. Pre-flight (in ordine)

### 1.1 Daemon health
```bash
bash .claude/scripts/session_start.sh
curl -sf --max-time 5 http://192.168.1.2:9191/status
```
**IP iMac corrente**: `192.168.1.2` (regress post-reboot S147). Se irraggiungibile → `arp -a | grep a8:20:66` per IP attuale.
Se daemon DOWN → `pm2 resurrect` via SSH con NVM Node 20.11.0 (vedi `imac_network.md`).

### 1.2 Check inbound da Stile Car
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT direction, body, timestamp_it FROM messages WHERE dealer_id='TIER0_FG_001' ORDER BY timestamp_it;\""
```
**Atteso minimo**: 1 entry OUTBOUND (Day 1 inviato).
**Cercato**: 1+ entry INBOUND da 393334254654.

### 1.3 Stato conversazione
```bash
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/Documents/app-antigravity-auto/dealer_network.sqlite \"SELECT dealer_id, current_step, conversation_state, outbound_count, last_contact_at FROM conversations WHERE dealer_id='TIER0_FG_001';\""
```
**Atteso**: current_step=DAY1_SENT, conversation_state=ENGAGED, outbound_count=2 (bug noto, vedi HANDOFF lezione S147).

---

## 2. Decision tree

### 2.A — INBOUND ricevuto (qualsiasi)

Classifica intent del messaggio dealer e applica risposta **da `DAY1_STILE_CAR.md` sezione "Risposte pronte"**:

| Intent dealer | Risposta da usare | Note |
|---------------|-------------------|------|
| "Quanto costa?" / "Prezzo del servizio?" | risposta #1 (€1.000 a consegna) | Mai citare percentuali |
| "Chi sei?" / "Come ti chiami?" / "Referenze?" | risposta #2 (Luca Ferretti + LinkedIn + sito) | Onestà sul "0 recensioni ancora" |
| "Dove hai preso il numero?" / "Come mi hai trovato?" | risposta #3 (AS24 + Google) | Niente "lista comprata" |
| "Già importo da solo" / "Ho fornitore" | risposta #4 (offerta affiancamento test) | NO attacco competitor |
| "Non interessa" / "Nulla" / "No grazie" | risposta #5 (uscita dignitosa) | NON insistere, archivia CLOSED_NO |
| Domanda sul **veicolo specifico** (km, foto, configurazione) | invia dossier PDF: `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf` | Conferma listing 200 OK prima |
| Risposta **positiva**: "Mandami scheda" / "Interessante" / "Vediamo" | invia dossier PDF + frase ponte: "Ecco scheda completa con DAT report e analisi prezzo. La guardi con calma e mi dice se vale la pena bloccarla?" | Pricing detail solo se richiesto |

**SQL UPDATE post-risposta** (NO incremento outbound_count, vedi lezione S147):
```sql
UPDATE conversations
SET current_step='<NUOVO_STEP>',
    conversation_state='ENGAGED',
    last_contact_at=datetime('now'),
    state_updated_at=datetime('now'),
    notes=COALESCE(notes,'') || char(10) || 'S148 risposta a <INTENT> - <ORARIO>'
WHERE dealer_id='TIER0_FG_001';
```

### 2.B — Silenzio < 48h

Watch passive. Nessun follow-up. Check inbound ogni 4-6h. Reminder: il dealer del Sud che riceve un WA alle 16:44 può rispondere anche dopo 24h, è normale.

### 2.C — Silenzio 48-72h

NON fare follow-up automatico. Aspettare 7 giorni dall'invio = **2026-05-07 16:44**.

### 2.D — Silenzio 7 giorni

**Day 3 follow-up** (rules/communication.md riga 39: "Day 3: Foto HD + secondo veicolo"):
- Verifica listing X3 ancora vivo (`curl -sI` 200)
- Verifica DB Market Price Index per **secondo candidato** diverso (es. X1 sport o Serie 3 Touring se nel frattempo è uscita una scraperizzata buona)
- Componi messaggio Day 3 RELAZIONALE: 1 foto HD del X3 + accenno secondo veicolo + domanda chiusa
- **Approvazione Luke obbligatoria** prima dell'invio
- SQL UPDATE post-invio (sempre senza outbound_count)

### 2.E — Silenzio 14 giorni

Break-up message gentile (rules/communication.md riga 42). Esempio:
> "Buongiorno, capisco che il momento non sia quello giusto. Le lascio il numero, se in futuro le serve un veicolo specifico mi scriva. Buon lavoro. Luca."

UPDATE: current_step='BREAKUP_SENT', conversation_state='COLD'.

---

## 3. Vincoli S148 (NON negoziabili)

- ✋ MAX 1 risposta per ogni inbound dealer (no follow-up immediato)
- ✋ NO modifiche al testo delle 5 risposte pronte senza approvazione Luke
- ✋ NO incremento manuale outbound_count (bug noto S147)
- ✋ Se il dealer chiede dossier → verificare PDF esistente in `dossiers/` aggiornato (data scrape ≤7gg, listing 200 OK), altrimenti rigenerare
- ✋ NO citazione tech stack ARGOS (CoVe, Anthropic, RAG, embedding) in nessuna risposta
- ✋ Mantieni firma "Luca" (no "Luca Ferretti" full) finché non chiede esplicitamente referenze

---

## 4. Fine sessione

Se è arrivato inbound + risposta inviata:
1. Aggiorna MEMORY.md con outcome conversazione (intent dealer + risposta usata)
2. Aggiorna `HANDOFF.md` sezione "Stato conversazione Stile Car"
3. Crea `prompts/s149_*.md` se serve continuare follow-up
4. Commit: `HANDOFF.md` + `prompts/s149_*.md`

Se silenzio totale:
1. Aggiorna MEMORY.md: "S148 close — silenzio assoluto, watch continua fino a Day 3 (2026-05-07)"
2. Crea `prompts/s149_day3_check.md` con calendar trigger 2026-05-07

---

## 5. Riferimenti rapidi

- IP iMac: `192.168.1.2` (regress da `.12`)
- Daemon: `http://192.168.1.2:9191`
- DB: `~/Documents/app-antigravity-auto/dealer_network.sqlite` (su iMac via SSH)
- Tabella inbound/outbound: `messages` (col `direction` = `OUTBOUND` o `INBOUND`)
- Tabella conversazione: `conversations` (col `current_step`, `conversation_state`)
- Stile Car: 393334254654 / TIER0_FG_001 / RELAZIONALE 8.5
- Day 1 inviato: 2026-04-30 16:44 CEST, msg_id `out_1777560285710_7i2id`
- Veicolo proposto: BMW X3 xDrive20i 2022 €34.900 (Autohaus Becker-Tiemann)
- Dossier PDF: `dossiers/ARGOS_BMW_X3_2022_Stile_Car_20260427_112932.pdf`
- 5 risposte pronte: `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` (sezione "Risposte pronte")
