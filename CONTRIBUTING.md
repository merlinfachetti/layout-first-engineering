# Contributing to Layout-First Engineering

Thank you for helping create a useful, secure, vendor-independent skill.

## Principles

1. Keep the owner in control, with high-value questions and no deceptive autonomy.
2. Preserve genuine design-first gating, even when a model defaults to writing code.
3. Avoid provider-specific mandates. Describe how to detect capabilities and fall back safely.
4. Make costs verifiable, with currency, quantity assumptions and sources.
5. Build proportionate engineering practices; don't turn simple websites into infrastructure projects.
6. Keep `SKILL.md` concise and route detailed stages to focused `references/` files.
7. Avoid collecting personal data or credentials in examples and fixtures.

## Workflow

- Open an issue explaining the failure or improvement, with stage and an expected agent response.
- Include a minimal reproducible conversation without personal data, when possible.
- Update the reference, template and sample scenario together if behavior changes.
- Run `python3 -m unittest discover -s tests -v`.
- For behavioral changes, manually test with at least one available agent; **do not claim cross-model compatibility unless tested**. Report model/client/version and connector availability.

## Contribution scope

Welcome: internationalization, empirical prompt-evaluation cases, anti-hallucination checks, accessibility, privacy, project-management workflows, cost-model improvements and integrations documented with actual official references. Do not add vendor lock-in without an optional path.

## Attribution and maintainership

Original creator and maintainer: [Merlin Fachetti (@merlinfachetti)](https://github.com/merlinfachetti). Human contributions are welcome through pull requests and keep attribution to their actual authors. Do not add AI systems as commit co-authors. Merging is reviewed and controlled by the maintainer; automated CI must not push code.
