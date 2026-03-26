# S85 — Transport Validation + PDF Fix + Target Alignment

## Contesto
S84 ha costruito pipeline completo (7 stati, dashboard, sanitizer, seller contact).
Founder ha chiarito: il target ARGOS NON e' il grande concessionario strutturato.
E' il PICCOLO dealer che compra 1 auto alla volta su commissione del cliente.

## Priorita' S85

### 1. Validare transport_estimator.py
Il modulo esiste gia': `tools/transport_estimator.py`
- Analizzarlo, capire cosa calcola
- Verificare che copra il caso d'uso: 1 auto, DE→Sud Italia
- Due opzioni per il dealer: ritiro personale (volo+guida) vs trasportatore singolo
- MAI bisarca nel dossier — il nostro dealer non compra 10 auto alla volta

### 2. Aggiornare PDF generator
- Rimuovere "bisarca" dal dossier
- Mostrare 2 opzioni trasporto:
  - Opzione A: Ritiro personale (volo A/R + carburante + pedaggi + 1 giorno)
  - Opzione B: Trasportatore singolo (preventivo stimato EUR X)
- Trip calculator integrato con dati reali (volo Ryanair, pedaggi AT+IT, carburante)

### 3. Object detection per targhe (futuro)
- Il sanitizer attuale copre 80% dei casi (posizioni fisse)
- Per il 20% rimanente serve YOLO o simile (modello open-source, zero costi)
- Per ora: controllo manuale dalla dashboard prima dell'invio

### 4. Allineamento target nel CLAUDE.md
- Aggiornare sezione target: 10-30 auto, commissione, NON strutturato
- Tutto il linguaggio dossier/messaggi deve riflettere questo profilo

### 5. Deep research completata
- research/s84_transport_options_deep_research.md — 5 opzioni analizzate
- Treno auto DE→IT NON esiste (DB Autozug chiuso 2016)
- Dealer italiani: 70% trasportatore, 30% ritiro personale
- Trip calculator ARGOS gia' nel progetto — validare e aggiornare

### 6. Deploy e test su iMac
- Dashboard /vehicles funzionante con bottone "Genera PDF"
- rsync per aggiornare i file
- Test generazione PDF on-the-fly dalla dashboard

## File critici
```
tools/transport_estimator.py           # DA VALIDARE — trip calculator esistente
tools/scripts/pdf_generator_enterprise.py  # DA FIXARE — rimuovere bisarca
src/cove/image_sanitizer.py           # Fixato — crop chirurgico, no blur invasivo
research/s84_transport_options_deep_research.md  # Deep research trasporto
```
