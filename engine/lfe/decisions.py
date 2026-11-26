"""Proposals and human decisions (RFC-0001, 8.2 and 9). The only code that writes to the ledger."""
from __future__ import annotations

import getpass
import re
import subprocess
import sys
from pathlib import Path

from . import evidence, gates, ledger, workspace
from .workspace import GATES, LfeError


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
    if gate == "G5" and verdict == "approved":
        evidence.require_complete(root)  # D-06
    exc_list = [{"id": f"EXC-{i:03d}", "description": d, "owner": o, "mustResolveBefore": g}
                for i, (d, o, g) in enumerate(exceptions, start=1)]
    out(summary(root, gate, verdict, scope, exc_list))
    if ask(f"Type {gate} to confirm: ").strip() != gate:
        raise LfeError("ABORTED", "confirmation did not match; nothing was recorded", 2)
    entry = {
        "kind": "decision", "id": ledger.next_id(entries, "decision", floor=_floor(state)), "gate": gate,
        "verdict": verdict,
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


def record_chat_approval(root: Path, gate, quote, *, option=None, composition=None, actor=None, message_ref=None):
    """Agent records the person's verbatim chat approval (channel `chat-quote`, unverified).

    G1 is always accepted. G2–G6 only when the project opted in (`lfe chat-approvals enable`), the
    quote contains the confirmation code of the latest proposal and a message reference is given.
    """
    state = workspace.load_state(root)
    allowed = gates.chat_gates(state)
    if gate not in allowed:
        raise LfeError("CHANNEL_NOT_ALLOWED",
                       f"a chat quote can only record {', '.join(sorted(allowed))} in this project; {gate} needs "
                       "`lfe approve` in a terminal, or the person enables chat approvals with "
                       "`lfe chat-approvals enable --gates ... --quote ... --message-ref ...`", 6)
    entries = ledger.read(root)
    proposal = _latest_proposal(entries, gate)
    if proposal is None:
        raise LfeError("NO_PROPOSAL", f"propose {gate} first (`lfe propose {gate} --artifact ...`)", 6)
    current = _current_scope(state, [s["id"] for s in proposal["scope"]["artifacts"]])
    if current != proposal["scope"]["artifacts"]:
        raise LfeError("STALE_PROPOSAL", f"the content proposed for {gate} changed; propose again", 6)
    code = gates.confirmation_code(proposal)
    evidence_doc = {"quote": quote, "quotedAt": workspace.now()}
    if gate != "G1":
        if code.lower() not in quote.lower():
            raise LfeError("CONFIRMATION_CODE_MISSING",
                           f"the quote must contain the code {code} of {proposal['id']}; ask the person to reply "
                           f"\"aprovo {code}\" (or \"approve {code}\")", 6)
        if not (message_ref or "").strip():
            raise LfeError("MISSING_EVIDENCE", "--message-ref is required for G2–G6 (chat message id or link)", 6)
        if gate == "G5":
            evidence.require_complete(root)  # D-06, same rule as the terminal
        evidence_doc.update(messageRef=message_ref, confirmationCode=code)
    elif message_ref:
        evidence_doc["messageRef"] = message_ref
    entry = {
        "kind": "decision", "id": ledger.next_id(entries, "decision", floor=_floor(state)), "gate": gate,
        "verdict": "approved", "scope": proposal["scope"], "actorDeclared": actor or _declared_actor(),
        "channel": "chat-quote", "evidence": evidence_doc, "authenticity": "unverified", "at": workspace.now(),
    }
    if option:
        entry["option"] = option
    if composition:
        entry["composition"] = normalize_composition(composition)
    return _commit(root, state, entry)


def normalize_composition(raw):
    """Accept the shapes people and agents actually write and return the contract shape.

    themeVariants: [{"theme","direction"}] or {"dark": "A"} or ["dark=A"]
    complementary: [{"direction","usage"}] or {"C": "usage"} or ["C=usage"] or ["C: usage"]
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("primary"), str) or not raw["primary"].strip():
        raise LfeError("BAD_COMPOSITION", 'composition needs "primary", e.g. {"primary": "A"}', 2)
    out = {"primary": raw["primary"].strip()}

    def pairs(value, left, right, field):
        if isinstance(value, dict):
            items = list(value.items())
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict):
                    items.append((item.get(left), item.get(right)))
                elif isinstance(item, str) and re.search(r"[=:]", item):
                    a, b = re.split(r"\s*[=:]\s*", item, maxsplit=1)
                    items.append((a, b))
                else:
                    raise LfeError("BAD_COMPOSITION", f"{field}: use {left}={right}, got {item!r}", 2)
        else:
            raise LfeError("BAD_COMPOSITION", f"{field} must be a list or an object", 2)
        result = []
        for a, b in items:
            if not (isinstance(a, str) and a.strip() and isinstance(b, str) and b.strip()):
                raise LfeError("BAD_COMPOSITION", f"{field}: every entry needs {left} and {right}", 2)
            result.append({left: a.strip(), right: b.strip()})
        return result

    if raw.get("themeVariants"):
        out["themeVariants"] = pairs(raw["themeVariants"], "theme", "direction", "themeVariants")
    if raw.get("complementary"):
        out["complementary"] = pairs(raw["complementary"], "direction", "usage", "complementary")
    if raw.get("nonNegotiables"):
        values = raw["nonNegotiables"]
        values = [values] if isinstance(values, str) else values
        if not all(isinstance(v, str) and v.strip() for v in values):
            raise LfeError("BAD_COMPOSITION", "nonNegotiables must be a list of texts", 2)
        out["nonNegotiables"] = [v.strip() for v in values]
    unknown = set(raw) - {"primary", "themeVariants", "complementary", "nonNegotiables"}
    if unknown:
        raise LfeError("BAD_COMPOSITION", f"unknown composition fields: {', '.join(sorted(unknown))}", 2)
    return out


def set_chat_approvals(root: Path, gate_list, quote, message_ref):
    """Opt the project in to chat approvals for the listed gates, with the person's own words (#27)."""
    gate_list = sorted(set(gate_list))
    bad = [g for g in gate_list if g not in GATES[1:]]
    if bad or not gate_list:
        raise LfeError("BAD_GATES", "list gates from G2 to G6, e.g. --gates G2,G3,G4", 2)
    if not quote.strip() or not message_ref.strip():
        raise LfeError("MISSING_EVIDENCE", "enabling chat approvals needs the person's quote and message reference", 2)
    state = workspace.load_state(root)
    state["chatApprovals"] = {"gates": gate_list, "enabledAt": workspace.now(), "quote": quote,
                              "messageRef": message_ref}
    gates.refresh_cache(state, gates.evaluate(root, state, ledger.read(root)))
    workspace.save_state(root, state)
    return state["chatApprovals"]


def disable_chat_approvals(root: Path):
    state = workspace.load_state(root)
    state.pop("chatApprovals", None)
    gates.refresh_cache(state, gates.evaluate(root, state, ledger.read(root)))
    workspace.save_state(root, state)


def _floor(state):
    return (state.get("numbering") or {}).get("decisionFloor", 0)


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
