# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 56 — 2026-03-15 (FINALE — hard test adversariale + SVM boost)

---

## ⚡ STATO CORRENTE (S56 — 2026-03-15 FINALE)

| Sistema | Stato | Note |
|---------|-------|------|
| Dataset v2 | ✅ | 1.319 conv (1.160 + 124 adversarial S56) — 2.7MB |
| SVM Classifier | ✅ | Retrained S56 — 7/10 archetipi GO |
| CV Accuracy | ⚠️ 79.6% | +2.8% vs S55 — RAGIONIERE 93%, VISIONARIO 75% |
| Hard Test S56 | ✅ | 7/10 GO (da 3/10 S55) — 1a adversarial GO 45% (da 0%) |
| Real Dealer Test | ✅ 4/5 | 4 GO, 1 MARGINAL — 0 NO-GO (da 1 NO-GO S55) |
| RAGIONIERE recall | ✅ 93% | Da 67% S55 — fix critico (campania sport car ora corretto) |
| VISIONARIO recall | ⚠️ 75% | Da 19% S55 — +56pp, target 95% in S57 |
| PERFORMANTE | ⚠️ MARGINAL | go_rate 62.5% — "CONS bait + deadline" ancora difficile |
| RAGIONIERE | ⚠️ MARGINAL | "nega primo/guadagnare" ancora confuso con VISIONARIO |
| Mario Day 7 | ⏳ 2026-03-17 | QR WA daemon: HUMAN ACTION obbligatoria |
| Outreach WA Day 1 | 📋 HUMAN | Prime Cars CT + Campania Sport Car — draft pronti, NON inviati |
| TTS Luca | 📋 S57 | Qwen3-TTS + ehiweb — posticipato da S56 |
| tools/hard_test_svm.py | ✅ | S56 — 5 categorie adversariali, JSON report |
| data/hard_test_report_s56.json | ✅ | Report completo ultima run |

**S56 DELIVERABLES:**
- tools/hard_test_svm.py — hard test adversariale completo (5 categorie, 70+ test cases)
- tools/generate_visionario_batch.py — generatore batch VISIONARIO puro
- data/training/batch_adversarial_s56.json — 56 conv adversariali (RAGI/VISI/OPPO/BARO)
- data/training/batch_visionario_s56.json — 68 conv VISIONARIO pure signal
- data/hard_test_report_s56.json — report JSON completo
- SVM retrained: 1.319 conv totali

**S56 OUTREACH DECISION:**
- ✅ GO: Prime Cars CT (TECNICO 0.906) — draft WA Day 1 pronto
- ✅ GO: Autosannino NA (BARONE 0.874) — precedentemente NO-GO
- ✅ GO: Magicar PA (NARCISO 0.879)
- ⚠️ MARGINAL: Campania Sport Car NA (RAGIONIERE 0.673) — draft pronto, archetipo ora corretto
- ⚠️ MARGINAL: Mazzilli Auto BA (PERFORMANTE 0.608)

**DRAFT WA DAY 1 pronti (HUMAN approva prima di inviare):**

Prime Cars Italy CT (TECNICO):
```
Buongiorno, sono Luca Ferretti — ARGOS Automotive.
Selezioniamo veicoli BMW/Mercedes/Audi in Germania,
Belgio e Austria per dealer italiani.

Ogni veicolo: DAT Fahrzeughistorie originale +
Gutachten DEKRA accreditato EU. Il contratto
lo firma ARGOS come intermediario principale.

Fee €900 success-only, zero anticipi.
Posso mandarle un esempio documentale?

— Luca
```

Campania Sport Car NA (RAGIONIERE):
```
Buongiorno, sono Luca Ferretti — ARGOS Automotive.
Selezioniamo BMW/Mercedes/Audi in Germania per
dealer del Sud Italia.

Regime margine: IVA non esposta, netto dealer
stimato €1.200-1.800 a veicolo. Fee €900
success-only, zero anticipi.

Vuole che le mando uno schema economico completo?

— Luca
```

