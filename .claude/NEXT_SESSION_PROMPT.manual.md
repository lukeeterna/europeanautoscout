# S220 — Fisco blindato: commit lavoro accumulato (secret blocker) + wording materiali + delivery

## STATO CHIUSO S219 (context 61%)

### ✅ Fatto
1. **Verifica fiscale fossato import — FATTA DA ME (non "incolla Gemini")**. Agent `research-fact-checker` + 2 WebFetch su fonti primarie (Euroconference, Studio Pizzano, AdE, Gazzetta). 6/6 claim CONFIRMED. Memory `s218_fossato_servizio_import_research.md` aggiornata.
   - **Correzioni fattuali a S218**: codice tributo NON 6099 (=saldo IVA annuale) → veicoli UE = **6201-6212 mensili / 6231-6234 trimestrali** (ris. AdE 337/E/2007). Pagamento dealer-dealer = **F24 elementi identificativi vincolato al telaio, preliminare immatricolazione**, poi riconciliato in liquidazione (NON "integrazione invece di F24").
   - Auto "usata" IVA = ENTRAMBE >6.000km E >6 mesi (art.38 DL331/93); manca una → "nuova" 22% IT sempre.
2. **Commit dirty 2/3 fatti puliti**:
   - `5bd5c63` gitignore hardening — `dossiers/` intera (130MB, 424 file: PDF dealer+foto AS24 copyright+PII) ora ignorata → **fixa root cause dirty 100% sessioni**. + `*_qr_code.png`/captcha/`.DS_Store`/screenshot. + untrack `.pyc`.
   - `1bf984d` rimozione 64 prompts/ legacy + STATE/CURRENT_SPRINT → riorg .planning.

### ⛔ Commit 3 BLOCCATO (next session priorità)
`feat: lavoro accumulato S180-S218` → **hook pre-commit: "Possible hardcoded secret detected"**. C'è un secret hardcoded in uno dei ~245 file untracked (src/tools/tests/landing/research). NON committato (corretto). Working tree = 250 entry, intatto.
- **STEP S220-1**: trovare il secret. `git add -A && git diff --cached | grep -iE 'key|token|secret|password|api[_-]?key|sk-|AKIA'` oppure leggere lo script hook in `.claude/hooks/` per capire il pattern che ha matchato. Rimuovere/spostare in .env, poi committare il resto.

## WORDING MATERIALI (sbloccato — fisco verificato)
- ❌ MAI: "gestisco/assolvo io l'IVA", "ti tolgo problema IVA", "immatricolo io/faccio le pratiche" (abusivo L.264/1991 €2.582–10.329 se non studio autorizzato).
- ✅ OK: "individuo e ti propongo l'auto UE; **resti TU acquirente e soggetto fiscale**; coordino agenzie pratiche autorizzate + fornitori; **paghi solo a risultato**" (mandato CON rappresentanza art.1704).
- ✅ distinguere sempre **regime margine** (no IVA detraibile) vs **IVA esposta** (reverse charge).
- Landing `landing/index.html` oggi dice l'opposto (Step03 :523, FAQ :588, card :476, fee :597 = "import a parte/gestisci tu") → da riconciliare. NON toccare in chiusura context, sessione fresca.

## NUOVA IDEA LUKE (S219) — orchestrazione CONSEGNA auto
Luke: "possiamo gestire la consegna — scrapiamo le migliori soluzioni trasporto più economiche per il dealer. Dobbiamo essere il miglior servizio."
- **Fattibile + già seminato in S218**: broker trasporto bisarca scrapeable (Clicktrans, Macingo) €350-900/auto. Rientra nel fossato "ufficio acquisti estero" SENZA rischio fiscale (trasporto ≠ IVA).
- **STEP S220-2 (scope, decidere con Luke)**: definire MVP scraper preventivi trasporto DE→IT (Clicktrans/Macingo) + integrazione nel dossier/quote dealer. NON costruire a freddo: prima validare quali portali espongono preventivi pubblici scrapeable.

## Day 1 Stile Car — blocker invariati
C-SAN-001 (sanitizer, TinEye manuale Luke su /tmp/s217_revtest/ pending), C-E2E-ZERO, C-COMM-INTEL-001 (materiali, ora sbloccabile lato fisco), C-GATE-FONTE-001.

## NON toccare
image_sanitizer.py / codice produzione. landing/PDF/messaggi finché materiali non riscritti+rivisti.
