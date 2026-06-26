# HANDOFF — S4-OPS sessione 2 — collector social FB + IG

**FB COLLECTOR = VERDE (5/5)**
**IG web_profile_info DA QUI = SÌ (4/4 a 200, control @nasa=200) → IG collector COSTRUITO**

> Nota: in DB solo 4 dealer hanno handle IG (non 5). Probe e collector girati sui 4 → 4/4.
> Gate richiesto ≥3/5: superato con margine (4/4, control @nasa=200 → endpoint vivo, HTTP/3 negoziato).

---

## FASE 0 — re-ground (riportato, non costruito)
- `pwd` = root, `git HEAD` = b9f614f, status = solo rumore-hook (NEXT_SESSION_PROMPT/STATE/rings.json). OK.
- `resilient_fetcher.py` espone `ResilientFetcher` con `IMPERSONATE="chrome120"` + curl_cffi + HTTP/2/3. VERIFICATO.
- Tabelle FASE 1 `dealer_operational_profile`/`operational_anchors`: **NON esistevano** (né DB né codice).
  Schema (ri)creato in questa sessione — `tools/social_collectors/schema.py`.
- curl_cffi da questa macchina: `chrome120` → status 200, http_version 3. VERIFICATO.

## PARTE A — collector Facebook (provato sul campo → costruito)
Modulo: `tools/social_collectors/fb_collector.py`. Fetch HTML pubblico (curl_cffi) →
og:title/og:description/og:url + body (`category_name`, +39 phone, email/website se pubblici).
Degradazione: email/website/data-post login-gated → vuoti (non errore); og: assente → `source=js_only`.

| dealer_id | fb_category | fb_likes | fb_talking | fb_phone | email | website | data-post | source |
|---|---|---|---|---|---|---|---|---|
| 2f_motors_cs | Automotive Dealership | 1922 | 21 | — (gated) | — | — | — (gated) | ok |
| auto_carfora_ce | Automotive Wholesaler | 13952 | 271 | +39 392 921 4946 | — | — | — | ok |
| autoline_av | Motor vehicle company | 4666 | 129 | +39 345 899 0088 | — | — | — | ok |
| de_cicco_cs | Automotive Store | 504 | — | +39 335 148 0797 | — | — | — | ok |
| gp_cars_ta | Automotive Store | 37888 | 339 | — (gated) | — | — | — | ok |

- og: SEMPRE presenti (5/5 ok, 0 js_only). Categoria 5/5, likes 5/5, telefono 3/5 (2 login-gated → vuoto, degradazione mostrata).
- email/website/data-ultimo-post: login-gated su tutte e 5 → vuote per design (non errore).
- **Idempotenza: 0 duplicati** (re-run → profile resta 5 righe; upsert su dealer_id).

## PARTE B — Instagram (probe → build)
**B1 PROBE** (`tools/social_collectors/ig_probe.py`, read-only): web_profile_info via curl_cffi+HTTP/2,
header `x-ig-app-id:936619743392459` + UA mobile + Accept-Language it-IT, cookie-stripping.
VERDETTO: **4/4 a 200** (HTTP/3). Control `@nasa`=200 → endpoint vivo lato macchina.

**B2 BUILD** (≥3/5 → costruito): `tools/social_collectors/ig_collector.py`, persiste bio/link-in-bio/
categoria/follower/recency. Stessa degradazione + idempotenza.

| dealer_id | @handle | ig_category | follower | link-in-bio | ultimo post |
|---|---|---|---|---|---|
| 2f_motors_cs | @2fmotors | Concessionario di auto | 4230 | http://www.2fmotors.com/ | 0 gg fa |
| auto_carfora_ce | @autocarforasrl | Concessionario di automobili | 13536 | http://www.autocarfora.it/ | 1 gg fa |
| de_cicco_cs | @decicco_automobili | (none) | 1011 | impresapiu.subito.it/shops/21445… | 1 gg fa |
| gp_cars_ta | @gpcars.concessionarioauto | Automobili | 6951 | https://wa.me/393283132484/ | 0 gg fa |

- **Idempotenza: 0 duplicati** (profile 5 righe, anchors 20 righe = 4×5, stabili su re-run).

## Copertura 4 anchor (`operational_anchors`, dati REALI)
| dealer | qualifica | canale | vivo | volume |
|---|---|---|---|---|
| 2f_motors_cs | auto:Automotive Dealership (fb) | web:2fmotors.com (ig) | ig_post 0gg (ig) | ig_foll:4230 (ig) |
| auto_carfora_ce | auto:Automotive Wholesaler (fb) | tel:+39 392 921 4946 (fb) | ig_post 1gg (ig) | ig_foll:13536 (ig) |
| autoline_av | auto:Motor vehicle company (fb) | tel:+39 345 899 0088 (fb) | fb_talking:129 (fb) | fb_likes:4666 (fb) |
| de_cicco_cs | auto:Automotive Store (fb) | tel:+39 335 148 0797 (fb) | ig_post 1gg (ig) | ig_foll:1011 (ig) |
| gp_cars_ta | auto:Automotive Store (fb) | whatsapp:wa.me/393283132484 (ig) | ig_post 0gg (ig) | ig_foll:6951 (ig) |

- **qualifica** 5/5 (FB/IG category). **canale** 5/5 (tel-FB o wa.me/web-IG). **vivo** 5/5 (recency IG, fallback fb_talking). **volume** 5/5 (IG followers, fallback fb_likes).
- autoline_av (solo FB) coperto 100% da soli dati FB → FB sufficiente come fonte unica quando IG manca.

## Garanzie
- **0 colonne personali (PII)**: schema verificato, nessuna colonna titolare/cf/piva/owner.
- FUORI SCOPE rispettato: niente pain-da-commenti, niente post oltre i 12, niente proxy/dongle/Docker, niente repo terzi (SSujitX confermato morto: 5/5 import error nello scratch).
- Dipendenza unica: curl_cffi (già nel repo via resilient_fetcher).

## File nominati (commit, no push)
- `tools/social_collectors/schema.py`
- `tools/social_collectors/fb_collector.py`
- `tools/social_collectors/ig_probe.py`
- `tools/social_collectors/ig_collector.py`
- `tools/social_collectors/anchors.py`
- `HANDOFF_CURRENT.md`
- (dati persistiti in `dealer_network.sqlite` — non committato)
