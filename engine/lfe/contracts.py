"""Load and validate LFE contract documents (RFC-0001, section 8).

Validation runs in four layers, in order, and stops at the first layer that fails:
1. parsing: strict JSON (no duplicate keys, no floats, no NaN/Infinity);
2. version: `schemaVersion` names a known contract and a compatible version;
3. schema: structural rules from `contracts/<name>.schema.json`;
4. semantics: cross-field invariants that a schema cannot express clearly.

Each problem is an Issue with a stable `code`; fixtures and tests rely on these codes.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath

from . import schema_lite

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

# contract name -> highest minor version understood, per major version
KNOWN = {
    "state": {0: 1},
    "decision": {0: 1},
    "baseline": {0: 1},
    "requirements": {0: 1},
    "action": {0: 1},
    "policy-decision": {0: 1},
    "evidence": {0: 1},
}
VERSION_RE = re.compile(r"^lfe\.([a-z-]+)/(\d+)\.(\d+)$")
ARTIFACT_PREFIX = {
    "direction-set": "DIR-",
    "experience-baseline": "DESIGN-",
    "requirements-set": "SCOPE-",
    "architecture-decision": "ADR-",
    "release-candidate": "RC-",
    "deployment-plan": "DEPLOY-",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd)=\S+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str

    def __str__(self):
        return f"{self.code} at {self.path}: {self.message}"


class _Reject(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise _Reject("DUPLICATE_KEY", f"key {key!r} appears more than once")
        obj[key] = value
    return obj


def _no_float(text):
    raise _Reject("FLOAT_NOT_ALLOWED", f"non-integer number {text}; contracts use integers only")


def _no_constant(text):
    raise _Reject("FLOAT_NOT_ALLOWED", f"{text} is not valid in a contract")


def parse(text):
    """Strict JSON parsing. Returns (document, issues)."""
    try:
        doc = json.loads(text, object_pairs_hook=_no_duplicates,
                         parse_float=_no_float, parse_constant=_no_constant)
    except _Reject as exc:
        return None, [Issue(exc.code, "$", str(exc))]
    except json.JSONDecodeError as exc:
        return None, [Issue("INVALID_JSON", "$", str(exc))]
    return doc, []


def canonical_json(doc):
    """Byte form used for hashing: sorted keys, no whitespace, UTF-8."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=None)
