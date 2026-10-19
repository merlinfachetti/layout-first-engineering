# Roadmap / Plano público

This roadmap is directional, not a delivery commitment. File an Issue before undertaking a substantial change.

## Done / Entregue (2026-10)

- [x] Machine-checked state, hash-chained decision ledger and computed gates (`lfe`), RFC-0001.
- [x] Action policy + Claude Code hooks: production code denied before G2+G3+G4; agent cannot approve.
- [x] Evidence receipts, traceability and G5 gated on proof; resume via handoff and session hooks.
- [x] Claude Code plugin with `/lfe:*` commands; engine shipped inside the skill; reproducible zips.
- [x] VS-01 example with two visual directions, prototype, app and an end-to-end proof in Chromium (CI).
- [x] Read-only visual studio (`lfe studio`); CI on Python 3.10 and 3.12.

## Priorities / Prioridades

- [ ] Run `scripts/agent_evals.py` with a logged-in Claude Code and record results in `docs/VALIDATION-MATRIX.md`.
- [ ] Integrate the v0.1.4-rc.2 method track (tool-blocker recovery, delegated execution, gate with exceptions).
- [ ] Make `vs01-proof` a required check once it has been stable for a few PRs.
- [ ] Test skill installation and activation with current versions of Claude Code, Gemini CLI and Codex.
- [ ] Run and document end-to-end design-first case studies with verifiable checkpoints and tool limitations.
- [ ] Maintain negative/edge-case tests: consent, security trade-offs, missing connectors, unrealistic budgets and agent handoff.
- [ ] Add an accessibility audit checklist for generated interfaces and documentation.
- [ ] Improve cost-model transparency and real-source attribution for vendor prices.
- [ ] Review prompt-injection defenses for repository, design, web and file sources.
- [ ] Provide a compatibility matrix with date, client version, permissions and evidence.
- [ ] Maintain bilingual PT-BR/EN guides; invite additional translations with reviewers.

Propose a task via [Feature request](https://github.com/merlinfachetti/layout-first-engineering/issues/new/choose). Label suggested new-contributor tasks `good first issue` only after they are sufficiently scoped and reproducible.
