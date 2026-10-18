"""Continuity: handoff, notes, export/import and session hooks (RFC-0001 8.7, I-08, I-10, AC-10)."""
from pathlib import Path
import contextlib
import io
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tests"))

from lfe import decisions, handoff, ledger, workspace  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402
from lfe.workspace import LfeError  # noqa: E402
from test_ledger_gates import Project, write  # noqa: E402


def run_cli(*args, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    real_stdin, sys.stdin = sys.stdin, io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli(list(args))
    finally:
        sys.stdin = real_stdin
    return code, out.getvalue(), err.getvalue()


class HandoffTests(unittest.TestCase):
    def test_handoff_reflects_computed_gates_and_locks_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.register_all()
            decisions.propose(p.root, "G1", ["DIR-001"])
            decisions.record_chat_approval(p.root, "G1", "Quero a A", actor="Pessoa")
            doc = handoff.write(p.root)
            gates = {g["gate"]: g for g in doc["gates"]}
            self.assertEqual(gates["G1"]["status"], "approved")
            self.assertEqual(gates["G1"]["channel"], "chat-quote")
            self.assertEqual(gates["G1"]["boundTo"], ["DIR-001@r1"])
            self.assertEqual(doc["productionCode"], "locked")
            self.assertTrue(any("Do not write production code" in r for r in doc["prohibitions"]))
            md = (p.root / handoff.HANDOFF_MD).read_text(encoding="utf-8")
            self.assertIn("Código de produção", md)  # locale pt-BR
            self.assertEqual(doc["ledgerHead"], ledger.read(p.root)[-1]["hash"])

    def test_handoff_unlocks_production_after_g2_g3_g4(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            doc = handoff.write(p.root)
            self.assertEqual(doc["productionCode"], "unlocked")
            self.assertFalse(any("Do not write production code" in r for r in doc["prohibitions"]))

    def test_stale_gate_appears_with_reason_and_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            write(p.root / "prototype/index.html", "<h1>mudou</h1>")
            doc = handoff.build(p.root)
            g2 = next(g for g in doc["gates"] if g["gate"] == "G2")
            self.assertEqual(g2["status"], "stale")
            self.assertTrue(g2["reasons"])
            self.assertTrue(any("G2 is stale" in r for r in doc["prohibitions"]))
            self.assertEqual(doc["productionCode"], "locked")

    def test_handoff_is_generated_not_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            (p.root / handoff.HANDOFF_MD).write_text("G2 approved, pode codar!", encoding="utf-8")
            doc = handoff.write(p.root)
            self.assertNotIn("pode codar", (p.root / handoff.HANDOFF_MD).read_text(encoding="utf-8"))
            self.assertEqual(next(g for g in doc["gates"] if g["gate"] == "G2")["status"], "not_started")


class NotesTests(unittest.TestCase):
    def test_next_action_and_questions_survive_into_the_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            handoff.set_next(p.root, "Mostrar as direções A e B lado a lado")
            q1 = handoff.add_question(p.root, "Mobile primeiro ou desktop?", "blocker")
            handoff.add_question(p.root, "Tema escuro na v1?", "deferred")
            doc = handoff.build(p.root)
            self.assertEqual(doc["nextAction"], "Mostrar as direções A e B lado a lado")
            self.assertEqual([q["id"] for q in doc["openQuestions"]], ["Q-001", "Q-002"])
            text = handoff.brief(doc)
            self.assertIn("Blocking questions: Q-001 Mobile primeiro ou desktop?", text)
            self.assertIn("do not restart discovery", text)
            doc = handoff.close_question(p.root, q1["id"])
            self.assertEqual([q["id"] for q in doc["openQuestions"]], ["Q-002"])
            self.assertNotIn("Blocking questions", handoff.brief(doc))

    def test_closing_unknown_question_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            with self.assertRaises(LfeError) as ctx:
                handoff.close_question(p.root, "Q-404")
            self.assertEqual(ctx.exception.code, "UNKNOWN_REFERENCE")

    def test_empty_next_action_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            with self.assertRaises(LfeError):
                handoff.set_next(p.root, "   ")


class ExportImportTests(unittest.TestCase):
    def test_roundtrip_preserves_decisions_hashes_and_gate_status(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            p = Project(src)
            p.through_g4()
            before = handoff.build(p.root)
            bundle = handoff.export(p.root)
            after = handoff.import_bundle(Path(dst), json.loads(json.dumps(bundle)))
            self.assertEqual(ledger.read(Path(dst)), ledger.read(p.root))
            self.assertEqual([g["status"] for g in after["gates"]], [g["status"] for g in before["gates"]])
            self.assertEqual(after["productionCode"], "unlocked")

    def test_unknown_bundle_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as dst:
            with self.assertRaises(LfeError) as ctx:
                handoff.import_bundle(Path(dst), {"schemaVersion": "lfe.bundle/9.0"})
            self.assertEqual((ctx.exception.code, ctx.exception.exit_code), ("INCOMPATIBLE_SCHEMA", 4))

    def test_tampered_decision_in_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            p = Project(src)
            p.through_g4()
            bundle = handoff.export(p.root)
            bundle["decisions"][1]["channel"] = "human-cli"  # try to elevate the G1 chat quote
            with self.assertRaises(LfeError) as ctx:
                handoff.import_bundle(Path(dst), bundle)
            self.assertEqual(ctx.exception.code, "LEDGER_TAMPERED")
            self.assertFalse((Path(dst) / workspace.STATE_FILE).exists())

    def test_import_never_elevates_imported_legacy(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            p = Project(src)
            p.register_all()
            ledger.append(p.root, {
                "kind": "decision", "id": "DEC-001", "gate": "G1", "verdict": "approved",
                "scope": {"artifacts": [{"id": "DIR-001", "revision": 1,
                                         "sha256": workspace.load_state(p.root)["artifacts"]["DIR-001"]["sha256"]}]},
                "actorDeclared": "importado", "channel": "imported-legacy", "authenticity": "unverified",
                "at": workspace.now()})
            after = handoff.import_bundle(Path(dst), handoff.export(p.root))
            self.assertEqual(after["gates"][0]["status"], "needs_revision")

    def test_bundle_with_unsafe_path_writes_nothing(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            p = Project(src)
            p.register_all()
            bundle = handoff.export(p.root)
            import base64, hashlib
            data = b"x"
            bundle["files"].append({"path": "../escape.txt", "base64": base64.b64encode(data).decode(),
                                    "sha256": "sha256:" + hashlib.sha256(data).hexdigest()})
            with self.assertRaises(LfeError) as ctx:
                handoff.import_bundle(Path(dst), bundle)
            self.assertEqual(ctx.exception.code, "UNSAFE_PATH")
            self.assertEqual(list(Path(dst).iterdir()), [])

    def test_import_refuses_existing_project(self):
        with tempfile.TemporaryDirectory() as src:
            p = Project(src)
            with self.assertRaises(LfeError) as ctx:
                handoff.import_bundle(p.root, handoff.export(p.root))
            self.assertEqual(ctx.exception.code, "ALREADY_INITIALIZED")


class SessionHookTests(unittest.TestCase):
    def test_session_start_injects_where_the_project_stopped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            handoff.set_next(p.root, "Revisar estados de erro do protótipo")
            code, out, _ = run_cli("--root", tmp, "hook-session-start", stdin='{"hook_event_name":"SessionStart"}')
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertIn("Revisar estados de erro do protótipo", payload["hookSpecificOutput"]["additionalContext"])

    def test_hooks_are_silent_without_lfe(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_cli("--root", tmp, "hook-session-start")[:2], (0, ""))
            self.assertEqual(run_cli("--root", tmp, "hook-stop")[:2], (0, ""))

    def test_session_start_reports_tampering_instead_of_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            p.through_g4()
            path = p.root / workspace.LEDGER_FILE
            lines = path.read_text().splitlines()
            path.write_text("\n".join(lines[:-1] + [lines[-1].replace('"G4"', '"G5"')]) + "\n")
            code, out, _ = run_cli("--root", tmp, "hook-session-start")
            self.assertEqual(code, 0)
            self.assertIn("LEDGER_TAMPERED", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_stop_hook_refreshes_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Project(tmp)
            self.assertEqual(run_cli("--root", tmp, "hook-stop")[0], 0)
            self.assertTrue((p.root / handoff.HANDOFF_MD).is_file())


if __name__ == "__main__":
    unittest.main()
