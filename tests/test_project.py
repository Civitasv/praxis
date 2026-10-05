from pathlib import Path
import tempfile
import unittest

from praxis.project import (
    UnsafeStatePathError,
    discover_project_root,
    state_directory,
    state_file,
)


class ProjectBoundaryTests(unittest.TestCase):
    def test_nearest_git_directory_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = root / "parent"
            child = parent / "child"
            nested = child / "src" / "pkg"
            (parent / ".git").mkdir(parents=True)
            (child / ".git").mkdir(parents=True)
            nested.mkdir(parents=True)
            self.assertEqual(discover_project_root(nested), child.resolve())

    def test_git_file_marks_worktree_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktree = root / "worktree"
            nested = worktree / "src"
            nested.mkdir(parents=True)
            (worktree / ".git").write_text("gitdir: ../git/worktrees/x\n", encoding="utf-8")
            self.assertEqual(discover_project_root(nested), worktree.resolve())

    def test_git_symlink_marker_is_boundary_without_following_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            nested = repo / "src"
            nested.mkdir(parents=True)
            (repo / ".git").symlink_to(root / "outside-git")
            self.assertEqual(discover_project_root(nested), repo.resolve())

    def test_no_git_uses_supplied_cwd_not_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "plain" / "nested"
            cwd.mkdir(parents=True)
            self.assertEqual(discover_project_root(cwd), cwd.resolve())

    def test_symlinked_state_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            (root / ".praxis").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(UnsafeStatePathError):
                state_directory(root)

    def test_symlinked_state_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".praxis"
            state_dir.mkdir()
            outside = root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            (state_dir / "state.json").symlink_to(outside)
            with self.assertRaises(UnsafeStatePathError):
                state_file(root)


if __name__ == "__main__":
    unittest.main()
