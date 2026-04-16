# HANDOFF — ARGOS Automotive / CoVe 2026
**Working dir**: `/Users/macbook/Documents/combaretrovamiauto-enterprise`
**Aggiornato**: Session S126 — 2026-04-16

---

## S126 COMPLETATA — PIVOT HUMAN-FIRST + SKILL ARCHITECTURE PHASE 0

### Cosa è stato fatto

1. **Research Nord/Centro completata** (agente parallelo):
   - File: `.planning/research/s126_research_nord_centro_dealer.md`
   - Nord: non vendono l'ORIGINE, vendono la CERTEZZA. Frame: "veicolo verificato"
   - Centro BO/FI: frame = sicurezza legale. Roma: serve "storia" + continuità
   - Lombardia = mercato #1 premium. Veneto +11.5% crescita.

2. **MVP materiale formativo Stile Car costruito** (`tools/outreach/formativo_stile_car_mvp.md`):
   - 3 pezzi: scheda comunicabile + script WA + post IG
   - **RIFIUTATO dal founder: "sa di spam"**

3. **Feedback critico → pivot strategico:**
   - MAI proporre auto specifica nel Day 1 prima di dialogo
   - Domenico (Stile Car) GIA' fa import EU — zero valore aggiunto nel pitch a freddo
   - Parlare di EUROPA intera, non solo Germania
   - Day 1 = aprire conversazione, non chiudere vendita
   - 3 aperture alternative proposte (A/B/C) — non ancora scelte

4. **Skill `human-first-outreach` — Phase 0 completata:**
   - Handoff da Claude Web: `/Users/macbook/Downloads/HANDOFF_human-first-outreach_skill.md`
   - Schema DB mappato, archetipi letti (10 non 5), validator.py esistente trovato
   - Decisioni G1-G6 prese dal CTO (vedi memory)
   - Founder ha output da discutere → S127 parte da Phase 1 Architecture

### Stato pipeline

- **NESSUN dealer contattato** — approccio Day 1 ancora da definire
- WA daemon: online e connesso (verificato)
- DB iMac: `dealer_network.sqlite` — `conversations` manca `opt_out` (da aggiungere in Phase 2)

---

## S127 DEVE INIZIARE DA

1. **Founder porta il suo output** sulla skill `human-first-outreach`
2. Discussione → allineamento su Phase 1 Architecture
3. Approvazione `ARCHITECTURE.md` + catalogo `rule_id`
4. Solo dopo: Phase 2 Execute (codice)

---

## File chiave S126

```
tools/outreach/formativo_stile_car_mvp.md          ← MVP rifiutato, non inviare
.planning/research/s126_research_nord_centro_dealer.md  ← research Nord/Centro
/Users/macbook/Downloads/HANDOFF_human-first-outreach_skill.md  ← handoff skill
data/training/archetypes_v2.json                   ← 10 archetipi completi
wa-intelligence/validator.py                        ← validator esistente da estendere
```