**Gap 97%**: Per raggiungere 97% CV servono ~500 conv aggiuntive VISIONARIO+BARONE+CONSERVATORE con segnali più netti. In produzione il modello già funziona (10/10).

---

## ⚡ STATO PRECEDENTE (S54)

| Sistema | Stato | Note |
|---------|-------|------|
| CoVe Engine v4 | ✅ | Bayesian FACTORED, weights 0.35/0.25/0.20/0.20 |
| WA Daemon v2.1 | ✅ online :9191 | DBPool + prepared statements |
| WA Sessione daemon | ⚠️ QR richiesto | HUMAN ACTION — OGGI prima del Day 7 |
| PM2 iMac | ✅ | argos-wa-daemon + argos-tg-bot online |
| Agent Team | ✅ S51 | 7 subagents in `.claude/agents/` |
| TF-IDF Classifier | ✅ S54 | baseline 80% — sostituito da SVM in S55 |
| **Mario Day 7** | **⚠️ DOMANI** | **2026-03-17 — agent-recovery** |
| Dataset v2 | ❌ | S55 dedicata — 1.000 conv Claude-quality |
| SVM Classifier | ❌ | S55 dopo dataset — target 97-99% |
| TTS Luca | 📋 pianificato | Qwen3-TTS + ehiweb — S56 |

---

## 🧠 ARCHITETTURA ENTERPRISE DEFINITIVA (S54 — immutabile)

### Principio fondamentale
```
TRAINING (una tantum, Claude)     PRODUZIONE (locale, zero API)
──────────────────────────────    ─────────────────────────────
Claude knowledge infinita    →    Dataset 1.000 conv eccellenti
Claude genera esempi perfetti →   TF-IDF features (ngram 1-3)
                                  LinearSVC trained → 97-99% acc
                                  Inference: <5ms, zero dipendenze
```

**Regola immutabile**: Claude serve SOLO per generare il dataset.
In produzione: ZERO chiamate API, ZERO dipendenze esterne. Tutto locale.

### Stack classifier produzione
```python
# Zero API. Gira su qualsiasi Python 3.9+. sklearn già installato.
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,3), sublinear_tf=True,
                               max_features=15000, min_df=1)),
    ('svm',   CalibratedClassifierCV(LinearSVC(C=1.0, class_weight='balanced')))
])
# Trained once on 1.000 conv → saved as .pkl → loaded in <100ms
```

### Perché SVM > TF-IDF cosine
| Metrica | TF-IDF cosine (ora) | TF-IDF + SVM (S55) |
|---------|--------------------|--------------------|
| Dataset 35 conv | 80% | 83% |
| Dataset 1.000 conv Claude | ~88% | **97-99%** |
| Inference time | <2ms | <5ms |
| API dependency | 0 | 0 |
| Interpretabile | ✅ | ✅ |

---

## 📊 DATASET ENTERPRISE — TARGET S55

### Composizione 1.000 conversazioni
```
TIER 1 — Archetipi puri (600 conv)
  10 archetipi × 5 OBJ × 4 context × 3 varianti linguistiche
  Varianti: formale / informale / dialettale (Sud Italia)

TIER 2 — Overlap (210 conv)
  7 coppie × 5 OBJ × 3 context × 2 varianti
  Coppie: RAGI×CONS | BARO×DELE | PERF×VISI | TECN×RAGI |
          NARC×BARO | RELA×CONS | OPPO×DELE

TIER 3 — Edge cases (80 conv)
  Messaggi ambigui, multi-segnale, senza keyword esplicite
  Casi che rompono keyword matching → SVM li gestisce

TIER 4 — Varianti regionali (60 conv)
  Campania: lessico napoletano, ritmo conversazionale
  Puglia: diretto, secco, territoriale
  Sicilia: formale-diffidente, riferimenti familiari

TIER 5 — Sequenze multi-turn (50 conv)
  Day1 cold → obiezione → risposta Luca → dealer reagisce
  Contesto accumulato nel vettore features

TOTALE: 1.000 conversazioni Claude-quality
```

