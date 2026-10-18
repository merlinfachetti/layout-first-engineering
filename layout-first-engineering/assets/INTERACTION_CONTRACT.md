# Interaction contract — {{PROJECT_NAME}} / {{COMPONENT}}

> S2 design agreement. Attach editable frames/recordings when available. Do not label static mockups as implemented or validated interactions.

- Component: {{CARD_CAROUSEL_DIALOG_OTHER}}
- Purpose and primary user action: {{ACTION}}
- Visual baseline + Figma node (verified): {{BASELINE_URL}}
- Desktop/mobile/tablet: {{DEVICE_BEHAVIOR}}
- Dark/light tokens shared: {{SEMANTIC_TOKENS}}

| State | Trigger | Visual response | Screen reader / focus behavior | Reduced motion | Acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| Default | initial | {{DESIGN}} | {{SEMANTICS}} | N/A | {{LINK}} |
| Hover (optional) | pointer | {{DESIGN}} | no hover dependency | N/A | {{LINK}} |
| Focus | keyboard | {{VISIBLE_FOCUS}} | reachable by tab | N/A | {{LINK}} |
| Open / expanded | activation | {{DETAIL_VIEW}} | semantic navigation, preserved focus | instant alternative | {{LINK}} |
| Saved / selected | action | {{SUCCESS_FEEDBACK}} | announcement when appropriate | no unnecessary motion | {{LINK}} |
| Loading / error / empty | async outcome | {{FEEDBACK}} | status/error communicated | static fallback | {{LINK}} |

## Cards

- Primary card destination is clear and keyboard-reachable. Secondary Save/Follow actions are separately actionable, with **no nested interactive controls**.
- Information hierarchy (cover, title, metadata), image aspect/fallback, long titles, external data attribution and missing image behavior: {{RULES}}.
- Focus return after closing a modal or returning from detail: {{PLAN}}.

## Carousels (only where discovery benefits)

- Prefer user-driven navigation; **no autoplay by default**. Include visible next/previous, keyboard operability, touch behavior where relevant, focus visibility and accessible labels.
- Do not make a catalog or dense personal collection hard to search by forcing it into a carousel. Preserve a discoverable grid/list option.
- Boundary behavior, scroll/snap, navigation feedback and reduced-motion fallback: {{RULES}}.

## Verification protocol

Mark each item as `specified / prototyped / manually-tested / automated-tested`, citing files and actual test results. Never confuse "illustrated" with "interactive".
