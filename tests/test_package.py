"""Offline packaging checks: structure + state policy. Not a behavioral LLM test."""
from pathlib import Path
import importlib.util
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "layout-first-engineering"

spec = importlib.util.spec_from_file_location("verify_project", SKILL / "scripts/verify_project.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter_standard(self):
        data = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(data.startswith("---\n"))
        header = data.split("---", 2)[1]
        name = re.search(r"(?m)^name:\s*([^\n]+)$", header).group(1).strip()
        desc = re.search(r"(?m)^description:\s*([^\n]+)$", header).group(1).strip()
        self.assertEqual(name, SKILL.name)
        self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertTrue(1 <= len(desc) <= 1024)
        self.assertIn("when a user", desc.lower())

    def test_local_reference_paths_exist(self):
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        ref_paths = re.findall(r"(?:references|assets)/[a-zA-Z0-9_.-]+\.md", body)
        self.assertGreaterEqual(len(set(ref_paths)), 12)
        for link in set(ref_paths):
            with self.subTest(path=link):
                self.assertTrue((SKILL / link).is_file())

    def test_required_project_assets_and_license(self):
        for x in ["LICENSE", "SKILL.md", "scripts/verify_project.py", "assets/PROJECT_STATE.md",
                  "assets/DESIGN_HANDOFF.md", "assets/COST_MODEL.md", "assets/DELIVERY_PLAN.md"]:
            with self.subTest(file=x):
                self.assertTrue((SKILL / x).is_file())

    def test_public_guides_and_entrypoint_are_present(self):
        required = [
            "docs/INSTALACAO-E-USO.pt-BR.md",
            "docs/MANUAL-MESTRE.pt-BR.md",
            "docs/INSTALLATION-AND-USAGE.md",
            "docs/PROMPTS-MESTRES.pt-BR.md",
            "docs/PUBLICACAO-GITHUB-MAC.md",
            "PUBLICAR_NO_GITHUB.command",
            "scripts/publish-macos.sh",
        ]
        for x in required:
            with self.subTest(file=x):
                self.assertTrue((ROOT / x).is_file())
        readme = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")
        self.assertIn("docs/INSTALACAO-E-USO.pt-BR.md", readme)
        self.assertIn("docs/MANUAL-MESTRE.pt-BR.md", readme)
        self.assertIn("docs/PROMPTS-MESTRES.pt-BR.md", readme)

    def test_project_template_is_valid(self):
        errors, warnings = mod.validate(SKILL / "assets/PROJECT_STATE.md")
        self.assertEqual(errors, [], (errors, warnings))


class GateTests(unittest.TestCase):
    def mutate(self, *, stage="S6", statuses=None):
        source = (SKILL / "assets/PROJECT_STATE.md").read_text(encoding="utf-8")
        source = source.replace("**Current stage:** S0", f"**Current stage:** {stage}")
        for gate, status in (statuses or {}).items():
            source = re.sub(rf"(?m)^(\| {gate} \|[^\n]*?\|) not_started (\|)",
                            rf"\g<1> {status} \2", source)
        return source

    def check(self, data):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "PROJECT_STATE.md"
            f.write_text(data, encoding="utf-8")
            return mod.validate(f)

    def test_engineering_blocked_without_approvals(self):
        errors, _ = self.check(self.mutate())
        self.assertTrue(any("G2=approved" in s for s in errors))
        self.assertTrue(any("G3=approved" in s for s in errors))
        self.assertTrue(any("G4=approved" in s for s in errors))

    def test_engineering_unblocked_with_gates(self):
        statuses = {f"G{i}": "approved" for i in (2, 3, 4)}
        errors, warnings = self.check(self.mutate(statuses=statuses))
        self.assertEqual(errors, [])
        self.assertTrue(any("decision ID" in w for w in warnings))

    def test_release_candidate_and_deploy_warning(self):
        statuses = {f"G{i}": "approved" for i in (2, 3, 4, 5)}
        errors, warnings = self.check(self.mutate(stage="S8", statuses=statuses))
        self.assertEqual(errors, [])
        self.assertTrue(any("do NOT deploy" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
