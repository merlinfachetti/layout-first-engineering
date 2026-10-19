"""TEST-001 (SEC-001) and TEST-002 (NFR-001): engine rules applied to this example project."""
from pathlib import Path
import shutil
import tempfile
import unittest

from . import _engine

_engine.load()
from lfe import contracts, ledger, policy, workspace  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]


class Sec001ProductionLock(unittest.TestCase):
    """TEST-001 · SEC-001: writing app/ is denied while G2, G3 or G4 is not valid."""

    def test_app_write_denied_without_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "p"
            shutil.copytree(PROJECT, copy, ignore=shutil.ignore_patterns("__pycache__"))
            # A fresh ledger: no gate has a human decision.
            (copy / workspace.LEDGER_FILE).write_text("", encoding="utf-8")
            state = workspace.load_state(copy)
            state["mode"] = "project"
            state["stage"] = "S1"
            state["gatesCache"] = {g: {"status": "not_started", "decisionId": None} for g in workspace.GATES}
            workspace.save_state(copy, state)
            decision = policy.check(copy, "Write", targets=["app/app.js"])
            self.assertFalse(decision["allowed"])
            self.assertIn(decision["reasonCode"], ("GATE_NOT_APPROVED", "STAGE_NOT_REACHED"))

    def test_human_approval_command_denied_to_agent(self):
        decision = policy.check(PROJECT, "Bash", command="python3 -m lfe approve G2")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reasonCode"], "HUMAN_CHANNEL_REQUIRED")


class Nfr001ValidArtifacts(unittest.TestCase):
    """TEST-002 · NFR-001: every artifact of this project is valid, hashed and inside the project."""

    def test_state_and_ledger(self):
        self.assertEqual(contracts.validate_file(PROJECT / workspace.STATE_FILE, expected="state"), [])
        ledger.read(PROJECT)

    def test_registered_artifacts_match_their_hashes(self):
        state = workspace.load_state(PROJECT)
        self.assertTrue(state["artifacts"])
        for art_id, art in state["artifacts"].items():
            with self.subTest(artifact=art_id):
                digest, problems = workspace.artifact_digest(PROJECT, art["path"])
                self.assertEqual(problems, [])
                self.assertEqual(digest, art["sha256"])

    def test_contract_documents(self):
        for rel, kind in ((".lfe/requirements.json", "requirements"),
                          (".lfe/baselines/DESIGN-001.json", "baseline")):
            with self.subTest(file=rel):
                self.assertEqual(contracts.validate_file(PROJECT / rel, expected=kind), [])


if __name__ == "__main__":
    unittest.main()
