# Repository stewardship throughout S0–S9 (optional, tool-dependent)

**Purpose:** maintain a traceable project history without turning design discovery into an infrastructure project. This is a behavioral protocol, not an automatic GitHub connector. If the user has not requested or authorized a repository, keep state locally and defer remote operations.

## S0 repository audit — before any Git write

1. Inspect the *actual* workspace and account: canonical absolute path, `git status --porcelain=v1`, `git branch --show-current`, `git remote -v`, `git log -1`, `gh auth status` when available. Obtain remote visibility, default branch, history, permissions, rulesets, and CI status using available tools. Mark unknown values as unknown, not confirmed.
2. Compare workspace contents with the remote. A URL in a prompt is *not* evidence that the remote is empty. If `git log` fails, stop and diagnose an unborn branch; do not guess that a branch exists.
3. Verify Git author and committer identity per repo. Honor the user's explicit authorship preference; **never append synthetic `Co-authored-by` trailers**. Retain legitimate human contributors' attribution. Avoid publishing private email when a verified noreply is available and desired.
4. Inspect `.gitignore` and staged paths for secrets, `.env`, tokens, sensitive data and unlicensed assets. Never log, commit or paste credentials. Flag questionable files; do not silently delete anything.
5. Log capability as `verified | limited | unavailable | unknown`, with evidence and dates when known. Store project Git decisions in `REPOSITORY_STATE.md` and reference them from `PROJECT_STATE.md`.

## First publication

- Stage S0–S2 documents and visual samples may be versioned **before production code**, if the user opted into repository management.
- Require explicit approval for the initial remote publication: account, destination URL, visibility, branch, file scope, attribution and expected exposure.
- For an existing **truly empty** remote: create a minimal initial commit on `main` only if the user authorizes exactly this. Verify remote and account again before pushing. If populated, follow the existing history and protection; never replace or reinitialize it.
- Distinguish `prepared`, `committed locally`, `pushed to branch`, `PR open`, `merged`, `synced local` and `released`. They are not interchangeable.

## Routine loop after first publication

1. Start from updated main (`fetch`, compare, `pull --ff-only` when safe). If working tree is dirty or commits diverged, stop and explain safe options, preserving all files.
2. Create a named topic branch for an approved deliverable. Make the smallest coherent change. Run relevant verification and record exact outcomes.
3. Commit with configured user attribution; create a pull request through available authenticated tools; link related approved Issues and relevant design decisions.
4. Check PR file diff, branch protections, human review requirements, CI and billable consequences. Merge only with appropriate authorization and **passing required checks**. Never use administrative bypass merely because checks fail; diagnose instead.
5. Confirm merge from remote with actual PR status and merged SHA; then switch/pull local `main` safely. Update the state record with confirmed SHA and outcome. Never say synchronized solely because a push command was attempted.
6. Ask only for meaningful authorization decisions. When the user explicitly delegates routine commits/PRs within bounded scope, don't request repetitive permissions, but irreversible, costly, privacy-changing or production actions remain separate.

## CI troubleshooting matrix

| Observation | What it establishes | Next action |
| --- | --- | --- |
| Local unit tests pass | The local checked-out files passed those tests | Do not label CI green; inspect remote check |
| Workflow job fails in seconds with zero steps | Runner likely did not execute job steps | Inspect workflow status, runner provisioning, account billing/restrictions, usage, org policy and GitHub incident status; root cause **unconfirmed** until evidence |
| Steps ran, failing test identified | Test/code failure has actionable log | Reproduce locally, fix, rerun checks |
| Check missing/pending | Required status is not confirmed | Confirm check name, integration, event, triggers, GitHub Actions enablement and workflows |
| PR requires another human approval | Author cannot approve own PR | Seek authorized human reviewer or an approved repository governance change; never fabricate sign-off |
| CI externally blocked | No verified required check success | Keep PR open; record blocker and mitigation; do not silently bypass |

**Billing restriction** may explain zero-step failures but must not be presented as confirmed without a provider message. Do not suggest paying for services without explaining costs and verifying entitlement.

## Issues and roadmap

- Categorize `idea`, `investigation`, `approved work`, `bug` or `risk`; keep exploratory ideas in a document until they need tracked action.
- Issues require purpose, scope, acceptance criteria, stage/gate and dependency, not one Issue per conversation question. Link PRs to approved Issues. Use milestones only where they improve coordination.
- Use read-only discovery before changing community settings, rulesets, visibility or enabling third-party integrations. Owner decides these separately.

## Canonical workspace and handoff

- If the user changes the project directory, confirm old and new paths, compare contents and open changes, update relative links and Git remote configuration, and mark one canonical source of truth. Keep the old copy until the user decides otherwise. Do not write into the historical workspace.
- Maintain an evidence ledger with `intent → authorization → execution → verification` and URI/path/SHA; record failures as failed, never as succeeded. For Figma record file/node and artifact type; editable frame is not proof of a working prototype.
- Without Git, network or credentials, prepare a diff, offline artifacts and precise manual instructions. Never pretend remote operations happened.

## Guardrails

- No force push, destructive reset/clean, secrets, unauthorized visibility changes or production deployment.
- GitHub and other providers are **optional**; don't require creating an account to explore design.
- Respect the project's actual CI and branch policies, not assumptions copied from another repository.
