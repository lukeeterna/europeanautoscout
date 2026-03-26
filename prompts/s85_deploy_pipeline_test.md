# S85 — Deploy Pipeline + Test End-to-End

## Contesto
S84 ha costruito il pipeline orchestrator completo (7 stati, 4 gate, 4 wave).
Tutto funziona in dry-run. Mai testato con dati reali (email, SMTP, enricher live).

## Obiettivi S85

### 1. Deploy dashboard su iMac
```bash
ssh gianlucadistasi@192.168.1.2
cd /path/to/project
git pull
pm2 restart argos-dashboard
# Verificare: http://192.168.1.2:8080/vehicles
```

### 2. Gmail App Password
- Creare app password per ferretti.argosautomotive@gmail.com
- Salvare in .env come ARGOS_EMAIL_PASSWORD
- Testare: python3 src/cove/seller_contact.py fresh_84aec3405b5d --dry-run

### 3. Fresh scrape con filtro margine
Il BMW X3 target ha margine EUR 699 — troppo basso (Gate 3 blocca < 2.500).
Serve fresh scrape con:
- Modelli: BMW X3/X5, Mercedes GLC/GLE, Audi Q5
- Prezzo EU: EUR 20.000-35.000 (margine IT piu' alto)
- Fonte: AS24 DE + NL (prezzi piu' bassi)
- Obiettivo: trovare 3-5 veicoli con margine >= EUR 3.500

### 4. Test pipeline REALE
```bash
# Setup cron
0 */4 * * * cd /path && ARGOS_DB_PATH=dealer_network.sqlite python3 src/cove/pipeline_orchestrator.py >> logs/pipeline.log 2>&1

# Run manuale
ARGOS_DB_PATH=dealer_network.sqlite python3 src/cove/pipeline_orchestrator.py
```

### 5. Primo contatto venditore EU
- Pipeline porta listing ENRICHED → email discovery → SLIM email EN
- Monitorare risposte (IMAP o manuale)
- Se risponde: richiedere foto + dati → aggiornare DB → generare PDF

## File critici
```
src/cove/pipeline_orchestrator.py    # Orchestratore principale
src/cove/pipeline_states.py          # Stati + gate
src/cove/dealer_matcher.py           # Matching + freshness
src/cove/image_sanitizer.py          # Blur targa/dealer
src/cove/seller_email_discovery.py   # Trova email venditore
src/cove/seller_contact.py           # Email slim + follow-up + IMAP
wa-intelligence/dashboard/app.py     # Dashboard con /vehicles
.planning/phases/05-pipeline-orchestrator/RESEARCH.md  # Deep research flow ottimale
```

## Regole
- ZERO source nelle immagini (blur targa + dealer frame)
- Margine minimo EUR 2.500 per Gate 3
- Email slim al primo contatto (VIN + disponibilita'), foto nel follow-up
- Inglese per tutti i venditori EU
- cove_engine_v4.py NON MODIFICARE
