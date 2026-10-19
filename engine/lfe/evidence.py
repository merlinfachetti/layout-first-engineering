"""Evidence receipts, report verification and traceability (RFC-0001, 8.6, E-01..E-05, R-04, D-06).

`run` executes a test command without a shell and writes an `EvidenceReceipt` whose status is
derived from the exit code and the runner's own summary, never from what the caller claims.
`verify_report` recomputes every artifact hash; `trace` checks that each implemented requirement
has a clean, passing receipt from a test that the registered RequirementSet says covers it.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import contracts, workspace
from .workspace import LfeError

EVIDENCE_DIR = Path(".lfe") / "evidence"
PRODUCER = "lfe-run/0.1"
DEFAULT_TIMEOUT = 600
LIMITATION = "ambiente local; não representa produção"
TEST_ID_RE = re.compile(r"^TEST-[0-9]{3,}$")
REQ_ID_RE = re.compile(r"^(FR|NFR|SEC|UX)-[0-9]{3,}$")
RECEIPT_RE = re.compile(r"^EVID-([0-9]{3,})\.json$")

# unittest's closing summary: "Ran 3 tests in 0.01s" then "OK", "OK (skipped=1)" or
# "FAILED (failures=1, errors=2, skipped=1)". Python 3.12+ prints "NO TESTS RAN" for zero tests.
RAN_RE = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
RESULT_RE = re.compile(r"^(OK|FAILED|NO TESTS RAN)(?: \(([^)]*)\))?\s*$", re.MULTILINE)


def redact(text):
    """E-05: mask anything that looks like a credential before it is written to disk."""
    for pattern in contracts.SECRET_PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]" if m.lastindex else "[REDACTED]", text)
    return text


def parse_unittest(output):
    """Return {run, skipped, failures, errors, found} from unittest's summary (last one wins)."""
    summary = {"run": 0, "skipped": 0, "failures": 0, "errors": 0, "found": False}
    runs = RAN_RE.findall(output)
    if runs:
        summary.update(run=int(runs[-1]), found=True)
    results = RESULT_RE.findall(output)
    if results:
        _, details = results[-1]
        for part in filter(None, (p.strip() for p in details.split(","))):
            key, _, value = part.partition("=")
            if key in ("skipped", "failures", "errors") and value.isdigit():
                summary[key] = int(value)
    return summary


def classify(exit_code, summary):
    """E-01/E-02: derive (status, reason) from what actually happened."""
    if exit_code == 126:
        return "blocked", "permission_denied"
    if summary["found"] and summary["run"] == 0:
        return "fail", "no_tests_ran"
    if exit_code != 0 or summary["failures"] or summary["errors"]:
        if summary["failures"] or summary["errors"]:
            return "fail", f"tests_failed:failures={summary['failures']},errors={summary['errors']}"
        return "fail", f"exit_code:{exit_code}"
    if summary["run"] == 0:
        return "fail", "no_test_summary"
    if summary["skipped"]:
        return "skipped", f"tests_skipped:{summary['skipped']}"
    return "pass", None


