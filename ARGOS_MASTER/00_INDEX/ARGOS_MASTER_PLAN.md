# ARGOS — MASTER PLAN END-TO-END
> Versione: 2026-06-01 · Stato: SOURCE-OF-TRUTH del sistema completo
> Sostituisce e ingloba gli handoff parziali precedenti (incl. HANDOFF 2026-05-30 sullo scraping Marche).
> Da incollare/aprire all'inizio di OGNI sessione nuova. Se una sessione contraddice questo file, vince questo file salvo decisione esplicita di Luke.

---

## REGOLE DEL TAVOLO (chi fa cosa)
- **Luke (Gianluca Di Stasi)** = autorità del modello. Idea, sì/no su azioni irreversibili.
- **CC (Claude Code)** = esecutore tecnico sul Mac. Pieno accesso filesystem/git/deploy. È l'autorità sui path reali e sullo stato del codice.
- **Claude AI** (questa sessione) = giudice/researcher esterno. NON tocca il filesystem. Critica, valida con evidenza, monta strategia e documenti.
- Memoria di Claude AI = ipotesi fallibile. Lo stato vero del codice lo dà CC.

---

## COS'È ARGOS IN UNA FRASE
Un motore che **arma un micro-operatore senza stock** dandogli (1) autorità di mercato verso clienti altospendenti tramite contenuti, e (2) capacità di reperire l'auto premium UE giusta su richiesta — incassando una **fee a deal chiuso pagata dal dealer**, protetta dal fatto che il dealer non può scavalcare ARGOS senza la fonte dell'auto.

---

## IL SISTEMA A 5 FASI (end-to-end)

### FASE 1 — ACQUISIZIONE DEALER (automatizzata, per territorio)
- ARGOS contatta micro-operatori per **regione → provincia → città** italiana.
- Leva centrale: **SCARSITÀ / ESCLUSIVITÀ TERRITORIALE**. "Un solo dealer (1-2) per zona/segmento."
- La scarsità fa doppio lavoro:
  - verso il dealer: urgenza a entrare prima del rivale di zona;
  - verso il cliente del dealer: il dealer diventa "l'unico in città che trova premium su richiesta" = status.
- Questo strato è automatizzabile perché è outbound strutturato, **non** è la relazione di fiducia col cliente finale.
- **CHI CONTATTA: il SALES AGENT (automatizzato), NON il founder.** Il contatto dealer è gestito da un sales agent che parte già con una **KB pre-addestrata** (persona "Luca Ferretti", persone-dealer, obiezioni→risposte, leve di scarsità — vedi 03_ASSET_VALIDATI). Luke NON chiama i dealer a mano.
- **VALIDAZIONE: via TEST CAMPIONE del sales agent**, non via chiamate-founder. Si lancia il sales agent su un campione di dealer e si misura la conversione reale (ricevono richieste premium? cederebbero la fee?). Il gate si supera sui risultati del campione, non su telefonate manuali. Vedi GATE-CAMPO in 05.
- ⚠ STATO: il pitch di scarsità è VALIDATO come strategia (vedi 03_ASSET_VALIDATI), ma la CONVERSIONE reale del sales agent sui dealer NON è ancora validata. Il test campione serve a quello.

### FASE 2 — ISTRUZIONE/ONBOARDING DEALER (area dedicata)
- Il dealer entra in un'area che gli insegna: (a) attrarre clientela altospendente, (b) vendere auto high-ticket.
- Strumento operativo: **contenuti pronti** (reel, caption, guide, post-testimonianza) che il dealer pubblica **a suo nome** su social / WhatsApp / altro.
- Principio non negoziabile: **AI nel back-end, MAI nel front-end del lusso.** L'AI genera, l'umano (dealer) firma e pubblica. L'AI-slop nel front-end del lusso è punito.
- Mix contenuti validato (vedi 03): walkaround nuovi arrivi, consegne/testimonianze, educativo/guide, comunità-locale. Il dealer esegue, non crea.

### FASE 3 — RICHIESTA CLIENTE → SOURCING (il cuore del prodotto)
- Il cliente altospendente chiede un'auto al dealer.
- ARGOS la cerca su **100+ portali europei** selezionati con logica precisa → restituisce **l'auto migliore**: miglior prezzo + migliori caratteristiche + massima affidabilità.
- Sourcing tecnico già scoperto fattibile a costo zero: AutoScout24 con `?source=DE` restituisce `__NEXT_DATA__` JSON con lo stock tedesco, da IP italiano. (Vedi 04_STATO_TECNICO.)
- Scoring/verifica: motore CoVe v4 in produzione (Bayesian Si = μ − λ·σ, λ=0.25; soglie DEALER_PREMIUM=0.75, VIN_CHECK=0.60; fraud flags). Branding pubblico: Protocollo ARGOS™ / CERTIFICATO™. MAI esporre CoVe/Claude/Anthropic al dealer.

### FASE 4 — ACCOMPAGNAMENTO IMPORT + CERTIFICATO
- ARGOS segue il processo di importazione.
- Genera il **documento/certificato** che attesta i parametri dell'auto (numerosi e affidabili — set di 47 parametri, 10 chiave già definiti; vedi 03).
- Questo certificato è il deliverable che giustifica la fee.

### FASE 5 — PAGAMENTO FEE (trigger delle automazioni)
- Alla generazione del certificato, **il dealer paga la fee**.
- Può pagarla perché ha già incassato **l'acconto dal cliente** che ha commissionato l'auto.
- **Tutti i flussi di pagamento vanno controllati.** Solo a pagamento confermato, partono le automazioni a valle (rilascio fonte/posizione auto + step import).
- LOCK-IN economico: il dealer cresce con ARGOS e non ne può più fare a meno → **meno transazioni, più margine per transazione.** Non gli conviene più vendere la Fiat Punto.

