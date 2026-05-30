# Prompt ripartenza S208 — Run scraper S207 ri-targato

**Generato**: 2026-05-30 (chiusura S207 ordinata su gate context #7 a 60%)
**Branch**: `s206/marche-register`
**Commit ultimo**: `44a8bc8 feat(S207): ri-target prospect modello mandato — invert stock + drop F5 + rename flag`

## STATO S207 CHIUSO VERDE (scope codice)

S207 ha completato il **ri-target del codice** modello mandato demand-side.
- Codice patched: `tools/s206_marche_scraper.py` (D1 stock invertito + D3 flag rinominato + D4 phone mandatory + D5 gate onesto)
- F5 verificato non presente (vive in CoVe, non in prospect scraper)
- Syntax check PASS
- Commit unico 44a8bc8 (+230/-79)

## COSA RESTA — S208

**Run effettivo scraper** (10-20min su 3 portali) + commit output + consegna Luke.

Entry point: `prompts/s208_run_scraper_ritargato_marche.md`

Comando one-liner:
```bash
cd /Users/macbook/Documents/combaretrovamiauto-enterprise
git checkout s206/marche-register
python3 tools/s206_marche_scraper.py 2>&1 | tee /tmp/s208_run.log
```

Output attesi in `research/s206_marche_register/`:
- `prospect_list.csv` (schema S207)
- `prospect_list_per_provincia.md`
- `corpus_register.md`
- `EXECUTION_REPORT.md` con **tabella onestà sezione 1** (4 metriche: portali OK / % description / # prospect / # plausibili)

## GATE S208

- VERDE → commit + consegna CSV a Luke
- GIALLO → NON falsificare. Identifica cosa è rotto (403, captcha, parser __NEXT_DATA__ cambiato), riporta a Luke con fix proposto

## VINCOLI

- Branch `s206/marche-register`, NO push master
- NO Ondata 2 Puglia/Basilicata finché Luke valida Marche
- NO contatti operatori
- Re-run idempotente (dedup telefono)
