"""`lfe adopt` on a synthetic project already under way (issue #28). Offline, real files."""
from pathlib import Path
import contextlib
import io
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import adopt, decisions, gates, ledger, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402

STATE = """# Estado do projeto — Filmoteca

- **Project ID:** filmoteca
- **Owner / aprovador:** Pessoa (PO)
- **Current stage:** S7
- **Etapa atual:** **S7 — Verificação (G5)**.
- **Design source (verified URL):** https://www.figma.com/design/AbC123xyz/Filmoteca

## Gates

| Gate | Description | Status | Decision ID | Approved on | Evidence | Notas |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | Direção visual | aprovado ✅ | DEC-005 | 2026-11-25 | docs/design/VISUAL_DIRECTIONS.md | híbrida |
| G2 | Baseline visual | approved | DEC-005 | 2026-11-25 | docs/evidence/*.png | — |
| G3 | Escopo MVP | approved | DEC-006 | 2026-11-25 | docs/product/PRODUCT_SCOPE.md | — |
| G4 | Arquitetura | approved | DEC-007 | 2026-11-25 | docs/architecture/ADR-001-platform.md | — |
| G5 | Candidato | proposto | — | — | — | — |
| G6 | Produção | not_started | — | — | — | — |
"""
DECISIONS = "| DEC-001 | nome |\n| DEC-012 | outra decisão |\n"
SCOPE = """# Escopo

## MoSCoW

| Prioridade | Item |
| --- | --- |
| **Must** | Home (em alta, continuar), busca, ficha de filme |
| **Should** | Exportar JSON; PWA |
| **Won't (MVP)** | Rede social |
"""


def png(width, height):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x00" * width for _ in range(2))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def project(tmp):
    root = Path(tmp)
    files = {
        "PROJECT_STATE.md": STATE,
        "docs/DECISIONS.md": DECISIONS,
        "docs/product/PRODUCT_SCOPE.md": SCOPE,
        "docs/architecture/ADR-001-platform.md": "# ADR-001\nNext.js + Postgres\n",
        "docs/design/VISUAL_DIRECTIONS.md": "# Direções\nA e B\n",
        "prototypes/s1/a-sala.html": "<h1>A</h1>",
        "node_modules/pkg/PROJECT_STATE.md": "| G1 | x | approved |",
    }
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    for name, size in (("home-desktop.png", (1440, 4000)), ("home-mobile.png", (390, 844)),
                       ("series-desktop.png", (1440, 900))):
        path = root / "docs/evidence" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png(*size))
    return root


class ParsingTests(unittest.TestCase):
    def test_tolerant_state_reading(self):
        parsed = adopt.parse_state_text(STATE)
        self.assertEqual(parsed["stage"], "S7")
        self.assertEqual({g: r["status"] for g, r in parsed["gates"].items()},
                         {"G1": "approved", "G2": "approved", "G3": "approved", "G4": "approved",
                          "G5": "proposed", "G6": "not_started"})
        self.assertEqual(parsed["gates"]["G1"]["decisionId"], "DEC-005")
        self.assertEqual(parsed["fields"]["projectId"], "filmoteca")

    def test_stage_line_variants(self):
        for text in ("- Etapa atual: S3 — escopo", "Stage: S4", "- **Etapa atual:** **S2 — protótipos**"):
            self.assertEqual(adopt.parse_state_text(text)["stage"][0], "S", text)

    def test_moscow_rows_split_outside_parentheses(self):
        found = adopt.requirement_candidates(SCOPE)
        self.assertIn((None, "Home (em alta, continuar)", "must"), found)
        self.assertIn((None, "PWA", "should"), found)
        self.assertIn((None, "Rede social", "wont"), found)

    def test_written_requirement_ids_are_kept(self):
        found = adopt.requirement_candidates("- FR-001: Buscar títulos (Must)\n- NFR-002 LCP abaixo de 2,5 s (Should)\n")
        self.assertEqual(found, [("FR-001", "Buscar títulos (Must)", "must"), ("NFR-002", "LCP abaixo de 2,5 s (Should)", "should")])


