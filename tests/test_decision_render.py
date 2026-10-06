from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from praxis.decisions import (
    DecisionRenderError,
    create_decision,
    decisions_status,
    render_decisions,
    select_decision,
)
from praxis.state import enable_state, load_state, mutate_state
from praxis.tasks import create_task


class DecisionRenderTests(unittest.TestCase):
    def make_task(self, root: Path) -> str:
        enable_state(root)
        task_id, _ = create_task(root, 0, host="codex", title="Tutor")
        return task_id

    def test_render_is_stable_sorted_and_keeps_provenance_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            with patch("praxis.decisions.secrets.token_hex", side_effect=["bbbbbbbbbbbbbbbb", "aaaaaaaaaaaaaaaa"]):
                create_decision(root, task_id, "engineering", "Second", "second context")
                first_id, _ = create_decision(
                    root,
                    task_id,
                    "architectural",
                    "First",
                    "first context",
                    user_proposal="Use Redis only",
                    verified_constraints=["History must survive restart"],
                    praxis_challenge="Durability is not guaranteed by default",
                    alternatives=["Database source of truth"],
                    blocked_scopes=["message-storage"],
                )
            select_decision(root, first_id, 0, "Database source of truth")

            path = render_decisions(root)
            text = path.read_text(encoding="utf-8")

            self.assertIn('<!-- praxis:decisions revision="2" -->', text)
            self.assertLess(text.index("## First"), text.index("## Second"))
            self.assertIn(
                f'<!-- praxis:decision id="{first_id}" revision="1" status="selected" class="architectural" task="{task_id}" -->',
                text,
            )
            self.assertIn("### User proposal\nUse Redis only", text)
            self.assertIn("### Praxis challenge\nDurability is not guaranteed by default", text)
            self.assertIn("### Selected decision\nDatabase source of truth", text)
            self.assertIn("### User reasoning\nNot recorded", text)
            self.assertIn("### Implementation result\nNot recorded", text)
            self.assertIn("### Verification\nNot recorded", text)
            self.assertIn("### Later evidence\nNot recorded", text)

    def test_deleted_projection_rebuilds_to_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            create_decision(root, task_id, "engineering", "Storage", "ctx")
            path = render_decisions(root)
            expected = path.read_bytes()
            path.unlink()
            self.assertTrue(decisions_status(root)["render_required"])
            rebuilt = render_decisions(root)
            self.assertEqual(rebuilt.read_bytes(), expected)
            self.assertFalse(decisions_status(root)["render_required"])

    def test_unrelated_state_change_does_not_invalidate_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            create_decision(root, task_id, "engineering", "Storage", "ctx")
            render_decisions(root)
            before = decisions_status(root)
            state = load_state(root)
            mutate_state(root, state["revision"], lambda value: {**value, "future_metadata": {"keep": True}})
            after = decisions_status(root)
            self.assertEqual(after["revision"], before["revision"])
            self.assertFalse(after["render_required"])

    def test_decision_change_marks_projection_out_of_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            decision_id, _ = create_decision(root, task_id, "engineering", "Storage", "ctx")
            render_decisions(root)
            select_decision(root, decision_id, 0, "Use database")
            self.assertTrue(decisions_status(root)["render_required"])

    def test_status_without_state_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status = decisions_status(root)
            self.assertEqual(
                status,
                {
                    "exists": False,
                    "revision": None,
                    "decisions": [],
                    "open_decisions": [],
                    "blocked_scopes": [],
                    "render_required": False,
                },
            )
            self.assertFalse((root / ".praxis").exists())

    def test_unsafe_projection_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            task_id = self.make_task(root)
            create_decision(root, task_id, "engineering", "Storage", "ctx")
            target = Path(outside) / "decisions.md"
            target.write_text("outside", encoding="utf-8")
            (root / ".praxis" / "decisions.md").symlink_to(target)
            with self.assertRaises(DecisionRenderError):
                render_decisions(root)

    def test_replace_failure_preserves_state_and_previous_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            decision_id, _ = create_decision(root, task_id, "engineering", "Storage", "ctx")
            path = render_decisions(root)
            before_projection = path.read_bytes()
            select_decision(root, decision_id, 0, "Use database")
            before_state = (root / ".praxis" / "state.json").read_bytes()
            with patch("praxis.decisions.os.replace", side_effect=OSError("boom")):
                with self.assertRaises(DecisionRenderError):
                    render_decisions(root)
            self.assertEqual(path.read_bytes(), before_projection)
            self.assertEqual((root / ".praxis" / "state.json").read_bytes(), before_state)


if __name__ == "__main__":
    unittest.main()
