"""`lfe adopt`: start the engine on a project that is already under way (issue #28)."""
from __future__ import annotations

import json
from pathlib import Path

from . import adopt


def cmd_adopt(args):
    result = adopt.adopt(args.root, state_file=args.state_file, project_id=args.project_id, name=args.name,
                         locale=args.locale, dry_run=args.dry_run)
    the_plan = result["plan"]
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    print(f"{'plan for' if args.dry_run else 'adopted'} {the_plan['name']} ({the_plan['projectId']}) "
          f"from {the_plan['source'] or 'no PROJECT_STATE.md'}")
    print(f"  stage in the Markdown: {the_plan['stage']}"
          + ("" if args.dry_run else f" · recorded: {result['stage']}"))
    print(f"  ledger ids continue after DEC-{the_plan['decisionFloor']:03d}")
    for art in the_plan["artifacts"]:
        print(f"  {art['id']:<10} {art['kind']:<22} {art['path']}{'  (generated draft)' if 'doc' in art else ''}")
    for gate in the_plan["legacyGates"]:
        code = (result.get("codes") or {}).get(gate)
        state = "will be proposed" if args.dry_run and gate in the_plan["proposals"] else (
            f"proposed, confirmation code {code}" if code else "cannot be proposed yet")
        print(f"  {gate}: approved in Markdown → {state}")
    for note in the_plan["notes"]:
        print(f"  note: {note}")
    if args.dry_run:
        problems = adopt.contract_check(the_plan)
        for problem in problems:
            print(f"  contract: {problem}")
        print("  nothing was written (--dry-run)")
        return 6 if problems else 0
    print(f"  report: {result['report']}")
    print(f"  next action: {result['nextAction']}")
    return 0


def register(sub):
    p = sub.add_parser("adopt", help="start LFE on a project already under way, keeping its history and numbering",
                       description="Reads PROJECT_STATE.md tolerantly, continues DEC ids after the project's own, "
                                   "generates draft typed artifacts in .lfe/adopted/ and proposes each gate the "
                                   "Markdown says was approved, ready for reconfirmation.")
    p.add_argument("--state-file", type=Path, help="PROJECT_STATE.md to read (default: the shallowest one found)")
    p.add_argument("--project-id")
    p.add_argument("--name")
    p.add_argument("--locale", default="pt-BR")
    p.add_argument("--dry-run", action="store_true", help="print the plan and validate it; write nothing")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_adopt)
