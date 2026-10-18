"""Bridge between `.lfe/` and the Markdown templates (RFC-0001, section 10).

`render` writes the computed gates into PROJECT_STATE.md, touching only the block between
`<!-- lfe:begin gates -->` and `<!-- lfe:end gates -->` plus the `Current stage` line.
`import_md` reads a legacy PROJECT_STATE.md with the parser of `verify_project.py` and records
each `approved` row as an `imported-legacy` decision, which never unlocks S6 (N-4, I-08).
"""
from __future__ import annotations

import importlib.util
import re
from functools import lru_cache
from pathlib import Path

from . import gates, ledger, workspace
from .workspace import GATES, LfeError

SKILL_DIR = Path(__file__).resolve().parents[2] / "layout-first-engineering"
TEMPLATE = SKILL_DIR / "assets" / "PROJECT_STATE.md"
BEGIN, END = "<!-- lfe:begin gates -->", "<!-- lfe:end gates -->"
HEADER = ["| Gate | Description | Status | Decision ID | Approved on | Evidence |",
          "| --- | --- | --- | --- | --- | --- |"]
DESCRIPTIONS = {
    "G1": "Visual direction selected",
    "G2": "Prototype and visual baseline approved",
    "G3": "MVP and revised visual handoff approved",
    "G4": "Architecture, scope, cost envelope approved",
    "G5": "Verified release candidate accepted",
    "G6": "Specific production release authorized",
}
STAGE_RE = re.compile(r"(?im)^(- \*\*Current stage:\*\*[ \t]*)(S[0-9])[ \t]*$")
ROW_RE = re.compile(r"^\|\s*(G[1-6])\s*\|")
EMPTY = "—"
# Imported stages above this one need human gates; see import_md.
IMPORT_STAGE_CAP = "S5"


@lru_cache(maxsize=None)
def legacy_parser():
    """The parser of the legacy validator, so both readings of PROJECT_STATE.md agree."""
    spec = importlib.util.spec_from_file_location("lfe_verify_project", SKILL_DIR / "scripts" / "verify_project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cell(text):
    """Keep a value inside one table cell."""
    return " ".join(str(text).replace("|", "/").split()) or EMPTY


# --- render ----------------------------------------------------------------------------

def gate_rows(state, results, entries, descriptions=None):
    """Return the six table rows (as cell lists) for the computed gates."""
    by_id = {e["id"]: e for e in entries}
    proposals = {e["gate"]: e for e in entries if e["kind"] == "proposal"}
    rows = []
    for gate in GATES:
        r = results[gate]
        decision = by_id.get(r["decisionId"]) if r["decisionId"] else None
        status, approved_on, evidence = r["status"], EMPTY, EMPTY
        if status == "stale":
            status, evidence = "needs_revision", "stale: hash divergente"
        elif status in ("approved", "not_applicable"):
            approved_on = decision["at"][:10]
            scope = decision["scope"]["artifacts"]
            evidence = ", ".join(f"{a['id']} r{a['revision']}" for a in scope) or decision.get("rationale", "")
            evidence = f"{evidence} ({decision['channel']})" if evidence else decision["channel"]
        elif status == "proposed":
            prop = proposals[gate]
            evidence = f"{prop['id']}: " + ", ".join(f"{a['id']} r{a['revision']}" for a in prop["scope"]["artifacts"])
        elif decision is not None and decision["channel"] == "imported-legacy" and status == "needs_revision":
            evidence = "imported-legacy: reconfirmar com lfe approve"
        elif r["reasons"]:
            evidence = r["reasons"][0]
        description = (descriptions or {}).get(gate) or DESCRIPTIONS[gate]
        rows.append([gate, _cell(description), status, r["decisionId"] or EMPTY, approved_on, _cell(evidence)])
    return rows


def render_block(rows):
    lines = [BEGIN, *HEADER]
    lines += ["| " + " | ".join(cells) + " |" for cells in rows]
    lines.append(END)
    return lines


def _table_bounds(lines):
    """(start, end) of the Markdown table holding the gate rows, end exclusive; None if absent."""
    first = next((i for i, line in enumerate(lines) if ROW_RE.match(line)), None)
    if first is None:
        return None
    start = first
    while start > 0 and lines[start - 1].lstrip().startswith("|"):
        start -= 1
    end = first
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    return start, end


def _existing_descriptions(lines):
    found = {}
    for line in lines:
        if ROW_RE.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1] not in ("", EMPTY):
                found[cells[0]] = cells[1]
    return found


def render_text(text, state, results, entries):
    """Return the new PROJECT_STATE.md text. Everything outside the block is kept, except the
    stage value on the `Current stage` line, which comes from the state."""
    lines = text.split("\n")
    stripped = [line.strip() for line in lines]
    lead = trail = []
    if BEGIN in stripped and END in stripped and stripped.index(BEGIN) < stripped.index(END):
        start, end = stripped.index(BEGIN), stripped.index(END) + 1
    elif BEGIN in stripped or END in stripped:
        raise LfeError("BROKEN_MARKERS", f"PROJECT_STATE.md must contain {BEGIN} and then {END}", 6)
    elif _table_bounds(lines):
        start, end = _table_bounds(lines)
    else:
        # No gate table at all: add one under the gate heading, or at the end of the file.
        heading = next((i for i, line in enumerate(lines) if line.startswith("## ") and "gate" in line.lower()), None)
        start = end = heading + 1 if heading is not None else len(lines) - (lines[-1] == "")
        lead = [""] if start > 0 and lines[start - 1].strip() else []
        trail = [""] if start < len(lines) and lines[start].strip() else []
    block = render_block(gate_rows(state, results, entries, _existing_descriptions(lines[start:end])))
    lines[start:end] = lead + block + trail
    out = "\n".join(lines)
    if STAGE_RE.search(out):
        out = STAGE_RE.sub(lambda m: m.group(1) + state["stage"], out, count=1)
    else:
        begin = out.index(BEGIN)
        out = out[:begin] + f"- **Current stage:** {state['stage']}\n\n" + out[begin:]
    return out


