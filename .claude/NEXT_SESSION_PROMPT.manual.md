# BRIEF CC — ARGOS · Sessione S264 (IDEMPOTENTE) — DE-GATE FETCH PROFONDO IT + RERUN PROBE
# Obiettivo: sbloccare la paginazione profonda su AS24.it (path Selenium GIA' ESISTENTE, oggi gated) e ri-eseguire il probe S263 identico.
# NON-obiettivo: nessuna infra nuova (no proxy/stealth/retry-framework), nessun ridisegno del verdetto, nessuna ratifica forzata.
# Progetto: /Users/macbook/Documents/combaretrovamiauto-enterprise (MacBook locale, macOS Big Sur)
# Branch: s210/audit-master-plan
# Autorita': Luke. Autonomia tecnica piena. NESSUNA azione esterna.
# Fonte di verita': PLAN.md + STATE.md + git.

> EREDITATO DA S263 (verificato, non assunto):
> - Anello PDF CHIUSO (S262, commit 9fb7824). Probe S263 = ESITO C: muro = scraper, NON mercato.
> - AS24.it JS-rendered: curl_cffi vede SOLO pagina-1 SSR (~19 listing). Famiglie esatte 0 a L0/L1.
> - Path Selenium profondo ESISTE (`autoscout_scraper.py:1250`, cap 5 pagine) ma gated su zero-data
>   (`autoscout_scraper.py:1227-1228`: scatta solo se >=80% listing con price==0 AND km==0).
> - Report: `.claude/REPORT_S263.md`. Probe identico riusabile: `tools/_s263_probe.py` (NON eliminato).

## INQUADRAMENTO — L'ESITO E' PARZIALE PER COSTRUZIONE (non saltarlo)
Il fallback Selenium e' cappato a 5 pagine (`min(max_pages,5)`). Il rerun porta ~19 -> ~100-150 listing,
NON "tutto il mercato".
Conseguenza da ACCETTARE PRIMA di partire, non da scoprire a meta':
- Famiglie LIQUIDE (320d, 318d): 100-150 listing probabilmente BASTANO. Se a L0/L1 raccolgono N>=8
  -> Esito A per quella famiglia, CHIUSO.
- Famiglie THIN (M340, forse 330i): 5 pagine quasi certamente NON bastano. Se restano 0-2, NON e'
  dimostrato "mercato non le contiene" -> e' "5 pagine non bastano". Resta ambiguo, ed e' OK.
DoD NON e' "deciso A vs B". E': "deciso A vs B PER LE LIQUIDE; per le thin, misurato il meglio che
5 pagine danno e NOMINATO se serve andare oltre". Chiamare "deciso" cio' che 5 pagine non possono
decidere = disonesto.

## REGOLE DI ESECUZIONE (idempotenza)
- Sicuro da rieseguire: nessun doppio effetto.
- NON delegare a subagent (S258). Main context, output reddiretto su file (`> /tmp/s264.txt 2>&1`, leggi tail/grep).
- Converge su OUTPUT definito (tabella per-famiglia + esito nominato). Se gia' prodotto in rerun -> riportalo e FERMATI.
- Source-of-truth (STATE.md/PLAN.md): solo diff-first, mostra il diff a Luke prima di scrivere.
  NB: Gate E blocca Write/Edit/cp su SOT (e da' FP anche sul backup `cp STATE.md` per match-su-nome).
  Tieni l'edit STATE.md come ULTIMO passo, diff-first, e lascia a Luke il token `approve` se serve.

## FASE 0 — GROUND TRUTH (sola lettura)
a) `git rev-parse --show-toplevel` + branch corretti.
b) Conferma la RIGA REALE del gating zero-data: `autoscout_scraper.py:1227-1228`
   (`zero_data = sum(... price_eur==0 and km==0)`; `if zero_data < len*0.8: return listings`).
   Se non combacia col report S263 -> NON modificare a memoria: riporta la condizione reale e adatta.
c) Conferma che `tools/_s263_probe.py` esiste ed e' rieseguibile identico.
Solo dopo a-c si procede.

## FASE 1 — DE-GATE (cambio minimo, componente esistente)
Obiettivo: il deep-fetch Selenium (fino a 5 pagine) deve scattare per il caso IT ANCHE quando i
listing hanno dati validi — non solo sul trigger zero-data.
- Modifica MINIMA: aggiungi una condizione che attiva il path profondo per `autoscout24_it`
  a prescindere dal trigger zero-data (es. flag esplicito `deep_fetch=True` per la sorgente IT,
  o condizione equivalente sulla riga reale di FASE 0).
