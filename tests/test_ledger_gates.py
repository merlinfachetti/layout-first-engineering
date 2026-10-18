"""State, ledger and gate behaviour (RFC-0001, D-01..D-09, S-02..S-04). Offline, real files.

Each test builds a small project in a temporary directory and drives it through the same
functions the CLI uses. Human decisions are injected with interactive=True and a scripted
confirmation; the CLI itself has no way to skip the terminal check.
"""
from pathlib import Path
import contextlib
import io
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import decisions, gates, ledger, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402


def write(path: Path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) if not isinstance(doc, str) else doc, encoding="utf-8")


class Project:
    """A demo-free project with every artifact needed up to G4."""

    def __init__(self, tmp):
        self.root = Path(tmp)
        workspace.init(self.root, "teste", "Projeto de teste")
        write(self.root / "prototype/index.html", "<h1>v1</h1>")
        write(self.root / ".lfe/directions/DIR-001.json", {"options": ["A", "B"]})
        write(self.root / ".lfe/baselines/DESIGN-001.json", {
            "schemaVersion": "lfe.baseline/0.1", "id": "DESIGN-001", "revision": 1, "title": "Tela",
            "medium": "local-html", "mediumDecisionId": "DEC-001", "fidelity": "static-layout",
            "screens": [{"screenId": "UI-001", "name": "Lista", "goal": "Ver leituras",
                         "states": ["default", "empty", "error"], "viewports": [{"width": 390, "height": 844}],
                         "prototype": {"path": "prototype/index.html"}}],
            "files": [{"path": "prototype/index.html", "sha256": "sha256:" + "0" * 64}]})
        write(self.root / ".lfe/requirements.json", {
            "schemaVersion": "lfe.requirements/0.1", "id": "SCOPE-001", "revision": 1, "tests": [],
            "items": [{"id": "FR-001", "title": "Adicionar", "acceptance": [{"given": "a", "when": "b", "then": "c"}],
                       "priority": "must", "uiRefs": ["UI-001"], "testRefs": [], "status": "approved"}]})
        write(self.root / ".lfe/decisions/ADR-001.json", {"chosen": "local-only"})

    def register(self, art_id, kind, rel, refresh=False):
        state = workspace.load_state(self.root)
        art, changed = workspace.register_artifact(self.root, state, art_id, kind, rel, refresh=refresh)
        workspace.save_state(self.root, state)
        return art, changed

    def register_all(self):
        self.register("DIR-001", "direction-set", ".lfe/directions/DIR-001.json")
        self.register("DESIGN-001", "experience-baseline", ".lfe/baselines/DESIGN-001.json", refresh=True)
        self.register("SCOPE-001", "requirements-set", ".lfe/requirements.json")
        self.register("ADR-001", "architecture-decision", ".lfe/decisions/ADR-001.json")

    def approve(self, gate, artifacts, **kw):
        decisions.propose(self.root, gate, artifacts)
        return decisions.decide(self.root, gate, "approved", interactive=True, ask=lambda _: gate,
                                out=lambda *_: None, actor="Pessoa", **kw)

    def through_g4(self):
        self.register_all()
        decisions.propose(self.root, "G1", ["DIR-001"])
        decisions.record_chat_approval(self.root, "G1", "Quero a direção A", option="A", actor="Pessoa")
        self.approve("G2", ["DESIGN-001"])
        self.approve("G3", ["DESIGN-001", "SCOPE-001"])
        self.approve("G4", ["SCOPE-001", "ADR-001"])

    def results(self):
        return gates.evaluate(self.root, workspace.load_state(self.root), ledger.read(self.root))


class HappyPathTests(unittest.TestCase):
    def test_full_path_to_s6_and_status_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            r = p.results()
            self.assertEqual([r[g]["status"] for g in ("G1", "G2", "G3", "G4")], ["approved"] * 4)
            decisions.set_stage(p.root, "S6")
            self.assertEqual(workspace.load_state(p.root)["stage"], "S6")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli(["--root", tmp, "status"]), 0)
            self.assertIn("production code: unlocked", out.getvalue())

    def test_registration_bumps_revision_only_on_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            art, changed = p.register("ADR-001", "architecture-decision", ".lfe/decisions/ADR-001.json")
            self.assertEqual((art["revision"], changed), (1, True))
            art, changed = p.register("ADR-001", "architecture-decision", ".lfe/decisions/ADR-001.json")
            self.assertEqual((art["revision"], changed), (1, False))
            write(p.root / ".lfe/decisions/ADR-001.json", {"chosen": "backend"})
            art, changed = p.register("ADR-001", "architecture-decision", ".lfe/decisions/ADR-001.json")
            self.assertEqual((art["revision"], changed), (2, True))


