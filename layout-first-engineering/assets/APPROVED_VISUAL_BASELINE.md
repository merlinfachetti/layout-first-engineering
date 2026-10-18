# Approved visual baseline — {{PROJECT_NAME}}

> Template to copy **only after G1 is explicitly approved**. This is a visual direction record, **not** G2 prototype approval. Never claim placeholder paths or URLs were verified.

- **Gate:** G1 — `approved` only after explicit user decision
- **Decision ID:** {{DECISION_ID}}
- **Approver / date:** {{APPROVER}} / {{DATE}}
- **Baseline revision:** {{BASELINE_VERSION}}
- **Project:** {{PROJECT_NAME}}
- **Canonical design tool / file:** {{VERIFIED_DESIGN_URL_OR_UNAVAILABLE}}
- **Design artifact fidelity:** `moodboard | static-layout | editable-frames | interactive-prototype` (use `interactive-prototype` only with evidence that the interaction was actually exercised; an editable frame is not interactive)
- **Current G2:** `not_started | exploring | proposed` (not automatically approved)

## Original proposals (preserve these)

| Direction | Intended role | Verified editable source | Local preview | License / provenance | Status |
| --- | --- | --- | --- | --- | --- |
| A | {{PRIMARY_OR_ALTERNATIVE}} | {{FIGMA_NODE_A_OR_UNAVAILABLE}} | `previews/a.png` | {{ASSET_SOURCE_A}} | {{STATUS_A}} |
| B | {{THEME_OR_ALTERNATIVE}} | {{FIGMA_NODE_B_OR_UNAVAILABLE}} | `previews/b.png` | {{ASSET_SOURCE_B}} | {{STATUS_B}} |
| C | {{COMPLEMENTARY_OR_ALTERNATIVE}} | {{FIGMA_NODE_C_OR_UNAVAILABLE}} | `previews/c.png` | {{ASSET_SOURCE_C}} | {{STATUS_C}} |

Render the actual previews in the finished document using repository-relative paths (not absolute local paths):

<!-- Replace this example with each verified local image. Do not leave missing images in an approved artifact. -->
`![A — primary visual direction](previews/a.png)`

## Approved composition and shared design system

- **One product, not separate disconnected themes:** {{DECISION}}
- **Default theme:** {{THEME}}
- **Other theme(s):** {{THEMES}}
- **Shared information hierarchy / component anatomy:** {{RULES}}
- **Semantic tokens:** {{COLOR_TYPE_SPACING_REFERENCES}}
- **Typography & iconography:** {{TYPE_DECISIONS}}
- **Breakpoints:** {{CONFIRMED_OR_TO_VALIDATE}}
- **Motion:** {{DURATIONS_OR_PENDING}}, reduced-motion fallback required
- **Keyboard / focus / touch:** {{BEHAVIOR_OR_PENDING}}
- **Approved inspirations from discarded directions:** {{PARTIAL_REUSE}}

## Evidence and constraints

- **What was actually inspected:** {{LINKS_AND_TOOL_RESULTS}}
- **What is only conceptual:** {{MOODBOARD_AND_SPEC_LIMITS}}
- **What is not yet validated:** {{A11Y_INTERACTION_RESPONSIVE_PERFORMANCE}}
- **Asset rights / API media concerns:** {{RIGHTS_OR_UNVERIFIED}}
- **Known risks and owners:** {{RISKS}}
- **G2 prototype acceptance criteria:** {{CRITERIA}}

## Change log

| Date | Baseline revision | Decision | What changed | Impact on G2/G3/G4 |
| --- | --- | --- | --- | --- |
| {{DATE}} | {{BASELINE_VERSION}} | {{DECISION_ID}} | Initial approved direction | G2 remains pending |

## README discoverability

Link this document from the project's README and **embed at least the primary approved local preview** in the README. On theme projects show both dark and light variants. Confirm image paths render in repository Markdown and are versioned. Keep original S1 proposals and images intact; add new S2 revisions in separate files.
