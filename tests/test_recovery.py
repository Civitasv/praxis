from pathlib import Path
import tempfile
import unittest

from praxis.decisions import create_decision, select_decision
from praxis.project_map import upsert_section
from praxis.recovery import recovery_status
from praxis.state import enable_state, load_state, pause_state
from praxis.tasks import create_task


class RecoveryStatusTests(unittest.TestCase):
    def test_uninitialized_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(snapshot["initialized"], False)
            self.assertEqual(snapshot["enabled"], False)
            self.assertIsNone(snapshot["revision"])
            self.assertEqual(snapshot["task_resolution"], {"kind": "none", "task": None, "candidates": []})
            self.assertEqual(snapshot["open_decisions"], [])
            self.assertEqual(snapshot["blocked_scopes"], [])
            self.assertEqual(snapshot["project_model"], {"stale_sections": [], "unknown_sections": []})
            self.assertFalse((root / ".praxis").exists())

    def test_paused_state_is_not_refreshed_or_mutated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            paused = pause_state(root, 0)
            state_path = root / ".praxis" / "state.json"
            before = state_path.read_bytes()
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertTrue(snapshot["initialized"])
            self.assertFalse(snapshot["enabled"])
            self.assertEqual(snapshot["revision"], paused["revision"])
            self.assertEqual(state_path.read_bytes(), before)

    def test_exact_dsh_task_wins_and_open_decisions_are_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            exact_id, state = create_task(
                root,
                0,
                host="dsh",
                conversation_id="session-1",
                title="Auth",
            )
            other_id, _ = create_task(root, state["revision"], host="codex", title="Billing")
            decision_id, _ = create_decision(
                root,
                exact_id,
                "architectural",
                "Session ownership",
                "Choose ownership.",
                blocked_scopes=["session-persistence"],
            )
            unrelated_id, _ = create_decision(
                root,
                other_id,
                "engineering",
                "Retry",
                "Choose retry.",
                blocked_scopes=["billing-retry"],
            )
            before_tasks = load_state(root)["tasks"]
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(snapshot["task_resolution"]["kind"], "exact")
            self.assertEqual(snapshot["task_resolution"]["task"]["id"], exact_id)
            self.assertEqual(snapshot["task_resolution"]["candidates"], [])
            self.assertEqual([item["id"] for item in snapshot["open_decisions"]], [decision_id])
            self.assertEqual(snapshot["blocked_scopes"], ["session-persistence"])
            self.assertNotIn(unrelated_id, str(snapshot))
            self.assertNotIn("billing-retry", str(snapshot))
            self.assertEqual(load_state(root)["tasks"], before_tasks)

    def test_multiple_exact_tasks_remain_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first, state = create_task(root, 0, host="dsh", conversation_id="session-1", title="First")
            second, _ = create_task(root, state["revision"], host="dsh", conversation_id="session-1", title="Second")
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(snapshot["task_resolution"]["kind"], "exact_ambiguous")
            self.assertIsNone(snapshot["task_resolution"]["task"])
            self.assertEqual(
                [item["id"] for item in snapshot["task_resolution"]["candidates"]],
                sorted([first, second]),
            )
            self.assertEqual(snapshot["open_decisions"], [])
            self.assertEqual(snapshot["blocked_scopes"], [])

    def test_unmatched_tasks_become_candidate_or_ambiguous_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            only, state = create_task(root, 0, host="codex", title="Carry over")
            one = recovery_status(root, host="dsh", conversation_id="new-session")
            self.assertEqual(one["task_resolution"]["kind"], "candidate")
            self.assertEqual(one["task_resolution"]["task"]["id"], only)

            second, _ = create_task(root, state["revision"], host="dsh", title="Second")
            many = recovery_status(root, host="dsh", conversation_id="new-session")
            self.assertEqual(many["task_resolution"]["kind"], "candidate_ambiguous")
            self.assertIsNone(many["task_resolution"]["task"])
            self.assertEqual(
                [item["id"] for item in many["task_resolution"]["candidates"]],
                sorted([only, second]),
            )

    def test_selected_decision_is_not_reported_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(root, 0, host="dsh", conversation_id="session-1")
            decision_id, _ = create_decision(root, task_id, "engineering", "Storage", "Choose")
            select_decision(root, decision_id, 0, "Use database")
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(snapshot["open_decisions"], [])
            self.assertEqual(snapshot["blocked_scopes"], [])

    def test_refresh_surfaces_stale_and_unknown_sections_without_auto_clearing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            upsert_section(root, "unknown", "Unknown", "Need inspection.", [])
            evidence.write_text("v2", encoding="utf-8")
            snapshot = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(snapshot["project_model"]["stale_sections"], ["auth"])
            self.assertEqual(snapshot["project_model"]["unknown_sections"], ["unknown"])

            evidence.write_text("v1", encoding="utf-8")
            again = recovery_status(root, host="dsh", conversation_id="session-1")
            self.assertEqual(again["project_model"]["stale_sections"], ["auth"])


if __name__ == "__main__":
    unittest.main()
