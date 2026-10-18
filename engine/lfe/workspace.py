"""Project workspace: the `.lfe/` directory, project state and artifact registration (RFC-0001, 6 and 8.1)."""
from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path

from . import contracts

STATE_FILE = Path(".lfe") / "state.json"
LEDGER_FILE = Path(".lfe") / "decisions.jsonl"
GATES = [f"G{i}" for i in range(1, 7)]
STAGES = [f"S{i}" for i in range(10)]

# Artifact kinds that have a contract schema; others are hashed but not schema-checked in v0.1.
KIND_CONTRACT = {"experience-baseline": "baseline", "requirements-set": "requirements"}


class LfeError(Exception):
    """An expected, user-facing failure with a stable code and a CLI exit code."""

    def __init__(self, code, message, exit_code=2):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code

    def __str__(self):
        return f"{self.code}: {self.args[0]}"


def now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json_atomic(path: Path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_contract(path: Path, expected):
    """Read a strict JSON contract document; raise LfeError on any problem."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LfeError("NOT_INITIALIZED", f"{path} not found; run `lfe init` first") from None
    doc, issues = contracts.parse(text)
    if not issues:
        issues = contracts.validate(doc, expected=expected)
    if issues:
        exit_code = 4 if all(i.code == "INCOMPATIBLE_SCHEMA" for i in issues) else 6
        raise LfeError(issues[0].code, f"{path}: " + "; ".join(map(str, issues)), exit_code)
    return doc


def resolve(root: Path, rel: str) -> Path:
    """Resolve a contract path inside the project, refusing escapes (S-01)."""
    if contracts.unsafe_path(rel):
        raise LfeError("UNSAFE_PATH", f"{rel!r} must be relative and stay inside the project", 6)
    target = (root / rel).resolve()
    if not target.is_relative_to(root.resolve()):
        raise LfeError("UNSAFE_PATH", f"{rel!r} resolves outside the project", 6)
    return target


def file_digest(path: Path) -> str:
    return contracts.sha256_of(path.read_bytes())


def artifact_digest(root: Path, rel: str):
    """Return (digest, problems) for an artifact file.

    JSON artifacts are hashed in canonical form, so formatting changes do not matter, and every
    file listed in their `files[]` must still match its recorded hash. Other files are hashed
    byte for byte.
    """
    path = resolve(root, rel)
    if not path.is_file():
        return None, [f"{rel} is missing"]
    raw = path.read_bytes()
    doc, issues = contracts.parse(raw.decode("utf-8", errors="replace"))
    if issues:
        return contracts.sha256_of(raw), []
    problems = []
    for entry in doc.get("files", []) if isinstance(doc, dict) else []:
        try:
            listed = resolve(root, entry["path"])
        except LfeError as exc:
            problems.append(str(exc))
            continue
        if not listed.is_file():
            problems.append(f"{entry['path']} is missing")
        elif file_digest(listed) != entry.get("sha256"):
            problems.append(f"{entry['path']} changed after it was hashed")
    return contracts.sha256_of(contracts.canonical_json(doc)), problems


def init(root: Path, project_id: str, name: str, locale="pt-BR", mode="project"):
    state_path = root / STATE_FILE
    if state_path.exists():
        raise LfeError("ALREADY_INITIALIZED", f"{state_path} already exists")
    state = {
        "schemaVersion": "lfe.state/0.1",
        "projectId": project_id,
        "name": name,
        "locale": locale,
        "mode": mode,
        "stage": "S0",
        "artifacts": {},
        "gatesCache": {g: {"status": "not_started", "decisionId": None} for g in GATES},
        "nextAction": "Ask for the product intent and audience",
        "updatedAt": now(),
    }
    issues = contracts.validate(state, expected="state")
    if issues:
        raise LfeError(issues[0].code, "; ".join(map(str, issues)), 6)
    write_json_atomic(state_path, state)
    (root / LEDGER_FILE).write_text("", encoding="utf-8")
    return state


def load_state(root: Path):
    return read_contract(root / STATE_FILE, "state")


def save_state(root: Path, state):
    state["updatedAt"] = now()
    issues = contracts.validate(state, expected="state")
    if issues:
        raise LfeError(issues[0].code, "; ".join(map(str, issues)), 6)
    write_json_atomic(root / STATE_FILE, state)


def refresh_files(root: Path, rel: str):
    """Rewrite the sha256 of every entry in an artifact's `files[]` to match the disk."""
    path = resolve(root, rel)
    doc = read_contract_free(path)
    for entry in doc.get("files", []):
        listed = resolve(root, entry["path"])
        if not listed.is_file():
            raise LfeError("MISSING_FILE", f"{entry['path']} listed in {rel} does not exist", 6)
        entry["sha256"] = file_digest(listed)
    write_json_atomic(path, doc)


def read_contract_free(path: Path):
    doc, issues = contracts.parse(path.read_text(encoding="utf-8"))
    if issues:
        raise LfeError(issues[0].code, f"{path}: {issues[0]}", 6)
    return doc


def register_artifact(root: Path, state, art_id: str, kind: str, rel: str, refresh=False):
    """Record the current revision and hash of an artifact in the state.

    The revision increases only when the content hash changes. Registration is a proposal-side
    action: it never approves anything, it only makes the current content addressable.
    """
    prefix = contracts.ARTIFACT_PREFIX.get(kind)
    if prefix is None:
        raise LfeError("UNKNOWN_KIND", f"unknown artifact kind {kind!r}", 6)
    if not art_id.startswith(prefix):
        raise LfeError("ARTIFACT_KIND_MISMATCH", f"kind {kind} requires id prefix {prefix}", 6)
    if refresh:
        refresh_files(root, rel)
    path = resolve(root, rel)
    if not path.is_file():
        raise LfeError("MISSING_FILE", f"{rel} does not exist", 6)
    if kind in KIND_CONTRACT:
        read_contract(path, KIND_CONTRACT[kind])
    digest, problems = artifact_digest(root, rel)
    if problems:
        raise LfeError("UNHASHED_FILE", "; ".join(problems) + " (use --refresh-files)", 6)
    current = state["artifacts"].get(art_id)
    if current and current["kind"] != kind:
        raise LfeError("ARTIFACT_KIND_MISMATCH", f"{art_id} is registered as {current['kind']}", 6)
    if current and current["sha256"] == digest and current["path"] == rel:
        return current, False
    revision = current["revision"] + 1 if current else 1
    state["artifacts"][art_id] = {"kind": kind, "revision": revision, "path": rel, "sha256": digest}
    return state["artifacts"][art_id], True
