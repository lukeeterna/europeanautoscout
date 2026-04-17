# Skill Description Audit — 2026-04-17 (Sessione S134 safe)

## Esito audit: stato ottimo, 0 skill silenti

| Metrica | Valore |
|---------|--------|
| Skill totali in `.claude/skills/` | 50 |
| Con campo `description` presente | 50 (100%) |
| Con description trigger-rich (match pattern attivazione) | 48 |
| Con description generica (rischio auto-invoke mancato) | 2 |

Best practice Anthropic: la `description` deve contenere **keyword specifiche** che il loader confronta col contesto per decidere se caricare la skill. Description vaghe = skill silente.

---

## 2 skill con description migliorabile

### 1. `.claude/skills/skill-argos-debug/SKILL.md`
- **Name field**: `argos-wa-debug` (mismatch cartella vs name — minor inconsistency)
- Description contiene pattern di attivazione chiari ("Usa SEMPRE questa skill quando", "PRIORITÀ su...") ma non matcha il regex standard del mio audit. Funzionalmente OK.
- **Azione consigliata:** nessuna urgente. Eventualmente uniformare `name: skill-argos-debug` per coerenza col path.

### 2. `.claude/skills/skill-handover/SKILL.md`
- Description: `"Genera handover a fine sessione: aggiorna memory, crea prompt S(N+1), documenta stato"`
- **Problema:** nessun keyword trigger esplicito (es. "quando Luke dice 'fine sessione'", "attiva su handoff", ecc.).
- **Rischio:** potrebbe non auto-attivarsi quando serve.
- **Azione consigliata post-E2E:** aggiungere keyword trigger del tipo:
  ```yaml
  description: >
    Genera handover a fine sessione ARGOS: aggiorna MEMORY.md, crea prompt S(N+1),
    aggiorna HANDOFF.md, commit. Attivare quando Luke dice: "fine sessione",
    "handover", "chiudi sessione", "aggiorna memory", "prepara prossima sessione".
  ```

---

## Distribuzione per categoria (informale)

Dai nomi file rilevati nel sistema:
- **Skill ARGOS-specific** (prefisso `skill-argos*` + trigger mirati): ~20
- **Skill enterprise standard** (marketing, finance, ops, sales): ~30

Coesistono due ecosistemi paralleli — entrambi ben descritti, bassissimo rischio collisione.

---

## Raccomandazione finale

**Nessuna modifica in questa sessione.** Il sistema skill è già in stato di produzione:
- 100% skill descritte
- 96% skill trigger-rich
- 4% (2 skill) migliorabili ma non broken

**Rimandare a Sessione C** (post-E2E, dopo primo dealer reale):
1. Uniformare `name: skill-argos-debug` col path
2. Aggiungere keyword trigger in `skill-handover`
3. Eventuale consolidamento overlap semantico tra ARGOS-specific ed enterprise standard (es. skill-sales-official vs agent-sales)

**Zero azioni ora.** Report-only come da piano.