def load_schema(name):
    return json.loads((CONTRACTS_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def contract_of(doc):
    """Return (name, issues) from the document's schemaVersion."""
    if not isinstance(doc, dict) or not isinstance(doc.get("schemaVersion"), str):
        return None, [Issue("INCOMPATIBLE_SCHEMA", "$.schemaVersion", "missing or not a string")]
    match = VERSION_RE.match(doc["schemaVersion"])
    if not match:
        return None, [Issue("INCOMPATIBLE_SCHEMA", "$.schemaVersion", "expected lfe.<contract>/<major>.<minor>")]
    name, major, minor = match.group(1), int(match.group(2)), int(match.group(3))
    if name not in KNOWN:
        return None, [Issue("INCOMPATIBLE_SCHEMA", "$.schemaVersion", f"unknown contract {name!r}")]
    if major not in KNOWN[name] or minor > KNOWN[name][major]:
        return None, [Issue("INCOMPATIBLE_SCHEMA", "$.schemaVersion",
                            f"{doc['schemaVersion']} is newer than or incompatible with this reader")]
    return name, []


def validate(doc, expected=None):
    """Validate an already-parsed document. Returns a list of Issues (empty = valid)."""
    name, issues = contract_of(doc)
    if issues:
        return issues
    if expected and name != expected:
        return [Issue("INCOMPATIBLE_SCHEMA", "$.schemaVersion", f"expected a {expected} document, got {name}")]
    structural = [Issue("SCHEMA_VIOLATION", p, m) for p, m in schema_lite.validate(doc, load_schema(name))]
    if structural:
        return structural
    return SEMANTIC[name](doc)


def validate_text(text, expected=None):
    doc, issues = parse(text)
    return issues if issues else validate(doc, expected)


def validate_file(path, expected=None):
    return validate_text(Path(path).read_text(encoding="utf-8"), expected)


# --- semantic rules -----------------------------------------------------------------

def unsafe_path(value):
    """True when a contract path is absolute, escapes the project or is not POSIX style (S-01)."""
    if not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return True
    return ".." in PurePosixPath(value).parts


def _check_paths(pairs):
    return [Issue("UNSAFE_PATH", where, f"{value!r} must be relative and stay inside the project")
            for where, value in pairs if unsafe_path(value)]


def _gate_number(gate):
    return int(gate[1])


def _state(doc):
    issues = []
    for art_id, art in doc["artifacts"].items():
        prefix = ARTIFACT_PREFIX[art["kind"]]
        if not art_id.startswith(prefix):
            issues.append(Issue("ARTIFACT_KIND_MISMATCH", f"$.artifacts.{art_id}",
                                f"kind {art['kind']} requires id prefix {prefix}"))
    issues += _check_paths((f"$.artifacts.{k}.path", v["path"]) for k, v in doc["artifacts"].items())
    stage = int(doc["stage"][1])
    cache = doc["gatesCache"]
    required = []
    if stage >= 6:
        required += ["G2", "G3", "G4"]
    if stage >= 8:
        required += ["G5"]
    # A stored state may stay in a stage after an approved gate turned `stale` (content changed);
    # entering the stage requires valid gates, which `lfe stage` checks on computed status.
    for gate in required:
        if cache[gate]["status"] not in ("approved", "stale"):
            issues.append(Issue("STAGE_GATE_VIOLATION", f"$.gatesCache.{gate}",
                                f"stage {doc['stage']} requires {gate} approved"))
    if stage == 9 and cache["G6"]["status"] not in ("approved", "not_applicable", "stale"):
        issues.append(Issue("STAGE_GATE_VIOLATION", "$.gatesCache.G6", "S9 requires G6 approved or not_applicable"))
    for gate, entry in cache.items():
        if entry["status"] in ("approved", "not_applicable") and not entry["decisionId"]:
            issues.append(Issue("MISSING_DECISION_ID", f"$.gatesCache.{gate}", "approved gate without decision id"))
    return issues


# Which authenticity label each channel must carry (RFC-0001, D-03 and N-6).
CHANNEL_AUTHENTICITY = {
    "agent": "host-asserted",
    "human-cli": "host-asserted",
    "studio-export": "host-asserted",
    "chat-quote": "unverified",
    "imported-legacy": "unverified",
    "simulated-human": "simulated",
}


def _decision(doc):
    issues = []
    kind, gate, channel = doc["kind"], doc["gate"], doc["channel"]
    verdict = doc.get("verdict")
    expected_prefix = "PROP-" if kind == "proposal" else "DEC-"
    if not doc["id"].startswith(expected_prefix):
        issues.append(Issue("ID_KIND_MISMATCH", "$.id", f"a {kind} id must start with {expected_prefix}"))
    if doc["authenticity"] != CHANNEL_AUTHENTICITY[channel]:
        issues.append(Issue("AUTHENTICITY_MISMATCH", "$.authenticity",
                            f"channel {channel} must be labelled {CHANNEL_AUTHENTICITY[channel]}"))
    if kind == "proposal":
        if channel != "agent":
            issues.append(Issue("CHANNEL_NOT_ALLOWED", "$.channel", "proposals come from the agent channel"))
        for field in ("verdict", "exceptions", "actorDeclared"):
            if field in doc:
                issues.append(Issue("PROPOSAL_HAS_DECISION_FIELD", f"$.{field}", "only decisions carry this field"))
        if not doc["scope"]["artifacts"]:
            issues.append(Issue("EMPTY_SCOPE", "$.scope.artifacts", "a proposal must name what is proposed"))
        return issues

    if verdict is None:
        issues.append(Issue("MISSING_VERDICT", "$.verdict", "a decision needs a verdict"))
    if not doc.get("actorDeclared"):
        issues.append(Issue("MISSING_ACTOR", "$.actorDeclared", "a decision needs the declared human actor"))
    if channel == "agent":
        issues.append(Issue("CHANNEL_NOT_ALLOWED", "$.channel", "the agent channel can only propose (I-03)"))
    if channel == "chat-quote":
        if gate != "G1":
            issues.append(Issue("CHANNEL_NOT_ALLOWED", "$.channel",
                                "a chat quote can only record G1 (DEC-RFC-002, I-02)"))
        if not doc.get("evidence", {}).get("quote", "").strip():
            issues.append(Issue("MISSING_EVIDENCE", "$.evidence.quote", "chat-quote needs the verbatim user message"))
    # A legacy import has no registered artifact to bind; it never counts anyway (N-4, I-08).
    if verdict == "approved" and not doc["scope"]["artifacts"] and channel != "imported-legacy":
        issues.append(Issue("EMPTY_SCOPE", "$.scope.artifacts", "an approval must be bound to artifact hashes (D-05)"))
    if verdict == "not_applicable" and gate not in ("G1", "G6"):
        issues.append(Issue("NOT_APPLICABLE_FORBIDDEN", "$.verdict", "only G1 and G6 may be not_applicable in v0.1"))
    if verdict in ("not_applicable", "revoked") and not doc.get("rationale", "").strip():
        issues.append(Issue("MISSING_RATIONALE", "$.rationale", f"{verdict} requires a rationale"))
    if "exceptions" in doc:
        if verdict != "approved":
            issues.append(Issue("INVALID_EXCEPTION", "$.exceptions", "exceptions only accompany an approval"))
        for i, exc in enumerate(doc["exceptions"]):
            if _gate_number(exc["mustResolveBefore"]) <= _gate_number(gate):
                issues.append(Issue("INVALID_EXCEPTION", f"$.exceptions[{i}].mustResolveBefore",
                                    "must name a gate after the one being approved (D-09)"))
    if "composition" in doc and gate != "G1":
        issues.append(Issue("COMPOSITION_OUTSIDE_G1", "$.composition", "a visual composition belongs to G1"))
    return issues


def _baseline(doc):
    issues = []
    if doc["medium"] == "local-html" and not doc.get("mediumDecisionId"):
        issues.append(Issue("MISSING_MEDIUM_DECISION", "$.mediumDecisionId",
                            "a coded prototype needs the decision that chose it (SKILL.md:55)"))
    ids = [s["screenId"] for s in doc["screens"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        issues.append(Issue("DUPLICATE_ID", "$.screens", f"{dup} appears more than once"))
    pairs = [(f"$.files[{i}].path", f["path"]) for i, f in enumerate(doc["files"])]
    for i, screen in enumerate(doc["screens"]):
        for key in ("prototype", "preview"):
            if key in screen:
                pairs.append((f"$.screens[{i}].{key}.path", screen[key]["path"]))
    if "tokens" in doc:
        pairs.append(("$.tokens.path", doc["tokens"]["path"]))
    issues += _check_paths(pairs)
    listed = {f["path"] for f in doc["files"]}
    for where, value in pairs:
        if not where.startswith("$.files") and value not in listed:
            issues.append(Issue("UNHASHED_FILE", where, f"{value} must also be listed in files[] with its hash"))
    if doc["fidelity"] == "interactive-prototype" and not doc.get("interactionEvidence"):
        issues.append(Issue("UNPROVEN_FIDELITY", "$.fidelity",
                            "interactive-prototype requires interactionEvidence (an editable frame is not interactive)"))
    return issues


def _requirements(doc):
    issues = []
    item_ids = [i["id"] for i in doc["items"]]
    test_ids = [t["id"] for t in doc["tests"]]
    for dup in sorted({x for x in item_ids + test_ids if (item_ids + test_ids).count(x) > 1}):
        issues.append(Issue("DUPLICATE_ID", "$", f"{dup} appears more than once"))
    for n, item in enumerate(doc["items"]):
        if item["status"] in ("implemented", "verified") and not item["testRefs"]:
            issues.append(Issue("IMPLEMENTED_WITHOUT_TEST", f"$.items[{n}].testRefs",
                                f"{item['id']} is {item['status']} but has no test (R-03)"))
        for ref in item["testRefs"]:
            if ref not in test_ids:
                issues.append(Issue("UNKNOWN_REFERENCE", f"$.items[{n}].testRefs", f"{ref} is not declared in tests[]"))
    for n, test in enumerate(doc["tests"]):
        for ref in test["covers"]:
            if ref not in item_ids:
                issues.append(Issue("UNKNOWN_REFERENCE", f"$.tests[{n}].covers", f"{ref} is not declared in items[]"))
    return issues


def _action(doc):
    issues = []
    if not doc["targets"] and not doc.get("command"):
        issues.append(Issue("MISSING_TARGET", "$", "an action needs targets or a command"))
    issues += _check_paths((f"$.targets[{i}]", t) for i, t in enumerate(doc["targets"]))
    return issues


def _policy_decision(doc):
    if not doc["allowed"] and not doc.get("reasonCode"):
        return [Issue("MISSING_REASON", "$.reasonCode", "a denial must say why")]
    return []


def _evidence(doc):
    issues = []
    if doc["status"] == "pass":
        if doc.get("exitCode") != 0 or doc["testsRun"] < 1 or doc["testsSkipped"] != 0:
            issues.append(Issue("PASS_WITHOUT_PROOF", "$.status",
                                "pass needs exitCode 0, at least one test run and no skipped tests (E-01)"))
    elif not doc.get("reason", "").strip():
        issues.append(Issue("MISSING_REASON", "$.reason", f"status {doc['status']} must explain why (E-02)"))
    if doc["status"] == "not_executed" and doc.get("exitCode") is not None:
        issues.append(Issue("NOT_EXECUTED_WITH_EXIT", "$.exitCode", "nothing ran, so there is no exit code"))
    for i, arg in enumerate(doc["argv"]):
        if any(p.search(arg) for p in SECRET_PATTERNS):
            issues.append(Issue("SECRET_IN_ARGV", f"$.argv[{i}]", "argument looks like a credential (E-05)"))
    issues += _check_paths([("$.cwd", doc["cwd"])] if doc["cwd"] != "." else [])
    issues += _check_paths((f"$.artifacts[{i}].path", a["path"]) for i, a in enumerate(doc["artifacts"]))
    return issues


SEMANTIC = {
    "state": _state,
    "decision": _decision,
    "baseline": _baseline,
    "requirements": _requirements,
    "action": _action,
    "policy-decision": _policy_decision,
    "evidence": _evidence,
}
