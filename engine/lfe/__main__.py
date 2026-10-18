"""Command line entry point: `PYTHONPATH=engine python3 -m lfe <command>` (RFC-0001, section 9).

Exit codes: 0 ok · 1 internal error · 2 usage, environment or non-interactive channel ·
3 denied by policy/stage rules · 4 incompatible schema · 5 integrity violated · 6 contract violated.
"""
from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
from pathlib import Path

from . import contracts, decisions, gates, ledger, workspace
from .workspace import GATES, STAGES, LfeError

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


def cmd_init(args):
    workspace.init(args.root, args.project_id, args.name, locale=args.locale)
    print(f"initialized {args.root / workspace.STATE_FILE} at S0")
    return EXIT_OK


def cmd_status(args):
    state = workspace.load_state(args.root)
    entries = ledger.read(args.root)
    mismatch = gates.cache_problems(state, entries)
    if mismatch:
        raise LfeError("STATE_CACHE_MISMATCH", "; ".join(mismatch), 5)
    results = gates.evaluate(args.root, state, entries)
    if args.json:
        print(json.dumps({"projectId": state["projectId"], "stage": state["stage"], "gates": results,
                          "nextAction": state["nextAction"], "ledgerEntries": len(entries)},
                         indent=2, ensure_ascii=False))
        return EXIT_OK
    print(f"{state['name']} ({state['projectId']}) · stage {state['stage']} · mode {state['mode']}")
    for gate in GATES:
        r = results[gate]
        line = f"  {gate} {r['status']:<14} {r['decisionId'] or '—':<8} {gates.MEANING[gate]}"
        print(line)
        for reason in r["reasons"]:
            print(f"       ↳ {reason}")
    production = all(gates.is_valid(results, g) for g in ("G2", "G3", "G4"))
    print(f"  production code: {'unlocked' if production else 'locked'}")
    print(f"  next action: {state['nextAction']}")
    return EXIT_OK


def cmd_artifact(args):
    state = workspace.load_state(args.root)
    art, changed = workspace.register_artifact(args.root, state, args.id, args.kind, args.path, refresh=args.refresh_files)
    gates.refresh_cache(state, gates.evaluate(args.root, state, ledger.read(args.root)))
    workspace.save_state(args.root, state)
    print(f"{args.id} r{art['revision']} {art['sha256']} {'(new revision)' if changed else '(unchanged)'}")
    return EXIT_OK


def cmd_propose(args):
    entry = decisions.propose(args.root, args.gate, args.artifact)
    print(f"{entry['id']} proposes {args.gate}: " + ", ".join(f"{a['id']}@r{a['revision']}" for a in entry["scope"]["artifacts"]))
    print("waiting for a human decision: `lfe approve` must be typed by the person, in their own terminal")
    return EXIT_OK


def _exceptions(raw):
    parsed = []
    for item in raw or []:
        parts = [p.strip() for p in item.split("|")]
        if len(parts) != 3 or not all(parts):
            raise LfeError("BAD_EXCEPTION", "use --exception 'description|owner|G5'", 2)
        parsed.append(tuple(parts))
    return parsed


def cmd_approve(args):
    verdict = "not_applicable" if args.not_applicable else "approved"
    entry = decisions.decide(args.root, args.gate, verdict, option=args.option, rationale=args.rationale,
                             exceptions=_exceptions(args.exception), actor=args.actor)
    print(f"{entry['id']} recorded: {args.gate} {verdict}")
    return EXIT_OK


def cmd_reject(args):
    entry = decisions.decide(args.root, args.gate, "rejected", rationale=args.rationale, actor=args.actor)
    print(f"{entry['id']} recorded: {args.gate} rejected")
    return EXIT_OK


def cmd_revoke(args):
    entry = decisions.decide(args.root, args.gate, "revoked", rationale=args.rationale, actor=args.actor)
    print(f"{entry['id']} recorded: {args.gate} revoked")
    return EXIT_OK


def cmd_chat_approval(args):
    composition = json.loads(args.composition) if args.composition else None
    entry = decisions.record_chat_approval(args.root, args.gate, args.quote, option=args.option,
                                           composition=composition, actor=args.actor)
    print(f"{entry['id']} recorded from chat quote: {args.gate} approved (authenticity: unverified)")
    return EXIT_OK


def cmd_stage(args):
    decisions.set_stage(args.root, args.stage)
    print(f"stage set to {args.stage}")
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(prog="lfe", description="Layout-First Engineering core (RFC-0001)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="validate contract documents")
    val.add_argument("files", nargs="+")
    val.add_argument("--contract", choices=sorted(contracts.KNOWN))
    val.set_defaults(func=cmd_validate)

    ini = sub.add_parser("init", help="create .lfe/ at S0")
    ini.add_argument("project_id")
    ini.add_argument("name")
    ini.add_argument("--locale", default="pt-BR")
    ini.set_defaults(func=cmd_init)

    st = sub.add_parser("status", help="computed stage, gates and next action")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    art = sub.add_parser("artifact", help="register the current content of an artifact")
    art.add_argument("id")
    art.add_argument("--kind", required=True, choices=sorted(contracts.ARTIFACT_PREFIX))
    art.add_argument("--path", required=True)
    art.add_argument("--refresh-files", action="store_true", help="rewrite files[] hashes from disk first")
    art.set_defaults(func=cmd_artifact)

    pro = sub.add_parser("propose", help="agent: propose a gate bound to current artifacts")
    pro.add_argument("gate", choices=GATES)
    pro.add_argument("--artifact", action="append", required=True)
    pro.set_defaults(func=cmd_propose)

    app = sub.add_parser("approve", help="person: approve a gate (interactive terminal only)")
    app.add_argument("gate", choices=GATES)
    app.add_argument("--option")
    app.add_argument("--not-applicable", action="store_true", help="only G1 and G6; requires --rationale")
    app.add_argument("--rationale")
    app.add_argument("--exception", action="append", metavar="DESC|OWNER|GATE")
    app.add_argument("--as", dest="actor")
    app.set_defaults(func=cmd_approve)

    rej = sub.add_parser("reject", help="person: send a gate back for revision")
    rej.add_argument("gate", choices=GATES)
    rej.add_argument("--rationale")
    rej.add_argument("--as", dest="actor")
    rej.set_defaults(func=cmd_reject)

    rev = sub.add_parser("revoke", help="person: withdraw an earlier decision")
    rev.add_argument("gate", choices=GATES)
    rev.add_argument("--rationale", required=True)
    rev.add_argument("--as", dest="actor")
    rev.set_defaults(func=cmd_revoke)

    chat = sub.add_parser("record-chat-approval", help="agent: record the user's verbatim G1 choice from chat")
    chat.add_argument("gate", choices=GATES)
    chat.add_argument("--quote", required=True)
    chat.add_argument("--option")
    chat.add_argument("--composition", help="JSON: {primary, themeVariants, complementary, nonNegotiables}")
    chat.add_argument("--as", dest="actor")
    chat.set_defaults(func=cmd_chat_approval)

    stg = sub.add_parser("stage", help="move to a stage; refused when its gates are not valid")
    stg.add_argument("stage", choices=STAGES)
    stg.set_defaults(func=cmd_stage)

    # Extension point: every module named `cli_<topic>.py` in this package exposes
    # `register(subparsers)`. New commands live in their own module, so parallel work
    # never has to edit this file.
    package = sys.modules[__package__]
    for info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if info.name.startswith("cli_"):
            importlib.import_module(f"{__package__}.{info.name}").register(sub)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LfeError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
