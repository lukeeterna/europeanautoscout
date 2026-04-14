# DOSSIER: Merge Anti-Ban Layer FLUXION → ARGOS
**Data**: 2026-04-14 | **Stato**: PROPOSTA — in attesa audit fondatore
**Fonte**: `/Volumes/MontereyT7/FLUXION/tools/SalesAgentWA/SALES-AGENT-BLUEPRINT.md`

---

## 0. PREMESSA — PERCHE' QUESTO DOSSIER

Il fondatore ha chiesto che la pipeline ARGOS operi **autonomamente** senza human-in-the-loop.
Il blueprint FLUXION Sales Agent contiene un layer anti-ban piu' maturo di quello ARGOS.
Questo dossier propone un merge selettivo di 6 componenti.

**Nessun codice viene scritto prima dell'approvazione del fondatore.**

---

## 1. STATO ATTUALE ARGOS (evidence-based)

### Cosa funziona gia'
- whatsapp-web.js daemon (porta 9191) — connesso, sessione persistente, headless
- State machine: COLD → CONTACTED → ENGAGED → INTERESTED → CLOSED
- Template-first + LLM fallback (Gemini/Groq/OpenRouter cascade)
- CoVe Engine scoring + PDF dossier enterprise (922KB, 6 foto)
- Response analyzer con classificatore (POSITIVE/NEGATIVE/CURIOSITY/OBJECTION/VEHICLE_REQUEST/MEDIA)
- Noise filter (fixato S116) — filtra body vuoti, base64, encoded
- Anti-spam 24h cooldown + sha256 dedup (fixato S116)
- Telegram alert su ogni evento

### Cosa MANCA per operazione autonoma sicura
1. **Zero warm-up** — daily_limit=30 dal giorno 1. Account nuovo = alto rischio ban
2. **Zero variazione testo** — se LLM genera messaggi simili a N dealer, WA flagga
3. **Zero pausa lunga** — raffica di 5-10 msg senza break = pattern bot
4. **Zero stats aggregate** — non possiamo misurare delivery/read/reply/block rate per giorno
5. **Zero block rate monitoring** — se un dealer segnala spam, non lo sappiamo
6. **Zero pause/resume** — per fermare tutto serve `pm2 stop` (no graceful)

---

## 2. COSA PROPONGO (6 componenti)

### COMPONENTE 1: Warm-up Schedule

**Cosa**: Limite giornaliero progressivo che sale con l'eta' dell'account.
**Perche'**: Account WA nuovi con volume alto = ban immediato (fonte: Chatarmin 2025, WASenderAPI docs).
**Come**: Tabella `agent_state` in dealer_network.sqlite + logica in wa-daemon.js.

```
Settimana 1-2:  max  5 msg/giorno  (fondatore puo' ancora supervisionare)
Settimana 3-4:  max 10 msg/giorno
Settimana 5:    max 20 msg/giorno
Settimana 6+:   max 25 msg/giorno  (MAI superare 30)
```

**File modificati**: wa-daemon.js (CONFIG section)
**Rischio**: Nessuno — e' solo un cap piu' conservativo
**Alternativa**: Restare a daily_limit=30 fisso (rischio ban alto)
**Verifica**: `curl localhost:9191/status` mostra `daily_limit` corrente

---

### COMPONENTE 2: Variazione Testo (Jaccard Check)

**Cosa**: Prima di inviare, confrontare il messaggio con gli ultimi 5 inviati. Se la similarita' Jaccard e' >60% (variazione <40%), rigenerare.
**Perche'**: WA detecta messaggi ripetitivi come spam. L'incidente Car Plus (3 msg LLM quasi identici + fee leak) lo dimostra.
**Come**: Funzione `estimate_variation()` da FLUXION (trigram Jaccard) aggiunta in response-analyzer.py.

```python
def estimate_variation(msg1: str, msg2: str) -> float:
    """Jaccard distance su trigrammi. Target: > 0.40"""
    def trigrams(text):
        return set(text[i:i+3] for i in range(len(text) - 2))
    t1, t2 = trigrams(msg1.lower()), trigrams(msg2.lower())
    if not t1 and not t2:
        return 1.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return 1.0 - (intersection / union if union > 0 else 0)
```

**File modificati**: response-analyzer.py (pre-approve check)
**Rischio**: Basso — se il check fallisce 5 volte, invia comunque (graceful degradation)
**Alternativa**: Non fare check — rischio msg ripetitivi = ban
**Verifica**: Log `[VARIATION] X% vs last msg — PASS/REGEN`

