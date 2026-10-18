# LFE contracts v0.1

Language-neutral data contracts defined in [RFC-0001](../docs/rfcs/0001-core-contracts.md).
Any implementation, in any language, is conformant only if it accepts every file in
`fixtures/<contract>/valid/` and rejects every file in `fixtures/<contract>/invalid/` with the
error code written before `__` in the file name.

| Contract | Schema | `schemaVersion` |
|---|---|---|
| ProjectState | [state.schema.json](state.schema.json) | `lfe.state/0.1` |
| GateDecision | [decision.schema.json](decision.schema.json) | `lfe.decision/0.1` |
| ExperienceBaseline | [baseline.schema.json](baseline.schema.json) | `lfe.baseline/0.1` |
| RequirementSet | [requirements.schema.json](requirements.schema.json) | `lfe.requirements/0.1` |
| ActionRequest | [action.schema.json](action.schema.json) | `lfe.action/0.1` |
| PolicyDecision | [policy-decision.schema.json](policy-decision.schema.json) | `lfe.policy-decision/0.1` |
| EvidenceReceipt | [evidence.schema.json](evidence.schema.json) | `lfe.evidence/0.1` |

The `AgentHandoff` schema arrives with the handoff command, because that document is generated.

Validate a file with the reference implementation (Python 3.10+, standard library only):

```bash
PYTHONPATH=engine python3 -m lfe validate path/to/document.json
```

Exit codes: `0` valid, `4` incompatible `schemaVersion`, `6` contract violation.

Schemas use a small subset of JSON Schema 2020-12. Rules that cross fields (for example
"a chat quote can only record G1" or "`pass` needs at least one executed test") live in
`engine/lfe/contracts.py` and are covered by the same fixtures. The fixtures contain only
invented demo data and placeholder hashes; never put real credentials or private project data in them.
