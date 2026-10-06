from pathlib import Path
import tempfile
import unittest

from plugins.codex.hooks.praxis_context import build_context
from praxis.decisions import create_decision, record_implementation, record_verification, select_decision
from praxis.project_map import project_model_status, upsert_section
from praxis.state import enable_state, load_state
from praxis.tasks import create_task


class CodexRecoveryTests(unittest.TestCase):
    def event(self, root: Path, *, source: str = "startup", session_id: str = "session-1") -> dict[str, object]:
        return {
            "hook_event_name": "SessionStart",
            "cwd": str(root),
            "session_id": session_id,
            "source": source,
        }

    def test_all_session_start_sources_produce_enabled_context(self) -> None:
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                enable_state(root)
                context = build_context(self.event(root, source=source))
                self.assertIn("Praxis is enabled", context)

    def test_exact_codex_session_task_is_recovered_without_task_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(
                root,
                0,
                host="codex",
                conversation_id="session-1",
                title="Authentication",
            )
            before_tasks = load_state(root)["tasks"]
            context = build_context(self.event(root))
            self.assertIn("Recovered task", context)
            self.assertIn(task_id, context)
            self.assertIn("Authentication", context)
            self.assertEqual(load_state(root)["tasks"], before_tasks)
            self.assertEqual(load_state(root)["revision"], state["revision"])

    def test_multiple_exact_session_tasks_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first, state = create_task(root, 0, host="codex", conversation_id="session-1", title="First")
            second, _ = create_task(
                root,
                state["revision"],
                host="codex",
                conversation_id="session-1",
                title="Second",
            )
            context = build_context(self.event(root))
            self.assertIn("Multiple matching Codex tasks", context)
            self.assertIn(first, context)
            self.assertIn(second, context)
            self.assertNotIn("Recovered task:", context)

    def test_changed_project_evidence_is_marked_stale_before_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")
            context = build_context(self.event(root))
            status = project_model_status(root)
            self.assertEqual(status["stale_sections"], ["auth"])
            self.assertIn("Stale project sections: auth", context)

    def test_recovery_does_not_auto_clear_existing_stale_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "auth.py"
            evidence.write_text("v1", encoding="utf-8")
            enable_state(root)
            upsert_section(root, "auth", "Authentication", "Auth facts.", ["auth.py"])
            evidence.write_text("v2", encoding="utf-8")
            build_context(self.event(root))
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])
            evidence.write_text("v1", encoding="utf-8")
            build_context(self.event(root))
            self.assertEqual(project_model_status(root)["stale_sections"], ["auth"])


    def test_one_unmatched_pending_task_is_candidate_without_rebinding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(root, 0, host="dsh", title="Payments")
            before = load_state(root)["tasks"]
            context = build_context(self.event(root, session_id="new-session"))
            self.assertIn("Recoverable task candidate", context)
            self.assertIn(task_id, context)
            self.assertIn("Payments", context)
            self.assertEqual(load_state(root)["tasks"], before)
            self.assertNotIn("conversation_id", load_state(root)["tasks"][task_id])

    def test_multiple_pending_tasks_require_user_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            first, state = create_task(root, 0, host="codex", title="Alpha")
            second, _ = create_task(root, state["revision"], host="dsh", title="Beta")
            context = build_context(self.event(root, session_id="new-session"))
            self.assertIn("Multiple pending task candidates", context)
            self.assertIn("ask the user which task to continue", context)
            ordered = sorted([first, second])
            self.assertLess(context.index(ordered[0]), context.index(ordered[1]))

    def test_open_decisions_and_blocked_scopes_are_summarized_for_recovered_task_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, state = create_task(
                root, 0, host="codex", conversation_id="session-1", title="Auth"
            )
            other_task, _ = create_task(root, state["revision"], host="dsh", title="Billing")
            decision_id, _ = create_decision(
                root,
                task_id,
                "architectural",
                "Session ownership",
                "Choose session source of truth.",
                blocked_scopes=["session-persistence"],
            )
            unrelated_id, _ = create_decision(
                root,
                other_task,
                "engineering",
                "Billing retry",
                "Choose retry semantics.",
                blocked_scopes=["billing-retry"],
            )
            context = build_context(self.event(root))
            self.assertIn(f"Open decision: {decision_id}", context)
            self.assertIn("Session ownership", context)
            self.assertIn("Blocked scopes: session-persistence", context)
            self.assertNotIn(unrelated_id, context)
            self.assertNotIn("billing-retry", context)

    def test_non_open_decisions_are_not_presented_as_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enable_state(root)
            task_id, _ = create_task(
                root, 0, host="codex", conversation_id="session-1", title="Auth"
            )
            selected_id, _ = create_decision(root, task_id, "engineering", "Selected", "Context")
            select_decision(root, selected_id, 0, "Use A")
            implemented_id, _ = create_decision(root, task_id, "engineering", "Implemented", "Context")
            select_decision(root, implemented_id, 0, "Use B")
            record_implementation(root, implemented_id, 1, "Implemented B")
            verified_id, _ = create_decision(root, task_id, "engineering", "Verified", "Context")
            select_decision(root, verified_id, 0, "Use C")
            record_implementation(root, verified_id, 1, "Implemented C")
            record_verification(root, verified_id, 2, "Verified C")
            context = build_context(self.event(root))
            for decision_id in (selected_id, implemented_id, verified_id):
                self.assertNotIn(f"Open decision: {decision_id}", context)
            self.assertNotIn("user reasoning", context.lower())


if __name__ == "__main__":
    unittest.main()
