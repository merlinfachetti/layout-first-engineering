# `lfe` — the engine that locks, remembers and proves

`lfe` is the executable part of the Layout-First Engineering skill. The skill says **what** the agent
should do; `lfe` enforces in code what it **cannot** do without you:

- **locks:** production code only after G2, G3 and G4 are approved and still valid;
- **remembers:** `.lfe/` records where the project stopped, and a new session resumes there;
- **proves:** every test run becomes a verifiable receipt; no proof, no "passed".

Requirement: Python 3.10+, nothing to install (standard library only). Full Portuguese guide:
[LFE-CLI.pt-BR.md](LFE-CLI.pt-BR.md).

## Where the command lives

| Install | Command |
|---|---|
| Claude Code, personal | `python3 ~/.claude/skills/layout-first-engineering/scripts/lfe.py` |
| Claude Code, project | `python3 .claude/skills/layout-first-engineering/scripts/lfe.py` |
| Repository clone | `python3 layout-first-engineering/scripts/lfe.py` |

## Who runs what

| Who | Commands |
|---|---|
| **Agent** | `init`, `artifact`, `propose`, `record-chat-approval G1`, `run`, `trace`, `render`, `next`, `question`, `handoff`, `status` |
| **You, in your own terminal** | `approve`, `reject`, `revoke`; confirming an `import` that carries approvals |

`lfe approve` refuses to run without an interactive terminal and asks you to type the gate name.

## Flow

1. `lfe init my-idea "My idea"`
2. `lfe artifact DIR-001 --kind direction-set --path .lfe/directions/DIR-001.json` — the agent registers content by hash.
3. `lfe propose G1 --artifact DIR-001` — a gate bound to that exact content.
4. G1: `lfe record-chat-approval G1 --quote "..."`. G2–G6: **you** run `lfe approve G2`.
5. `lfe status` — computed gates, reasons, `production code: locked|unlocked`.
6. Content changed after approval: the gate turns `stale` and production code locks again.
7. `lfe stage S6` — refused unless G2, G3 and G4 are valid.
8. `lfe run TEST-003 --req FR-001 -- <command>` — evidence receipt; missing tools are `not_executed`.
9. `lfe trace --check` — every implemented requirement needs a passing receipt; G5 requires it.
10. `lfe next`, `lfe question`, `lfe handoff` — resumable context; Claude Code hooks in
    [adapters/claude-code/session-hooks.md](../adapters/claude-code/session-hooks.md).

Portable bundle: `lfe export --out p.lfe.json` and `lfe --root ../copy import p.lfe.json` (you confirm any approvals it carries).
Try it without deciding anything: `lfe demo examples/vs01-leituras --workdir /tmp/lfe-demo` (simulated approvals, always labelled).

Exit codes: `0` ok · `2` usage or no human terminal · `3` denied by gate/stage rules · `4` incompatible contract ·
`5` integrity violated · `6` contract violated.

Limits: someone with full disk access can forge files; `lfe` makes that **detectable** (hash chain), not impossible.
Contracts and rules: [RFC-0001](rfcs/0001-core-contracts.md), [RFC-0002](rfcs/0002-vertical-slice-01.md).
