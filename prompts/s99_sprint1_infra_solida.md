# S99 — Sprint 1: Infra Solida

## Contesto

S98 ha prodotto la deep research architetturale (`research/s98_ARCHITETTURA_DEFINITIVA.md`).
Pipeline fermata. Zero codice finche' infra non e' solida. Zero dealer reali finche' test E2E non passano.

## PREREQUISITO: Leggere prima

```
research/s98_ARCHITETTURA_DEFINITIVA.md   ← Architettura completa
```

## Obiettivo Sprint 1

Un deploy che non rompe, un DB che non si corrompe, alert se qualcosa va storto.

## Task ordinati

### 1. Schema DB unificato
- Creare schema migration in `src/db.py`
- Merge tabelle `conversations` (daemon) + `dealers` (CRM) → schema unico
- Testare: entrambi Node e Python leggono/scrivono senza errori
- WAL mode + busy_timeout=10000 su entrambi

### 2. Deploy atomico
- Creare `deploy/sync.sh` (rsync + symlink swap)
- `.env` fuori dalle release, symlinked
- `deploy/restart.sh` (restart daemon con PATH corretto per pm2)
- `deploy/healthcheck.sh` (curl status + DB integrity + LLM test)
- Fix IP 192.168.1.12 → 192.168.1.2 in deploy.sh

### 3. Backup DB automatico
- Cron iMac ogni 6h: `sqlite3 $DB ".backup ..."`
- Mantieni ultimi 20 backup
- MAI usare `cp` su SQLite

### 4. Monitoring → Telegram
- Ogni 5 minuti verifica:
  - WA daemon connected
  - DB integrity_check OK
  - Almeno 1 LLM provider funzionante
- Se fallisce → Telegram alert immediato
- WAL checkpoint ogni 30 minuti

### 5. Verifiche finali
- Deploy da MacBook → iMac funziona
- Daemon si riavvia senza errori
- DB integrity OK dopo restart
- Alert Telegram arriva se forzo un errore

## NON fare in questo sprint
- Nessun outreach dealer
- Nessun nuovo script send_*.py
- Nessun refactoring LLM (quello e' Sprint 2)
- Nessuna UI/landing

## Decisioni da confermare col founder
1. iMac e' Apple Silicon o Intel?
2. Dashboard (app.py): serve o deprecare?
