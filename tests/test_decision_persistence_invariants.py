import json
from pathlib import Path
import tempfile
import unittest

from praxis.state import InvalidStateError, load_state


class PersistedDecisionLifecycleTests(unittest.TestCase):
    def base_state(self, status: str) -> dict:
        task_id = "task_0123456789abcdef"
        decision_id = "decision_0123456789abcdef"
        return {
            "format_version": 1,
            "revision": 0,
            "enabled": True,
            "tasks": {
                task_id: {
                    "host": "codex",
                    "stage": "design",
                    "status": "active",
                    "pending_choices": [],
                }
            },
            "decisions": {
                "revision": 0,
                "records": {
                    decision_id: {
                        "revision": 0,
                        "task_id": task_id,
                        "class": "engineering",
                        "status": status,
                        "title": "Storage",
                        "context": "Choose storage",
                        "user_proposal": None,
                        "verified_constraints": [],
                        "praxis_challenge": None,
                        "alternatives": [],
                        "selected_decision": None,
                        "user_reasoning": None,
                        "accepted_tradeoffs": [],
                        "blocked_scopes": [],
                        "implementation_result": None,
                        "verification": None,
                        "later_evidence": [],
                    }
                },
            },
        }

    def assert_invalid(self, state: dict) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / ".praxis"
            directory.mkdir()
            path = directory / "state.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(InvalidStateError):
                load_state(root)
            self.assertEqual(path.read_bytes(), before)

    def test_open_record_cannot_already_contain_selected_or_execution_results(self) -> None:
        for field, value in (
            ("selected_decision", "Use Postgres"),
            ("implementation_result", "Implemented"),
            ("verification", "Passed"),
        ):
            with self.subTest(field=field):
                state = self.base_state("open")
                state["decisions"]["records"]["decision_0123456789abcdef"][field] = value
                self.assert_invalid(state)

    def test_selected_requires_selected_decision_and_no_execution_results(self) -> None:
        state = self.base_state("selected")
        self.assert_invalid(state)

        for field, value in (("implementation_result", "Implemented"), ("verification", "Passed")):
            with self.subTest(field=field):
                state = self.base_state("selected")
                record = state["decisions"]["records"]["decision_0123456789abcdef"]
                record["selected_decision"] = "Use Postgres"
                record[field] = value
                self.assert_invalid(state)

    def test_implemented_requires_selection_and_implementation_but_not_verification(self) -> None:
        state = self.base_state("implemented")
        record = state["decisions"]["records"]["decision_0123456789abcdef"]
        record["selected_decision"] = "Use Postgres"
        self.assert_invalid(state)

        state = self.base_state("implemented")
        record = state["decisions"]["records"]["decision_0123456789abcdef"]
        record["selected_decision"] = "Use Postgres"
        record["implementation_result"] = "Implemented"
        record["verification"] = "Passed"
        self.assert_invalid(state)

    def test_verified_requires_selection_implementation_and_verification(self) -> None:
        state = self.base_state("verified")
        record = state["decisions"]["records"]["decision_0123456789abcdef"]
        record["selected_decision"] = "Use Postgres"
        record["implementation_result"] = "Implemented"
        self.assert_invalid(state)

    def test_superseded_requires_existing_distinct_replacement(self) -> None:
        state = self.base_state("superseded")
        self.assert_invalid(state)

        state = self.base_state("superseded")
        record = state["decisions"]["records"]["decision_0123456789abcdef"]
        record["superseding_decision_id"] = "decision_deadbeef"
        self.assert_invalid(state)


if __name__ == "__main__":
    unittest.main()
