# Design tools, their limits and automatic fallback (S1–S2, G2)

Load this when a stage needs editable design work. Goal: the person only authorizes; the agent picks the tool, detects the limit, switches, and explains in one short message what changed and what (if anything) the person must do.

## 1. Pick the tool by capability, not by habit

Record each tool in `state.capabilities` (`status`: `available | limited | unavailable | unknown`, with `checkedAt`, `method`, `blockedReason`). Check by *doing a cheap read*, never by assuming a connector works.

Order of preference for editable UI work an agent can drive:

1. **Penpot** (default free path). Open source (MPL-2.0), self-hostable, the official MCP server is free, and the cloud plan is free with no file limits. It speaks plain MCP, so it works with any MCP client (Claude, Codex, Cursor, VS Code, OpenCode and others), whichever model provider the person uses.
2. **Figma** when the person has a paid seat, or for read-only inspection of an existing Figma file.
3. **Local HTML/CSS prototype** with tokens (`prototype/**`, always labelled as a prototype) plus real screenshots. Always available; needs a recorded `mediumDecisionId` (see the baseline contract).

### Known limits (verify again when a run fails; dated facts go stale)

| Tool | Plan | Limit that matters for an agent | Observed / source |
| --- | --- | --- | --- |
| Figma | Starter (free) | MCP calls are a small monthly quota and **write calls (`use_figma`) count against it**; the quota can end in one screen build. One mode per variable collection, so light/dark tokens need two collections or a paid plan. | Field use, 2026-11-26 (quota exhausted mid-build) |
| Figma | Professional and up | Writes allowed; still rate limited | Figma docs |
| Penpot | Free (cloud) | No file limit; storage and team caps apply; MCP has no stated quota. The MCP plugin runs inside an open Penpot tab, and only one tab owns the connection. | penpot.app/pricing and help.penpot.app/mcp, read 2026-11-26 |
| Penpot | Self-hosted | Same features; you run it | penpot.app self-host docs |
| Local HTML | — | No editable nodes for designers; screenshots are the visual evidence | — |

## 2. Detect the limit and switch (no person in the loop for routine fallback)

Treat any of these as **limit reached**: HTTP 429, or "quota", "rate limit", "upgrade" or "plan" in an MCP error; writes refused on a read-only plan; a variable collection refusing a second mode.

When it happens:

1. Stop writing to that tool at once. Do not retry the same call in a loop.
2. Record it: `capabilities.figma = {status: limited, blockedReason: "<exact error>", checkedAt, method}`.
3. Save what already exists (screenshots, exported tokens) as evidence, so no work is lost.
4. Switch to the next tool in §1 that is `available`. If none is set up, use the local HTML prototype for this session and offer the Penpot setup in §3.
5. Tell the person in one message: what hit the limit, what you switched to, what it costs (nothing on the free paths) and the single action needed from them, if any. Never ask the person to pay to continue; offer it only as an option with its price and source.

## 3. Penpot setup the person does once (exact steps)

Account creation and access keys belong to the person; the agent never creates accounts or handles the key.

1. Open https://design.penpot.app and create a free account (or sign in).
2. Click the avatar at the bottom left → **Your account** → **Integrations** → **MCP Server** → set **Status** to **Enabled** → **Generate key**. The key is shown only once.
3. Copy the server URL shown there. It embeds the personal key, so treat it as a secret: paste it **only** into the AI client's connector settings, never into a chat message or a file in the repository.
4. Add it to the AI client as a remote MCP server (Claude: Settings → Connectors → Add custom connector → paste the URL; other clients: their MCP settings, or `npx -y add-mcp -g -n penpot <URL>`).
5. In Penpot, open the project file and keep that tab open while the agent works (the MCP plugin acts on the page in focus).

Local alternative, no hosted key: run `npx -y @penpot/mcp@stable`; in a Penpot file choose **Plugins → Load from URL** → `http://localhost:4400/manifest.json` → **Connect to MCP server**; the client then uses `http://localhost:4401/mcp`.

## 4. Building the G2 baseline in a design tool (quota-aware order)

1. Tokens first (color, type, spacing, radius, motion; light and dark as separate sets or themes), then components, then one screen per required state.
2. After each screen, export or screenshot it into the repository (`docs/evidence/` or `prototype/previews/`), so the evidence survives a quota stop.
3. Baseline contract: `medium: penpot` or `figma`, `sourceUrl` set to the file link (required for those media), previews listed in `files[]` with hashes. Then `lfe artifact DESIGN-### --kind experience-baseline --path ... --refresh-files` and `lfe propose G2`.
4. Report observed fidelity honestly: editable frames are not an interactive prototype unless an interaction receipt exists.
