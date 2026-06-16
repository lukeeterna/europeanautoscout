# REPORT S276 — Verifica eval STATE.md + riallineamento SoT al leading edge

> Record durevole. SoT di stato = `STATE.md`. Questo è il report di sessione.
> Commit: `bd89a10` (STATE.md riallineato — 3 stale verificati corretti).

## 1. Cosa è stato chiesto
Verificare contro i dati un'eval esterna che sosteneva: *"STATE.md è stale al leading edge —
stessa classe di bug del PDF Frankenstein / pool cappato, applicata al file che dovrebbe prevenirla."*
Metodo: verifica claim-per-claim contro il **file su disco**, non contro il paste dell'eval (vincolo #1/#10).

## 2. Esito verifica — claim per claim

| # | Claim eval | Verdetto | Evidenza (disco) |
|---|------------|----------|------------------|
| **1** | item (b) mostra framing PRE-S275 ("rimuovere eventuale istruzione KB"); **baebe77 non atterrato**; "due sessioni invisibili" | **FALSO** | Righe 124-138 = framing **post-baebe77**: "meccanismo runtime di impersonificazione (NON 'istruzione KB eventuale')", "rimossa in REPO a TUTTI i layer", "chiuso-in-repo ≠ chiuso-in-produzione", "RESIDUO firma". `git log STATE.md` → baebe77 è ancestor di HEAD. L'eval leggeva un **paste vecchio** (versione S274 STEP-0, *prima* dell'edit) |
| **2** | banner S263 ESITO C in cima = stale | **VERO** | righe 10-17 congelavano a ~10 sessioni fa ("S264 proposto" già avvenuto) |
| **3** | header "Aggiornato: S245 · 2026-06-08" stale | **VERO** | riga 8 — ~30 sessioni indietro |
| **4** | Ring 5 non dichiara base-mercato non-fidata | **VERO** (fix in narrativa, NON nel blocco GENERATED — quello è generato da `rings.json`) | tabella anelli traccia la macchina d'invio, non la fondazione-dati |
| **5** | "persona Luca Ferretti DECISI" stale | **PARZIALE** | riga 83 leggeva come impersonificazione blindata, in tensione con §3(b) |

