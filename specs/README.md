# Specs ARGOS

Una directory per feature, creata da `/spec nome-feature`.

## Struttura
```
specs/{nome-feature}/
  requirements.md  ← WHEN X THEN system SHALL Y (EARS, testabile)
  design.md        ← HOW + architettura + decisioni A/B
  tasks.md         ← task atomici + comando verifica + expected output
```

Il validator legge requirements.md — non la memoria del chat.
