from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.zb_execution_workspace import (
    SubprocessCommand,
    WorkspaceError,
    audit_workspace,
    create_detached_worktree,
    remove_worktree,
)


def git(*args: str, cwd: Path) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def init_repo(root: Path) -> str:
    git("init", cwd=root)
    git("config", "user.email", "zb-tests@example.invalid", cwd=root)
    git("config", "user.name", "ZB Tests", cwd=root)
    (root / "scripts").mkdir()
    (root / "scripts" / "fixture.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
    git("add", ".", cwd=root)
    git("commit", "-m", "base", cwd=root)
    return git("rev-parse", "HEAD", cwd=root)


class WorkspaceTests(unittest.TestCase):
    def test_create_detached_worktree_at_exact_base_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            worktree = Path(tmp) / "worktree"
            command = SubprocessCommand()

            create_detached_worktree(root, base_sha, worktree, command)
            self.assertTrue(worktree.is_dir())
            self.assertEqual(git("rev-parse", "HEAD", cwd=worktree), base_sha)
            self.assertEqual(git("symbolic-ref", "-q", "--short", "HEAD", cwd=worktree), "")

            remove_worktree(root, worktree, command)
            self.assertFalse(worktree.exists())

    def test_dirty_source_checkout_is_rejected_before_worktree_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            (root / "scripts" / "fixture.py").write_text("DIRTY = True\n", encoding="utf-8")
            with self.assertRaisesRegex(WorkspaceError, "SOURCE_CHECKOUT_DIRTY"):
                create_detached_worktree(root, base_sha, Path(tmp) / "worktree", SubprocessCommand())

    def test_audit_collects_changed_files_and_stable_patch_hash_without_moving_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            worktree = Path(tmp) / "worktree"
            command = SubprocessCommand()
            create_detached_worktree(root, base_sha, worktree, command)
            try:
                (worktree / "scripts" / "fixture.py").write_text("VALUE = 2\n", encoding="utf-8")
                first = audit_workspace(worktree, ("scripts/",), command)
                second = audit_workspace(worktree, ("scripts/",), command)
                self.assertEqual(first.start_head, base_sha)
                self.assertEqual(first.end_head, base_sha)
                self.assertEqual(first.changed_files, ("scripts/fixture.py",))
                self.assertEqual(first.patch_sha256, second.patch_sha256)
                self.assertRegex(first.patch_sha256, r"^[0-9a-f]{64}$")
            finally:
                remove_worktree(root, worktree, command)

    def test_audit_detects_binary_patch_stably(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            worktree = Path(tmp) / "worktree"
            command = SubprocessCommand()
            create_detached_worktree(root, base_sha, worktree, command)
            try:
                (worktree / "binary.bin").write_bytes(b"\x00\xff\x10\x11\x12")
                first = audit_workspace(worktree, ("binary.bin",), command)
                second = audit_workspace(worktree, ("binary.bin",), command)
                self.assertEqual(first.changed_files, ("binary.bin",))
                self.assertEqual(first.patch_sha256, second.patch_sha256)
            finally:
                remove_worktree(root, worktree, command)

    def test_audit_rejects_disallowed_changed_file_and_path_escape_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            worktree = Path(tmp) / "worktree"
            command = SubprocessCommand()
            create_detached_worktree(root, base_sha, worktree, command)
            try:
                (worktree / "binary.bin").write_bytes(b"changed")
                with self.assertRaisesRegex(WorkspaceError, "WRITE_SCOPE_VIOLATION"):
                    audit_workspace(worktree, ("scripts/",), command)
                with self.assertRaisesRegex(WorkspaceError, "INVALID_WRITE_SCOPE"):
                    audit_workspace(worktree, ("../",), command)
                with self.assertRaisesRegex(WorkspaceError, "INVALID_WRITE_SCOPE"):
                    audit_workspace(worktree, ("/absolute",), command)
            finally:
                remove_worktree(root, worktree, command)

    def test_audit_rejects_committed_head_movement_when_expected_base_is_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base_sha = init_repo(root)
            worktree = Path(tmp) / "worktree"
            command = SubprocessCommand()
            create_detached_worktree(root, base_sha, worktree, command)
            try:
                (worktree / "scripts" / "fixture.py").write_text("VALUE = 9\n", encoding="utf-8")
                git("add", ".", cwd=worktree)
                git("-c", "user.email=zb-tests@example.invalid", "-c", "user.name=ZB Tests", "commit", "-m", "forbidden", cwd=worktree)
                with self.assertRaisesRegex(WorkspaceError, "HEAD_MOVED"):
                    audit_workspace(worktree, ("scripts/",), command, expected_base_sha=base_sha)
            finally:
                remove_worktree(root, worktree, command)


if __name__ == "__main__":
    unittest.main()