def computed(root: Path):
    """State, ledger and computed gates, refusing a hand-edited cache (S-02)."""
    state = workspace.load_state(root)
    entries = ledger.read(root)
    mismatch = gates.cache_problems(state, entries)
    if mismatch:
        raise LfeError("STATE_CACHE_MISMATCH", "; ".join(mismatch), 5)
    return state, entries, gates.evaluate(root, state, entries)


def render(root: Path, target: Path):
    """Write the computed gates into `target`. Returns 'created', 'updated' or 'unchanged'."""
    state, entries, results = computed(root)
    if target.exists():
        before = target.read_text(encoding="utf-8")
        outcome = "updated"
    else:
        before = TEMPLATE.read_text(encoding="utf-8")
        outcome = "created"
    after = render_text(before, state, results, entries)
    if outcome == "updated" and after == before:
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(after, encoding="utf-8")
    return outcome


# --- import ----------------------------------------------------------------------------

def _field(text, label):
    match = re.search(rf"(?im)^- \*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", text)
    value = match.group(1) if match else ""
    return "" if value.upper().startswith("TBD") else value


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64].strip("-")


def import_md(root: Path, source: Path, project_id=None, name=None):
    """Import a legacy PROJECT_STATE.md. Returns a report dict.

    Rules (RFC-0001, section 10, N-4, I-08):
    - creates `.lfe/` when it is missing; otherwise adds to the existing ledger;
    - each `approved` row becomes a decision `channel: imported-legacy`, `authenticity: unverified`,
      with an empty scope (there is no registered artifact to bind) and the legacy cells as notes;
    - a gate that already has a decision in the ledger is skipped, so an import never replaces a
      human decision;
    - the stage is the imported one, lowered to the highest stage the computed gates allow. Imported
      gates are never valid, so anything from S6 up becomes S5 and the pending reconfirmation is
      written to `nextAction`.
    """
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise LfeError("MISSING_FILE", f"{source} does not exist", 2) from None
    stage_number, rows, errors = legacy_parser().parse(text)
    if errors:
        raise LfeError("INVALID_LEGACY_STATE", f"{source}: " + "; ".join(errors), 6)
    imported_stage = f"S{stage_number}"

    created = not (root / workspace.STATE_FILE).exists()
    if created:
        pid = project_id or _slug(_field(text, "Project ID")) or _slug(root.resolve().name) or "imported-project"
        locale = _field(text, "Language / locale")
        if not re.fullmatch(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*", locale):
            locale = "pt-BR"
        workspace.init(root, pid, name or _field(text, "Project name") or pid, locale=locale)
    state = workspace.load_state(root)
    entries = ledger.read(root)
    decided = {e["gate"] for e in entries if e["kind"] == "decision"}
    actor = _field(text, "Owner / approver") or "unknown (legacy PROJECT_STATE.md)"

    imported, skipped = [], []
    for gate in GATES:
        cells = rows[gate]
        if cells[2] != "approved":
            continue
        if gate in decided:
            skipped.append(gate)
            continue
        notes = f"imported from {source.name}: legacy decision {cells[3]}, approved on {cells[4]}, evidence {cells[5]}"
        stored = ledger.append(root, {
            "kind": "decision", "id": ledger.next_id(entries, "decision"), "gate": gate, "verdict": "approved",
            "scope": {"artifacts": [], "notes": notes}, "actorDeclared": actor,
            "channel": "imported-legacy", "authenticity": "unverified", "at": workspace.now(),
        })
        entries.append(stored)
        imported.append(gate)

    results = gates.evaluate(root, state, entries)
    stage = imported_stage
    while gates.stage_problems(results, stage):
        stage = f"S{int(stage[1]) - 1}"
    state["stage"] = stage
    gates.refresh_cache(state, results)
    reconfirm = [g for g in GATES if results[g]["status"] == "needs_revision" and g in imported]
    if stage != imported_stage:
        state["nextAction"] = (f"Imported at {imported_stage}, recorded at {stage}: reconfirm "
                               f"{', '.join(reconfirm) or 'G2, G3, G4'} with `lfe propose` + `lfe approve` (N-4)")
    elif reconfirm:
        state["nextAction"] = f"Reconfirm imported gates {', '.join(reconfirm)} with `lfe propose` + `lfe approve`"
    workspace.save_state(root, state)
    return {"created": created, "importedStage": imported_stage, "stage": stage,
            "imported": imported, "skipped": skipped, "reconfirm": reconfirm, "nextAction": state["nextAction"]}
