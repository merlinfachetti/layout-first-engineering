# Progressive product discovery and scope control (S3)

## Deepen product understanding **after** initial visuals

Compare approved visual workflows against real business tasks. Use jobs-to-be-done, story maps, simple personas only when useful; prioritize observable value and avoid over-documenting a tiny website. Treat drawings as hypotheses, not validation of market demand.

Explore questions as required, not as a giant form:
- core job, beneficiary and success criteria; measurable outcomes and constraints
- user roles and permissions, onboarding, account recovery, guest experience
- content source, moderation, search, localization, accessibility, notification preferences
- data classes, ownership, consent, deletion, retention, residency and third-party sharing
- transactions, billing/refunds only if a paid product, and abuse prevention
- failure paths: denied permission, expired token, lost network, partial upload, duplicate request, quota exceeded, empty dataset, concurrent edits
- integrations, exports, import, audit needs, data portability, vendor exit
- legal/compliance exposure by jurisdiction; do not give legal assurance
- operational ownership: admin, support, analytics consent, backup, restore, SLAs when warranted
- MVP vs later features, feature flags and migration plan

Use targeted **challenge prompts**: "Who can see another user's private content?", "What happens when an upload fails halfway?", "Will the user understand this control on a phone?", "Can the system work without collecting that data?" Only ask when applicable.

## MVP and requirement specification

Write requirement IDs `FR-###`, `NFR-###`, `SEC-###`, `UX-###`, and acceptance criteria using testable language (Given/When/Then where useful). Link each to screen IDs (`UI-###`) and later tests (`TEST-###`). Classify Must / Should / Could / Won't-now, and label all assumptions. Identify explicit out-of-scope items and change triggers.

Create `PRODUCT_BRIEF.md` and update `DESIGN_HANDOFF.md` from templates. At G3, user approves the *MVP behavior* and revised UI. If an unexplored requirement could materially alter data security, permission boundaries, pricing or critical UX, keep G3 blocked.

## PM/EM considerations

Map dependency risks, handoff owners, external API assumptions, launch criteria, stakeholder approvals, support handover and metrics; do not assume the solo developer has a team. A single-person project can use lean artifacts without losing quality. Estimate effort as ranges and mark uncertainty; never promise delivery dates without validated velocity and availability.
