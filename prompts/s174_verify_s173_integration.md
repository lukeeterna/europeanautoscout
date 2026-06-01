# S174 ARGOS — Verifica integration S173 PRIMA di nuovo scope (verification-first)

**Sessione precedente**: S173 chiuso VERDE 8/8 in commit `b306c6b` (~88% context al close). MA: chiusura basata su 14 unit test mock (response LLM fabbricate, non reali) + migration mai applicata + iMac mai sync verified. Pattern S160 in versione SW (gate superficie ≠ gate integration).

**Vincolo #11 pattern recognition**: S160 era "import lazy ≠ init reale". S173 è "unit mock ≠ pipeline reale". Stesso anti-pattern famiglia.

**Scope S174**: NO nuovo lavoro. Verify che S173 funziona realmente PRIMA di S175 mystery shopper pilot.

---

## LEGGI PRIMA

- `data/s173_cciaa_target_d28.csv` (33 micro-dealer Sud)
- `migrations/s173_handoff_source.sql` (NON applicata)
- `tests/test_ambra_layer3.py` (14 mock unit test passanti)
- `wa-intelligence/response-analyzer.py` (modificato, top of file line 305-430)
- `wa-intelligence/state_machine.py` (modificato, line 79-160)
- `/Volumes/MontereyT7/venture-os/wiki/projects/ARGOS/AMBRA-AUDIT.md` sez 6 (P3 marcato completed — verificare claim)

---

## 3 GATE INTEGRATION (verification-first, NO new scope)

### Gate G1 — Migration applicata su DB reali (~15min)

