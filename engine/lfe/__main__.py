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
    code = gates.confirmation_code(entry)
    print(f"confirmation code: {code}")
    print("waiting for a human decision: the person types `lfe approve` in their own terminal", end="")
    if args.gate in gates.chat_gates(workspace.load_state(args.root)):
        print(f", or replies in chat with \"aprovo {code}\" (record it with `lfe record-chat-approval {args.gate} "
              f"--quote ... --message-ref ...`)")
    else:
        print()
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


def _composition(args):
    raw = None
    if args.composition:
        try:
            raw = json.loads(args.composition)
        except json.JSONDecodeError as exc:
            raise LfeError("BAD_COMPOSITION", f"--composition is not valid JSON ({exc.msg}); see `lfe "
                           "record-chat-approval --help` for an example, or use --primary/--theme-variant", 2) from None
    if args.primary or args.theme_variant or args.complementary or args.non_negotiable:
        raw = dict(raw or {})
        if args.primary:
            raw["primary"] = args.primary
        raw.setdefault("primary", args.option)
        if args.theme_variant:
            raw["themeVariants"] = list(raw.get("themeVariants") or []) + args.theme_variant
        if args.complementary:
            raw["complementary"] = list(raw.get("complementary") or []) + args.complementary
        if args.non_negotiable:
            raw["nonNegotiables"] = list(raw.get("nonNegotiables") or []) + args.non_negotiable
    return raw


def cmd_chat_approval(args):
    entry = decisions.record_chat_approval(args.root, args.gate, args.quote, option=args.option,
                                           composition=_composition(args), actor=args.actor,
                                           message_ref=args.message_ref)
    print(f"{entry['id']} recorded from chat quote: {args.gate} approved (authenticity: unverified)")
    return EXIT_OK


def cmd_chat_approvals(args):
    if args.action == "enable":
        cfg = decisions.set_chat_approvals(args.root, [g.strip() for g in args.gates.split(",")], args.quote,
                                           args.message_ref)
        print(f"chat approvals enabled for {', '.join(cfg['gates'])}, besides G1, which always accepts a chat quote "
              f"(quote recorded, {cfg['messageRef']})")
        print("each approval must quote the confirmation code printed by `lfe propose`")
    elif args.action == "disable":
        decisions.disable_chat_approvals(args.root)
        print("chat approvals disabled: only G1 can be recorded from chat; earlier chat approvals of G2–G6 no longer count")
    else:
        cfg = workspace.load_state(args.root).get("chatApprovals")
        print(json.dumps(cfg or {"gates": []}, indent=2, ensure_ascii=False))
    return EXIT_OK


def cmd_reconfirm(args):
    recorded = decisions.reconfirm(args.root, args.quote, args.message_ref, actor=args.actor)
    print(f"recorded from one chat message: {', '.join(recorded)} approved (authenticity: unverified)")
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

    chat = sub.add_parser(
        "record-chat-approval", help="agent: record the person's verbatim chat approval (G1; G2–G6 when enabled)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # G1, simple choice
  lfe record-chat-approval G1 --quote "Quero a A" --option A
  # G1, hybrid composition without JSON
  lfe record-chat-approval G1 --quote "A no dark, B no light, coleções da C" \\
      --primary A --theme-variant dark=A --theme-variant light=B \\
      --complementary "C=coleções" --non-negotiable "contraste AA"
  # the same composition as JSON (the contract shape)
  --composition '{"primary":"A","themeVariants":[{"theme":"dark","direction":"A"}],
                  "complementary":[{"direction":"C","usage":"coleções"}],"nonNegotiables":["contraste AA"]}'
  # G2–G6 (after `lfe chat-approvals enable`): quote the code printed by `lfe propose`
  lfe record-chat-approval G3 --quote "aprovo G3-7f3a2c" --message-ref "<chat message id or link>"
""")
    chat.add_argument("gate", choices=GATES)
    chat.add_argument("--quote", required=True, help="the person's message, verbatim")
    chat.add_argument("--message-ref", help="id or link of that chat message (required for G2–G6)")
    chat.add_argument("--option")
    chat.add_argument("--composition", help="G1 only, JSON: {primary, themeVariants, complementary, nonNegotiables}")
    chat.add_argument("--primary", help="G1 composition: main direction (defaults to --option)")
    chat.add_argument("--theme-variant", action="append", metavar="THEME=DIRECTION")
    chat.add_argument("--complementary", action="append", metavar="DIRECTION=USAGE")
    chat.add_argument("--non-negotiable", action="append", metavar="TEXT")
    chat.add_argument("--as", dest="actor")
    chat.set_defaults(func=cmd_chat_approval)

    cha = sub.add_parser("chat-approvals", help="opt in/out of chat approvals for G2–G6 (owner's quote required)",
                         description="For owners who only work through chat (mobile, cloud sessions). Off by "
                                     "default. Each chat approval must then quote the proposal's confirmation code.")
    cha.add_argument("action", choices=["enable", "disable", "show"])
    cha.add_argument("--gates", default="G2,G3,G4,G5,G6", help="comma-separated, default G2,G3,G4,G5,G6")
    cha.add_argument("--quote", default="", help="the person's message asking for chat approvals, verbatim")
    cha.add_argument("--message-ref", default="", help="id or link of that chat message")
    cha.set_defaults(func=cmd_chat_approvals)

    rec = sub.add_parser("reconfirm", help="agent: record every gate whose confirmation code is in one chat message",
                         description="For adopted projects: the person replies once with several codes "
                                     "(e.g. 'reconfirmo G1-aaaaaa G2-bbbbbb'); each gate is checked as in "
                                     "record-chat-approval.")
    rec.add_argument("--quote", required=True, help="the person's message, verbatim")
    rec.add_argument("--message-ref", required=True, help="id or link of that chat message")
    rec.add_argument("--as", dest="actor")
    rec.set_defaults(func=cmd_reconfirm)

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
