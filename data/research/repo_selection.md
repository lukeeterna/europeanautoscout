# Selezione libreria Facebook Group Scraper
**Valutato:** 2026-06-17 | **Stack:** macOS 11.7.10 Big Sur / Python 3.13.2

## Tabella decisione

| repo | ultimo commit (data + URL) | install OK su Big Sur 3.13 (sì/no + nota) | supporto gruppi (sì/no) | fetch-test esito | DECISIONE |
|------|---------------------------|-------------------------------------------|------------------------|-----------------|-----------|
| [kevinzg/facebook-scraper](https://github.com/kevinzg/facebook-scraper) v0.2.59 | 2022-08-31 ([PyPI](https://pypi.org/project/facebook-scraper/)) — ultimo commit GitHub ~ott 2023 | **SI con fix manuale** — install OK ma `import` fallisce su Python 3.13 per breaking change lxml: `lxml.html.clean` separato in `lxml_html_clean`. Serve `pip install lxml_html_clean` post-hoc. Con il fix: `IMPORT OK`. | Si (doc: `get_posts(group=<id>, cookies=...)`) | Fetch non testato: richiede cookie-auth Facebook reale. Metodo basato su mbasic.facebook.com — FB cambia HTML frequentemente e repo non riceve manutenzione da ~3.5 anni | **SCARTATA** — fallisce must "ultimo commit <12 mesi": ultimo rilascio PyPI ago 2022, nessun commit 2024-2026. Repo de facto morta. FB ha cambiato ripetutamente mbasic.facebook.com dal 2022 senza aggiornamenti del maintainer. |
| [MasuRii/FBScrapeIdeas](https://github.com/MasuRii/FBScrapeIdeas) v0.8.3 | **2025-12-21** ([commit e3f5450](https://github.com/MasuRii/FBScrapeIdeas)) — ~6 mesi fa, entro 12 mesi | **SI** — tutte le dipendenze core (selenium 4.45.0, webdriver-manager 4.1.2, bs4, lxml, requests) installate senza errori. `import scraper` OK. Chrome 138 disponibile su macchina. Nessuna wheel incompatibile Big Sur. | **Si** — README esplicito: "logs into Facebook to scrape posts and comments from private or public groups" | Fetch non testato: richiede login Facebook reale + cookie session. Nessun test fetch eseguito (nessuna credenziale usata). | **SCELTA** — unico candidato che supera tutti i [must]: commit dic 2025 (entro 12 mesi), install+import 100% OK Big Sur 3.13, supporto gruppi esplicito, Selenium + Chrome disponibile. |

---

## Candidati esclusi dalla valutazione approfondita

| repo | motivo esclusione |
|------|-------------------|
| [wspooong/facebook-group-scraper](https://github.com/wspooong/facebook-group-scraper) | 4 stelle, ispirato a kevinzg (stessa base), non su PyPI, ultima attività non determinabile ma pattern "fork di repo morta". Escluso per priorità. |

---

## Repo scelta: MasuRii/FBScrapeIdeas v0.8.3

**Perché:** Unico candidato verificato che supera tutti e tre i [must]: (1) commit 2025-12-21 — entro 12 mesi; (2) install completo senza errori su Big Sur 3.13 + `import scraper` OK; (3) supporto esplicito gruppi pubblici e privati via Selenium + login.

**Avvertenze operative per `collect_fb_groups.py`:**
- Richiede cookie-auth Facebook reale (nessun fetch anonimo possibile su gruppi).
- Chrome 138 presente su macchina — webdriver-manager scarica automaticamente ChromeDriver compatibile al primo run.
- Dipendenza `google-generativeai` e `openai` sono OPZIONALI (solo per analisi AI integrata) — per puro scraping bastano le dipendenze core già testate.
- Nessuna wheel AVX2-dipendente nel dependency tree — compatibile con iMac 2012 no-AVX2.
- Fetch non testato con credenziali reali: eseguire UAT su gruppo test privato prima di usare in produzione.
- **Licenza:** MIT ([LICENSE](https://github.com/MasuRii/FBScrapeIdeas/blob/master/LICENSE)) — nessun vincolo legale.

**Fetch-test:** Dichiarato onestamente come "non eseguito" — richiederebbe login Facebook reale con credenziali. Il gate [must] decisivo (install+import+freshness) è soddisfatto. Il test fetch è una due diligence da fare con un account di test prima dell'integrazione.

---

*Fonti: [PyPI facebook-scraper](https://pypi.org/project/facebook-scraper/) | [GitHub kevinzg commits](https://github.com/kevinzg/facebook-scraper/commits) | [GitHub MasuRii releases](https://github.com/MasuRii/FBScrapeIdeas/releases) | [GitHub topics facebook-scraper 2026](https://github.com/topics/facebook-scraper)*