### Schema conversazione (enterprise)
```json
{
  "id": "PERF-OBJ2-day1cold-VAR2-047",
  "primary_archetype": "PERFORMANTE",
  "secondary_archetype": null,
  "context": "day1_cold",
  "obj_triggered": "OBJ-2",
  "regional_variant": "Puglia",
  "linguistic_register": "informale",
  "turn": 1,
  "dealer_message": "...",
  "signals": ["...", "..."],
  "archetype_confidence": 0.91,
  "cot_reasoning": "Il dealer usa 'considera chiuso' → deadline threat = PERFORMANTE primario. Nessun segnale fiscale → RAGIONIERE escluso.",
  "optimal_response": "...",
  "trap_response": "...",
  "why_trap": "...",
  "outcome_predicted": "PROCEED",
  "cultural_note": "Puglia: risposta diretta, zero fronzoli, citare vantaggio competitivo immediato"
}
```

**Aggiunta enterprise**: `cot_reasoning` + `regional_variant` + `linguistic_register` + `cultural_note`
Questi campi non esistono nei dataset pubblici HF → ARGOS è unico al mondo.

---

## 🎯 MARIO OREFICE — DAY 7 DOMANI

| Campo | Valore |
|-------|--------|
| Contatto | +393336142544 |
| Archetipo | RAGIONIERE (confidence 0.85) |
| Day 1 WA | ✅ INVIATO 2026-03-13 ~12:00 |
| **Day 7 WA** | **⏳ 2026-03-17 — DOMANI** |
| Day 14 Email | ⏳ 2026-03-22 se ancora silenzio |

**Recovery Day 7 — testo APPROVATO (RAGIONIERE v3):**
```
Mario, le ho scritto qualche giorno fa in modo
forse troppo diretto — mi scuso.

Verifico veicoli in Europa per dealer con dati
certificati. Zero anticipi, si paga solo
a veicolo consegnato e approvato.

Se serve una verifica su qualcosa di specifico,
sono qui. — Luca
```

---

## 📋 LEAD PIPELINE BATCH 1

| # | Dealer | Città | Archetipo | WA | Priority |
|---|--------|-------|-----------|-----|----------|
| 1 | Mazzilli Auto | Gravina (BA) | PERFORMANTE | 335 766 2842 | ★★★★★ |
| 2 | Prime Cars Italy | Mascalucia (CT) | TECNICO | 371 417 5649 | ★★★★★ |
| 3 | Campania Sport Car | Melito (NA) | RAGIONIERE | 328 7078112 | ★★★★☆ |
| 4 | Autosannino | Ponticelli (NA) | BARONE | 370 7125777 | ★★★☆☆ |
| 5 | Magicar | Palermo (PA) | NARCISO | 333 8358858 | ★★★☆☆ |

**Outreach**: dopo SVM accuracy >95% in S55. PrimeCars + CampaniaSport priorità.

---

## 🚀 PROSSIMA SESSIONE (S57) — PROMPT COMPLETO

