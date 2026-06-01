"""
portal_profiles.py -- ARGOS 73-Portal Search Profiles
CoVe 2026 | Enterprise Grade

Profili di ricerca per TUTTI i 73 portali EU target.
Ogni profilo definisce: URL template, encoding, regexes, currency, lingua.

REGOLA FOUNDER: "TUTTE le fonti, non top-N. Il vantaggio e' nella QUANTITA'."

Author: ARGOS Automotive CTO Stack
"""

from __future__ import annotations
from .generic_scraper import SearchProfile


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — GERMANIA (DE)
# ═══════════════════════════════════════════════════════════════════════════════

KLEINANZEIGEN_DE = SearchProfile(
    url_template="{base_url}/s-autos/{make}-{model}/k0c216+autos.regja_i:{year_min},+autos.regja_s:{year_max},+autos.km_i:,{km_max}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="de-DE,de;q=0.9,en;q=0.8",
    country="DE",
    currency="EUR",
    listing_block_re=r'<article[^>]*class="[^"]*aditem[^"]*"[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/s-anzeige/)[^"\']*)["\']',
    price_re=r'<p[^>]*class="[^"]*aditem-main--middle--price[^"]*"[^>]*>[^<]*?([\d.,]+)\s*€',
    title_re=r'<a[^>]+class="[^"]*ellipsis[^"]*"[^>]*>([^<]+)</a>',
    image_re=r'<img[^>]+src=["\']([^"\']*(?:img\.ebay-kleinanzeigen|img\.kleinanzeigen)[^"\']*)["\']',
    km_re=r'([\d.,]+)\s*km',
    year_re=r'EZ\s*(\d{2}/\d{4})',
    results_per_page=25,
    make_map={
        "Mercedes": "mercedes-benz",
        "Range Rover": "land-rover",
    },
)

