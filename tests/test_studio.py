"""`lfe studio`: generated, self-contained, escaped and faithful to the computed state."""
from pathlib import Path
import base64
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tests"))

from lfe import handoff, studio, workspace  # noqa: E402
from test_ledger_gates import Project, write  # noqa: E402

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


class StudioTests(unittest.TestCase):
    def test_locked_project_shows_locked_and_all_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            out = studio.write(p.root)
            page = out.read_text(encoding="utf-8")
            self.assertIn("Código de produção bloqueado", page)
            for gate in ("G1", "G2", "G3", "G4", "G5", "G6"):
                self.assertIn(f'aria-label="{gate} not_started"', page)
            self.assertIn('aria-current="step"><span class="num">S0', page)

    def test_unlocked_after_g4_and_stale_after_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            self.assertIn("Código de produção liberado", studio.write(p.root).read_text(encoding="utf-8"))
            write(p.root / "prototype/index.html", "<h1>mudou</h1>")
            page = studio.write(p.root).read_text(encoding="utf-8")
            self.assertIn('aria-label="G2 stale"', page)
            self.assertIn("Código de produção bloqueado", page)

    def test_project_text_is_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            handoff.set_next(p.root, '<script>alert(1)</script><img src=x onerror=alert(2)>')
            page = studio.write(p.root).read_text(encoding="utf-8")
            self.assertNotIn("<script>alert", page)
            self.assertNotIn("<img src=x", page)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_page_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = studio.write(Project(tmp).root).read_text(encoding="utf-8")
            self.assertNotIn("<script", page)
            self.assertFalse(re.search(r'(src|href)="https?://', page))
            self.assertIn("Content-Security-Policy", page)

    def test_baseline_preview_is_shown_with_a_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            (p.root / "prototype/previews").mkdir(parents=True)
            (p.root / "prototype/previews/ui-001.png").write_bytes(PNG)
            base = p.root / ".lfe/baselines/DESIGN-001.json"
            import json
            doc = json.loads(base.read_text())
            doc["screens"][0]["preview"] = {"path": "prototype/previews/ui-001.png"}
            doc["files"].append({"path": "prototype/previews/ui-001.png", "sha256": "sha256:" + "0" * 64})
            base.write_text(json.dumps(doc))
            p.register("DESIGN-001", "experience-baseline", ".lfe/baselines/DESIGN-001.json", refresh=True)
            page = studio.write(p.root).read_text(encoding="utf-8")
            self.assertIn('src="../prototype/previews/ui-001.png"', page)
            self.assertIn("static-layout", page)

    def test_english_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace.init(root, "en-app", "English app", locale="en")
            self.assertIn("Production code locked", studio.write(root).read_text(encoding="utf-8"))

    def test_accepted_exception_is_visible_on_its_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            from lfe import decisions
            decisions.propose(p.root, "G1", ["DIR-001"])
            decisions.record_chat_approval(p.root, "G1", "A", actor="Pessoa")
            p.approve("G2", ["DESIGN-001"], exceptions=[("click-through não testado", "agente", "G5")])
            page = studio.write(p.root).read_text(encoding="utf-8")
            self.assertIn("pendência aceita EXC-001: click-through não testado — trava G5", page)


if __name__ == "__main__":
    unittest.main()
