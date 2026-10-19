"""Continuity commands: handoff, next, question, export, import and session hooks (RFC-0001 8.7)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import contracts, handoff
from .workspace import STATE_FILE, LfeError


def cmd_handoff(args):
    doc = handoff.write(args.root)
    print(handoff.to_json(doc) if args.json else handoff.render_markdown(doc), end="" if not args.json else "\n")
    return 0


def cmd_next(args):
    handoff.set_next(args.root, args.text)
    print(f"next action saved: {args.text.strip()}")
    return 0


def cmd_question(args):
    if args.action == "add":
        q = handoff.add_question(args.root, args.text, args.klass, args.stage)
        print(f"{q['id']} added ({q['class']})")
    else:
        handoff.close_question(args.root, args.text)
        print(f"{args.text} closed")
    return 0


def cmd_export(args):
    bundle = handoff.export(args.root)
    Path(args.out).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"exported {len(bundle['decisions'])} decisions and {len(bundle['files'])} files to {args.out}")
    return 0


def cmd_import(args):
    doc, issues = contracts.parse(Path(args.bundle).read_text(encoding="utf-8"))
    if issues:
        raise LfeError(issues[0].code, str(issues[0]), 6)
    args.root.mkdir(parents=True, exist_ok=True)
    result = handoff.import_bundle(args.root, doc)
    print(f"imported into {args.root}: stage {result['stage']}, production code {result['productionCode']}")
    return 0


def _hook_payload():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def cmd_hook_session_start(args):
    """SessionStart hook: inject where the project stopped. Silent when LFE is not in use."""
    _hook_payload()
    if not (args.root / STATE_FILE).exists():
        return 0
    try:
        context = handoff.brief(handoff.write(args.root))
    except LfeError as exc:
        context = f"LFE state could not be loaded ({exc.code}). Do not guess the project state; run `lfe status`."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


def cmd_hook_stop(args):
    """Stop hook: refresh .lfe/HANDOFF.md so the next session resumes from facts. Never blocks."""
    _hook_payload()
    if (args.root / STATE_FILE).exists():
        try:
            handoff.write(args.root)
        except LfeError as exc:
            print(f"lfe: handoff not refreshed: {exc}", file=sys.stderr)
    return 0


def register(sub):
    p = sub.add_parser("handoff", help="generate .lfe/HANDOFF.md from ledger, state and evidence")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("next", help="save the next single action")
    p.add_argument("text")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("question", help="track open questions: add TEXT --class … | close Q-###")
    p.add_argument("action", choices=["add", "close"])
    p.add_argument("text")
    p.add_argument("--class", dest="klass", choices=["blocker", "important", "deferred"], default="important")
    p.add_argument("--stage", choices=[f"S{i}" for i in range(10)])
    p.set_defaults(func=cmd_question)

    p = sub.add_parser("export", help="portable bundle: state, ledger, artifacts and evidence")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="restore a bundle into an empty folder (never elevates any decision)")
    p.add_argument("bundle")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("hook-session-start", help="Claude Code SessionStart hook")
    p.set_defaults(func=cmd_hook_session_start)

    p = sub.add_parser("hook-stop", help="Claude Code Stop hook")
    p.set_defaults(func=cmd_hook_stop)
