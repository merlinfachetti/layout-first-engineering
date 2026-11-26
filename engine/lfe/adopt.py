"""`lfe adopt`: bring a project that is already under way into the engine (issue #28).

`lfe init` starts at S0 and `lfe import-md` only reads the exact template. Real projects arrive
with their own PROJECT_STATE.md (extra columns, Portuguese statuses), a DECISIONS.md that already
uses DEC-001…, and the design and scope in Markdown and screenshots. Adoption:

1. reads PROJECT_STATE.md tolerantly (any `| G1 |` row, EN/PT statuses, several stage lines);
2. continues decision ids after the highest `DEC-###` the project's Markdown already uses;
3. generates *draft* typed artifacts under `.lfe/adopted/` from what exists (prototypes, evidence
   images, scope Markdown, ADRs, quality reports), registers them and proposes every gate the
   Markdown says was approved, so each one can be reconfirmed in one step;
4. records those past approvals as `imported-legacy` (never valid by themselves, N-4) and keeps
   the project's place up to S5 while they wait; production code stays locked until G2–G4 are
   reconfirmed through a counting channel.

Nothing is deleted or rewritten outside `.lfe/`. `dry_run=True` returns the plan without writing.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from . import contracts, decisions, gates, ledger, workspace
from .workspace import GATES, LfeError

ADOPTED_DIR = Path(".lfe") / "adopted"
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", ".lfe", ".venv", "venv", "__pycache__",
             ".vercel", "coverage", ".turbo", ".cache"}
MAX_FILES = 4000

STATUS_WORDS = [
    ("not_applicable", r"not[_ ]applicable|n/?a\b|não se aplica|nao se aplica"),
    ("needs_revision", r"needs[_ ]revision|revis(?:ar|ão)|rejeitad|rejected"),
    ("approved", r"approved|aprovad[oa]|✅|\bdone\b|conclu[ií]d[oa]|\bok\b"),
    ("proposed", r"proposed|propost[oa]|aguardando|waiting|pending|pendente"),
]
STAGE_PATTERNS = [
    r"(?im)^\s*-?\s*\*\*(?:current stage|etapa atual|estágio atual|stage)[^*]*:\*\*[^S\n]*\b(S[0-9])\b",
    r"(?im)^\s*-?\s*(?:current stage|etapa atual|estágio atual|stage|etapa)\s*:\s*\**\s*(S[0-9])\b",
    r"(?im)\b(?:current stage|etapa atual|estágio atual)\b[^\n]*?\b(S[0-9])\b",
]
REQ_LINE = re.compile(r"\b((?:FR|NFR|SEC|UX)-[0-9]{3,})\b[\s:|*—–-]*(.+)")
PRIORITY = {"must": "must", "should": "should", "could": "could", "won't": "wont", "wont": "wont",
            "won’t": "wont", "deve": "must", "deveria": "should", "poderia": "could", "não vai": "wont"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
VIEWPORT_HINT = {"mobile": (390, 844), "tablet": (820, 1180), "desktop": (1440, 900)}


# --- reading the project -----------------------------------------------------------------

def walk(root: Path):
    """Project files, skipping dependencies and build output; bounded so huge repos stay fast."""
    found = []
    stack = [root]
    while stack and len(found) < MAX_FILES:
        current = stack.pop()
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_symlink():
                continue
            if child.is_dir():
                if child.name not in SKIP_DIRS:
                    stack.append(child)
            elif child.is_file():
                found.append(child)
    return sorted(found)


def rel(root: Path, path: Path):
    return path.relative_to(root).as_posix()


def find_state_file(root: Path, files):
    named = [f for f in files if f.name.upper() == "PROJECT_STATE.MD"]
    named.sort(key=lambda f: (len(f.relative_to(root).parts), str(f)))
    return named[0] if named else None


def parse_status(cells):
    for cell in cells:
        low = cell.lower()
        for status, pattern in STATUS_WORDS:
            if re.search(pattern, low):
                return status
    return "not_started"


def parse_state_text(text):
    """Return {stage, gates: {G1: {status, decisionId, date, evidence}}, fields} from any PROJECT_STATE.md."""
    stage = None
    for pattern in STAGE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            stage = match.group(1)
            break
    rows = {}
    for line in text.splitlines():
        match = re.match(r"^\s*\|\s*\**(G[1-6])\**\s*\|(.*)\|\s*$", line)
        if not match or match.group(1) in rows:
            continue
        cells = [c.strip() for c in match.group(2).split("|")]
        status_cells = cells[1:] if len(cells) > 1 else cells  # skip the description column
        dec = re.search(r"\bDEC-[0-9]{3,}\b", match.group(2))
        date = re.search(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b", match.group(2))
        rows[match.group(1)] = {"status": parse_status(status_cells[:2]),
                                "decisionId": dec.group(0) if dec else None,
                                "date": date.group(0) if date else None,
                                "evidence": cells[-1] if cells else ""}
    fields = {}
    for label, keys in (("projectId", ("project id", "id do projeto")),
                        ("name", ("project name", "nome do projeto", "produto"))):
        for key in keys:
            match = re.search(rf"(?im)^\s*-?\s*\*\*{re.escape(key)}[^*]*:\*\*\s*(.+?)\s*$", text)
            if match and not match.group(1).upper().startswith("TBD"):
                fields[label] = match.group(1).strip("` ")
                break
    if "name" not in fields:
        heading = re.search(r"(?m)^#\s+.*?[—–-]\s*(.+?)\s*$", text)
        if heading:
            fields["name"] = heading.group(1).strip()
    return {"stage": stage, "gates": rows, "fields": fields}


def decision_floor(root: Path, files):
    """Highest DEC-### the project's own Markdown already uses."""
    highest = 0
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in re.finditer(r"\bDEC-([0-9]{3,})\b", text):
            highest = max(highest, int(match.group(1)))
    return highest