class AdoptTests(unittest.TestCase):
    def test_dry_run_writes_nothing_and_plan_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            result = adopt.adopt(root, dry_run=True)
            self.assertFalse((root / ".lfe").exists())
            the_plan = result["plan"]
            self.assertEqual(adopt.contract_check(the_plan), [])
            self.assertEqual(the_plan["source"], "PROJECT_STATE.md")  # not the one in node_modules
            self.assertEqual(the_plan["decisionFloor"], 12)
            self.assertEqual(the_plan["legacyGates"], ["G1", "G2", "G3", "G4"])
            baseline = next(a for a in the_plan["artifacts"] if a["id"] == "DESIGN-001")["doc"]
            self.assertEqual(baseline["medium"], "figma")
            self.assertTrue(baseline["sourceUrl"].startswith("https://www.figma.com/design/AbC123xyz"))
            self.assertEqual([s["name"] for s in baseline["screens"]], ["Home", "Series"])
            self.assertIn({"width": 390, "height": 844}, baseline["screens"][0]["viewports"])

    def test_adopt_keeps_numbering_place_and_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            result = adopt.adopt(root)
            self.assertEqual((result["importedStage"], result["stage"]), ("S7", "S5"))
            entries = ledger.read(root)
            decision_ids = [e["id"] for e in entries if e["kind"] == "decision"]
            self.assertEqual(decision_ids, ["DEC-013", "DEC-014", "DEC-015", "DEC-016"])
            self.assertEqual(set(result["codes"]), {"G1", "G2", "G3", "G4"})
            state = workspace.load_state(root)
            results = gates.evaluate(root, state, entries)
            self.assertEqual(results["G2"]["status"], "needs_revision")
            self.assertIn("G2-", state["nextAction"])
            self.assertTrue((root / ".lfe/ADOPTION.md").is_file())
            with self.assertRaises(LfeError):
                decisions.set_stage(root, "S6")

    def test_reconfirming_by_chat_unlocks_s6(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            codes = adopt.adopt(root)["codes"]
            decisions.set_chat_approvals(root, ["G2", "G3", "G4"], "aprova pelo chat", "m1")
            for gate in ("G1", "G2", "G3", "G4"):
                decisions.record_chat_approval(root, gate, f"reconfirmo {codes[gate]}", message_ref="m2", actor="PO")
            decisions.set_stage(root, "S6")
            entries = ledger.read(root)
            self.assertEqual([e["id"] for e in entries if e["kind"] == "decision"][-1], "DEC-020")

    def test_one_message_reconfirms_every_gate_it_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            codes = adopt.adopt(root)["codes"]
            decisions.set_chat_approvals(root, ["G1", "G2", "G3", "G4"], "aprova pelo chat", "m1")
            quote = "reconfirmo " + " ".join(codes[g] for g in ("G1", "G2", "G3", "G4"))
            self.assertEqual(decisions.reconfirm(root, quote, "m2", actor="PO"), ["G1", "G2", "G3", "G4"])
            decisions.set_stage(root, "S6")
            with self.assertRaises(LfeError) as ctx:
                decisions.reconfirm(root, "ok, pode seguir", "m3")
            self.assertEqual(ctx.exception.code, "CONFIRMATION_CODE_MISSING")

    def test_reconfirm_stops_at_a_gate_that_is_not_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            codes = adopt.adopt(root)["codes"]
            with self.assertRaises(LfeError) as ctx:
                decisions.reconfirm(root, f"{codes['G1']} {codes['G2']}", "m2")
            self.assertEqual(ctx.exception.code, "CHANNEL_NOT_ALLOWED")
            self.assertIn("G1", str(ctx.exception))

    def test_dry_run_warns_when_a_live_product_will_be_locked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            notes = adopt.adopt(root, dry_run=True)["plan"]["notes"]
            self.assertTrue(notes[0].startswith("PRODUCTION CODE WILL BE LOCKED"))

    def test_existing_lfe_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            workspace.init(root, "x", "x")
            with self.assertRaises(LfeError) as ctx:
                adopt.adopt(root)
            self.assertEqual(ctx.exception.code, "ALREADY_INITIALIZED")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(tmp)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli(["--root", tmp, "adopt", "--dry-run"]), 0)
                self.assertEqual(cli(["--root", tmp, "adopt"]), 0)
            text = out.getvalue()
            self.assertIn("nothing was written", text)
            self.assertIn("ledger ids continue after DEC-012", text)
            self.assertIn("confirmation code G3-", text)


if __name__ == "__main__":
    unittest.main()
