# S222 — Partner unico: Gemini Deep Research → rewrite landing fiscale

## STATO CHIUSO S221
### ✅ Sicurezza leak (step 1-2-3 S221) — CHIUSO
- **Step 1** — `~/.claude/hooks/global_session_end.sh`: gate secret+junk DOPO `git add -A`. Scansiona staged diff (regex sk-or/sk-ant/sk-/ghp_/github_pat_/AKIA/xox/Telegram + junk .chrome_profile/.bak/.db/.sqlite). Hit → `git reset` + SESSION_DIRTY.md redatto, MAI commit. Testato in repo temp: vettori S220 bloccati, codice pulito passa.
- **Step 3** — `.git/hooks/pre-commit`: stesso TOKEN_PATTERN aggiunto (prima matchava solo `api_key=`). Testato.
- **Step 2** — branch `backup-pre-s220-reset-1a132e3` ELIMINATO. Commit-disastro `1a132e3` fuori da ogni branch (solo reflog ~30gg).
- **OpenRouter**: Luke ha ruotato, nuovo token in `.env` (verificato presenza prefisso sk-or-v1). GitHub PAT + Telegram già morti.

### ✅ DECISIONE FOUNDER S221 — "PARTNER UNICO ORCHESTRATORE"
Luke decide: ARGOS NON più "scouting only" → orchestra l'intera filiera (trasporto+pratiche+qualificazione fiscale), dealer resta acquirente+soggetto fiscale, paga a risultato. Punto = **unicità del servizio**. Memory: `s221_decisione_partner_unico_orchestratore.md`.
**2 GUARDRAIL (Luke):** (1) affidabilità dati — claim fiscali verificati fonte primaria, mai inventati; (2) zero costi — ogni anello orchestrato a costo zero ARGOS.
**3 PALETTI WORDING:** "coordino agenzie autorizzate" (no pratiche in proprio, L.264/1991) · "verifica documentale del regime fiscale" (no "consulenza") · MAI "gestisco/assolvo IVA" → "resti TU soggetto fiscale".

## PROSSIMI STEP S222 (in ordine)
1. **Gemini Deep Research** — validare LEGALMENTE il modello orchestrazione (guardrail #1). Riprendere i 3 prompt consegnati S218 (stream fiscale prioritario). Output → matrix VERIFIED/DISPUTED come S217.
2. **Rewrite 3 sezioni landing** `landing/index.html` (card :476, Step03 :523, FAQ :588, fee :597) rispettando i 3 paletti. La frase illegale "gestisco IVA" NON è presente oggi (verificato) — il problema è il posizionamento "import a parte / gestisci tu", opposto al partner-unico.
3. **Review legal-compliance** sulla copy riscritta PRIMA di qualsiasi deploy (gate AGCM €5k-500k).
4. **Step 5 — scraper trasporto** DE→IT (Clicktrans/Macingo): validare quali portali espongono preventivi pubblici scrapeable. Sbloccato dal modello orchestrazione.

## NON toccare
image_sanitizer.py / codice produzione. NON deployare landing/PDF/messaggi finché copy riscritta E rivista.

## Stato reale anelli ARGOS (NON production-ready)
VERIFIED = 1/9 (#1 scrape). #6 inbox `messages` MISSING. #9 HITL EXISTS_BUGGY (`sent=1 approvata=0`). Safety 0/8. E2E osservato Luke: NO.

## Day 1 Stile Car — blocker invariati
C-SAN-001 (TinEye manuale Luke /tmp/s217_revtest/), C-E2E-ZERO, C-COMM-INTEL-001, C-GATE-FONTE-001.
