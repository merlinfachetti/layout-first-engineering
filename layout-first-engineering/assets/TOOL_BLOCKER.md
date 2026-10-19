# Tool blocker — {{PROJECT_NAME}} / {{TOOL}}

> Fill when a tool failure affects a deliverable. Never mark blocked work as done.

- **Tool and capability:** {{e.g. design tool write access}}
- **Status:** `limited | unavailable` since {{ISO_TIME}}
- **Observed evidence:** {{exact error message, quota notice or permission response}}
- **Deliverable affected:** {{artifact id and stage, e.g. DESIGN-001 r3, S2}}
- **What was NOT done because of it:** {{list; nothing here may be reported as done}}

## Recovery chosen

| Option | Authorized? | Artifact it produces | Chosen |
| --- | --- | --- | --- |
| Other authorized tool | {{yes/no}} | {{type}} | {{ }} |
| Coded throw-away prototype (`prototype/`, no production code) | {{yes/no}} | interactive local preview | {{ }} |
| Written specification only | yes | spec, marked as such | {{ }} |

- **Front advanced meanwhile:** {{requirements, risks, accessibility, test plan…}}
- **Person's involvement needed:** {{none | the single step only they can do, and why}}

## Reconciliation when the tool returns

- [ ] Changes ported back and compared with the fallback artifact
- [ ] New baseline revision registered (`lfe artifact … --refresh-files`)
- [ ] Affected gates re-proposed (approvals on the old revision are now `stale`)
- [ ] Capability status updated to `available` with the time it was verified
