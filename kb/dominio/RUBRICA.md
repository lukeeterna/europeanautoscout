# RUBRICA — Standard di ammissione fatti KB dominio

> Questo file definisce **la FORMA** che ogni fatto deve avere per entrare in `kb/dominio/*.md`.
> Non contiene fatti di dominio. È lo standard che `validate_kb.py` applica in modo deterministico.
> La VERITÀ della fonte NON è verificata qui: il gate controlla solo il formato e rigetta la spazzatura.
> Il contenuto reale (numeri, fonti vive) lo grada il giudice sulle fonti, non la memoria del modello.

## Formato riga-fatto (obbligatorio, una riga per fatto)

```
FATTO: <claim> | FONTE: <url o citazione> | DATA: <YYYY-MM-DD> | NUMERO: <cifra/€/%/meccanismo quantificato> | VERIFICA: <metodo riproducibile>
```

- Ammesso il prefisso lista markdown `- ` davanti a `FATTO:`.
- I 5 tag (`FATTO FONTE DATA NUMERO VERIFICA`) sono tutti obbligatori e con valore non vuoto.
- Separatore di campo = pipe `|`. Ordine libero dei tag dopo `FATTO:`.

## I 4 requisiti (FONTE + DATA + NUMERO + VERIFICABILITÀ)

1. **FONTE citabile** — deve contenere un URL `http(s)://` **oppure** un marcatore di citazione
   (`Art.`, `Reg.`, `Direttiva`, `D.Lgs`, `D.M`, `Decreto`, `comma`, `§`, `ISO`, `EN`, `UNI`, `CdS`,
   `sentenza`, `report`, `rapporto`, `studio`, `bollettino`, `gazzetta`) **oppure** un anno a 4 cifre
   accompagnato da un nome di fonte (≥6 lettere). Serve poter risalire alla fonte.
2. **DATA** — formato ISO esatto `YYYY-MM-DD`, data reale. Niente "recente", "anni fa", "2020 circa".
3. **NUMERO/meccanismo** — deve contenere almeno una cifra `[0-9]`. Un meccanismo va **quantificato**
   (es. delta %, importo €, soglia). Prosa senza numero = rigettata.
4. **VERIFICABILITÀ** — deve contenere un URL **oppure** un verbo azionabile
   (`controlla`, `verifica`, `confronta`, `richiedi`, `calcola`, `ricalcola`, `cerca`, `consulta`,
   `interroga`, `incrocia`). Deve dire COME chiunque ricontrolla.

## Definizione di SPAZZATURA (rigetto automatico)

Un fatto è spazzatura — e il gate lo blocca — se ricade in uno di questi:

- **no-fonte** — FONTE vuota, `n/a`, `tbd`, `todo`, `?`.
- **forum/social/sentito-dire** — FONTE che cita reddit, facebook, instagram, twitter/x, tiktok,
  forum, quora, whatsapp, telegram, "un amico", "gruppo", "sentito", "si dice", "dicono", "tizio".
- **403/vuota/morta** — FONTE che dichiara `403`, `404`, "link morto", "pagina vuota",
  "pagina non disponibile".
- **no-data** — DATA assente o non in formato `YYYY-MM-DD`.
- **vago** — NUMERO senza cifre; oppure VERIFICA senza URL né verbo azionabile
  (`fidati`, `ovvio`, `tutti sanno`, `è così`).
- **plausibile-non-verificabile** — riga che "suona giusta" ma senza metodo riproducibile in VERIFICA.

## Struttura ammessa nei file `kb/dominio/*.md`

Il gate accetta come righe **non-fatto** solo: intestazioni `#`, note/citazioni `>`,
commenti HTML `<!-- ... -->`, righe vuote. Qualunque altra riga di prosa libera è **rigettata**
(anti-avvelenamento: un fatto non può essere contrabbandato come paragrafo).

## Esempio di forma (placeholder, NON un fatto reale)

```
FATTO: <claim placeholder> | FONTE: https://esempio.tld/documento | DATA: 2026-01-01 | NUMERO: <€ o % con cifra> | VERIFICA: confronta con <fonte> su esempio.tld
```

> `RUBRICA.md` è escluso dalla validazione: è lo standard, non un file di fatti.

## TIER FONTI (obbligatorio su ogni fatto)

- T1 = primaria/istituzionale (ministeri, GU, decreti, registri statali, Parlamento EU)
- T2 = indipendente non-interessata (associazioni consumatori, club automobilistici, testate con dati propri)
- T3 = commerciale-interessata (venditori di report/servizi: carVertical, autoDNA, ecc.)

Regola: fatti T3 = solo ordine di grandezza, MAI citati come certi nel copy pubblico.
Ogni riga-fatto termina con [T1]/[T2]/[T3].
