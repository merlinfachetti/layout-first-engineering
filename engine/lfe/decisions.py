"""Proposals and human decisions (RFC-0001, 8.2 and 9). The only code that writes to the ledger."""
from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path

from . import gates, ledger, workspace
from .workspace import LfeError


def _declared_actor():
    try:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        name = ""
    return name or getpass.getuser()


def _current_scope(state, artifact_ids):
    scope = []
    for art_id in artifact_ids:
        current = state["artifacts"].get(art_id)
        if current is None:
            raise LfeError("UNKNOWN_REFERENCE", f"{art_id} is not registered; run `lfe artifact` first", 6)
        scope.append({"id": art_id, "revision": current["revision"], "sha256": current["sha256"]})
    return scope


def _latest_proposal(entries, gate):
    proposals = [e for e in entries if e["kind"] == "proposal" and e["gate"] == gate]
    return proposals[-1] if proposals else None


def _commit(root, state, entry):
    stored = ledger.append(root, entry)
    gates.refresh_cache(state, gates.evaluate(root, state, ledger.read(root)))
    workspace.save_state(root, state)
    return stored


def propose(root: Path, gate, artifact_ids):
    """Agent-side: bind a gate to the exact current content of the required artifacts."""
    state = workspace.load_state(root)
    entries = ledger.read(root)
    kinds = {state["artifacts"][a]["kind"] for a in artifact_ids if a in state["artifacts"]}
    missing = [k for k in gates.REQUIRED_KINDS[gate] if k not in kinds]
    scope = _current_scope(state, artifact_ids)
    if missing:
        raise LfeError("MISSING_ARTIFACT_KIND", f"{gate} must bind: {', '.join(missing)}", 6)
    for item in scope:
        _, problems = workspace.artifact_digest(root, state["artifacts"][item["id"]]["path"])
        if problems:
            raise LfeError("STALE_ARTIFACT", f"{item['id']}: {'; '.join(problems)}; re-register it first", 6)
    return _commit(root, state, {
        "kind": "proposal", "id": ledger.next_id(entries, "proposal"), "gate": gate,
        "scope": {"artifacts": scope}, "channel": "agent", "authenticity": "host-asserted",
        "at": workspace.now(),
    })


def summary(root, gate, verdict, scope, exceptions):
    lines = [f"You are about to record: {gate} = {verdict}", f"  meaning: {gates.MEANING[gate]}"]
    for item in scope:
        lines.append(f"  binds {item['id']} r{item['revision']} {item['sha256'][:19]}…")
    for exc in exceptions:
        lines.append(f"  open exception {exc['id']}: {exc['description']} (blocks {exc['mustResolveBefore']})")
    if verdict == "approved":
        if gate in ("G2", "G3", "G4"):
            lines.append("  production code is unlocked only when G2, G3 and G4 are all valid")
        lines.append("  this does NOT approve any later gate, any cost, publication or deployment")
    return "\n".join(lines)


def decide(root: Path, gate, verdict, *, option=None, rationale=None, exceptions=(), actor=None,
           interactive=None, ask=input, out=print):
    """Human-side decision through an interactive terminal (channel `human-cli`).

    There is deliberately no flag to skip the terminal check: an agent running commands
    without a terminal cannot record a human decision (first barrier against self-approval).
    """
    interactive = sys.stdin.isatty() if interactive is None else interactive
    if not interactive:
        raise LfeError("CHANNEL_NOT_INTERACTIVE",
                       f"`lfe {verdict_command(verdict)}` must be typed by a person in an interactive terminal", 2)
    state = workspace.load_state(root)
    entries = ledger.read(root)
    scope = []
    if verdict in ("approved", "rejected"):
        proposal = _latest_proposal(entries, gate)
        if proposal is None:
            raise LfeError("NO_PROPOSAL", f"nothing has been proposed for {gate} yet", 6)
        scope = proposal["scope"]["artifacts"]
        current = _current_scope(state, [s["id"] for s in scope])
        if current != scope:
            raise LfeError("STALE_PROPOSAL", f"the content proposed for {gate} changed; propose again", 6)
    exc_list = [{"id": f"EXC-{i:03d}", "description": d, "owner": o, "mustResolveBefore": g}
                for i, (d, o, g) in enumerate(exceptions, start=1)]
    out(summary(root, gate, verdict, scope, exc_list))
    if ask(f"Type {gate} to confirm: ").strip() != gate:
        raise LfeError("ABORTED", "confirmation did not match; nothing was recorded", 2)
    entry = {
        "kind": "decision", "id": ledger.next_id(entries, "decision"), "gate": gate, "verdict": verdict,
        "scope": {"artifacts": scope}, "actorDeclared": actor or _declared_actor(),
        "channel": "human-cli", "authenticity": "host-asserted", "at": workspace.now(),
    }
    if option:
        entry["option"] = option
    if rationale:
        entry["rationale"] = rationale
    if exc_list:
        entry["exceptions"] = exc_list
    return _commit(root, state, entry)


def verdict_command(verdict):
    return {"approved": "approve", "rejected": "reject", "revoked": "revoke",
            "not_applicable": "approve --not-applicable"}[verdict]


def record_chat_approval(root: Path, gate, quote, *, option=None, composition=None, actor=None):
    """Agent records the user's verbatim chat approval. Valid for G1 only (DEC-RFC-002)."""
    if gate != "G1":
        raise LfeError("CHANNEL_NOT_ALLOWED", "a chat quote can only record G1; G2–G6 need `lfe approve`", 6)
    state = workspace.load_state(root)
    entries = ledger.read(root)
    proposal = _latest_proposal(entries, gate)
    if proposal is None:
        raise LfeError("NO_PROPOSAL", "propose G1 with the direction set first", 6)
    entry = {
        "kind": "decision", "id": ledger.next_id(entries, "decision"), "gate": gate, "verdict": "approved",
        "scope": proposal["scope"], "actorDeclared": actor or _declared_actor(), "channel": "chat-quote",
        "evidence": {"quote": quote, "quotedAt": workspace.now()}, "authenticity": "unverified",
        "at": workspace.now(),
    }
    if option:
        entry["option"] = option
    if composition:
        entry["composition"] = composition
    return _commit(root, state, entry)


def set_stage(root: Path, stage):
    state = workspace.load_state(root)
    results = gates.evaluate(root, state, ledger.read(root))
    problems = gates.stage_problems(results, stage)
    if problems:
        raise LfeError("STAGE_GATE_VIOLATION", "; ".join(problems), 3)
    state["stage"] = stage
    gates.refresh_cache(state, results)
    workspace.save_state(root, state)
    return state