---

### COMPONENTE 3: Long Pause ogni N messaggi

**Cosa**: Ogni 5 messaggi inviati, pausa di 5-10 minuti.
**Perche'**: Pattern "5 msg rapidi poi silenzio" e' piu' umano di "1 msg ogni 2 min per 6 ore".
**Come**: Contatore in wa-daemon.js che triggera sleep dopo ogni 5o invio.

```javascript
// In /send endpoint, dopo invio OK:
CONFIG.DAILY_SENT++;
if (CONFIG.DAILY_SENT % 5 === 0) {
    const pauseMs = Math.floor(Math.random() * 300000) + 300000; // 5-10 min
    log('INFO', `Long pause: ${Math.round(pauseMs/60000)} min (every 5 msgs)`);
    // La pausa NON blocca il server — solo un flag che rifiuta invii per N minuti
    CONFIG.PAUSE_UNTIL = Date.now() + pauseMs;
}
```

**File modificati**: wa-daemon.js (send endpoint + config)
**Rischio**: Rallenta throughput. Con 25 msg/giorno e 5 pause da 7min = +35min. Accettabile.
**Alternativa**: Nessuna pausa — rischio pattern bot
**Verifica**: Log `Long pause: Xm` + `curl /status` mostra `pause_until`

---

### COMPONENTE 4: daily_stats Table

**Cosa**: Tabella SQLite che aggrega metriche per giorno.
**Perche'**: Senza dati aggregati non puoi misurare se il sistema funziona o sta per essere bannato.
**Come**: Nuova tabella in dealer_network.sqlite + update automatico in wa-daemon.js.

```sql
CREATE TABLE IF NOT EXISTS daily_stats (
    date            TEXT PRIMARY KEY,       -- YYYY-MM-DD
    sent            INTEGER DEFAULT 0,      -- messaggi inviati
    delivered       INTEGER DEFAULT 0,      -- ACK delivered
    read_count      INTEGER DEFAULT 0,      -- ACK read
    replied         INTEGER DEFAULT 0,      -- risposte ricevute
    failed          INTEGER DEFAULT 0,      -- invii falliti
    blocked         INTEGER DEFAULT 0,      -- segnalazioni spam
    new_contacts    INTEGER DEFAULT 0       -- primi contatti (COLD→CONTACTED)
);
```

**File modificati**: wa-daemon.js (crea tabella + incrementa contatori), response-analyzer.py (incrementa replied)
**Rischio**: Nessuno — solo INSERT/UPDATE, non modifica tabelle esistenti
**Alternativa**: Calcolare stats on-demand con query su messages (lento, impreciso)
**Verifica**: `SELECT * FROM daily_stats ORDER BY date DESC LIMIT 7`

---

### COMPONENTE 5: Block Rate Monitoring + Auto-Stop

**Cosa**: Se block_rate > 2% su ultimi 50 msg → STOP automatico + alert Telegram.
**Perche'**: Un block rate alto = WA sta per bannare il numero. Meglio fermarsi subito.
**Come**: Check periodico (ogni ora) in wa-daemon.js scheduler.

```
Soglie (da FLUXION, allineate a best practice 2025):
- Delivery rate < 85% → WARNING Telegram
- Block rate > 2%     → AUTO-STOP + Telegram "PERICOLO BAN"
- Read rate < 20%     → WARNING "rivedi templates"
- Reply rate < 2%     → WARNING "hook debole"
```

**File modificati**: wa-daemon.js (scheduler + nuovo endpoint GET /health-metrics)
**Rischio**: False positive se campione troppo piccolo (<20 msg). Soglia minima: almeno 20 msg inviati.
**Alternativa**: Monitorare manualmente — impraticabile per autonomia
**Verifica**: `curl localhost:9191/health-metrics` + alert Telegram

**NOTA CRITICA**: Il block detection dipende da WA che notifica il block. whatsapp-web.js puo' rilevare alcuni segnali (numero non raggiungibile, errore invio) ma NON tutti i block. Il monitoring e' best-effort, non garantito.

---

### COMPONENTE 6: Pause/Resume API

**Cosa**: Endpoint HTTP per mettere in pausa e riprendere l'agent.
**Perche'**: Se qualcosa va storto, devi poter fermare tutto con un comando.
**Come**: Nuovo endpoint in wa-daemon.js + stato in agent_state.

