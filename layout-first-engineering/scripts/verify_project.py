#!/usr/bin/env python3
"""Lightweight LFE state gate sanity check. Standard library only; read-only.

Usage: python path/to/layout-first-engineering/scripts/verify_project.py /path/to/PROJECT_STATE.md
This checks declarations, not the truth of human approval or tool evidence.
"""
from pathlib import Path
import re
import sys

GATES = [f"G{i}" for i in range(1, 7)]
STATUSES = {"not_started", "exploring", "proposed", "approved", "needs_revision", "blocked"}


def validate(path: Path):
    errors, warnings = [], []
    if not path.is_file():
        return [f"Missing state file: {path}"], warnings
    content = path.read_text(encoding="utf-8")
    stage_match = re.search(r"(?im)^- \*\*Current stage:\*\*\s*(S[0-9])\s*$", content)
    stage = int(stage_match.group(1)[1]) if stage_match else None
    if stage is None:
        errors.append("Provide a current stage S0-S9 in PROJECT_STATE.md")
    gate_rows = {}
    for line in content.splitlines():
        match = re.match(r"^\|\s*(G[1-6])\s*\|(.+)$", line)
        if match:
            cells = [s.strip() for s in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                errors.append(f"{match.group(1)} row should have six columns")
            else:
                gate_rows[cells[0]] = cells
                if cells[2] not in STATUSES:
                    errors.append(f"{cells[0]}: invalid status {cells[2]!r}")
    for gate in GATES:
        if gate not in gate_rows:
            errors.append(f"Missing gate {gate}")
    if stage is not None and stage >= 6:
        for gate in ("G2", "G3", "G4"):
            if gate in gate_rows and gate_rows[gate][2] != "approved":
                errors.append(f"S{stage} requires {gate}=approved before production engineering")
    if stage is not None and stage >= 8:
        if gate_rows.get("G5", [None, None, None])[2] != "approved":
            errors.append("S8 requires G5=approved (verified release candidate)")
        if gate_rows.get("G6", [None, None, None])[2] != "approved":
            warnings.append("S8 is preparation only until G6 is approved; do NOT deploy")
    for gate, cells in gate_rows.items():
        if cells[2] == "approved" and cells[3] in {"—", "-", "TBD", ""}:
            warnings.append(f"{gate}: approved without a decision ID; verify human sign-off")
    return errors, warnings


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("PROJECT_STATE.md")
    errors, warnings = validate(path)
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"LFE state validation: {'FAIL' if errors else 'PASS'} ({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
