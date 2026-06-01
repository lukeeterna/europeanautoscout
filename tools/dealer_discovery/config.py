"""
ARGOS Dealer Discovery — Configurazione province target e segnali commissione
"""

# Province target TUTTA ITALIA — ordinate per priorita'
# P1: Sud core (family business premium, territorio vuoto)
# P2: Sud esteso + Sicilia/Sardegna
# P3: Centro Italia
# P4: Nord Italia (piu' competitivo ma volume alto)
PROVINCE_TARGET = [
    # ── PRIORITA' 1: Sud core (territorio vuoto, family business) ──
    {"province": "foggia", "region": "puglia", "priority": 1},
    {"province": "caserta", "region": "campania", "priority": 1},
    {"province": "cosenza", "region": "calabria", "priority": 1},
    {"province": "avellino", "region": "campania", "priority": 1},
    {"province": "lecce", "region": "puglia", "priority": 1},
    {"province": "taranto", "region": "puglia", "priority": 1},
    {"province": "salerno", "region": "campania", "priority": 1},
    # ── PRIORITA' 2: Sud esteso + Isole ──
    {"province": "catanzaro", "region": "calabria", "priority": 2},
    {"province": "bari", "region": "puglia", "priority": 2},
    {"province": "benevento", "region": "campania", "priority": 2},
    {"province": "potenza", "region": "basilicata", "priority": 2},
    {"province": "crotone", "region": "calabria", "priority": 2},
    {"province": "reggio-calabria", "region": "calabria", "priority": 2},
    {"province": "napoli", "region": "campania", "priority": 2},
    {"province": "brindisi", "region": "puglia", "priority": 2},
    {"province": "matera", "region": "basilicata", "priority": 2},
    {"province": "catania", "region": "sicilia", "priority": 2},
    {"province": "palermo", "region": "sicilia", "priority": 2},
    {"province": "messina", "region": "sicilia", "priority": 2},
    {"province": "siracusa", "region": "sicilia", "priority": 2},
    {"province": "cagliari", "region": "sardegna", "priority": 2},
    {"province": "sassari", "region": "sardegna", "priority": 2},
    {"province": "vibo-valentia", "region": "calabria", "priority": 2},
    # ── PRIORITA' 3: Centro Italia ──
    {"province": "roma", "region": "lazio", "priority": 3},
    {"province": "frosinone", "region": "lazio", "priority": 3},
    {"province": "latina", "region": "lazio", "priority": 3},
    {"province": "rieti", "region": "lazio", "priority": 3},
    {"province": "viterbo", "region": "lazio", "priority": 3},
    {"province": "perugia", "region": "umbria", "priority": 3},
    {"province": "terni", "region": "umbria", "priority": 3},
    {"province": "pescara", "region": "abruzzo", "priority": 3},
    {"province": "chieti", "region": "abruzzo", "priority": 3},
    {"province": "teramo", "region": "abruzzo", "priority": 3},
    {"province": "l-aquila", "region": "abruzzo", "priority": 3},
    {"province": "campobasso", "region": "molise", "priority": 3},
    {"province": "isernia", "region": "molise", "priority": 3},
    {"province": "firenze", "region": "toscana", "priority": 3},
    {"province": "arezzo", "region": "toscana", "priority": 3},
    {"province": "siena", "region": "toscana", "priority": 3},
    {"province": "grosseto", "region": "toscana", "priority": 3},
    {"province": "ancona", "region": "marche", "priority": 3},
    {"province": "pesaro-urbino", "region": "marche", "priority": 3},
    {"province": "macerata", "region": "marche", "priority": 3},
    # ── PRIORITA' 4: Nord Italia (competitivo, volume alto) ──
    {"province": "milano", "region": "lombardia", "priority": 4},
    {"province": "brescia", "region": "lombardia", "priority": 4},
    {"province": "bergamo", "region": "lombardia", "priority": 4},
    {"province": "monza-e-della-brianza", "region": "lombardia", "priority": 4},
    {"province": "varese", "region": "lombardia", "priority": 4},
    {"province": "torino", "region": "piemonte", "priority": 4},
    {"province": "cuneo", "region": "piemonte", "priority": 4},
    {"province": "verona", "region": "veneto", "priority": 4},
    {"province": "padova", "region": "veneto", "priority": 4},
    {"province": "treviso", "region": "veneto", "priority": 4},
    {"province": "vicenza", "region": "veneto", "priority": 4},
    {"province": "bologna", "region": "emilia-romagna", "priority": 4},
    {"province": "modena", "region": "emilia-romagna", "priority": 4},
    {"province": "parma", "region": "emilia-romagna", "priority": 4},
    {"province": "reggio-emilia", "region": "emilia-romagna", "priority": 4},
    {"province": "trento", "region": "trentino-alto-adige", "priority": 4},
    {"province": "bolzano", "region": "trentino-alto-adige", "priority": 4},
    {"province": "genova", "region": "liguria", "priority": 4},
    {"province": "udine", "region": "friuli-venezia-giulia", "priority": 4},
    {"province": "trieste", "region": "friuli-venezia-giulia", "priority": 4},
]

# Segnali che indicano dealer "su commissione"
COMMISSION_KEYWORDS = [
    "su richiesta", "cerchiamo", "troviamo", "su ordinazione",
    "a richiesta", "ricerchiamo per voi", "il veicolo che cerchi",
    "ricerca personalizzata", "auto su misura", "procuriamo",
    "la tua auto ideale", "cerchi un'auto", "trovare l'auto",
    "su commissione", "conto vendita",
]

# Marche premium ARGOS
PREMIUM_BRANDS = [
    "BMW", "Mercedes", "Mercedes-Benz", "Audi", "Porsche",
    "Lamborghini", "Ferrari", "McLaren", "Range Rover", "Land Rover",
    "Maserati", "Jaguar", "Volvo", "Lexus", "Alfa Romeo",
]

# Score segnali commissione
COMMISSION_SCORING = {
    "few_listings_min": 3,
    "few_listings_max": 15,
    "brand_diversity_min": 4,        # >= 4 marche diverse = eterogeneo
    "keyword_match_weight": 3.0,     # peso per keyword "su richiesta"
    "few_listings_weight": 2.0,      # peso per pochi annunci
    "brand_diversity_weight": 2.0,   # peso per marche diverse
    "premium_presence_weight": 1.5,  # peso per presenza premium
    "low_reviews_weight": 1.0,       # peso per poche recensioni (< 30)
    "threshold_commission": 5.0,     # score minimo per classificare "commissione"
    "threshold_fit_argos": 7.0,      # score minimo per fit ARGOS
}

# Rate limiting
RATE_LIMIT = {
    "subito_delay_min": 5,
    "subito_delay_max": 12,
    "as24_delay_min": 5,
    "as24_delay_max": 10,
    "gmaps_delay_min": 8,
    "gmaps_delay_max": 18,
}
