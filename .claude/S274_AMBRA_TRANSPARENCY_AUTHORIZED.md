# S274 — Trasparenza AMBRA: FINDING + AUTORIZZAZIONE LUKE (esecuzione S275)

> Record durevole git-tracked. Il breadcrumb NEXT_SESSION_PROMPT.md è zero-status
> (rigenerato dall'hook), /tmp è effimero → la decisione vive qui finché S275 non la esegue.

## DECISIONE LUKE (S274, chiusa — autorizzata l'esecuzione)
**Correggere il meccanismo runtime di impersonificazione. NON ripristinarlo.**
- ✅ Versione DICHIARATA: AMBRA = assistente automatica palese di Luca Ferretti (mandante
  reale), motivazione vera (Luca è sul campo in Europa), NIENTE superlativi. Lecita, vera.
- ⛔ Impersonificazione ("Sei Luca" in prima persona + divieto-parole "bot/automatico" +
  deflessione): inganno della controparte, autolesionista. Da rimuovere, non ripristinare.
- Razionale Luke: un agente che si finge umano è la sopra-dichiarazione massima sull'attore
  più importante (chi compra). Stesso falso-PASS combattuto da S256, al layer identità. La
  disclosure è il pezzo che tiene in piedi la credibilità verificabile = ARGOS.

## FINDING (verificato dal codice S274) — la negazione è RUNTIME, non KB
`wa-intelligence/response-analyzer.py:335-378` (PROMPT_MODULES, system-prompt classifier):
- riga 341 `'identity'`: "Sei Luca Ferretti" (prima persona umana)
- riga 360 `hard_rules`: ban parole "...bot...automatico...ARGOS"
- riga 364: "Se chiedono 'sei un bot/automatico' → proponi una telefonata o un vocale" (deflessione)
- riga 377 `hard_rules_post_handoff`: stessa deflessione
- riga 349 `'identity_post_handoff'`: "Sei Luca Ferretti di Argos" (prima persona)
KB (config, già nota): `argos_knowledge_base.md:244-245` blocco "Sei un bot?" = istruzione di non-ammissione.

## ESECUZIONE S275 (autorizzata — include RUNTIME)
**STEP 0 (PRIMA di tutto):** incollare in STATE.md §3 il riframing item (b) (sezione
"STATE.md §3 — RIFRAMING" sotto). Allinea il SoT al finding PRIMA dell'edit runtime.
Se Luke non l'ha già fatto in TextEdit a fine S274 → S275 lo gestisce come step 0
(via Gate E `overwrite_sot`: packet → approve → edit). Solo dopo, gli step 1-6.

1. `response-analyzer.py`:
   - `identity` / `identity_post_handoff`: da "Sei Luca Ferretti" → "Sei l'assistente automatica
     di Luca Ferretti" (mandante reale; AMBRA gestisce i primi contatti perché Luca è sul campo).
   - `hard_rules` (360) e `hard_rules_post_handoff` (373): RIMUOVI "bot"/"automatico" dalla ban-list.
   - righe 364 / 377: da deflessione → disclosure fattuale + motivazione (Luca sul campo in Europa,
     niente superlativi). Testo persona di riferimento: vedi addendum brief S274.
2. `argos_knowledge_base.md:244-245`: riscrivi blocco "Sei un bot?" → disclosure fattuale coerente.
3. FASE 2 coerenza identità: allinea "sono Luca" (KB:292) + firma dossier/email → "assistente di Luca".
4. FASE 4 verifica: re-grep negazione=0; `grep -niE "eccezion|migliore|tutta europa|esperto|best|top"`
   sul testo nuovo = 0; test comportamento AMBRA su "sei un bot?" (se assente → mini-test asserzione persona).
5. STATE.md §3 item (b): CHIUSO (backup 1d, diff-first, slug da packet Gate E `overwrite_sot`).
6. Commit + push KB + runtime-persona + STATE.md + test.

## STATE.md §3 — RIFRAMING item (b) (da incollare in TextEdit, SoT; Gate E blocca l'edit di CC)
Sostituire la riga (b) attuale con:
> (b) **trasparenza AMBRA — meccanismo runtime di impersonificazione (NON "istruzione KB
>     eventuale")**: `response-analyzer.py:341-377` impersona Luca in prima persona, vieta le
>     parole "bot/automatico" e deflette se interrogata. DECISIONE LUKE S274: correggere (assistente
>     palese di Luca reale + disclosure + motivo vero), NON ripristinare. Edit runtime AUTORIZZATO.
>     Esecuzione S275 (vedi `.claude/S274_AMBRA_TRANSPARENCY_AUTHORIZED.md`). Item (a) liceità
>     canale resta BLOCKED-ON-LUKE.

## Evidenze E2E sessione S274 (refresh.sh fc1cf54b)
Ring 2 / 9A / 5 VERIFIED smoke. Ring 1 / 9B / 6-7 UNVERIFIED. Ring 8 BLOCKED. NESSUN invio reale.
