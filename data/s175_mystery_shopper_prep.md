# S175 Mystery shopper Layer 2 — Preparation pack (Luke physical execution)

**Generato**: 2026-05-15 S175 in-session
**Fonte**: `data/s173_cciaa_target_d28.csv` (33 micro-dealer Sud Italia, 15 HIGH)
**Filtro applicato**: ranking_d28=HIGH AND regione IN (Calabria, Puglia)
**Selezione**: 3/8 candidati per copertura geografica + diversità forma giuridica + maximally micro

---

## 3 DEALER HIGH SELEZIONATI

### Dealer #1 — LUCKY CARS S.R.L.S.
- **Località**: San Lucido (CS) — Calabria Nord costa tirrenica
- **Forma**: S.R.L.S. — capitale ridotto, struttura post-2012
- **Fatturato**: 0-1 milioni
- **Profilo D-28**: micro-stock confermato, SRLS = struttura giovane = no eredità marchio
- **Mystery shopper canale**: visita fisica preferibile (Cosenza-area raggiungibile Luke); telefonica fallback
- **Auto plausibile zona**: Calabria costa = preferenza SUV compact (Renegade, 500X, T-Cross) o berline tedesche entry (Serie 1, A3, Classe A) 2019-2022 €15-22k

### Dealer #2 — TONYMOTORS DI FIMOGNARI ANTONIO
- **Località**: Siderno (RC) — Calabria Sud costa ionica
- **Forma**: Ditta individuale — owner = Fimognari Antonio (WA primary atteso)
- **Fatturato**: non pervenuto (proxy: digitalmente silente)
- **Profilo D-28**: ditta personale = single-owner family business = archetipo puro
- **Mystery shopper canale**: telefonica probabile (RC = distanza geografica Luke); preparare scenario phone-first
- **Auto plausibile zona**: Calabria Sud rurale = preferenza auto familiari/utility (Fiat Tipo SW, Dacia Duster, BMW Serie 3 touring) 2018-2021 €13-20k

### Dealer #3 — MOTORS CAR DI SUFIANE ANTARA
- **Località**: Latiano (BR) — Puglia Sud rurale entroterra
- **Forma**: Ditta individuale — owner = Sufiane Antara (WA primary atteso, possibile background nord-africano = mercato segmento specifico)
- **Fatturato**: non pervenuto
- **Profilo D-28**: ditta personale + territorio rurale BR = pattern commissione informale forte
- **Mystery shopper canale**: telefonica o fisica se Luke transita Puglia
- **Auto plausibile zona**: Puglia rurale BR = preferenza utility/lavoro (Fiat Doblò, Ducato, berline media usate) 2017-2020 €10-18k; segmento premium tedesco meno dominante qua

---

## SCRIPT MYSTERY SHOPPER LAYER 2 — RAFFINATO POST-AUTOCRITICA

### Principio guida (post-autocritica vincolo #4)

**NON** entrare con frase Argos-forward. La frase seed `"ho visto online che Argos cerca auto in Germania"` del prompt è strutturalmente fragile:
- Argos non ha presenza online trovabile → cover blown se dealer chiede "che sito"
- 3 mystery shoppers con stessa frase in 30gg = pattern detection (dealer Sud comunicano)
- Scripted opening = innaturale

**Struttura corretta**: cover primario = ricerca auto reale plausibile per Luke (deve poter sostenere conversazione 15-30min senza inventare). Argos = mention secondario CONDIZIONATO a friction.

### Step script per ogni dealer

**STEP 1 — Apertura cover (Luke fisico/voce)**
> "Buongiorno, sto cercando una [MODELLO] del [ANNO] sui [BUDGET]. Mi sono fatto un giro online ma non trovo molto sotto i [BUDGET MAX]. Lei ne ha qualcuna in arrivo o sa dove guardare?"

Luke compila `[MODELLO/ANNO/BUDGET]` plausibile per zona dealer (vedi colonna "Auto plausibile zona" sopra). Vincolo: Luke deve poter sostenere 10min discussione tecnica sul modello scelto (kilometraggio realistico, optional desiderati, motorizzazione preferita).

**STEP 2 — Sondare modello commissione (sense-making naturale)**
Se dealer risponde "non ce l'ho ma posso cercare":
> "Ah ok, come funziona? Lei la trova e me la fa vedere prima?"

Se dealer risponde "non ne arrivano spesso":
> "Capisco. Senta, ma se le do io l'indicazione, lei la cercherebbe?"

**Goal step 2**: registrare lessico spontaneo dealer per:
- Modello operativo: "su ordine" / "su commissione" / "te la cerco" / "la procuro"
- Pricing: "ti faccio sapere quanto" / "ci metto io X" / "il margine mio è Y"
- Time: "10 giorni" / "una settimana" / "subito"

