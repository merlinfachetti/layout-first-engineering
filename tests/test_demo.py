"""Demo replay safety and behaviour (RFC-0002 §8, D-03, D-08)."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tests"))

from lfe import decisions, demo, handoff, ledger, workspace  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402
from test_ledger_gates import Project  # noqa: E402


def proposed_example(tmp):
    p = Project(tmp)
    p.register_all()
    decisions.propose(p.root, "G1", ["DIR-001"])
    decisions.propose(p.root, "G2", ["DESIGN-001"])
    decisions.propose(p.root, "G3", ["DESIGN-001", "SCOPE-001"])
    decisions.propose(p.root, "G4", ["SCOPE-001", "ADR-001"])
    return p


class DemoReplayTests(unittest.TestCase):
    def test_replay_approves_as_simulated_and_reaches_s6(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            p = proposed_example(src)
            work = Path(out) / "demo"
            result = demo.replay(p.root, work)
            self.assertEqual(result["approved"], ["G1", "G2", "G3", "G4"])
            self.assertEqual(result["handoff"]["stage"], "S6")
            self.assertEqual(result["handoff"]["productionCode"], "unlocked")
            decisions_ = [e for e in ledger.read(work) if e["kind"] == "decision"]
            self.assertTrue(all(e["channel"] == "simulated-human" and e["authenticity"] == "simulated" for e in decisions_))
            self.assertIn("SIMULATED", (work / handoff.HANDOFF_MD).read_text(encoding="utf-8"))

    def test_source_project_is_untouched(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            p = proposed_example(src)
            before = (p.root / workspace.LEDGER_FILE).read_bytes()
            demo.replay(p.root, Path(out) / "demo")
            self.assertEqual((p.root / workspace.LEDGER_FILE).read_bytes(), before)
            self.assertEqual(workspace.load_state(p.root)["mode"], "project")

    def test_simulated_decisions_do_not_count_if_mode_is_switched_back(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            p = proposed_example(src)
            work = Path(out) / "demo"
            demo.replay(p.root, work)
            state = workspace.load_state(work)
            state["mode"] = "project"
            state["stage"] = "S5"
            workspace.save_state(work, state)
            doc = handoff.build(work)
            self.assertEqual(doc["productionCode"], "locked")

    def test_until_stops_early(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            p = proposed_example(src)
            result = demo.replay(p.root, Path(out) / "demo", until="G2")
            self.assertEqual(result["approved"], ["G1", "G2"])
            self.assertEqual(result["handoff"]["stage"], "S0")

    def test_refuses_in_place_and_non_empty_workdir(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            p = proposed_example(src)
            with self.assertRaises(LfeError) as ctx:
                demo.replay(p.root, p.root / "sub")
            self.assertEqual(ctx.exception.code, "DEMO_IN_PLACE")
            (Path(out) / "x.txt").write_text("ocupado")
            with self.assertRaises(LfeError) as ctx:
                demo.replay(p.root, Path(out))
            self.assertEqual(ctx.exception.code, "WORKDIR_NOT_EMPTY")

    def test_refuses_folder_without_lfe(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            with self.assertRaises(LfeError) as ctx:
                demo.replay(Path(src), Path(out) / "demo")
            self.assertEqual(ctx.exception.code, "NOT_INITIALIZED")


if __name__ == "__main__":
    unittest.main()