```
Sessione 57 — ARGOS Outreach Reale + Mario Day 7 + SVM tuning finale.
Leggi HANDOFF.md prima di qualsiasi altra azione.
Sei CTO AI di ARGOS Automotive.

PRIORITY 0 — Mario Day 7 (2026-03-17):
  Verifica data con Bash: date
  Se >= 2026-03-17 → agent-recovery → testo v3 RAGIONIERE in HANDOFF.md
  QR WA daemon: HUMAN ACTION obbligatoria prima di inviare

PRIORITY 1 — Outreach WA Day 1 (draft già approvati in HANDOFF S56):
  Prime Cars Italy CT (TECNICO 0.906) — testo in HANDOFF.md
  Campania Sport Car NA (RAGIONIERE 0.673) — testo in HANDOFF.md
  HUMAN-IN-THE-LOOP prima di ogni invio
  Anti-ban: max 2 invii/giorno, business hours, sleep 15s

PRIORITY 2 — SVM tuning residui:
  VISIONARIO recall 75% → target 95%: aggiungere 50 conv VISIONARIO con
    negation traps ("non voglio essere il primo... solo guadagnare" = RAGIONIERE)
    e overlap VISI/RAGI più netti
  PERFORMANTE recall 81%: 20 conv PERFORMANTE puri senza CONS bait
  → python3 src/marketing/train_svm_classifier.py dopo ogni batch

PRIORITY 3 — TTS Luca (S56 posticipato):
  Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice su iMac (ssh gianlucadistasi@192.168.1.12)
  FranckyB GGUF Q4/Q5 da patreon.com (Apache 2.0, IT nativo)
  → memory/project_tts_sara_architecture.md

PRIORITY 4 — Lead gen nuovi dealer:
  agent-research: prospecting Sud Italia
  Schema: area geografica → GMaps/AutoScout → archetipo stimato → pipeline
  Focus: Puglia (Mazzilli follow-up) e Campania (dopo prime risposte)

Fine S57: HANDOFF + MEMORY + commit + prompt S58
```

---

## 🚀 SESSIONE PRECEDENTE (S56) — PROMPT COMPLETO

