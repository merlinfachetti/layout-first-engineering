# Visual-first design method (S0–S2)

## Define what "layout first" means

Do not start by selecting Next.js, React, Supabase, PostgreSQL or vendor products. Define experience, emotion and intent. Gather **just enough** product context to design the first useful screens: product purpose, audience, core action and aesthetic references/anti-references. Deep product discovery follows early layout exploration.

Before drawing, identify the device contexts and any known accessibility needs. Accessibility is not a retrofit; proactively avoid color-only meaning, low contrast, animation traps and impossible keyboard interactions.

## Deliverable sequence

### A. Art direction proposals (G1)

Produce 2–3 *meaningfully different* directions. Describe for each:
- one-sentence big idea and personality
- hierarchy, grid, typography and palette
- imagery/illustration approach and legal provenance (generated, stock, user-owned, licensed)
- interaction/motion narrative and reduced-motion alternative
- signature section/element with real UX purpose
- pros/cons in clarity, performance, accessibility and development effort
- visual references/moodboard and actual editable draft if design connectors support this

Never use the same generic hero/cards/dashboard layout three times with different colors. At G1 offer a recommendation, not a false forced choice. Allow hybridization.

### B. Design baseline (G2)

Create an initial information architecture and visually coherent prototype for the **minimum screens needed to test the primary task**, then remaining priority screens. Include desktop/tablet/mobile where applicable, navigation, hierarchy, content states and visual hierarchy. Avoid filler text and arbitrary fake metrics in final mockups; clearly label demonstration data.

Components: tokens, semantic colors, type scales, spacing, surfaces, breakpoints, focus/hover/disabled, aria semantics, reusable patterns, media and illustrations, localization and RTL if applicable, loading/empty/error/success, motion duration/easing and reduced motion.

If design tool allows, deliver actual editable nodes/components with link and a verified creation action. If not, deliver a structured artifact with screen-by-screen annotations, design tokens and interaction descriptions. Static AI images cannot stand in for actual editable prototypes when editability is required.

### C. Product reconciliation (after G2, before G3)

Discovering a new role, billing model, data flow or permission can force design changes. Show visual impact, propose solution, and get design amendment sign-off. The *approved current design handoff version* (not the oldest image) is the implementation visual baseline.

## Creative rigor

Use one cohesive visual concept with restraint. A visually surprising UI that hides key actions is not successful. Meaningful differentiation examples: editorial layouts, expressive typographic hierarchy, cinematic imagery with purposeful cropping, illustration system, contextual animation, compositional depth, carefully choreographed transitions, thematic data visualization. Don't assume every application needs 3D/particle effects or a dark UI.

Performance-minded design: responsive image variants, loading strategy, font subsets, no gratuitous heavy videos/canvases. Responsive and keyboard flows matter even for experimental visuals.

## Review matrix

Each design proposal includes qualitative evaluation (Evidence / Issue / Remediation):
- originality and brand fit
- clarity and task completion
- contrast, keyboard and focus, content readability
- responsive/layout resilience, long text and localization
- implementation feasibility and performance risk
- asset licensing and accessibility alternatives
- edge-state coverage

Do not assign uncalibrated 99% quality scores. Ask the user to approve when meaningful artifact(s) have been delivered.
