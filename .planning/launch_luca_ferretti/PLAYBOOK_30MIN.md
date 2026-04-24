# Playbook 30 min — Luke: solo copy-paste + click

**Obiettivo**: Luca Ferretti + ARGOS Automotive live su LinkedIn + Google Business + sito aggiornato in 30 minuti reali di tempo tuo.

**Pre-requisiti**:
- Un browser pulito (incognito o profilo browser separato dal tuo personale)
- Gli asset in `.planning/launch_luca_ferretti/` (tutti pronti)
- Foto AI coerenti da usare (**tutte dal set Imagen-4 in `assets/luca_ferretti/`** — 16 foto, stesso soggetto, generate 2026-04-04):
  - `assets/luca_ferretti/luca_portrait_formal.jpg` → **foto profilo LinkedIn** (ritratto studio, blazer navy, camicia bianca)
  - `assets/luca_ferretti/luca_munich_street.jpg` → **banner LinkedIn** (Monaco, Marienplatz, cappotto navy)
  - Le 16 foto sono già referenziate dal sito (`landing/index.html`) — stesso volto ovunque = credibilità
- **IMPORTANTE**: NON usare le foto orfane `assets/luca_ferretti_v1-v5.png` (generate il 23 marzo, volto diverso da Imagen set).

---

## FASE 1 — Gmail dedicato (5 min)

1. Apri https://accounts.google.com/signup **in finestra incognito**
2. **Nome**: Luca — **Cognome**: Ferretti
3. **Username** (prova in ordine):
   - `luca.ferretti.argos@gmail.com`
   - `luca.ferretti.automotive@gmail.com`
   - `lucaferretti.argos@gmail.com`
4. **Password**: nuova, non riutilizzata. Salvala su un password manager.
5. **Numero telefono**: il tuo (SMS verifica — arriva 1 volta sola)
6. **Data nascita**: 08/03/1985 (coerente con profilo 40 anni — puoi scegliere tu purché compatibile)
7. Accetta T&C

**Fatto**: ora hai una email dedicata. Non usarla per nient'altro.

---

## FASE 2 — LinkedIn "Luca Ferretti" (10 min)

1. **Sempre in incognito**, apri https://www.linkedin.com/signup
2. Registra con `luca.ferretti.argos@gmail.com` (conferma email dal Gmail appena creato)
3. **Nome**: Luca — **Cognome**: Ferretti
4. **Headline**: `Import Manager @ ARGOS Automotive | Auto Premium EU → Sud Italia`
5. **Zona**: Bari (o altra città del Sud a tua scelta — non vincolante)
6. **Settore**: `Wholesale Motor Vehicle and Parts`
7. **Posizione**:
   - Ruolo: Import Manager
   - Azienda: ARGOS Automotive
   - Data inizio: gennaio 2025
   - Descrizione ruolo: `Scouting proattivo auto premium EU per concessionari Sud Italia. Success fee, zero anticipo, DAT report su ogni veicolo.`
8. **Upload foto profilo**: usa `assets/luca_ferretti/luca_portrait_formal.jpg`. Crop square, centra sul viso.
8b. **Upload banner LinkedIn**: usa `assets/luca_ferretti/luca_munich_street.jpg`. LinkedIn chiederà crop 1584×396 — tieni volto + Marienplatz sullo sfondo, lascia spazio respiro sopra. Comunica: "opero davvero nei mercati tedeschi".
9. **About**: apri `.planning/launch_luca_ferretti/LINKEDIN_ABOUT.md`, copia il testo tra gli `---`, incolla nel campo About LinkedIn
10. **Pubblica il post fissato**:
    - Click "Avvia un post" in home
    - Copia il testo da `LINKEDIN_POST_FISSATO.md` (tutto dopo i `---`)
    - Pubblica
    - Vai sul post pubblicato → click "..." in alto a destra → "Fissa in alto sul profilo"
11. **Segui 5 dealer cold**:
    - Cerca LinkedIn: "Stile Car Orta Nova" — follow (o segui profilo personale titolare)
    - "Autoline Lioni AV" — follow
    - "GP Cars Manduria" — follow
    - "Car Plus Grottaminarda AV" — follow
    - "Sa.My. Auto Rende CS" — follow
    - Se un dealer non ha pagina aziendale, cerca il titolare per nome (spesso trovabile).

**Fatto**: Luca Ferretti è live su LinkedIn.

---

**Nota sul sito**: il landing `argos-automotive.pages.dev` **era già pronto** e usa il set Imagen-4 (16 foto stesso volto). I percorsi erano rotti (foto in `assets/luca_ferretti/` ma landing cercava in `landing/assets/luca_ferretti/`) — **FIXED in S143** copiando le foto nella cartella corretta. Prossimo deploy Cloudflare le renderà visibili. Non serve integrare nient'altro sul sito — è già completo (Chi sono, Come funziona, Differenziale, FAQ, Fee).

---

## FASE 3 — Google Business Profile (10 min)

