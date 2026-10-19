"""The installable skill archive carries a working engine and is reproducible."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_release", ROOT / "scripts" / "build_release.py")
build_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_release)


class ReleasePackageTests(unittest.TestCase):
    def test_skill_zip_contains_engine_contracts_and_launcher(self):
        with tempfile.TemporaryDirectory() as out:
            build_release.build(Path(out))
            names = zipfile.ZipFile(Path(out) / "layout-first-engineering-skill.zip").namelist()
            for required in ("layout-first-engineering/SKILL.md", "layout-first-engineering/scripts/lfe.py",
                             "layout-first-engineering/engine/lfe/__main__.py",
                             "layout-first-engineering/engine/lfe/gates.py",
                             "layout-first-engineering/contracts/decision.schema.json"):
                self.assertIn(required, names)
            self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])

    def test_archives_are_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertEqual(build_release.build(Path(a)), build_release.build(Path(b)))

    def test_installed_skill_runs_lfe_end_to_end(self):
        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as home, \
                tempfile.TemporaryDirectory() as project:
            build_release.build(Path(out))
            zipfile.ZipFile(Path(out) / "layout-first-engineering-skill.zip").extractall(home)
            launcher = Path(home) / "layout-first-engineering" / "scripts" / "lfe.py"

            def lfe(*args):
                return subprocess.run([sys.executable, "-B", str(launcher), "--root", project, *args],
                                      capture_output=True, text=True, timeout=60, cwd=home)

            self.assertEqual(lfe("version").returncode, 0)
            self.assertEqual(lfe("init", "instalado", "Projeto instalado").returncode, 0)
            status = lfe("status")
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn("production code: locked", status.stdout)
            invalid = Path(project) / "x.json"
            invalid.write_text('{"schemaVersion": "lfe.evidence/0.1"}', encoding="utf-8")
            self.assertEqual(lfe("validate", str(invalid)).returncode, 6)  # schemas travel with the skill


if __name__ == "__main__":
    unittest.main()