class AuditProbeTests(unittest.TestCase):
    """The six probes run against verify_project.py during the audit, now against the core."""

    def test_p1_p2_hand_edited_cache_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            state = workspace.load_state(p.root)
            for gate in ("G2", "G3", "G4"):
                state["gatesCache"][gate] = {"status": "approved", "decisionId": "DEC-999"}
            workspace.write_json_atomic(p.root / workspace.STATE_FILE, state)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(cli(["--root", tmp, "status"]), 5)
            self.assertIn("STATE_CACHE_MISMATCH", err.getvalue())

    def test_p3_appended_or_edited_ledger_line_is_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            path = p.root / workspace.LEDGER_FILE
            lines = path.read_text().splitlines()
            forged = json.loads(lines[-1])
            forged.update(seq=len(lines) + 1, gate="G5", id="DEC-099")
            path.write_text("\n".join(lines + [json.dumps(forged)]) + "\n")
            with self.assertRaises(LfeError) as ctx:
                ledger.read(p.root)
            self.assertEqual(ctx.exception.code, "LEDGER_TAMPERED")
            edited = json.loads(lines[1])
            edited["verdict"] = "approved"
            edited["actorDeclared"] = "outra pessoa"
            path.write_text("\n".join([lines[0], json.dumps(edited)] + lines[2:]) + "\n")
            with self.assertRaises(LfeError) as ctx:
                ledger.read(p.root)
            self.assertEqual(ctx.exception.code, "LEDGER_TAMPERED")

    def test_p4_s9_without_g6_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            with self.assertRaises(LfeError) as ctx:
                decisions.set_stage(p.root, "S9")
            self.assertEqual(ctx.exception.code, "STAGE_GATE_VIOLATION")

    def test_p5_g2_without_g1_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            p.approve("G2", ["DESIGN-001"])
            r = p.results()
            self.assertEqual(r["G2"]["status"], "blocked")
            with self.assertRaises(LfeError) as ctx:
                decisions.set_stage(p.root, "S3")  # no gate needed for S3: allowed
                decisions.set_stage(p.root, "S6")
            self.assertEqual(ctx.exception.code, "STAGE_GATE_VIOLATION")


class ContentBindingTests(unittest.TestCase):
    def test_editing_the_prototype_makes_g2_and_g3_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            decisions.set_stage(p.root, "S6")
            write(p.root / "prototype/index.html", "<h1>v2 com outro layout</h1>")
            r = p.results()
            self.assertEqual(r["G2"]["status"], "stale")
            self.assertEqual(r["G3"]["status"], "stale")
            self.assertEqual(r["G4"]["status"], "blocked")  # its predecessor is no longer valid
            self.assertTrue(any("changed" in x for x in r["G2"]["reasons"]))
            self.assertTrue(gates.stage_problems(r, "S6"))

    def test_new_revision_requires_a_new_proposal_and_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            write(p.root / "prototype/index.html", "<h1>v2</h1>")
            art, changed = p.register("DESIGN-001", "experience-baseline", ".lfe/baselines/DESIGN-001.json", refresh=True)
            self.assertEqual((art["revision"], changed), (2, True))
            self.assertEqual(p.results()["G2"]["status"], "stale")
            p.approve("G2", ["DESIGN-001"])
            self.assertEqual(p.results()["G2"]["status"], "approved")
            self.assertEqual(p.results()["G3"]["status"], "stale")  # G3 still bound to r1

    def test_approving_an_outdated_proposal_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G2", ["DESIGN-001"])
            write(p.root / "prototype/index.html", "<h1>v2</h1>")
            p.register("DESIGN-001", "experience-baseline", ".lfe/baselines/DESIGN-001.json", refresh=True)
            with self.assertRaises(LfeError) as ctx:
                decisions.decide(p.root, "G2", "approved", interactive=True, ask=lambda _: "G2", out=lambda *_: None)
            self.assertEqual(ctx.exception.code, "STALE_PROPOSAL")

    def test_proposal_must_bind_every_required_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            with self.assertRaises(LfeError) as ctx:
                decisions.propose(p.root, "G3", ["DESIGN-001"])
            self.assertEqual(ctx.exception.code, "MISSING_ARTIFACT_KIND")