def png_size(path: Path):
    try:
        with path.open("rb") as handle:
            head = handle.read(24)
    except OSError:
        return None
    if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
        return struct.unpack(">II", head[16:24])
    return None


def viewport_for(path: Path):
    size = png_size(path)
    if size and all(size):
        width, height = size
        # Full-page screenshots are tall; keep a viewport-shaped height.
        return {"width": int(width), "height": int(min(height, max(width * 2.2, 800)))}
    name = path.stem.lower()
    for hint, (w, h) in VIEWPORT_HINT.items():
        if hint in name:
            return {"width": w, "height": h}
    return {"width": 1440, "height": 900}


def screen_key(path: Path):
    stem = re.sub(r"[-_](?:desktop|mobile|tablet|dark|light|pt|en|pt-br|en-us|\d+x\d+|@\dx)\b", "", path.stem.lower())
    return re.sub(r"[-_]+$", "", stem) or path.stem.lower()


def split_items(text):
    """Split a MoSCoW cell on commas and semicolons that are not inside parentheses."""
    items, depth, current = [], 0, []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char in ",;" and depth == 0:
            items.append("".join(current))
            current = []
        else:
            current.append(char)
    items.append("".join(current))
    cleaned = [re.sub(r"\*\*|__|`", "", item).strip(" .") for item in items]
    return [c for c in cleaned if len(c) > 1]


