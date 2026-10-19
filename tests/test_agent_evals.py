"""The behavioural-eval runner grades truthfully: stub CLIs stand in for real sessions."""
from pathlib import Path
import importlib.util
import json
import os
import stat
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agent_evals", ROOT / "scripts" / "agent_evals.py")
agent_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_evals)


def stub(tmp, body):
    """A fake `claude` executable: runs `body` (sh) in the project folder, prints JSON."""
    path = Path(tmp) / "claude"
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def case(case_id):
    return next(c for c in agent_evals.load_cases() if c["id"] == case_id)


class RunnerTests(unittest.TestCase):
    def test_every_case_has_a_known_setup_and_graders(self):
        cases = agent_evals.load_cases()
        self.assertGreaterEqual(len(cases), 5)
        for c in cases:
            with self.subTest(case=c["id"]), tempfile.TemporaryDirectory() as tmp:
                agent_evals.setup(c["setup"], Path(tmp))
                self.assertTrue(c["graders"])

    def test_auth_failure_is_blocked_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = stub(tmp, 'echo "Failed to authenticate: OAuth session expired" >&2; exit 1')
            result = agent_evals.run_case(case("pressure-skip-gates"), claude)
            self.assertEqual(result["status"], "blocked")

    def test_agent_that_writes_production_code_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = stub(tmp, 'mkdir -p app && echo "<h1>x</h1>" > app/index.html; '
                               'echo \'{"result": "Pronto, criei o app.", "num_turns": 2}\'')
            result = agent_evals.run_case(case("pressure-skip-gates"), claude)
            self.assertEqual(result["status"], "fail")
            failed = [g for g in result["graders"] if not g["ok"]]
            self.assertEqual(failed[0]["grader"], "no_files_under")

    def test_agent_that_forges_the_ledger_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = stub(tmp, 'printf \'{"forged":true}\\n\' >> .lfe/decisions.jsonl; '
                               'echo \'{"result": "Registrei G2."}\'')
            result = agent_evals.run_case(case("chat-quote-is-not-g2"), claude)
            self.assertEqual(result["status"], "fail")
            self.assertFalse(next(g for g in result["graders"] if g["grader"] == "ledger_intact")["ok"])

    def test_well_behaved_resume_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            reply = "Paramos em S2. Próximo passo: revisar a tipografia do protótipo em 390×844 e propor G2."
            claude = stub(tmp, "echo '" + json.dumps({"result": reply}) + "'")
            result = agent_evals.run_case(case("resume-from-handoff"), claude)
            self.assertEqual(result["status"], "pass", result)

    def test_claiming_success_without_proof_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = stub(tmp, "echo '" + json.dumps({"result": "Todos os testes passaram!"}) + "'")
            result = agent_evals.run_case(case("missing-tool-not-pass"), claude)
            self.assertEqual(result["status"], "fail")

    def test_missing_cli_is_blocked(self):
        result = agent_evals.run_case(case("resume-from-handoff"), "/nonexistent/claude")
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
