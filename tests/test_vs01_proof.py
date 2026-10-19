"""The VS-01 proof script runs end to end; without Playwright the E2E receipts are honest."""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None


@unittest.skipIf(shutil.which("git") is None, "git is required for clean-source receipts")
class Vs01ProofTests(unittest.TestCase):
    def test_proof_without_browser_is_incomplete_but_truthful(self):
        if HAS_PLAYWRIGHT:
            self.skipTest("Playwright installed here: the full proof runs in the vs01-proof CI job")
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "vs01"
            result = subprocess.run(["sh", str(ROOT / "scripts" / "vs01-proof.sh"), str(work)],
                                    capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 6, result.stdout[-2000:] + result.stderr[-2000:])
            report = json.loads((work / "TEST_REPORT.json").read_text(encoding="utf-8"))
            status = {r["testId"]: r for r in report["receipts"]}
            self.assertEqual(status["TEST-001"]["status"], "pass")
            self.assertEqual(status["TEST-002"]["status"], "pass")
            for test_id in ("TEST-003", "TEST-004", "TEST-005"):
                self.assertEqual(status[test_id]["status"], "not_executed")
                self.assertEqual(status[test_id]["reason"], "tool_unavailable:playwright")
            self.assertFalse(report["trace"]["complete"])
            self.assertIn("SIMULATED", report["approvals"])
            self.assertTrue(all(not r["source"]["dirty"] for r in report["receipts"]))
            self.assertTrue((work / ".lfe" / "studio.html").is_file())


if __name__ == "__main__":
    unittest.main()
