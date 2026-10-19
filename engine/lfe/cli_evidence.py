"""`lfe run`, `lfe verify-report` and `lfe trace` (RFC-0001, 8.6 and 9; RFC-0002, AC-06..AC-08, AC-12)."""
from __future__ import annotations

import json

from . import evidence


def cmd_run(args):
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    receipt = evidence.run(args.root, args.test_id, argv, requirement_ids=args.req or [],
                           requires=args.requires or [], timeout=args.timeout, cwd=args.cwd)
    line = f"{receipt['id']} {receipt['testId']} {receipt['status']}"
    line += f" (ran {receipt['testsRun']}, skipped {receipt['testsSkipped']}, exit {receipt['exitCode']})"
    if receipt.get("reason"):
        line += f" · {receipt['reason']}"
    print(line)
    rev = receipt["sourceRevision"]
    print(f"  source {rev['git'] or 'unknown'}{' (dirty)' if rev['dirty'] else ''}"
          f" · .lfe/evidence/{receipt['id']}.json")
    return 0


def cmd_verify_report(args):
    receipts = evidence.verify_report(args.root)
    count = sum(len(r["artifacts"]) for r in receipts)
    print(f"OK {len(receipts)} receipts, {count} artifacts match their recorded hashes")
    return 0


def cmd_trace(args):
    report = evidence.trace(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for row in report["requirements"]:
            mark = "ok  " if row["ok"] else "MISS"
            tests = ", ".join(row["tests"]) or "—"
            passing = ", ".join(row["passing"]) or "—"
            print(f"  {mark} {row['id']:<8} {row['status']:<12} tests {tests} · passing {passing}")
            if not row["ok"]:
                print(f"       ↳ {row['missing']}")
        print(f"  trace: {'complete' if report['complete'] else 'incomplete'}")
    return 6 if args.check and not report["complete"] else 0


def register(sub):
    run = sub.add_parser("run", help="run a test without a shell and record an evidence receipt",
                         description="Exit 0 whenever a receipt was written; read its status "
                                     "(pass, fail, blocked, skipped, not_executed).")
    run.add_argument("test_id", metavar="TEST-ID")
    run.add_argument("--req", action="append", metavar="FR-001", help="requirement this run is about (repeatable)")
    run.add_argument("--requires", action="append", metavar="X",
                     help="python:<module> or an executable that must exist, else not_executed (repeatable)")
    run.add_argument("--timeout", type=int, default=evidence.DEFAULT_TIMEOUT, help="seconds (default: %(default)s)")
    run.add_argument("--cwd", default=".", help="working directory, relative to the project root")
    run.add_argument("argv", nargs="+", help="the command, after `--`")
    run.set_defaults(func=cmd_run)

    ver = sub.add_parser("verify-report", help="recompute every evidence artifact hash (exit 5 if tampered)")
    ver.set_defaults(func=cmd_verify_report)

    tr = sub.add_parser("trace", help="requirements → tests → passing receipts")
    tr.add_argument("--check", action="store_true", help="exit 6 if a must or implemented requirement lacks a clean passing receipt")
    tr.add_argument("--json", action="store_true")
    tr.set_defaults(func=cmd_trace)
