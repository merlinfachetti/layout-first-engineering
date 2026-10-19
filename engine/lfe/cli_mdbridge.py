"""`lfe render` and `lfe import-md`: the Markdown bridge (RFC-0001, section 10)."""
from __future__ import annotations

from pathlib import Path

from . import mdbridge


def cmd_render(args):
    target = args.file if args.file.is_absolute() else args.root / args.file
    outcome = mdbridge.render(args.root, target)
    print(f"{target}: {outcome} (gate block and current stage from .lfe/)")
    return 0


def cmd_import_md(args):
    source = args.path if args.path.is_absolute() else args.root / args.path
    report = mdbridge.import_md(args.root, source, project_id=args.project_id, name=args.name)
    print(f"{'created' if report['created'] else 'updated'} .lfe/ from {source}")
    print(f"  stage: {report['stage']}" + (f" (file says {report['importedStage']})"
                                          if report["stage"] != report["importedStage"] else ""))
    for gate in report["imported"]:
        print(f"  {gate}: imported-legacy, authenticity unverified → reconfirm with `lfe approve`")
    for gate in report["skipped"]:
        print(f"  {gate}: already decided in the ledger, not imported")
    print("  imported approvals never unlock S6 (N-4); the person must reconfirm them")
    print(f"  next action: {report['nextAction']}")
    return 0


def register(sub):
    ren = sub.add_parser("render", help="write the computed gates into PROJECT_STATE.md (marked block only)")
    ren.add_argument("--file", type=Path, default=Path("PROJECT_STATE.md"))
    ren.set_defaults(func=cmd_render)

    imp = sub.add_parser("import-md", help="import a legacy PROJECT_STATE.md; approvals need reconfirmation")
    imp.add_argument("path", type=Path)
    imp.add_argument("--project-id", help="used only when .lfe/ does not exist yet")
    imp.add_argument("--name", help="used only when .lfe/ does not exist yet")
    imp.set_defaults(func=cmd_import_md)