- NON rimuovere il trigger zero-data esistente: AGGIUNGI un secondo motivo di attivazione, non sostituire.
- NON toccare altro in base_scraper/autoscout_scraper oltre questa attivazione. Niente refactor opportunistici.
- Reversibilita': backup del file prima dell'edit (Rule 1d). [il file scraper NON e' SOT -> niente Gate E qui]
VERIFICA FASE 1 (terminal fact, non "compila"): una scrape live di prova su Serie 3 IT deve restituire
>19 listing (prova che il deep-fetch ora scatta). Incolla il conteggio reale di pagine fetchate e
listing totali. Se resta a 1 pagina/19 -> de-gate NON ha funzionato: FERMATI e diagnostica, non proseguire.

## FASE 2 — RERUN PROBE IDENTICO
- `python3 -m tools._s263_probe` (stesso identico probe, zero modifiche alla logica di conteggio).
- Stesse 4 famiglie, stesse chiavi gate (`derive_trim_family` + `_match` L0->L3), stessa regola:
  DEDUP per `listing_id` (VIN assente nel SSR AS24.it) + RI-FILTRO col gate. Conta SOLO listing
  distinti validati dal gate, non righe di pagina.
- NB: il probe oggi fa UNA scrape (anno+-2). Per la traiettoria N-per-pagina (vedi sotto) potrebbe
  servire loggare il conteggio per pagina: aggiungilo SOLO come print nel probe throwaway, non in produzione.
- Riporta SEMPRE per famiglia: grezzi totali, dopo-dedup, N validati per livello L0->L3, e a quale
  livello (se mai) tocca N>=8.

## OUTPUT (fatto terminale)
Tabella per famiglia:
  FAMIGLIA | pagine_fetchate | grezzi | dedup | L0 L1 L2 L3 | N>=8 a quale livello
Piu' la riga di esito per famiglia (A deciso / thin-ambiguo / misto), NON un giudizio aggregato unico.

## DECISIONE (nomina, NON eseguire design)
- Famiglia LIQUIDA che tocca N>=8 a L0/L1 -> Esito A per quella famiglia: mediana puntuale regge li'.
- Famiglia THIN che resta 0-2 dopo 5 pagine -> NON dichiarare "mercato thin": dichiara "indeciso a
  5 pagine, servirebbe profondita' >5 per decidere". E' un dato, non un fallimento.
- Esito complessivo atteso = MISTO o PARZIALE. Porta i NUMERI a Luke. Il design del verdetto (mediana
  dove regge / bande dove e' thin) lo decide Luke sui numeri, NON CC in sessione.
- "Conta, non interpretare": riporta i numeri, la lettura strategica la fa Luke.

## min_n — RATIFICA SOLO SE I DATI LO PERMETTONO
- Se le liquide producono una distribuzione N reale (non corrotta dal muro) -> PROPONI min_n
  difendibile dai loro numeri, Luke ratifica.
- Se anche post-de-gate i numeri restano near-zero ovunque -> min_n resta PARCHEGGIATO, e questo
  stesso e' un segnale forte (frammentazione domina il volume). NON ratificare su rumore.

## DOMANDA APERTA DA RISOLVERE COI NUMERI (non prima)
Il cap a 5 pagine: dopo il rerun, i numeri delle thin dicono se "andare oltre 5 pagine" e' necessario o inutile.
- Thin a 5 pagine gia' a 0 con pool totale grande (es. 150 listing e M340=0) -> forte indizio che il
  mercato davvero non le contiene -> andare oltre 5 pagine NON aiuterebbe -> vira verso bande per le thin.
- Thin che cresce ma non basta (es. 0->4 da p1 a p5, traiettoria non satura) -> >5 pagine potrebbe
  deciderle -> decisione di scope separata, a freddo coi numeri davanti.
NON decidere lo scope ">5 pagine" in questa sessione: PORTA la traiettoria (N per pagina) a Luke.

## OUTPUT FINE SESSIONE (richiesto)
- Scrivi `<repo>/.claude/REPORT_S264.md` (NEL REPO): tabella per-famiglia coi conteggi e pagine_fetchate,
  esito per-famiglia, traiettoria N-per-pagina delle thin, proposta min_n (o motivazione del parcheggio),
  debito residuo.
- Aprilo: `open -a TextEdit "<repo>/.claude/REPORT_S264.md"`
- Persisti esito in STATE.md diff-first (Gate E: lascia a Luke il token approve se blocca).

## VINCOLI / ANTI-PATTERN
- Prova al layer giusto: FASE 1 provata da >19 listing reali fetchati, NON da "compila"; il probe
  conta post-dedup+gate, non righe di pagina.
- NON inseguire un Esito A forzato: NON abbassare min_n, NON allargare le chiavi, NON reintrodurre L4
  (fusione drivetrain) per "far salire N". Un misto/thin onesto e' il risultato corretto.
- NON allargare lo scope: solo de-gate + rerun. Niente proxy/stealth/scaling/mobile.de. Il cap a 5
  pagine NON si supera in questa sessione.
- NON chiudere al budget spacciandolo per progresso: se de-gate non funziona o il probe non gira sulle
  4 famiglie -> BLOCKED-ON col fatto mancante, non "completato".
- NON toccare `cove_engine_v4.py`. NESSUNA azione esterna.

## FUORI SCOPE (dopo i numeri di S264)
- Profondita' >5 pagine -> decisione di scope separata, solo se la traiettoria thin la giustifica.
- Stealth/scaling/proxy -> solo su Esito A confermato su famiglie liquide.
- Verdetto a bande -> solo su thin confermate dal mercato (non dal cap pagine).
- mobile.de / Vincario / invio dossier.