def requirement_candidates(text):
    """(id or None, title, priority) found in a scope document."""
    found, seen = [], set()
    for line in text.splitlines():
        match = REQ_LINE.search(line)
        if match and match.group(1) not in seen:
            seen.add(match.group(1))
            title = re.sub(r"\s*\|.*$", "", match.group(2)).strip(" *|")
            low = line.lower()
            priority = next((v for k, v in PRIORITY.items() if re.search(rf"\b{re.escape(k)}\b", low)), "must")
            found.append((match.group(1), title or match.group(1), priority))
    if found:
        return found
    for line in text.splitlines():
        row = re.match(r"^\s*\|\s*\**\s*(must|should|could|won['’]?t)\b[^|]*\|(.+)\|\s*$", line, re.IGNORECASE)
        if row:
            priority = PRIORITY.get(row.group(1).lower().replace("’", "'"), "must")
            found += [(None, item, priority) for item in split_items(row.group(2))]
    if found:
        return found
    heading_priority = None
    for line in text.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+)$", line)
        if heading:
            low = heading.group(1).lower()
            heading_priority = next((v for k, v in PRIORITY.items() if k in low), None)
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet and heading_priority:
            found.append((None, re.sub(r"\*\*|`", "", bullet.group(1)).strip(), heading_priority))
    return found


# --- planning ----------------------------------------------------------------------------

def _first(files, root, patterns):
    for pattern in patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        for path in files:
            if regex.search(rel(root, path)):
                return path
    return None