PKW_DE = SearchProfile(
    url_template="{base_url}/suche?fahrzeugart=pkw&marke={make}&modell={model}&ez_von={year_min}&ez_bis={year_max}&km_bis={km_max}&seite={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="de-DE,de;q=0.9",
    country="DE",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*result-list-entry[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/angebot/|/fahrzeug/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=20,
    model_map={
        "BMW": {"Serie 3": "3er", "Serie 5": "5er", "Serie 1": "1er"},
        "Mercedes": {"Classe A": "A-Klasse", "Classe C": "C-Klasse", "Classe E": "E-Klasse"},
    },
)

AUTO_DE = SearchProfile(
    url_template="{base_url}/angebot/{make}/{model}/gebrauchtwagen/?erstzulassung-von={year_min}&erstzulassung-bis={year_max}&kilometerstand-bis={km_max}&seite={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="de-DE,de;q=0.9",
    country="DE",
    currency="EUR",
    uses_json_ld=True,
    listing_block_re=r'<div[^>]*class="[^"]*listing-item[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/fahrzeug/|/auto/|/angebot/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=15,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — OLANDA (NL)
# ═══════════════════════════════════════════════════════════════════════════════

MARKTPLAATS_NL = SearchProfile(
    url_template="{base_url}/q/{make}+{model}/?categoryId=91&bouwjaarVan={year_min}&bouwjaarTot={year_max}&kmTot={km_max}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="nl-NL,nl;q=0.9,en;q=0.8",
    country="NL",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<li[^>]*class="[^"]*hz-Listing[^"]*"[^>]*>(.*?)</li>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/v/auto-s/|/a/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=30,
    make_map={
        "Mercedes": "Mercedes-Benz",
        "Range Rover": "Land Rover",
    },
)

AUTOTRACK_NL = SearchProfile(
    url_template="{base_url}/aanbod/{make}/{model}/?minyear={year_min}&maxyear={year_max}&maxmileage={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="nl-NL,nl;q=0.9",
    country="NL",
    currency="EUR",
    uses_next_data=True,  # Autotrack uses __NEXT_DATA__ — parse JSON first
    listing_block_re=r'<a[^>]+href="([^"]*(?:/a/)[^"]*)"[^>]*>.*?</a>',
    url_re=r'href="([^"]*(?:/a/)[^"]*)"',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — BELGIO (BE)
# ═══════════════════════════════════════════════════════════════════════════════

TWEEDEHANDS_BE = SearchProfile(
    url_template="{base_url}/q/{make}+{model}/?categoryId=91",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="nl-BE,nl;q=0.9,fr-BE;q=0.8,en;q=0.7",
    country="BE",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<li[^>]*class="[^"]*classified[^"]*"[^>]*>(.*?)</li>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/a/autos/|/v/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=30,
    make_map={
        "Mercedes": "Mercedes-Benz",
        "Range Rover": "Land Rover",
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — AUSTRIA (AT)
# ═══════════════════════════════════════════════════════════════════════════════

WILLHABEN_AT = SearchProfile(
    url_template="{base_url}/iad/gebrauchtwagen/auto/{make}/{model}?YEAR_MODEL_FROM={year_min}&YEAR_MODEL_TO={year_max}&MILEAGE_TO={km_max}&page={page}&rows=25",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="de-AT,de;q=0.9,en;q=0.8",
    country="AT",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*class="[^"]*search-result-entry[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/iad/)[^"\']*d-\d+[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=25,
    make_map={
        "Mercedes": "mercedes-benz",
        "Range Rover": "land-rover",
    },
)

GEBRAUCHTWAGEN_AT = SearchProfile(
    url_template="{base_url}/gebrauchtwagen/{make}/{model}?bj_von={year_min}&bj_bis={year_max}&km_bis={km_max}&seite={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="de-AT,de;q=0.9",
    country="AT",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*car-item[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/gebrauchtwagen/|/auto/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

AUTOREVUE_AT = SearchProfile(
    url_template="{base_url}/marktplatz/gebrauchtwagen/?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="de-AT,de;q=0.9",
    country="AT",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-card[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/fahrzeug/|/inserat/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — FRANCIA (FR)
# ═══════════════════════════════════════════════════════════════════════════════

LEBONCOIN_FR = SearchProfile(
    url_template="{base_url}/recherche?category=2&text={make}+{model}&mileage_max={km_max}&regdate_min={year_min}&regdate_max={year_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="fr-FR,fr;q=0.9,en;q=0.8",
    country="FR",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<a[^>]*class="[^"]*styles_adCard[^"]*"[^>]*>(.*?)</a>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/ad/voitures/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=35,
    make_map={
        "Mercedes": "Mercedes-Benz",
        "Range Rover": "Land Rover",
    },
)

LARGUS_FR = SearchProfile(
    url_template="{base_url}/occasion/{make}/{model}.html?yearMin={year_min}&yearMax={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="fr-FR,fr;q=0.9",
    country="FR",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*annonce[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/occasion/|/annonce/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=20,
)

LACENTRALE_FR = SearchProfile(
    url_template="{base_url}/listing?makesModelsCommercialNames={make}%3A{model}&yearMin={year_min}&yearMax={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="uppercase",
    model_in_url="uppercase",
    accept_language="fr-FR,fr;q=0.9",
    country="FR",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*class="[^"]*searchCard[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auto-occasion/|/annonce-voiture/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=16,
    make_map={
        "Mercedes": "MERCEDES",
        "Range Rover": "LAND ROVER",
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — SVEZIA (SE)
# ═══════════════════════════════════════════════════════════════════════════════

BLOCKET_SE = SearchProfile(
    url_template="{base_url}/annonser/hela_sverige/fordon/bilar?q={make}+{model}&cg_m={year_min}&cg_x={year_max}&cg_mils_max={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="sv-SE,sv;q=0.9,en;q=0.8",
    country="SE",
    currency="SEK",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*class="[^"]*styled__Wrapper[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/annons/|/ad/)[^"\']*)["\']',
    price_re=r'([\d\s]+)\s*kr',
    results_per_page=40,
)

BYTBIL_SE = SearchProfile(
    url_template="{base_url}/bil/{make}/{model}?yearMin={year_min}&yearMax={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="sv-SE,sv;q=0.9",
    country="SE",
    currency="SEK",
    listing_block_re=r'<div[^>]*class="[^"]*listing-card[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/bil/|/annons/)[^"\']*)["\']',
    price_re=r'([\d\s]+)\s*kr',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — REP. CECA (CZ)
# ═══════════════════════════════════════════════════════════════════════════════

SAUTO_CZ = SearchProfile(
    url_template="{base_url}/inzerce/osobni/{make}/{model}?rokOd={year_min}&rokDo={year_max}&kmDo={km_max}&strana={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="cs-CZ,cs;q=0.9,en;q=0.8",
    country="CZ",
    currency="CZK",
    listing_block_re=r'<div[^>]*class="[^"]*c-item[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/inzerce/|/detail/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:Kc|CZK|Kč)',
    results_per_page=20,
    make_map={
        "Mercedes": "mercedes-benz",
        "Range Rover": "land-rover",
    },
)

BAZOS_CZ = SearchProfile(
    url_template="{base_url}/inzeraty/{make}-{model}/?strana={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="cs-CZ,cs;q=0.9",
    country="CZ",
    currency="CZK",
    listing_block_re=r'<div[^>]*class="[^"]*inzeraty[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/inzerat/|/detail/)[^"\']*\.php[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:Kc|CZK|Kč)',
    results_per_page=20,
)

INZERCE_AUTO_CZ = SearchProfile(
    url_template="{base_url}/inzerce/{make}/{model}/?rokOd={year_min}&rokDo={year_max}&kmDo={km_max}&strana={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="cs-CZ,cs;q=0.9",
    country="CZ",
    currency="CZK",
    listing_block_re=r'<div[^>]*class="[^"]*ad-item[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/inzerce/|/auto/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:Kc|CZK|Kč)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — POLONIA (PL)
# ═══════════════════════════════════════════════════════════════════════════════

OTOMOTO_PL = SearchProfile(
    url_template="{base_url}/osobowe/{make}/{model}/?search%5Bfilter_float_year%3Afrom%5D={year_min}&search%5Bfilter_float_year%3Ato%5D={year_max}&search%5Bfilter_float_mileage%3Ato%5D={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="pl-PL,pl;q=0.9,en;q=0.8",
    country="PL",
    currency="PLN",
    uses_next_data=True,
    listing_block_re=r'<article[^>]*data-testid="listing-ad"[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/oferta/|/osobowe/)[^"\']*\.html)["\']',
    price_re=r'([\d\s]+)\s*(?:PLN|zl|zł)',
    results_per_page=32,
    make_map={
        "Mercedes": "mercedes-benz",
        "Range Rover": "land-rover",
    },
)

OLX_PL = SearchProfile(
    url_template="{base_url}/motoryzacja/samochody/{make}/{model}/?search%5Bfilter_float_year%3Afrom%5D={year_min}&search%5Bfilter_float_year%3Ato%5D={year_max}&search%5Bfilter_float_milage%3Ato%5D={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="pl-PL,pl;q=0.9",
    country="PL",
    currency="PLN",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*data-cy="l-card"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/d/oferta/|/oferta/)[^"\']*)["\']',
    price_re=r'([\d\s]+)\s*(?:PLN|zl|zł)',
    results_per_page=40,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — UNGHERIA (HU)
# ═══════════════════════════════════════════════════════════════════════════════

HASZNALTAUTO_HU = SearchProfile(
    # hasznaltauto.hu returns 403 to scrapers — strong anti-bot (rate limiting + UA check).
    # Clean URL confirmed: /szemelyauto/{make}/{model} (no query params in base URL).
    # The encoded "talalatok" path with opaque token is used by their internal search
    # (token encodes all filter params, not human-readable).
    # Workaround approach: use /szemelyauto/bmw/x3 base + filter params appended.
    # Known filter params (from Hungarian scraper community):
    #   evjarat_min / evjarat_max (year), km_max (km), oldalszam (page number, 1-based).
    # Requires Selenium + Hungarian UA + session cookies to bypass 403.
    # Status: BROKEN — 403 WAF. Needs Selenium with HU Accept-Language header.
    url_template="{base_url}/szemelyauto/{make}/{model}?evjarat_min={year_min}&evjarat_max={year_max}&km_max={km_max}&oldalszam={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="_",
    accept_language="hu-HU,hu;q=0.9,en;q=0.8",
    country="HU",
    currency="HUF",
    listing_block_re=r'<div[^>]*class="[^"]*talalat-sor[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/szemelyauto/|/hirdetes/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:Ft|HUF)',
    results_per_page=20,
    make_map={
        "BMW": "bmw",
        "Mercedes": "mercedes_benz",
        "Audi": "audi",
        "Range Rover": "land_rover",
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — ROMANIA (RO)
# ═══════════════════════════════════════════════════════════════════════════════

AUTOVIT_RO = SearchProfile(
    url_template="{base_url}/autoturisme/{make}/{model}/?search%5Bfilter_float_year%3Afrom%5D={year_min}&search%5Bfilter_float_year%3Ato%5D={year_max}&search%5Bfilter_float_mileage%3Ato%5D={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="ro-RO,ro;q=0.9,en;q=0.8",
    country="RO",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<article[^>]*data-testid="listing-ad"[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/oferta/|/anunt/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:EUR|€)',
    results_per_page=32,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)

OLX_RO = SearchProfile(
    url_template="{base_url}/auto-masini-moto-ambarcatiuni/autoturisme/q-{make}-{model}/?search%5Bfilter_float_year%3Afrom%5D={year_min}&search%5Bfilter_float_year%3Ato%5D={year_max}&search%5Bfilter_float_milage%3Ato%5D={km_max}&page={page}",
    make_in_url="uppercase",
    model_in_url="raw",
    accept_language="ro-RO,ro;q=0.9",
    country="RO",
    currency="EUR",
    listing_block_re=r'',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/d/oferta/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:EUR|€|lei|RON)',
    results_per_page=40,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — DANIMARCA (DK)
# ═══════════════════════════════════════════════════════════════════════════════

DBA_DK = SearchProfile(
    url_template="{base_url}/biler/model-{model}/reg-{year_min}-{year_max}/km-0-{km_max}/?soeg={make}+{model}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="da-DK,da;q=0.9,en;q=0.8",
    country="DK",
    currency="DKK",
    listing_block_re=r'<tr[^>]*class="[^"]*dbaListing[^"]*"[^>]*>(.*?)</tr>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/id-)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*kr',
    results_per_page=30,
)

BILBASEN_DK = SearchProfile(
    url_template="{base_url}/brugt/bil/{make}/{model}/?YearFrom={year_min}&YearTo={year_max}&MillageFrom=0&MillageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="da-DK,da;q=0.9",
    country="DK",
    currency="DKK",
    listing_block_re=r'<div[^>]*class="[^"]*bb-listing-clickable[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/brugt/bil/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*kr',
    results_per_page=30,
    make_map={"Mercedes": "Mercedes-Benz", "Range Rover": "Land Rover"},
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — SPAGNA (ES)
# ═══════════════════════════════════════════════════════════════════════════════

COCHES_NET = SearchProfile(
    url_template="{base_url}/segunda-mano/?MakeIds={make}&ModelIds={model}&MinYear={year_min}&MaxYear={year_max}&MaxKms={km_max}&pg={page}",
    make_in_url="raw",
    model_in_url="raw",
    accept_language="es-ES,es;q=0.9,en;q=0.8",
    country="ES",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*mt-Card[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/segunda-mano/|/coche/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=30,
    make_map={
        "BMW": "bmw", "Mercedes": "mercedes-benz", "Audi": "audi",
        "Porsche": "porsche", "Range Rover": "land-rover",
    },
)

MILANUNCIOS_ES = SearchProfile(
    url_template="{base_url}/coches-segunda-mano/{make}-{model}.htm?desde={year_min}&hasta={year_max}&kmhasta={km_max}&pagina={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="es-ES,es;q=0.9",
    country="ES",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*ma-AdCard[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/coches-segunda-mano/|/anuncio/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=30,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — PORTOGALLO (PT)
# ═══════════════════════════════════════════════════════════════════════════════

STANDVIRTUAL_PT = SearchProfile(
    url_template="{base_url}/carros/{make}/{model}/?search%5Bfilter_float_year%3Afrom%5D={year_min}&search%5Bfilter_float_year%3Ato%5D={year_max}&search%5Bfilter_float_mileage%3Ato%5D={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="pt-PT,pt;q=0.9,en;q=0.8",
    country="PT",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<article[^>]*data-testid="listing-ad"[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/anuncio/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=32,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — IRLANDA (IE)
# ═══════════════════════════════════════════════════════════════════════════════

DONEDEAL_IE = SearchProfile(
    url_template="{base_url}/cars/{make}/{model}?year_from={year_min}&year_to={year_max}&mileage_to={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="titlecase",
    accept_language="en-IE,en;q=0.9",
    country="IE",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<li[^>]*class="[^"]*card[^"]*"[^>]*>(.*?)</li>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/cars/)[^"\']*\d+)["\']',
    price_re=r'€([\d,]+)',
    results_per_page=30,
    make_map={"Mercedes": "Mercedes-Benz", "Range Rover": "Land Rover"},
)

CARSIRELAND_IE = SearchProfile(
    url_template="{base_url}/used-cars/{make}/{model}/?yearfrom={year_min}&yearto={year_max}&mileageto={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="en-IE,en;q=0.9",
    country="IE",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*car-listing[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/used-cars/)[^"\']*)["\']',
    price_re=r'€([\d,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — GRECIA (GR)
# ═══════════════════════════════════════════════════════════════════════════════

CAR_GR = SearchProfile(
    url_template="{base_url}/used-cars/{make}/{model}.html?lang=en&offer_type=sale&rg_from={year_min}&rg_to={year_max}&ml_to={km_max}&pg={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="el-GR,el;q=0.9,en;q=0.8",
    country="GR",
    currency="EUR",
    listing_block_re=r'<article[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/used-cars/|/classifieds/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=25,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)

XE_GR = SearchProfile(
    # Verified URL pattern from Google index: xe.gr uses /automoto/r/ for search results.
    # BMW X3: https://www.xe.gr/automoto/r/metaxeirismena-aytokinhta-bmw-x3
    # Pattern: /automoto/r/metaxeirismena-aytokinhta-{make_slug}-{model_slug}
    # Alternative /automoto/used-cars-{MAKE},{MODEL}.html also indexed but returns 405.
    # Filter params: site uses JS SPA — additional filters (year, km) require JS rendering.
    # Status: BROKEN — returns 405 on direct fetch, JS-rendered content for filters.
    # The /automoto/r/ slug URL is server-side rendered and may return listings without JS.
    # No confirmed query param structure for year/km — requires Selenium for filtered search.
    url_template="{base_url}/automoto/r/metaxeirismena-aytokinhta-{make_slug}-{model_slug}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="el-GR,el;q=0.9,en;q=0.8",
    country="GR",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*result-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/automoto/d/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=25,
    make_map={
        "BMW": "bmw",
        "Mercedes": "mercedes-benz",
        "Audi": "audi",
        "Porsche": "porsche",
        "Range Rover": "land-rover",
    },
    model_map={
        "BMW": {
            "X3": "x3",
            "X5": "x5",
            "Serie 3": "3",
            "Serie 5": "5",
            "M3": "m3",
        },
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — SLOVENIA (SI)
# ═══════════════════════════════════════════════════════════════════════════════

AVTONET_SI = SearchProfile(
    # Verified: avto.net uses /Ads/results.asp with znamka= (make), model= (model slug),
    # letnikMin= / letnikMax= (year range), kmMax= (km max), stran= (page number).
    # Model for BMW X3 is "serija+X3:" (colon suffix required by avto.net).
    # The old "Brand=", "Model=", "YearFrom=", "KmTo=", "page=" params are WRONG.
    url_template="{base_url}/Ads/results.asp?znamka={make}&model={model}&letnikMin={year_min}&letnikMax={year_max}&kmMax={km_max}&zaloga=10&arhiv=0&stran={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="sl-SI,sl;q=0.9,en;q=0.8",
    country="SI",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*GO-Results-Row[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/Ads/details|/oglas/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=20,
    make_map={
        "BMW": "BMW",
        "Mercedes": "Mercedes-Benz",
        "Audi": "Audi",
        "Range Rover": "Land Rover",
    },
    model_map={
        "BMW": {
            "X3": "serija+X3:",
            "X5": "serija+X5:",
            "Serie 3": "serija+3:",
            "Serie 5": "serija+5:",
        },
    },
)

BOLHA_SI = SearchProfile(
    # bolha.com is actively WAF-blocked (0 bytes response) — confirmed S68.
    # URL structure best guess based on Slovenian classifieds conventions:
    # /avto-moto/osebni-avtomobili/?q={make}+{model} with standard ?page=N pagination.
    # The old path /avto/rabljeni/{make}-{model} likely dead or wrong category.
    # Requires Selenium (JS SPA) or Flaresolverr to bypass Cloudflare WAF.
    # Status: BROKEN — WAF. Fix requires proxy/headless. Low priority (SI, small market).
    url_template="{base_url}/avto-moto/osebni-avtomobili/?q={make}+{model}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="sl-SI,sl;q=0.9",
    country="SI",
    currency="EUR",
    listing_block_re=r'<li[^>]*class="[^"]*EntityList-item[^"]*"[^>]*>(.*?)</li>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/oglas/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=25,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — SLOVACCHIA (SK)
# ═══════════════════════════════════════════════════════════════════════════════

AUTOBAZAR_SK = SearchProfile(
    # Verified: autobazar.eu uses /en/vysledky/ (SUV) or /en/vysledky/osobne-vozidla/ path.
    # BMW X3 is categorized as SUV: /en/vysledky/suv-terenne-vozidla/bmw/x3/
    # Filter params confirmed from trpcState JSON: yearFrom= yearTo= kmTo= page=
    # EN interface available at /en/ prefix.
    # Old Slovak path /inzercia/osobne-auta/ is autobazar.sk subdomain (different URL).
    url_template="{base_url}/en/vysledky/suv-terenne-vozidla/{make}/{model}/?yearFrom={year_min}&yearTo={year_max}&kmTo={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="sk-SK,sk;q=0.9,cs;q=0.8,en;q=0.7",
    country="SK",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*inzerat[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/detail-|/detail/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=20,
    model_map={
        "BMW": {
            "X3": "x3",
            "X5": "x5",
            "Serie 3": "3",
            "Serie 5": "5",
            "M3": "m3",
        },
        "Mercedes": {
            "GLC": "glc",
            "GLE": "gle",
            "Classe C": "c",
            "Classe E": "e",
        },
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — BALTICI (EE/LV/LT)
# ═══════════════════════════════════════════════════════════════════════════════

AUTO24_EE = SearchProfile(
    # auto24.ee uses numeric IDs: b=brand_id, bw=model_id
    # BMW=4, X3=809, X5=69, Serie 3=68, Serie 5=70
    url_template="{base_url}/kasutatud/nimekiri.php?bn=2&a=100&ae=2&af={year_min}&at={year_max}&b={make}&bw={model}&ak={page}",
    make_in_url="raw",
    model_in_url="raw",
    accept_language="et-EE,et;q=0.9,en;q=0.8",
    country="EE",
    currency="EUR",
    listing_block_re=r'class="result-row[^"]*"[^>]*>(.{100,5000}?)(?=class="result-row|$)',
    url_re=r'<a[^>]+href="(/soidukid/\d+)"',
    price_re=r'class="price">([\d\s.,]+)',
    year_re=r'class="year">(\d{4})<',
    results_per_page=20,
    make_map={
        "BMW": "4", "Mercedes": "57", "Audi": "3", "Porsche": "76",
        "Range Rover": "49", "Land Rover": "49", "Lamborghini": "48",
        "Ferrari": "26", "McLaren": "111",
    },
    model_map={
        "BMW": {"X3": "809", "X1": "808", "X5": "69", "Serie 3": "68", "Serie 5": "70", "M3": "1003", "M4": "1197"},
        "Audi": {"Q3": "1070", "Q5": "900", "Q7": "536", "A3": "44", "A4": "45", "A5": "535", "A6": "46"},
    },
)

SS_LV = SearchProfile(
    url_template="{base_url}/lv/transport/cars/{make}/{model}/sell/?topt%5B8%5D%5Bmin%5D={year_min}&topt%5B8%5D%5Bmax%5D={year_max}&topt%5B15%5D%5Bmax%5D={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="lv-LV,lv;q=0.9,en;q=0.8",
    country="LV",
    currency="EUR",
    listing_block_re=r'<tr[^>]*class="[^"]*msg[^"]*"[^>]*>(.*?)</tr>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/msg/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=30,
)

AUTOPLIUS_LT = SearchProfile(
    url_template="{base_url}/skelbimai/naudoti-automobiliai/{make}/{model}?year_from={year_min}&year_to={year_max}&km_to={km_max}&page_nr={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="lt-LT,lt;q=0.9,en;q=0.8",
    country="LT",
    currency="EUR",
    listing_block_re=r'',
    url_re=r'href="(https://autoplius\.lt/skelbimai/[^"]*-\d+\.html)"',
    price_re=r'data-amount="(\d+)"',
    year_re=r'<span>(\d{4})-\d{2}</span>',
    results_per_page=20,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — BULGARIA (BG)
# ═══════════════════════════════════════════════════════════════════════════════

MOBILE_BG = SearchProfile(
    url_template="{base_url}/obiavi/avtomobili-dzhipove/{make}/{model}/p-{page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="bg-BG,bg;q=0.9,en;q=0.8",
    country="BG",
    currency="EUR",
    # mobile.bg uses windows-1251 encoding — Cyrillic garbled but structure intact
    # Listing block: <div class="item TOP " id="ida{id}">...</div></div></div></div>
    # Price in: <div class="price ..."><div>3 250 €</div>
    # URL: //www.mobile.bg/obiava-{id}-{slug}
    listing_block_re=r'id="ida\d+"[^>]*>(.{200,5000}?)</div>\s*</div>\s*</div>\s*</div>',
    url_re=r'href="((?:https?:)?//(?:www\.)?mobile\.bg/obiava-\d+[^"]*)"',
    price_re=r'class="price[^"]*"[^>]*>\s*<div>([\d\s.,]+)',
    title_re=r'class="title[^"]*"[^>]*>([^<]+)</a>',
    # km extraction: windows-1251 encoding makes Cyrillic unreadable but numbers survive
    # Pattern matches "123 456 km" or digits followed by "km" in params spans
    km_re=r'(\d[\d\s.]+)\s*km',
    results_per_page=20,
)

CARS_BG = SearchProfile(
    url_template="{base_url}/offer/search/?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&kmTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="bg-BG,bg;q=0.9",
    country="BG",
    currency="BGN",
    listing_block_re=r'<div[^>]*class="[^"]*offer-item[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/offer/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:лв|BGN|EUR|€)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — CROAZIA (HR)
# ═══════════════════════════════════════════════════════════════════════════════

NJUSKALO_HR = SearchProfile(
    url_template="{base_url}/auti/{make}-{model}?godisteOd={year_min}&godisteDo={year_max}&kmDo={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="hr-HR,hr;q=0.9,en;q=0.8",
    country="HR",
    currency="EUR",
    listing_block_re=r'<article[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*oglas-\d+[^"\']*)["\']',
    price_re=r'([\d.]+)\s*€',
    km_re=r'([\d.,]+)\s*km',
    year_re=r'(\d{1,2}/\d{4}|\b20[12]\d\b)',
    results_per_page=25,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — FINLANDIA (FI)
# ═══════════════════════════════════════════════════════════════════════════════

NETTIAUTO_FI = SearchProfile(
    url_template="{base_url}/{make}/{model}?vuosimalliMin={year_min}&vuosimalliMax={year_max}&kmMax={km_max}&sivu={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    accept_language="fi-FI,fi;q=0.9,en;q=0.8",
    country="FI",
    currency="EUR",
    uses_json_ld=True,
    listing_block_re=r'<div[^>]*class="[^"]*list_element[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vaihtoauto/|/auto/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=32,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — LUSSEMBURGO (LU)
# ═══════════════════════════════════════════════════════════════════════════════

ANZEIGER_LU = SearchProfile(
    url_template="{base_url}/search?category=auto&q={make}+{model}&yearMin={year_min}&yearMax={year_max}&kmMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="fr-LU,fr;q=0.9,de;q=0.8,en;q=0.7",
    country="LU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*listing[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auto/|/annonce/)[^"\']*)["\']',
    price_re=r'([\d.,]+)\s*€',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEDS — NORVEGIA (NO)
# ═══════════════════════════════════════════════════════════════════════════════

FINN_NO = SearchProfile(
    url_template="{base_url}/car/used/search.html?make={make}&model={model}&year_from={year_min}&year_to={year_max}&mileage_to={km_max}&page={page}",
    make_in_url="raw",
    model_in_url="raw",
    accept_language="nb-NO,nb;q=0.9,no;q=0.8,en;q=0.7",
    country="NO",
    currency="NOK",
    uses_next_data=True,
    listing_block_re=r'<article[^>]*class="[^"]*ads__unit[^"]*"[^>]*>(.*?)</article>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/car/used/ad/|/finnkode=)[^"\']*)["\']',
    price_re=r'([\d\s]+)\s*kr',
    results_per_page=50,
    make_map={
        "BMW": "0.744", "Mercedes": "0.746", "Audi": "0.743",
        "Porsche": "0.789", "Range Rover": "0.779", "Land Rover": "0.779",
    },
)


# ═══════════════════════════════════════════════════════════════════════════════
# ASTE B2B + FLEET — PAN-EU
# ═══════════════════════════════════════════════════════════════════════════════

OPENLANE_EU = SearchProfile(
    url_template="{base_url}/vehicles?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-card[^"]*"[^>]*>(.*?)</div>\s*</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/lot/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

BCA_EU = SearchProfile(
    url_template="{base_url}/buyer/search/?make={make}&model={model}&regYearFrom={year_min}&regYearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*lot-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/lot/|/vehicle/)[^"\']*)["\']',
    price_re=r'(?:€|GBP)\s*([\d.,]+)',
    results_per_page=20,
)

AUTOROLA_EU = SearchProfile(
    url_template="{base_url}/auction/search?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&kmTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auction-item[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auction/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

MANHEIM_EXPRESS_EU = SearchProfile(
    url_template="{base_url}/search?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&maxKm={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-tile[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/lot/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# ASTE NAZIONALI
# ═══════════════════════════════════════════════════════════════════════════════

CARONSALE_DE = SearchProfile(
    url_template="{base_url}/de/auctions?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&maxMileage={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="de-DE,de;q=0.9,en;q=0.8",
    country="DE",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auction-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auction/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

AUTOBID_DE = SearchProfile(
    url_template="{base_url}/de/suche/?brand={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&kmTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="de-DE,de;q=0.9",
    country="DE",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*car-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auction/|/fahrzeug/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

ECARSTRADE_EU = SearchProfile(
    url_template="{base_url}/used-cars?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*class="[^"]*car-tile[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/used-cars/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

AUTOPROFF_EU = SearchProfile(
    url_template="{base_url}/search?make={make}&model={model}&yearMin={year_min}&yearMax={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/car/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*(?:kr|SEK|DKK|€|EUR)',
    results_per_page=20,
)

KVDCARS_SE = SearchProfile(
    url_template="{base_url}/auctions?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="sv-SE,sv;q=0.9,en;q=0.8",
    country="SE",
    currency="SEK",
    listing_block_re=r'<div[^>]*class="[^"]*auction-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auction/|/object/)[^"\']*)["\']',
    price_re=r'([\d\s]+)\s*kr',
    results_per_page=20,
)

VPAUTO_FR = SearchProfile(
    url_template="{base_url}/voitures?marque={make}&modele={model}&annee_min={year_min}&annee_max={year_max}&km_max={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="fr-FR,fr;q=0.9",
    country="FR",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*lot-item[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/lot/|/enchere/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=20,
)

ALCOPA_FR = SearchProfile(
    url_template="{base_url}/en/search?brand={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&kmMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="fr-FR,fr;q=0.9,en;q=0.8",
    country="FR",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auction-lot[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/lot/|/auction/)[^"\']*)["\']',
    price_re=r'([\d\s.,]+)\s*€',
    results_per_page=20,
)

VWE_NL = SearchProfile(
    url_template="{base_url}/zoeken/?merk={make}&model={model}&bouwjaar_van={year_min}&bouwjaar_tot={year_max}&km_tot={km_max}&pagina={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="nl-NL,nl;q=0.9",
    country="NL",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auto-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auto/|/voertuig/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FLEET REMARKETING
# ═══════════════════════════════════════════════════════════════════════════════

AYVENS_CARMARKET = SearchProfile(
    url_template="{base_url}/vehicles?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&maxKm={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

ARVAL_MOTORTRADE = SearchProfile(
    url_template="{base_url}/search?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*car-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

ATHLON_CARPLAZA = SearchProfile(
    url_template="{base_url}/auto/zoeken?merk={make}&model={model}&bouwjaar_van={year_min}&bouwjaar_tot={year_max}&km_tot={km_max}&pagina={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="nl-NL,nl;q=0.9,en;q=0.8",
    country="NL",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auto-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auto/|/aanbod/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

EXLEASINGCAR_EU = SearchProfile(
    url_template="{base_url}/vehicles?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageMax={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*vehicle-item[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/vehicle/|/car/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM + LUXURY
# ═══════════════════════════════════════════════════════════════════════════════

ELFERSPOT_EU = SearchProfile(
    url_template="{base_url}/offers/?brand=Porsche&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="raw",  # Always Porsche
    model_in_url="raw",
    accept_language="en-US,en;q=0.9,de;q=0.8",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*offer-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/offer/|/listing/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

JAMESEDITION_EU = SearchProfile(
    url_template="{base_url}/cars/{make}/{model}?year_min={year_min}&year_max={year_max}&mileage_max={km_max}&page={page}",
    make_in_url="lowercase",
    model_in_url="lowercase",
    slug_separator="-",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    uses_next_data=True,
    listing_block_re=r'<div[^>]*class="[^"]*listing-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/cars/|/listing/)[^"\']*)["\']',
    price_re=r'(?:€|EUR|USD)\s*([\d,]+)',
    results_per_page=20,
    make_map={"Mercedes": "mercedes-benz", "Range Rover": "land-rover"},
)

COLLECTING_CARS_EU = SearchProfile(
    url_template="{base_url}/search?q={make}+{model}&year_min={year_min}&year_max={year_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auction-card[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/lots/|/auction/)[^"\']*)["\']',
    price_re=r'(?:€|£|GBP|EUR)\s*([\d,]+)',
    results_per_page=20,
)

CLASSIC_DRIVER_EU = SearchProfile(
    url_template="{base_url}/en/cars?make={make}&model={model}&yearFrom={year_min}&yearTo={year_max}&mileageTo={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*result-listing[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/car/|/listing/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)

BAT_EU = SearchProfile(
    url_template="{base_url}/auctions/search?q={make}+{model}&yearFrom={year_min}&yearTo={year_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="en-US,en;q=0.9",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*auction-item[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/listing/|/auction/)[^"\']*)["\']',
    price_re=r'\$([\d,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATORI + INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

AUTOUNCLE_EU = SearchProfile(
    url_template="{base_url}/it/ricerca-auto?make={make}&model={model}&year_min={year_min}&year_max={year_max}&km_max={km_max}&page={page}",
    make_in_url="titlecase",
    model_in_url="raw",
    accept_language="it-IT,it;q=0.9,en;q=0.8",
    country="EU",
    currency="EUR",
    listing_block_re=r'<div[^>]*class="[^"]*listing[^"]*"[^>]*>(.*?)</div>',
    url_re=r'<a[^>]+href=["\']([^"\']*(?:/auto-usate/|/used-cars/)[^"\']*)["\']',
    price_re=r'€\s*([\d.,]+)',
    results_per_page=20,
)


# ═══════════════════════════════════════════════════════════════════════════════
# MASTER REGISTRY — portal_key → SearchProfile
# ═══════════════════════════════════════════════════════════════════════════════

PROFILES: dict[str, SearchProfile] = {
    # DE Classifieds
    "kleinanzeigen_de": KLEINANZEIGEN_DE,
    "pkw_de": PKW_DE,
    "auto_de": AUTO_DE,
    # NL
    "marktplaats_nl": MARKTPLAATS_NL,
    "autotrack_nl": AUTOTRACK_NL,
    # BE
    "2dehands_be": TWEEDEHANDS_BE,
    # AT
    "willhaben_at": WILLHABEN_AT,
    "gebrauchtwagen_at": GEBRAUCHTWAGEN_AT,
    "autorevue_at": AUTOREVUE_AT,
    # FR
    "leboncoin_fr": LEBONCOIN_FR,
    "largus_fr": LARGUS_FR,
    "lacentrale_fr": LACENTRALE_FR,
    # SE
    "blocket_se": BLOCKET_SE,
    "bytbil_se": BYTBIL_SE,
    # CZ
    "sauto_cz": SAUTO_CZ,
    "bazos_cz": BAZOS_CZ,
    "inzerce_auto_cz": INZERCE_AUTO_CZ,
    # PL
    "otomoto_pl": OTOMOTO_PL,
    "olx_pl": OLX_PL,
    # HU
    "hasznaltauto_hu": HASZNALTAUTO_HU,
    # RO
    "autovit_ro": AUTOVIT_RO,
    "olx_ro": OLX_RO,
    # DK
    "dba_dk": DBA_DK,
    "bilbasen_dk": BILBASEN_DK,
    # ES
    "coches_net": COCHES_NET,
    "milanuncios_es": MILANUNCIOS_ES,
    # PT
    "standvirtual_pt": STANDVIRTUAL_PT,
    # IE
    "donedeal_ie": DONEDEAL_IE,
    "carsireland_ie": CARSIRELAND_IE,
    # GR
    "car_gr": CAR_GR,
    "xe_gr": XE_GR,
    # SI
    "avtonet_si": AVTONET_SI,
    "bolha_si": BOLHA_SI,
    # SK
    "autobazar_sk": AUTOBAZAR_SK,
    # EE/LV/LT
    "auto24_ee": AUTO24_EE,
    "ss_lv": SS_LV,
    "autoplius_lt": AUTOPLIUS_LT,
    # BG
    "mobile_bg": MOBILE_BG,
    "cars_bg": CARS_BG,
    # HR
    "njuskalo_hr": NJUSKALO_HR,
    # FI
    "nettiauto_fi": NETTIAUTO_FI,
    # LU
    "anzeiger_lu": ANZEIGER_LU,
    # NO
    "finn_no": FINN_NO,
    # Aste B2B pan-EU
    "openlane_eu": OPENLANE_EU,
    "bca_eu": BCA_EU,
    "autorola_eu": AUTOROLA_EU,
    "manheim_express_eu": MANHEIM_EXPRESS_EU,
    # Aste nazionali
    "caronsale_de": CARONSALE_DE,
    "autobid_de": AUTOBID_DE,
    "ecarstrade_eu": ECARSTRADE_EU,
    "autoproff_eu": AUTOPROFF_EU,
    "kvdcars_se": KVDCARS_SE,
    "vpauto_fr": VPAUTO_FR,
    "alcopa_fr": ALCOPA_FR,
    "vwe_nl": VWE_NL,
    # Fleet remarketing
    "ayvens_carmarket": AYVENS_CARMARKET,
    "arval_motortrade": ARVAL_MOTORTRADE,
    "athlon_carplaza": ATHLON_CARPLAZA,
    "exleasingcar_eu": EXLEASINGCAR_EU,
    # Premium + Luxury
    "elferspot_eu": ELFERSPOT_EU,
    "jamesedition_eu": JAMESEDITION_EU,
    "collecting_cars_eu": COLLECTING_CARS_EU,
    "classic_driver_eu": CLASSIC_DRIVER_EU,
    "bat_eu": BAT_EU,
    # Aggregatori
    "autouncle_eu": AUTOUNCLE_EU,
}
