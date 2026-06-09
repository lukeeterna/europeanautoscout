# S255 — Chiudere E2E anello 6-7 (invio dossier su TEST_FOUNDER)

**Generato S254**: 2026-06-08 · context chiuso a 66% prima di eseguire l'invio.
Apri fresco col telefono business (393314928901) in mano.

## Stato verificato S254 (wiring E2E COMPLETO — non ri-investigare)

- Daemon iMac: **ONLINE**, `wa_status=connected`, `daily_sent=0/20`, business hours OK.
- Tabella `dossiers` **ESISTE** su `~/Documents/app-antigravity-auto/dealer_network.sqlite` (iMac, 389KB).
- `/send-doc` (`wa-intelligence/wa-daemon.js:1492`) è **DUAL**:
  1. 1ª chiamata con `{phone,file_path,dealer_id}` → auto-registra PENDING → risponde `403 {error:"dossier registered, awaiting Luke approval", dossier_id:N}` + alert Telegram.
  2. Dopo che Luke approva → 2ª chiamata IDENTICA → `approval_status=APPROVED` → **invia** il PDF (`200 {status:"sent"}`).
- Approvazione Luke: dashboard `iMac:8080/pending-dossiers` (click) — preview confinata a `~/Documents/app-antigravity-auto/dossiers/` (`_DOSSIERS_BASE`, app.py:1035).
- Gate E (hook): `/send-doc` al SOLO `393314928901` con numero **esplicito nel comando bash** → ALLOW automatico. **Niente `gate_e approve` manuale** per TEST_FOUNDER. Se il numero NON è esplicito → ramo "no-number" → DENY.
- Il runner `tools/on_demand_runner.py` si ferma a scrape→CoVe→PDF: la registrazione/invio passa SOLO da `/send-doc`, non dal runner. Gap confermato.

## BLOCKER da risolvere PRIMO (unico)

Il PDF è solo su MacBook: `dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf` (2.3MB).
Il daemon fa `fs.existsSync(file_path)` **locale su iMac** → copialo su iMac:

```
scp dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf \
  gianlucadistasi@192.168.1.2:~/Documents/app-antigravity-auto/dossiers/
```

## Sequenza E2E (copia-incolla)

1. **scp PDF** su iMac (sopra).
2. **Registra PENDING** (curl gira SU iMac via ssh, daemon è su localhost:9191; numero esplicito = Gate E allow):
```
ssh gianlucadistasi@192.168.1.2 'curl -s -X POST localhost:9191/send-doc \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"393314928901\",\"file_path\":\"/Users/gianlucadistasi/Documents/app-antigravity-auto/dossiers/ARGOS_BMW_X1_2021_TEST_FOUNDER_20260608_184951.pdf\",\"dealer_id\":\"TEST_FOUNDER\",\"caption\":\"Esempio dossier ARGOS\"}"'
```
   → atteso `403 ... dossier_id:N`. Se `401 unauthorized` → serve header `-H "X-API-Key: <ARGOS_API_KEY>"` (S254 grep su .env/ecosystem = VUOTO, probabile nessuna key; se 401 prendi key da `ssh imac 'pm2 env <id-wa-daemon>'`).
3. **Luke approva** su browser `http://192.168.1.2:8080/pending-dossiers` → click approva sul dossier_id N.
4. **Invia**: ri-esegui IDENTICO il curl dello step 2 → atteso `200 {status:"sent"}`.
5. **Luke conferma** ricezione del PDF su WhatsApp 393314928901.
6. **Gate E**: per TEST_FOUNDER esplicito è già allow → di norma NON serve. Se (e solo se) l'harness blocca, Luke registra `! python3 .harness/gate_e.py approve <slug>` poi CC ritenta.

## Gate qualitativo
Day 1 dealer reale resta **BLOCCATO** finché E2E verde su TEST_FOUNDER **E** Luke dichiara esplicitamente "pienamente soddisfatto".

## Come riprendere (substrato)
1. `cd /Users/macbook/Documents/combaretrovamiauto-enterprise`
2. `bash state/refresh.sh <SESSION_ID>` → ri-deriva stato
3. Leggi `STATE.md` (anelli GENERATI) — questo file è il dettaglio operativo S255, STATE.md è il SoT degli anelli.
