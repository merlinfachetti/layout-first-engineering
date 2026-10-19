# Delegated execution and tool-blocker recovery (S1–S7)

**Purpose:** the person pilots product, rules and approvals; the agent produces design, code, tests,
fixes and documentation. Delegation removes busywork from the person. It never removes a gate.

## 1. Delegation contract

Record it once in `PROJECT_STATE.md` (or `lfe next` / `lfe question` when the engine is available):

- **The person decides:** product intent, audience, business rules, priorities, trade-offs with cost,
  privacy or risk, and every gate (G1 may come from a chat quote; G2–G6 only through `lfe approve`
  in their own terminal when the engine is installed).
- **The agent executes:** design artifacts, prototypes, code inside approved scope, tests, evidence,
  documentation, and tool operation, including repairs after tool failures.
- **Ask only material decisions.** Do not hand the person mechanical work: editing Figma layers,
  copying files, renaming nodes, running commands the agent can run itself, or clicking through a
  tool to "check one thing". If a step truly needs the person's hands (login, paid plan, physical
  device), say exactly why, once, with the shortest path.

## 2. When a tool blocks (quota, auth, permission, outage, missing connector)

1. **Detect and record honestly.** Mark the capability `limited` or `unavailable` with the reason
   and time (`capabilities` in `.lfe/state.json`, or the tools line of `PROJECT_STATE.md`).
   Use `assets/TOOL_BLOCKER.md` when the blocker affects a deliverable.
2. **Never claim the blocked work happened.** No "fixed in Figma" without a verified write; no
   screenshot or link that was not produced.
3. **Recover with an authorized alternative, in this order:**
   - another already-authorized tool that produces the same artifact type;
   - a **coded throw-away prototype** (local HTML/CSS/JS, no production architecture, no real data,
     no paid service, no deploy), clearly labelled `prototype`, so interaction can be reviewed and
     tested while the design tool is down. The policy hook treats `prototype/` as non-production;
   - a precise written specification, marked as such.
4. **Advance another front** that does not depend on the blocked tool (requirements, risks,
   accessibility review, test plan) instead of idling or asking the person to operate the tool.
5. **Retry and reconcile.** When the tool returns, port the changes back, compare, and update the
   baseline revision. A new revision makes approvals bound to the old one `stale`: propose again.

## 3. Verify the exact component before asking for a fix

Screens hide variants, instances and nested frames. Before reporting a defect or asking for a
correction, re-inspect and record: node or file, parent, component and **variant**, state,
effective size **and clickable area** (minimum 44 × 44 CSS px for touch targets), and the viewport.
An old diagnosis is a hypothesis until re-inspected. A screenshot proves the selected element,
not its siblings or other variants.

## 4. Approving a gate with tracked exceptions

A person may approve a gate while knowing some items are still open (for example, "proceed with
this visual baseline; the click-through is not tested yet"). Record it with
`assets/GATE_ACCEPTANCE_WITH_EXCEPTIONS.md`, or with the engine:

```bash
lfe approve G2 --exception "click-through not tested|agent|G5"
```

Each exception names its owner and the later gate it **blocks** (`mustResolveBefore`). The engine
keeps that gate blocked until a new decision resolves it. An exception never authorizes
production work before G3/G4, never authorizes cost, publication or deploy, and is never inferred:
only the person grants it.

## 5. Done means shown

Close a delegated step with something the person can look at in seconds: the prototype URL or
file, `lfe studio`, a screenshot taken now, or a test receipt. Not another report about a report.