---

## IL NODO DEL PAGAMENTO (perché il dealer non scavalca) — CRITICO
Il dealer NON può prendere il certificato e fare il deal da solo, perché:
1. **Posizione/fonte secretata** (leva primaria, la più forte): il certificato mostra l'auto e i parametri, ma NON dove si trova né chi la vende. Solo a **fee pagata** il dealer riceve posizione + fonte. Senza, non sa dove andare a prenderla.
2. **Sanitizer anti-reverse-image (leva secondaria)**: le immagini nel certificato sono modificate per NON essere ritrovabili con reverse-image-search (Google Images ecc.). Se le foto originali del listing non sono complete/HD, ARGOS le richiede in automatico e le tratta per renderle non rintracciabili.

⚠ Vedi 04_STATO_TECNICO per lo stato REALE del sanitizer (non è "fatto", è codice con bug noto sul plate-detection). Non scrivere mai questa fase come completata finché CC non la verifica.

---

## MONETIZZAZIONE (stato attuale del modello)
- **Fee a deal chiuso, pagata dal DEALER** (il dealer è il cliente pagante), agganciata alla generazione del certificato e protetta dalla secretazione-fonte.
- Range fee storicamente discusso: €800 (€400 in pilota). DA RICONFERMARE con Luke nel modello attuale.
- **Fatturazione = FUORI SCOPE di ARGOS.** Luke emette la fattura della fee al dealer a mano, col proprio gestionale personale, che NON si collega ad ARGOS. Il sistema non gestisce, non genera e non tocca la fatturazione. Nessun componente ARGOS deve assumere integrazione col gestionale.

---

## VINCOLI NON NEGOZIABILI (VOS)
- **G-NOAPI-AI**: Claude AI solo via prompt di sessione che Luke incolla. Zero API key.
- **G-APPROVAL**: sì/no via CLI nativa di CC. Mai bypass via Telegram o env-var silenziosa.
- **0-cost**: solo abbonamento (~€240/mese). Nessun servizio a pagamento aggiunto senza decisione esplicita.
- Hardware: macOS Big Sur 11.7.10 + iMac 2012 (no AVX2, no Docker). Python 3.13. CC pinnato a v2.1.110.
- Branch dedicato, mai master.
- Branding: mai esporre CoVe/Chain-of-Verification/Claude/Anthropic al dealer. Solo ARGOS™.
- Telegram Chat ID `931063621`: riservato esclusivamente a HITL operativo ARGOS.

---

## INDICE DEI FILE DI QUESTA DIRECTORY
- `00_INDEX/ARGOS_MASTER_PLAN.md` — questo file.
- `00_INDEX/README.md` — come usare la directory + ordine di lettura.
- `01_MODELLO/MODELLO_BUSINESS.md` — economia, monetizzazione, lock-in, segmento target.
- `02_FASI/PIPELINE_5_FASI_DETTAGLIO.md` — ogni fase con input/output/stato/dipendenze.
- `03_ASSET_VALIDATI/PERSONE_DEALER.md` — 5 persone-dealer + matrice di calibrazione.
- `03_ASSET_VALIDATI/OBIEZIONI_RISPOSTE.md` — obiezioni dealer → chiavi di risposta.
- `03_ASSET_VALIDATI/PARAMETRI_CERTIFICATO.md` — i 47 parametri (10 chiave) del certificato.
- `03_ASSET_VALIDATI/INTELLIGENCE_DEALER.md` — dove parlano/si trovano i dealer italiani.
- `03_ASSET_VALIDATI/SCARSITA_CONTENUTI.md` — modello scarsità + strategia contenuti validata.
- `04_STATO_TECNICO/STATO_COMPONENTI.md` — cosa è REALE vs da fare (sourcing, sanitizer, scraper, CoVe).
- `05_RISCHI_GATE/RISCHI_E_GATE.md` — rischi aperti + gate di validazione.

---

## ORDINE DI BUILD RACCOMANDATO (raccomandazione singola motivata)
1. **Costruire il SALES AGENT con KB pre-addestrata** e validarlo con un **TEST CAMPIONE** su un set di dealer PRIMA di scalarlo a tutto il territorio. Misura sul campione: (a) i dealer ricevono richieste premium reali, (b) cederebbero la fee. Il founder NON contatta a mano. Senza il test campione, scalare l'agent a tappeto è codice/outreach a rischio-morte.
2. **Consolidare FASE 3 (sourcing)** in parallelo: è il pezzo più solido tecnicamente (AS24 source=DE) ed è ciò che rende credibile il pitch del sales agent.
3. **Chiudere il NODO PAGAMENTO** (secretazione-fonte + sanitizer) a livello di design e poi di codice — è ciò che protegge il ricavo.
4. **FASE 4 certificato** sopra il sourcing consolidato.
5. **FASE 5 controllo pagamenti + automazioni a valle.**
6. **FASE 2 onboarding/contenuti** può procedere in parallelo perché è il "gratis" che apre la porta in Fase 1.
> Motivo dell'ordine: si valida il pezzo non-provato (conversione del sales agent) sul campione più piccolo prima di scalare l'outreach a tappeto; si costruisce prima il valore (sourcing) che rende vero il pitch; si protegge il ricavo (nodo pagamento) prima di scalare.
