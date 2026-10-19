# Changelog

## Unreleased — v0.2.0 candidate (not an official release)

- **Engine `lfe` (RFC-0001):** strict contracts v0.1, project state, hash-chained decision ledger, gate status
  computed from the ledger and current file hashes (stale on change), human-only approvals at an interactive
  terminal (G1 may come from a chat quote), stage rules.
- **Locks:** action policy and Claude Code `PreToolUse` hook deny production code before G2+G3+G4, agent-made
  approvals, and deploy/publish/cost/delete actions; fails closed.
- **Proves:** evidence receipts (`lfe run`), `verify-report`, traceability; G5 requires a clean passing receipt
  for every `must` requirement.
- **Remembers:** generated handoff, next action and open questions, `SessionStart`/`Stop` hooks,
  export/import that never elevates decisions (hardened after a security review).
- **Shows:** `lfe studio` read-only visual page; redesigned lifecycle diagram (EN/pt-BR).
- **Ships:** engine inside the skill (`scripts/lfe.py`), Claude Code plugin with `/lfe:status|next|resume|studio`,
  reproducible release zips, step-by-step guides.
- **VS-01:** reading-list example with two directions, prototype, app, and an end-to-end Chromium proof in CI.
- **Behavioural evals:** `scripts/agent_evals.py` (5 cases, deterministic grading); real runs pending a logged-in CLI.

## v0.1.4-rc.1 method track (merged, part of the candidate above)

- Added optional repository stewardship protocol S0–S9 and auditable publication state.
- Added required visual G1 baseline template with local image proof and theme/hybrid support.
- Added interaction contracts for cards/carousels, asset/API provenance and accessibility/motion.
- Added offline G1 baseline path validator, 12 behavioral evaluation scenarios and test-harness integrity checks.
- Expanded state tracking, CI failure diagnosis and separate local/remote verification.
- Real Codex/Gemini/Claude behavioral evaluations are pending; this candidate does not assert cross-model validation.


## 0.1.3 — 2026-10-16

- Added community governance, contributor conduct, support, roadmap and accessibility policy.
- Added privacy/data-handling notice and private-vulnerability-reporting procedures (manual GitHub toggle required).
- Added compatibility Issue template, improved PR checklist and security guidance without claiming regulatory certification.
- Replaced legacy direct-`main` update flow with human-reviewed protected-branch PR flow, with explicit identity and no AI co-authorship.
- Added offline community documentation checks and a permanent end-to-end maintainer guide.


## 0.1.2 — 2026-10-15

- Added one permanent canonical Portuguese manual covering usage, installation, initial publication, existing-repository upgrades, community governance and releases.
- Added safe macOS updater for already-published GitHub repositories, with account, remote, clean-worktree and fast-forward checks.
- Linked original individual guides and master prompts; none were removed.

## 0.1.1 — 2026-10-15

- Added comprehensive persistent Portuguese and English guides for native skill installation, fallback and cross-agent use.
- Restored the two master prompts as permanent documentation.
- Added an absolute-path macOS publication entrypoint and troubleshooting instructions.
- Corrected ChatGPT web skills eligibility guidance and linked official platform docs.

## 0.1.0 — 2026-10-15

- Initial open-source MVP of the Layout-First Engineering skill.
- Design-first approval gates (G1–G6) and S0–S9 lifecycle.
- Stage-specific reference guides, reusable handoff and governance templates.
- Read-only gate-state validator, offline structure checks, manual agent evaluation scenarios.
- Installation notes for Claude Code, Gemini CLI, OpenAI Codex, Claude.ai and other hosts.

This release validates the *package structure*; cross-platform agent behavior and connector integrations require real-world evaluations.
