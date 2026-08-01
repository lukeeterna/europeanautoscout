# PROTOCOLLO — Invarianti del sistema giudice ARGOS

1. RUOLI. Sol scrive il codice leggendo il repo a un commit PINNATO, non tocca mai git. CC esegue tutto il lavoro macchina. Il founder ha due soli atti: sigillo e GO sulle azioni che escono dal repo. Il giudice legge in sola lettura, emette blocchi, non giudica le unità conformi.
2. VIETATO che lo stesso modello scriva un artefatto e lo giudichi.
3. Un solo blocco attivo alla volta. Ogni blocco = una sessione CC NUOVA, una consegna. Ogni blocco inizia con la riga MODELLO:.
4. FONTE DI VERITÀ = docs/judge/STATE.md. Gli handoff in prosa sono aboliti. Fa fede il diff, mai il messaggio di commit. Una dichiarazione di assenza vale quanto la copertura dello strumento che l'ha prodotta.
5. CHIUSURA. Ogni unità che scrive ha una FASE CHIUSURA anche su rosso. Ultima riga esattamente «VERDETTO: VERDE» o «VERDETTO: ROSSO». git add solo per path dichiarati, mai add -A. Mai history rewrite. Mai --dangerously-skip-permissions.
6. Quando una sessione stampa VERDETTO, il founder esce senza scriverle nulla.
7. TELEMETRIA. Fa fede solo used_pct dal json della PROPRIA sessione (sonda mtime su /tmp/claude-ctx-*.json), mai la percentuale RAW dell'hook, che sovra-riporta. La protezione reale è la taglia XS/S, non la soglia.
8. CARVE-OUT ARGOS — mai toccare in git: data/recon/, data/registry/, data/pool_icp/, incoming/, .vos/, .env.test. Questi path sono gitignorati e non entrano mai in commit. Il check porcelain li esclude.
9. IRREVERSIBILI ARGOS. Nessun invio WhatsApp verso numeri diversi da TEST_FOUNDER_NUM senza GO esplicito del founder. RPO vincolante prima di qualunque chiamata ai dealer. Zero scraping FB/portali automatizzato. Zero bypass 403/Cloudflare. Il repo è PUBBLICO: PII e segreti non entrano mai in git.
10. PATH VOLATILI. /tmp solo per artefatti che nascono e muoiono nello stesso mandato; prima di ogni sospensione, salvataggio su storage durevole.
11. CORSIE. REPO (Claude Code web, VM cloud, branch vos/<nome> + PR, nessun accesso a daemon/iMac/DB) e MACCHINA (CC locale: runtime, invii, deploy). Le due corsie non operano mai in contemporanea sugli stessi file. Una sessione REPO non tocca mai il daemon WA né il DB SQLite live.
