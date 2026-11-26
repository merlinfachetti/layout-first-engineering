# Changelog

## 0.3.1 — 2026-11-26

From the first real adoption (a product already in production):

- **`lfe reconfirm`:** one chat message with several confirmation codes records every gate it names, each checked
  like `record-chat-approval` (opt-in, latest proposal, message reference, G5 evidence).
- **`lfe adopt`:** the plan and `--dry-run` warn first when the Markdown is at S6+ and code edits will stay locked
  until G1–G4 are reconfirmed; the next action points to `lfe reconfirm`.
- **`lfe chat-approvals enable`:** `G1` in `--gates` is accepted (it always takes a chat quote) and the success line
  no longer reads as if G1 had been enabled by the flag.

## 0.3.0 — 2026-11-26

Field fixes from running LFE on two real products, focused on making it work in every setup: cloud sessions,
chat-only owners, projects already under way and free design-tool plans.


- **Stage rules (#25):** entering S2–S9 needs the gate that closes the previous stage (S2 needs G1 … S9 needs G6);
  stages can no longer be skipped. Legacy imports keep their place up to S5 while approvals wait for reconfirmation.
- **Chat approvals for chat-only owners (#27):** opt-in `lfe chat-approvals enable` with the owner's quote; G2–G6
  then accept `record-chat-approval` when the quote carries the proposal's confirmation code (`lfe propose` prints
  it) and a `--message-ref`. Stored as `chat-quote` / `unverified`; disabling makes them stop counting.
- **G1 composition (#26):** `--primary`, `--theme-variant THEME=DIR`, `--complementary DIR=USAGE`,
  `--non-negotiable`; shorthand JSON is normalized; `--help` shows examples; invalid JSON is `BAD_COMPOSITION`.
- **`lfe adopt` (#28):** start the engine on a project already under way: tolerant PROJECT_STATE reader, ledger
  ids continue after the project's own `DEC-###`, draft typed artifacts generated from prototypes, evidence images,
  scope Markdown and ADRs, and a ready proposal (with confirmation code) for every gate approved in the Markdown.
- **Cloud sessions (#29):** `lfe install --project` vendors skill, engine and hooks into `.claude/` (merged into
  existing settings, `--check` for drift); SessionStart warns "LFE NOT ACTIVE" in repositories with LFE documents but
  no `.lfe/`; the skill description names concrete triggers; installed copies now find their own templates.
- **Design tools (#30):** `references/09-design-tools-and-fallback.md`: Penpot as the default free, provider-neutral
  MCP path, dated plan limits (Figma Starter quota counts writes; one mode per collection), automatic fallback rules
  and exact Penpot setup steps. `figma`/`penpot` baselines now require `sourceUrl`.
- **`lfe gate G5` (#31):** Lighthouse and axe-core JSON against a budget (`.lfe/budget.json`), unittest-style
  summary so `lfe run` records it as an evidence receipt.
- **Numbering:** optional `state.numbering.decisionFloor` keeps ledger ids after ids the project already uses.

## 0.2.0 — 2026-10-19

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
- **Method:** delegated execution and tool-blocker recovery (`references/08`), gate acceptance with tracked
  exceptions, 17 evaluation scenarios.
- **Known limits:** real Claude Code sessions (hooks and evals) not yet executed; `vs01-proof` approvals are
  simulated; Windows untested.

### Included from the v0.1.4-rc.1 method track

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
