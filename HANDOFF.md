# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session 58 — 2026-03-16

---

## ⚡ STATO CORRENTE (S58 — 2026-03-16)

| Sistema | Stato | Note |
|---------|-------|------|
| Dataset v2 | ✅ | 1.319 conv totali — 2.7MB |
| SVM Classifier v1 (TF-IDF) | ✅ | 79.6% CV — in produzione |
| SVM Classifier v2 (sentence-transformers) | ❌ 66.3% | TF-IDF vince (76.5%) — non sostituire |
| **Pipeline Salerno 8 dealer** | ✅ | Loader pronto, 5 con WA mobile |
| **WA Day 1 Variante A** | ✅ approvata | Messaggio neutro universale |
| **Response Analyzer v2** | ✅ riscritto S58 | 20/20 test, zero Ollama, 10 archetipi |
| **WA Business** | ✅ ATTIVO | Numero 328-1536308, su telefono personale |
| **send_message.js generico** | ✅ | Session argos-business |
| **auth_business.js** | ✅ | QR per WA Business |
| **Comando /outreach** | ✅ | In telegram-handler.py |
| .env + .gitignore | ✅ | Credenziali VOIP + Telegram |
| Mario Orefice | ❌ ELIMINATO | Non ha risposto — zero tempo su lead silenti |

---

## 🔴 DECISIONI STRATEGICHE S58

**Mario eliminato**: "Non ce ne frega, abbiamo l'Italia" — zero follow-up su chi non risponde.
**VOIP Ehiweb**: WA Business su 0972536918 — attivazione in corso.
**Variante A per tutti**: archetipo ignoto → messaggio neutro con hook €7-10k.
**Sentence-transformers**: Track B, script pronto, da eseguire quando install completata.
**Stasera il sistema deve contattare dealer veri**: tutto pronto lato code.

---

## 🗺️ ROADMAP 3 TRACK (aggiornata S58)

```
         S58 ✅              S59                S60+
TRACK A  8 dealer pronti──WA Business attivo──invio Day1──risposte──DEAL
TRACK B  script v2 pronto──train+compare──se >85% → produzione
TRACK C  (dopo primi invii) SMTP + template email per archetipo
```

---

### TRACK A — Salerno → Contatto reale → Deal

**S58 ✅ COMPLETATO:**
- Scouting completo: 8 dealer provincia Salerno con profilo full
- WA Day 1 Variante A approvata (messaggio neutro, hook €7-10k)
- Response analyzer v2: 20/20 test, gestisce tutti 10 archetipi, zero Ollama
- Pipeline loader: `python3 tools/salerno_pipeline_loader.py`
- send_message.js generico con session argos-business
- auth_business.js per QR WA Business
- Comando Telegram /outreach per invio Day 1
- .env con credenziali VOIP + .gitignore

**S59 — PROSSIMA SESSIONE:**
- WA Business attivo su 0972536918 → QR scan su iMac (`node auth_business.js`)
- Caricare pipeline: `python3 tools/salerno_pipeline_loader.py`
- Deploy su iMac: copiare send_message.js + auth_business.js + response-analyzer.py aggiornato
- Invio Day 1: `/outreach SALERNO_001` (Autovanny) e `/outreach SALERNO_002` (FC Luxury)
- Prima risposta reale → archetipo confermato → calibra follow-up
- Se sentence-transformers >85% → retrain con v2

**S60+:**
- Trattativa → sourcing EU → deal (anche in perdita = valida modello)

**Pipeline Salerno (8 dealer):**

