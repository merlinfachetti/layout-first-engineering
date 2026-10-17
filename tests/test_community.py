"""Community-governance structure tests. Do not imply legal or security certification."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CommunityChecks(unittest.TestCase):
    def test_community_health_files_exist(self):
        needed = [
            'LICENSE', 'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'GOVERNANCE.md',
            'PRIVACY.md', 'SECURITY.md', 'SUPPORT.md', 'ACCESSIBILITY.md', 'ROADMAP.md',
            '.github/CODEOWNERS', '.github/PULL_REQUEST_TEMPLATE.md',
            '.github/ISSUE_TEMPLATE/bug_report.md',
            '.github/ISSUE_TEMPLATE/feature_request.md',
            '.github/ISSUE_TEMPLATE/compatibility.md',
            '.github/ISSUE_TEMPLATE/config.yml',
            'docs/OPEN-SOURCE-MAINTENANCE.pt-BR.md',
            'docs/OPEN-SOURCE-MAINTENANCE.md',
        ]
        for name in needed:
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file(), name)
                self.assertGreater((ROOT / name).stat().st_size, 20 if name == ".github/CODEOWNERS" else 120, name)

    def test_ci_minimum_permissions_and_prs(self):
        yml = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertIn('pull_request:', yml)
        self.assertIn('contents: read', yml)
        self.assertNotIn('pull_request_target:', yml)
        self.assertNotIn('contents: write', yml)

    def test_privacy_warning_and_licensing(self):
        self.assertIn('MIT License', (ROOT / 'LICENSE').read_text())
        privacy = (ROOT / 'PRIVACY.md').read_text()
        self.assertIn('not a legal opinion', privacy)
        security = (ROOT / 'SECURITY.md').read_text()
        self.assertIn('Do not post exploit details', security)

    def test_no_main_push_in_update_scripts(self):
        script = (ROOT / 'scripts/update-community-macos.sh').read_text()
        self.assertIn('git switch -c "$BRANCH"', script)
        self.assertIn('gh pr create', script)
        self.assertNotIn('git push origin main', script)
        legacy = (ROOT / 'scripts/push-update-macos.sh').read_text()
        self.assertIn("!= 'main'", legacy)
        self.assertNotIn('git push origin main', legacy)

    def test_repo_entrypoints_link_policy(self):
        for name in ('README.md', 'README.pt-BR.md'):
            x=(ROOT/name).read_text()
            for linked in ('GOVERNANCE.md','PRIVACY.md','SECURITY.md','CONTRIBUTING.md'):
                self.assertIn(linked, x, f'{name}: missing {linked}')

if __name__ == '__main__':
    unittest.main()
