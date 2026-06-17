> SUPERSEDED da docs/ROADMAP.md — vedi STATE.md regola di precedenza.

# PROMPT RIPARTENZA — S278 (APPROVATO Luke 2026-06-17)

> Rilancia Claude Code con `ARGOS_HARNESS_UNLOCK=1` PRIMA di iniziare
> (la PRIORITA' 0 edita MEMORY.md, protetto da Gate-E `overwrite_sot`).

## Contesto (leggi in quest'ordine)
1. `.claude/REPORT_S277.md` + `.claude/REPORT_SESSIONE_S277.txt` — cosa fatto S277 (bundle Q3
   firma→Azzurra, commit `ee0694f`) + risposte C1-C4.
2. `STATE.md` — SoT di stato. Esegui `bash state/refresh.sh <SESSION_ID>` per ri-derivare gli anelli.

## Esegui IN ORDINE

[1] PRIORITA' 0 (correttezza) — SOTTO UNLOCK
   a) Backup Rule 1d di MEMORY.md, poi aggiorna la riga-indice 11 (oggi "cap-truncated only")
      con la riga gia' approvata:
      `- [S273 base-mercato BMW Serie3 NON affidabile (cap-truncated + geo + A/B)](s273_fixture_truncated_cap.md) — pool valido = 2 garanzie SEPARATE: (i) completezza DEEP_PAGES>=80 fino a pagina vuota + experiment-OFF; (ii) purezza geo==IT su location.countryCode. Calibrazione 330i invalida finche' non rifatta.`
   b) Aggiorna STATE.md a S277 (commit ee0694f, firma Azzurra; anelli invariati).

[2] COPY DAY-1 (C1 = Luke approva PRIMA)
   Scrivila come PROPOSTA: disclosure + provenienza contatto + opt-out, firma Azzurra, deve
   atterrare "calda" senza perdere response rate. Mostrala a Luke per OK. NON wirarla nel
   runtime prima dell'OK. (E' anche il sostrato del balancing test legale.)

[3] PIANO git filter-repo (C3)
   Produci il piano step-by-step (bonifica secret S220 in history + rotazione) da eseguire Luke.
   Sblocca il push.

## Vincoli
- Anelli E2E invariati: 2/9A/5 VERIFIED(smoke) · 1/9B/6-7 UNVERIFIED · 8 BLOCKED.
- NESSUN invio a dealer reale finche' i 3 gate tecnici non sono verdi:
  (1) E2E TEST_FOUNDER verde + Luke "pienamente soddisfatto";
  (2) trasparenza in PRODUZIONE (Azzurra+firma → sync.sh, C2 = dopo E2E verde, pre-flight wa-sender/);
  (3) base-mercato fidata (scrape esaustivo DEEP_PAGES>=80 + geo==IT + experiment-OFF).
- Liceita' canale = DECISO-FINALE (WA cold outreach). NON e' piu' un gate.
- Push bloccato (secret in history) finche' C3 non risolto → commit solo locali.
