# v0.1.4-rc.1 candidate — integration handoff

This is a prepared candidate, **not installed on your Mac, not pushed to GitHub and not released**. Compare with `main` before applying. Local Mac file access is not implied by this artifact.

## Objective and scope

Improve G1 visual evidence, continuous optional repository stewardship, CI diagnostics, hybrid themes, interactive components, asset provenance and evaluated agent behavior without weakening gates G1–G6.

## Safe steps on Mac

1. Update local `main` only when `git status --short` is empty; avoid destructive reset/clean.
2. Create branch `feat/lfe-evidence-and-repo-workflow` from updated `main`.
3. Unzip this candidate **in a separate staging folder**, not over your repository. Review with `diff -ru` or copy only reviewed paths. If the official repo has progressed, reconcile manually rather than overwriting newer files.
4. Ask your coding agent to inspect and integrate the candidate changes with the **current local branch**; never allow it to blindly replace maintained content.
5. Run `python3 -m unittest discover -s tests -v`, `python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md` and the real-agent scenarios in `docs/VALIDATION-MATRIX.md`.
6. Check `git diff --check`, file diffs and developer identity. Use a focused commit, push to the feature branch and open a PR. Keep main untouched until review/CI passes.
7. Only after human review and verified CI/agent evaluation, decide whether to mark v0.1.4 stable.

Do not bypass failed remote CI, publish private Kizunote data, claim legal compliance or fabricate any test.
