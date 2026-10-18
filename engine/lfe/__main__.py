"""Command line entry point: `PYTHONPATH=engine python3 -m lfe <command>`.

Only `validate` exists in v0.1.0.dev0; the remaining RFC-0001 commands arrive in later PRs.
"""
from __future__ import annotations

import argparse
import sys

from . import contracts

EXIT_OK, EXIT_USAGE, EXIT_INCOMPATIBLE, EXIT_INVALID = 0, 2, 4, 6


def cmd_validate(args):
    worst = EXIT_OK
    for path in args.files:
        try:
            issues = contracts.validate_file(path, expected=args.contract)
        except OSError as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            return EXIT_USAGE
        if not issues:
            print(f"OK {path}")
            continue
        for issue in issues:
            print(f"INVALID {path}: {issue}")
        code = EXIT_INCOMPATIBLE if all(i.code == "INCOMPATIBLE_SCHEMA" for i in issues) else EXIT_INVALID
        worst = max(worst, code)
    return worst


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lfe", description="Layout-First Engineering core (RFC-0001)")
    sub = parser.add_subparsers(dest="command", required=True)
    val = sub.add_parser("validate", help="validate contract documents (exit 0 ok, 4 incompatible, 6 invalid)")
    val.add_argument("files", nargs="+")
    val.add_argument("--contract", choices=sorted(contracts.KNOWN), help="require this contract type")
    val.set_defaults(func=cmd_validate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
