"""Fixes from field use on two real projects (issues #25, #26, #27). Offline, real files."""
from pathlib import Path
import contextlib
import io
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tests"))

from lfe import decisions, gates, ledger, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402
from test_ledger_gates import Project, write  # noqa: E402


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli(list(argv))
    return code, out.getvalue() + err.getvalue()


def latest_proposal(root, gate):
    return [e for e in ledger.read(root) if e["kind"] == "proposal" and e["gate"] == gate][-1]


class StageEnforcementTests(unittest.TestCase):
    """#25: a stage can only be entered once the gate closing the previous stage is valid."""

    def test_s2_is_refused_while_g1_is_only_proposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G1", ["DIR-001"])
            with self.assertRaises(LfeError) as ctx:
                decisions.set_stage(p.root, "S2")
            self.assertEqual(ctx.exception.code, "STAGE_GATE_VIOLATION")
            self.assertIn("G1", str(ctx.exception))
            code, out = run("--root", tmp, "stage", "S2")
            self.assertEqual(code, 3)

    def test_stages_cannot_be_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            for stage in ("S3", "S4", "S5"):
                with self.assertRaises(LfeError):
                    decisions.set_stage(p.root, stage)
            decisions.set_stage(p.root, "S1")  # no gate closes S0

    def test_each_gate_opens_the_next_stage_and_going_back_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G1", ["DIR-001"])
            decisions.record_chat_approval(p.root, "G1", "Quero a A", option="A", actor="Pessoa")
            decisions.set_stage(p.root, "S2")
            with self.assertRaises(LfeError):
                decisions.set_stage(p.root, "S3")
            p.approve("G2", ["DESIGN-001"])
            decisions.set_stage(p.root, "S3")
            decisions.set_stage(p.root, "S1")
            self.assertEqual(workspace.load_state(p.root)["stage"], "S1")

    def test_g1_not_applicable_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            decisions.decide(p.root, "G1", "not_applicable", rationale="redesign de um app existente",
                             interactive=True, ask=lambda _: "G1", out=lambda *_: None, actor="Pessoa")
            decisions.set_stage(p.root, "S2")


