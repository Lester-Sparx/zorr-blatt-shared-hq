from __future__ import annotations

from pathlib import Path
import re
import unittest


WORKFLOW_ROOT = Path('.github/workflows')
ISSUE_WRITE = re.compile(r'(?m)^\s*issues:\s*write\s*$')
TRUSTED_ISSUE_WRITERS = {
    'zb-communication-base.yml',
    'zb-communication-r02b.yml',
    'zb-communication-r02b-v2.yml',
}


class StateWriterCapabilitySurfaceTests(unittest.TestCase):
    @staticmethod
    def workflow_text(path: Path) -> str:
        return path.read_text(encoding='utf-8')

    def issue_write_workflows(self) -> set[str]:
        return {
            path.name
            for path in WORKFLOW_ROOT.glob('*.yml')
            if ISSUE_WRITE.search(self.workflow_text(path))
        }

    def test_issue_write_capability_is_closed_to_exact_existing_transport_set(self) -> None:
        self.assertEqual(self.issue_write_workflows(), TRUSTED_ISSUE_WRITERS)

    def test_issue_write_workflows_are_issue_comment_only_not_pull_request_target(self) -> None:
        for name in sorted(TRUSTED_ISSUE_WRITERS):
            with self.subTest(workflow=name):
                text = self.workflow_text(WORKFLOW_ROOT / name)
                self.assertIn('issue_comment:', text)
                self.assertNotIn('pull_request_target:', text)
                self.assertIn("github.event.comment.user.login == 'Lester-Sparx'", text)

    def test_issue_write_workflows_pin_checkout_and_disable_persisted_credentials(self) -> None:
        pinned_checkout = 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262'
        for name in sorted(TRUSTED_ISSUE_WRITERS):
            with self.subTest(workflow=name):
                text = self.workflow_text(WORKFLOW_ROOT / name)
                self.assertIn(pinned_checkout, text)
                self.assertIn('persist-credentials: false', text)


if __name__ == '__main__':
    unittest.main()
