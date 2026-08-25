import tempfile
import unittest
from pathlib import Path

from hq_pr_scope import classify


class PullRequestScopeTest(unittest.TestCase):
    def roots(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        base, head = root / "base", root / "head"
        base.mkdir()
        head.mkdir()
        return temp, base, head

    def write(self, root: Path, relative: str, value: str):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def test_code_only_pr_is_not_a_state_transition(self):
        temp, base, head = self.roots()
        with temp:
            self.write(base, "scripts/tool.py", "old")
            self.write(head, "scripts/tool.py", "new")
            self.assertFalse(classify(base, head, "transition"))
            self.assertFalse(classify(base, head, "artifact"))

    def test_task_or_record_change_is_classified(self):
        temp, base, head = self.roots()
        with temp:
            self.write(base, "hq/tasks/GITHUB_SHARED_HQ.json", "{}")
            self.write(head, "hq/tasks/GITHUB_SHARED_HQ.json", "{\"revision\":1}")
            self.assertTrue(classify(base, head, "transition"))
            self.assertTrue(classify(base, head, "artifact"))

    def test_git_metadata_is_ignored(self):
        temp, base, head = self.roots()
        with temp:
            self.write(base, ".git/HEAD", "base")
            self.write(head, ".git/HEAD", "head")
            self.assertFalse(classify(base, head, "transition"))


if __name__ == "__main__":
    unittest.main()
