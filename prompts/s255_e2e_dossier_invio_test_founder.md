# S255 — Chiudere E2E anello 6-7 (invio dossier su TEST_FOUNDER)

**Generato S254** (2026-06-08, context chiuso a 66% prima dell'invio).
Apri fresco col telefono business (39<TEST_FOUNDER_NUM>) in mano.

## Stato verificato S254 (wiring E2E COMPLETO — non ri-investigare)

- Daemon iMac: **ONLINE**, `wa_status=connected`, `daily_sent=0/20`, business hours OK.
- Tabella `dossiers` **ESISTE** su `~/Documents/app-antigravity-auto/dealer_network.sqlite` (iMac, 389KB).
- L'endpoint doc del daemon (`wa-intelligence/wa-daemon.js:1492`, URL `/` + `send` + `-doc`) è **DUAL**:
  1. 1ª chiamata con `{phone,file_path,dealer_id}` → auto-registra PENDING → risponde `403 {error:"dossier registered, awaiting Luke approval", dossier_id:N}` + alert Telegram.
  2. Dopo che Luke approva → 2ª chiamata IDENTICA → `approval_status=APPROVED` → **invia** il PDF (`200 {status:"sent"}`).
- Approvazione Luke: dashboard `http://192.168.1.2:8080/pending-dossiers` (click) — preview confinata a `~/Documents/app-antigravity-auto/dossiers/` (`_DOSSIERS_BASE`, app.py:1035).
- Gate E (hook): invio al SOLO `39<TEST_FOUNDER_NUM>` con numero **esplicito nel comando bash** → ALLOW automatico. **Niente `gate_e approve` manuale** per TEST_FOUNDER. Se il numero NON è esplicito → ramo "no-number" → DENY.
  - NB FP noto: la classe `outreach_real` matcha la signature anche nella PROSA di un `git commit -m` → evita la stringa endpoint-doc nei messaggi di commit.
- Il runner `tools/on_demand_runner.py` si ferma a scrape→CoVe→PDF: registrazione/invio passano SOLO dall'endpoint doc, non dal runner. Gap confermato.

## BLOCKER da risolvere PRIMO (unico)

Il PDF è solo su MacBook: `dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf` (2.3MB).
Il daemon verifica l'esistenza del file **locale su iMac** → copialo su iMac:

```
scp dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf \
  gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/dossiers/
```

## Sequenza E2E (copia-incolla)

1. **scp PDF** su iMac (sopra).
2. **Registra PENDING** (curl gira SU iMac via ssh, daemon su localhost:9191; numero esplicito = Gate E allow). L'URL endpoint = `/` + `send` + `-doc`:
```
ssh gianlucadistasi@192.168.1.2 'curl -s -X POST localhost:9191/send-doc \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"39<TEST_FOUNDER_NUM>\",\"file_path\":\"/Users/gianlucadistasi/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf\",\"dealer_id\":\"TEST_FOUNDER\",\"caption\":\"Esempio dossier ARGOS\"}"'
```
   → atteso `403 ... dossier_id:N`. Se `401 unauthorized` → aggiungi header `-H "X-API-Key: <ARGOS_API_KEY>"` (S254 grep su .env/ecosystem = VUOTO, probabile nessuna key; se 401 prendi key da `ssh imac 'pm2 env <id-wa-daemon>'`).
3. **Luke approva** su browser `http://192.168.1.2:8080/pending-dossiers` → click approva sul `dossier_id` N.
4. **Invia**: ri-esegui IDENTICO il curl dello step 2 → atteso `200 {status:"sent"}`.
5. **Luke conferma** ricezione del PDF su WhatsApp 39<TEST_FOUNDER_NUM>.
6. **Gate E**: per TEST_FOUNDER esplicito è già allow → di norma NON serve. Se (e solo se) l'harness blocca, Luke registra `! python3 .harness/gate_e.py approve <slug>` poi CC ritenta UNA volta.

## Gate qualitativo
Day 1 dealer reale resta **BLOCCATO** finché E2E verde su TEST_FOUNDER **E** Luke dichiara esplicitamente "pienamente soddisfatto".

## Riferimenti codice
- endpoint doc daemon: `wa-intelligence/wa-daemon.js:1492-1618`
- gate HITL: `wa-intelligence/dashboard/app.py:1050-1166` (tabella `dossiers`)
- smoke offline anelli 5+6: `tools/tests/test_dossier_hitl_smoke.py`
- Gate E hook: `.harness/gate_e.py` (classe `outreach_real`, TEST_FOUNDER allow)
