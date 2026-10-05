from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from praxis.decisions import InvalidDecisionError, create_decision, get_decision, get_decisions
from praxis.state import enable_state, load_state, mutate_state
from praxis.tasks import create_task


class DecisionSchemaTests(unittest.TestCase):
    def make_task(self, root: Path) -> str:
        enable_state(root)
        task_id, _ = create_task(root, 0, host="codex", title="Auth")
        return task_id

    def test_first_decision_creates_authoritative_aggregate_and_core_owned_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            with patch("praxis.decisions.secrets.token_hex", return_value="0123456789abcdef"):
                decision_id, state = create_decision(
                    root,
                    task_id,
                    "engineering",
                    "Session storage",
                    "Choose durable session ownership.",
                    user_proposal="Use Redis only.",
                    verified_constraints=["Sessions must survive Redis restart."],
                    praxis_challenge="Redis-only durability needs explicit guarantees.",
                    alternatives=["Database source of truth", "Redis persistence"],
                    blocked_scopes=["session-persistence"],
                )
            self.assertEqual(decision_id, "decision_0123456789abcdef")
            self.assertEqual(state["decisions"]["revision"], 0)
            record = state["decisions"]["records"][decision_id]
            self.assertEqual(record["revision"], 0)
            self.assertEqual(record["task_id"], task_id)
            self.assertEqual(record["class"], "engineering")
            self.assertEqual(record["status"], "open")
            self.assertEqual(record["selected_decision"], None)
            self.assertEqual(record["user_reasoning"], None)
            self.assertEqual(record["accepted_tradeoffs"], [])
            self.assertEqual(record["implementation_result"], None)
            self.assertEqual(record["verification"], None)
            self.assertEqual(record["later_evidence"], [])
            self.assertEqual(get_decision(state, decision_id), record)
            self.assertEqual(get_decisions(state)["records"][decision_id], record)

    def test_unknown_task_and_mechanical_decision_are_rejected_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_task(root)
            path = root / ".praxis" / "state.json"
            before = path.read_bytes()
            with self.assertRaises(InvalidDecisionError):
                create_decision(root, "task_deadbeef", "engineering", "X", "Y")
            with self.assertRaises(InvalidDecisionError):
                create_decision(root, next(iter(load_state(root)["tasks"])), "mechanical", "X", "Y")
            self.assertEqual(path.read_bytes(), before)

    def test_invalid_semantic_payload_is_rejected_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            path = root / ".praxis" / "state.json"
            before = path.read_bytes()
            with self.assertRaises(InvalidDecisionError):
                create_decision(root, task_id, "engineering", "", "context")
            with self.assertRaises(InvalidDecisionError):
                create_decision(root, task_id, "engineering", "Title", "context", alternatives=[""])
            self.assertEqual(path.read_bytes(), before)

    def test_creation_preserves_other_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_id = self.make_task(root)
            current = load_state(root)
            current = mutate_state(root, current["revision"], lambda state: {**state, "project_model": {"revision": 0, "sections": {}}, "future_metadata": {"keep": True}})
            decision_id, updated = create_decision(root, task_id, "architectural", "Boundary", "Choose boundary")
            self.assertIn(task_id, updated["tasks"])
            self.assertEqual(updated["project_model"], {"revision": 0, "sections": {}})
            self.assertEqual(updated["future_metadata"], {"keep": True})
            self.assertIn(decision_id, updated["decisions"]["records"])


if __name__ == "__main__":
    unittest.main()
