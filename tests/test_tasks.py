from pathlib import Path
import tempfile
import unittest

from praxis.state import RevisionConflictError, enable_state, load_state
from praxis.tasks import InvalidTaskError, create_task, pending_tasks, update_task


class TaskLifecycleTests(unittest.TestCase):
    def test_create_task_generates_core_id_and_associations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(root, 0, host="codex", conversation_id="chat-1", title="Auth design")
            self.assertRegex(task_id, r"^task_[0-9a-f]+$")
            self.assertEqual(state["revision"], 1)
            self.assertEqual(state["tasks"][task_id], {
                "host": "codex",
                "conversation_id": "chat-1",
                "stage": "understanding",
                "status": "active",
                "pending_choices": [],
                "title": "Auth design",
            })

    def test_create_task_omits_optional_fields_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(root, 0, host="dsh")
            task = state["tasks"][task_id]
            self.assertNotIn("conversation_id", task)
            self.assertNotIn("title", task)

    def test_invalid_stage_and_status_are_rejected_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(root, 0, host="codex")
            before = (root / ".praxis" / "state.json").read_bytes()
            with self.assertRaises(InvalidTaskError):
                update_task(root, state["revision"], task_id, stage="invented")
            with self.assertRaises(InvalidTaskError):
                update_task(root, state["revision"], task_id, status="invented")
            self.assertEqual((root / ".praxis" / "state.json").read_bytes(), before)

    def test_update_task_changes_only_named_task_and_preserves_other_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first_id, state = create_task(root, 0, host="codex", title="Auth")
            second_id, state = create_task(root, state["revision"], host="dsh", title="Billing")
            second_before = dict(state["tasks"][second_id])
            updated = update_task(root, state["revision"], first_id, stage="awaiting_decision", pending_choices=["storage", "session-policy"])
            self.assertEqual(updated["tasks"][first_id]["stage"], "awaiting_decision")
            self.assertEqual(updated["tasks"][first_id]["pending_choices"], ["storage", "session-policy"])
            self.assertEqual(updated["tasks"][second_id], second_before)

    def test_completing_one_task_does_not_complete_other_and_filters_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first_id, state = create_task(root, 0, host="codex")
            second_id, state = create_task(root, state["revision"], host="dsh")
            updated = update_task(root, state["revision"], first_id, stage="complete", status="complete", pending_choices=[])
            pending = pending_tasks(updated)
            self.assertNotIn(first_id, pending)
            self.assertIn(second_id, pending)
            self.assertEqual(updated["tasks"][second_id]["status"], "active")

    def test_stale_revision_cannot_update_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(root, 0, host="codex")
            with self.assertRaises(RevisionConflictError):
                update_task(root, 0, task_id, stage="design")
            self.assertEqual(load_state(root)["revision"], state["revision"])

    def test_pending_choices_must_be_strings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(root, 0, host="codex")
            with self.assertRaises(InvalidTaskError):
                update_task(root, state["revision"], task_id, pending_choices=["ok", 3])


if __name__ == "__main__":
    unittest.main()
