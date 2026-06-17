# BRIEF B — TOOL-RESEARCH (raccolta → KB voce AMBRA). CC Max nativo per sintesi. system python3.
# Output verificabili a ogni stadio su disco. 4 moduli ISOLATI.
#
# MODULO 1 — collect_as24_listings.py (STABILE, riusa scraper esistente)
#   Per ogni listing: descrizione testuale + seller{companyName,type} + location.countryCode.
#   Build sotto experiment-OFF. → data/research/as24_listings_raw.json. Verifica: file esiste, conta righe.
#
# MODULO 2 — collect_fb_groups.py (FRAGILE, ISOLATO, rischio-account dichiarato)
#   pip install facebook-scraper playwright ; python -m playwright install chromium.
#   Input: config/fb_groups.yaml (URL gruppi — popolata A MANO da Luke).
#   facebook-scraper via cookie primario; fallback Playwright headless se <1 pagina (JS-render gruppi).
#   IP via Tailscale exit-node (config esterna, NON nel codice). Account SACRIFICABILE in .env (NON operativo).
#   Rate: max 3 pagine/gruppo, sleep 30-60s random. → data/research/fb_posts_raw.json.
#   ISOLATO: se fallisce/banna, MODULO 1 + sintesi girano lo stesso sui soli annunci AS24.
#   NON scoprire gruppi via scraping della search FB (trigger anti-bot): la scoperta e' manuale (yaml),
#   lo scraper LEGGE gruppi noti. Post PUBBLICI = ricerca di mercato; account separato perche' il ban colpisce l'account.
#
# MODULO 3 — riduzione (subagent SOLO qui; S258: solo riduzione input→output, MAI logica)
#   Subagent legge i 2 JSON raw → dedup → tiene SOLO il campo testo → campiona se >500 →
#   data/research/corpus_reduced.json. Verifica al ritorno contro file (esiste, conta righe, no PII non necessario).
#   Se corpus <500 item: salta subagent, riduci nel main.
#
# MODULO 4 — sintesi voce (CC NATIVO, no API/no modello esterno) → data/research/ambra_voice_profile.md
#   Da corpus_reduced: lessico ESATTO dei dealer ("permuta","subito","no perditempo"…), registro/tono,
#   leve (prezzo/disponibilita'/fiducia), cosa enfatizzano, cosa RIFIUTANO. Ogni voce ANCORATA a occorrenze reali.
#   GATE ONESTA' (vincolo dell'intero progetto): grep "eccezion|migliore|unico|best|top|garantito" sul profilo = 0.
#   La voce e' "parla COME loro", NON "vendi come un cafone".
#
# ORDINE: M1 → M3 → M4. M2 parallelo/opzionale (NESSUNO stadio dipende da M2). Verifica file a ogni stadio.