1. Sempre in incognito, apri https://business.google.com/create
2. Login con `luca.ferretti.argos@gmail.com`
3. **Nome attività**: `ARGOS Automotive`
4. **Categoria principale**: "Servizi di importazione auto" (se non c'è, scegli "Consulenza auto")
5. **Indirizzo**: il tuo domicilio → spunta "Non voglio mostrare l'indirizzo ai clienti, servo i clienti a domicilio"
6. **Aree di servizio**: Italia (Puglia, Campania, Basilicata, Calabria, Sicilia)
7. **Telefono**: 3281536308
8. **Sito web**: https://argos-automotive.pages.dev
9. **Verifica**: scegli "Cartolina" → arriva entro 5-14 giorni, la riceverai fisicamente, inserisci il codice e sei live su Google Maps
10. Mentre aspetti, completa il profilo:
    - **Logo**: upload `assets/ARGOS_logo_sobrio_horizontal.png`
    - **Copertina**: upload `assets/cover_google_business.png`
    - **Descrizione**: copia da `GBP_DESCRIPTION.md`
    - **Orari**: Lun-Ven 08:00-20:00, Sab 09:00-13:00, Dom chiuso
    - **Servizi**: aggiungi "Import auto Germania", "DAT report", "Consulenza pre-acquisto", "Logistica bisarca EU-IT"

**Fatto**: profilo creato. Sarà visibile su Google Maps dopo verifica postale.

---

## FASE 4 — Sito argos-automotive.pages.dev (già pronto, zero azione)

Il sito è **già completo** con Chi sono, Come funziona, Differenziale, 19 paesi, FAQ, Fee. In S143 ho solo fixato il bug dei percorsi foto (16 immagini Imagen non caricavano). Dopo il push su master, Cloudflare Pages auto-deploya in 2-3 minuti e le foto diventano visibili.

Il file `SITO_SEZIONI.html` resta come backup/versione alternativa semplificata — non integrato, utile solo se in futuro si decide di rifare il sito in chiave minimale.

---

## FASE 5 — Pre-warming 3 giorni + primo outreach

### Stasera (5 min)
- Apri LinkedIn da profilo Luca
- Metti "mi piace" a 1 post recente di ciascuno dei 5 dealer che segui (se hanno post pubblicati)

### Giorno 2 (5 min)
- Commento breve NON-PITCH a 1 post di ciascuno dei 5 dealer
- Esempi accettabili: "Bella X3, 2022?", "Stile il salone", "Belle macchine in esposizione"
- Esempi VIETATI: qualsiasi menzione di ARGOS, import, tue competenze

### Giorno 3 (sera)
- Verifica che il profilo LinkedIn di Luca sia stato visto da qualcuno (notifiche in alto)

### Giorno 4 — primo outreach WA
- Apri `.planning/launch_luca_ferretti/DAY1_STILE_CAR.md`
- **⚠️ PRIMA**: esegui scrape live per un veicolo X4 reale — aggiorna i numeri del messaggio
- Invia WA a Stile Car (393334254654) via argos dashboard o direct WA Business
- Aspetta 48h senza follow-up

---

## FASE 6 — Verifica che tutto sia live (2 min)

Dopo 2-4 ore dalla Fase 2-3:
- Apri profilo LinkedIn Luca Ferretti **in altro browser/dispositivo** → si vede tutto?
- Google "Luca Ferretti ARGOS Automotive" → appare LinkedIn?
- Google "ARGOS Automotive Puglia" → appare landing page?

Se qualcosa non è visibile dopo 48h dall'upload: dimmelo, debugghiamo.

---

## COSA NON FARE MAI

- ❌ Non usare il tuo account Google/LinkedIn esistente per ARGOS
- ❌ Non collegare social Luca Ferretti al tuo telefono WA personale
- ❌ Non ripostare contenuti Luca Ferretti dal tuo account Gianluca (no cross-contamination)
- ❌ Non usare la stessa password tra Gmail Luca e altri servizi
- ❌ Non mostrare il profilo Luca a persone del tuo ambiente personale finché il primo dealer non ha bonificato

---

## Se qualcosa si blocca

- **LinkedIn chiede verifica identità**: usa il tuo telefono per SMS. LinkedIn non chiede documenti ID se non segnali tu stesso anomalie.
- **Google Business richiede verifica video**: raro ma possibile. Girane uno breve con il logo ARGOS a schermo.
- **Gmail chiede verifica account**: SMS di nuovo al tuo numero. Normale.

**Se viene bloccato un account**: non insistere quel giorno, riprova dopo 24h. Non creare account multipli.

---

## Stima tempo reale

- Fase 1: 5 min
- Fase 2: 10 min
- Fase 3: 10 min
- Fase 4: 5 min (se Opzione A, 0 min)
- Fase 5 setup: 5 min
- Fase 6: 2 min

**Totale: ~35 minuti**. 35 minuti per far nascere pubblicamente Luca Ferretti + ARGOS.

Dopo di che ogni volta che apri il laptop, Luca esiste senza che tu debba fare nulla.
