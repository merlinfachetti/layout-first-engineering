"""Markdown bridge: `lfe render` and `lfe import-md` (RFC-0001, section 10, N-4, I-08).

Every rendered PROJECT_STATE.md must still pass the legacy validator, and an imported approval
must never unlock S6.
"""
from pathlib import Path
import contextlib
import importlib.util
import io
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "layout-first-engineering"
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lfe import contracts, decisions, gates, ledger, mdbridge, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402
from test_ledger_gates import Project, write  # noqa: E402

spec = importlib.util.spec_from_file_location("verify_project", SKILL / "scripts/verify_project.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

TEMPLATE = (SKILL / "assets/PROJECT_STATE.md").read_text(encoding="utf-8")


def legacy(stage="S7", approved=("G2", "G3", "G4")):
    """A hand-maintained PROJECT_STATE.md as the chat-only workflow produces it."""
    text = TEMPLATE.replace("**Current stage:** S0", f"**Current stage:** {stage}")
    for n, gate in enumerate(approved, start=1):
        text = re.sub(rf"(?m)^(\| {gate} \| [^|]+\|) not_started \| — \| — \| — \|",
                      rf"\g<1> approved | DEC-10{n} | 2026-09-0{n} | revisado na conversa |", text)
    return text


def rows(text):
    return {cells[0]: cells for cells in
            ([c.strip() for c in line.strip().strip("|").split("|")] for line in text.splitlines()
             if re.match(r"^\|\s*G[1-6]\s*\|", line))}


def human_text(text):
    """The file without the gate table, its markers and the stage value: what render must keep."""
    gate_lines = {mdbridge.BEGIN, mdbridge.END, *mdbridge.HEADER}
    kept = [line for line in text.split("\n")
            if line not in gate_lines and not re.match(r"^\|\s*G[1-6]\s*\|", line)]
    return re.sub(r"\*\*Current stage:\*\* S\d", "**Current stage:** S?", "\n".join(kept))


def check(text):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "PROJECT_STATE.md"
        path.write_text(text, encoding="utf-8")
        return verify.validate(path)


def decide(root, gate, verdict, **kw):
    return decisions.decide(root, gate, verdict, interactive=True, ask=lambda _: gate,
                            out=lambda *_: None, actor="Pessoa", **kw)


class RenderTests(unittest.TestCase):
    def render(self, p, text=None):
        target = p.root / "PROJECT_STATE.md"
        if text is not None:
            target.write_text(text, encoding="utf-8")
        outcome = mdbridge.render(p.root, target)
        return outcome, target.read_text(encoding="utf-8")

    def test_render_preserves_human_text_outside_the_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            human = mdbridge.render_block([[g, "x", "not_started", "—", "—", "—"] for g in workspace.GATES])
            source = TEMPLATE.replace("- TBD\n", "- Leituras offline são obrigatórias\n", 1)
            source = re.sub(r"(?s)\| Gate \|.*?\| G6 \|[^\n]*", "\n".join(human), source)
            _, out = self.render(p, source)
            self.assertEqual(human_text(out), human_text(source))
            self.assertIn("Leituras offline são obrigatórias", out)

    def test_render_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            outcome, first = self.render(p, TEMPLATE)
            self.assertEqual(outcome, "updated")
            outcome, second = self.render(p)
            self.assertEqual((outcome, second), ("unchanged", first))

    def test_status_mapping_approved_proposed_not_started(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            p.register("RC-001", "release-candidate", ".lfe/decisions/ADR-001.json")
            decisions.propose(p.root, "G5", ["RC-001"])
            _, out = self.render(p, TEMPLATE)
            r = rows(out)
            self.assertEqual([r[g][2] for g in workspace.GATES],
                             ["approved"] * 4 + ["proposed", "not_started"])
            self.assertRegex(r["G2"][3], r"^DEC-\d{3}$")
            self.assertRegex(r["G2"][4], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn("DESIGN-001 r1", r["G2"][5])
            self.assertIn("PROP-", r["G5"][5])
            self.assertEqual(r["G6"][3:], ["—", "—", "—"])

    def test_stale_renders_as_needs_revision_with_evidence_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            write(p.root / "prototype/index.html", "<h1>v2</h1>")
            state, entries, results = mdbridge.computed(p.root)
            self.assertEqual(results["G2"]["status"], "stale")
            _, out = self.render(p, TEMPLATE)
            g2 = rows(out)["G2"]
            self.assertEqual((g2[2], g2[5]), ("needs_revision", "stale: hash divergente"))
            self.assertEqual(check(out)[0], [])

    def test_not_applicable_renders_and_passes_the_legacy_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            decide(p.root, "G1", "not_applicable", rationale="produto existente com design estabelecido")
            _, out = self.render(p, TEMPLATE)
            self.assertEqual(rows(out)["G1"][2], "not_applicable")
            self.assertEqual(check(out)[0], [])

    def test_rendered_state_at_s6_passes_verify_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            decisions.set_stage(p.root, "S6")
            _, out = self.render(p, TEMPLATE)
            self.assertIn("**Current stage:** S6", out)
            errors, warnings = check(out)
            self.assertEqual((errors, warnings), ([], []))

    def test_file_without_markers_gets_its_table_wrapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            self.assertNotIn(mdbridge.BEGIN, TEMPLATE)
            _, out = self.render(p, TEMPLATE)
            self.assertEqual(out.count(mdbridge.BEGIN), 1)
            self.assertEqual(out.count("| Gate | Description |"), 1)
            self.assertEqual(len(rows(out)), 6)
            self.assertEqual(out.split(mdbridge.BEGIN)[0], TEMPLATE.split("| Gate | Description")[0])
            self.assertEqual(out.split(mdbridge.END)[1], TEMPLATE.split("| G6 |")[1].split("\n", 1)[1].join(["\n", ""]))
            self.assertEqual(human_text(out), human_text(TEMPLATE))

    def test_file_without_any_gate_table_gets_a_block_under_the_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            source = "# Estado\n\n- **Current stage:** S0\n\n## Stage and gate table\n\nNotas da equipe.\n"
            _, out = self.render(p, source)
            self.assertIn("## Stage and gate table\n\n" + mdbridge.BEGIN, out)
            self.assertIn(mdbridge.END + "\n\nNotas da equipe.\n", out)
            self.assertIn("**Current stage:** S0\n\n## Stage", out)
            self.assertEqual(check(out)[0], [])
            _, out = self.render(p, "# Estado\n\n- **Current stage:** S0\n\nTexto final.\n")
            self.assertIn("Texto final.\n\n" + mdbridge.BEGIN, out)
            self.assertTrue(out.endswith(mdbridge.END + "\n"))

    def test_missing_file_is_created_from_the_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            target = p.root / "docs/PROJECT_STATE.md"
            self.assertEqual(mdbridge.render(p.root, target), "created")
            out = target.read_text(encoding="utf-8")
            self.assertIn("## Session handoff to the next agent", out)
            self.assertIn(mdbridge.BEGIN, out)
            self.assertEqual(check(out)[0], [])

    def test_broken_markers_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            with self.assertRaises(LfeError) as ctx:
                self.render(p, TEMPLATE.replace("| Gate |", mdbridge.BEGIN + "\n| Gate |"))
            self.assertEqual(ctx.exception.code, "BROKEN_MARKERS")

    def test_render_refuses_a_hand_edited_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            state = workspace.load_state(p.root)
            state["gatesCache"]["G2"] = {"status": "approved", "decisionId": "DEC-999"}
            workspace.write_json_atomic(p.root / workspace.STATE_FILE, state)
            with self.assertRaises(LfeError) as ctx:
                mdbridge.render(p.root, p.root / "PROJECT_STATE.md")
            self.assertEqual(ctx.exception.code, "STATE_CACHE_MISMATCH")


class ImportTests(unittest.TestCase):
    def test_legacy_g2_to_g4_approved_never_unlocks_s6(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PROJECT_STATE.md").write_text(legacy("S7"), encoding="utf-8")
            report = mdbridge.import_md(root, root / "PROJECT_STATE.md", project_id="legado")
            self.assertEqual((report["importedStage"], report["stage"]), ("S7", "S5"))
            self.assertEqual(report["imported"], ["G2", "G3", "G4"])
            state = workspace.load_state(root)
            self.assertEqual(state["stage"], "S5")
            self.assertIn("reconfirm", state["nextAction"])
            entries = ledger.read(root)
            self.assertEqual({(e["channel"], e["authenticity"]) for e in entries},
                             {("imported-legacy", "unverified")})
            results = gates.evaluate(root, state, entries)
            self.assertEqual([results[g]["status"] for g in ("G2", "G3", "G4")], ["needs_revision"] * 3)
            with self.assertRaises(LfeError) as ctx:
                decisions.set_stage(root, "S6")
            self.assertEqual(ctx.exception.code, "STAGE_GATE_VIOLATION")

    def test_import_then_render_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = legacy("S4", approved=("G1", "G2"))
            (root / "PROJECT_STATE.md").write_text(source, encoding="utf-8")
            mdbridge.import_md(root, root / "PROJECT_STATE.md", project_id="legado")
            self.assertEqual(mdbridge.render(root, root / "PROJECT_STATE.md"), "updated")
            out = (root / "PROJECT_STATE.md").read_text(encoding="utf-8")
            self.assertEqual(human_text(out), human_text(source))
            r = rows(out)
            self.assertEqual([r[g][2] for g in ("G1", "G2", "G3")], ["needs_revision", "needs_revision", "not_started"])
            self.assertIn("reconfirmar", r["G1"][5])
            self.assertIn("**Current stage:** S4", out)
            self.assertEqual(check(out)[0], [])
            # A second import of the rendered file adds nothing: no row is approved any more.
            other = Path(tmp) / "copia"
            other.mkdir()
            report = mdbridge.import_md(other, root / "PROJECT_STATE.md", project_id="copia")
            self.assertEqual((report["stage"], report["imported"]), ("S4", []))
            self.assertEqual(mdbridge.render(root, root / "PROJECT_STATE.md"), "unchanged")

    def test_import_never_replaces_a_human_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            (p.root / "legacy.md").write_text(legacy("S6"), encoding="utf-8")
            report = mdbridge.import_md(p.root, p.root / "legacy.md")
            self.assertEqual((report["imported"], report["skipped"]), ([], ["G2", "G3", "G4"]))
            self.assertEqual(report["stage"], "S6")
            results = gates.evaluate(p.root, workspace.load_state(p.root), ledger.read(p.root))
            self.assertTrue(all(gates.is_valid(results, g) for g in ("G2", "G3", "G4")))

    def test_invalid_legacy_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PROJECT_STATE.md").write_text(legacy("S2").replace("| G5 |", "| G9 |"), encoding="utf-8")
            with self.assertRaises(LfeError) as ctx:
                mdbridge.import_md(root, root / "PROJECT_STATE.md")
            self.assertEqual(ctx.exception.code, "INVALID_LEGACY_STATE")
            self.assertFalse((root / ".lfe").exists())

    def test_cli_import_md_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "PROJECT_STATE.md").write_text(legacy("S8"), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli(["--root", tmp, "import-md", "PROJECT_STATE.md", "--project-id", "via-cli"]), 0)
                self.assertEqual(cli(["--root", tmp, "render"]), 0)
                self.assertEqual(cli(["--root", tmp, "status"]), 0)
            text = out.getvalue()
            self.assertIn("stage: S5 (file says S8)", text)
            self.assertIn("reconfirm with `lfe approve`", text)
            self.assertIn("production code: locked", text)
            self.assertEqual(workspace.load_state(Path(tmp))["projectId"], "via-cli")


class LegacyValidatorTests(unittest.TestCase):
    def test_stale_and_not_applicable_are_accepted_but_s6_still_needs_approved(self):
        text = legacy("S5", approved=("G2", "G3"))
        text = re.sub(r"(?m)^(\| G4 \| [^|]+\|) not_started ", r"\1 stale ", text)
        text = re.sub(r"(?m)^(\| G1 \| [^|]+\|) not_started ", r"\1 not_applicable ", text)
        self.assertEqual(check(text)[0], [])
        errors, _ = check(text.replace("**Current stage:** S5", "**Current stage:** S6"))
        self.assertEqual(errors, ["S6 requires G4=approved before production engineering"])
        errors, _ = check(text.replace("| G2 | Prototype and visual baseline approved | approved",
                                       "| G2 | Prototype and visual baseline approved | not_applicable")
                          .replace("**Current stage:** S5", "**Current stage:** S6"))
        self.assertIn("S6 requires G2=approved before production engineering", errors)

    def test_import_md_uses_the_legacy_parser(self):
        stage, gate_rows, errors = mdbridge.legacy_parser().parse(legacy("S3", approved=("G1",)))
        self.assertEqual((stage, errors, gate_rows["G1"][2]), (3, [], "approved"))


class ContractTests(unittest.TestCase):
    def decision(self, channel, authenticity):
        return {"schemaVersion": "lfe.decision/0.1", "kind": "decision", "seq": 1, "id": "DEC-001",
                "gate": "G3", "verdict": "approved", "scope": {"artifacts": []}, "actorDeclared": "Pessoa",
                "channel": channel, "authenticity": authenticity, "at": "2026-10-19T09:00:00Z",
                "prevHash": "sha256:" + "0" * 64, "hash": "sha256:" + "1" * 64}

    def test_empty_scope_only_for_imported_legacy(self):
        self.assertEqual(contracts.validate(self.decision("imported-legacy", "unverified")), [])
        for channel in ("human-cli", "studio-export"):
            with self.subTest(channel=channel):
                codes = [i.code for i in contracts.validate(self.decision(channel, "host-asserted"))]
                self.assertEqual(codes, ["EMPTY_SCOPE"])


if __name__ == "__main__":
    unittest.main()
