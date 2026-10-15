# Security policy

LFE is a prompt/workflow skill plus a small read-only standard-library validator. It does not need secrets, persistent cloud access, network calls, elevated permissions or third-party packages to install.

**Trust boundary:** The skill text does not grant its agent permission to access accounts or act on your behalf. Connected apps, terminal environments and remote documents may carry sensitive data. Review what you allow the host agent to read or write.

Never commit API keys, passwords, .env files or customer datasets. Report potential vulnerabilities by opening an issue with a sanitized example, or privately contacting the repository maintainer once a contact channel is published. Do not publish exploit details or customer information in issues.

Threats to evaluate include prompt injection through reference pages/design files, unauthorized tool actions, secret exfiltration, inaccurate price claims, invented deployment success and unsafe scripts. The included `verify_project.py` checks formatting and gate states, not authorization authenticity or system security.
