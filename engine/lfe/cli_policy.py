"""Action policy commands: check-action, the Claude Code PreToolUse hook and show-policy (RFC-0001 8.5, 9).

Hook contract (Claude Code hooks reference, PreToolUse): the payload arrives on stdin with
`tool_name` and `tool_input`; file tools carry an absolute `file_path` (`notebook_path` for
NotebookEdit) and Bash carries `command`. A denial is printed as
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": "..."}}` with exit 0; the reason is shown to the assistant.
An allowed action prints nothing, so the host's normal permission flow still applies: the hook
can take permissions away, never grant them.
"""
from __future__ import annotations

import json
import sys

from . import contracts, policy

EXIT_OK, EXIT_DENIED = 0, 3

# Tools whose call can change files, and where each keeps its target.
WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
SHELL_TOOLS = {"Bash"}


def _print(doc):
    print(json.dumps(doc, indent=2, ensure_ascii=False))


def cmd_check_action(args):
    if args.target or args.command_line:
        tool = args.tool or ("Bash" if args.command_line and not args.target else "Write")
        decision = policy.check(args.root, tool, args.target or [], args.command_line)
    else:
        request, issues = contracts.parse(sys.stdin.read())
        if issues:
            decision = policy.deny("production_code", issues[0].code, f"invalid ActionRequest: {issues[0]}")
        else:
            decision = policy.decide(args.root, request)
    _print(decision)
    return EXIT_OK if decision["allowed"] else EXIT_DENIED


def hook_response(root, payload):
    """Map a PreToolUse payload to the hook's stdout document, or None to stay silent (no decision)."""
    tool = payload.get("tool_name")
    if tool not in WRITE_TOOLS and tool not in SHELL_TOOLS:
        return None  # reads never pass through the policy
    if not (root / ".lfe").is_dir():
        return None  # LFE is not in use in this project
    tool_input = payload.get("tool_input") or {}
    if tool in WRITE_TOOLS:
        target = tool_input.get(WRITE_TOOLS[tool]) or tool_input.get("file_path")
        if not isinstance(target, str) or not target:
            raise ValueError(f"{tool} payload without {WRITE_TOOLS[tool]}")
        decision = policy.check(root, tool, [target])
    else:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Bash payload without command")
        decision = policy.check(root, tool, [], command)
    if decision["allowed"]:
        return None
    return _deny(f"LFE {decision['reasonCode']} [{decision['class']}]: {decision['message'].rstrip('.')}."
                 + (f" Missing: {', '.join(decision['missing'])}." if decision["missing"] else "")
                 + " Do not work around this rule; tell the person what is needed.")


def _deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def cmd_hook_pre_tool_use(args):
    """Fail closed for tools that write; fail open only for tools the policy never governs."""
    tool = None
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        tool = payload.get("tool_name") if isinstance(payload, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("payload is not a JSON object")
        response = hook_response(args.root, payload)
    except Exception as exc:  # noqa: BLE001 — any failure of the core must not let a write through
        if tool is not None and tool not in WRITE_TOOLS and tool not in SHELL_TOOLS:
            return EXIT_OK
        if not (args.root / ".lfe").exists():
            return EXIT_OK
        response = _deny(f"LFE_INTERNAL_ERROR: the LFE policy could not evaluate this action "
                         f"({type(exc).__name__}: {exc}), so it is denied (fail closed). "
                         "Ask the person to run `lfe status` and fix the project state.")
    if response is not None:
        print(json.dumps(response, ensure_ascii=False))
    return EXIT_OK


def cmd_show_policy(args):
    _print(policy.load_policy(args.root))
    return EXIT_OK


def register(sub):
    p = sub.add_parser("check-action", help="classify an agent action and print a PolicyDecision (exit 3 if denied)",
                       description="Reads an ActionRequest JSON from stdin, or builds one from the flags.")
    p.add_argument("--tool", help="host tool name (default: Write with --target, Bash with --command)")
    p.add_argument("--target", action="append", help="file the action writes; repeatable")
    p.add_argument("--command", dest="command_line", help="shell command the action runs")
    p.set_defaults(func=cmd_check_action)

    p = sub.add_parser("hook-pre-tool-use", help="Claude Code PreToolUse hook (payload on stdin)")
    p.set_defaults(func=cmd_hook_pre_tool_use)

    p = sub.add_parser("show-policy", help="print the project policy in effect (built-in rules always apply too)")
    p.set_defaults(func=cmd_show_policy)
