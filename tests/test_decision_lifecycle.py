from pathlib import Path
import tempfile
import unittest

from praxis.decisions import (
    DecisionConflictError,
    InvalidDecisionTransitionError,
    abandon_decision,
    add_later_evidence,
    create_decision,
    get_decision,
    record_implementation,
    record_verification,
    select_decision,
    supersede_decision,
)
from praxis.state import enable_state, load_state
from praxis.tasks import create_task


class DecisionLifecycleTests(unittest.TestCase):
    def make_task(self, root: Path) -> str:
        enable_state(root)
        task_id, _ = create_task(root, 0, host="codex")
        return task_id

    def make_decision(self, root: Path, task_id: str, title: str = "Storage") -> tuple[str, dict]:
        return create_decision(root, task_id, "engineering", title, "Choose storage boundary")

    def test_primary_lifecycle_keeps_states_distinct_and_revisions_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            decision_id, created = self.make_decision(root, task_id)
            self.assertEqual(created["decisions"]["revision"], 0)

            selected = select_decision(root, decision_id, 0, "Database source of truth", user_reasoning="Need durable history", accepted_tradeoffs=["extra dependency"])
            record = get_decision(selected, decision_id)
            self.assertEqual((record["status"], record["revision"]), ("selected", 1))
            self.assertEqual(selected["decisions"]["revision"], 1)
            self.assertEqual(record["user_reasoning"], "Need durable history")

            implemented = record_implementation(root, decision_id, 1, "Postgres owns messages; Redis handles fanout")
            record = get_decision(implemented, decision_id)
            self.assertEqual((record["status"], record["revision"]), ("implemented", 2))
            self.assertIsNone(record["verification"])

            verified = record_verification(root, decision_id, 2, "Redis restart preserved message history")
            record = get_decision(verified, decision_id)
            self.assertEqual((record["status"], record["revision"]), ("verified", 3))
            self.assertEqual(record["verification"], "Redis restart preserved message history")
            self.assertEqual(verified["decisions"]["revision"], 3)

    def test_selection_never_copies_ai_reasoning_into_user_reasoning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            decision_id, _ = create_decision(root, task_id, "engineering", "Storage", "Context", praxis_challenge="Praxis says use Postgres")
            selected = select_decision(root, decision_id, 0, "Use Postgres")
            record = get_decision(selected, decision_id)
            self.assertIsNone(record["user_reasoning"])
            self.assertEqual(record["praxis_challenge"], "Praxis says use Postgres")

    def test_invalid_transitions_and_terminal_states_do_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            decision_id, _ = self.make_decision(root, task_id)
            state_path = root / ".praxis" / "state.json"
            before = state_path.read_bytes()
            with self.assertRaises(InvalidDecisionTransitionError):
                record_implementation(root, decision_id, 0, "too early")
            self.assertEqual(state_path.read_bytes(), before)

            abandoned = abandon_decision(root, decision_id, 0)
            self.assertEqual(get_decision(abandoned, decision_id)["status"], "abandoned")
            before = state_path.read_bytes()
            with self.assertRaises(InvalidDecisionTransitionError):
                select_decision(root, decision_id, 1, "cannot reopen")
            self.assertEqual(state_path.read_bytes(), before)

    def test_unrelated_decisions_can_progress_after_global_revision_moves_but_same_decision_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            first_id, _ = self.make_decision(root, task_id, "First")
            second_id, _ = self.make_decision(root, task_id, "Second")
            first = select_decision(root, first_id, 0, "A")
            second = select_decision(root, second_id, 0, "B")
            self.assertEqual(get_decision(first, first_id)["revision"], 1)
            self.assertEqual(get_decision(second, second_id)["revision"], 1)
            before = (root / ".praxis" / "state.json").read_bytes()
            with self.assertRaises(DecisionConflictError):
                select_decision(root, first_id, 0, "stale")
            self.assertEqual((root / ".praxis" / "state.json").read_bytes(), before)

    def test_supersede_abandon_and_later_evidence_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            old_id, _ = self.make_decision(root, task_id, "Old")
            new_id, _ = self.make_decision(root, task_id, "New")
            superseded = supersede_decision(root, old_id, 0, new_id)
            self.assertEqual(get_decision(superseded, old_id)["status"], "superseded")
            self.assertEqual(get_decision(superseded, old_id)["superseding_decision_id"], new_id)

            selected = select_decision(root, new_id, 0, "Use new")
            evidenced = add_later_evidence(root, new_id, 1, "Production latency increased 10%")
            self.assertEqual(get_decision(evidenced, new_id)["later_evidence"], ["Production latency increased 10%"])
            before_revision = evidenced["revision"]
            before = (root / ".praxis" / "state.json").read_bytes()
            duplicate = add_later_evidence(root, new_id, 2, "Production latency increased 10%")
            self.assertEqual(duplicate["revision"], before_revision)
            self.assertEqual((root / ".praxis" / "state.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
