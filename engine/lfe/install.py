"""`lfe install --project`: vendor the skill, engine and hooks into a repository (issue #29).

Cloud sessions (claude.ai/code, project threads, CI agents) start from a fresh clone and do not
have the user's plugins, so the skill is missing and no hook runs. Vendoring puts everything the
session needs inside the repository:

- `.claude/skills/layout-first-engineering/` — SKILL.md, references, assets, scripts, the engine
  (`engine/lfe`) and the contract schemas, the same layout as the release zip;
- `.claude/settings.json` — the PreToolUse, SessionStart and Stop hooks pointing at that copy,
  merged into any existing settings (nothing else is changed or removed).

The copy is pinned to the installing version and listed with hashes in `INSTALL.json`, so
`lfe install --check` can tell whether it is current. Standard library only.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import __version__, contracts
from .workspace import LfeError, write_json_atomic

TARGET = Path(".claude") / "skills" / "layout-first-engineering"
SETTINGS = Path(".claude") / "settings.json"
MANIFEST = "INSTALL.json"
LAUNCHER = '"$CLAUDE_PROJECT_DIR/.claude/skills/layout-first-engineering/scripts/lfe.py"'
HOOKS = {
    "PreToolUse": ("Write|Edit|MultiEdit|NotebookEdit|Bash",
                   f'python3 {LAUNCHER} --root "$CLAUDE_PROJECT_DIR" hook-pre-tool-use || exit 2'),
    "SessionStart": (None, f'python3 {LAUNCHER} --root "$CLAUDE_PROJECT_DIR" hook-session-start'),
    "Stop": (None, f'python3 {LAUNCHER} --root "$CLAUDE_PROJECT_DIR" hook-stop'),
}
DENY = ["Edit(/.lfe/state.json)", "Edit(/.lfe/decisions.jsonl)", "Edit(/.lfe/evidence/**)", "Edit(/.lfe/policy.json)"]
SKIP = {"__pycache__", ".DS_Store"}


def sources():
    """(source file, path inside the installed skill) for the running engine's skill."""
    engine = Path(__file__).resolve().parent              # .../engine/lfe
    base = engine.parents[1]
    skill = base / "layout-first-engineering" if (base / "layout-first-engineering" / "SKILL.md").is_file() else base
    if not (skill / "SKILL.md").is_file():
        raise LfeError("SKILL_NOT_FOUND", f"no SKILL.md next to the engine ({skill})", 2)
    pairs = []
    for path in sorted(skill.rglob("*")):
        relative = path.relative_to(skill)
        if not path.is_file() or any(part in SKIP or part.startswith(".") for part in relative.parts):
            continue
        if relative.parts[0] in ("engine", "contracts") or relative.as_posix() == MANIFEST:
            continue  # taken from the running engine below, so the copy matches what is executing
        pairs.append((path, relative.as_posix()))
    pairs += [(p, f"engine/lfe/{p.name}") for p in sorted(engine.glob("*.py"))]
    pairs += [(p, f"contracts/{p.name}") for p in sorted(contracts.CONTRACTS_DIR.glob("*.schema.json"))]
    return pairs


def _merge_settings(path: Path):
    doc = {}
    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LfeError("BAD_SETTINGS", f"{path} is not valid JSON ({exc.msg}); fix it first, nothing was changed", 6) from None
        if not isinstance(doc, dict):
            raise LfeError("BAD_SETTINGS", f"{path} must be a JSON object", 6)
    changed = []
    hooks = doc.setdefault("hooks", {})
    for event, (matcher, command) in HOOKS.items():
        groups = hooks.setdefault(event, [])
        present = any(command == h.get("command") for g in groups if isinstance(g, dict)
                      for h in g.get("hooks", []) if isinstance(h, dict))
        if not present:
            group = {"hooks": [{"type": "command", "command": command}]}
            if matcher:
                group = {"matcher": matcher, **group}
            groups.append(group)
            changed.append(f"hook {event}")
    deny = doc.setdefault("permissions", {}).setdefault("deny", [])
    for rule in DENY:
        if rule not in deny:
            deny.append(rule)
            changed.append(f"deny {rule}")
    return doc, changed


def install(root: Path, dry_run=False):
    root = root.resolve()
    target = root / TARGET
    pairs = sources()
    manifest = {"version": __version__, "files": {name: contracts.sha256_of(src.read_bytes()) for src, name in pairs}}
    settings_doc, settings_changes = _merge_settings(root / SETTINGS)
    current = check(root)
    copy_needed = current["status"] != "current"
    if not dry_run:
        if copy_needed:
            if target.exists():
                shutil.rmtree(target)  # only the vendored skill folder, which this command owns
            for src, name in pairs:
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
                if name.startswith("scripts/"):
                    dest.chmod(0o755)
            write_json_atomic(target / MANIFEST, manifest)
        if settings_changes:
            write_json_atomic(root / SETTINGS, settings_doc)
    return {"target": TARGET.as_posix(), "version": __version__, "files": len(pairs), "copied": copy_needed,
            "settingsChanges": settings_changes, "dryRun": dry_run, "previous": current}


def check(root: Path):
    """Is the vendored copy present, the same version and unmodified?"""
    target = root / TARGET
    path = target / MANIFEST
    if not path.is_file():
        return {"status": "missing", "problems": [f"{TARGET.as_posix()} is not installed"]}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "modified", "problems": [f"{MANIFEST} is not valid JSON"]}
    problems = []
    for name, digest in manifest.get("files", {}).items():
        file = target / name
        if not file.is_file():
            problems.append(f"{name} is missing")
        elif contracts.sha256_of(file.read_bytes()) != digest:
            problems.append(f"{name} was modified")
    if problems:
        return {"status": "modified", "version": manifest.get("version"), "problems": problems}
    expected = {name: contracts.sha256_of(src.read_bytes()) for src, name in sources()}
    if manifest.get("version") != __version__ or manifest.get("files") != expected:
        return {"status": "outdated", "version": manifest.get("version"),
                "problems": [f"installed {manifest.get('version')}, engine {__version__}; run `lfe install --project`"]}
    settings = root / SETTINGS
    try:
        doc = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except json.JSONDecodeError:
        doc = {}
    commands = {h.get("command") for groups in (doc.get("hooks") or {}).values() if isinstance(groups, list)
                for g in groups if isinstance(g, dict) for h in g.get("hooks", []) if isinstance(h, dict)}
    missing = [event for event, (_, command) in HOOKS.items() if command not in commands]
    if missing:
        return {"status": "hooks-missing", "version": __version__,
                "problems": [f"{SETTINGS.as_posix()} lacks the {', '.join(missing)} hook(s)"]}
    return {"status": "current", "version": __version__, "problems": []}