**STEP 3 — Seed Argos CONDIZIONATO (solo se naturalmente innesca)**

Se dealer dice "in Italia non si trovano molto" o "bisogna guardare estero" → opening naturale per seed:
> "Eh, mi avevano detto. Mio cugino [o: un amico] mi ha parlato di un servizio Argos che cerca auto in Germania per i concessionari. Lei lo conosce? O sente nominare?"

Se dealer NON apre porta estero → **NON FORZARE seed**. Skip step 3. Mystery shopper resta cover puro auto-search. Status output = NEUTRAL non REJECTED.

**STEP 4 — Disponibilità futura**
> "Senta, le lascio il numero. Se le capita qualcosa simile mi chiama?"

Registrare: dealer chiede numero? Salva contatto? Promette richiamata? (= proxy interesse commissione)

---

## REGISTRAZIONE GROUND-TRUTH (Luke fuori sessione)

Per ogni dealer, Luke compila in `data/s175_mystery_shopper_outputs.md`:

```markdown
## Dealer [#1|#2|#3] — [NOME]

**Data/ora visita/chiamata**: YYYY-MM-DD HH:MM
**Canale**: visita fisica | telefonica WA | telefonica fissa
**Durata**: X minuti
**Cover auto**: [MODELLO ANNO BUDGET usato]

### Trascrizione/sintesi (5-15 righe)
[Luke scrive sintesi conversazione, marca verbatim dealer in `"virgolette"`]

### Lessico spontaneo dealer (TAG)
- commissione: [parole usate verbatim, es. "te la cerco", "su ordine", "ti procuro"]
- margine: [verbatim, es. "ci metto io 2000", "il mio guadagno"]
- estero: [verbatim, es. "Germania", "fuori", "su"]
- tempo: [verbatim, es. "10 giorni", "appena trovo"]

### Reazione frase Argos (se step 3 attivato)
- Step 3 attivato: SI | NO (se NO, motivo: dealer non ha aperto porta estero)
- Reazione: [risposta verbatim dealer]
- Apertura/chiusura: [valutazione Luke: curioso | neutro | scettico | ostile]

### Disponibilità futura
- Salva contatto Luke: SI | NO
- Promette richiamata: SI | NO
- WA business attivo: SI | NO | non verificato

### STATUS
SEEDED | NEUTRAL | REJECTED

**Justification**:
- SEEDED = dealer ha mostrato curiosità Argos + ha salvato contatto + apertura futura
- NEUTRAL = conversazione cover OK ma seed non attivato (porta estero non aperta) o reazione neutra
- REJECTED = dealer ostile a mention Argos o intermediari estero
```

---

## VINCOLI ESECUZIONE LUKE FISICO

1. **NO mention "ARGOS Automotive"** come brand professionale — usa "Argos" generico come se fosse passaparola informale.
2. **NO mention fee €800-1.200** — non sei venditore, sei cliente curioso.
3. **NO mention persona "Luca Ferretti"** — questo è frontman per Layer 3 AMBRA, NON per mystery shopper Layer 2.
4. **Coerenza persona** — se 2 mystery shopper su 3 dealer geograficamente vicini (CS+RC entrambe Calabria), persona cliente DEVE differire (origine, lavoro, modello cercato) per evitare pattern detection rete dealer.
5. **Recording** — audio se possibile (memo iPhone), altrimenti note immediate post-visita entro 10min (memoria verbatim degrada >30min).

---

## OUTPUT GATE PER RIATTIVAZIONE S175.5 (Claude in sessione)

Luke deve consegnare `data/s175_mystery_shopper_outputs.md` con 3/3 dealer compilati. Allora Claude esegue:
- S175.5 calibration `target_lexicon` module su lessico verbatim raccolto
- S175.5 rerun G2 verify S174 (target_lexicon test passing post-calibration)
- S175.5 add test integration reale `tests/test_ambra_layer3.py` con ground-truth utterance
- S175.6 SQL update `handoff_source='mystery_shopper'` per dealer SEEDED only

---

## CRITERI VERDE/GIALLO/ROSSO S175 (da prompt)

- **VERDE**: ≥2/3 SEEDED + target_lexicon calibrato + ≥1 test integration reale passing → handoff S176 Day 1 AMBRA primo dealer SEEDED
- **GIALLO**: 1/3 SEEDED + lexicon parziale → handoff S176-bis (espandi mystery shopper 5-10 MEDIUM)
- **ROSSO**: 0/3 SEEDED → D-27 strategy invalidata, handoff S176-strat (rivedi 3-layer model)
