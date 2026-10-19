# Gate accepted with exceptions — {{PROJECT_NAME}} / {{GATE}}

> Use only when the person explicitly approves a gate while accepting open items. An exception is
> never inferred, never authorizes production before G3/G4, cost, publication or deploy.

- **Gate:** {{G1–G6}} · **Decision:** {{DEC-###}} · **Approved by:** {{person}} · **When:** {{ISO date}}
- **Bound to:** {{artifact id @ revision, e.g. DESIGN-001@r2}}
- **Person's words:** "{{verbatim approval, including the accepted exceptions}}"
- **Engine command (when installed):** `lfe approve {{GATE}} --exception "description|owner|G#"`

| ID | Open item accepted | Owner | Blocks gate | How it will be resolved | Evidence when resolved |
| --- | --- | --- | --- | --- | --- |
| EXC-001 | {{e.g. click-through not tested}} | {{agent/person}} | {{G5}} | {{test, review…}} | {{receipt or link}} |

**Effect:** the gate counts as approved for moving forward; each exception keeps its "blocks gate"
closed until a new decision records it as resolved. List open exceptions in every status report.
