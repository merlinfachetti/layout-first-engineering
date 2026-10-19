"""Claude Code plugin packaging: manifests agree, hooks run the real engine and fail closed."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def hook_command(event):
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    return hooks[event][0]["hooks"][0]["command"]


def run_hook(event, payload, project, plugin_root=ROOT):
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_root), CLAUDE_PROJECT_DIR=str(project),
               PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(["sh", "-c", hook_command(event)], input=json.dumps(payload), capture_output=True,
                          text=True, env=env, timeout=60)


class ManifestTests(unittest.TestCase):
    def test_versions_and_names_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        skill = (ROOT / "layout-first-engineering" / "SKILL.md").read_text(encoding="utf-8")
        version = re.search(r'(?m)^\s+version:\s*"([^"]+)"', skill).group(1)
        self.assertEqual(plugin["version"], version)
        self.assertEqual([p["name"] for p in market["plugins"]], [plugin["name"]])
        for path in plugin["skills"]:
            self.assertTrue((ROOT / path / "SKILL.md").is_file(), path)

    def test_command_skills_are_user_invoked_and_use_the_launcher(self):
        names = []
        for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            front = text.split("---", 2)[1]
            with self.subTest(skill=skill.parent.name):
                self.assertIn("disable-model-invocation: true", front)
                self.assertRegex(front, r'(?m)^description: ".+"$')  # quoted: colons must not break YAML
                self.assertIn("${CLAUDE_PLUGIN_ROOT}/layout-first-engineering/scripts/lfe.py", text)
            names.append(skill.parent.name)
        self.assertEqual(names, ["next", "resume", "status", "studio"])

    def test_pretooluse_fails_closed(self):
        self.assertTrue(hook_command("PreToolUse").rstrip().endswith("|| exit 2"))


class HookExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        subprocess.run([str(ROOT / "bin" / "lfe"), "--root", str(self.project), "init", "plugin-test", "Plugin test"],
                       check=True, capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def tearDown(self):
        self.tmp.cleanup()

    def write_payload(self, rel):
        return {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(self.project),
                "tool_input": {"file_path": str(self.project / rel), "content": "x"}}

    def test_production_write_is_denied_before_gates(self):
        result = run_hook("PreToolUse", self.write_payload("app/x.js"), self.project)
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("GATE_NOT_APPROVED", decision["permissionDecisionReason"])

    def test_docs_write_is_allowed_silently(self):
        result = run_hook("PreToolUse", self.write_payload("docs/notes.md"), self.project)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, ""))

    def test_broken_engine_blocks_with_exit_2(self):
        result = run_hook("PreToolUse", self.write_payload("app/x.js"), self.project, plugin_root="/nonexistent")
        self.assertEqual(result.returncode, 2)

    def test_session_start_injects_context(self):
        result = run_hook("SessionStart", {"hook_event_name": "SessionStart"}, self.project)
        self.assertEqual(result.returncode, 0)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("plugin-test", context)
        self.assertIn("production code locked", context)

    def test_stop_hook_writes_handoff(self):
        self.assertEqual(run_hook("Stop", {"hook_event_name": "Stop"}, self.project).returncode, 0)
        self.assertTrue((self.project / ".lfe" / "HANDOFF.md").is_file())


if __name__ == "__main__":
    unittest.main()