def source_revision(root: Path):
    """`{git, dirty}` for the project directory. `.lfe/` is excluded: receipts and state are
    outputs of the core, not source. Without git nothing proves the source is clean, so the
    receipt is marked dirty and cannot satisfy D-06 (E-03)."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    try:
        head = git("rev-parse", "HEAD")
        if head.returncode != 0:
            return {"git": None, "dirty": True}
        status = git("status", "--porcelain", "--", ".", ":(exclude).lfe")
    except (OSError, subprocess.SubprocessError):
        return {"git": None, "dirty": True}
    return {"git": head.stdout.strip(), "dirty": status.returncode != 0 or bool(status.stdout.strip())}


def _environment(tools):
    """Allow-listed environment only (8.6): never arbitrary environment variables."""
    return {"os": platform.system(), "osRelease": platform.release(),
            "python": platform.python_version(), "tools": tools}


def _check_requires(requires):
    """Return (tools, missing_name). `python:<module>` is looked up in this interpreter;
    anything else is an executable on PATH."""
    tools = {}
    for item in requires:
        if item.startswith("python:"):
            module = item[len("python:"):]
            try:
                found = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError):
                found = False
            if not found:
                return tools, module
            try:
                tools[module] = importlib.metadata.version(module)
            except importlib.metadata.PackageNotFoundError:
                tools[module] = "present"
        else:
            if shutil.which(item) is None:
                return tools, item
            tools[item] = "present"
    return tools, None


def _executable_problem(argv0, cwd: Path):
    """(status, reason) when the program cannot be started, else None."""
    if os.sep in argv0 or (os.altsep and os.altsep in argv0):
        path = Path(argv0) if Path(argv0).is_absolute() else cwd / argv0
        if not path.exists():
            return "not_executed", f"tool_unavailable:{Path(argv0).name}"
        if not os.access(path, os.X_OK):
            return "blocked", "permission_denied"
        return None
    if shutil.which(argv0) is None:
        return "not_executed", f"tool_unavailable:{argv0}"
    return None


def receipt_paths(root: Path):
    folder = root / EVIDENCE_DIR
    if not folder.is_dir():
        return []
    return sorted((p for p in folder.iterdir() if RECEIPT_RE.match(p.name)),
                  key=lambda p: int(RECEIPT_RE.match(p.name).group(1)))


def _next_id(root: Path):
    numbers = [int(RECEIPT_RE.match(p.name).group(1)) for p in receipt_paths(root)]
    folder = root / EVIDENCE_DIR
    if folder.is_dir():
        numbers += [int(p.name[5:]) for p in folder.iterdir()
                    if p.is_dir() and re.match(r"^EVID-[0-9]{3,}$", p.name)]
    return f"EVID-{max(numbers, default=0) + 1:03d}"


def run(root: Path, test_id, argv, requirement_ids=(), requires=(), timeout=DEFAULT_TIMEOUT, cwd="."):
    """Execute `argv` without a shell and record an EvidenceReceipt. Returns the receipt."""
    root = Path(root)
    workspace.load_state(root)  # refuse outside an initialized project
    argv, requirement_ids, requires = list(argv), list(requirement_ids), list(requires)
    if not argv:
        raise LfeError("USAGE", "nothing to run; pass the command after `--`", 2)
    if not TEST_ID_RE.match(test_id):
        raise LfeError("USAGE", f"{test_id!r} is not a TEST-### id", 2)
    for req in requirement_ids:
        if not REQ_ID_RE.match(req):
            raise LfeError("USAGE", f"{req!r} is not a FR/NFR/SEC/UX-### id", 2)
    for i, arg in enumerate(argv):
        if any(p.search(arg) for p in contracts.SECRET_PATTERNS):
            raise LfeError("SECRET_IN_ARGV", f"argument {i} looks like a credential; pass secrets through "
                                             "the environment, never on the command line (E-05)", 6)
    workdir = workspace.resolve(root, cwd)
    if not workdir.is_dir():
        raise LfeError("USAGE", f"{cwd} is not a directory", 2)

    receipt_id = _next_id(root)
    tools, missing = _check_requires(requires)
    receipt = {
        "schemaVersion": "lfe.evidence/0.1", "id": receipt_id, "testId": test_id,
        "requirementIds": requirement_ids, "argv": argv, "cwd": cwd,
        "environment": _environment(tools), "sourceRevision": source_revision(root),
        "startedAt": workspace.now(), "durationMs": 0, "exitCode": None,
        "testsRun": 0, "testsSkipped": 0, "status": "not_executed",
        "artifacts": [], "limitations": [LIMITATION], "producer": PRODUCER,
    }
    if receipt["sourceRevision"]["git"] is None:
        receipt["limitations"].append("revisão de código desconhecida (sem git); não satisfaz D-06")

    problem = ("not_executed", f"tool_unavailable:{missing}") if missing else _executable_problem(argv[0], workdir)
    if problem:
        receipt["status"], receipt["reason"] = problem
        return _save(root, receipt)

    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(argv, cwd=workdir, stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=timeout, shell=False)
        exit_code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out, exit_code, out, err = True, None, exc.stdout or b"", exc.stderr or b""
    except FileNotFoundError:
        receipt["status"], receipt["reason"] = "not_executed", f"tool_unavailable:{Path(argv[0]).name}"
        return _save(root, receipt)
    except PermissionError:
        receipt["status"], receipt["reason"] = "blocked", "permission_denied"
        return _save(root, receipt)
    receipt["durationMs"] = int((time.monotonic() - started) * 1000)
    receipt["exitCode"] = exit_code

    stdout = redact(out.decode("utf-8", errors="replace"))
    stderr = redact(err.decode("utf-8", errors="replace"))
    folder = root / EVIDENCE_DIR / receipt_id
    folder.mkdir(parents=True, exist_ok=False)
    for name, text in (("stdout.txt", stdout), ("stderr.txt", stderr)):
        (folder / name).write_text(text, encoding="utf-8")
        rel = (EVIDENCE_DIR / receipt_id / name).as_posix()
        receipt["artifacts"].append({"path": rel, "sha256": workspace.file_digest(folder / name)})

    summary = parse_unittest(stderr + "\n" + stdout)
    receipt["testsRun"], receipt["testsSkipped"] = summary["run"], summary["skipped"]
    if timed_out:
        status, reason = "fail", f"timeout:{timeout}s"
    else:
        status, reason = classify(exit_code, summary)
    receipt["status"] = status
    if reason:
        receipt["reason"] = reason
    return _save(root, receipt)


def _save(root: Path, receipt):
    issues = contracts.validate(receipt, expected="evidence")
    if issues:
        raise LfeError(issues[0].code, "; ".join(map(str, issues)), 1)
    workspace.write_json_atomic(root / EVIDENCE_DIR / f"{receipt['id']}.json", receipt)
    return receipt


def receipt_problems(root: Path, path: Path):
    """Return (receipt or None, problems) after re-validating a receipt and every artifact (E-04).

    Besides the hashes, the recorded counts and status must follow from the stored output: a
    receipt edited from `fail` to `pass` is caught even when its logs were left untouched.
    """
    try:
        receipt = workspace.read_contract(path, "evidence")
    except LfeError as exc:
        return None, [str(exc)]
    problems = []
    if path.name != f"{receipt['id']}.json":
        problems.append(f"{path.name} holds {receipt['id']}")
    texts = {}
    for artifact in receipt["artifacts"]:
        try:
            target = workspace.resolve(root, artifact["path"])
        except LfeError as exc:
            problems.append(str(exc))
            continue
        if not target.is_file():
            problems.append(f"{artifact['path']} is missing")
        elif workspace.file_digest(target) != artifact["sha256"]:
            problems.append(f"{artifact['path']} changed after the receipt was written")
        else:
            texts[target.name] = target.read_text(encoding="utf-8")
    if not problems and {"stdout.txt", "stderr.txt"} <= texts.keys():
        summary = parse_unittest(texts["stderr.txt"] + "\n" + texts["stdout.txt"])
        if (receipt["testsRun"], receipt["testsSkipped"]) != (summary["run"], summary["skipped"]):
            problems.append("testsRun/testsSkipped do not match the stored output")
        if receipt["status"] == "pass" and classify(receipt["exitCode"], summary)[0] != "pass":
            problems.append("status pass does not follow from the stored output")
    return receipt, problems


def verify_report(root: Path):
    """E-04: recompute every receipt's artifacts. Returns the receipts; raises EVIDENCE_TAMPERED."""
    root = Path(root)
    receipts, problems = [], []
    for path in receipt_paths(root):
        receipt, found = receipt_problems(root, path)
        problems += [f"{path.name}: {p}" for p in found]
        if receipt is not None:
            receipts.append(receipt)
    if problems:
        raise LfeError("EVIDENCE_TAMPERED", "; ".join(problems), 5)
    return receipts


