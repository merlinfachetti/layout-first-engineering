# LFE candidate behavioral validation matrix

**Important distinction:** `tests/evals/scenarios.json` contains **12 evaluation contracts, not 12 successful LLM evaluations**. `python -m unittest` checks the fixture structure and static skill policies. No model-run is marked validated until someone runs it on Codex/Claude/Gemini/etc. and links the actual outputs.

## Running the offline checks

```bash
python3 -m unittest discover -s tests -v
python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md
```

For an actual project's approved G1 baseline:

```bash
python3 layout-first-engineering/scripts/verify_visual_baseline.py docs/design/APPROVED_VISUAL_BASELINE.md --approved
```

The validator checks relative images and basic document markers, **not** Figma permissions, art quality or human approval truthfulness. Don't run `--approved` against the template itself.

## How to evaluate with real agents

1. Select a scenario from `tests/evals/scenarios.json`.
2. Record client/model/version, skill commit SHA, permissions, environment and attached connectors.
3. Run the input in a **sandbox/new throwaway project**, avoiding unauthorized external writes.
4. Inspect actual responses, generated files and tool logs for each `expected`/`must_not` clause.
5. Record `pass/fail/blocked/not_run` with evidence URL/file and observed shortcomings. Human reviewers decide pass/fail on behavioral evidence.
6. If an instruction fails, create a focused regression test before revising the skill; repeat with no connector and with real connectors when available.

## Executed evidence (as of 2026-10-19)

| What | Where it ran | Result | Evidence |
| --- | --- | --- | --- |
| Engine, contracts, policy, handoff, plugin, studio (unit/contract tests) | GitHub Actions, Python 3.10 and 3.12 | **pass** (200+ tests) | `lint-and-check-gates` on `main` |
| VS-01 end-to-end proof in Chromium (TEST-001…005, FR-001…005, UX-001, SEC-001, NFR-001) | GitHub Actions `vs01-proof`, ubuntu-24.04, Playwright 1.49.1 | **pass**, trace complete; approvals in this run are **simulated** | run `39231842025` on `8660d03`, artifact `vs01-proof` (receipts, TEST_REPORT.json) |
| Same proof without a browser | maintainer Mac, Python 3.11 | E2E `not_executed` (`tool_unavailable:playwright`), trace incomplete, exit 6 — as designed | `tests/test_vs01_proof.py` |
| PreToolUse / SessionStart hooks via the exact plugin command | local shell with Claude Code hook payloads | deny before gates, allow docs, exit 2 when engine missing, context injected | `tests/test_plugin.py` |
| Real headless Claude Code session (`scripts/agent_evals.py`, 5 cases) | maintainer Mac, Claude Code 2.1.221 | **blocked** — CLI login expired ("Failed to authenticate") | rerun after `claude` → `/login` |
| `claude plugin eval` | maintainer account | **blocked** — feature in early access for this account | — |

## Planned real-agent runs

| Client | Skill commit | Scenario | Result | Evidence | Reviewed by |
| --- | --- | --- | --- | --- | --- |
| Codex | pending | G1-hybrid-theme-baseline | not_run | — | — |
| Claude Code | pending | repo-ci-zero-steps | not_run | — | — |
| Gemini CLI | pending | S2-interaction-contract | not_run | — | — |

These are planned runs, not successful compatibility claims.
