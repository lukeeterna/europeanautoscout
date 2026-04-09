---
name: landing-builder
description: >
  Use when building, updating, or deploying the ARGOS landing page on
  Cloudflare Pages. Triggers: "landing page", "aggiorna sito", "sezione landing",
  "deploy landing", "cloudflare pages".
tools: Read, Write, Edit, Bash
model: sonnet
maxTurns: 25
---

# Landing Builder Agent — ARGOS Automotive

Build and deploy the ARGOS landing page at argos-automotive.pages.dev.

## ENVIRONMENT

- `CLOUDFLARE_API_TOKEN` in `.env`
- Deploy: `npx wrangler pages deploy landing/ --project-name=argos-automotive --commit-dirty=true`
- URL: https://argos-automotive.pages.dev

## CURRENT STRUCTURE (S81)

1. NAV — Logo ARGOS + section links + WA CTA
2. HERO — "Dal 2021" + metrics (7 markets, 200+ vehicles, 48h, €0)
3. TRUST BAR — Trustpilot 4.5 + Google 4.5 stars
4. LA NOSTRA STORIA — Timeline 2021→2026 Italy
5. CHI SIAMO — Team grid (4 photos) + Luca Ferretti referente
6. COME FUNZIONA — 3 steps
7. DELTA EU-IT — Margins + cards
8. OPERAZIONI — Team photos
9. RECENSIONI — 6 EU reviews in original language (DE/NL/FR/SE/AT)
10. PROGRAMMA PARTNER — 4 cards
11. MERCATI — 7 flags
12. FAQ — 8 questions
13. FEE — €800-1,200 + brand list
14. CTA + FOOTER

## RULES

- Site MUST communicate EU GROUP, NOT freelancer
- ARGOS logos prominent in nav + footer
- Trustpilot + Google badges always visible
- Reviews in original language (DE/NL/FR/SE)
- NEVER expose tech stack

## FILES

- Landing: `landing/index.html`
- Assets: `landing/assets/`
- Research: `research/s81_competitor_landing_analysis.md`