class ChannelTests(unittest.TestCase):
    def test_approval_needs_an_interactive_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G2", ["DESIGN-001"])
            with self.assertRaises(LfeError) as ctx:
                decisions.decide(p.root, "G2", "approved", interactive=False)
            self.assertEqual(ctx.exception.code, "CHANNEL_NOT_INTERACTIVE")
            self.assertEqual(len(ledger.read(p.root)), 1)  # only the proposal

    def test_cli_approve_without_terminal_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G2", ["DESIGN-001"])
            err = io.StringIO()
            # Piped stdin is what an agent's shell tool provides: not a terminal, even if it types "G2".
            real_stdin, sys.stdin = sys.stdin, io.StringIO("G2\n")
            try:
                with contextlib.redirect_stderr(err):
                    code = cli(["--root", tmp, "approve", "G2"])
            finally:
                sys.stdin = real_stdin
            self.assertEqual(code, 2)
            self.assertIn("CHANNEL_NOT_INTERACTIVE", err.getvalue())

    def test_wrong_confirmation_records_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G2", ["DESIGN-001"])
            with self.assertRaises(LfeError) as ctx:
                decisions.decide(p.root, "G2", "approved", interactive=True, ask=lambda _: "sim", out=lambda *_: None)
            self.assertEqual(ctx.exception.code, "ABORTED")

    def test_chat_quote_only_records_g1(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G2", ["DESIGN-001"])
            with self.assertRaises(LfeError) as ctx:
                decisions.record_chat_approval(p.root, "G2", "gostei da opção B")
            self.assertEqual(ctx.exception.code, "CHANNEL_NOT_ALLOWED")

    def test_hybrid_g1_composition_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G1", ["DIR-001"])
            entry = decisions.record_chat_approval(
                p.root, "G1", "A no dark, B no light, coleções da C", actor="Pessoa",
                composition={"primary": "A", "themeVariants": [{"theme": "dark", "direction": "A"},
                                                                {"theme": "light", "direction": "B"}],
                             "complementary": [{"direction": "C", "usage": "coleções"}]})
            self.assertEqual(entry["authenticity"], "unverified")
            self.assertEqual(p.results()["G1"]["status"], "approved")


class DecisionLifecycleTests(unittest.TestCase):
    def test_revoke_unlocks_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            decisions.decide(p.root, "G3", "revoked", rationale="escopo mudou", interactive=True,
                             ask=lambda _: "G3", out=lambda *_: None, actor="Pessoa")
            r = p.results()
            self.assertEqual(r["G3"]["status"], "not_started")
            self.assertEqual(r["G4"]["status"], "blocked")

    def test_open_exception_blocks_its_target_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G1", ["DIR-001"])
            decisions.record_chat_approval(p.root, "G1", "A", actor="Pessoa")
            p.approve("G2", ["DESIGN-001"], exceptions=[("click-through não testado", "agente", "G3")])
            p.approve("G3", ["DESIGN-001", "SCOPE-001"])
            r = p.results()
            self.assertEqual(r["G2"]["status"], "approved")
            self.assertEqual(r["G3"]["status"], "blocked")
            self.assertTrue(any("EXC-001" in x for x in r["G3"]["reasons"]))

    def test_not_applicable_only_for_g1_and_g6(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            entry = decisions.decide(p.root, "G1", "not_applicable", rationale="produto existente", interactive=True,
                                     ask=lambda _: "G1", out=lambda *_: None, actor="Pessoa")
            self.assertEqual(entry["verdict"], "not_applicable")
            with self.assertRaises(LfeError) as ctx:
                decisions.decide(p.root, "G3", "not_applicable", rationale="pular", interactive=True,
                                 ask=lambda _: "G3", out=lambda *_: None, actor="Pessoa")
            self.assertEqual(ctx.exception.code, "NOT_APPLICABLE_FORBIDDEN")

    def test_imported_legacy_never_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            ledger.append(p.root, {
                "kind": "decision", "id": "DEC-001", "gate": "G1", "verdict": "approved",
                "scope": {"artifacts": [{"id": "DIR-001", "revision": 1,
                                         "sha256": workspace.load_state(p.root)["artifacts"]["DIR-001"]["sha256"]}]},
                "actorDeclared": "importado", "channel": "imported-legacy", "authenticity": "unverified",
                "at": workspace.now()})
            r = p.results()
            self.assertEqual(r["G1"]["status"], "needs_revision")
            self.assertIn("reconfirm", r["G1"]["reasons"][0])

    def test_simulated_decisions_only_count_in_demo_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            ledger.append(p.root, {
                "kind": "decision", "id": "DEC-001", "gate": "G1", "verdict": "approved",
                "scope": {"artifacts": [{"id": "DIR-001", "revision": 1,
                                         "sha256": workspace.load_state(p.root)["artifacts"]["DIR-001"]["sha256"]}]},
                "actorDeclared": "demo", "channel": "simulated-human", "authenticity": "simulated",
                "at": workspace.now()})
            self.assertEqual(p.results()["G1"]["status"], "needs_revision")
            state = workspace.load_state(p.root)
            state["mode"] = "demo"
            workspace.save_state(p.root, state)
            self.assertEqual(p.results()["G1"]["status"], "approved")

    def test_unsafe_artifact_path_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            with self.assertRaises(LfeError) as ctx:
                p.register("ADR-002", "architecture-decision", "../fora.json")
            self.assertEqual(ctx.exception.code, "UNSAFE_PATH")



class CommandDiscoveryTests(unittest.TestCase):
    def test_cli_modules_are_discovered(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli(["version"]), 0)
        self.assertIn("lfe.decision/0.1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
