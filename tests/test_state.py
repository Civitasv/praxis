import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import praxis.state as state_module
from praxis.state import (
    FORMAT_VERSION,
    InvalidStateError,
    MalformedStateError,
    RevisionConflictError,
    StateWriteError,
    UnsupportedFormatError,
    enable_state,
    load_state,
    mutate_state,
    pause_state,
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

    def test_state_read_failure_is_reported_separately_and_preserves_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            original = json.dumps({
                "format_version": 1,
                "revision": 0,
                "enabled": True,
                "tasks": {},
            }).encode("utf-8")
            path.write_bytes(original)
            with patch("pathlib.Path.read_text", side_effect=PermissionError("denied")):
                with self.assertRaises(state_module.StateReadError):
                    load_state(root)
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

    def test_invalid_persisted_task_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            (directory / "state.json").write_text(
                json.dumps({
                    "format_version": 1,
                    "revision": 0,
                    "enabled": True,
                    "tasks": {"task_deadbeef": {"status": "active"}},
                }),
                encoding="utf-8",
            )
            with self.assertRaises(InvalidStateError):
                load_state(root)

    def test_invalid_persisted_decision_record_is_rejected_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            original = json.dumps({
                "format_version": 1,
                "revision": 0,
                "enabled": True,
                "tasks": {},
                "decisions": {"revision": 0, "records": {"decision_deadbeef": {"status": "open"}}},
            }).encode("utf-8")
            path.write_bytes(original)
            with self.assertRaises(InvalidStateError):
                load_state(root)
            self.assertEqual(path.read_bytes(), original)

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
                    "tasks": {
                        "task_0123456789abcdef": {
                            "host": "codex",
                            "stage": "understanding",
                            "status": "active",
                            "pending_choices": [],
                        }
                    },
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


class StateMutationTests(unittest.TestCase):
    def test_stale_revision_conflict_preserves_newer_state_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first = mutate_state(root, 0, lambda state: {**state, "marker": "new"})
            self.assertEqual(first["revision"], 1)
            path = root / ".praxis" / "state.json"
            before = path.read_bytes()
            with self.assertRaises(RevisionConflictError):
                mutate_state(root, 0, lambda state: {**state, "marker": "stale"})
            self.assertEqual(path.read_bytes(), before)

    def test_pause_preserves_tasks_and_unknown_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            enriched = mutate_state(
                root,
                0,
                lambda state: {
                    **state,
                    "tasks": {
                        "task_a": {
                            "host": "codex",
                            "stage": "understanding",
                            "status": "active",
                            "pending_choices": ["db"],
                        }
                    },
                    "future_metadata": {"keep": True},
                },
            )
            paused = pause_state(root, enriched["revision"])
            self.assertFalse(paused["enabled"])
            self.assertEqual(paused["revision"], 2)
            self.assertEqual(paused["tasks"], enriched["tasks"])
            self.assertEqual(paused["future_metadata"], {"keep": True})

    def test_successful_mutation_increments_revision_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            updated = mutate_state(root, 0, lambda state: {**state, "marker": 1})
            self.assertEqual(updated["revision"], 1)
            self.assertEqual(load_state(root)["revision"], 1)

    def test_replace_failure_preserves_previous_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            path = root / ".praxis" / "state.json"
            before = path.read_bytes()
            with patch("praxis.state.os.replace", side_effect=OSError("boom")):
                with self.assertRaises(StateWriteError):
                    mutate_state(root, 0, lambda state: {**state, "marker": "never"})
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(load_state(root)["revision"], 0)


if __name__ == "__main__":
    unittest.main()
