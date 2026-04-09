---
name: frontend-developer
description: >
  Standard enterprise per sviluppo frontend. Invocare AUTOMATICAMENTE per:
  componenti React/TypeScript, CSS/design tokens, Tauri UI, bundle optimization,
  accessibility, performance frontend. Contiene checklist, pattern e regole
  che Claude deve seguire quando scrive o revisiona codice frontend.
---

## Standard obbligatori

**TypeScript:**
- `strict: true` in tsconfig. No `any`. No `as Type`. No `!` non-null assertion.
- Tipi espliciti su tutte le funzioni pubbliche e props dei componenti.
- Preferire `unknown` su `any` quando il tipo è incerto.

**Componenti React 19:**
- Max 150 righe per componente. Se più lungo: splittare.
- Preferire composizione su ereditarietà.
- Co-locare test con componenti: `Component.test.tsx`.
- Esportare tipi insieme ai componenti.
- Mai `document.getElementById` in React — usare `useRef`.
- No `useEffect` per data fetching — usare React Query o Tauri commands.

**CSS / Styling:**
- Design tokens/variabili CSS — mai magic numbers hardcoded.
- No inline styles eccetto per valori veramente dinamici.
- Mobile-first: 375px min width, touch targets 44×44px minimo.
- Dark mode: semantic token pairs, mai inversione diretta dei colori.

**Performance checklist:**
- Bundle size: controllare warnings prima di committare.
- Immagini: lazy load, WebP, dimensioni corrette.
- Animazioni: CSS/native only — JS sul main thread = frame drops.
- Code splitting: ogni route separata.

**Accessibilità (non opzionale):**
- Ogni elemento interattivo è navigabile da tastiera.
- ARIA roles corretti su componenti custom.
- Focus visible: ring visibile, non rimosso con `outline: none`.
- Contrasto testo: minimo 4.5:1 (WCAG AA).

## Workflow obbligatorio

1. Leggere il codice esistente PRIMA di scrivere. Capire i pattern in uso.
2. Verificare `package.json` prima di suggerire nuove dipendenze.
3. Scrivere il componente → scrivere il test → in quest'ordine.
4. Eseguire `npm run build` e correggere TUTTI gli errori TS prima di dichiarare done.

## Checklist pre-commit frontend

```
[ ] TypeScript compila senza errori?
[ ] Nessun console.log nel codice?
[ ] Componenti under 150 righe?
[ ] Test scritti per la nuova logica?
[ ] Bundle size non aumentato significativamente?
[ ] Stati: loading, error, empty sono gestiti?
[ ] Accessibilità: tab navigation funziona?
```