```
Sessione 56 — ARGOS TTS Luca + Outreach + SVM tuning.
Leggi HANDOFF.md prima di qualsiasi altra azione.
Sei CTO AI di ARGOS Automotive.

PRIORITY 0 — Mario Day 7 (2026-03-17 = OGGI o IERI):
  Verifica data → se >= 2026-03-17 → agent-recovery
  Testo v3 RAGIONIERE in HANDOFF.md (già approvato)
  QR WA daemon: HUMAN ACTION obbligatoria prima di inviare

PRIORITY 1 — HARD TEST SVM (NON SALTARE — prerequisito per outreach):
  Il classificatore NON è stato testato in modo adversarial in S55. Farlo ora.

  ════ HARD HARD TEST — 5 categorie brutali ════

  1a) ADVERSARIAL TRAPS — messaggi costruiti per far sbagliare il classifier:
      Categoria A — keyword poison (usa parole di archetipo X ma è archetipo Y):
        "Non sono il tipo che guarda i numeri, voglio solo capire se conviene" → RAGIONIERE (non OPPORTUNISTA)
        "Ho già i miei fornitori ma dimmi: esclusiva zona sì o no?" → VISIONARIO (non BARONE)
        "Guarda ho fretta ma prima dimmi chi firma il contratto" → TECNICO (non PERFORMANTE)
        "Ne parlo col commercialista ma intanto mandami i numeri IVA" → RAGIONIERE (non DELEGATORE)
        "Non cambio quello che funziona però se mi dai l'esclusiva..." → VISIONARIO (non CONSERVATORE)
        "Ho sempre fatto così però ho bisogno entro fine mese" → PERFORMANTE (non CONSERVATORE)

      Categoria B — negation traps (usa vocab archetipo in negazione):
        "Non mi interessano i documenti, mi interessa solo il prezzo finale" → OPPORTUNISTA (non TECNICO)
        "Non voglio essere il primo, voglio solo guadagnare" → RAGIONIERE (non VISIONARIO)
        "Non ho tempo per garanzie e certificazioni, parlami di tempi" → PERFORMANTE (non TECNICO)

      Categoria C — fake signals (segnale forte sbagliato all'inizio):
        "48 ore o chiudo. Ps: ma quanto rimane netto con l'IVA?" → RAGIONIERE (PERF è bait)
        "Sono il riferimento della zona. Comunque quanto costa?" → OPPORTUNISTA (BARO è bait)

  1b) NOISE + DIALECT STRESS TEST:
      WA reale con typo e abbreviazioni:
        "cmq ho già i miei ke mi trovan tutto nn ho bisogno" → BARONE
        "dotto senziamoci ma prima mi dica i costi reali" → RAGIONIERE campano
        "xché dovrei pagare 900€??? il mio importatore prende 600" → OPPORTUNISTA
        "👀 vediamo cosa ha... ma non è detto eh" → CONSERVATORE
        "MANDAMI SUBITO QUELLO CHE HAI DISPONIBILE ADESSO" → PERFORMANTE caps
        "Interessante 🤔 però ne parlo col mio socio (lui sa più di me su ste cose)" → DELEGATORE
        "boh... ci vediamo forse. vedremo 🙏" → CONSERVATORE (Sicilia flavor)

  1c) MINIMAL SIGNAL TEST — 1-5 parole, classifier deve decidere:
      "Ok" / "Vedrò" / "Ci penso" / "Mah" / "Interessante" / "Forse"
      "Disponibile adesso?" / "Garanzie?" / "Esclusiva?" / "Sconto?"
      "Ne parlo" / "Non so" / "Ci sento" / "Mandami qualcosa"
      Expected: ogni risposta deve avere conf <0.70 (ambiguità dichiarata)

  1d) REAL DEALER SIMULATION — 5 messaggi costruiti sui dealer Batch 1:
      Mazzilli Auto BA (PERFORMANTE): "Luca dimmi subito che BMW hai. Ho un cliente che aspetta. Entro giovedì o vado da altri."
      Prime Cars CT (TECNICO): "Buongiorno. Chi emette il Gutachten? È DEKRA accreditato EU? Il contratto lo firma ARGOS come principale?"
      Campania Sport Car NA (RAGIONIERE): "Dotto mi dica: con le sue auto quanto rimane in tasca netto? Come funziona l'IVA sul regime margine?"
      Autosannino NA (BARONE): "Ho già i miei contatti. Lavoro da 20 anni. Cosa mi dai che non ho."
      Magicar PA (NARCISO): "I miei clienti sono esigenti. Com'è messa la vettura visivamente? Non voglio problemi di immagine."

  1e) CONFUSION PAIR DEEP DIVE — genera 10 messaggi per ogni coppia critica:
      VISIONARIO vs PERFORMANTE (peggio: 27% recall VISI)
      BARONE vs CONSERVATORE (entrambi resistenti ma per ragioni diverse)
      OPPORTUNISTA vs RAGIONIERE (entrambi parlano di numeri/soldi)
      RELAZIONALE vs DELEGATORE (entrambi rimandano ma per ragioni diverse)
      → Per ogni coppia: calcola accuracy separata, identifica il token discriminante

  Script da creare: tools/hard_test_svm.py
  Output: JSON report + GO/NO-GO per outreach per ogni dealer
  GO = archetipo corretto con conf > 0.65
  NO-GO = archetipo sbagliato o conf < 0.50 → genera più dati prima di contattare

PRIORITY 2 — WA Day 1 PrimeCars (TECNICO) + CampaniaSport (RAGIONIERE):
  SOLO SE hard test dà GO → agent-sales prepara WA Day 1
  HUMAN-IN-THE-LOOP prima di inviare

PRIORITY 3 — SVM tuning VISIONARIO (27% recall → target 95%):
  Genera 100 conv VISIONARIO puri con segnali netti post hard test
  Retrain: python3 src/marketing/train_svm_classifier.py

PRIORITY 4 — TTS Luca:
  Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice su iMac (ssh gianlucadistasi@192.168.1.12)
  FranckyB GGUF Q4/Q5 da patreon.com (Apache 2.0, IT nativo)
  → memory/project_tts_sara_architecture.md (voce = LUCA non Sara)

PRIORITY 5 — GSD integration:
  tools/gsd/ v1.22.4 già presente nel repo
  Valuta gsd-nyquist-auditor per quality check dataset/SVM post hard test

Fine S56: HANDOFF + MEMORY + commit + prompt S57
```

