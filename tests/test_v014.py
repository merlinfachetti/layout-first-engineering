"""Offline guards for v0.1.4 candidate. Does NOT execute LLMs, remote Git or Figma."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'layout-first-engineering'

spec = importlib.util.spec_from_file_location('visual', SKILL / 'scripts' / 'verify_visual_baseline.py')
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)


class CandidateStructureTests(unittest.TestCase):
    def test_new_files_and_routing(self):
        required = [
            'references/07-repository-and-contribution-workflow.md',
            'assets/APPROVED_VISUAL_BASELINE.md',
            'assets/REPOSITORY_STATE.md',
            'assets/INTERACTION_CONTRACT.md',
            'scripts/verify_visual_baseline.py',
        ]
        skill = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for path in required:
            with self.subTest(path=path):
                self.assertTrue((SKILL / path).is_file())
                self.assertIn(path, skill)
        self.assertIn('G1', skill)
        self.assertIn('G2', skill)
        self.assertIn('G3', skill)
        self.assertIn('G4', skill)

    def test_eval_contracts_are_distinct_and_complete(self):
        scenarios = json.loads((ROOT / 'tests/evals/scenarios.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(scenarios), 10)
        self.assertEqual(len(set(x['id'] for x in scenarios)), len(scenarios))
        for case in scenarios:
            with self.subTest(case=case['id']):
                self.assertIn(case['stage'], ['S0','S1','S2','S3','S4','S5','S6','S7','S8','S9','G1','G2','G3','G4','G5','G6'])
                for key in ('situation', 'expected', 'must_not', 'evidence_required'):
                    self.assertTrue(case.get(key), (case['id'], key))

    def test_explicit_nonbehavioral_qualification(self):
        matrix = (ROOT / 'docs/VALIDATION-MATRIX.md').read_text(encoding='utf-8')
        self.assertIn('not_run', matrix)
        self.assertIn('not 12 successful LLM evaluations', matrix)


class VisualBaselineTests(unittest.TestCase):
    def test_valid_local_embedded_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / 'previews').mkdir()
            (d / 'previews' / 'dark.png').write_bytes(b'png-placeholder')
            f = d / 'APPROVED_VISUAL_BASELINE.md'
            f.write_text('# G1 approved baseline\nG2 not approved\n![Dark variant](previews/dark.png)\n', encoding='utf-8')
            errors, warnings = visual.validate_baseline(f, approved=True)
            self.assertEqual((errors, warnings), ([], []))

    def test_broken_image_and_unapproved_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'APPROVED_VISUAL_BASELINE.md'
            f.write_text('# G1 approved\n![A](previews/missing.png)\n{{SOURCE}}\n', encoding='utf-8')
            errors, _ = visual.validate_baseline(f, approved=True)
            self.assertTrue(any('Broken preview' in s for s in errors))
            self.assertTrue(any('placeholders' in s for s in errors))
            self.assertTrue(any('G2' in s for s in errors))

    def test_text_link_or_code_span_does_not_count_as_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'docs.md'
            f.write_text('[Image](previews/a.png)\n`![Preview](previews/a.png)`', encoding='utf-8')
            # Inline code is not a renderable image. The validator must detect lack of real embed.
            errors,_=visual.validate_baseline(f)
            self.assertTrue(any('No embedded' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
