# Contributing / Como contribuir

Thank you for making Layout-First Engineering more useful, safe, and vendor-independent. All experience levels are welcome. Read [GOVERNANCE.md](GOVERNANCE.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md) before contributing.

## Before you begin / Antes de começar

1. Check [Issues](https://github.com/merlinfachetti/layout-first-engineering/issues) and [ROADMAP.md](ROADMAP.md). For substantial behavior changes, open an Issue describing the user problem before writing code.
2. Pick one scoped issue, fork the repository (or create a branch with explicitly granted write access), and keep each PR small.
3. Avoid real personal data, proprietary prompt/context, credentials or unlicensed images. Use synthetic examples and redact screenshots/logs.
4. Only contribute work you have the right to submit under the project's [MIT license](LICENSE). Preserve licenses and copyright notices of external assets and code; when unsure, ask first.
5. Test in at least one real AI host for behavior changes and report **client, version/date, connector availability and observed behavior**. Do not assume that instructions alone guarantee identical execution across models.

## Development / Desenvolvimento

```bash
python3 -m unittest discover -s tests -v
python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md
```

- Keep `SKILL.md` concise and stage-specific explanations in `references/`.
- Maintain design-first approvals; no implementation before approved G2/G3/G4 and no release without G6.
- Add or update behavior scenarios and relevant documentation with any change in logic.
- Prefer auditable citations for costs, supported tool claims, and policy details.
- Do not introduce vendor lock-in, unexpected expenses or permissions without providing an optional path and discussing trade-offs.
- Check accessibility, security, and unintended external actions.

## Pull Request checklist / Lista do PR

- State the goal, impacted stage, behavior before/after, verification evidence and compatibility limitations.
- Review whether the change could leak data, grant unwanted autonomy or break design handoff.
- Disclose **AI-assisted work if material** to help reviewers scrutinize licensing and quality; this is a process note, **not AI co-authorship**.
- Link related Issues and attach sanitized screenshots for visual changes when relevant.
- Keep commits and authorship truthful: human contributors own their changes; never impersonate a different author. The original project is maintained by [@merlinfachetti](https://github.com/merlinfachetti).

## Review, rights and license / Revisão e licença

Opening a PR offers a proposal; merging is subject to maintainer review, repository rules, tests and long-term compatibility. The project does **not** require a CLA, copyright assignment, or sign-off at this time. By contributing, you confirm you are authorized to submit the material under the project's MIT license. Third-party contributions retain their actual human attribution and their relevant copyright notices. The initial creator remains credited for the initial work, **without claiming exclusive authorship of future community work**.

For privacy issues see [PRIVACY.md](PRIVACY.md). For vulnerabilities, never open a public Issue; use [SECURITY.md](SECURITY.md). For normal questions, use [SUPPORT.md](SUPPORT.md).