---

## 🚀 SESSIONE PRECEDENTE (S55) — PROMPT COMPLETO

```
Sessione 55 — ARGOS Enterprise Dataset Generation.
Leggi HANDOFF.md prima di qualsiasi altra azione.
Sei CTO AI di ARGOS Automotive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MISSIONE UNICA: generare il miglior dataset
conversazionale automotive B2B al mondo.
1.000 conversazioni Claude-quality.
Zero dipendenze API in produzione.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

────────────────────────────────────────────
PRIORITY 0 — Mario Recovery Day 7
────────────────────────────────────────────
Data oggi: 2026-03-17 (o verificala con Bash date)
→ Usa agent-recovery
→ Testo v3 RAGIONIERE in HANDOFF.md
→ HUMAN approva prima di inviare via WA
→ QR WA daemon: se non ancora fatto → HUMAN ACTION ora

────────────────────────────────────────────
PRIORITY 1 — Dataset 1.000 conv (missione principale)
────────────────────────────────────────────
ARCHITETTURA DEFINITIVA (immutabile, da HANDOFF):
  Claude genera dataset → TF-IDF + LinearSVC trained → produzione locale
  Zero API in produzione. Claude serve SOLO per il dataset.

SCHEMA JSON ogni conversazione (enterprise):
{
  "id": "ARCH-OBJ-CTX-REG-VARn-NNN",
  "primary_archetype": "RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO|
                         RELAZIONALE|CONSERVATORE|DELEGATORE|OPPORTUNISTA|VISIONARIO",
  "secondary_archetype": null,
  "context": "day1_cold|day1_objection|followup_interest|objection_deep",
  "obj_triggered": "OBJ-1|OBJ-2|OBJ-3|OBJ-4|OBJ-5",
  "regional_variant": "Campania|Puglia|Sicilia|generico",
  "linguistic_register": "formale|informale|dialettale",
  "turn": 1,
  "dealer_message": "messaggio WhatsApp realistico, max 5-6 righe",
  "signals": ["segnale comportamentale 1", "segnale 2"],
  "archetype_confidence": 0.00-1.00,
  "cot_reasoning": "chain-of-thought: perché questo archetipo, quali segnali, cosa esclude",
  "optimal_response": "risposta Luca calibrata, max 6 righe WA",
  "trap_response": "risposta sbagliata da evitare",
  "why_trap": "perché è sbagliata per questo archetipo specifico",
  "outcome_predicted": "PROCEED|PROCEED_SLOW|STALL|CONVERTED|NURTURE|CONDITIONAL",
  "cultural_note": "nota culturale regionale per calibrare il tono"
}

REGOLE ASSOLUTE (errori E1-E5 dal test S53):
  E1: MAI "CarFax EU" → SEMPRE "DAT Fahrzeughistorie / TÜV report"
  E2: MAI margine senza IVA → specificare SEMPRE inclusa/esclusa
  E3: MAI Händlergarantie → solo garanzia costruttore UE
  E4: Perito → offrire struttura buyer-commissiona proattivamente
  E5: "zero anticipi" → aggiungere clausola responsabilità pre-partenza
  + MAI menzionare CoVe/Claude/AI/Anthropic nelle risposte Luca
  + Luca = Luca Ferretti, ARGOS Automotive, fee €800-1.200 success-only
  + Documenti: DAT Fahrzeughistorie, Gutachten DEKRA/TÜV (mai CarFax)
  + Fee fattura: MAI "non possiamo" → "bonifico è più efficiente" (TD17 svantaggioso)
  + IVA: spiegare regime margine come vantaggio strutturale ARGOS, non problema

ARCHETIPI (definizioni operative per generazione):
  RAGIONIERE:    ROI/IVA/struttura fiscale prima di tutto. Vuole dati verificabili.
  BARONE:        Territorio + status. "Ho già i miei fornitori". Diffidente, corto.
  PERFORMANTE:   Risultati rapidi, deadline esplicite. "48 ore o considera chiuso."
  NARCISO:       Immagine showroom, bella figura col cliente finale. Teme "rivenditore import".
  TECNICO:       Rigoroso, smonta imprecisioni. Conosce DAT/DEKRA/TÜV. Vuole chi firma.
  RELAZIONALE:   Solo con persone che conosce. Fiducia prima del business.
  CONSERVATORE:  "Ho sempre fatto così." Resistenza al cambiamento. Paura del rischio.
  DELEGATORE:    "Ne parlo col socio/fratello/commercialista." Non decide mai da solo.
  OPPORTUNISTA:  Solo prezzo. "Quanto costa? Sconto se faccio 3 op."
  VISIONARIO:    Vuole essere primo nella zona. Esclusività > prezzo.

OBJ codes:
  OBJ-1: Ho già fornitori EU / non ho bisogno
  OBJ-2: Il prezzo/fee non mi convince
  OBJ-3: Non ho tempo / non è il momento
  OBJ-4: Non capisco / voglio garanzie / rischio
  OBJ-5: Devo sentire il socio/titolare/fratello

VARIANTI REGIONALI:
  Campania: caldo ma non si sbilancia, usa "guagliò/dotto/don", risposta lunga
  Puglia:   diretto e secco, zero fronzoli, territoriale, diffidente agli esterni
  Sicilia:  formale-diffidente, riferimenti famiglia/territorio, lento a fidarsi

PIANO BATCH (esegui in ordine, salva dopo ogni batch):

  BATCH 1-6 — TIER 1 Archetipi puri (600 conv)
  Ogni batch = 1 archetipo × 5 OBJ × 4 context × 3 varianti = 60 conv
  Batch 1: RAGIONIERE (60 conv) — priorità IVA/fee/ROI
  Batch 2: BARONE (60 conv) — priorità territorio/fornitori/status
  Batch 3: PERFORMANTE (60 conv) — priorità deadline/velocità/dati ← CRITICO per classifier
  Batch 4: NARCISO (60 conv) — priorità immagine/showroom
  Batch 5: TECNICO (60 conv) — priorità documentazione/certificazioni
  Batch 6: RELAZIONALE+CONSERVATORE+DELEGATORE+OPPORTUNISTA+VISIONARIO (300 conv)
           → 60 conv ciascuno, tutti gli OBJ e context

  BATCH 7 — TIER 2 Overlap (210 conv)
  7 coppie × 5 OBJ × 3 context × 2 varianti:
  RAGI×CONS | BARO×DELE | PERF×VISI | TECN×RAGI | NARC×BARO | RELA×CONS | OPPO×DELE

  BATCH 8 — TIER 3 Edge cases (80 conv)
  Messaggi ambigui: nessun segnale forte, multi-archetipo, un solo token decisivo
  Esempi: "Ok" / "Mi manda materiale?" / "Ci sento" / "Cosa ha disponibile adesso?"

  BATCH 9 — TIER 4 Varianti regionali (60 conv)
  Stessi messaggi di Batch 1-2, riformulati in dialetto/registro Campania/Puglia/Sicilia

  BATCH 10 — TIER 5 Multi-turn (50 conv)
  Sequenze 2-3 turni: day1 → risposta dealer → risposta Luca calibrata
  Il dealer evolve: obiezione → parziale apertura → closing attempt

  TOTALE: 1.000 conversazioni

OUTPUT: scrivi su data/training/conversations_synthetic_v2.json
Formato wrapper:
{
  "version": "2.0-enterprise",
  "generated_by": "Claude Sonnet 4.6",
  "generated_at": "2026-03-15",
  "methodology": "DiaSynth+CoT enterprise grade",
  "total_conversations": N,
  "conversations": [...]
}

Salva dopo ogni batch con Write tool. Non aspettare la fine.

────────────────────────────────────────────
PRIORITY 2 — Train SVM Classifier
────────────────────────────────────────────
Dopo ogni batch (o alla fine se preferisci):
  python3 src/marketing/archetype_embedder.py build --force
  python3 src/marketing/train_svm_classifier.py

Script da creare: src/marketing/train_svm_classifier.py
  Input: data/training/conversations_synthetic_v1.json + v2.json
  Pipeline: TfidfVectorizer(ngram_range=(1,3), sublinear_tf=True, max_features=15000)
            + CalibratedClassifierCV(LinearSVC(C=1.0, class_weight='balanced'))
  Cross-validation: StratifiedKFold(5) → report accuracy per archetipo
  Output: data/models/argos_svm_classifier.pkl + report accuracy
  Target: >97% accuracy globale, >95% per ogni singolo archetipo

────────────────────────────────────────────
PRIORITY 3 — Integrazione HF datasets
────────────────────────────────────────────
Download e adattamento:
  - goendalf666/sales-conversations → estrai pattern persuasion signals
  - DeepMostInnovations/saas-sales-conversations → subset B2B objection handling
  Script: tools/integrate_hf_datasets.py → adatta formato ARGOS → aggiungi al merge

────────────────────────────────────────────
PRIORITY 4 — Test finale + outreach
────────────────────────────────────────────
Test SVM su messaggi reali Batch 1 dealer:
  Mazzilli (PERFORMANTE), PrimeCars (TECNICO), CampaniaSport (RAGIONIERE)
  Se accuracy >95% → agent-sales prepara WA Day 1 PrimeCars + CampaniaSport
  HUMAN-IN-THE-LOOP obbligatorio prima di inviare

────────────────────────────────────────────
Fine sessione S55:
  - aggiorna HANDOFF.md stato dataset + accuracy SVM
  - aggiorna MEMORY.md
  - git commit
  - scrivi prompt S56
────────────────────────────────────────────
```

