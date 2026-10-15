# Layout-First Engineering — installation and usage guide

**Created and maintained by [Merlin Fachetti (@merlinfachetti)](https://github.com/merlinfachetti).** [Portuguese complete guide](INSTALACAO-E-USO.pt-BR.md).

LFE is a **portable workflow specification**, not a connector, subscription, background agent or production-code generator on its own. A host must support Agent Skills (or accept the fallback prompt), and relevant design/repository tools require separate authorization.

## What happens

S0 vision and tool audit → S1 visual concepts (**G1** approval) → S2 UI prototypes (**G2**) → S3 deep product discovery and scope (**G3**) → S4 architecture, risk and cost comparison (**G4**) → S5 delivery planning → S6 incremental engineering → S7 verification (**G5**) → S8 launch preparation and explicit deployment permission (**G6**) → S9 ongoing iteration.

**Rules:** start with visuals, ask only timely questions, present alternatives and costs transparently, never assume permission, never code the production application before G2+G3+G4, never deploy before G6, persist progress in `PROJECT_STATE.md` when possible.

## Install from a local clone

Clone the repository, then run these from its root (the directory containing `README.md` and `layout-first-engineering/`):

**Claude Code (user scope):**

```bash
mkdir -p ~/.claude/skills
cp -R layout-first-engineering ~/.claude/skills/
```

Project scope: copy to `.claude/skills/` in the target project. Claude.ai web (eligible accounts): upload **the skill ZIP** in Settings → Features → Skills / Custom Skills.

**Gemini CLI (user scope):**

```bash
mkdir -p ~/.gemini/skills
cp -R layout-first-engineering ~/.gemini/skills/
```

Project scope: copy to `.gemini/skills/` or `.agents/skills/`. Confirm discovery with `/skills list`; use `/skills reload` when needed. After the repo is published, supported CLI versions can use:

```bash
gemini skills install https://github.com/merlinfachetti/layout-first-engineering.git --path layout-first-engineering
```

**OpenAI Codex (user scope):**

```bash
mkdir -p ~/.agents/skills
cp -R layout-first-engineering ~/.agents/skills/
```

Project scope: copy to `.agents/skills/`. Invoke `$layout-first-engineering` where supported.

**ChatGPT web:** Native Skills upload is documented for eligible Business, Enterprise, Healthcare and Edu accounts, subject to workspace settings; check Plugins → Skills → Create → Upload. Do not assume Plus has the feature. If missing, use `FALLBACK_SINGLE_PROMPT.md` in a project or conversation. This is a non-native fallback.

**DeepSeek, Qwen and other models:** Their compatibility depends on the *agent client*, not model branding. If the client supports the Agent Skills standard, place the folder in its documented skills directory. Otherwise paste `FALLBACK_SINGLE_PROMPT.md`, provide the necessary stage references, and manually persist the state/handoff.

## Start a project

```text
Use layout-first-engineering to develop [PRODUCT] for [USERS].
Begin with visual exploration before selecting technologies.
Ask only the next necessary question, explain your recommendation,
and preserve approved decisions. Do not start production coding
without G2/G3/G4 approval, or deploy without G6.
Tell me which design/repository connectors you actually have.
```

## Resume elsewhere

Share `PROJECT_STATE.md`, `DESIGN_HANDOFF.md` and `DECISIONS.md`, plus any relevant product/cost/architecture documents. Tell the next agent: `Resume using Layout-First Engineering from these artifacts. Validate the current gate and do not infer approvals or restart answered questions.`

## Keep it updated

A manually copied Skill **does not auto-update** from GitHub. Review the changelog, refresh the skill folder, verify discovery, and review any script/tool changes before activation. Publishing and maintenance on macOS are described in [the Portuguese GitHub guide](PUBLICACAO-GITHUB-MAC.md).

## Official references

- Agent Skills: https://agentskills.io/specification
- Claude: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Gemini CLI: https://geminicli.com/docs/cli/using-agent-skills/
- Codex: https://developers.openai.com/blog/skills-agents-sdk
- ChatGPT: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
