from pathlib import Path
import tempfile
import unittest

from praxis.decisions import (
    create_decision,
    decision_blocked_scopes,
    get_decisions,
    list_decisions,
    list_open_decisions,
    select_decision,
)
from praxis.state import enable_state, load_state
from praxis.tasks import create_task, update_task


class DecisionQueryTests(unittest.TestCase):
    def make_tasks(self, root: Path) -> tuple[str, str]:
        enable_state(root)
        first, state = create_task(root, 0, host="codex", title="A")
        second, _ = create_task(root, state["revision"], host="dsh", title="B")
        return first, second

    def test_open_decisions_are_queryable_globally_and_by_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_task, second_task = self.make_tasks(root)
            first_id, _ = create_decision(root, first_task, "engineering", "A", "A ctx", blocked_scopes=["db", "api"])
            second_id, _ = create_decision(root, second_task, "architectural", "B", "B ctx", blocked_scopes=["api", "deploy"])
            state = load_state(root)
            self.assertEqual(set(list_open_decisions(state)), {first_id, second_id})
            self.assertEqual(set(list_open_decisions(state, task_id=first_task)), {first_id})
            self.assertEqual(decision_blocked_scopes(state), ["api", "db", "deploy"])
            self.assertEqual(decision_blocked_scopes(state, task_id=first_task), ["api", "db"])

    def test_non_open_decisions_are_not_unresolved_and_queries_are_deep_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id, _ = self.make_tasks(root)
            decision_id, _ = create_decision(root, task_id, "engineering", "A", "ctx")
            selected = select_decision(root, decision_id, 0, "Use A")
            self.assertEqual(list_open_decisions(selected, task_id=task_id), {})
            copied = list_decisions(selected, task_id=task_id)
            copied[decision_id]["title"] = "mutated"
            self.assertEqual(get_decisions(selected)["records"][decision_id]["title"], "A")

    def test_pending_choices_do_not_create_or_resolve_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id, _ = self.make_tasks(root)
            current = load_state(root)
            with_pending = update_task(root, current["revision"], task_id, pending_choices=["legacy-choice"])
            self.assertEqual(list_open_decisions(with_pending, task_id=task_id), {})
            decision_id, state = create_decision(root, task_id, "engineering", "Storage", "ctx")
            changed = update_task(root, state["revision"], task_id, pending_choices=[])
            self.assertIn(decision_id, list_open_decisions(changed, task_id=task_id))

    def test_completing_task_does_not_implicitly_mutate_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id, _ = self.make_tasks(root)
            decision_id, state = create_decision(root, task_id, "engineering", "Storage", "ctx")
            before = get_decisions(state)
            completed = update_task(root, state["revision"], task_id, stage="complete", status="complete")
            self.assertEqual(get_decisions(completed), before)
            self.assertIn(decision_id, list_open_decisions(completed, task_id=task_id))


if __name__ == "__main__":
    unittest.main()
