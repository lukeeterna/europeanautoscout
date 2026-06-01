# S223 — Verifica anelli #6 + #9 su CODICE REALE (no fix prima della verifica)

## STATO CHIUSO S222
### ✅ Merge branch→master consolidato
- `s210/audit-master-plan` → `master` ESEGUITO (fast-forward pulito). master == branch == origin/master == origin/branch, tutti su `999a755`. Divergenza 0/0.
- 31 commit accumulati S180→S221 ora in master ufficiale GitHub.
- Scan secret pre-merge sul diff: pulito.
- Memory: `s222_merge_master_consolidato.md`.

### Stato reale anelli ARGOS (production_ready=FALSE — gate VOS)
VERIFIED = **1/9** (#1 scrape, 2026-05-22). Safety 0/8. E2E osservato Luke: NO.

## STANCE CTO (Luke ha approvato in S222)
ARGOS produce codice più veloce di quanto verifica: 60 sessioni, 1/9 anelli VERIFIED. S221 ha allargato lo scope (partner-unico = +trasporto+pratiche+fiscale) sopra una catena dove l'inbox base manca.
→ **Scope S222 CONGELATO** (rewrite landing / Gemini Deep Research / scraper trasporto). Niente parte finché non sale il numero che conta: **anelli VERIFIED su 9**. Obiettivo S223 = portarlo verso 3/9.

## PROSSIMI STEP S223 (in ordine, NO fix prima di verifica)
1. **Verifica #6 inbox `messages`** SUL CODICE/DB REALE, locale E iMac.
   - ⚠️ CONFLITTO DA RISOLVERE: gate-state S222 dice `messages` MISSING; ma memory S201/S202 (`s201_closure_pivot_architect_findings.md`, `s202_closure_2of5_handoff_s203.md`) dicono EXISTS + ALTER 3 col + 3 idx già applicato su iMac (commit 7e0521f). Uno dei due è stale.
   - Comando: `ssh gianlucadistasi@192.168.1.2` + `sqlite3 dealer_network.sqlite ".schema messages"` (o path DB iMac autoritativo — vedi `s204_verita_codice_audit`). Stesso check su DB locale.
2. **Verifica #9 HITL bug `sent=1 approvata=0`** — riprodurre. Codice: `wa-intelligence/` (bridge_outbound vive in `comm-broker/bridge.sqlite` separato, lezione S193). Capire dove un messaggio viene marcato `sent` senza essere `approvata`.
3. **Solo se i dati confermano il gate** → fix #6 (creare tabella) + #9 (bug safety) + 1 E2E su TEST_FOUNDER 393314928901 (Luke fisico, vedi feedback memory). Se i dati dicono altro → da CTO ricalibro priorità, niente parte senza verifica.

## NON toccare
image_sanitizer.py / codice produzione. NON deploy landing/PDF/messaggi. Scope partner-unico (landing/Gemini/trasporto) congelato.

## Vincoli sessione
- Context: chiusa S222 a 51%. Partire fresca.
- TEST_FOUNDER prima di qualsiasi dealer reale. Domenica = OFF Luke (no scadenze fisiche di domenica).
- Day 1 Stile Car blocker invariati: C-SAN-001, C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001.
