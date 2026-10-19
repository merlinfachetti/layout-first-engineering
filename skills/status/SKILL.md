---
name: status
description: "Show the LFE project state: computed gates, production-code lock, reasons and next action."
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

Current LFE state, computed by the engine from `.lfe/` (not from memory):

!`python3 "${CLAUDE_PLUGIN_ROOT}/layout-first-engineering/scripts/lfe.py" status`

Summarize it for the person in their language in at most 6 lines: stage, which gates are valid, whether production code is locked, why anything is blocked or stale, and the next action. If the output says the project is not initialized, offer to start with `lfe init`. Never claim a gate is approved unless the output above says so.
