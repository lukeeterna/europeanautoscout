# S208 — Run scraper S207 ri-targato + generazione prospect_list.csv

## STATO IN INGRESSO

S207 ha completato il **ri-target del codice** (modello mandato demand-side) ma
NON ha eseguito il run effettivo sui portali (gate context #7 chiuso a 57%
prima del run). Il codice è verde syntax-check e committato sul branch
`s206/marche-register`.

**Commit di riferimento**: `feat(S207): ri-target prospect modello mandato — invert stock + drop F5 + rename flag`

## COSA È STATO FATTO IN S207

- `tools/s206_marche_scraper.py` patched (D1+D3+D4+D5)
  - D1: logica stock invertita → `plausibile` 1-8, `borderline` 9-15, `deprioritizzato` 16+, `escluso` big dealer
  - D2: verificato F5 (anomalia prezzo EU→IT) NON presente in questo scraper (vive in CoVe). Solo nota in EXECUTION_REPORT
  - D3: `flag_target_alto_si_no` → `flag_micro_operatore_plausibile` + nuove colonne `multi_brand`, `accesso_clienti="DA_VERIFICARE_AL_TELEFONO"`
  - D4: `if not phone: continue` hard-skip (riga senza telefono = inutile per Luke)
  - D5: EXECUTION_REPORT con tabella onestà 4 metriche + gate VERDE solo su dati reali
- Sort prospects: plausibile > borderline > deprioritizzato > escluso

## COSA RESTA DA FARE IN S208

### STEP 1 — Run scraper (atteso 10-20 min)
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git checkout s206/marche-register
python3 tools/s206_marche_scraper.py 2>&1 | tee /tmp/s208_run.log
```

Output attesi in `research/s206_marche_register/`:
- `prospect_list.csv` (schema nuovo: colonne `flag_micro_operatore_plausibile`, `multi_brand`, `accesso_clienti`)
- `prospect_list_per_provincia.md`
- `corpus_register.md`
- `EXECUTION_REPORT.md` con tabella onestà

### STEP 2 — Verifica gate onesto
Leggi `EXECUTION_REPORT.md` sezione "1. Tabella onestà". Se **GIALLO**:
- Quale portale è 0 listing (403/captcha/parser rotto)?
- % description bassa = enrich detail rotto?
- 0 plausibili = pipeline produce tutto big dealer o stock zero?

NON falsificare il gate. Riporta lo stato reale.

### STEP 3 — Commit CSV + report
```bash
git add research/s206_marche_register/
git commit -m "feat(S208): output run scraper S207 ri-targato — prospect_list + EXECUTION_REPORT"
```

### STEP 4 — Consegna a Luke
- Se VERDE: CSV pronto per chiamate.
- Se GIALLO: spiega cosa è rotto e cosa serve fixare (fix scraper portale X / schema __NEXT_DATA__ cambiato / ecc.).

## VINCOLI

- Branch `s206/marche-register` (NON push master)
- NO Ondata 2 (Puglia/Basilicata) finché Luke non valida i numeri Marche
- NO contatti operatori
- Re-run idempotente (dedup telefono)

## RIFERIMENTI

- Codice scraper: `tools/s206_marche_scraper.py` (riga 120 dataclass Prospect, riga 1063 build_prospects, riga 1411 EXECUTION_REPORT)
- Direttiva originale Luke: `prompts/s207_ritarget_micro_operatore_mandato.md`
- Modello mandato: `~/.claude/rules/identity.md`
