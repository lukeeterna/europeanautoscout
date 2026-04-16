# S127 — human-first-outreach: Phase 1 Architecture

## Contesto (da S126 — 2026-04-16)

### Punto di partenza

Il founder porta un **output da discutere** sulla skill `human-first-outreach`.
S127 inizia da quella discussione, poi procede con Phase 1 Architecture.

### Skill da costruire

`human-first-outreach` — genera il messaggio WhatsApp Day 1 per dealer italiani.
Approccio: signal-anchored (trigger pubblico verificabile) + human-first (peer-to-peer, domanda aperta, zero pitch).

Handoff completo: `/Users/macbook/Downloads/HANDOFF_human-first-outreach_skill.md`

### Decisioni già prese (G1-G6 — CTO)

- **G1:** `opt_out INTEGER DEFAULT 0` → aggiungo a tabella `conversations`
- **G2:** validation_log + LIA → SQLite `dealer_network.sqlite` (DuckDB resta CoVe-only)
- **G3:** 2 endpoint daemon: `GET /validate/rate` + `GET /validate/dealer/:id` → skill chiama via SSH curl con X-API-Key
- **G4:** Signal anchor = AutoScout24 listing update (fallback: Google Business review < 2 sett.)
- **G5:** Opt-out: `"Se preferisce non sentirmi, basta dirmelo."` — riga prima firma
- **G6:** Top 8 archetipi + NEUTRO fallback (RAGIONIERE, BARONE, RELAZIONALE, CONSERVATORE, PERFORMANTE, NARCISO, TECNICO, DELEGATORE)

### Phase 0 findings (già fatto, non ripetere)

- DB outreach = SQLite `dealer_network.sqlite` su iMac (`/Users/gianlucadistasi/Documents/app-antigravity-auto/`)
- `conversations` table: ha persona_type, last_contact_at, outbound_count — MANCA `opt_out`
- 10 archetipi in `data/training/archetypes_v2.json`
- `validator.py` + `outbound_guard.py` già esistono in `wa-intelligence/`
- `/send` payload: `{"phone":"...","message":"...","dealer_id":"..."}`

---

## Agenda S127

### Step 1 — Discussione output founder
Il founder ha un output da condividere sulla skill. Discutere, allineare, integrare nelle decisioni architetturali.

### Step 2 — Phase 1: ARCHITECTURE.md (proposta, no codice)

Produrre documento `ARCHITECTURE.md` da approvare con:

**Tree completo:**
```
.claude/skills/human-first-outreach/
├── SKILL.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── references/
│   ├── archetypes.md          ← da data/training/archetypes_v2.json
│   ├── brand-guardrails.md
│   ├── compliance-lia.md
│   ├── signal-taxonomy.md
│   └── gotchas.md
├── assets/
│   ├── day1_templates.jsonl
│   ├── banned_phrases.txt
│   └── banned_patterns.regex
├── scripts/
│   ├── check_window.py
│   ├── check_rate_limit.py    ← chiama GET /validate/rate via SSH
│   ├── dedup_check.py         ← chiama GET /validate/dealer/:id via SSH
│   ├── log_lia.py
│   ├── validate_message.py    ← orchestrator
│   ├── telemetry.py
│   ├── sync_to_personal.sh
│   └── test_validator.py      ← ≥20 casi pytest
├── examples/
│   ├── stile_car_narciso_good.md
│   ├── stile_car_narciso_bad.md
│   └── archetype_routing.md
└── sql/
    ├── 001_validation_log.sql
    ├── 002_lia_log.sql
    └── 003_opt_out_migration.sql   ← ALTER TABLE conversations ADD opt_out
```

**Catalogo rule_id completo** (HARD/SOFT, layer, fires_on)

**Contratti funzioni principali** (signature, input/output types, side effects)

### Step 3 — Check-in approvazione (STOP obbligatorio)
Aspettare go founder su ARCHITECTURE.md + rule_id prima di Phase 2.

### Step 4 — Phase 2 Execute (se approvato in S127)
Nell'ordine: SQL schema → check_window.py → check_rate_limit.py → dedup_check.py → log_lia.py → validate_message.py → test_validator.py → daemon endpoints → SKILL.md (per ultimo)

---

## File da leggere all'inizio sessione

```
HANDOFF.md                                              ← stato S126
memory/MEMORY.md                                        ← decisioni G1-G6
/Users/macbook/Downloads/HANDOFF_human-first-outreach_skill.md  ← handoff completo
data/training/archetypes_v2.json                        ← 10 archetipi
wa-intelligence/validator.py                            ← validator esistente
wa-intelligence/wa-daemon.js                            ← interfaccia daemon (line 50+)
```

## Stato sistema

- WA daemon: online (`wa_status: connected`)
- iMac: online e raggiungibile via SSH
- Dealer pipeline: NESSUN contatto. Day 1 approccio ancora da definire (human-first pivot)
- Nessun commit in S126
