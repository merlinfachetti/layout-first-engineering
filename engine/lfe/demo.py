"""Demo replay (RFC-0002 §8): copy an example project and approve its open proposals as *simulated*.

Safety by construction:
- it only ever works on a fresh copy, never in place, so a real project can't gain simulated approvals;
- the copy is switched to `mode: demo`, the only mode where `simulated-human` decisions count (D-03);
- every simulated decision carries `authenticity: simulated` and is labelled in status and handoff (D-08).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import decisions, gates, handoff, ledger, workspace
from .workspace import GATES, LfeError

DEMO_ACTOR = "demo replay (simulado)"


def replay(source: Path, workdir: Path, until="G4"):
    source, workdir = source.resolve(), workdir.resolve()
    if not (source / workspace.STATE_FILE).is_file():
        raise LfeError("NOT_INITIALIZED", f"{source} has no .lfe/state.json", 2)
    if workdir == source or source in workdir.parents:
        raise LfeError("DEMO_IN_PLACE", "the demo must run in a separate folder, never inside the source project", 2)
    if workdir.exists() and any(workdir.iterdir()):
        raise LfeError("WORKDIR_NOT_EMPTY", f"{workdir} must be empty or not exist", 2)
    ledger.read(source)  # refuse to replay a tampered example
    shutil.copytree(source, workdir, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "node_modules"))

    state = workspace.load_state(workdir)
    state["mode"] = "demo"
    workspace.save_state(workdir, state)

    approved = []
    for gate in GATES[: GATES.index(until) + 1]:
        entries = ledger.read(workdir)
        proposals = [e for e in entries if e["kind"] == "proposal" and e["gate"] == gate]
        if not proposals:
            break
        ledger.append(workdir, {
            "kind": "decision", "id": ledger.next_id(entries, "decision"), "gate": gate, "verdict": "approved",
            "scope": proposals[-1]["scope"], "actorDeclared": DEMO_ACTOR, "channel": "simulated-human",
            "authenticity": "simulated", "at": workspace.now(),
        })
        approved.append(gate)

    state = workspace.load_state(workdir)
    results = gates.evaluate(workdir, state, ledger.read(workdir))
    gates.refresh_cache(state, results)
    workspace.save_state(workdir, state)
    if not gates.stage_problems(results, "S6"):
        decisions.set_stage(workdir, "S6")
    return {"workdir": str(workdir), "approved": approved,
            "gates": {g: results[g]["status"] for g in GATES}, "handoff": handoff.write(workdir)}