| ID | Dealer | Città | Stock | Score | WA | Archetipo |
|----|--------|-------|-------|-------|-----|-----------|
| SALERNO_001 | Autovanny Group | Eboli | 58 | 8.5/10 | 335-5250129 ✅ | NARCISO |
| SALERNO_002 | FC Luxury Car Center | S.Egidio MA | 27 | 8.0/10 | 342-5036799 ✅ | BARONE |
| SALERNO_003 | Ferrauto Srl | S.V.Torio | 68 | 8.0/10 | 081-5187350 📞 | BARONE |
| SALERNO_004 | A.B. Motors | Montecorvino P. | 49 | 7.5/10 | 335-6418105 ✅ | RELAZIONALE |
| SALERNO_005 | Auto Genova | Salerno | 117 | 7.0/10 | 329-4357882 ✅ | RAGIONIERE |
| SALERNO_006 | Autoluce Srl | Baronissi | 26 | 7.0/10 | 089-953608 📞 | BARONE |
| SALERNO_007 | Tirrenia Auto | Cava de' Tirreni | 51 | 7.0/10 | 089-2962937 📞 | DELEGATORE |
| SALERNO_008 | Gruppo Emme | Battipaglia | 53 | 6.5/10 | 347-6832587 ✅ | TECNICO |

✅ = WA mobile verificato (invio diretto), 📞 = solo fisso (serve numero mobile)
Ordine invio: SALERNO_001, SALERNO_002, SALERNO_004, SALERNO_005, SALERNO_008

---

### TRACK B — Sentence-Transformers (pronto per test)

Script: `src/marketing/train_svm_v2_sentence.py`
Model: `paraphrase-multilingual-MiniLM-L12-v2` (420MB, offline, IT nativo)
Dipendenze: sentence-transformers + torch (install in corso S58)
**TESTATO S58: TF-IDF 76.5% vs sentence-transformers 66.3% → TF-IDF VINCE**
Sentence-transformers perde 10pp — servirebbero 5k+ conversazioni.
TF-IDF resta in produzione. Rivalutare quando dataset >5.000 conv.

---

### TRACK C — Email backup (dopo primi invii)

SMTP + template per archetipo. Da implementare S60+.

---

## 📋 LEAD PIPELINE BATCH 1 (IN ATTESA — dopo validazione Salerno)

| # | Dealer | Città | Archetipo | WA | Priority |
|---|--------|-------|-----------|-----|----------|
| 1 | Mazzilli Auto | Gravina (BA) | PERFORMANTE | 335 766 2842 | ★★★★★ |
| 2 | Prime Cars Italy | Mascalucia (CT) | TECNICO | 371 417 5649 | ★★★★★ |
| 3 | Campania Sport Car | Melito (NA) | RAGIONIERE | 328 7078112 | ★★★★☆ |
| 4 | Autosannino | Ponticelli (NA) | BARONE | 370 7125777 | ★★★☆☆ |
| 5 | Magicar | Palermo (PA) | NARCISO | 333 8358858 | ★★★☆☆ |

---

## 🏛️ IDENTITÀ E BUSINESS MODEL

**Brand**: ARGOS Automotive | **Persona**: Luca Ferretti
**Business**: B2B vehicle scouting EU→IT | **Fee**: €800-1.200 success-fee
**Target**: Concessionari family-business Sud Italia, 30-80 auto
**Mercati**: DE/BE/NL/AT/FR/SE/CZ | **Veicoli**: BMW/Mercedes/Audi 2018-2023

**Talk track**: "I trader nascondono €7-10k nel prezzo. Noi: €1.000 fisso, tu scegli, DAT+DEKRA inclusi."

---

## 🧠 ARCHITETTURA ENTERPRISE DEFINITIVA (immutabile)

```
Claude (training) → Dataset 1.000 conv → SVM (TF-IDF o sentence-transf) → produzione locale
```

Zero API in produzione. Claude serve SOLO per il dataset.

---

## 📂 FILE CRITICI

```
CoVe Engine:           src/cove/cove_engine_v4.py              ← NON modificare MAI
Classifier v1 TF-IDF:  src/marketing/train_svm_classifier.py
Classifier v2 SentT:   src/marketing/train_svm_v2_sentence.py  ← NUOVO S58
SVM model v1:          data/models/argos_svm_classifier.pkl
SVM model v2:          data/models/argos_svm_v2_sentence.pkl    ← DA TRAINARE
Hard test:             tools/hard_test_svm.py
Pipeline loader:       tools/salerno_pipeline_loader.py          ← NUOVO S58
Response analyzer:     wa-intelligence/response-analyzer.py      ← RISCRITTO S58
Telegram handler:      wa-intelligence/telegram-handler.py       ← AGGIORNATO S58
WA sender:             ~/Documents/app-antigravity-auto/wa-sender/send_message.js ← NUOVO S58
WA auth:               ~/Documents/app-antigravity-auto/wa-sender/auth_business.js ← NUOVO S58
Dataset v2:            data/training/conversations_synthetic_v2.json
MCP config:            .mcp.json                                ← TENERLO VUOTO
.env:                  .env                                     ← VOIP + Telegram
```

