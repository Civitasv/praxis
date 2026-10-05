import json
from pathlib import Path
import tempfile
import unittest

from praxis.state import (
    FORMAT_VERSION,
    InvalidStateError,
    MalformedStateError,
    RevisionConflictError,
    UnsupportedFormatError,
    enable_state,
    load_state,
)


class StateSchemaTests(unittest.TestCase):
    def test_absent_state_loads_none_without_creating_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(load_state(root))
            self.assertFalse((root / ".praxis").exists())

    def test_first_enable_initializes_format_one_at_revision_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = enable_state(root)
            self.assertEqual(
                state,
                {"format_version": FORMAT_VERSION, "revision": 0, "enabled": True, "tasks": {}},
            )
            self.assertEqual(load_state(root), state)

    def test_malformed_json_is_preserved_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            original = b"{not-json\n"
            path.write_bytes(original)
            with self.assertRaises(MalformedStateError):
                load_state(root)
            with self.assertRaises(MalformedStateError):
                enable_state(root)
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            (directory / "state.json").write_text(
                json.dumps({"format_version": 1, "revision": -1, "enabled": True, "tasks": {}}),
                encoding="utf-8",
            )
            with self.assertRaises(InvalidStateError):
                load_state(root)

    def test_unsupported_format_is_preserved_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            original = json.dumps({"format_version": 2, "revision": 0, "enabled": True, "tasks": {}})
            path.write_text(original, encoding="utf-8")
            with self.assertRaises(UnsupportedFormatError):
                enable_state(root)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_reenable_paused_state_requires_matching_revision_and_preserves_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            path.write_text(
                json.dumps({
                    "format_version": 1,
                    "revision": 4,
                    "enabled": False,
                    "tasks": {"task_x": {"status": "active"}},
                    "future_metadata": {"keep": True},
                }),
                encoding="utf-8",
            )
            with self.assertRaises(RevisionConflictError):
                enable_state(root)
            updated = enable_state(root, expected_revision=4)
            self.assertTrue(updated["enabled"])
            self.assertEqual(updated["revision"], 5)
            self.assertEqual(updated["future_metadata"], {"keep": True})
            self.assertEqual(updated["tasks"], {"task_x": {"status": "active"}})


if __name__ == "__main__":
    unittest.main()