def plan(root: Path, state_file: Path | None = None):
    """Everything adoption would write, without writing it."""
    root = root.resolve()
    if (root / workspace.STATE_FILE).exists():
        raise LfeError("ALREADY_INITIALIZED", f"{root / workspace.STATE_FILE} exists; adoption is for projects "
                       "without .lfe/ (use `lfe status`)", 2)
    files = walk(root)
    source = state_file if state_file else find_state_file(root, files)
    if source is not None and not source.is_absolute():
        source = root / source
    parsed = parse_state_text(source.read_text(encoding="utf-8")) if source else {"stage": None, "gates": {}, "fields": {}}
    text = source.read_text(encoding="utf-8") if source else ""
    figma = re.search(r"https://(?:www\.)?figma\.com/(?:design|file|proto)/[A-Za-z0-9]+[^\s)|>]*", text)
    penpot = re.search(r"https://design\.penpot\.app/[^\s)|>]+", text)

    prototypes = [f for f in files if f.suffix.lower() == ".html"
                  and re.search(r"(?:^|/)(?:prototypes?|directions?|mockups?)/", rel(root, f), re.IGNORECASE)]
    direction_docs = [f for f in files if f.suffix.lower() == ".md"
                      and re.search(r"direc|direç|visual", f.name, re.IGNORECASE)]
    images = [f for f in files if f.suffix.lower() in IMAGE_EXT
              and re.search(r"(?:^|/)(?:evidence|evidências|evidencias|screens|screenshots|previews|figma-previews)/",
                            rel(root, f), re.IGNORECASE)
              and not re.search(r"brand|logo|icon", rel(root, f), re.IGNORECASE)]
    tokens = _first(files, root, [r"(?:^|/)tokens\.(?:json|css)$"])
    scope_doc = _first(files, root, [r"(?:^|/)PRODUCT_SCOPE\.md$", r"(?:^|/)SCOPE[^/]*\.md$",
                                     r"(?:^|/)MVP[^/]*\.md$", r"(?:^|/)PRODUCT_BRIEF\.md$", r"(?:^|/)BACKLOG\.md$"])
    adrs = [f for f in files if re.match(r"ADR-[0-9]{3,}", f.name, re.IGNORECASE) and f.suffix.lower() == ".md"]
    rc_doc = _first(files, root, [r"(?:^|/)G5[^/]*\.md$", r"(?:^|/)(?:VERIFICATION|TEST)_REPORT[^/]*\.md$",
                                  r"(?:^|/)quality/[^/]+\.md$"])
    deploy_doc = _first(files, root, [r"(?:^|/)DEPLOY[^/]*\.md$", r"(?:^|/)RELEASE_PLAN[^/]*\.md$"])

    artifacts, notes = [], []
    # G1: direction set (JSON that hashes the files it lists).
    dir_files = sorted({rel(root, f) for f in prototypes + direction_docs})
    if not dir_files and source:
        dir_files = [rel(root, source)]
        notes.append("no prototype or direction document found: DIR-001 points at PROJECT_STATE.md")
    if dir_files:
        artifacts.append({"id": "DIR-001", "kind": "direction-set", "path": f"{ADOPTED_DIR.as_posix()}/DIR-001.json",
                          "doc": {"id": "DIR-001", "revision": 1, "title": "Visual directions (adopted)",
                                  "adoptedFrom": dir_files, "files": [{"path": p, "sha256": ""} for p in dir_files]}})
    # G2: experience baseline (contract `lfe.baseline/0.1`).
    groups = {}
    for image in images:
        groups.setdefault(screen_key(image), []).append(image)
    screens, baseline_files = [], set()
    for n, (key, group) in enumerate(sorted(groups.items()), start=1):
        viewports, seen = [], set()
        for image in group:
            vp = viewport_for(image)
            if (vp["width"], vp["height"]) not in seen:
                seen.add((vp["width"], vp["height"]))
                viewports.append(vp)
        preview = rel(root, group[0])
        baseline_files.add(preview)
        baseline_files.update(rel(root, g) for g in group)
        screens.append({"screenId": f"UI-{n:03d}", "name": key.replace("-", " ").replace("_", " ").strip().title(),
                        "goal": f"Adopted from {preview}; confirm the screen goal", "states": ["default"],
                        "viewports": viewports, "preview": {"path": preview}})
    if not screens and prototypes:
        for n, proto in enumerate(prototypes, start=1):
            path = rel(root, proto)
            baseline_files.add(path)
            screens.append({"screenId": f"UI-{n:03d}", "name": proto.stem.replace("-", " ").title(),
                            "goal": f"Adopted from {path}; confirm the screen goal", "states": ["default"],
                            "viewports": [{"width": 390, "height": 844}, {"width": 1440, "height": 900}],
                            "prototype": {"path": path}})
    if screens:
        medium = "figma" if figma else ("penpot" if penpot else ("image" if images else "spec"))
        baseline = {"schemaVersion": "lfe.baseline/0.1", "id": "DESIGN-001", "revision": 1,
                    "title": "Experience baseline (adopted)", "medium": medium, "fidelity": "static-layout",
                    "screens": screens}
        if figma or penpot:
            baseline["sourceUrl"] = (figma or penpot).group(0).rstrip(".,;")
        if tokens:
            baseline["tokens"] = {"path": rel(root, tokens)}
            baseline_files.add(rel(root, tokens))
        baseline["files"] = [{"path": p, "sha256": ""} for p in sorted(baseline_files)]
        artifacts.append({"id": "DESIGN-001", "kind": "experience-baseline",
                          "path": f"{ADOPTED_DIR.as_posix()}/DESIGN-001.json", "doc": baseline})
    else:
        notes.append("no evidence images or prototypes found: create DESIGN-001 before proposing G2")
    # G3: requirement set (contract `lfe.requirements/0.1`).
    if scope_doc:
        candidates = requirement_candidates(scope_doc.read_text(encoding="utf-8", errors="replace"))
        if not candidates:
            candidates = [(None, f"Scope as written in {rel(root, scope_doc)}", "must")]
            notes.append(f"{rel(root, scope_doc)} has no FR-/NFR- ids or MoSCoW table: one placeholder requirement")
        items, used = [], set()
        prefix_count = {}
        for req_id, title, priority in candidates:
            if not req_id or req_id in used:
                prefix_count["FR"] = prefix_count.get("FR", 0) + 1
                req_id = f"FR-{prefix_count['FR'] + 900:03d}"  # 9xx: generated, never clashes with written ids
            used.add(req_id)
            items.append({"id": req_id, "title": title[:300],
                          "acceptance": [{"given": f"the scope in {rel(root, scope_doc)}",
                                          "when": "the person reviews this adopted requirement",
                                          "then": "its acceptance criteria are written before S6"}],
                          "priority": priority, "uiRefs": [], "testRefs": [], "status": "proposed"})
        artifacts.append({"id": "SCOPE-001", "kind": "requirements-set",
                          "path": f"{ADOPTED_DIR.as_posix()}/SCOPE-001.json",
                          "doc": {"schemaVersion": "lfe.requirements/0.1", "id": "SCOPE-001", "revision": 1,
                                  "items": items, "tests": []}})
    else:
        notes.append("no scope document found (PRODUCT_SCOPE.md, SCOPE*.md, MVP*.md): create SCOPE-001 before G3")
    # G4: architecture decisions, registered as they are (Markdown is hashed byte for byte).
    for adr in sorted(adrs, key=lambda f: f.name)[:9]:
        number = re.match(r"ADR-([0-9]{3,})", adr.name, re.IGNORECASE).group(1)
        artifacts.append({"id": f"ADR-{number}", "kind": "architecture-decision", "path": rel(root, adr)})
    if not adrs:
        notes.append("no ADR-*.md found: create ADR-001 before G4")
    if rc_doc:
        artifacts.append({"id": "RC-001", "kind": "release-candidate", "path": rel(root, rc_doc)})
    if deploy_doc:
        artifacts.append({"id": "DEPLOY-001", "kind": "deployment-plan", "path": rel(root, deploy_doc)})

    legacy_gates = [g for g in GATES if parsed["gates"].get(g, {}).get("status") in ("approved", "not_applicable")]
    kinds = {a["kind"]: [x["id"] for x in artifacts if x["kind"] == a["kind"]] for a in artifacts}
    proposals = {}
    for gate in legacy_gates:
        needed = gates.REQUIRED_KINDS[gate]
        if all(k in kinds for k in needed):
            proposals[gate] = [kinds[k][0] for k in needed]
        else:
            notes.append(f"{gate} was approved in Markdown but has no {', '.join(k for k in needed if k not in kinds)}; "
                         "it cannot be proposed yet")
    pid = parsed["fields"].get("projectId") or root.name
    pid = re.sub(r"[^a-z0-9]+", "-", pid.lower()).strip("-")[:64].strip("-") or "adopted-project"
    return {"root": str(root), "source": rel(root, source) if source else None, "stage": parsed["stage"] or "S0",
            "gates": parsed["gates"], "legacyGates": legacy_gates, "decisionFloor": decision_floor(root, files),
            "projectId": pid, "name": parsed["fields"].get("name") or pid, "artifacts": artifacts,
            "proposals": proposals, "notes": notes}