Pre-flight check (vincolo #1):
```bash
# Verifica colonne PRE-migration su entrambi i DB
sqlite3 dealer_network.sqlite "PRAGMA table_info(conversations)" | grep -E "handoff_source|is_micro_dealer"
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/argos/dealer_network.sqlite 'PRAGMA table_info(conversations)'" | grep -E "handoff_source|is_micro_dealer"
```

Expected pre-migration: **0 righe** (colonne assenti).

Apply migration su entrambi (MacBook locale + iMac remoto):
```bash
sqlite3 dealer_network.sqlite < migrations/s173_handoff_source.sql
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/argos/dealer_network.sqlite < /dev/stdin" < migrations/s173_handoff_source.sql
```

Post-migration verify:
```bash
sqlite3 dealer_network.sqlite "PRAGMA table_info(conversations)" | grep -E "handoff_source|is_micro_dealer"
ssh gianlucadistasi@192.168.1.2 "sqlite3 ~/argos/dealer_network.sqlite 'PRAGMA table_info(conversations)'" | grep -E "handoff_source|is_micro_dealer"
```

Expected: **2 righe ciascuno** (handoff_source TEXT default 'cold' + is_micro_dealer INTEGER default 0).

**Fail cases**:
- Migration fallisce su iMac (path DB diverso, permission, lock) → debug + applica manualmente con `ALTER TABLE ADD COLUMN`
- DB iMac path diverso da assumption → trova path reale con `ssh imac "find ~ -name dealer_network.sqlite 2>/dev/null"`

### Gate G2 — LLM call reale produce output conforme (~20min)

Smoke test integration con LLM reale (Groq priority — gratis + veloce):

```bash
# Step 1: prepara mock dealer in DB locale con handoff_source='mystery_shopper'
sqlite3 dealer_network.sqlite <<SQL
INSERT OR REPLACE INTO conversations (dealer_id, persona_type, conversation_state, handoff_source, is_micro_dealer)
VALUES ('S174-VERIFY-001', 'DEFAULT', 'CONTACTED', 'mystery_shopper', 1);
SQL

# Step 2: invoke response-analyzer.py direttamente (no wa-daemon)
python3 wa-intelligence/response-analyzer.py \
  --msg-id S174_TEST_001 \
  --msg-body "ah si Argos, il cliente che e' passato da me me ne aveva parlato. che mi propone?" \
  --dealer-id S174-VERIFY-001 \
  --dealer-name "Test Verify S173" \
  --persona DEFAULT \
  --step CONTACTED \
  --db-path dealer_network.sqlite 2>&1 | tee /tmp/s174_g2_output.log

# Step 3: estrai risposta LLM + verifica
grep -E "LLM OK|VALIDATOR|messages" /tmp/s174_g2_output.log
sqlite3 dealer_network.sqlite "SELECT id, body FROM pending_replies WHERE dealer_id='S174-VERIFY-001' ORDER BY id DESC LIMIT 3"
```

**3 check obbligatori sull'output LLM reale**:
1. (a) Identity post-handoff attiva: risposta NON contiene "ho trovato il suo contatto online" (frase cold)
2. (b) Ban "argos" rilassato: risposta PUO' contenere "Argos" senza essere flagged in violations
3. (c) Target lexicon presente se applicabile: ≥1 termine commissione D-28 ("commissione", "su ordine", "non tengo stock") se prompt era cost-related

**Fail cases**:
- LLM ignora identity post-handoff (output sembra cold-contact) → prompt module non sufficiente, iterate wording
- LLM output flagged da validator → check log: se "banned_exact: argos" appare con handoff_source=mystery_shopper, c'è bug nel wire-up validator
- LLM produce TARGET_LEXICON con tutti i 7 termini in 1 risposta → scriptato, vincolo S173 critica strutturale 30gg materializzato

**Cleanup post-test**:
```bash
sqlite3 dealer_network.sqlite "DELETE FROM conversations WHERE dealer_id='S174-VERIFY-001'"
sqlite3 dealer_network.sqlite "DELETE FROM pending_replies WHERE dealer_id='S174-VERIFY-001'"
```

### Gate G3 — iMac sync verified (~10min)

wa-daemon.js su iMac invoca response-analyzer.py via subprocess. Verifica che la versione modificata sia presente lato iMac:

```bash
# Compare hash MacBook vs iMac
md5 wa-intelligence/response-analyzer.py
ssh gianlucadistasi@192.168.1.2 "md5 ~/argos/wa-intelligence/response-analyzer.py"

# Stessa cosa per state_machine.py + argos_knowledge_base.md
md5 wa-intelligence/state_machine.py wa-intelligence/argos_knowledge_base.md
ssh gianlucadistasi@192.168.1.2 "md5 ~/argos/wa-intelligence/state_machine.py ~/argos/wa-intelligence/argos_knowledge_base.md"
```

**Se hash divergono**: deploy con `bash deploy/sync.sh` (rsync atomico, regola security.md). Verifica post-deploy hash matchano.

**Se deploy script non aggiornato** o blocca: rsync manuale ATOMIC:
```bash
rsync -avz --checksum \
  wa-intelligence/response-analyzer.py \
  wa-intelligence/state_machine.py \
  wa-intelligence/argos_knowledge_base.md \
  migrations/s173_handoff_source.sql \
  gianlucadistasi@192.168.1.2:~/argos/wa-intelligence/
```

Post-deploy: PM2 restart wa-daemon NON necessario (response-analyzer.py invocato fresh ogni reply).

---

## CRITERIA GO/NO-GO S174 → S175

- **VERDE** (3/3 gate pass) → S175 mystery shopper Layer 2 pilot fisico (3 dealer da `data/s173_cciaa_target_d28.csv` HIGH ranking)
- **GIALLO** (1-2 gate fail con fix < 30min) → fix in S174 + close VERDE, S175 ok
- **ROSSO** (gate fail strutturale) → handoff S174-bis, S175 deferred, NO mystery shopper finché non verde

**No fishing**: se trovi findings collaterali (es. wa-daemon dup S171 fix non verde) → BACKLOG, NON aprire scope. S174 = solo verify S173.

---

## VINCOLI S174

- **#1 verifica fattuale**: ogni claim "fatto" deve avere log/output reale
- **#3 raccomandazione singola**: no liste decisioni a Luke su tecnica
- **#6 mai PARTIAL**: VERDE/GIALLO/ROSSO chiari, no "ARANCIONE"
- **#7 context budget**: parto basso, /context ogni 5 turn, sopra 60% close
- **#9 mai diplomatico**: se G2 mostra LLM ignora identity post-handoff, dichiarare "S173 retune NON sufficiente" — no soft language
- **#11 pattern recognition**: questo S174 ESISTE perché S173 ha ripetuto pattern S160 (gate superficie ≠ integration). Documentare in feedback memory se G2/G3 falliscono.
- **CLAUDE.md ARGOS**: NO outreach reale, NO TEST_FOUNDER fisico richiesto (S174 è solo backend verify)

---

## OUTPUT ATTESI S174

1. `/tmp/s174_g2_output.log` — full output LLM call reale (Groq/Gemini)
2. Tabella verify hash MacBook vs iMac (3 file)
3. Verdict G1/G2/G3 in commit message
4. Se ROSSO: feedback memory nuova "S173 mock-only validation insufficient" — pattern recognition vincolo #11
5. Aggiornamento `MEMORY.md` con outcome S174

---

## CHIUSURA S174

- VERDE 3/3 → MEMORY entry + commit "S174 verify S173 green" + handoff S175 prompt
- GIALLO 1-2 con fix → MEMORY entry + commit fix incluso
- ROSSO → MEMORY entry + handoff S174-bis prompt con fix path verificato + feedback memory pattern
