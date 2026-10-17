# Security policy / Política de segurança

## Reporting a vulnerability privately / Comunicação privada

**Do not post exploit details, secrets or private proof-of-concept material in public Issues, PRs or Discussions.** Use GitHub's [Security Advisories](https://github.com/merlinfachetti/layout-first-engineering/security/advisories) and **Report a vulnerability** when the maintainer has enabled *Private vulnerability reporting* (Settings → Advanced Security). If that button is unavailable, do not disclose sensitive details publicly. Request a private contact route through the maintainer's GitHub profile, without sharing the vulnerability itself in a public channel; if no suitable channel is available, wait for private reporting to be enabled.

Include a concise impact assessment, affected version, reproduction steps with redacted or synthetic data, and a suggested mitigation when possible. No SLA or security-response deadline is guaranteed; the maintainer will handle reports on a best-effort basis and may publish a coordinated advisory once a fix or mitigation is available.

## Scope and security boundaries / Escopo

This is an Agent Skill and small offline validator, **not** a hosted service or independently verified security product. An instruction file does not itself authorize tool calls, account access, payments, deployments, processing personal data or network actions. Real access depends on the host's permissions and the user's explicit approval.

High-priority threats include:

- Prompt injection from third-party reference text, code, web pages, design assets, issue bodies or tool output.
- Malicious changes in incoming pull requests or dependencies.
- Exposed tokens, credentials, customer data or AI conversation history.
- Unexpected writes, external spending, deployment or destructive operations by an agent.
- Fabricated connector use, pricing, completed tests or production readiness.

## Maintainer precautions / Precauções

- Keep CI read-only with minimum GitHub token permissions; do not execute PR-submitted code with privileged secrets or `pull_request_target` unnecessarily.
- Never add credentials to the repository. Do not grant broad GitHub Apps or Actions write scopes unless essential.
- Review changes to `.github/workflows`, scripts and skill instructions with extra care.
- Use branch protection, minimal dependencies, tagged releases and tested rollback procedures where relevant.
- Use private advisories for coordinated disclosures; do not promise a vulnerability can be deleted from public forks or Git history.

See [PRIVACY.md](PRIVACY.md), [GOVERNANCE.md](GOVERNANCE.md) and [docs/OPEN-SOURCE-MAINTENANCE.pt-BR.md](docs/OPEN-SOURCE-MAINTENANCE.pt-BR.md).
