"""Gate validity, computed from the ledger and the current artifact hashes (RFC-0001, D-03 to D-09).

Nothing here trusts a stored status. Every call recomputes from first principles:
which decision is in effect, through which channel it entered, whether the previous gate is
valid, whether open exceptions block it and whether the approved content is still the same.
"""
from __future__ import annotations

from pathlib import Path

from .workspace import GATES, artifact_digest

# Artifact kinds every proposal for a gate must bind (RFC-0001, 8.1). This creates the cascade:
# a baseline change makes G2 and G3 stale; a scope change makes G3 and G4 stale.
REQUIRED_KINDS = {
    "G1": ["direction-set"],
    "G2": ["experience-baseline"],
    "G3": ["experience-baseline", "requirements-set"],
    "G4": ["requirements-set", "architecture-decision"],
    "G5": ["release-candidate"],
    "G6": ["release-candidate", "deployment-plan"],
}
MEANING = {
    "G1": "visual direction chosen",
    "G2": "prototype and visual baseline approved",
    "G3": "MVP scope and revised visual handoff approved",
    "G4": "architecture, scope and cost envelope approved",
    "G5": "verified release candidate accepted",
    "G6": "this specific production deploy authorized",
}
VALID = ("approved", "not_applicable")


def chat_gates(state):
    """Gates the project accepts from a chat quote: always G1, plus the opt-in list (#27)."""
    return {"G1", *((state.get("chatApprovals") or {}).get("gates") or [])}


def confirmation_code(proposal):
    """Short code bound to one proposal's hash. The person quotes it to approve by chat, which
    ties the approval to the exact content proposed: new content, new proposal, new code."""
    return f"{proposal['gate']}-{proposal['hash'][len('sha256:'):][:6]}"


def channel_allows(channel, gate, mode, chat=("G1",)):
    """D-03: which channels can make a decision count."""
    if channel in ("human-cli", "studio-export"):
        return True, None
    if channel == "chat-quote":
        return gate in chat, (f"a chat quote only counts for {', '.join(sorted(chat))}; enable chat approvals "
                              f"for {gate} with `lfe chat-approvals enable` or approve it with `lfe approve`")
    if channel == "simulated-human":
        return mode == "demo", "simulated decisions only count in a demo workspace"
    if channel == "imported-legacy":
        return False, "imported from Markdown; reconfirm with `lfe approve`"
    return False, "the agent channel can only propose"


def binding_problems(root: Path, state, decision):
    """D-05: the approved content must still be the registered, unchanged content."""
    problems = []
    for item in decision["scope"]["artifacts"]:
        current = state["artifacts"].get(item["id"])
        if current is None:
            problems.append(f"{item['id']} is no longer registered")
            continue
        if current["revision"] != item["revision"] or current["sha256"] != item["sha256"]:
            problems.append(f"{item['id']} changed: approved r{item['revision']}, now r{current['revision']}")
            continue
        digest, file_problems = artifact_digest(root, current["path"])
        if digest is None or digest != current["sha256"]:
            problems.append(f"{item['id']} file changed on disk since registration")
        problems += [f"{item['id']}: {p}" for p in file_problems]
    return problems


def evaluate(root: Path, state, entries):
    """Return {gate: {status, decisionId, reasons, exceptions}} for G1..G6."""
    effective, last_proposal = {}, {}
    for entry in entries:
        target = effective if entry["kind"] == "decision" else last_proposal
        target[entry["gate"]] = entry

    results = {}
    for index, gate in enumerate(GATES):
        decision = effective.get(gate)
        result = {"status": "not_started", "decisionId": None, "reasons": [], "exceptions": []}
        results[gate] = result
        proposal = last_proposal.get(gate)
        if decision is None:
            if proposal:
                result["status"] = "proposed"
            continue
        result["decisionId"] = decision["id"]
        verdict = decision["verdict"]
        if verdict == "rejected":
            result["status"] = "needs_revision"
            if proposal and proposal["seq"] > decision["seq"]:
                result["status"] = "proposed"
            continue
        if verdict == "revoked":
            result["status"] = "not_started"
            result["reasons"].append(f"revoked by {decision['id']}: {decision.get('rationale', '')}")
            continue

        allowed, why = channel_allows(decision["channel"], gate, state["mode"], chat_gates(state))
        if not allowed:
            result["status"] = "needs_revision"
            result["reasons"].append(why)
            continue
        if index > 0 and results[GATES[index - 1]]["status"] not in VALID:
            result["status"] = "blocked"
            result["reasons"].append(f"{GATES[index - 1]} is not valid (D-04)")
        for earlier in GATES[:index]:
            for exc in (effective.get(earlier) or {}).get("exceptions", []):
                if exc["mustResolveBefore"] == gate:
                    result["status"] = "blocked"
                    result["reasons"].append(f"open exception {exc['id']} from {earlier}: {exc['description']} (D-09)")
        if verdict == "approved":
            stale = binding_problems(root, state, decision)
            if stale:
                result["status"] = "stale"
                result["reasons"] += stale
        if result["status"] == "not_started":
            result["status"] = verdict
        result["exceptions"] = decision.get("exceptions", [])
    return results


def is_valid(results, gate):
    return results[gate]["status"] in VALID


# Entering a stage requires every gate that closes the stages before it (S-03, S-04). This is
# the SKILL.md table read as a rule: S2 needs G1, S3 needs G2, S4 needs G3, S5–S7 need G4,
# S8 needs G5 and S9 needs G6. Going back to an earlier stage is always allowed.
STAGE_REQUIRES = {
    "S0": [], "S1": [], "S2": ["G1"], "S3": ["G1", "G2"], "S4": ["G1", "G2", "G3"],
    "S5": ["G1", "G2", "G3", "G4"], "S6": ["G1", "G2", "G3", "G4"], "S7": ["G1", "G2", "G3", "G4"],
    "S8": ["G1", "G2", "G3", "G4", "G5"], "S9": GATES,
}


def stage_problems(results, stage, tolerate=()):
    """Gates that must be valid before `stage` can be entered, with their current status.

    `tolerate` lists gates accepted as pending reconfirmation (imported history, see mdbridge);
    it never applies from S6 up, where production code starts.
    """
    tolerated = set(tolerate) if int(stage[1]) < 6 else set()
    return [f"{stage} requires {g} valid (now {results[g]['status']})"
            for g in STAGE_REQUIRES[stage] if not is_valid(results, g) and g not in tolerated]


def cache_problems(state, entries):
    """S-02: the stored cache may lag behind file changes, but it must never claim a decision
    that the ledger does not contain. This catches hand-edited approvals (probes P1 and P2)."""
    effective = {}
    for entry in entries:
        if entry["kind"] == "decision":
            effective[entry["gate"]] = entry
    problems = []
    for gate in GATES:
        cached = state["gatesCache"][gate]
        decision = effective.get(gate)
        if cached["status"] in VALID:
            if decision is None or decision["id"] != cached["decisionId"] or decision["verdict"] != cached["status"]:
                problems.append(f"{gate} cache says {cached['status']} ({cached['decisionId']}) but the ledger disagrees")
    return problems


def refresh_cache(state, results):
    state["gatesCache"] = {g: {"status": r["status"], "decisionId": r["decisionId"]} for g, r in results.items()}
