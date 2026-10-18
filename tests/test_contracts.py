"""Contract conformance suite (RFC-0001, section 13). Offline; exercises real validation code.

Every file in contracts/fixtures/<contract>/valid must produce no issue; every file in
contracts/fixtures/<contract>/invalid/<CODE>__<description>.json must produce an issue with CODE.
"""
from pathlib import Path
import contextlib
import io
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

from lfe import contracts, schema_lite  # noqa: E402
from lfe.__main__ import main as cli  # noqa: E402

FIXTURES = ROOT / "contracts" / "fixtures"


class FixtureConformanceTests(unittest.TestCase):
    def test_every_contract_has_schema_and_enough_fixtures(self):
        for name in contracts.KNOWN:
            with self.subTest(contract=name):
                self.assertTrue((ROOT / "contracts" / f"{name}.schema.json").is_file())
                valid = list((FIXTURES / name / "valid").glob("*.json"))
                invalid = list((FIXTURES / name / "invalid").glob("*.json"))
                self.assertGreaterEqual(len(valid), 2)
                self.assertGreaterEqual(len(invalid), 5)

    def test_valid_fixtures_have_no_issues(self):
        for path in sorted(FIXTURES.glob("*/valid/*.json")):
            with self.subTest(fixture=f"{path.parent.parent.name}/{path.name}"):
                issues = contracts.validate_file(path, expected=path.parent.parent.name)
                self.assertEqual(issues, [], [str(i) for i in issues])

    def test_invalid_fixtures_report_the_declared_code(self):
        for path in sorted(FIXTURES.glob("*/invalid/*.json")):
            expected_code = path.stem.split("__", 1)[0]
            with self.subTest(fixture=f"{path.parent.parent.name}/{path.name}"):
                issues = contracts.validate_file(path)
                codes = {i.code for i in issues}
                self.assertIn(expected_code, codes, [str(i) for i in issues])


class StrictParsingTests(unittest.TestCase):
    def test_duplicate_keys_are_rejected(self):
        _, issues = contracts.parse('{"stage": "S0", "stage": "S6"}')
        self.assertEqual([i.code for i in issues], ["DUPLICATE_KEY"])

    def test_floats_and_non_finite_numbers_are_rejected(self):
        for text in ('{"n": 1.5}', '{"n": 1e3}', '{"n": NaN}', '{"n": Infinity}'):
            with self.subTest(text=text):
                _, issues = contracts.parse(text)
                self.assertEqual([i.code for i in issues], ["FLOAT_NOT_ALLOWED"])

    def test_broken_json_is_reported(self):
        _, issues = contracts.parse('{"stage": ')
        self.assertEqual([i.code for i in issues], ["INVALID_JSON"])

    def test_wrong_contract_type_is_incompatible(self):
        doc = {"schemaVersion": "lfe.action/0.1", "actor": "agent", "tool": "Write", "targets": ["a.txt"]}
        self.assertEqual([i.code for i in contracts.validate(doc, expected="state")], ["INCOMPATIBLE_SCHEMA"])


class CanonicalHashTests(unittest.TestCase):
    def test_key_order_and_whitespace_do_not_change_the_hash(self):
        a = contracts.canonical_json({"b": 1, "a": "ção"})
        b = contracts.canonical_json({"a": "ção", "b": 1})
        self.assertEqual(a, b)
        self.assertEqual(a, '{"a":"ção","b":1}'.encode("utf-8"))

    def test_known_vector(self):
        # sha256 of the empty object `{}`; pins the algorithm and the prefix format.
        self.assertEqual(contracts.sha256_of(contracts.canonical_json({})),
                         "sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a")


class UnsafePathTests(unittest.TestCase):
    def test_paths(self):
        for value in ("../x", "a/../../x", "/etc/passwd", "C:/x", "a\\b", ""):
            with self.subTest(value=value):
                self.assertTrue(contracts.unsafe_path(value))
        for value in ("app/src/x.js", ".lfe/state.json", "prototype/index.html"):
            with self.subTest(value=value):
                self.assertFalse(contracts.unsafe_path(value))


class SchemaLiteTests(unittest.TestCase):
    def test_unknown_keyword_fails_loudly(self):
        with self.assertRaises(schema_lite.UnsupportedKeyword):
            schema_lite.validate({}, {"type": "object", "dependentRequired": {}})

    def test_bool_is_not_an_integer(self):
        self.assertTrue(schema_lite.validate(True, {"type": "integer"}))
        self.assertFalse(schema_lite.validate(3, {"type": "integer"}))

    def test_schemas_only_use_supported_keywords(self):
        # Validating any document walks the schema; an unsupported keyword would raise.
        for path in sorted(FIXTURES.glob("*/valid/*.json")):
            with self.subTest(fixture=path.name):
                contracts.validate_file(path)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli(["validate", *map(str, args)])
        return code, out.getvalue()

    def test_exit_codes(self):
        valid = next((FIXTURES / "state" / "valid").glob("*.json"))
        invalid = FIXTURES / "evidence" / "invalid" / "PASS_WITHOUT_PROOF__exit_zero_zero_tests.json"
        future = FIXTURES / "state" / "invalid" / "INCOMPATIBLE_SCHEMA__future_minor.json"
        self.assertEqual(self.run_cli(valid)[0], 0)
        code, out = self.run_cli(invalid)
        self.assertEqual(code, 6)
        self.assertIn("PASS_WITHOUT_PROOF", out)
        self.assertEqual(self.run_cli(future)[0], 4)


if __name__ == "__main__":
    unittest.main()
