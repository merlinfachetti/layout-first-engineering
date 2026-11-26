"""Automated quality checks for G5 (issue #31): Lighthouse and axe-core JSON against a budget.

Reads the reports the tools already write (no network, no browser here) and compares them with a
budget. The result prints a unittest-style summary, so `lfe run TEST-### --req NFR-### -- lfe gate
G5 ...` turns it into an ordinary evidence receipt that `lfe trace` and `lfe approve G5` see.
"""
from __future__ import annotations

import json
from pathlib import Path

from .workspace import LfeError

DEFAULT_BUDGET = {
    "lighthouse": {
        "categories": {"performance": 0.9, "accessibility": 0.95, "best-practices": 0.9, "seo": 0.9},
        "audits": {"largest-contentful-paint": 2500, "cumulative-layout-shift": 0.1, "total-blocking-time": 200},
    },
    "axe": {"maxViolations": {"critical": 0, "serious": 0}},
}
BUDGET_FILE = Path(".lfe") / "budget.json"


def load_json(path: Path, what):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LfeError("MISSING_FILE", f"{what} {path} does not exist", 2) from None
    except json.JSONDecodeError as exc:
        raise LfeError("BAD_REPORT", f"{what} {path} is not JSON ({exc.msg})", 6) from None


def load_budget(root: Path, explicit=None):
    budget = json.loads(json.dumps(DEFAULT_BUDGET))
    path = Path(explicit) if explicit else root / BUDGET_FILE
    if explicit and not path.is_absolute():
        path = root / path
    if path.is_file():
        custom = load_json(path, "budget")
        for section in ("lighthouse", "axe"):
            for key, value in (custom.get(section) or {}).items():
                if isinstance(value, dict):
                    budget[section].setdefault(key, {}).update(value)
                else:
                    budget[section][key] = value
    return budget


def lighthouse_checks(report, budget, label):
    if not isinstance(report, dict) or "categories" not in report:
        raise LfeError("BAD_REPORT", f"{label} is not a Lighthouse JSON report (no categories)", 6)
    checks = []
    url = report.get("finalDisplayedUrl") or report.get("finalUrl") or report.get("requestedUrl") or label
    form = (report.get("configSettings") or {}).get("formFactor", "")
    where = f"{url}{f' [{form}]' if form else ''}"
    for category, minimum in budget["lighthouse"]["categories"].items():
        score = (report["categories"].get(category) or {}).get("score")
        ok = isinstance(score, (int, float)) and score >= minimum
        shown = "missing" if score is None else f"{round(score * 100)}"
        checks.append({"check": f"lighthouse {category}", "where": where, "value": shown,
                       "limit": f">= {round(minimum * 100)}", "ok": ok})
    for audit, maximum in budget["lighthouse"]["audits"].items():
        value = ((report.get("audits") or {}).get(audit) or {}).get("numericValue")
        ok = isinstance(value, (int, float)) and value <= maximum
        unit = "" if audit == "cumulative-layout-shift" else " ms"
        shown = "missing" if value is None else (f"{value:.3f}" if not unit else f"{round(value)}{unit}")
        checks.append({"check": f"lighthouse {audit}", "where": where, "value": shown,
                       "limit": f"<= {maximum}{unit}", "ok": ok})
    return checks


def axe_checks(report, budget, label):
    # axe-core results object, the CLI's array of results, or {"violations": [...]}.
    runs = report if isinstance(report, list) else [report]
    checks = []
    for run in runs:
        if not isinstance(run, dict) or "violations" not in run:
            raise LfeError("BAD_REPORT", f"{label} is not an axe-core result (no violations)", 6)
        where = run.get("url") or label
        counts = {}
        for violation in run["violations"]:
            impact = violation.get("impact") or "unknown"
            counts[impact] = counts.get(impact, 0) + len(violation.get("nodes") or [1])
        for impact, maximum in budget["axe"]["maxViolations"].items():
            found = counts.get(impact, 0)
            ids = sorted(v.get("id", "?") for v in run["violations"] if v.get("impact") == impact)
            checks.append({"check": f"axe {impact} violations", "where": where,
                           "value": str(found) + (f" ({', '.join(ids)})" if ids else ""),
                           "limit": f"<= {maximum}", "ok": found <= maximum})
    return checks


def evaluate(root: Path, lighthouse=(), axe=(), budget_path=None):
    if not lighthouse and not axe:
        raise LfeError("NO_REPORTS", "give at least one --lighthouse or --axe report", 2)
    budget = load_budget(root, budget_path)
    checks = []
    for item in lighthouse:
        path = Path(item) if Path(item).is_absolute() else root / item
        checks += lighthouse_checks(load_json(path, "Lighthouse report"), budget, item)
    for item in axe:
        path = Path(item) if Path(item).is_absolute() else root / item
        checks += axe_checks(load_json(path, "axe report"), budget, item)
    return {"passed": all(c["ok"] for c in checks), "checks": checks, "budget": budget}
