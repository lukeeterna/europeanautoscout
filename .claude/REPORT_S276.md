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
Le aggiunte dell'eval al banner ("contaminato / padding EU-wide", "geo-filter location.countryCode", "ADD-1")
**non sono nei dati verificati**: la memoria S273 dice solo **cap-truncated**. NON le ho scritte nel SoT.

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

## 7. Next prompt (resume S277)
```
Leggi .claude/REPORT_S276.md §5 (blocker + risposte Luke a Q1-Q4) + STATE.md §3.
PRIMA di tutto: applica le decisioni di Luke su Q1-Q4. Poi, SE Q3 confermato:
1. response-analyzer.py firma "Luca" → "Assistente di Luca Ferretti" (WA + reply contratto);
   verifica al RENDER, non al grep (lezione S271). Seam: testo WA→assistente, voce/tel→Luca reale.
2. Ritocca copy Day-1 perché atterri caldo (protegge response rate vs ancora identity.md step 1).
3. Commit.
SE Q2 autorizzato: verifica pre-flight sync.sh (symlink wa-sender/) PRIMA del deploy.
Item (a) liceità canale = BLOCKED-ON-LUKE finché Q1 non ha risposta. Nessun invio reale.
```
