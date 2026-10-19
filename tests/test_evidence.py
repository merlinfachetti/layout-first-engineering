"""Evidence receipts, report verification and traceability (RFC-0001, 8.6, E-01..E-05, R-04, D-06;
RFC-0002, AC-06, AC-07, AC-08, AC-12). Offline, real files, real subprocesses.

Each test builds a small project in a temporary directory whose `tests/` folder holds a tiny but
real unittest suite; `lfe run` executes it through the same interpreter that runs these tests.
"""
from pathlib import Path
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import contracts, decisions, evidence, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402

PY = sys.executable
UNITTEST = [PY, "-m", "unittest", "discover", "-s"]

SUITE_PASS = """import unittest
class Lista(unittest.TestCase):
    def test_adiciona(self):
        self.assertEqual([1] + [2], [1, 2])
    def test_titulo(self):
        self.assertTrue("Duna".strip())
"""
SUITE_FAIL = """import unittest
class Lista(unittest.TestCase):
    def test_ok(self):
        pass
    def test_quebra(self):
        self.assertEqual(1, 2)
"""
SUITE_SKIP = """import unittest
class Lista(unittest.TestCase):
    def test_ok(self):
        pass
    @unittest.skip("sem navegador")
    def test_e2e(self):
        pass
"""
SUITE_SECRET = """import unittest
class Lista(unittest.TestCase):
    def test_vaza(self):
        print("conectando com token=abc123XYZ e ghp_" + "a" * 36)
"""


def write(path: Path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc, indent=2), encoding="utf-8")


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=Teste", "-c", "user.email=teste@example.invalid",
                    "-c", "commit.gpgsign=false", *args], cwd=root, check=True, capture_output=True)


class Project:
    """An initialized project with a requirements set and real unittest suites on disk."""

    def __init__(self, tmp, use_git=True, status="implemented"):
        self.root = Path(tmp)
        workspace.init(self.root, "teste", "Projeto de teste")
        write(self.root / "suites/passing/test_lista.py", SUITE_PASS)
        write(self.root / "suites/failing/test_lista.py", SUITE_FAIL)
        write(self.root / "suites/skipping/test_lista.py", SUITE_SKIP)
        write(self.root / "suites/secret/test_lista.py", SUITE_SECRET)
        (self.root / "suites/empty").mkdir(parents=True)
        write(self.root / ".gitignore", "__pycache__/\n")
        write(self.root / ".lfe/requirements.json", {
            "schemaVersion": "lfe.requirements/0.1", "id": "SCOPE-001", "revision": 1,
            "items": [
                {"id": "FR-001", "title": "Adicionar", "acceptance": [{"given": "a", "when": "b", "then": "c"}],
                 "priority": "must", "uiRefs": [], "testRefs": ["TEST-001"], "status": status},
                {"id": "FR-002", "title": "Persistir", "acceptance": [{"given": "a", "when": "b", "then": "c"}],
                 "priority": "should", "uiRefs": [], "testRefs": [], "status": "approved"}],
            "tests": [{"id": "TEST-001", "kind": "unit", "covers": ["FR-001"]},
                      {"id": "TEST-002", "kind": "unit", "covers": ["FR-002"]}]})
        self.register("SCOPE-001", "requirements-set", ".lfe/requirements.json")
        if use_git:
            git(self.root, "init", "-q")
            git(self.root, "add", "-A")
            git(self.root, "commit", "-q", "-m", "inicial")

    def register(self, art_id, kind, rel):
        state = workspace.load_state(self.root)
        workspace.register_artifact(self.root, state, art_id, kind, rel)
        workspace.save_state(self.root, state)

    def run(self, suite, test_id="TEST-001", **kw):
        return evidence.run(self.root, test_id, UNITTEST + [f"suites/{suite}"], **kw)

    def receipt(self, receipt_id):
        return json.loads((self.root / f".lfe/evidence/{receipt_id}.json").read_text(encoding="utf-8"))


def quiet_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli(list(argv))
    return code, out.getvalue(), err.getvalue()