---

## 🔴 REGOLE CRITICHE IMMUTABILI

```
Archetipi (10): RAGIONIERE|BARONE|PERFORMANTE|NARCISO|TECNICO|
                RELAZIONALE|CONSERVATORE|DELEGATORE|OPPORTUNISTA|VISIONARIO
OBJ (5):        OBJ-1=fornitori | OBJ-2=prezzo | OBJ-3=tempo | OBJ-4=garanzie | OBJ-5=socio
CoVe:           recommendation (MAI verdict) | threshold 0.75/0.60
MCP:            .mcp.json SEMPRE VUOTO
Fee:            €1.000 (MAI €400) | MAI "non possiamo fatturare" → "bonifico più efficiente"
IVA:            regime margine = moat competitivo ARGOS, non problema
Dataset:        Claude genera → SVM trained → zero API in produzione (IMMUTABILE)
MAI:            CoVe/RAG/Claude/Anthropic/embedding nei messaggi dealer
MAI:            "CarFax EU" → "report DAT" / "DAT Fahrzeughistorie"
MAI:            "Händlergarantie" → "garanzia costruttore UE"
MAI:            "Vincario" → "report DAT"
Lead silenti:   NON fare follow-up — passare al prossimo dealer
```

---

## 🚀 PROSSIMA SESSIONE (S59) — PROMPT COMPLETO

```
Sessione 59 — ARGOS Invio Day 1 Salerno + Sentence-Transformers Test.
Leggi HANDOFF.md prima di qualsiasi altra azione.
Sei CTO AI di ARGOS Automotive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STASERA IL SISTEMA CONTATTA DEALER VERI.
8 dealer Salerno pronti. Variante A approvata.
Response analyzer riscritto S58 — 20/20 test.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIORITY 0 — Collegare WA Business all'iMac (ESEGUI SUBITO)
  WA Business ATTIVO su 328-1536308.
  Ora serve collegare a whatsapp-web.js sull'iMac:
    1. ssh gianlucadistasi@192.168.1.12
    2. Copiare file aggiornati dal MacBook:
       scp wa-intelligence/response-analyzer.py gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-intelligence/
       scp wa-intelligence/telegram-handler.py gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-intelligence/
       scp wa-intelligence/ecosystem.config.js gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-intelligence/
       scp ~/Documents/app-antigravity-auto/wa-sender/send_message.js gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-sender/
       scp ~/Documents/app-antigravity-auto/wa-sender/auth_business.js gianlucadistasi@192.168.1.12:~/Documents/app-antigravity-auto/wa-sender/
    3. cd ~/Documents/app-antigravity-auto/wa-sender/
    4. node auth_business.js → QR appare nel terminale
    5. AZIONE UMANA: WA Business → Dispositivi collegati → Collega → Scansiona QR
    6. python3 ~/Documents/combaretrovamiauto-enterprise/tools/salerno_pipeline_loader.py
    7. pm2 restart all
    8. /outreach SALERNO_001 (Autovanny — score 8.5/10)
    9. /outreach SALERNO_002 (FC Luxury — score 8.0/10)
    10. Aspetta risposte → il sistema gestisce con Telegram approval

PRIORITY 1 — Sentence-Transformers: CHIUSO
  Testato S58: TF-IDF 76.5% vs sent-transf 66.3% → TF-IDF RESTA
  Non toccare il classifier. Focus su conversazioni reali.

PRIORITY 2 — Prima risposta reale
  Quando un dealer risponde:
    - wa-daemon.js riceve → response-analyzer.py classifica
    - Telegram ti mostra messaggio + risposta suggerita
    - /approva o /modifica → invio con anti-ban sleep
    - Nota l'archetipo REALE vs ipotesi → calibra

Fine S59: HANDOFF + MEMORY + commit
```
