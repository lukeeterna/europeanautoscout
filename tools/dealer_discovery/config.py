"""
ARGOS Dealer Discovery — Configurazione province target e segnali commissione
"""

# Province target Sud Italia — ordinate per priorita'
PROVINCE_TARGET = [
    {"province": "foggia", "region": "puglia", "priority": 1},
    {"province": "caserta", "region": "campania", "priority": 1},
    {"province": "cosenza", "region": "calabria", "priority": 1},
    {"province": "avellino", "region": "campania", "priority": 2},
    {"province": "lecce", "region": "puglia", "priority": 2},
    {"province": "taranto", "region": "puglia", "priority": 2},
    {"province": "salerno", "region": "campania", "priority": 2},
    {"province": "catanzaro", "region": "calabria", "priority": 2},
    {"province": "bari", "region": "puglia", "priority": 3},
    {"province": "benevento", "region": "campania", "priority": 3},
    {"province": "potenza", "region": "basilicata", "priority": 3},
    {"province": "crotone", "region": "calabria", "priority": 3},
    {"province": "reggio-calabria", "region": "calabria", "priority": 3},
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