class RunStatusTests(unittest.TestCase):
    """E-01 and E-02: the status follows from what happened, not from the exit code alone."""

    def test_real_suite_passes_with_valid_receipt_and_clean_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            receipt = p.run("passing", requirement_ids=["FR-001"])
            self.assertEqual(receipt["status"], "pass")
            self.assertEqual((receipt["testsRun"], receipt["testsSkipped"], receipt["exitCode"]), (2, 0, 0))
            self.assertEqual(receipt["id"], "EVID-001")
            self.assertNotIn("reason", receipt)
            self.assertRegex(receipt["sourceRevision"]["git"], r"^[0-9a-f]{40}$")
            self.assertFalse(receipt["sourceRevision"]["dirty"])
            self.assertEqual(contracts.validate(p.receipt("EVID-001"), expected="evidence"), [])
            for artifact in receipt["artifacts"]:
                self.assertTrue(artifact["path"].startswith(".lfe/evidence/EVID-001/"))
                self.assertEqual(workspace.file_digest(p.root / artifact["path"]), artifact["sha256"])

    def test_exit_zero_with_zero_tests_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Project(tmp).run("empty")
            self.assertEqual(receipt["status"], "fail")
            self.assertEqual(receipt["testsRun"], 0)
            self.assertEqual(receipt["reason"], "no_tests_ran")

    def test_skipped_tests_never_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Project(tmp).run("skipping")
            self.assertEqual(receipt["exitCode"], 0)
            self.assertNotEqual(receipt["status"], "pass")
            self.assertEqual((receipt["testsRun"], receipt["testsSkipped"]), (2, 1))

    def test_failing_suite_is_fail_with_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Project(tmp).run("failing")
            self.assertEqual(receipt["status"], "fail")
            self.assertEqual(receipt["exitCode"], 1)
            self.assertEqual(receipt["reason"], "tests_failed:failures=1,errors=0")

    def test_missing_executable_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            receipt = evidence.run(p.root, "TEST-003", ["lfe-ferramenta-inexistente", "--versao"])
            self.assertEqual(receipt["status"], "not_executed")
            self.assertEqual(receipt["reason"], "tool_unavailable:lfe-ferramenta-inexistente")
            self.assertIsNone(receipt["exitCode"])
            self.assertEqual(receipt["artifacts"], [])

    def test_missing_requirement_is_not_executed_and_nothing_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            marker = p.root / "rodou.txt"
            argv = [PY, "-c", f"open({str(marker)!r}, 'w').write('x')"]
            receipt = evidence.run(p.root, "TEST-003", argv, requires=["python:lfe_modulo_inexistente"])
            self.assertEqual((receipt["status"], receipt["reason"]), ("not_executed", "tool_unavailable:lfe_modulo_inexistente"))
            receipt = evidence.run(p.root, "TEST-003", argv, requires=["lfe-binario-inexistente"])
            self.assertEqual(receipt["reason"], "tool_unavailable:lfe-binario-inexistente")
            self.assertFalse(marker.exists())

    def test_present_requirement_records_tool_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Project(tmp).run("passing", requires=["python:unittest", Path(PY).name])
            self.assertEqual(receipt["status"], "pass")
            self.assertIn("unittest", receipt["environment"]["tools"])
            self.assertEqual(set(receipt["environment"]), {"os", "osRelease", "python", "tools"})

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_permission_denied_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            write(p.root / "roda.sh", "#!/bin/sh\necho oi\n")
            os.chmod(p.root / "roda.sh", 0o644)
            receipt = evidence.run(p.root, "TEST-003", ["./roda.sh"])
            self.assertEqual((receipt["status"], receipt["reason"]), ("blocked", "permission_denied"))
            receipt = evidence.run(p.root, "TEST-003", [PY, "-c", "raise SystemExit(126)"])
            self.assertEqual((receipt["status"], receipt["reason"]), ("blocked", "permission_denied"))

    def test_timeout_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            receipt = evidence.run(p.root, "TEST-003", [PY, "-c", "import time; time.sleep(30)"], timeout=1)
            self.assertEqual((receipt["status"], receipt["reason"]), ("fail", "timeout:1s"))
            self.assertIsNone(receipt["exitCode"])

    def test_without_git_the_receipt_is_dirty(self):
        with tempfile.TemporaryDirectory() as tmp:
            if shutil.which("git"):
                # make sure no enclosing repository is picked up
                os.environ["GIT_CEILING_DIRECTORIES"] = str(Path(tmp).resolve().parent)
            try:
                receipt = Project(tmp, use_git=False).run("passing")
            finally:
                os.environ.pop("GIT_CEILING_DIRECTORIES", None)
            self.assertEqual(receipt["sourceRevision"], {"git": None, "dirty": True})
            self.assertTrue(any("D-06" in item for item in receipt["limitations"]))

    def test_uncommitted_source_marks_receipt_dirty_but_lfe_outputs_do_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.run("passing")
            self.assertFalse(p.run("passing")["sourceRevision"]["dirty"])  # .lfe/ is excluded
            write(p.root / "suites/passing/test_lista.py", SUITE_PASS + "\n# edição\n")
            self.assertTrue(p.run("passing")["sourceRevision"]["dirty"])