def _requirement_sets(root: Path, state):
    sets = []
    for art_id, art in sorted(state["artifacts"].items()):
        if art["kind"] != "requirements-set":
            continue
        digest, problems = workspace.artifact_digest(root, art["path"])
        if digest != art["sha256"] or problems:
            raise LfeError("STALE_ARTIFACT", f"{art_id} changed on disk since registration; register it again", 6)
        sets.append(workspace.read_contract(workspace.resolve(root, art["path"]), "requirements"))
    if not sets:
        raise LfeError("NO_REQUIREMENTS", "no requirements-set artifact is registered; run `lfe artifact` first", 6)
    return sets


def trace(root: Path):
    """R-04/AC-08: map each requirement to its covering tests and clean passing receipts.

    Coverage comes from the registered RequirementSet (`items[].testRefs` and `tests[].covers`),
    never from the receipt's own `requirementIds`. Only intact `pass` receipts with
    `sourceRevision.dirty = false` count (E-03).
    """
    root = Path(root)
    state = workspace.load_state(root)
    receipts = []
    for path in receipt_paths(root):
        receipt, problems = receipt_problems(root, path)
        if receipt is not None and not problems:
            receipts.append(receipt)
    rows = []
    for req_set in _requirement_sets(root, state):
        for item in req_set["items"]:
            tests = sorted(set(item["testRefs"]) | {t["id"] for t in req_set["tests"] if item["id"] in t["covers"]})
            covering = [r for r in receipts if r["testId"] in tests]
            passing = [r["id"] for r in covering if r["status"] == "pass" and not r["sourceRevision"]["dirty"]]
            needed = item["status"] in ("implemented", "verified")
            row = {"scope": req_set["id"], "id": item["id"], "status": item["status"], "tests": tests,
                   "receipts": [r["id"] for r in covering], "passing": passing, "ok": bool(passing) or not needed}
            if not row["ok"]:
                dirty = [r["id"] for r in covering if r["status"] == "pass"]
                row["missing"] = (f"only dirty passing receipts ({', '.join(dirty)})" if dirty
                                  else "no passing receipt from a covering test")
            rows.append(row)
    return {"complete": all(r["ok"] for r in rows), "requirements": rows}


def require_complete(root: Path):
    """D-06: approving G5 needs a complete trace; anything less is EVIDENCE_INCOMPLETE."""
    try:
        report = trace(root)
    except LfeError as exc:
        raise LfeError("EVIDENCE_INCOMPLETE", f"G5 needs traceable evidence: {exc}", 3) from None
    missing = [f"{r['id']} ({r['missing']})" for r in report["requirements"] if not r["ok"]]
    if missing:
        raise LfeError("EVIDENCE_INCOMPLETE", "G5 needs a clean passing receipt for: " + "; ".join(missing), 3)
    return report
