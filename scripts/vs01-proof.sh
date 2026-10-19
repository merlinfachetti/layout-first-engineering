#!/bin/sh
# Reproducible end-to-end proof of the VS-01 vertical slice (RFC-0002 §8, AC-01..AC-12).
#
#   sh scripts/vs01-proof.sh [WORKDIR]
#
# 1. replays examples/vs01-leituras into WORKDIR with SIMULATED approvals (labelled as such);
# 2. snapshots it in a throwaway git repo so receipts can prove a clean source;
# 3. runs TEST-001..TEST-005 through `lfe run`, writing evidence receipts;
# 4. verifies receipts, checks traceability, writes HANDOFF.md, studio.html and TEST_REPORT.json.
# Without Playwright the E2E receipts are `not_executed` and the trace stays incomplete: by design.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORK=${1:-"$(mktemp -d)/vs01"}
export LFE_ENGINE="$REPO/engine" PYTHONDONTWRITEBYTECODE=1
lfe() { python3 "$REPO/layout-first-engineering/scripts/lfe.py" --root "$WORK" "$@"; }
g() { git -C "$WORK" -c user.name="lfe demo" -c user.email=demo@lfe.invalid -c commit.gpgsign=false "$@"; }

python3 "$REPO/layout-first-engineering/scripts/lfe.py" demo "$REPO/examples/vs01-leituras" --workdir "$WORK"
g init -q
g add -A
g commit -q -m "VS-01 demo snapshot"

lfe run TEST-001 --req SEC-001 --cwd . -- python3 -m unittest tests_unit.test_core_rules.Sec001ProductionLock
lfe run TEST-002 --req NFR-001 --cwd . -- python3 -m unittest tests_unit.test_core_rules.Nfr001ValidArtifacts
lfe run TEST-003 --req FR-001 --req FR-002 --req FR-003 --requires python:playwright --cwd . -- \
    python3 -m unittest tests_e2e.test_vs01.Test003AddPersistMark
lfe run TEST-004 --req FR-004 --req FR-005 --requires python:playwright --cwd . -- \
    python3 -m unittest tests_e2e.test_vs01.Test004Errors
lfe run TEST-005 --req UX-001 --requires python:playwright --cwd . -- \
    python3 -m unittest tests_e2e.test_vs01.Test005Keyboard

lfe verify-report
lfe handoff > /dev/null
lfe studio > /dev/null
python3 - "$WORK" "$REPO" <<'PY'
import json, subprocess, sys
from pathlib import Path
work, repo = Path(sys.argv[1]), Path(sys.argv[2])
lfe = [sys.executable, str(repo / "layout-first-engineering/scripts/lfe.py"), "--root", str(work)]
trace = json.loads(subprocess.run(lfe + ["trace", "--json"], capture_output=True, text=True).stdout)
receipts = [json.loads(p.read_text()) for p in sorted((work / ".lfe/evidence").glob("EVID-*.json"))]
head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
report = {
    "schemaVersion": "lfe.test-report/0.1",
    "slice": "VS-01 Lista de leituras",
    "lfeRepositoryCommit": head or None,
    "approvals": "SIMULATED (lfe demo) — not human decisions",
    "receipts": [{k: r[k] for k in ("id", "testId", "status", "testsRun", "testsSkipped", "durationMs")}
                 | {"reason": r.get("reason"), "source": r["sourceRevision"], "environment": r["environment"]}
                 for r in receipts],
    "trace": trace,
}
(work / "TEST_REPORT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\nTEST_REPORT.json")
for r in report["receipts"]:
    print(f"  {r['id']} {r['testId']:<9} {r['status']:<13} tests={r['testsRun']} {r['reason'] or ''}")
print(f"  trace complete: {trace['complete']}")
PY
echo "workdir: $WORK"
lfe trace --check
