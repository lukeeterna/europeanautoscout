# ARGOS — STATE
aggiornato: 2026-07-30 · fonte: git (mai memoria, mai tracker)

## Coordinate
repo: github.com/lukeeterna/europeanautoscout (PUBBLICO)
branch: s210/audit-master-plan
workspace: ~/Documents/europeanautoscout
archivio SOLA LETTURA: ~/Documents/combaretrovamiauto-enterprise
catena: 5607cea > 832c31a > 1b9042e > 932796d > 66d143f > 9d7c3f7 > 382236f > 3fd1c8f > acb8966

## Scadenza
produzione 2026-08-27, non negoziabile.
fuori percorso critico verso il primo pagante = coda.

## Ponte Sol > CC (fisso)
Sol legge il repo a un commit pinnato, non tocca mai git, non ha credenziali di scrittura.
Consegna: Sol produce un file > il founder lo salva in incoming/<nome> (path fisso per unita, una consegna per unita).
Primo atto di OGNI blocco CC: cp incoming/<nome> .vos/incoming-archive/$(date -u +%Y%m%dT%H%M%SZ)-<nome>
POI leggere, rivedere, integrare. Mai integrare senza snapshot.
La revisione della consegna Sol e di CC, non del founder.
Il giudice non legge incoming/: giudica il diff dopo il push.
Token di scrittura a Sol e branch di quarantena: RESPINTI, non riaprire.

## Unita aperte
- INGEST v1 — bloccata su CSV Telemaco (atto founder). destinazione data/registry/ (gitignorata).
- PROTOCOLLO.md + bin/vos_check.sh — sorgente inesistente (verificata assente su venture-os e su disco). da generare, non da copiare.

## Unita chiuse (non in ridiscussione)
- SWITCH v1: remoto ripubblicato pulito, provenienza risolta, fork=0.
- funnel 3 province: 44 CONTATTABILI (PZ 18 · TV 22 · RM 4), campione-verificato PZ 7/8 · TV 7/8.
- igiene pubblica v1: numero test founder grezzo 0 a HEAD, .bak tracciati 0.
- diagnosi auto-accept: causa = ~/.claude.json chiave tengu_quill_harbor.
- FIX-AUTOACCEPT v1: permissions.defaultMode=default (questo commit).

## Pendenti founder (decisioni, non esecuzione)
- collaudo footer accept-edits: sessione nuova E dopo primo compact. fallback: reset one-shot tengu_quill_harbor.
- RPO: vincolante PRIMA di qualunque chiamata ai 44.
- PII di terzi in albero pubblico: 155 occorrenze, 76 numeri distinti, 31 file. decisione aperta.
- rotazione numero test founder (resta comunque in history).
- Telemaco: estrazione ATECO 46.18.41 + 47.92.21 + 47.92.31 su PZ/TV/RM.

## Coda
- env-fix 7 file con placeholder prima del prossimo E2E fisico:
  .harness/gate_e.py · argos-proxy/src/lib/wa-daemon.ts · chaos_db_stress.py · chaos_test.sh ·
  tools/test_ambra_5scenarios.py · tools/test_e2e_full.py · tools/tests/test_dossier_hitl_smoke.py
- rings E2E: #1 UNVERIFIED · #9B UNVERIFIED · #6-7 UNVERIFIED (founder-gated) · #8 BLOCKED-ON dealer reale · resto PASS.
- rimozione .claude/NEXT_SESSION_PROMPT.* (sostituiti da questo file).
- generatore chiudi-ordinatamente: ripuntare l'output su docs/judge/STATE.md invece di HANDOFF_CURRENT.md. unita SOL, post-27/08. nel frattempo HANDOFF_CURRENT.md e gitignorato.

## Invarianti
un solo blocco attivo cross-venture · ogni blocco apre con MODELLO: · git -C esplicito mai in variabile ·
path assoluti mai cd · snapshot durevole prima di consumare un artefatto volatile ·
PII e segreti mai in git · zero bypass 403/Cloudflare · zero contatto imprese senza mandato ·
lo stesso modello non scrive e non giudica lo stesso codice ·
l'hook auto-close committa qualunque file dirty a fine sessione · autorita = git/disco.
