# ARGOS — PIPELINE 5 FASI (dettaglio operativo)
> Supporto a 00_INDEX/ARGOS_MASTER_PLAN.md
> Per ogni fase: cosa entra, cosa esce, da cosa dipende, stato.

---

## FASE 1 — ACQUISIZIONE DEALER
- **Input**: lista micro-operatori per territorio (regione→provincia→città).
- **Chi contatta**: il **SALES AGENT automatizzato** con KB pre-addestrata (persona Luca Ferretti + persone-dealer + obiezioni + leve scarsità). **NON il founder.** Luke non chiama a mano.
- **Processo**: outbound strutturato del sales agent con leva scarsità/esclusività territoriale.
- **Output**: dealer agganciato che entra in onboarding (Fase 2).
- **Dipende da**: il sales agent + la sua KB (vedi 03), lista prospect (recuperabile a mano dai portali; lo scraper NON è il modo giusto per questo — vedi 04). Pitch di scarsità (validato come strategia).
- **Validazione**: TEST CAMPIONE del sales agent su un sottoinsieme di dealer → si misura conversione reale. NON chiamate-founder. → GATE-CAMPO (05).
- **Stato**: pitch validato come strategia; il sales agent e la sua conversione NON sono validati. Il test campione serve a quello.
- **Asset pronti per la KB**: PERSONE_DEALER.md, OBIEZIONI_RISPOSTE.md, SCARSITA_CONTENUTI.md, INTELLIGENCE_DEALER.md.

## FASE 2 — ONBOARDING / CONTENUTI
- **Input**: dealer agganciato.
- **Processo**: area dedicata che istruisce il dealer; ARGOS genera contenuti (reel, caption, guide, testimonianze) tarati su premium + zona.
- **Output**: dealer che pubblica a suo nome → attrae clientela altospendente → genera richieste.
- **Dipende da**: motore di generazione contenuti (AI back-end). Mix contenuti validato.
- **Regola ferrea**: AI nel back-end, l'umano firma. Niente AI-slop nel front-end del lusso.
- **Stato**: pipeline contenuti esiste in altra forma (FLUXION build_video.py per altri verticali); per ARGOS è da tarare. Verificare con CC.

## FASE 3 — RICHIESTA CLIENTE → SOURCING
- **Input**: richiesta auto dal cliente altospendente (via dealer): modello, anno, km, budget, optional.
- **Processo**: ricerca su 100+ portali EU con logica di selezione → scoring CoVe v4 → fraud flags → ranking.
- **Output**: shortlist auto candidate (miglior prezzo/caratteristiche/affidabilità).
- **Dipende da**: accesso portali (AS24 source=DE confermato a costo zero; altri portali da mappare), motore scoring CoVe v4 (in produzione).
- **Stato**: pezzo PIÙ SOLIDO tecnicamente. Sourcing AS24 fattibile. "100+ portali" è target, non stato: mappati realmente molti meno. Vedi 04.

## FASE 4 — ACCOMPAGNAMENTO IMPORT + CERTIFICATO
- **Input**: auto selezionata.
- **Processo**: ARGOS accompagna l'import; genera il certificato con i parametri (47, di cui 10 chiave).
- **Output**: CERTIFICATO™/Protocollo ARGOS™ — SENZA posizione/fonte, con immagini sanitizzate.
- **Dipende da**: set parametri (PARAMETRI_CERTIFICATO.md), sanitizer immagini (stato reale in 04), template certificato.
- **Stato**: parametri definiti; sanitizer = codice con bug noto (plate-detection). NON dare per fatto.

## FASE 5 — PAGAMENTO FEE + AUTOMAZIONI
- **Input**: certificato generato + dealer che ha incassato acconto dal cliente.
- **Processo**: dealer paga fee → **controllo flusso pagamento** → a conferma, rilascio posizione/fonte auto + avvio step import a valle.
- **Output**: deal sbloccato, fee incassata, automazioni partite.
- **Dipende da**: stack pagamento controllato (riferimento allo stack FLUXION: Stripe/Worker, webhook idempotenza, ecc. — verificare cosa è riusabile per ARGOS con CC), gating del rilascio-fonte sul pagamento.
- **Stato**: da costruire. È il punto che protegge il ricavo: il gating "fonte solo post-pagamento" deve essere a prova di scavalco.

---

## DIPENDENZE CRITICHE TRA FASI
- Fase 1 NON va scalata a tappeto prima del GATE-CAMPO (test campione del sales agent). Scalare l'outreach prima di validare la conversione = outreach a rischio-morte.
- Fase 3 abilita la credibilità di Fase 1 (il pitch del sales agent è vero solo se il sourcing funziona).
- Fase 5 (gating pagamento) protegge il valore generato in 3+4. Se il gating è debole, tutto il resto perde senso economico.
