"""`lfe demo`: replay an example project with simulated approvals in a separate folder."""
from __future__ import annotations

from pathlib import Path

from . import demo


def cmd_demo(args):
    result = demo.replay(Path(args.source), Path(args.workdir), until=args.until)
    print(f"demo workspace: {result['workdir']}")
    print("simulated approvals (not real human decisions): " + (", ".join(result["approved"]) or "none"))
    for gate, status in result["gates"].items():
        print(f"  {gate} {status}")
    print(f"stage {result['handoff']['stage']} · production code {result['handoff']['productionCode']}")
    return 0


def register(sub):
    p = sub.add_parser("demo", help="replay an example with SIMULATED approvals in a new folder")
    p.add_argument("source", help="example project folder with .lfe/ (e.g. examples/vs01-leituras)")
    p.add_argument("--workdir", required=True, help="new empty folder for the demo copy")
    p.add_argument("--until", default="G4", choices=[f"G{i}" for i in range(1, 7)])
    p.set_defaults(func=cmd_demo)
