"""Agent action policy: classify an ActionRequest and decide (RFC-0001, 8.5; invariants I-01, I-07).

Every target path and the command are classified into action classes. When several rules match,
the most restrictive class wins, so the order of rules never matters and a project policy can
only add restrictions on top of the built-in ones. Anything not classified is `production_code`.

Built-in rules always apply, whatever `.lfe/policy.json` says: the agent can never write the
state, the ledger, evidence or the policy itself, never run `lfe approve|reject|revoke`, and never
deploy, publish, spend, delete or touch secrets in v0.1, even with G6 approved.

Reading files never passes through the policy. Command classification is heuristic: it is a
defence layer, and the ledger hash chain (D-01) is the detection layer behind it.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from . import contracts, gates, ledger, workspace
from .workspace import LfeError

POLICY_FILE = Path(".lfe") / "policy.json"
PRODUCTION_GATES = ("G2", "G3", "G4")

# Most restrictive first. The first class in this list among the matches is the action's class.
PRIORITY = ["lfe_human_command", "lfe_state", "secret", "deploy", "publish", "cost", "delete",
            "production_code", "prototype", "docs"]
ALWAYS_DENIED = {
    "lfe_human_command": ("HUMAN_CHANNEL_REQUIRED",
                          "only a person can approve, reject or revoke, in their own interactive terminal"),
    "lfe_state": ("PROTECTED_STATE",
                  "LFE state, ledger, evidence, policy and hook configuration change only through the `lfe` CLI"),
}
for _cls in ("deploy", "publish", "cost", "delete", "secret"):
    ALWAYS_DENIED[_cls] = ("DENY_REQUIRES_EXPLICIT_AUTH",
                           f"{_cls} actions are never delegated to the agent in v0.1, even with G6 approved (I-07); "
                           "the person runs them directly")
ALLOWED_CLASSES = ("docs", "prototype")

# A command word in shell position: start of the command, after a separator, a quote or `$(`,
# optionally behind `sudo`, env assignments or a package runner such as `npx`.
_AT = (r"(?:^|[;&|(\n'\"`]|\$\()\s*(?:sudo\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
       r"(?:(?:npx|bunx|pnpx)\s+(?:-y\s+)?|(?:pnpm|yarn)\s+dlx\s+)?")
_SIMPLE = r"[^;&|`$<>\n]*$"          # a single command: no chaining, redirection or substitution
_CD = r"^\s*(?:cd\s+[^;&|`$<>\n]+&&\s*)?"
# Options that make an otherwise read-only command execute or write (find -exec, rg --pre, git --output).
_NO_EXEC = r"(?![^\n]*\s(?:-exec|-execdir|-ok|-okdir|-delete|-fprint\w*|-fls|--pre|--output|--ext-diff|--textconv)\b)"
_ENV = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
# `lfe` subcommands the agent may run at any stage; approve/reject/revoke are built-in denials.
_LFE_AGENT_COMMANDS = (r"(?:status|propose|artifact|validate|init|record-chat-approval|check-action|version|next|"
                       r"question|handoff|trace|impact|doctor|verify-report|render|stage|export|import|import-md|"
                       r"show-policy)\b")
_PROTECTED_RE = r"\.lfe/(?:state\.json|decisions\.jsonl|policy\.json|evidence\b)"

BUILTIN_PATHS = [
    {"glob": ".lfe/state.json", "class": "lfe_state"},
    {"glob": ".lfe/decisions.jsonl", "class": "lfe_state"},
    {"glob": ".lfe/evidence/**", "class": "lfe_state"},
    {"glob": ".lfe/policy.json", "class": "lfe_state"},
]
BUILTIN_COMMANDS = [
    # `lfe approve|reject|revoke`, also as `python3 -m lfe`, with global options before the verb.
    {"pattern": r"\blfe(?:\.__main__)?\b[^;&|\n]*?\s(?:approve|reject|revoke)\b", "class": "lfe_human_command"},
    # Writing a protected file from the shell (reading it stays allowed).
    {"pattern": r"(?i)(?:>|\btee\b|\bsed\b[^;&|\n]*\s-i|\b(?:cp|mv|rm|truncate|dd|ln|touch|install|rsync|"
                r"chmod|git\s+(?:checkout|restore|reset|rm|mv|stash))\b)[^;&|\n]*" + _PROTECTED_RE,
     "class": "lfe_state"},
    {"pattern": _AT + r"(?:vercel|netlify|flyctl|wrangler|railway|heroku|surge)\b", "class": "deploy"},
    {"pattern": _AT + r"(?:fly|firebase|serverless|sls|cdk|sam|pulumi|amplify|eb)\s+(?:deploy|up|publish)\b",
     "class": "deploy"},
    {"pattern": _AT + r"kubectl\s+(?:apply|create|replace|rollout|scale|delete|patch)\b", "class": "deploy"},
    {"pattern": _AT + r"helm\s+(?:install|upgrade|uninstall|rollback)\b", "class": "deploy"},
    {"pattern": _AT + r"(?:npm|yarn|pnpm|bun)\s+publish\b", "class": "publish"},
    {"pattern": _AT + r"gh\s+release\s+(?:create|upload|edit|delete)\b", "class": "publish"},
    {"pattern": _AT + r"(?:twine\s+upload|cargo\s+publish|gem\s+push|docker\s+push|(?:poetry|uv|flit|hatch)\s+publish)\b",
     "class": "publish"},
    {"pattern": _AT + r"(?:aws|gcloud|az|doctl)\s", "class": "cost"},
    {"pattern": _AT + r"terraform\s+(?:apply|destroy|import)\b", "class": "cost"},
    {"pattern": _AT + r"gh\s+codespace\s+create\b", "class": "cost"},
    {"pattern": _AT + r"rm\s+(?:[^;&|\n]*\s)?(?:-[A-Za-z]*[rRf][A-Za-z]*|--recursive|--force)\b", "class": "delete"},
    {"pattern": _AT + r"git\s+push\b[^;&|\n]*\s(?:--force(?:-with-lease)?\b|-f\b|--delete\b|--mirror\b|\+\S)",
     "class": "delete"},
    {"pattern": _AT + r"git\s+(?:reset\s+--hard|clean\s+-\S*f|branch\s+-D\b|filter-branch|filter-repo)",
     "class": "delete"},
    {"pattern": _AT + r"(?:gh\s+repo\s+delete|dropdb|shred)\b", "class": "delete"},
    {"pattern": r"\bfind\b[^;&|\n]*\s-delete\b", "class": "delete"},
    {"pattern": r"(?i)\bdrop\s+(?:table|database|schema)\b", "class": "delete"},
    {"pattern": r"(?:^|[\s/'\"=])\.env(?!\.(?:example|sample|template)\b)(?:\.[\w-]+)?(?=$|[\s'\";|&)])",
     "class": "secret"},
    {"pattern": r"\b(?:id_rsa|id_ed25519|id_ecdsa)\b|\.(?:pem|p12|pfx)\b", "class": "secret"},
    {"pattern": _AT + r"(?:gh\s+auth\s+token|security\s+find-(?:generic|internet)-password|printenv)\b",
     "class": "secret"},
    {"pattern": _AT + r"env\s*(?:$|[;&|])", "class": "secret"},
]

# Project policy used when `.lfe/policy.json` does not exist. It only adds to the built-in rules.
DEFAULT_POLICY = {
    "schemaVersion": "lfe.policy/0.1",
    "pathClasses": [
        {"glob": ".lfe/HANDOFF.md", "class": "lfe_state"},
        {"glob": ".claude/settings.json", "class": "lfe_state"},
        {"glob": ".claude/settings.local.json", "class": "lfe_state"},
        {"glob": ".claude/hooks/**", "class": "lfe_state"},
        {"glob": ".claude/skills/layout-first-engineering/**", "class": "lfe_state"},
        {"glob": ".lfe/**", "class": "docs"},
        {"glob": "docs/**", "class": "docs"},
        {"glob": "**/*.md", "class": "docs"},
        {"glob": "prototype/**", "class": "prototype"},
        {"glob": "directions/**", "class": "prototype"},
        {"glob": "**/.env", "class": "secret"},
        {"glob": "**/.env.*", "class": "secret"},
        {"glob": "**/*.pem", "class": "secret"},
        {"glob": "**/*.key", "class": "secret"},
        {"glob": "**/id_rsa*", "class": "secret"},
        {"glob": "**/id_ed25519*", "class": "secret"},
    ],
    "commandClasses": [
        {"pattern": _CD + _NO_EXEC + r"(?:ls|pwd|cat|head|tail|wc|grep|rg|find|stat|which|echo|diff|du|df|date|"
                          r"whoami|uname)\b" + _SIMPLE, "class": "docs"},
        {"pattern": _CD + _NO_EXEC + r"git\s+(?:status|log|diff|show|branch|rev-parse|ls-files|blame|remote\s+-v)\b" + _SIMPLE,
         "class": "docs"},
        {"pattern": _CD + _ENV + r"(?:lfe|python3?\s+-m\s+lfe|python3?\s+\S*lfe\.py)(?:\s+--root\s+\S+)?\s+"
                          + _LFE_AGENT_COMMANDS + _SIMPLE, "class": "docs"},
        {"pattern": r"^\s*[\w.-]+\s+(?:--version|-V|version)\s*$", "class": "docs"},
    ],
}


# --- loading --------------------------------------------------------------------------

def load_policy(root: Path):
    """The project policy: `.lfe/policy.json` when present (strictly validated), else the default."""
    path = root / POLICY_FILE
    if not path.exists():
        return DEFAULT_POLICY
    return workspace.read_contract(path, "policy")


# --- classification -------------------------------------------------------------------

@lru_cache(maxsize=None)
def glob_regex(glob):
    """Translate a project glob: `**` crosses segments, `*` and `?` stay inside one. Case-insensitive,
    because macOS and Windows file systems are, and a protected file must not hide behind `.LFE/`."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("/**", i) and i + 3 == len(glob):
            out.append("(?:/.*)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out), re.IGNORECASE)


def _most_restrictive(classes):
    return min(classes, key=PRIORITY.index) if classes else "production_code"


def classify_path(rel: str, policy) -> str:
    rules = BUILTIN_PATHS + policy["pathClasses"]
    return _most_restrictive({r["class"] for r in rules if glob_regex(r["glob"]).fullmatch(rel)})


# Variables that change which code a command loads. Path lists are checked entry by entry; the
# others can inject code by themselves and are never trusted.
_ASSIGNMENT = re.compile(r"(?:^|[\s;&|(])(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(\S*)")
_PATH_LISTS = {"PYTHONPATH", "PATH", "NODE_PATH", "PERL5LIB", "RUBYLIB", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH",
               "DYLD_FRAMEWORK_PATH"}
_CODE_VARS = {"PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE", "PYTHONINSPECT", "LD_PRELOAD", "LD_AUDIT",
              "NODE_OPTIONS", "BASH_ENV", "ENV", "RUBYOPT", "PERL5OPT", "GIT_EXEC_PATH", "GIT_CONFIG_GLOBAL",
              "GIT_DIR", "GIT_WORK_TREE"}
_SCRIPT = re.compile(r"\bpython3?(?:\.\d+)?\s+(?:-\S+\s+)*([^\s-]\S*\.py)\b")


def _agent_writable(root: Path, path: str, policy) -> bool:
    """True when the agent could have written `path`: inside the project and not protected."""
    path = os.path.expanduser(path.strip("'\""))
    spellings = project_paths(root, path)
    if spellings is None:
        return False  # outside the project: file tools are denied there (UNSAFE_PATH)
    return any(classify_path(rel, policy) not in ALWAYS_DENIED for rel in spellings)


def untrusted_code(root: Path, command: str, policy) -> bool:
    """An allowlisted command must only load code the agent cannot write (no module or env hijack)."""
    for name, value in _ASSIGNMENT.findall(command):
        if name in _CODE_VARS or (name.startswith("DYLD_") and name not in _PATH_LISTS):
            return True
        if name in _PATH_LISTS and any(_agent_writable(root, entry or ".", policy) for entry in value.split(":")):
            return True
    # `python -m` imports from the current directory, and a `cd` can point it at a writable folder.
    if re.search(r"(?:^|[;&|\s])cd\s", command) and re.search(r"\bpython3?(?:\.\d+)?\s+(?:-\S+\s+)*-m\b", command):
        return True
    return any(_agent_writable(root, script, policy) for script in _SCRIPT.findall(command))


def classify_command(command: str, policy, root: Path | None = None) -> str:
    rules = BUILTIN_COMMANDS + policy["commandClasses"]
    matched = {r["class"] for r in rules if re.search(r["pattern"], command)}
    if any(p.search(command) for p in contracts.SECRET_PATTERNS):
        matched.add("secret")
    cls = _most_restrictive(matched)
    if cls in ALLOWED_CLASSES and root is not None and untrusted_code(root, command, policy):
        return "production_code"
    return cls


def project_paths(root: Path, target: str):
    """Every project-relative spelling of `target` (lexical first), or None when it leaves the project.

    The lexical path and the path after following symlinks are both classified, so a symlinked
    directory cannot launder a write into `.lfe/`. Relative targets are taken from the root.
    """
    base = Path(os.path.abspath(root))
    real_base = base.resolve()
    lexical = Path(os.path.normpath(target if os.path.isabs(target) else base / target))
    spellings = []
    for anchor in (base, real_base):
        if lexical.is_relative_to(anchor):
            spellings.append(lexical.relative_to(anchor).as_posix())
            break
    resolved = lexical.resolve()
    if not spellings or not resolved.is_relative_to(real_base):
        return None
    if resolved.relative_to(real_base).as_posix() not in spellings:
        spellings.append(resolved.relative_to(real_base).as_posix())
    return spellings


# --- decision -------------------------------------------------------------------------

def _decision(allowed, cls, reason_code=None, message="", missing=()):
    doc = {"schemaVersion": "lfe.policy-decision/0.1", "allowed": allowed, "class": cls,
           "reasonCode": reason_code, "message": message, "missing": list(missing),
           "evaluatedAt": workspace.now()}
    issues = contracts.validate(doc, expected="policy-decision")
    if issues:
        raise LfeError(issues[0].code, "; ".join(map(str, issues)), 1)
    return doc


def deny(cls, reason_code, message, missing=()):
    return _decision(False, cls, reason_code, message, missing)


def _production_check(root: Path):
    """production_code: stage >= S6 and G2, G3, G4 valid, recomputed from the ledger (N-2)."""
    try:
        state = workspace.load_state(root)
        entries = ledger.read(root)
    except LfeError as exc:
        return deny("production_code", exc.code, f"cannot verify gates: {exc.args[0]}", PRODUCTION_GATES)
    mismatch = gates.cache_problems(state, entries)
    if mismatch:
        return deny("production_code", "STATE_CACHE_MISMATCH", "; ".join(mismatch), PRODUCTION_GATES)
    results = gates.evaluate(root, state, entries)
    invalid = [g for g in PRODUCTION_GATES if not gates.is_valid(results, g)]
    if invalid:
        # The first invalid gate is the root cause: later gates are blocked by it (D-04).
        code = "GATE_STALE" if results[invalid[0]]["status"] == "stale" else "GATE_NOT_APPROVED"
        details = []
        for gate in invalid:
            r = results[gate]
            detail = f"{gate} is {r['status']}"
            if r["reasons"]:
                detail += f" ({'; '.join(r['reasons'])})"
            details.append(detail)
        return deny("production_code", code,
                    "production code needs G2, G3 and G4 approved and still bound to the current content; "
                    + "; ".join(details) + ". Propose with `lfe propose`; the person approves in their terminal.",
                    invalid)
    if int(state["stage"][1]) < 6:
        return deny("production_code", "STAGE_NOT_REACHED",
                    f"G2, G3 and G4 are valid but the project is at {state['stage']}; run `lfe stage S6` first")
    return _decision(True, "production_code")


def decide(root: Path, request, policy=None):
    """Return a PolicyDecision (contract `lfe.policy-decision/0.1`) for an ActionRequest document."""
    issues = contracts.validate(request, expected="action")
    if issues:
        return deny("production_code", issues[0].code, "invalid ActionRequest: " + "; ".join(map(str, issues)))
    try:
        policy = load_policy(root) if policy is None else policy
    except LfeError as exc:
        return deny("production_code", exc.code, f"the project policy is invalid, so every write is denied: {exc}")
    classes = set()
    for target in request["targets"]:
        spellings = project_paths(root, target)
        if spellings is None:
            return deny("production_code", "UNSAFE_PATH", f"{target!r} resolves outside the project")
        classes.update(classify_path(rel, policy) for rel in spellings)
    if request.get("command"):
        classes.add(classify_command(request["command"], policy, root))
    cls = _most_restrictive(classes)
    if request["actor"] == "human":
        return _decision(True, cls, message="the policy restricts the agent; people act through their own channel")
    if cls in ALLOWED_CLASSES:
        return _decision(True, cls)
    if cls in ALWAYS_DENIED:
        code, message = ALWAYS_DENIED[cls]
        return deny(cls, code, message)
    return _production_check(root)


def check(root: Path, tool, targets=(), command=None, actor="agent", policy=None):
    """Decide for raw host input: targets may be absolute; they are made project-relative first."""
    relative = []
    for target in targets:
        spellings = project_paths(root, target)
        if spellings is None:
            return deny("production_code", "UNSAFE_PATH", f"{target!r} resolves outside the project")
        relative.append(spellings[0])  # decide() re-resolves symlinks itself
    request = {"schemaVersion": "lfe.action/0.1", "actor": actor, "tool": tool, "targets": relative,
               "command": command}
    return decide(root, request, policy)
