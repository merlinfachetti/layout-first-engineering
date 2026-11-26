"""`lfe gate G5` on Lighthouse and axe JSON (issue #31)."""
from pathlib import Path
import contextlib
import io
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import evidence, quality  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402


def lighthouse(perf=0.95, a11y=1.0, lcp=1800, cls=0.02, tbt=90):
    return {"finalDisplayedUrl": "https://example.test/", "configSettings": {"formFactor": "mobile"},
            "categories": {"performance": {"score": perf}, "accessibility": {"score": a11y},
                           "best-practices": {"score": 1.0}, "seo": {"score": 0.92}},
            "audits": {"largest-contentful-paint": {"numericValue": lcp},
                       "cumulative-layout-shift": {"numericValue": cls}, "total-blocking-time": {"numericValue": tbt}}}


def axe(*impacts):
    return {"url": "https://example.test/",
            "violations": [{"id": f"rule-{i}", "impact": impact, "nodes": [{}]} for i, impact in enumerate(impacts)]}


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli(list(argv))
    return code, out.getvalue()


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, doc):
        (self.root / name).write_text(json.dumps(doc), encoding="utf-8")
        return name

    def test_passing_reports(self):
        code, out = run("--root", self.tmp.name, "gate", "G5", "--lighthouse", self.write("lh.json", lighthouse()),
                        "--axe", self.write("axe.json", axe("minor")))
        self.assertEqual(code, 0, out)
        summary = evidence.parse_unittest(out)
        self.assertEqual((summary["run"], summary["failures"]), (9, 0))

    def test_failures_are_reported_and_counted(self):
        code, out = run("--root", self.tmp.name, "gate", "G5",
                        "--lighthouse", self.write("lh.json", lighthouse(perf=0.71, lcp=4100)),
                        "--axe", self.write("axe.json", axe("serious", "critical")))
        self.assertEqual(code, 3)
        self.assertIn("FAIL lighthouse performance", out)
        self.assertIn("rule-0", out)
        self.assertEqual(evidence.parse_unittest(out)["failures"], 4)

    def test_budget_override(self):
        (self.root / ".lfe").mkdir()
        (self.root / ".lfe/budget.json").write_text(json.dumps({"lighthouse": {"categories": {"performance": 0.7}}}))
        result = quality.evaluate(self.root, [self.write("lh.json", lighthouse(perf=0.71))])
        self.assertTrue(result["passed"])
        self.assertEqual(result["budget"]["lighthouse"]["categories"]["accessibility"], 0.95)

    def test_wrong_files_are_refused(self):
        with self.assertRaises(LfeError) as ctx:
            quality.evaluate(self.root, [self.write("x.json", {"violations": []})])
        self.assertEqual(ctx.exception.code, "BAD_REPORT")
        with self.assertRaises(LfeError) as ctx:
            quality.evaluate(self.root)
        self.assertEqual(ctx.exception.code, "NO_REPORTS")

    def test_axe_cli_array_form(self):
        result = quality.evaluate(self.root, axe=[self.write("a.json", [axe(), axe("minor")])])
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["checks"]), 4)


if __name__ == "__main__":
    unittest.main()
