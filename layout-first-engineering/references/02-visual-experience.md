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

### A.1. Durable G1 approval artifact

After explicit G1 approval, generate a baseline from `assets/APPROVED_VISUAL_BASELINE.md` and store it in the project's `docs/design/APPROVED_VISUAL_BASELINE.md` if filesystem access is available. The artifact must:
- Embed real locally versioned preview images with Markdown `![alt](relative/path.png)` rather than text links alone; verify images and links, and add a discoverable README link and image.
- Cite editable design frames/nodes only when actually created/inspected. Record art provenance, license status, desktop/mobile samples, approved core principles, decision ID and date, version and known unverified aspects.
- Support approved hybrid identities: one system with semantic dark/light theme tokens, common information hierarchy, shared components and device behavior; rejected concept elements may be reused explicitly.
- Preserve all original proposals and previews. Differentiate moodboard, static composition, editable frame and **verified working interactive prototype**.
- Leave G2 pending. Changes to an approved G1 baseline require a superseding decision, not silent image replacement.
- When practical, use `scripts/verify_visual_baseline.py ... --approved` to check local asset paths (structural check only).


### B. Design baseline (G2)

Create an initial information architecture and visually coherent prototype for the **minimum screens needed to test the primary task**, then remaining priority screens. Include desktop/tablet/mobile where applicable, navigation, hierarchy, content states and visual hierarchy. Avoid filler text and arbitrary fake metrics in final mockups; clearly label demonstration data.

Components: tokens, semantic colors, type scales, spacing, surfaces, breakpoints, focus/hover/disabled, aria semantics, reusable patterns, media and illustrations, localization and RTL if applicable, loading/empty/error/success, motion duration/easing and reduced motion.

If design tool allows, deliver actual editable nodes/components with link and a verified creation action. If not, deliver a structured artifact with screen-by-screen annotations, design tokens and interaction descriptions. Static AI images cannot stand in for actual editable prototypes when editability is required.

### B.1. Interaction contract for visually rich elements

Use `assets/INTERACTION_CONTRACT.md` as a starting point for cards, carousels and key navigational patterns. Cards need distinguishable primary navigation vs secondary actions and no nested controls. State the `pointer/keyboard/touch` paths, empty/loading/error feedback, focus behavior, motion limits, reduced-motion fallback and evidence of what really works. Carousels must have visible controls, usable keyboard access and normally no autoplay; reserve grids/lists for efficient search and management. Never imply motion or interaction was tested based on a static image.


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
