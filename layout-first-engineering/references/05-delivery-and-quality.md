# Engineering delivery, quality and operational readiness (S5–S9)

## Engineering manager setup

Break work into vertical slices that a user can try, rather than implementing all frontend then all backend when integration feedback would be delayed. Build a dependency map and prioritized backlog with traceability to `FR-`, `NFR-`, `SEC-`, `UX-` and `UI-` IDs. Provide incremental scope, work owner (person or agent), sequencing, acceptance, test approach, risk and estimated effort as an assumption-based range.

Definition of Ready (DoR): approved design/scope trace, acceptance criteria, dependencies resolved or documented, test fixture strategy, security/privacy impact understood.

Definition of Done (DoD): code reviewed, type/lint checks, required tests executed and passing, visual comparison, accessibility considerations, observability for critical flows, docs/decision log updated, no unapproved secret or expense, release note where appropriate.

## Implementation sequence

1. Inspect existing repo conventions, toolchain, CI and recent changes; avoid destructive wholesale rewrites.
2. Scaffold only the dependencies approved at G4. Prefer contract-first API boundaries and type-safe models.
3. Implement design tokens and reusable UI primitives; run mobile/desktop and keyboard checks early.
4. Implement one critical end-to-end journey including states, validation, errors and permission boundaries.
5. Add tests (TDD when valuable; Given/When/Then for critical flows), incrementally integrate remaining journeys.
6. Check changes against approved design and requirement traceability in every slice.
7. Periodically reassess operational costs, technical debt, performance and dependency risk.

Never treat a generated file or passing unit tests as evidence of successful production behavior. Report actual commands and results, failures and missing environment prerequisites. Avoid arbitrary 100% coverage claims. For UI snapshots, ensure baselines correspond to approved current design and compare at appropriate viewports.

## Repository operation is not a verified build

When the user wants GitHub integrated across stages, follow `references/07-repository-and-contribution-workflow.md`. A green local test is not a passing remote status check. Required CI that cannot run due to runner/billing/policy problems blocks normal merge and must be reported distinctly from test failures; never invent the root cause or bypass it to manufacture a green release. Verify commit/PR state remotely and synchronize the canonical workspace only after a confirmed merge. Record `specified`, `implemented`, `executed`, `passed`, `blocked` separately.


## Verification matrix

- Functional: happy-path + failure-path E2E, auth/role boundaries, validation, concurrency where relevant.
- Visual: key desktop/mobile viewports, interaction fidelity, long strings, image loading and design baseline differences.
- Accessibility: keyboard, focus order, semantics, labels, contrast, screen-reader smoke tests where possible, reduced motion; target WCAG 2.2 AA as appropriate.
- Security: check input/output encoding, session/auth, authorization, data leakage, supply chain, secrets, abuse-rate controls; map to appropriate OWASP ASVS controls (not a compliance guarantee).
- Reliability/operations: health signals, logs without sensitive data, restore/recovery tests where applicable, feature flags and rollback.
- Performance: collect actual metrics via appropriate tools: LCP, INP, CLS and representative load/latency. State lab vs field and device/network context.
- Economics: verify resource usage/billing assumptions and configure budget alert where available.

If no runnable environment: distinguish 'reviewed' from 'tested'. Leave G5 blocked on critical unverified checks or explicitly document user-accepted limitations; never misrepresent readiness.

## Release gate

At G5 present a release candidate checklist with evidence (commands, screenshots/test reports, known risks, open defects and rollback). Confirm user acceptance of disclosed residual risks.

At G6 request **specific release approval**: which environment, target URL/domain, data migration impact, expected charges, recovery/rollback and user-visible effects. Back up before significant migrations if required. Run only authorized actions; report actual deployment result (URLs only if real). Distinguish 'release prepared' from 'deployed'.

## After launch

Capture feedback and metrics aligned with product success: funnel events with consent if necessary, accessibility regressions, error budgets, support issues, cost growth, dependency upgrades, data lifecycle and security alerts. Route major UI changes back to G2/G3 and architecture changes to G4; avoid silent divergence from the design handoff.
