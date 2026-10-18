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

| Client | Skill commit | Scenario | Result | Evidence | Reviewed by |
| --- | --- | --- | --- | --- | --- |
| Codex | pending | G1-hybrid-theme-baseline | not_run | — | — |
| Claude Code | pending | repo-ci-zero-steps | not_run | — | — |
| Gemini CLI | pending | S2-interaction-contract | not_run | — | — |

These are planned runs, not successful compatibility claims.
