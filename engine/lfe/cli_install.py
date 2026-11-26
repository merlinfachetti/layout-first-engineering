"""`lfe install --project` and `lfe install --check` (issue #29)."""
from __future__ import annotations

from . import install


def cmd_install(args):
    if args.check:
        result = install.check(args.root)
        print(f"{install.TARGET.as_posix()}: {result['status']}")
        for problem in result["problems"]:
            print(f"  {problem}")
        return 0 if result["status"] == "current" else 3
    if not args.project:
        print("use `lfe install --project` (vendor into this repository) or `lfe install --check`")
        return 2
    result = install.install(args.root, dry_run=args.dry_run)
    verb = "would install" if args.dry_run else "installed"
    print(f"{verb} lfe {result['version']} into {result['target']} ({result['files']} files"
          f"{'' if result['copied'] else ', already current'})")
    for change in result["settingsChanges"]:
        print(f"  .claude/settings.json: + {change}")
    if not args.dry_run:
        print("  commit .claude/ so every cloud session of this repository loads the skill and the hooks")
    return 0


def register(sub):
    p = sub.add_parser("install", help="vendor the skill, engine and hooks into this repository (cloud sessions)",
                       description="Copies the skill and engine to .claude/skills/layout-first-engineering/ and "
                                   "merges the LFE hooks into .claude/settings.json. Commit both so cloud "
                                   "sessions, which do not have your plugins, still load the skill and hooks.")
    p.add_argument("--project", action="store_true", help="install into the project at --root")
    p.add_argument("--check", action="store_true", help="report whether the vendored copy is current (exit 3 if not)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install)
