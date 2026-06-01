# Architecture: Cross-Channel Narrative Consistency

**Domain:** B2B brand positioning for automotive broker
**Researched:** 2026-04-03

## Recommended Architecture

Hub-and-spoke model: one central narrative document drives all channel-specific adaptations.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Central Narrative Doc | Single source of truth for all claims | All channels |
| Landing Page | Public-facing, formal backstory | Central Narrative |
| LinkedIn Profile/Posts | Personal authority building | Central Narrative |
| Google Business | Local discovery, first impression | Central Narrative |
| WhatsApp Messages | Direct dealer communication | Central Narrative |
| PDF Dossier Footer | Implicit credibility on deliverables | Central Narrative |
| FAQ Document | Internal, prepared answers | Central Narrative |
| Email Signature | Professional touchpoint | Central Narrative |

### Data Flow

```
Central Narrative Document (backstory_luca_ferretti.md + this research)
    |
    +-> Landing Page (formal, entity voice)
    +-> LinkedIn (personal, expert voice)
    +-> Google Business (concise, local voice)
    +-> WhatsApp templates (direct, vehicle-first)
    +-> PDF footer (technical, protocol voice)
    +-> Email signature (professional, minimal)
    +-> FAQ doc (internal, defensive)
```

Every claim on any channel must trace back to the Central Narrative. If the Central Narrative changes (e.g., portal count goes from 73 to 80), ALL channels must be updated.

## Patterns to Follow

### Pattern 1: "Verifiable Facts Only" Rule
**What:** Every public claim must pass: "If a dealer googles this, will they find confirmation or contradiction?"
**When:** Every time any public-facing content is created or modified.

### Pattern 2: "Protocol Over Person" Credibility
**What:** Lead with methodology (Protocollo ARGOS, 4 analyses) rather than personal experience claims.
**When:** When dealer asks "why should I trust you?"

### Pattern 3: "Forward-Looking Retrospective" Content
**What:** Create content NOW that discusses past learnings without fabricating timeline.
**When:** LinkedIn posts, thought leadership content.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Aspirational Claims as Current Facts
**What:** Presenting future goals as current reality (Amsterdam HQ, team of analysts).
**Why bad:** Destroys trust permanently when discovered.
**Instead:** Present current reality honestly.

### Anti-Pattern 2: Different Stories on Different Channels
**What:** Landing says one thing, LinkedIn another, WhatsApp a third.
**Why bad:** Dealers cross-reference. Inconsistency = scam signal.
**Instead:** Central Narrative as single source of truth.

### Anti-Pattern 3: Partnership Claims Without Contracts
**What:** DAT Verified, DEKRA Inspected badges without active agreements.
**Why bad:** One phone call debunks entire brand.
**Instead:** Generic descriptors until partnerships active.

## Sources

- S74/S75 internal research on dealer credibility
- eCarsTrade, AutoProff, N26, Revolut positioning analysis