class SecretTests(unittest.TestCase):
    """E-05."""

    def test_secret_in_argv_is_refused_before_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            marker = p.root / "rodou.txt"
            argv = [PY, "-c", f"open({str(marker)!r}, 'w')", "api_key=abc123"]
            with self.assertRaises(LfeError) as ctx:
                evidence.run(p.root, "TEST-001", argv)
            self.assertEqual(ctx.exception.code, "SECRET_IN_ARGV")
            self.assertFalse(marker.exists())
            self.assertEqual(evidence.receipt_paths(p.root), [])

    def test_secrets_in_output_are_redacted_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            receipt = p.run("secret")
            stdout = (p.root / receipt["artifacts"][0]["path"]).read_text(encoding="utf-8")
            self.assertIn("token=[REDACTED]", stdout)
            self.assertNotIn("abc123XYZ", stdout)
            self.assertNotIn("ghp_aaaa", stdout)
            self.assertEqual(receipt["status"], "pass")


class VerifyReportTests(unittest.TestCase):
    """E-04 and AC-12."""

    def test_intact_report_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.run("passing")
            p.run("failing")
            self.assertEqual([r["id"] for r in evidence.verify_report(p.root)], ["EVID-001", "EVID-002"])

    def test_edited_artifact_is_evidence_tampered_exit_5(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            receipt = p.run("failing")
            log = p.root / receipt["artifacts"][1]["path"]
            log.write_text(log.read_text(encoding="utf-8").replace("FAILED", "OK"), encoding="utf-8")
            with self.assertRaises(LfeError) as ctx:
                evidence.verify_report(p.root)
            self.assertEqual((ctx.exception.code, ctx.exception.exit_code), ("EVIDENCE_TAMPERED", 5))
            code, _, err = quiet_cli("--root", str(p.root), "verify-report")
            self.assertEqual(code, 5)
            self.assertIn("EVIDENCE_TAMPERED", err)

    def test_receipt_upgraded_to_pass_by_hand_is_tampered(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.run("failing")
            path = p.root / ".lfe/evidence/EVID-001.json"
            forged = p.receipt("EVID-001")
            forged.update(status="pass", exitCode=0)
            forged.pop("reason")
            write(path, forged)
            with self.assertRaises(LfeError) as ctx:
                evidence.verify_report(p.root)
            self.assertEqual(ctx.exception.code, "EVIDENCE_TAMPERED")
            self.assertFalse(evidence.trace(p.root)["complete"])


class TraceTests(unittest.TestCase):
    """R-04 and AC-08."""

    def test_trace_incomplete_without_passing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.run("failing")
            report = evidence.trace(p.root)
            self.assertFalse(report["complete"])
            row = next(r for r in report["requirements"] if r["id"] == "FR-001")
            self.assertEqual(row["receipts"], ["EVID-001"])
            self.assertEqual(row["missing"], "no passing receipt from a covering test")
            code, out, _ = quiet_cli("--root", str(p.root), "trace", "--check")
            self.assertEqual(code, 6)
            self.assertIn("MISS FR-001", out)

    def test_trace_complete_with_clean_passing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.run("passing")
            report = evidence.trace(p.root)
            self.assertTrue(report["complete"])
            row = next(r for r in report["requirements"] if r["id"] == "FR-001")
            self.assertEqual((row["tests"], row["passing"]), (["TEST-001"], ["EVID-001"]))
            code, out, _ = quiet_cli("--root", str(p.root), "trace", "--check")
            self.assertEqual(code, 0)
            self.assertIn("trace: complete", out)

    def test_only_tests_declared_as_covering_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp, status="verified")
            # TEST-002 covers FR-002 only; the receipt claiming FR-001 does not change that
            p.run("passing", test_id="TEST-002", requirement_ids=["FR-001"])
            self.assertFalse(evidence.trace(p.root)["complete"])

    def test_dirty_receipt_does_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            write(p.root / "suites/passing/novo.txt", "não commitado")
            receipt = p.run("passing")
            self.assertEqual((receipt["status"], receipt["sourceRevision"]["dirty"]), ("pass", True))
            report = evidence.trace(p.root)
            self.assertFalse(report["complete"])
            self.assertIn("only dirty passing receipts", report["requirements"][0]["missing"])

    def test_trace_without_requirements_set_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace.init(Path(tmp), "vazio", "Vazio")
            with self.assertRaises(LfeError) as ctx:
                evidence.trace(Path(tmp))
            self.assertEqual(ctx.exception.code, "NO_REQUIREMENTS")


class G5EvidenceTests(unittest.TestCase):
    """D-06 in `decisions.decide` and AC-07."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.p = Project(self._tmp.name)
        write(self.p.root / ".lfe/release/RC-001.json", {"candidate": "v0.1.0"})
        self.p.register("RC-001", "release-candidate", ".lfe/release/RC-001.json")
        decisions.propose(self.p.root, "G5", ["RC-001"])

    def tearDown(self):
        self._tmp.cleanup()

    def approve_g5(self):
        return decisions.decide(self.p.root, "G5", "approved", interactive=True, ask=lambda _: "G5",
                                out=lambda *_: None, actor="Pessoa")

    def test_g5_blocked_without_evidence(self):
        evidence.run(self.p.root, "TEST-001", ["lfe-playwright-ausente"])  # not_executed
        with self.assertRaises(LfeError) as ctx:
            self.approve_g5()
        self.assertEqual(ctx.exception.code, "EVIDENCE_INCOMPLETE")
        self.assertIn("FR-001", str(ctx.exception))
        self.assertEqual((self.p.root / ".lfe/decisions.jsonl").read_text(encoding="utf-8").count("\n"), 1)

    def test_g5_allowed_with_clean_passing_evidence(self):
        self.p.run("passing")
        entry = self.approve_g5()
        self.assertEqual((entry["gate"], entry["verdict"]), ("G5", "approved"))

    def test_g5_rejection_does_not_need_evidence(self):
        entry = decisions.decide(self.p.root, "G5", "rejected", interactive=True, ask=lambda _: "G5",
                                 out=lambda *_: None, actor="Pessoa")
        self.assertEqual(entry["verdict"], "rejected")


class CliTests(unittest.TestCase):
    def test_run_through_cli_after_double_dash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            code, out, _ = quiet_cli("--root", str(p.root), "run", "TEST-001", "--req", "FR-001",
                                     "--timeout", "60", "--", *UNITTEST, "suites/passing")
            self.assertEqual(code, 0)
            self.assertIn("EVID-001 TEST-001 pass (ran 2, skipped 0, exit 0)", out)
            self.assertEqual(p.receipt("EVID-001")["requirementIds"], ["FR-001"])
            self.assertEqual(p.receipt("EVID-001")["argv"][0], PY)

    def test_cli_refuses_secret_with_exit_6(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            code, _, err = quiet_cli("--root", str(p.root), "run", "TEST-001", "--", "echo", "password=hunter2")
            self.assertEqual(code, 6)
            self.assertIn("SECRET_IN_ARGV", err)
            self.assertNotIn("hunter2", err)


if __name__ == "__main__":
    unittest.main()
