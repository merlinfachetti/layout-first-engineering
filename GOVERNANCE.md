# Governance / Governança

**Project:** [Layout-First Engineering](https://github.com/merlinfachetti/layout-first-engineering)  
**Original creator and lead maintainer:** [Merlin Fachetti (@merlinfachetti)](https://github.com/merlinfachetti)  
**License:** MIT ([LICENSE](LICENSE))

## Decision model / Modelo de decisões

- Anyone may propose improvements through Issues, Discussions and Pull Requests.
- The lead maintainer sets scope, roadmap, release policy, quality gates, and merge decisions for the official repository.
- A public PR is **a proposal**, not a right to merge. Decisions should state the relevant design, security, maintenance or compatibility rationale.
- Require passing tests and evidence for model/connector-dependent behavior. No untested cross-platform compatibility claims.
- Design-first checkpoints, user approvals, reproducibility, privacy and non-deceptive tool use are project invariants.
- For major direction changes, discuss and record the rationale in an Issue before implementation.
- If reviewers are added in future, permissions will be granted individually and may be revoked. This file does not confer GitHub permissions.

## Copyright and authorship / Direito autoral e autoria

The original MIT copyright notice credits the original creator; later human contributions retain their rightful authorship and copyright. Contributions incorporated into this MIT project must be offered under compatible terms with the contributor's right to license the material. **No Contributor License Agreement (CLA), assignment of copyright, or transfer of ownership is required at this stage.** Contributors should not upload third-party assets or code unless authorized and license-compatible.

The maintainership claim does **not** imply exclusive ownership of all third-party contributions or control of downstream forks allowed under MIT. Using an AI assistant does not make the AI a maintainer or co-author. Contributors remain responsible for evaluating rights in and quality of AI-assisted material. Do not add AI services as `Co-authored-by` in maintainer commits.

## Review and release / Revisão e versões

- Default branch: `main`, protected by the `protect-main` ruleset.
- Work occurs on an individual feature branch or fork and enters via Pull Request.
- Review code/documentation, run CI and check permissions and sensitive data before merge.
- The owner has an administrative PR-only bypass. Use it sparingly and **never as a substitute for checking CI and security**.
- Release versions follow semantic versioning *where applicable*. Publish notes and distributable skill archives only after manual verification.
- No third-party has an automatic right to merge or deploy; no agent may modify the repository autonomously.

## Sustainability / Sustentabilidade

The project is volunteer-maintained. Priority may be given to security issues, regressions, accessibility, clear usability problems and tested compatibility improvements. Proposed expenses, hosted services or paid dependencies must be reviewed and approved by the maintainer. See [ROADMAP.md](ROADMAP.md) and [SUPPORT.md](SUPPORT.md).
