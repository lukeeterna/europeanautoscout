# REPORT S277 — bundle Q3 (firma → Azzurra) + risposte C1-C4

> SoT di stato = `STATE.md`. Questo è il report di sessione (record durevole).
> Le risposte C1-C4 sotto rispondono a `.claude/REPORT_S276.md §8`.

## Fatto questo round
- **Bundle Q3 (residuo firma) — CHIUSO IN REPO, commit `ee0694f` (locale, no push)**:
  `wa-intelligence/response-analyzer.py` — l'output WA del bot non firma più "Luca" in 1ª
  persona. Aggiunta costante pubblica `ARGOS_ASSISTANT='Azzurra'` (riga 68);
  `ARGOS_PERSONA='Luca Ferretti'` INVARIATO (persona reale, voce/tel).
  Punti firma→Azzurra: format_prompt (386), istruzione LLM (835), reply contratto (2099),
  TEMPLATE_FALLBACK ×2 (2378/2382), retry auto-identificazione (2429), broker fallback (2478).
  `tools/test_ambra_5scenarios.py` 5/5 PASS.
- **Confine AMBRA/Azzurra DEFINITO e applicato**: **Azzurra** = unico nome public-facing (ciò che
  il dealer legge nel testo WA + auto-identificazione "sono Azzurra, l'assistente di Luca Ferretti").
  **AMBRA** = nome interno di sistema (identificatori codice, variabili, costanti, commenti, plan/doc) —
  invariato. "Luca Ferretti" = persona reale principale, nominata dove serve come principale.
- ⚠️ **Verifica render = solo statica sui literal** (firma è literal nei template/prompt, non costruita
  dinamica → adeguata). Il render LLM vero (messaggio generato che firma Azzurra) si vede nell'E2E
  TEST_FOUNDER, deferito (C4).

## Anelli E2E — INVARIATI
2/9A/5 VERIFIED(smoke) · 1/6-7/9B UNVERIFIED · 8 BLOCKED(esterno). Q3 = control-plane/persona, non muove anelli.

## Risposte Luke C1-C4 (DECISE questo round)
- **C1 — copy Day-1**: Luke vuole **APPROVARLA PRIMA** che tocchi il runtime. → la copy si scrive come
  PROPOSTA da mostrare, NON si wira finché Luke non dà OK. (È anche il sostrato del balancing test Q1/(a).)
- **C2 — deploy iMac (sync.sh)**: **DOPO** che l'E2E TEST_FOUNDER è verde, NON ora. Pre-flight symlink
  `wa-sender/` obbligatorio prima di sync.sh (memoria S252). Finché non deployato, daemon live nega ancora.
- **C3 — push/secret in history**: Luke vuole il **piano `git filter-repo` step-by-step** (bonifica
  secret S220 + rotazione) da eseguire LUI. DA PRODURRE (non ancora scritto). Finché irrisolto, commit locali.
- **C4 — autonomia S277**: **STOP dopo firma+Azzurra** (bundle Q3). Raggiunto. Luke rivede prima di copy/E2E.

## Primo step prossima sessione (S278) — ORDINE
1. **PRIORITÀ 0 (correttezza, NON cosmetico) — richiede `ARGOS_HARNESS_UNLOCK=1`**: rilanciare CC con
   l'env var, poi aggiornare la **riga-indice 11 di MEMORY.md** (Gate-E `overwrite_sot`) — oggi ancora
   "cap-truncated only", da allineare al topic file `s273_*` già completo. Riga pronta:
   `- [S273 base-mercato BMW Serie3 NON affidabile (cap-truncated + geo + A/B)](s273_fixture_truncated_cap.md) — pool valido = 2 garanzie SEPARATE: (i) completezza DEEP_PAGES>=80 fino a pagina vuota + experiment-OFF; (ii) purezza geo==IT su location.countryCode. Calibrazione 330i invalida finche' non rifatta.`
   (backup Rule 1d prima dell'Edit.) Aggiornare anche STATE.md a S277 (commit ee0694f, firma Azzurra) sotto unlock.
2. **Copy Day-1 proposta** (C1): scriverla (disclosure + provenienza contatto + opt-out, firma Azzurra,
   atterra caldo) e mostrarla a Luke per OK — NON wirarla prima.
3. **Piano git filter-repo** (C3): produrre step-by-step da eseguire Luke.

## 3 gate tecnici residui a un invio dealer REALE (nessuno legale: (a) DECISO-FINALE WA cold)
1. E2E TEST_FOUNDER verde (anelli 1/6-7/9B) + Luke "pienamente soddisfatto".
2. Trasparenza in PRODUZIONE: Azzurra+firma → `sync.sh` (C2, dopo E2E verde).
3. Base-mercato fidata: scrape esaustivo DEEP_PAGES≥80 + geo==IT + experiment-OFF (finding cont3).
