# S145 — Outreach primo dealer reale (Stile Car)

**Stato**: tutti i blocker pre-WA chiusi a fine S144. LinkedIn live, Gmail attivo, GBP attivato, Cloudflare production OK, WA daemon connesso.

**Obiettivo S145**: completare le 3 cose che mancano per inviare il primo Day 1 reale a Stile Car (Orta Nova FG) con credibilità intatta:
1. Verificare/popolare LinkedIn Luca Ferretti
2. Pre-warming 3 giorni passive sui 3 dealer COLD
3. Test TEST_FOUNDER → Day 1 a Stile Car

---

## STEP 0 — Read & verify (5 min)

```bash
# Identità live
cat ~/.claude/projects/-Users-macbook-Documents-combaretrovamiauto-enterprise/memory/luca_ferretti_identity.md

# WA daemon
ssh gianlucadistasi@192.168.1.2 "curl -sf http://localhost:9191/status"

# Cloudflare production deve servire image/jpeg
curl -sI https://argos-automotive.pages.dev/assets/luca_ferretti/luca_portrait_formal.jpg | head -3

# DB stato attuale (path + tabella corretti S145)
ssh gianlucadistasi@192.168.1.2 'sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite \
  "SELECT dealer_id,dealer_name,city,persona_type,score,current_step FROM conversations WHERE conversation_state=\"COLD\" ORDER BY score DESC;"'
```

Atteso:
- WA: `wa_status: connected`, business hours
- Cloudflare: `content-type: image/jpeg`
- DB: 5 dealer COLD — Stile Car FG **RELAZIONALE** 8.5, Autoline AV RAGIONIERE 8.0, GP Cars TA NARCISO 8.0, Car Plus AV RAGIONIERE 7.5, Sa.My. Auto CS TECNICO 7.0

Se uno fallisce → debug PRIMA di procedere.

---

## STEP 1 — Verifica LinkedIn popolato (10 min, manuale Luke)

Chiedi a Luke screenshot di:
- Foto profilo (deve essere `luca_portrait_formal.jpg` da Imagen)
- Banner (deve essere `luca_munich_street.jpg`)
- Headline ("Import Manager @ ARGOS Automotive | Auto Premium EU → Sud Italia")
- About (testo di `.planning/launch_luca_ferretti/LINKEDIN_ABOUT.md`)
- Post fissato (testo di `.planning/launch_luca_ferretti/LINKEDIN_POST_FISSATO.md`)

Se manca qualcosa → Luke completa. CC produce eventuali rifiniture testo se serve.

**NON proseguire a Step 2 finché LinkedIn non è completo.** Un dealer NARCISO che apre LinkedIn vuoto = autogol, regola "se salti uno step ricomincia da capo".

---

## STEP 2 — Pre-warming 3 giorni (passive, da Luke)

**Scelta deliberata S145**: pre-warming attivo solo sui 3 top score COLD (Stile Car / Sa.My. / Car Plus), NON tutti i 5. Motivo: profilo LinkedIn nuovo che fa 5 follow+like in pochi minuti = pattern bot, rischio restriction. Autoline + GP Cars (entrambi 8.0) restano watchlist e si attivano in S146 dopo validazione flow Stile Car.

### Day 1 (oggi, 5 min)
Da LinkedIn Luca Ferretti:
- Follow Stile Car Orta Nova (o titolare se non c'è pagina aziendale)
- Follow Sa.My. Auto Rende
- Follow Car Plus Grottaminarda
- Like 1 post recente di ciascuno (se hanno post)

### Day 2 (domani, 5 min)
- 1 commento breve non-pitch su un post di Stile Car (es. "Bella X3, configurazione rara da trovare in Puglia")
- Niente DM. Niente menzione ARGOS.

### Day 3 (dopodomani, 5 min)
- 1 commento simile su Sa.My. Auto o Car Plus (alternato)

Obiettivo: quando il dealer riceve WA Day 4, cerca "Luca Ferretti" su LinkedIn e trova un profilo che lo segue da 3 giorni con interazioni autentiche.

---

## STEP 3 — Day 4: test + invio (30 min, eseguito da CC con conferma Luke)

### 3a. Pre-flight listing (5 min)
```bash
LISTING="https://www.autoscout24.de/angebote/bmw-x3-xdrive20i-ahk-hifi-sportsitze-benzin-schwarz-70dcd99b-3d68-45ac-ae20-2113e8f3d719"
curl -sI "$LISTING" | head -1
# Atteso: HTTP/2 200
```

Se 404 → rieseguire scrape:
```bash
python3 tools/on_demand_runner.py --marca BMW --modello X3 --budget 35000 --dealer "Stile Car"
```
e prendere nuovo top candidate. Aggiornare DAY1_STILE_CAR.md con nuovi numeri.

### 3b. Test su TEST_FOUNDER (5 min)
```bash
ssh gianlucadistasi@192.168.1.2 "curl -X POST localhost:9191/send \
  -H 'Content-Type: application/json' \
  -d '{\"to\":\"393314928901\",\"message\":\"<testo Day 1 esatto>\"}'"
```

Verifica con Luke che il messaggio sia arrivato leggibile su WA TEST_FOUNDER prima di inviare al dealer.

### 3c. Invio Day 1 a Stile Car (1 messaggio, irreversibile)
- Numero: 393334254654
- Testo: corpo del messaggio in `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md` (sezione "DAY 1 — messaggio", **calibrato RELAZIONALE** S145)
- Endpoint: `POST localhost:9191/send` con X-API-Key header (vedi `.claude/rules/security.md`)
- **CONFERMA ESPLICITA LUKE PRIMA DI POST**: invio reale a numero reale, primo dealer ARGOS in assoluto.

### 3d. Annotazione DB (path + tabella + colonne corretti S145)
```bash
ssh gianlucadistasi@192.168.1.2 'sqlite3 /Users/gianlucadistasi/Documents/app-antigravity-auto/dealer_network.sqlite \
  "UPDATE conversations SET current_step=\"DAY1_SENT\", \
                            last_contact_at=datetime(\"now\"), \
                            outbound_count=outbound_count+1, \
                            state_updated_at=datetime(\"now\"), \
                            notes=\"Day1 X3 €34.904 RELAZIONALE inviato via WA daemon S145\" \
   WHERE dealer_id=\"TIER0_FG_001\";"'
```
NB: schema `conversations` non ha `pipeline_status / next_action_at / next_action_type`. Colonne disponibili rilevanti: `current_step`, `last_contact_at`, `conversation_state`, `outbound_count`, `state_updated_at`, `notes`.

---

## STEP 4 — 48h silent observation

- NO follow-up automatico
- Check WA inbound ogni 12h (manuale o via response-analyzer)
- Se inbound → segui albero risposte in `DAY1_STILE_CAR.md`
- Se silenzio 7gg → Day 3 soft (da definire — non auto-inviare)

---

## VINCOLI S145 (non derogabili)

- Test TEST_FOUNDER PRIMA di dealer reale (CLAUDE.md)
- Pre-warming 3gg PRIMA di Day 1 (regola sequenza credibilità Sud)
- Listing 200 OK pre-invio
- Max 5 righe Day 1, NO trigger words
- Conferma esplicita Luke prima di POST /send a dealer reale
- 1 solo messaggio Day 1 per numero (CLAUDE.md)

## Stato che NON va toccato in S145

- `cove_engine_v4.py` (NON modificare)
- `landing/index.html` (production OK)
- `fee_calculator.py` (problema noto S144 ma non blocking — fix in S146+)
- Scraper ADAC X4 lowball (gap noto, non blocking — usare X3)
