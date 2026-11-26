"""`lfe install --project` and the SessionStart notice for repositories without .lfe/ (issue #29)."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import install  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402

LAUNCHER = ROOT / "layout-first-engineering" / "scripts" / "lfe.py"


def lfe(root, *argv, stdin="", env=None):
    return subprocess.run([sys.executable, str(LAUNCHER), "--root", str(root), *argv], input=stdin,
                          capture_output=True, text=True, timeout=60, env=env)


class InstallTests(unittest.TestCase):
    def test_install_merges_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude").mkdir()
            (root / ".claude/settings.json").write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]},
                                                                    "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo bye"}]}]}}))
            first = install.install(root)
            self.assertTrue(first["copied"])
            self.assertEqual(len([c for c in first["settingsChanges"] if c.startswith("hook")]), 3)
            second = install.install(root)
            self.assertEqual((second["copied"], second["settingsChanges"]), (False, []))
            settings = json.loads((root / ".claude/settings.json").read_text())
            self.assertEqual(settings["permissions"]["allow"], ["Bash(ls:*)"])
            self.assertEqual(len(settings["hooks"]["Stop"]), 2)  # the user's own hook is kept
            self.assertEqual(install.check(root)["status"], "current")
            skill = root / install.TARGET
            for name in ("SKILL.md", "scripts/lfe.py", "engine/lfe/gates.py", "contracts/state.schema.json",
                         "references/01-conversation-and-state.md", "assets/PROJECT_STATE.md"):
                self.assertTrue((skill / name).is_file(), name)

    def test_vendored_copy_runs_on_its_own(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install.install(root)
            launcher = root / install.TARGET / "scripts/lfe.py"
            env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            for argv in (["init", "t", "T"], ["render"], ["status"]):
                done = subprocess.run([sys.executable, str(launcher), "--root", tmp, *argv], capture_output=True,
                                      text=True, timeout=60, env=env)
                self.assertEqual(done.returncode, 0, done.stderr)
            payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": f"{tmp}/app/x.js"}})
            done = subprocess.run([sys.executable, str(launcher), "--root", tmp, "hook-pre-tool-use"], input=payload,
                                  capture_output=True, text=True, timeout=60, env=env)
            self.assertIn('"deny"', done.stdout)

    def test_check_detects_tampering_and_bad_settings_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install.install(root)
            (root / install.TARGET / "engine/lfe/policy.py").write_text("# gone\n")
            self.assertEqual(install.check(root)["status"], "modified")
            self.assertEqual(lfe(root, "install", "--check").returncode, 3)
            install.install(root)
            self.assertEqual(install.check(root)["status"], "current")
            (root / ".claude/settings.json").write_text("{not json")
            with self.assertRaises(LfeError) as ctx:
                install.install(root)
            self.assertEqual(ctx.exception.code, "BAD_SETTINGS")


class SessionStartNoticeTests(unittest.TestCase):
    def test_lfe_documents_without_engine_get_a_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "PROJECT_STATE.md").write_text("# Estado\n- **Current stage:** S3\n")
            done = lfe(tmp, "hook-session-start", stdin="{}")
            context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("LFE NOT ACTIVE", context)
            self.assertIn("adopt --dry-run", context)

    def test_unrelated_repository_stays_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(lfe(tmp, "hook-session-start", stdin="{}").stdout, "")


if __name__ == "__main__":
    unittest.main()
