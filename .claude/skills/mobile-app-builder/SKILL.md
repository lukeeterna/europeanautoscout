---
name: mobile-app-builder
description: >
  Standard enterprise per sviluppo mobile. Invocare per: React Native, Tauri mobile,
  PWA, offline-first features, push notifications, deep links, performance su device
  low-end. Contiene vincoli, pattern e checklist mobile che Claude deve applicare.
---

## Vincoli mobile (sempre presenti)

| Vincolo | Standard | Perché |
|---------|---------|--------|
| Network | Progettare per 3G offline-first | Non assumere connessione stabile |
| Battery | No polling — usare push, batch background | Risparmio energetico |
| Screen | Min 375px, touch targets ≥ 44×44px | Usabilità con le dita |
| Memory | Testare su 2GB RAM | Non tutti hanno top di gamma |
| Storage | Dati locali minimi | Device dell'utente ≠ tuo database |

## Pattern obbligatori

**Offline-first:**
1. Progettare prima il meccanismo di sync, poi l'UI.
2. Operazioni locali → coda → sync quando online.
3. Conflict resolution: definire la policy prima di implementare.

**Gestione stati obbligatori (per ogni schermata):**
- Loading state: skeleton screens, non spinner generici
- Empty state: non schermate bianche — mostrare cosa fare
- Error state: messaggio actionable + retry
- Offline state: indicatore visibile + cosa funziona ancora

**Performance:**
- 60fps scrolling: profilare prima di shippare.
- First paint < 2s su 3G: code splitting + lazy loading.
- Animazioni: CSS/native animations only.

## Checklist pre-release mobile

```
[ ] Testato su device reale (non solo simulator)?
[ ] Network throttling testato (3G)?
[ ] Offline mode funziona?
[ ] VoiceOver/TalkBack: navigazione funziona?
[ ] Touch targets ≥ 44×44px su tutti gli elementi interattivi?
[ ] Deep links testati?
[ ] App size accettabile?
```
