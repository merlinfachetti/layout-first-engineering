"""Append-only, hash-chained decision ledger `.lfe/decisions.jsonl` (RFC-0001, 8.2, D-01)."""
from __future__ import annotations

from pathlib import Path

from . import contracts
from .workspace import LEDGER_FILE, LfeError

GENESIS = "sha256:" + "0" * 64


def entry_hash(entry) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return contracts.sha256_of(contracts.canonical_json(body))


def read(root: Path):
    """Read and fully verify the ledger. Any edit, removal or reordering raises LEDGER_TAMPERED."""
    path = root / LEDGER_FILE
    if not path.exists():
        raise LfeError("NOT_INITIALIZED", f"{path} not found; run `lfe init` first")
    entries, prev = [], GENESIS
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise LfeError("LEDGER_TAMPERED", f"line {number} is empty", 5)
        doc, issues = contracts.parse(line)
        if not issues:
            issues = contracts.validate(doc, expected="decision")
        if issues:
            raise LfeError("LEDGER_TAMPERED", f"line {number}: {issues[0]}", 5)
        if doc["seq"] != number:
            raise LfeError("LEDGER_TAMPERED", f"line {number} has seq {doc['seq']}", 5)
        if doc["prevHash"] != prev:
            raise LfeError("LEDGER_TAMPERED", f"line {number} does not chain to line {number - 1}", 5)
        if entry_hash(doc) != doc["hash"]:
            raise LfeError("LEDGER_TAMPERED", f"line {number} was modified after it was written", 5)
        entries.append(doc)
        prev = doc["hash"]
    return entries


def next_id(entries, kind):
    prefix = "PROP-" if kind == "proposal" else "DEC-"
    taken = [int(e["id"][len(prefix):]) for e in entries if e["id"].startswith(prefix)]
    return f"{prefix}{(max(taken) + 1 if taken else 1):03d}"


def append(root: Path, entry):
    """Chain, validate and append one entry. Returns the stored entry."""
    entries = read(root)
    entry = dict(entry)
    entry["schemaVersion"] = "lfe.decision/0.1"
    entry["seq"] = len(entries) + 1
    entry["prevHash"] = entries[-1]["hash"] if entries else GENESIS
    entry["hash"] = GENESIS  # placeholder so the schema check sees every required field
    entry["hash"] = entry_hash(entry)
    issues = contracts.validate(entry, expected="decision")
    if issues:
        raise LfeError(issues[0].code, "; ".join(map(str, issues)), 6)
    with (root / LEDGER_FILE).open("a", encoding="utf-8") as handle:
        handle.write(contracts.canonical_json(entry).decode("utf-8") + "\n")
    return entry
