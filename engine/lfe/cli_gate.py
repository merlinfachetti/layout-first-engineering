"""`lfe gate G5`: automated quality checks against a budget (issue #31)."""
from __future__ import annotations

import json

from . import quality


def cmd_gate(args):
    result = quality.evaluate(args.root, args.lighthouse or [], args.axe or [], args.budget)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for c in result["checks"]:
            print(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['check']:<38} {c['value']:<18} {c['limit']:<10} {c['where']}")
    failures = sum(not c["ok"] for c in result["checks"])
    # unittest-style summary, so `lfe run` records this as an ordinary evidence receipt
    print(f"Ran {len(result['checks'])} tests in 0.0s")
    print("OK" if not failures else f"FAILED (failures={failures})")
    return 0 if result["passed"] else 3


def register(sub):
    p = sub.add_parser("gate", help="automated gate checks: G5 reads Lighthouse and axe JSON against a budget",
                       description="Budget defaults: performance >= 90, accessibility >= 95, best-practices >= 90, "
                                   "SEO >= 90, LCP <= 2500 ms, CLS <= 0.1, TBT <= 200 ms, no critical or serious axe "
                                   "violations. Override in .lfe/budget.json or --budget. Record it as evidence with "
                                   "`lfe run TEST-### --req NFR-### -- python3 <skill>/scripts/lfe.py gate G5 ...`.")
    p.add_argument("gate", choices=["G5"])
    p.add_argument("--lighthouse", action="append", metavar="REPORT.json", help="repeatable (mobile, desktop, pages)")
    p.add_argument("--axe", action="append", metavar="RESULTS.json", help="repeatable")
    p.add_argument("--budget", help="budget JSON (default .lfe/budget.json, else built-in)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_gate)