class CompositionTests(unittest.TestCase):
    """#26: hybrid G1 compositions without having to read the schema."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Project(self.tmp.name)
        self.p.register_all()
        decisions.propose(self.p.root, "G1", ["DIR-001"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_shorthands_are_normalized(self):
        entry = decisions.record_chat_approval(
            self.p.root, "G1", "A no dark, B no light", actor="Pessoa",
            composition={"primary": "A", "themeVariants": {"dark": "A", "light": "B"},
                         "complementary": ["C: coleções"], "nonNegotiables": "contraste AA"})
        self.assertEqual(entry["composition"], {
            "primary": "A",
            "themeVariants": [{"theme": "dark", "direction": "A"}, {"theme": "light", "direction": "B"}],
            "complementary": [{"direction": "C", "usage": "coleções"}],
            "nonNegotiables": ["contraste AA"]})

    def test_cli_flags_build_the_composition(self):
        code, out = run("--root", self.tmp.name, "record-chat-approval", "G1", "--quote", "A no dark, B no light",
                        "--option", "A", "--theme-variant", "dark=A", "--theme-variant", "light=B",
                        "--complementary", "C=coleções", "--as", "Pessoa")
        self.assertEqual(code, 0, out)
        decision = [e for e in ledger.read(self.p.root) if e["kind"] == "decision"][-1]
        self.assertEqual(decision["composition"]["primary"], "A")
        self.assertEqual(len(decision["composition"]["themeVariants"]), 2)

    def test_bad_json_is_a_clear_error(self):
        code, out = run("--root", self.tmp.name, "record-chat-approval", "G1", "--quote", "x",
                        "--composition", "{primary: A}")
        self.assertEqual(code, 2)
        self.assertIn("BAD_COMPOSITION", out)

    def test_help_shows_examples(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            cli(["record-chat-approval", "--help"])
        self.assertIn("--theme-variant dark=A", out.getvalue())
        self.assertIn('"themeVariants":[{"theme":"dark","direction":"A"}]', out.getvalue())


class ChatApprovalTests(unittest.TestCase):
    """#27: opt-in chat approvals for G2–G6, bound to the proposal by a confirmation code."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Project(self.tmp.name)
        self.p.register_all()
        decisions.propose(self.p.root, "G1", ["DIR-001"])
        decisions.record_chat_approval(self.p.root, "G1", "Quero a A", option="A", actor="Pessoa")
        decisions.propose(self.p.root, "G2", ["DESIGN-001"])
        self.code = gates.confirmation_code(latest_proposal(self.p.root, "G2"))

    def tearDown(self):
        self.tmp.cleanup()

    def enable(self, gate_list=("G2", "G3", "G4")):
        decisions.set_chat_approvals(self.p.root, gate_list, "pode aprovar tudo pelo chat", "chat:msg-1")

    def test_off_by_default(self):
        with self.assertRaises(LfeError) as ctx:
            decisions.record_chat_approval(self.p.root, "G2", f"aprovo {self.code}", message_ref="chat:2")
        self.assertEqual(ctx.exception.code, "CHANNEL_NOT_ALLOWED")

    def test_code_and_message_ref_are_required(self):
        self.enable()
        with self.assertRaises(LfeError) as ctx:
            decisions.record_chat_approval(self.p.root, "G2", "aprovado!", message_ref="chat:2")
        self.assertEqual(ctx.exception.code, "CONFIRMATION_CODE_MISSING")
        with self.assertRaises(LfeError) as ctx:
            decisions.record_chat_approval(self.p.root, "G2", f"aprovo {self.code}")
        self.assertEqual(ctx.exception.code, "MISSING_EVIDENCE")

    def test_approval_with_code_counts_and_goes_stale_on_change(self):
        self.enable()
        entry = decisions.record_chat_approval(self.p.root, "G2", f"Aprovo {self.code.upper()}", message_ref="chat:2",
                                               actor="Pessoa")
        self.assertEqual((entry["channel"], entry["authenticity"]), ("chat-quote", "unverified"))
        self.assertEqual(entry["evidence"]["confirmationCode"], self.code)
        self.assertEqual(self.p.results()["G2"]["status"], "approved")
        decisions.set_stage(self.p.root, "S3")
        write(self.p.root / "prototype/index.html", "<h1>v2</h1>")
        self.assertEqual(self.p.results()["G2"]["status"], "stale")

    def test_code_of_an_older_proposal_is_refused(self):
        self.enable()
        old = self.code
        write(self.p.root / "prototype/index.html", "<h1>v2</h1>")
        self.p.register("DESIGN-001", "experience-baseline", ".lfe/baselines/DESIGN-001.json", refresh=True)
        decisions.propose(self.p.root, "G2", ["DESIGN-001"])
        with self.assertRaises(LfeError) as ctx:
            decisions.record_chat_approval(self.p.root, "G2", f"aprovo {old}", message_ref="chat:3")
        self.assertEqual(ctx.exception.code, "CONFIRMATION_CODE_MISSING")

    def test_disabling_stops_chat_approvals_from_counting(self):
        self.enable()
        decisions.record_chat_approval(self.p.root, "G2", f"aprovo {self.code}", message_ref="chat:2", actor="Pessoa")
        decisions.disable_chat_approvals(self.p.root)
        self.assertEqual(self.p.results()["G2"]["status"], "needs_revision")

    def test_only_enabled_gates(self):
        self.enable(("G2",))
        self.p.register("SCOPE-001", "requirements-set", ".lfe/requirements.json")
        decisions.record_chat_approval(self.p.root, "G2", f"aprovo {self.code}", message_ref="chat:2", actor="Pessoa")
        decisions.propose(self.p.root, "G3", ["DESIGN-001", "SCOPE-001"])
        code3 = gates.confirmation_code(latest_proposal(self.p.root, "G3"))
        with self.assertRaises(LfeError) as ctx:
            decisions.record_chat_approval(self.p.root, "G3", f"aprovo {code3}", message_ref="chat:4")
        self.assertEqual(ctx.exception.code, "CHANNEL_NOT_ALLOWED")

    def test_cli_round_trip(self):
        tmp = self.tmp.name
        code, out = run("--root", tmp, "chat-approvals", "enable", "--quote", "aprova pelo chat",
                        "--message-ref", "chat:1")
        self.assertEqual(code, 0, out)
        code, out = run("--root", tmp, "propose", "G2", "--artifact", "DESIGN-001")
        self.assertEqual(code, 0, out)
        new_code = out.split("confirmation code: ")[1].split()[0]
        self.assertIn(f'"aprovo {new_code}"', out)
        code, out = run("--root", tmp, "record-chat-approval", "G2", "--quote", f"aprovo {new_code}",
                        "--message-ref", "chat:5", "--as", "Pessoa")
        self.assertEqual(code, 0, out)
        code, out = run("--root", tmp, "chat-approvals", "enable", "--message-ref", "chat:1")
        self.assertEqual(code, 2)


class NumberingTests(unittest.TestCase):
    def test_decision_floor_skips_existing_ids(self):
        self.assertEqual(ledger.next_id([], "decision", floor=10), "DEC-011")
        self.assertEqual(ledger.next_id([], "decision"), "DEC-001")
        self.assertEqual(ledger.next_id([], "proposal", floor=10), "PROP-001")
        self.assertEqual(ledger.next_id([{"id": "DEC-012"}], "decision", floor=10), "DEC-013")


if __name__ == "__main__":
    unittest.main()
