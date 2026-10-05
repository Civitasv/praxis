import hashlib
from pathlib import Path
import tempfile
import unittest

from praxis.fingerprints import EvidenceError, capture_evidence, fingerprint_file


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_uses_exact_bytes_and_normalized_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "module.py"
            source.parent.mkdir()
            payload = b"alpha\r\nbeta\n"
            source.write_bytes(payload)

            evidence = fingerprint_file(root, Path("src") / ".." / "src" / "module.py")

            self.assertEqual(evidence["path"], "src/module.py")
            self.assertEqual(evidence["sha256"], hashlib.sha256(payload).hexdigest())

    def test_capture_evidence_is_deduplicated_and_sorted_by_normalized_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z.py").write_text("z", encoding="utf-8")
            (root / "a.py").write_text("a", encoding="utf-8")

            evidence = capture_evidence(root, ["z.py", "a.py", "./z.py"])

            self.assertEqual([item["path"] for item in evidence], ["a.py", "z.py"])

    def test_missing_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EvidenceError):
                fingerprint_file(Path(tmp), "missing.py")

    def test_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            with self.assertRaises(EvidenceError):
                fingerprint_file(root, "src")

    def test_praxis_and_git_internal_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".praxis").mkdir()
            (root / ".praxis" / "state.json").write_text("{}", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("x", encoding="utf-8")

            for relative in (".praxis/state.json", ".git/config"):
                with self.subTest(relative=relative):
                    with self.assertRaises(EvidenceError):
                        fingerprint_file(root, relative)

    def test_absolute_and_parent_escape_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            root = Path(project)
            external = Path(outside) / "external.py"
            external.write_text("outside", encoding="utf-8")

            for candidate in (external, Path("..") / external.name):
                with self.subTest(candidate=str(candidate)):
                    with self.assertRaises(EvidenceError):
                        fingerprint_file(root, candidate)

    def test_symlink_outside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
            root = Path(project)
            external = Path(outside) / "external.py"
            external.write_text("outside", encoding="utf-8")
            link = root / "link.py"
            try:
                link.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")

            with self.assertRaises(EvidenceError):
                fingerprint_file(root, "link.py")

    def test_symlink_to_file_inside_project_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "real.py"
            target.parent.mkdir()
            target.write_bytes(b"inside")
            link = root / "link.py"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")

            evidence = fingerprint_file(root, "link.py")

            self.assertEqual(evidence["path"], "link.py")
            self.assertEqual(evidence["sha256"], hashlib.sha256(b"inside").hexdigest())


if __name__ == "__main__":
    unittest.main()
