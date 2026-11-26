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
| **Agent** | `init`, `adopt`, `artifact`, `propose`, `record-chat-approval` (G1; G2–G6 when enabled), `chat-approvals`, `run`, `trace`, `render`, `next`, `question`, `handoff`, `status` |
| **You, in your own terminal** | `approve`, `reject`, `revoke`; confirming an `import` that carries approvals |

`lfe approve` refuses to run without an interactive terminal and asks you to type the gate name.

## Flow

1. `lfe init my-idea "My idea"`
2. `lfe artifact DIR-001 --kind direction-set --path .lfe/directions/DIR-001.json` — the agent registers content by hash.
3. `lfe propose G1 --artifact DIR-001` — a gate bound to that exact content.
4. G1: `lfe record-chat-approval G1 --quote "..."`. G2–G6: **you** run `lfe approve G2`, or, when you only work
   through chat, reply with the confirmation code `propose` printed (see "Chat-only owners" below).
5. `lfe status` — computed gates, reasons, `production code: locked|unlocked`.
6. Content changed after approval: the gate turns `stale` and production code locks again.
7. `lfe stage S2` — each stage needs the gate that closes the one before it (S2 needs G1, S3 G2, S4 G3,
   S5–S7 G4, S8 G5, S9 G6); `lfe stage S6` unlocks production code. Going back is always allowed.
8. `lfe run TEST-003 --req FR-001 -- <command>` — evidence receipt; missing tools are `not_executed`.
9. `lfe trace --check` — every implemented requirement needs a passing receipt; G5 requires it.
10. `lfe next`, `lfe question`, `lfe handoff` — resumable context; Claude Code hooks in
    [adapters/claude-code/session-hooks.md](../adapters/claude-code/session-hooks.md).

## A project already under way: `lfe adopt`

`lfe init` starts at S0. For a project with its own `PROJECT_STATE.md`, `DECISIONS.md`, prototypes and screenshots:

```bash
lfe adopt --dry-run   # the plan, validated against the contracts; writes nothing
lfe adopt
```

It reads the gate table tolerantly (extra columns, `aprovado ✅`, `Etapa atual: S5`…), continues ledger ids after
the highest `DEC-###` already in your Markdown, generates draft typed artifacts in `.lfe/adopted/` (directions from
prototypes, baseline screens from `docs/evidence/*.png` with their real size, requirements from FR-/NFR- ids or the
MoSCoW table, ADRs and the G5 report as they are), and proposes every gate the Markdown says was approved.
Those approvals are recorded as `imported-legacy`, keep the project's place up to S5, and unlock nothing until you
reconfirm each one (`lfe approve G2`, or the chat code). `.lfe/ADOPTION.md` lists what to review.

## Chat-only owners (mobile, cloud sessions)

Off by default. When the person has no terminal, they opt in once, in their own words:

```bash
lfe chat-approvals enable --gates G2,G3,G4,G5,G6 --quote "<their message, verbatim>" --message-ref "<message id or link>"
```

From then on `lfe propose G3 …` prints a code such as `G3-7f3a2c`. The person replies `aprovo G3-7f3a2c` and the
agent records it with `lfe record-chat-approval G3 --quote "aprovo G3-7f3a2c" --message-ref "<id>"`. The code is
derived from that proposal's hash, so an approval only matches the content that was proposed; new content means a
new proposal and a new code. Decisions are stored as `chat-quote`, `authenticity: unverified`, and stop counting if
chat approvals are disabled. Trade-off: the terminal *prevents* self-approval; a chat quote makes it *detectable*.

Hybrid G1 without JSON: `--primary A --theme-variant dark=A --theme-variant light=B --complementary "C=collections"`
(`lfe record-chat-approval --help` shows the JSON shape too).

Portable bundle: `lfe export --out p.lfe.json` and `lfe --root ../copy import p.lfe.json` (you confirm any approvals it carries).
Try it without deciding anything: `lfe demo examples/vs01-leituras --workdir /tmp/lfe-demo` (simulated approvals, always labelled).

Exit codes: `0` ok · `2` usage or no human terminal · `3` denied by gate/stage rules · `4` incompatible contract ·
`5` integrity violated · `6` contract violated.

Limits: someone with full disk access can forge files; `lfe` makes that **detectable** (hash chain), not impossible.
Contracts and rules: [RFC-0001](rfcs/0001-core-contracts.md), [RFC-0002](rfcs/0002-vertical-slice-01.md).