```
POST /pause  → imposta stato=paused, blocca tutti gli invii
POST /resume → imposta stato=active, riprende invii
GET /status  → mostra stato paused/active
```

**File modificati**: wa-daemon.js (2 nuovi endpoint + check stato in /send)
**Rischio**: Nessuno — aggiunge solo un gate, non modifica flusso esistente
**Alternativa**: `pm2 stop/start` — funziona ma perde sessione WA e richiede SSH
**Verifica**: `curl -X POST localhost:9191/pause -H "X-API-Key: ..."` → `{"status":"paused"}`

---

## 3. COSA NON FACCIO (e perche')

| Proposta scartata | Motivo |
|---|---|
| Sostituire whatsapp-web.js con Playwright | Playwright WA e' fragile (selettori CSS cambiano, serve GUI, QR frequente). whatsapp-web.js usa protocollo diretto, headless, sessione persistente, bidirezionale |
| DB separato leads.db | Aggiungere tabelle a dealer_network.sqlite. Un DB = una fonte di verita' |
| Rimuovere LLM per risposte | Per Day 1 template-only va bene. Ma quando un dealer chiede "che km ha?" serve LLM contestuale |
| Copiare il funnel YouTube→Landing→Stripe | ARGOS vende dossier PDF B2B, non SaaS B2C |
| LaunchAgent al posto di PM2 | PM2 e' superiore per daemon always-on con restart automatico |

---

## 4. ORDINE DI IMPLEMENTAZIONE

```
Fase 1 (sicurezza): Componente 1 (warm-up) + 6 (pause/resume)
  → Protegge il numero WA prima di qualsiasi invio autonomo
  → Tempo: ~2h

Fase 2 (qualita'): Componente 2 (variazione) + 4 (daily_stats)
  → Migliora qualita' messaggi + abilita misurazione
  → Tempo: ~2h

Fase 3 (monitoring): Componente 3 (long pause) + 5 (block rate)
  → Completa il layer anti-ban
  → Tempo: ~2h

Test E2E dopo ogni fase con TEST_FOUNDER.
```

---

## 5. RISCHI E MITIGAZIONI

| Rischio | Probabilita' | Impatto | Mitigazione |
|---|---|---|---|
| WA ban nonostante anti-ban | Media | Critico | Warm-up + variazione + pause + block monitor. Se ban: SIM nuova €10, riparti da settimana 1 |
| Playwright selectors FLUXION non applicabili | N/A | N/A | Non usiamo Playwright — whatsapp-web.js |
| LLM leak fee/banned words | Bassa (post S116 fix) | Alto | Validator v2 BLOCCA + retry. Template-first per Day 1 |
| Warm-up troppo lento (5 msg/giorno) | Certa | Basso | E' il prezzo della sicurezza. 5 dealer/giorno x 5 giorni = 25 dealer in settimana 1 |
| daily_stats tabella non allineata | Bassa | Basso | Contatori incrementali, recovery con query su messages |

---

## 6. DOMANDE APERTE PER IL FONDATORE

1. **Warm-up settimana 1-2**: 5 msg/giorno ok o vuoi partire con di piu'?
2. **Pausa/Resume**: vuoi anche un comando Telegram `/pause` `/resume` o solo API HTTP?
3. **Block threshold**: 2% ok o vuoi piu' conservativo (1%)?
4. **Day 1 template vs LLM**: per il PRIMO messaggio a un dealer nuovo, vuoi template fisso (deterministic, zero rischio leak) o LLM con guardrail?
5. **Priorita'**: inizio da Fase 1 (sicurezza) o vuoi tutto insieme?

---

## 7. DONE CRITERIA

| Componente | Test | Evidence |
|---|---|---|
| 1. Warm-up | `curl /status` → daily_limit=5 settimana 1 | JSON response |
| 2. Variazione | Invia 3 msg → log mostra variation >40% | pm2 logs |
| 3. Long pause | Invia 5 msg → pausa 5-10min dopo il 5o | pm2 logs |
| 4. daily_stats | `SELECT * FROM daily_stats` → row per oggi | SQLite query |
| 5. Block monitor | Simula block rate >2% → Telegram alert | TG message |
| 6. Pause/Resume | `POST /pause` → `/send` rifiutato → `POST /resume` → `/send` ok | curl response |

---

*Documento pronto per audit. Nessuna riga di codice viene scritta prima dell'approvazione.*
