# BRIEF A — E2E REALE: scraper→dossier→AMBRA parla. TEST_FOUNDER 39<TEST_FOUNDER_NUM>. CC Max. system python3.
# PREREQ [A0] (scoperto S280, NON saltare): WA daemon connesso (NON `initializing`) + orario lavorativo +
#   Luke fisico sulla SIM. Se daemon = initializing/qr_available:false → prima [A0] wa-daemon-ops (area S252).
# PRECONDIZIONE: ambra_voice_profile.md prodotto (BRIEF B) + integrato in response-analyzer.py.
# MAI dealer reale — solo TEST_FOUNDER.
# 1. Scraper AS24 → seleziona 1 veicolo reale (config esatta, pool experiment-OFF, geo==IT).
# 2. Dossier onesto: banda p25-p75 (NON punto), margine INTERVALLO, fonte etichettata "prezzi richiesti".
# 3. AMBRA genera il messaggio Day-1 CON la voce nuova (lessico dal profilo) + disclosure Azzurra
#    assistente di Luca + provenienza contatto + opt-out.
# 4. RENDER verificato (pypdf/lettura reale): firma Azzurra (NO "Luca" 1a persona), disclosure presente,
#    numeri = banda NON punto, grep superlativi = 0.
# 5. Invio a TEST_FOUNDER via Gate-E (classe outreach_real → BLOCCA → packet → approve Luke).
# 6. MOSTRA l'output reale: il messaggio che AMBRA manda, letto dal render — NON descritto.
# NB: PDF test usa base-mercato non-fidata (gate-3 [D]) → test di MECCANICA+RENDER, NON dei numeri.
# Questo PROVA "AMBRA parla ed e' credibile" sull'artefatto. Prima volta che la pipeline d'invio gira E2E.
#
# ─── CHECKLIST "VERDE" (gate qualitativo "Luke soddisfatto" = 7 punti spuntati sull'artefatto REALE) ───
#  1. Firma = "Assistente di Luca Ferretti" / Azzurra — MAI "Luca" in 1a persona, in nessun punto del msg.
#  2. Disclosure presente: AMBRA dichiara di essere automatica se il contesto lo richiede; non devia, non nega.
#  3. Numeri = banda p25-p75 (NON punto); margine = intervallo/tetto condizionato, MAI "≈€X netti garantiti".
#  4. Provenienza contatto + opt-out presenti nel messaggio.
#  5. Zero superlativi: grep "eccezion|migliore|unico|best|top|garantito" sull'output = 0.
#  6. RENDER letto, non descritto: punti 1-5 verificati LEGGENDO l'output reale (pypdf / messaggio generato),
#     non riferiti da CC a parole. Lezione statico-vs-render: il bundle Azzurra e' chiuso nei literal,
#     [A] e' la prima prova che atterra nell'OUTPUT generato.
#  7a. MECCANICA D'INVIO — Day-1 consegnato a TEST_FOUNDER 39<TEST_FOUNDER_NUM>: HTTP 200 + msg_id reale.
#      STATO: VERDE (commit 40a5d1e · msg_id out_1781986351333_evd8h = fatto terminale).
#  7b. BREAKER VIVO — Gate-E blocca outreach_real su numero NON-whitelist (deny→packet→approve→consume),
#      a vuoto, ZERO invio. STATO: DEFERITO a gate-pre-dealer-reale (è già nei 3 gate a dealer reale) —
#      NON è done-condition di [A1].
#  NB SPLIT (referto forense S285): il punto 7 monolitico ("invio passato per Gate-E") era INSODDISFACIBILE
#     su TEST_FOUNDER perché gate_e.py whitelista 39<TEST_FOUNDER_NUM> (gate_e.py:37,349 · commit 40a5d1e) → su
#     TEST_FOUNDER il breaker NON scatta by design; esercitarlo richiede un numero non-whitelist = dealer reale.
#  → punti 1-6 + 7a verdi sull'artefatto reale, 7b deferito = [A]/[A1] verde CON CRITERIO (non a occhio).