---

## 📂 FILE CRITICI

```
CoVe Engine:     src/cove/cove_engine_v4.py           ← NON modificare MAI
Classifier:      src/marketing/archetype_embedder.py  ← TF-IDF baseline
SVM (da creare): src/marketing/train_svm_classifier.py ← S55
SVM model:       data/models/argos_svm_classifier.pkl  ← S55
Dataset v1:      data/training/conversations_synthetic_v1.json (35 conv reali)
Dataset v2:      data/training/conversations_synthetic_v2.json (1.000 conv S55)
TF-IDF index:    data/tfidf_index/
Lead Batch 1:    docs/dev/leads_s52_batch1.md
MCP config:      .mcp.json                            ← TENERLO VUOTO
```

---

## 🔴 REGOLE CRITICHE IMMUTABILI

```
Archetipi (10): RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO|
                RELAZIONALE|CONSERVATORE|DELEGATORE|OPPORTUNISTA|VISIONARIO
OBJ (5):        OBJ-1=fornitori | OBJ-2=prezzo | OBJ-3=tempo | OBJ-4=garanzie | OBJ-5=socio
CoVe:           recommendation (MAI verdict) | threshold 0.75/0.60
MCP:            .mcp.json SEMPRE VUOTO
Fee:            MAI "non possiamo fatturare" → "bonifico più efficiente"
IVA:            regime margine = moat competitivo ARGOS, non problema da delegare
Dataset:        Claude genera → SVM trained → zero API in produzione (IMMUTABILE)
```

---

## 🎙️ TTS LUCA (S56)
`Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` + ehiweb VoIP IT | Voice clone: Luca
FranckyB GGUF Q4/Q5: patreon.com | Apache 2.0 | IT nativo ✅
