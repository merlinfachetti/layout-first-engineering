---
name: studio
description: "Generate the LFE Studio, a read-only visual page with gates, design previews, traceability and test receipts."
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/layout-first-engineering/scripts/lfe.py" studio`

Tell the person where the page was written and how to open it (macOS: `open .lfe/studio.html`). Briefly explain the colours: blue is agent work, yellow is their decision, green valid, red blocked or stale.
