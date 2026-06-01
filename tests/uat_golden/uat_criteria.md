# UAT Criteria — Sanitizer D-32 (S183)

**Contract**: questo file è la specifica BINARIA del gate UAT visual sanitizer.
Future UAT misurate contro questo file, non contro intuizione.

## Criteri (5 NO consecutivi su 5/5 sample = PASS)

| ID | Criterio | YES (fail) condition | NO (pass) condition |
|----|----------|----------------------|---------------------|
| C1 | Watermark seller leggibile | "Autohaus *" o nome seller leggibile a zoom 100% | Watermark coperto / illeggibile |
| C2 | Plate text leggibile | Caratteri targa distinguibili a zoom 100% | Targa coperta / illeggibile |
| C3 | Brand row footer riconoscibile | ≥2 loghi marche (BMW/MB/Audi/VW/Porsche/Mini) distinguibili in footer | Footer brand row coperto |
| C4 | Tagline testuale leggibile | Tagline sotto footer (es. "BMW Service Partner") leggibile | Tagline coperta |
| C5 | Cerchi/fari/trim auto modificati | Una qualsiasi feature auto rilevante (cerchi, fari, badge modello, trim AMG/M, paraurti) è stata coperta/modificata | Features auto intatte |

## Regola UAT PASS

- **UAT PASS** = 5 NO consecutivi (C1=NO, C2=NO, C3=NO, C4=NO, C5=NO) su **TUTTI** i 5 sample valutati
- **UAT FAIL** = 1+ YES su 1+ sample → diagnosi specifica gate B (B1/B2/B3) → handoff S183-bis

## Sample set ufficiale (10 golden in `tests/uat_golden/`)

| # | File | Seller | Tipo |
|---|------|--------|------|
| 1 | g01_isernhagen_smoke_00.jpg | Autohaus Isernhagen | baseline UAT NO-GO S179b |
| 2 | g02_isernhagen_smoke_01.jpg | Autohaus Isernhagen | baseline UAT NO-GO S179b |
| 3 | g03_isernhagen_smoke_02.jpg | Autohaus Isernhagen | baseline UAT NO-GO S179b |
| 4 | g04_isernhagen_raw_00.jpg | Autohaus Isernhagen | raw frontale BMW iX3 |
| 5 | g05_isernhagen_raw_01.jpg | Autohaus Isernhagen | raw posteriore |
| 6 | g06_mixed_030c.jpg | seller_diff_1 | mixed seller validation |
| 7 | g07_mixed_39d6.jpg | seller_diff_2 | mixed seller validation |
| 8 | g08_mixed_4289.jpg | seller_diff_3 | mixed seller validation |
| 9 | g09_mixed_76ea.jpg | seller_diff_4 | mixed seller validation |
| 10 | g10_mixed_7baf.jpg | seller_diff_5 | mixed seller validation |

UAT GATE C = 5 sample (scelta Luke tra i 10), 5/5 NO consecutivi → PASS.
