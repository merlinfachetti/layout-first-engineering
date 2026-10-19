---
name: next
description: "Show only the next unresolved decision of the LFE project and what it unlocks."
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

Engine output for the current project:

!`python3 "${CLAUDE_PLUGIN_ROOT}/layout-first-engineering/scripts/lfe.py" status --json`

From this JSON only, state the single next decision the person must take (the first gate that is not valid, or the next action), what it would unlock and what it would NOT unlock. If it is G2–G6, tell the person to approve it themselves in their own terminal with `lfe approve <gate>` after reviewing the artifacts; never approve it for them.
