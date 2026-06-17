# BRIEF C — MONITOR FONTI SOURCING B2B (settimanale, ampliabile). CC Max nativo. system python3.
# OBIETTIVO: lista CHIARA/DEFINITA/AMPLIABILE delle fonti dove ARGOS trova i deal migliori + script weekly.
#
# config/sourcing_sources.yaml — SEED (verificati esistere, web giu-2026), AMPLIABILE:
#   wholesale_b2b: auto1.com, caronsale.com, bca-europe.com, autoproff.it, autobid.de
#   italiane_b2b: autoinrete, eschini-b2bid
#   aste_giudiziarie: astagiudiziaria.com (IVG, beni mobili=veicoli), pvp.giustizia.it
#   Ogni voce: {nome, url, tipo, copre_veicoli: si/no/DA_VERIFICARE, accesso, ha_api: si/no/DA_VERIFICARE}
#
# tools/research/monitor_sources.py (run settimanale, cron o manuale)
#   Per ogni fonte: verifica raggiungibilita'; dove possibile (API/feed/HTML) conta veicoli nel segmento target
#   + flagga voci [DA_VERIFICARE] ancora aperte. NON inventare endpoint (lezione BDAG): se l'accesso non e'
#   confermato, resta DA_VERIFICARE con la domanda esatta da chiudere. → report/sourcing_weekly_<data>.md (delta vs scorsa).
#
# AMPLIAMENTO: il yaml e' la single-source. Aggiungere una fonte = 1 riga nel yaml; lo script la include al run dopo.
#   Nessun hardcode nel codice. Verifica: report generato, voci DA_VERIFICARE elencate, delta calcolato.
