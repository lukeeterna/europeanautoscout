# Session Log — ARGOS (archiviato da CLAUDE.md)

## Lessons Learned

### S98
- DB corrotto per ore senza alert → monitoring obbligatorio
- LLM esaurito senza fallback → cascade 5 livelli
- Cap 3 reply/dealer bloccava test → alzato a 10
- Cron MacBook non gira se in sleep → spostare su iMac
- Due DB con schema diversi → unificare in Sprint 1

### S105
- "Strade perfette tedesche" era FALSO (DE 5.3/7, NL 6.4) → MAI claim senza dati verificati
- Fee nel system prompt → LLM la rigurgita → fee SOLO in template OBJ_2_FEE
- Validatore che logga senza bloccare = inutile → validate() DEVE return BLOCK
- Modelli free non rispettano istruzioni negative → template-first, LLM-second
- Ferrari = mercato controllato con blacklist → MAI proporre
- Maserati perde 72% in 3 anni → MAI proporre

### S129
- Inviati messaggi WA multipli (10:00, 10:05, 10:31) senza warming → comportamento da spam
- batch_generator.py usava framework vecchio → fixato con commit ba00842

### S130
- Framework V3 (CHI+PERCHE'+DOMANDA) ha problemi strutturali:
  "cerco auto premium in Germania" = pitch vietato nel Day 1
  "Ho visto il suo stock" = anchor vuoto, non specifico
  Domanda su interesse servizio = alza la guardia del dealer
- Pipeline E2E mai completata end-to-end neanche una volta
- Architettura enterprise costruita prima che il ciclo base funzionasse

### S131
- Mega-skill-ombrello ("carica per qualsiasi task ARGOS") ricrea il problema del CLAUDE.md pesante
- Principio corretto: se serve sempre → CLAUDE.md | se serve a volte → skill con trigger specifici
- Contraddizione Day 1 risolta: citare auto specifica del dealer = OK, dichiarare cosa fa Luca = VIETATO

## Failure Modes — Evitare SEMPRE
- Contare listing senza verificare qualita' dati
- Costruire componenti nuovi senza collegare quelli esistenti
- Deploy con scp singoli file (usare rsync)
- Test manuali "rispondi dal telefono" (usare dry_run)
- Ignorare errori LLM/DB senza alert
- `verdict` invece di `recommendation`
- `created_at` invece di `analyzed_at`
- Tono startup nei messaggi dealer (usare tono B2B tradizionale)
- Regressioni silenziose (cio' che funzionava DEVE continuare a funzionare)
- Description skill con "qualsiasi" o "tutto" → si carica sempre → stesso problema di CLAUDE.md pesante