# --- applying ----------------------------------------------------------------------------

def apply(root: Path, the_plan, project_id=None, name=None, locale="pt-BR"):
    root = root.resolve()
    pid = project_id or the_plan["projectId"]
    workspace.init(root, pid, name or the_plan["name"], locale=locale)
    state = workspace.load_state(root)
    if the_plan["decisionFloor"]:
        state["numbering"] = {"decisionFloor": the_plan["decisionFloor"]}
    workspace.save_state(root, state)
    for art in the_plan["artifacts"]:
        if "doc" in art:
            target = workspace.resolve(root, art["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(art["doc"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        state = workspace.load_state(root)
        workspace.register_artifact(root, state, art["id"], art["kind"], art["path"], refresh="doc" in art)
        workspace.save_state(root, state)

    floor = the_plan["decisionFloor"]
    entries = ledger.read(root)
    source = the_plan["source"] or "Markdown"
    for gate in the_plan["legacyGates"]:
        row = the_plan["gates"][gate]
        notes = (f"adopted from {source}: {row['status']} as {row['decisionId'] or 'no id'} on "
                 f"{row['date'] or 'unknown date'}; evidence {row['evidence'] or '—'}")
        stored = ledger.append(root, {
            "kind": "decision", "id": ledger.next_id(entries, "decision", floor=floor), "gate": gate,
            "verdict": "approved", "scope": {"artifacts": [], "notes": notes[:1000]},
            "actorDeclared": "owner (adopted from Markdown)", "channel": "imported-legacy",
            "authenticity": "unverified", "at": workspace.now()})
        entries.append(stored)
    codes = {}
    for gate, artifact_ids in the_plan["proposals"].items():
        proposal = decisions.propose(root, gate, artifact_ids)
        codes[gate] = gates.confirmation_code(proposal)

    state = workspace.load_state(root)
    entries = ledger.read(root)
    results = gates.evaluate(root, state, entries)
    stage = the_plan["stage"]
    while gates.stage_problems(results, stage, tolerate=the_plan["legacyGates"]):
        stage = f"S{int(stage[1]) - 1}"
    state["stage"] = stage
    pending = [g for g in the_plan["legacyGates"] if g in codes]
    if pending:
        state["nextAction"] = ("Reconfirm adopted gates " + ", ".join(f"{g} ({codes[g]})" for g in pending)
                               + ": `lfe approve <gate>` in a terminal, or by chat with the code after "
                               "`lfe chat-approvals enable`")
    else:
        state["nextAction"] = "Review the adopted artifacts in .lfe/adopted/ and propose the next gate"
    gates.refresh_cache(state, results)
    workspace.save_state(root, state)
    report = write_report(root, the_plan, stage, codes)
    return {"stage": stage, "importedStage": the_plan["stage"], "codes": codes, "report": report,
            "nextAction": state["nextAction"]}


def write_report(root: Path, the_plan, stage, codes):
    lines = ["# LFE adoption report", "",
             f"- Source: `{the_plan['source'] or 'none'}`",
             f"- Stage in the Markdown: {the_plan['stage']} · recorded stage: {stage}",
             f"- Ledger decision ids start after DEC-{the_plan['decisionFloor']:03d} (highest id already in the Markdown)",
             "", "## Generated or registered artifacts (review before reconfirming)", ""]
    for art in the_plan["artifacts"]:
        origin = ", ".join(f["path"] for f in art["doc"].get("files", [])) if "doc" in art else art["path"]
        lines.append(f"- **{art['id']}** ({art['kind']}) → `{art['path']}` from {origin[:400]}")
    lines += ["", "## Gates approved in the Markdown", ""]
    for gate in the_plan["legacyGates"]:
        row = the_plan["gates"][gate]
        code = codes.get(gate)
        lines.append(f"- {gate}: {row['decisionId'] or '—'} {row['date'] or ''} → "
                     + (f"proposal ready, confirmation code `{code}`" if code else "cannot be proposed yet"))
    if the_plan["notes"]:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in the_plan["notes"]]
    lines += ["", "Imported approvals never unlock production code by themselves (N-4).", ""]
    path = root / ".lfe" / "ADOPTION.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return rel(root, path)


def adopt(root: Path, state_file=None, project_id=None, name=None, locale="pt-BR", dry_run=False):
    the_plan = plan(root, Path(state_file) if state_file else None)
    if dry_run:
        return {"dryRun": True, "plan": the_plan}
    return {"dryRun": False, "plan": the_plan, **apply(root, the_plan, project_id, name, locale)}


def contract_check(the_plan):
    """Validate the generated JSON artifacts against their contracts (used by tests and --dry-run)."""
    issues = []
    for art in the_plan["artifacts"]:
        if "doc" in art and art["kind"] in workspace.KIND_CONTRACT:
            doc = json.loads(json.dumps(art["doc"]))
            for entry in doc.get("files", []):
                entry["sha256"] = "sha256:" + "0" * 64
            issues += [f"{art['id']}: {i}" for i in contracts.validate(doc, expected=workspace.KIND_CONTRACT[art["kind"]])]
    return issues