**Meta-punto**: l'eval ha sbagliato il suo claim **più allarmante** (#1) commettendo l'errore esatto da cui
mette in guardia — affermare sull'artefatto senza leggere il file live. Reale = 3-su-5, NON "il SoT è marcio".
~~Le aggiunte dell'eval ("padding EU-wide", "geo-filter location.countryCode", "ADD-1") non sono nei dati verificati~~
**[CORREZIONE post-round — io ho rifatto il #1]**: quei finding SONO verificati su disco in
`REPORT_S273cont3.txt` (geo vero=`location.countryCode` riga 40; `isEuWideCountExperimentActive` riga 120/142;
over-collection 834 righe 42-56; DUE garanzie separate righe 128-129). Ho asserito dal **file-memoria**
(che diceva solo "cap-truncated") invece che dal **report primario** — stesso errore del #1. La memoria
durevole aveva perso un finding load-bearing. **Recuperato S276**: banner STATE.md ora porta entrambe le
garanzie (completezza A/B-OFF + purezza geo==IT); memoria `s273_*` aggiornata.

## 3. Cosa è stato corretto (commit `bd89a10`, locale — push bloccato dal secret in history)
- **header** → `S275 · 2026-06-16`
- **banner S263** → stato sourcing reale S273-cont: pool AS24 **cap-truncated** (>770 reali vs fixture 325,
  cap `DEEP_PAGES=20`); calibrazione su mezzo mercato (330i NO_VERDICT probabilmente CAP, non scarsità);
  **dossier reale BLOCKED** su scrape esaustiva `DEEP_PAGES≥80` fino a pagina vuota. Folda anche #4
  (fondazione-dati ora visibile nella mappa, distinta da "Ring 5 VERIFIED-smoke = il PDF si genera")
- **vincolo persona** → allineato a §3(b): AMBRA = assistente *dichiarata* di Luca reale, non impersonificazione
- Fix meccanico, fatto **folding non headline** — come l'eval stesso chiedeva.

## 4. Stato E2E (anelli) — INVARIATO questa sessione
| # | Anello | Stato |
|---|--------|-------|
| 2 | classifier intent (AMBRA) | VERIFIED (smoke) |
| 9A | approve → send | VERIFIED (smoke) |
| 5 | generazione dossier PDF | VERIFIED (smoke) — ma base-mercato sotto NON fidata (cap-truncated) |
| 1 | invio Day1 WA | UNVERIFIED |
| 9B | reject → abort | UNVERIFIED |
| 6-7 | approve HITL dossier → invio PDF dealer | UNVERIFIED |
| 8 | contract → sign_url | BLOCKED (fatto esterno: firma dealer reale) |

S276 NON ha mosso anelli E2E: ha corretto il **SoT** (control-plane), upstream di tutto.

## 5. BLOCKER APERTI — domande di chiarimento per Luke

> Tutte decisioni di **scope/founder** (non tecniche): legittimo chiederle (vincolo #3 eccezione scope).

### Q1 — (a) Liceità canale primo contatto **[IL BLOCCO REALE]**
Cold WA outbound a freddo in IT = alto rischio GDPR. CC non è un legale. È l'unica cosa tra te e un dealer
reale, parcheggiata di sessione in sessione.
**Domanda**: qual è il path che scegli —
  (i) parere legale professionista + balancing test scritto (sblocca cold WA com'è), oppure
  (ii) riframe del canale su base lecita (follow-up di lead inbound / referral / richiesta esplicita) che
       NON richiede balancing test?
*Senza una di queste, ogni sessione futura resta BLOCKED qui e nessun lavoro tecnico sposta il collo di bottiglia.*

### Q2 — Deploy iMac (chiude (b) in produzione)
La trasparenza è chiusa **in repo**; il daemon live **nega ancora** finché non si fa `bash deploy/sync.sh`.
⚠️ Memoria S252: `sync.sh` as-is non symlinka `wa-sender/` → rischio re-scan QR + release stale.
**Domanda**: autorizzi il deploy ora (con verifica pre-flight del path sync.sh prima di lanciarlo), o lo
teniamo fermo finché (a) non è chiuso (tanto senza (a) non si contatta nessuno comunque)?

### Q3 — Residuo firma "Luca" (S276 next)
`response-analyzer.py` firma ancora "Luca" in 1ª persona su output bot (WA + reply contratto) =
re-impersonificazione dalla firma. Correzione decisa S274 → "Assistente di Luca Ferretti".
**Domanda**: confermi che eseguo nella prossima sessione (firma + ritocco copy Day-1 perché
"Assistente di Luca" atterri caldo senza perdere response rate)? Oppure vuoi vedere prima la copy proposta?

### Q4 — Push / secret in history (tuo task)
Il push resta bloccato: secret live in history branch (S220). Fix = `git filter-repo` (bonifica history) +
rotazione secret.
**Domanda**: vuoi che ti prepari il piano `git filter-repo` step-by-step (lo esegui tu), o lo lasciamo parcheggiato?

## 6. Operativo
- Hook **PostCompact** fallisce (schema invalido: emette `hookSpecificOutput.additionalContext` per un evento
  che lo schema CC non prevede) → gate validazione post-compact non scatta. Fix = spostare in `systemMessage`.
  Non è task di sessione; dimmi se lo sistemo.
- Packet Gate E orfano `.harness/pending_review/overwrite_sot-0a13cfcff3.md` (S275): innocuo, cancellabile.

## 6b. Nome assistente — DECISIONE (Luke "vedi tu") → **AZZURRA**
Opzioni Luke: Azzurra / Ivonne / Mia / Sharon. Scelta **Azzurra**, motivata sui dati di progetto:
- **credibilità Sud Italia** (communication.md step 1): nome chiaramente **italiano** e caldo → riduce il
  sospetto "call-center estero/bot" che *Sharon/Ivonne* (anglo/franco) innescano nel target family-business.
- *Mia* scartato: "sono Mia" = collisione col possessivo italiano (ambiguo nel testo WA).
- *Azzurra* = elegante, memorabile, distintivo, zero pun. Resta **assistente dichiarata** di Luca reale
  (NON impersonificazione): "Sono Azzurra, l'assistente di Luca Ferretti…". `AMBRA` resta nome **interno**
  di sistema/formato, non public-facing.
- ⚠️ Implementazione = stessa superficie del residuo firma (Q3): identity/hard_rules/KB/disclosure/retry
  in `response-analyzer.py`. Si fa **insieme** a Q3 in S277, non in due passate.

## 7. Next prompt (resume S277)
```
Leggi .claude/REPORT_S276.md §5 (risposte Luke Q1-Q4) + §6b (nome) + STATE.md §3 e banner sourcing.

PRIORITA' 0 — RECUPERO cont3 GIA' FATTO S276 in STATE.md banner + memoria topic file s273_*
(commit f46c1d4: completezza A/B-OFF + purezza geo==IT su location.countryCode). RESIDUO UNICO =
riga-indice MEMORY.md (riga 11) ancora "cap-truncated" only → aggiornare a "cap-truncated + geo==IT
+ A/B-experiment-OFF" SOTTO ARGOS_HARNESS_UNLOCK=1 (Gate-E overwrite_sot). Primo step S277.
ADD-1 futura = scrape profonda + geo-filter + experiment-OFF (mai solo "più profonda" = pool falso-pulito).

POI applica Q1-Q4. SE Q3 confermato (bundle con nome AZZURRA):
1. response-analyzer.py: identity/firma "Luca" 1a persona → "Azzurra, assistente di Luca Ferretti"
   (WA + reply contratto). Verifica al RENDER non al grep (lezione S271). Seam: testo WA→Azzurra/assistente,
   voce/tel→Luca reale. AMBRA resta interno.
2. Ritocca copy Day-1 perché atterri caldo + disclosure + provenienza contatto + opt-out
   (= sostrato del balancing test per Q1/(a), NON lavoro parallelo: protegge response rate E serve al legale).
3. Commit.
SE Q2 autorizzato: pre-flight sync.sh (symlink wa-sender/) PRIMA del deploy.
Item (a) liceità canale = CONFERMATO (vedi §8). Nessun invio reale finché 3 gate tecnici verdi.
```

---

## 8. STATO FINALE ROUND — conferme Luke 2026-06-16

### Risolti questo round
- **Q1 (a) liceità canale → CONFERMATO** (commit `14ad7f7`): cold WA outreach AUTORIZZATO, decisione
  founder. **Il blocco a un dealer reale NON è più legale.** Sblocco più importante dell'arco S245→S276.
- **Q3 nome → AZZURRA** (commit `f46c1d4`): assistente *dichiarata* di Luca, italiana/credibile Sud Italia.
  Implementazione bundle con firma in S277.
- **Recupero finding cont3** (commit `f46c1d4`): geo==IT su `location.countryCode` + experiment-OFF
  recuperati in STATE.md banner + memoria. Memoria durevole aveva perso un finding load-bearing.
- **3 stale STATE.md corretti** (commit `bd89a10`): header, banner S263, vincolo persona.

### Avanzamenti E2E
**NESSUN anello E2E mosso questo round.** Lavoro tutto su **control-plane** (SoT/STATE.md) + **gate legale**.
Anelli invariati: 2/9A/5 VERIFIED(smoke) · 1/6-7/9B UNVERIFIED · 8 BLOCKED(esterno).
Il valore del round: ha rimosso il gate che dipendeva da Luke (a) e riallineato il SoT — sblocco
*upstream* di tutta la pipeline, non un avanzamento di anello.

### 3 gate tecnici residui a un invio dealer REALE (tutti miei, nessuno dipende da Luke)
1. **E2E TEST_FOUNDER** verde (anelli 1/6-7/9B) + Luke "pienamente soddisfatto" (gate qualitativo, recidiva-flagged).
2. **Trasparenza in PRODUZIONE**: Azzurra+firma (S277) → `sync.sh` (Q2). Daemon live nega ancora = bloccante per coerenza.
3. **Base-mercato fidata**: scrape esaustivo `DEEP_PAGES≥80` + geo==IT + experiment-OFF (finding cont3).

### CHIARIMENTI CHE MI SERVONO (per partire autonomo in S277)
- **C1 — copy Day-1**: la scrivo e la wiro in S277 *senza tua revisione preventiva* (poi la vedi nell'E2E
  TEST_FOUNDER), oppure vuoi **approvarla prima** che tocchi il runtime? (È anche il sostrato del balancing test.)
- **C2 — Q2 deploy**: autorizzi `sync.sh` in S277 dopo firma+Azzurra (con pre-flight wa-sender/), o lo
  tieni fermo finché l'E2E TEST_FOUNDER non è verde? (Senza deploy il test gira solo in repo/iMac, non live.)
- **C3 — Q4 push**: preparo il piano `git filter-repo` (bonifica secret in history) step-by-step da eseguire
  tu, o resta parcheggiato? (Finché non risolto, ogni commit S277 resta locale, non pushato.)
- **C4 — autonomia S277**: vuoi che proceda fino al gate "pienamente soddisfatto" fermandomi lì (Azzurra
  +firma+copy+E2E TEST_FOUNDER), o uno stop intermedio per tua review?

### Aggiornamenti chiusura (feedback Luke 2026-06-16, post-§8)
- **(a) liceità canale = DECISO-FINALE, INDISCUTIBILE** (Luke CAPS): canale = **WA cold outreach**, nessun
  reframe (l'opzione "(ii) riframe a base inbound" di §5/Q1 è CHIUSA, fuori discussione). Decisione founder.
  CC smette di trattarlo come blocco aperto. NON è più un gate. Restano SOLO i 3 gate tecnici (miei).
- **MEMORY.md riga-indice = PRIORITÀ 0 S277 (correttezza, NON cosmetico)**: l'indice è ciò che una sessione
  futura a corto di budget legge per PRIMA; indice stale "cap-truncated" + topic file fresco = riparte dal
  quadro dimezzato (stratificazione spostata di un livello). NON scivola sotto Q1-Q4. Fix sotto unlock.
- **Confine AMBRA/Azzurra = lavoro reale S277, non refuso**: grep → AMBRA 60× in code/docs/plan
  (`.planning/06-ambra-agent`, PLAN.md, S274, BACKLOG, report). Azzurra = solo testo S276. S277 deve
  DEFINIRE il confine: Azzurra = public-facing (ciò che dice al dealer) · AMBRA = interno (sistema/codice/
  identificatori/plan). Senza confine esplicito = incoerenza nomi load-bearing. Parte del bundle Q3.
